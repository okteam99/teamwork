"""Cross-stage regressions found in the v8.360.3 skill review."""
import argparse
import json
import subprocess
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import state as S
import _v8_engine as E
import _v8_stage_specs as SP
import _v8_ship as SH


def seed_feature(tmp_path, tier="tiny", dims=None):
    feature = tmp_path / "feature"
    feature.mkdir()
    plan = S.build_assembly_plan(tier, dims)
    chain = S.derive_chain(plan["dims"])
    st = {"feature_id": "T-F001", "flow_type": "Feature", "preset": tier,
          "assembly_plan": plan, "current_stage": chain[0],
          "legal_next_stages": S.derive_flow_graph(plan["dims"])[chain[0]],
          "completed_stages": [], "stage_contracts": {}, "concerns": [],
          "stage_review_roles": dict(plan["dims"]["review"]),
          "worktree": {"strategy": "off"}}
    S.atomic_write(feature / "state.json", st)
    return feature, st


def revise(feature, dim, to, capsys):
    S.cmd_revise_plan(argparse.Namespace(feature=str(feature), dim=dim, to=to,
                                        evidence="newly verified scope"))
    return json.loads(capsys.readouterr().out)


def start(feature, stage, capsys):
    args = S.build_parser().parse_args([stage + "-start", "--feature", str(feature)])
    with pytest.raises(SystemExit) as exc:
        args.func(args)
    result = json.loads(capsys.readouterr().out)
    assert exc.value.code == 0, result
    return result


def test_remove_next_stage_repositions_cursor_and_can_continue(tmp_path, capsys):
    feature, st = seed_feature(tmp_path)
    st.update(completed_stages=["dev"], current_stage="review")
    st["stage_contracts"]["dev"] = {"output_satisfied": True}
    S.atomic_write(feature / "state.json", st)
    revise(feature, "review.review", "[]", capsys)
    after = S.load_state(str(feature))
    assert after["current_stage"] == "pm_acceptance"
    assert after["legal_next_stages"] == ["ship", "dev"]
    assert "review" not in after["stage_review_roles"]
    start(feature, "pm_acceptance", capsys)


def test_insert_next_stage_is_not_silently_skipped(tmp_path, capsys):
    feature, st = seed_feature(tmp_path)
    st.update(completed_stages=["dev", "review"], current_stage="pm_acceptance")
    S.atomic_write(feature / "state.json", st)
    revise(feature, "verify_depth", "test", capsys)
    assert S.load_state(str(feature))["current_stage"] == "test"


def test_cannot_insert_prerequisite_behind_completed_work(tmp_path, capsys):
    feature, st = seed_feature(tmp_path)
    st.update(completed_stages=["dev"], current_stage="review")
    S.atomic_write(feature / "state.json", st)
    with pytest.raises(SystemExit):
        revise(feature, "spec_depth", "prd", capsys)
    assert S.load_state(str(feature))["assembly_plan"] == st["assembly_plan"]


def test_active_stage_cannot_be_removed_as_if_it_were_unstarted(tmp_path, capsys):
    feature, st = seed_feature(tmp_path)
    st.update(completed_stages=["dev"], current_stage="review")
    st["stage_contracts"]["review"] = {"input_satisfied": True}
    S.atomic_write(feature / "state.json", st)
    with pytest.raises(SystemExit):
        revise(feature, "review.review", "[]", capsys)
    assert S.load_state(str(feature))["current_stage"] == "review"


@pytest.mark.parametrize("tier", ["floor", "tiny"])
def test_custom_spec_depth_can_start_goal_and_transition(tmp_path, capsys, tier):
    feature, st = seed_feature(tmp_path, tier, {"spec_depth": "prd"})
    start(feature, "goal", capsys)
    assert SP._goal_transition(st) == "dev"
    assert not SP._evidence_ac_test_binding(st, argparse.Namespace(feature=str(feature)))[0]


def test_custom_full_plan_can_execute_without_evidence_gate(tmp_path, capsys):
    dims = {"spec_depth": "none", "evidence_gate": False, "verify_depth": "self",
            "review": {p: [] for p in S.REVIEW_POINTS}}
    feature, st = seed_feature(tmp_path, "full", dims)
    assert S.validate_dims(st["assembly_plan"]["dims"]) == []
    start(feature, "execute", capsys)


def write_result(feature, name, model="model-b", extra=""):
    d = feature / "external-cross-review"
    d.mkdir(exist_ok=True)
    path = d / name
    path.write_text("---\nreview_via: subagent\nreview_model: " + model
                    + "\nfiles_read: [code.py]\ncoverage: [implementation]\n"
                    + extra + "---\nActual review result.\n", encoding="utf-8")
    return path


def review_state():
    return {"current_stage": "review", "stage_review_roles": {"review": ["external"]}}


def test_other_stage_report_cannot_satisfy_review_evidence(tmp_path):
    write_result(tmp_path, "goal-model-a.md", "model-a")
    args = argparse.Namespace(feature=str(tmp_path))
    assert not SP._evidence_external_review_artifact(review_state(), args)[0]
    assert not SP._evidence_cross_review_coverage(review_state(), args)[0]


def test_other_stage_model_cannot_mask_identical_current_lanes(tmp_path):
    write_result(tmp_path, "goal-model-a.md", "model-a")
    write_result(tmp_path, "review-model-b.md")
    (tmp_path / "REVIEW.md").write_text("---\nreview_models:\n - architect: model-b\n---\n")
    assert not SP._evidence_review_models_staggered("REVIEW.md")(
        review_state(), argparse.Namespace(feature=str(tmp_path)))[0]


@pytest.mark.parametrize("request_id,commit,expected", [
    ("old", "code-head", False), ("current", "old-code", False),
    ("current", "code-head", True)])
def test_external_result_belongs_to_requested_round_and_commit(tmp_path, request_id, commit, expected):
    st = review_state()
    st["stage_contracts"] = {"review": {"external_review_request": {
        "request_id": "current", "target_commit": "code-head"}}}
    write_result(tmp_path, "review-model-b.md",
                 extra=f"review_request_id: {request_id}\ntarget_commit: {commit}\n")
    assert SP._evidence_external_review_artifact(st, argparse.Namespace(feature=str(tmp_path)))[0] is expected


def test_fix_recipe_is_not_a_completed_review(tmp_path):
    st = review_state()
    st["stage_contracts"] = {"review": {"rounds": [
        {"fix_commit": "fixed-code", "fix_at": "2026-01-01T00:00:00Z"}, {}]}}
    write_result(tmp_path, "review-model-b.md", extra="target_commit: old-code\n")
    d = tmp_path / "external-review-prompts"
    d.mkdir()
    (d / "review-fixverify.md").write_text("Dispatch instructions, no reviewer result.")
    args = argparse.Namespace(feature=str(tmp_path), verdict="APPROVE")
    assert not SP._evidence_external_verified_after_fix(st, args)[0]
    write_result(tmp_path, "review-model-b-fixverify.md", extra="target_commit: fixed-code\n")
    assert SP._evidence_external_verified_after_fix(st, args)[0]


def test_unrelated_failed_old_stage_does_not_poison_current_review(tmp_path):
    write_result(tmp_path, "goal-model-a.md", extra="status: CAPABILITY_BLOCKED\n")
    write_result(tmp_path, "review-model-b.md")
    assert SP._evidence_external_review_artifact(review_state(), argparse.Namespace(feature=str(tmp_path)))[0]


def test_fix_verification_requires_latest_fix_even_in_same_second(tmp_path):
    st = review_state()
    st["stage_contracts"] = {"review": {"rounds": [
        {"fix_commit": "first-fix", "fix_at": "2026-01-01T00:00:00Z"},
        {"fix_commit": "last-fix", "fix_at": "2026-01-01T00:00:00Z"}, {}]}}
    write_result(tmp_path, "review-model-b-fixverify.md", extra="target_commit: last-fix\n")
    assert SP._evidence_external_verified_after_fix(
        st, argparse.Namespace(feature=str(tmp_path), verdict="APPROVE"))[0]


def test_dispatch_round_is_persisted_and_invalidates_prior_result(tmp_path, capsys):
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(["git", "-c", "user.name=test", "-c", "user.email=test@example.invalid",
                    "commit", "-q", "--allow-empty", "-m", "code"], cwd=tmp_path, check=True)
    head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    feature, st = seed_feature(tmp_path)
    st["current_stage"] = "review"
    st["stage_contracts"]["review"] = {"auto_commit": "stale-previous-round"}
    S.atomic_write(feature / "state.json", st)
    args = S.build_parser().parse_args(["external-review", "--feature", str(feature), "--stage", "review"])
    S.cmd_external_review(args)
    first = json.loads(capsys.readouterr().out)
    assert first["target_commit"] == head
    write_result(feature, "review-model-b.md", extra=(
        f"review_request_id: {first['review_request_id']}\ntarget_commit: {head}\n"))
    gate_args = argparse.Namespace(feature=str(feature))
    assert SP._evidence_external_review_artifact(S.load_state(str(feature)), gate_args)[0]
    S.cmd_external_review(args)
    second = json.loads(capsys.readouterr().out)
    assert second["review_request_id"] != first["review_request_id"]
    assert not SP._evidence_external_review_artifact(S.load_state(str(feature)), gate_args)[0]


@pytest.mark.parametrize("verdict", ["FAIL", "PENDING"])
def test_monitor_preserves_finalize_failure_or_pending(tmp_path, monkeypatch, capsys, verdict):
    monkeypatch.setattr(SH, "_mr_state", lambda _: "MERGED")
    monkeypatch.setattr(SH, "_ci_with_attribution", lambda *_: {"status": "passing"})
    monkeypatch.setattr(SH, "_finalize_merged_feature", lambda _: {"verdict": verdict, "error": "fixture"})
    with pytest.raises(SystemExit) as exc:
        SH.cmd_await_merge(argparse.Namespace(feature=str(tmp_path), mr_url="https://example.invalid/1",
                          base="main", interval=5, max_checks=1, until_final=True))
    assert exc.value.code != 0
    assert json.loads(capsys.readouterr().out)["finalize"]["verdict"] == verdict


def test_merge_monitor_actually_runs_finalize_from_main_checkout(tmp_path, monkeypatch, capsys):
    feature = tmp_path / "worktree/feature"
    feature.mkdir(parents=True)
    main = tmp_path / "main"
    main.mkdir()
    monkeypatch.setattr(SH, "_mr_state", lambda _: "MERGED")
    monkeypatch.setattr(SH, "_ci_with_attribution", lambda *_: {"status": "passing"})
    monkeypatch.setattr(SH, "_list_worktrees", lambda _: [{"path": str(main)}, {"path": str(feature.parent)}])
    calls = []
    def run(cmd, **kwargs):
        calls.append((cmd, kwargs))
        return subprocess.CompletedProcess(cmd, 0, '{"verdict":"PASS","command":"ship-finalize"}', "")
    monkeypatch.setattr(SH.subprocess, "run", run)
    with pytest.raises(SystemExit) as exc:
        SH.cmd_await_merge(argparse.Namespace(feature=str(feature), mr_url="https://example.invalid/1",
                          base="main", interval=5, max_checks=1, until_final=True))
    assert exc.value.code == 0
    assert len(calls) == 1
    cmd, kwargs = calls[0]
    assert cmd[-3:] == ["ship-finalize", "--feature", str(feature.resolve())]
    assert Path(kwargs["cwd"]) == main
    assert json.loads(capsys.readouterr().out)["finalize"]["verdict"] == "PASS"
