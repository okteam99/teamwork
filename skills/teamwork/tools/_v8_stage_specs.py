"""
_v8_stage_specs.py — Teamwork v8.0 各 stage 的具体契约定义。

每个 stage 一个 StageSpec 实例,包含:
- prerequisites: 入口前置(xx-start 校验)
- artifacts: 出口产物(xx-complete 校验)
- evidence_checks: 事实证据(xx-complete 校验)
- brief_template_fn: next_action_brief 渲染
- auto_transition_fn: 自动转移到下一 stage

STAGE_SPECS dict 在文件末尾汇总。

实现进度:
- ✅ goal (B1)
- ✅ dev      (B6 · 完整模板示范)
- ⏳ ui_design / blueprint / blueprint_lite (B2/B4/B5)
- ⏳ review / test / browser_e2e / pm_acceptance / ship (B7-B11)

本文件即 stage 契约 schema 的现行权威(配合 state.py --help)。
v8.0 命令 schema 快照已清理 · git 历史可溯。
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

from _v8_engine import (
    StageArtifactSpec,
    StageEvidenceCheck,
    StagePrerequisite,
    StageSpec,
    commit_exists,
    get_git_commit_changeset,
    parse_frontmatter,
)


# ─── 暂停点纪律 helper(L2 substep 链内部 AI 自觉区的物化兜底) ──────
#
# 治本 case:PTR-F033 实战 · AI 在 goal substep 2(PL-PM 讨论)后擅自
# 插用户暂停点(AskUserQuestion)询问 Open Questions · 应该走完 substep 3-5
# 多角色 review 收敛后才到 substep 6 一次性 user-confirm。
#
# 根因:brief 列了 substep 链 + 末尾暂停点,但没明文写"中间禁暂停"。
# AI 把"至少 substep 6 暂停"理解成"至少这一次",而不是"只有这一次"。
#
# 修复:每个 stage brief 内联以下纪律段 · 让 AI 在执行那一刻就看到红线。


def _pause_discipline_block(authorized_pause_substep: str) -> str:
    """生成"暂停点纪律"段落 · 嵌入每个 stage 的 brief。

    Args:
        authorized_pause_substep: 本 stage 唯一授权的暂停点描述
                                  (如 "Substep 6 · 用户最终确认")
    """
    return f"""
### 🔴 暂停点纪律(CLAUDE.md 红线 R5 物化 · 治本 PTR-F033 case)

**本 stage 唯一授权暂停**:{authorized_pause_substep}

- ⛔ Substep 链中间 **0** 用户暂停点 · **0** AskUserQuestion · **0** "请确认"
- ⛔ Open Questions / 待决策项 **不是**用户暂停点 · 是 PRD/Review 的评审项
- ⛔ "节省 round-trip" "顺手问掉" "5 个开放问题阻塞" **不构成**插暂停理由
- ✅ 所有疑问写进 PRD/REVIEW 文档 · 由多角色 review 评 · 到授权暂停点一次性 escalate
- ✅ 主对话内角色切换(PM↔PL↔QA↔architect)闭环 · 不打扰用户

**反模式黑名单**(命中 = process 违规 · 必须重做):
  ❌ substep 2 (PL-PM 讨论) 后 AskUserQuestion
  ❌ substep 3 (多角色评审) 前 AskUserQuestion 询问 PRD 范围
  ❌ Open Questions 直接抛给用户
  ❌ "我有 3 个细节想跟你确认" / "先问几个问题再做"

**state.py 物化兜底**:
  本 stage complete 时 state.py 校验 review artifact mtime + frontmatter
  revision_history · 检测到 substep 链被压缩 → FAIL + hint。
"""


# ─── 通用前置 check 函数(共享) ──────────────────────────────────────


def _check_feature_initialized(state: dict, args) -> bool:
    return state.get("feature_id") is not None and state.get("flow_type") is not None


def _check_stage_output_satisfied(stage: str):
    def _check(state: dict, args) -> bool:
        c = state.get("stage_contracts", {}).get(stage, {})
        return c.get("output_satisfied") is True

    return _check


def _check_file_exists(rel_path: str):
    def _check(state: dict, args) -> bool:
        feature_dir = Path(args.feature)
        return (feature_dir / rel_path).exists()

    return _check


def _check_file_or_alt(*rel_paths: str):
    """任一文件存在即通过(如 PRD.md OR bugfix/BUG-*.md)"""

    def _check(state: dict, args) -> bool:
        feature_dir = Path(args.feature)
        for p in rel_paths:
            if "*" in p:
                if list(feature_dir.glob(p)):
                    return True
            elif (feature_dir / p).exists():
                return True
        return False

    return _check


# ─── 通用 evidence check 函数(共享) ─────────────────────────────────


# v8.14:artifact basename → 起草模板文件名(用于 evidence FAIL 时的 hint suffix)
# 治本 PTR-F054 "AI 找历史 Feature 抄" case · 缺产物 FAIL 时直接给模板路径
# 不全 · 只列有专用模板的 artifact(无映射 → suffix 为空 · 不污染原 hint)
_ARTIFACT_TEMPLATE_MAP: dict[str, str] = {
    "PRD.md": "prd.md",
    "UI.md": "ui.md",
    "TC.md": "tc.md",
    "TECH.md": "tech.md",
    "TEST-REPORT.md": "test-report.md",
    "BROWSER-TEST-REPORT.md": "browser-test-report.md",
    "PM-NOTE.md": "pm-note.md",
    "BUG-REPORT.md": "bug-report.md",
}


def _template_hint(artifact: str) -> str:
    """从 artifact 路径反查模板路径 · 返回 ` · 起草模板: <abs path>` 后缀(无映射返空)。

    调用方:evidence 失败的 reason 末尾 append · AI 直接 cat 模板而不找历史 Feature。
    """
    base = Path(artifact).name
    tmpl_name = _ARTIFACT_TEMPLATE_MAP.get(base)
    if not tmpl_name:
        return ""
    # SKILL_ROOT/templates/<tmpl>(本模块在 SKILL_ROOT/tools/ 下)
    tmpl_path = Path(__file__).resolve().parent.parent / "templates" / tmpl_name
    return f" · 起草模板:{tmpl_path}"


def _evidence_test_exit_code_zero(state: dict, args) -> tuple[bool, str]:
    """校验 --test-exit-code == 0"""
    exit_code = getattr(args, "test_exit_code", None)
    if exit_code is None:
        return False, "缺 --test-exit-code 参数"
    if int(exit_code) != 0:
        return False, f"test_exit_code={exit_code} ≠ 0 · 测试未通过"
    return True, ""


def _evidence_needs_ui_decided(state: dict, args) -> tuple[bool, str]:
    """v8.0+P0-6:校验 --needs-ui 已传 + 写入 state.execution_hints.ui_design_needed。

    根因治本:字段必有值 · 由 goal-complete --needs-ui 必传强制 ·
    state.py 不再走 None/fallback 路径。
    """
    val = getattr(args, "needs_ui", None)
    if val not in ("true", "false"):
        return False, (
            f"--needs-ui 必传(true/false)· got {val!r}。"
            f"该字段决策本 Feature 是否需要独立 UI Design Stage:\n"
            f"  true  → 下一 stage = ui_design(Designer 出 UI.md + preview)\n"
            f"  false → 下一 stage = blueprint(直接进技术方案)"
        )

    bool_val = val == "true"
    # 流程类型校验:敏捷需求 / Planning 不应有 UI
    flow = state.get("flow_type")
    if bool_val and flow == "敏捷需求":
        return False, (
            "敏捷需求流程 + --needs-ui=true 矛盾 · "
            "若有 UI 改动应升级 Feature 流程(reset-prev + 改 flow_type)"
        )
    # 写字段(state.execution_hints.ui_design_needed)
    hints = state.setdefault("execution_hints", {})
    hints["ui_design_needed"] = bool_val
    return True, ""


def _evidence_test_stdout_non_empty(state: dict, args) -> tuple[bool, str]:
    """校验 --test-stdout 非空"""
    stdout = getattr(args, "test_stdout", None)
    if not stdout:
        return False, "缺 --test-stdout 参数"
    p = Path(stdout)
    if p.exists():
        content = p.read_text(encoding="utf-8", errors="replace")
    else:
        content = stdout
    if not content.strip():
        return False, "test_stdout 为空"
    return True, ""


# ─── L2 substep 链纪律 evidence(治本 PTR-F033 case) ───────────────


def _evidence_review_after_primary(primary_artifact: str, review_artifact: str):
    """通用 check:review_artifact mtime 必须 > primary_artifact mtime。

    证明 review 发生在 primary 落盘 *之后* · 不是同时产出(压缩 substep 链)。
    """

    def _check(state: dict, args) -> tuple[bool, str]:
        feature_dir = Path(args.feature)
        primary = feature_dir / primary_artifact
        review = feature_dir / review_artifact
        if not primary.exists():
            return False, f"{primary_artifact} 不存在{_template_hint(primary_artifact)}"
        if not review.exists():
            return False, f"{review_artifact} 不存在 · review 未发生{_template_hint(review_artifact)}"
        if review.stat().st_mtime <= primary.stat().st_mtime:
            return False, (
                f"{review_artifact} mtime <= {primary_artifact} mtime · "
                f"review 未在 {primary_artifact} 落盘后发生 · "
                f"substep 链可能被压缩 · 重做 review"
            )
        return True, ""

    return _check


def _evidence_revision_history_present(artifact: str, min_revisions: int = 1):
    """通用 check:artifact frontmatter 含 revision_history(至少 N 条)。

    证明 artifact 经历过至少 N 次修订收敛(默认 1 = draft-v0.1 → v0.2 等)。
    """

    def _check(state: dict, args) -> tuple[bool, str]:
        feature_dir = Path(args.feature)
        target = feature_dir / artifact
        if not target.exists():
            return False, f"{artifact} 不存在{_template_hint(artifact)}"
        fm = parse_frontmatter(target)
        if not fm:
            return False, f"{artifact} 缺 frontmatter{_template_hint(artifact)}"
        rev_history = fm.get("revision_history")
        if not rev_history:
            return False, (
                f"{artifact} frontmatter 缺 `revision_history` 字段 · "
                f"无法证明 review 收敛过 · "
                f"添加 revision_history 字段(至少 {min_revisions} 条)"
            )
        if isinstance(rev_history, list) and len(rev_history) < min_revisions:
            return False, (
                f"{artifact} revision_history 仅 {len(rev_history)} 条 < {min_revisions}"
            )
        return True, ""

    return _check


def _evidence_reviewers_match(review_artifact: str):
    """v8.0+P0-9:review artifact frontmatter.reviewers 必含 state.stage_review_roles[当前 stage]。

    参数:review_artifact = 含 reviewers 字段的 markdown 路径(相对 feature_dir)
        - goal:PRD-REVIEW.md
        - blueprint:TECH-REVIEW.md
        - review:REVIEW.md
    """
    def _check(state: dict, args) -> tuple[bool, str]:
        current = state.get("current_stage")
        required = state.get("stage_review_roles", {}).get(current, [])
        if not required:
            return True, ""  # 无配置 · 跳过(此 stage 不要求 review)

        feature_dir = Path(args.feature)
        artifact_path = feature_dir / review_artifact
        if not artifact_path.exists():
            return False, (
                f"{review_artifact} 不存在 · 无法校验 reviewers"
                f"{_template_hint(review_artifact)}"
            )

        fm = parse_frontmatter(artifact_path)
        if not fm:
            return False, f"{review_artifact} 缺 frontmatter{_template_hint(review_artifact)}"

        reviewers = fm.get("reviewers")
        if not reviewers:
            return False, (
                f"{review_artifact} frontmatter.reviewers 为空 · 必含: {required}"
            )

        # reviewers 可能是 list 或 str · 统一处理(兼容行内 `[a, b, c]` 格式)
        if isinstance(reviewers, str):
            cleaned = reviewers.strip().lstrip("[").rstrip("]")
            reviewer_set = {r.strip().strip("\"'").lower() for r in cleaned.split(",") if r.strip()}
        elif isinstance(reviewers, list):
            reviewer_set = {str(r).strip().strip("\"'").lower() for r in reviewers if r}
        else:
            return False, f"{review_artifact} frontmatter.reviewers 格式非法"

        required_set = {r.lower() for r in required}
        # v8.111:角色 roll-call 容许「角色限定写法」—— reviewer token 命中角色名
        # 本身、或 `角色-<限定>` 前缀,即算该角色已覆盖(如 external-claude 满足
        # external · 保留异质模型 provenance)。异质性不由此 roll-call 保证 ——
        # 由 _evidence_external_review_artifact 校验 cross-review 产物的 review_model。
        def _role_covered(role: str) -> bool:
            return any(rv == role or rv.startswith(role + "-") for rv in reviewer_set)

        missing = sorted(r for r in required_set if not _role_covered(r))
        if missing:
            return False, (
                f"{review_artifact} frontmatter.reviewers 缺角色: {missing} · "
                f"必含 state.stage_review_roles[{current}] = {required} · "
                f"角色名本身或 `角色-限定`(如 external-claude)均可 · "
                f"补 reviewer 或在上一 stage complete 时跑 --next-stage-roles 调整"
            )
        return True, ""

    return _check


# ─── B1 · goal ─────────────────────────────────────────────────


def _goal_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Goal Stage

### 目标
PM 现状调研(自答优先)· 起草 PRD · PL 对抗质疑 · (条件)goal-critical 早问门 · 多角色并行评审 · 收敛后用户确认 · 决策是否需要 UI Design Stage。

### 结果(完成判定)
- `PRD.md`(frontmatter:`acceptance_criteria` + `revision_history`)
- `PRD-REVIEW.md`(frontmatter:`reviewers` + `verdicts` **全 APPROVE/SKIP** · 含 `PL-CHALLENGE` 段〔角色含 pl 时〕· mtime > PRD.md)
- `state.execution_hints.ui_design_needed` 已决策(由 `--needs-ui`)

### 怎么做
**必读** `stages/goal-stage.md`(详细步骤 9 步:调研 → 起草 → PL 质疑 → 早问门 → 评审 → 修订 → 判定 → needs-ui → 确认)。

### 完成方式
```
state.py goal-complete --feature <path> \
  --auto-commit <hash> --artifacts PRD.md,PRD-REVIEW.md \
  --needs-ui {{true|false}}
```
"""


def _goal_transition(state: dict) -> Optional[str]:
    """goal 完成后的下一 stage 选择(v8.0+P0-6 治本)。

    严格读 state.execution_hints.ui_design_needed · 字段必有值
    (goal-complete --needs-ui 必传 · evidence_check 已强制写入)。
    无 None / fallback / 默认值绕过。
    """
    flow = state.get("flow_type")
    hints = state.get("execution_hints", {})

    if flow == "Feature":
        # 字段必有值(evidence_check needs_ui_decided 已通过)
        if hints.get("ui_design_needed") is True:
            return "ui_design"
        return "blueprint"
    elif flow == "敏捷需求":
        # 敏捷需求必 --needs-ui false(evidence_check 校验)· 直接 blueprint_lite
        return "blueprint_lite"
    elif flow == "Bug":
        return "dev"
    elif flow == "Micro":
        return "dev"
    return None


def _evidence_prd_verdicts_all_pass(state: dict, args) -> tuple[bool, str]:
    """v8.132:PRD-REVIEW verdicts 全 APPROVE/SKIP 才 goal-complete(物化 substep 7「全员通过判定」·
    此前为纸面纪律 · 全 NEEDS_REVISION 也能过门禁)。

    解析策略:parse_frontmatter 是简易解析器(不支持嵌套 map)→ 直接在 frontmatter 原文上取
    verdicts 块(行内 {..} 或缩进 map 两种写法均兼容)· 扫描块内裁决词 · 任一非 APPROVE/SKIP → FAIL。
    """
    f = Path(args.feature) / "PRD-REVIEW.md"
    if not f.exists():
        return False, "PRD-REVIEW.md 不存在 · 无法校验 verdicts"
    text = f.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return False, "PRD-REVIEW.md 缺 frontmatter · 无法校验 verdicts"
    end = text.find("\n---\n", 4)
    fm_text = text[4:end] if end != -1 else ""
    m = re.search(r"^verdicts:(.*(?:\n[ \t]+[^\n]+)*)", fm_text, re.M)
    if not m:
        return False, (
            "PRD-REVIEW.md frontmatter 缺 verdicts(role: APPROVE|NEEDS_REVISION|SKIP)· "
            "模板见 templates/prd.md § PRD-REVIEW schema"
        )
    tokens = re.findall(
        r"\b(APPROVE|NEEDS_REVISION|SKIP|PASS_WITH_CONCERNS|PASS|REJECTED|REJECT)\b",
        m.group(1), re.I)
    if not tokens:
        return False, "verdicts 块未解析到任何裁决值(role: APPROVE|NEEDS_REVISION|SKIP)"
    bad = sorted({t.upper() for t in tokens} - {"APPROVE", "SKIP"})
    if bad:
        return False, (
            f"verdicts 未全员通过(含 {'/'.join(bad)})· "
            "NEEDS_REVISION → PM 回应修订 PRD 后重评(goal-stage substep 6→7)· "
            "全员 APPROVE/SKIP 才可 goal-complete(词表只认 APPROVE|NEEDS_REVISION|SKIP)"
        )
    return True, ""


def _evidence_pl_challenge_present(state: dict, args) -> tuple[bool, str]:
    """v8.132:stage_review_roles[goal] 含 pl 时 · PRD-REVIEW.md 必含「PL-CHALLENGE」标记
    (PL 对抗质疑物化 · 防同上下文切帽子的鼓掌过场)。

    敏捷需求 goal 默认角色无 pl → 自动放行;change-review-roles 去 pl 同理。
    """
    roles = [str(r).lower() for r in (state.get("stage_review_roles") or {}).get("goal", [])]
    if "pl" not in roles:
        return True, ""
    f = Path(args.feature) / "PRD-REVIEW.md"
    if not f.exists():
        return False, "PRD-REVIEW.md 不存在 · 无法校验 PL-CHALLENGE"
    if "PL-CHALLENGE" not in f.read_text(encoding="utf-8"):
        return False, (
            "PRD-REVIEW.md 缺 PL-CHALLENGE 段:PL 须按质疑五问(价值前提/问题定义/范围最小化/"
            "上游对齐/复活检查)发起对抗质疑 · 至少 1 条实质质疑或显式「无实质质疑 + 理由」· "
            "finding id 用 PL-CHALLENGE-{n} · 详 stages/goal-stage.md §3"
        )
    return True, ""


GOAL_SPEC = StageSpec(
    name="goal",
    prerequisites=[
        StagePrerequisite(
            id="feature_initialized",
            check_fn=_check_feature_initialized,
            hint="先跑 state.py init-feature 创建 state.json",
            description="state.feature_id + state.flow_type 必须存在",
        ),
        # v8.132:删 prepare_completed 死门禁(flow_type 恒非空 → 恒真 · 且 hint 引用 P0-12
        # 已删除的 state.py prepare 命令)· prepare 准入由 init-feature 的 prepare-check
        # audit 门禁承担(prepare.md §0.5 已物化)· 此处重复校验无信息量。
    ],
    # goal stage = 业务目标确认 · 产 PRD · Feature / 敏捷需求 流程专属
    # Feature Planning 走单 stage planning · 不进 goal
    artifacts=[
        # 文档类 artifact 多角色多轮修订 = 多 commit 常态 · must_be_in_commit=False
        # 防 AI 被迫 git reset --soft squash;ship R-S7 保证最终 commit。
        StageArtifactSpec(
            path="PRD.md",
            frontmatter_required=["acceptance_criteria"],
            body_min_lines=20,
            must_be_in_commit=False,
            description="需求规范 · 含结构化 AC",
        ),
        StageArtifactSpec(
            path="PRD-REVIEW.md",
            frontmatter_required=["reviewers", "verdicts"],
            body_min_lines=15,
            must_be_in_commit=False,
            description="多角色 PRD 评审记录",
        ),
    ],
    evidence_checks=[
        # v8.0+P0-1:L2 substep 链纪律物化兜底
        StageEvidenceCheck(
            name="prd_review_after_prd",
            check_fn=_evidence_review_after_primary("PRD.md", "PRD-REVIEW.md"),
            description="PRD-REVIEW.md mtime > PRD.md mtime · 证明 review 在 PRD 之后",
        ),
        StageEvidenceCheck(
            name="prd_revision_history",
            check_fn=_evidence_revision_history_present("PRD.md", min_revisions=1),
            description="PRD.md frontmatter 含 revision_history · 证明经历 review 收敛",
        ),
        # v8.0+P0-6:--needs-ui 必传 + 写字段(根因治本)
        StageEvidenceCheck(
            name="needs_ui_decided",
            check_fn=_evidence_needs_ui_decided,
            description=(
                "--needs-ui 必传(true/false)· "
                "字段写入 state.execution_hints.ui_design_needed · "
                "下一 stage 决策依据"
            ),
        ),
        # v8.0+P0-9:PRD-REVIEW.md reviewers 必含 state.stage_review_roles[goal]
        StageEvidenceCheck(
            name="reviewers_match",
            check_fn=_evidence_reviewers_match("PRD-REVIEW.md"),
            description="PRD-REVIEW.md frontmatter.reviewers 必含 state.stage_review_roles[goal]",
        ),
        # v8.132:物化 substep 7「全员通过判定」(此前纸面纪律 · NEEDS_REVISION 也能 complete)
        StageEvidenceCheck(
            name="prd_verdicts_all_pass",
            check_fn=_evidence_prd_verdicts_all_pass,
            description="PRD-REVIEW.md frontmatter.verdicts 全 APPROVE/SKIP · 全员通过才 goal-complete",
        ),
        # v8.132:PL 对抗质疑物化(防 self-talk 过场 · 角色无 pl 自动放行)
        StageEvidenceCheck(
            name="pl_challenge_present",
            check_fn=_evidence_pl_challenge_present,
            description="PRD-REVIEW.md 含 PL-CHALLENGE 段(质疑五问 · stage_review_roles[goal] 含 pl 时强制)",
        ),
    ],
    brief_template_fn=_goal_brief,
    auto_transition_fn=_goal_transition,
    allowed_flow_types=["Feature", "敏捷需求"],  # Feature Planning 走 planning · 不进 goal
    authorized_pause_point=(
        "Substep 9 · 用户最终确认(全员 review 通过后)"
        "+ 条件暂停:Substep 4 goal-critical 早问门(三闸过审的用户主权问题 ≤3 · 一次性 · "
        "auto 模式不停转 §待决策项 + WARN · 详 stages/goal-stage.md §4)"
    ),
)


# ─── B5.5 · diagnose(仅 Bug · 根因细查 + 修复方案确认 · v8.107)─────────


def _check_flow_is_bug(state: dict, args) -> bool:
    return state.get("flow_type") == "Bug"


def _evidence_diagnose_doc(state: dict, args) -> tuple[bool, str]:
    """diagnose 产出 = bugfix/BUG-*.md 且含根因 + 修复方案(深查实证 · 用户已确认)。

    检查:① bugfix/BUG-*.md 存在 · ② frontmatter root_cause + fix_summary 非空
    (fix_summary = 修复**方案**摘要 · 不是「已修」· diagnose 阶段还没写 fix 码)。
    BUG-*.md 动态命名 → 用 evidence_check(非固定路径 artifact)。
    """
    feature_dir = Path(args.feature)
    bug_files = list(feature_dir.glob("bugfix/BUG-*.md"))
    if not bug_files:
        return False, (
            "diagnose 未产出 bugfix/BUG-*.md(模板 templates/bug-report.md)· "
            "深读代码做根因细查 → 写 §现象/§根因/§修复方案 → 用户确认修复方案后再 diagnose-complete"
        )
    f = bug_files[0]
    fm = parse_frontmatter(f) or {}
    missing = [k for k in ("root_cause", "fix_summary") if not str(fm.get(k, "")).strip()]
    if missing:
        return False, (
            f"{f.name} frontmatter 缺 {missing}(根因 / 修复方案)· "
            "diagnose 必须深查真因 + 给出修复方案(改哪 / 怎么改 / 取舍)· 用户确认后才 complete"
        )
    return True, ""


def _diagnose_brief(state: dict) -> str:
    return """## Diagnose Stage(Bug · 根因细查 + 修复方案确认)

### 目标
🔴 **深读相关代码做根因细查**(triage/prepare 时读的代码往往不够细 · 必挖到真因)· 出修复方案 · **用户确认后才进 dev**。治本 fix 修偏。

### 结果(完成判定)
- `bugfix/BUG-*.md`(模板 templates/bug-report.md)· frontmatter `root_cause` + `fix_summary` 非空
- §现象(可复现)+ §根因(深查实证:哪行 / 哪个调用 / 为什么 · 非表面猜测)+ §修复方案(改哪 · 怎么改 · 取舍 · 影响面)
- 🔴 **不在本阶段写 fix 代码**(只查 + 规划 · 写码在 dev)

### 怎么做
**必读** `stages/diagnose-stage.md`(深读代码方法 + 根因实证 + 修复方案要素 + 用户确认协议)。

### 完成方式(🔴 R5 暂停点:先把 §修复方案 给用户确认 · 用户 ok 才跑)
```
state.py diagnose-complete --feature <path> --auto-commit <hash> --artifacts bugfix/BUG-<id>.md
```
"""


def _diagnose_transition(state: dict) -> Optional[str]:
    return "dev"


DIAGNOSE_SPEC = StageSpec(
    name="diagnose",
    prerequisites=[
        StagePrerequisite(
            id="flow_type_is_bug",
            check_fn=_check_flow_is_bug,
            hint="diagnose 仅 Bug 流程 · 检查 state.flow_type",
            description="flow_type == 'Bug'",
        ),
    ],
    artifacts=[],  # BUG-*.md 动态命名 → 用 evidence_check 校验(非固定路径 artifact)
    evidence_checks=[
        StageEvidenceCheck(
            name="diagnose_doc",
            check_fn=_evidence_diagnose_doc,
            description="bugfix/BUG-*.md 存在 + 根因/修复方案非空(深查 · 用户确认)",
        ),
    ],
    brief_template_fn=_diagnose_brief,
    auto_transition_fn=_diagnose_transition,
    allowed_flow_types=["Bug"],
    authorized_pause_point="diagnose-complete 前 · 🔴 把 §修复方案 给用户确认(R5)· 用户 ok 才 complete → dev",
)


# ─── B6 · dev(完整模板示范) ─────────────────────────────────────────


def _check_blueprint_or_alt_done(state: dict, args) -> bool:
    """dev 准入:blueprint/blueprint_lite output_satisfied · 或 Bug 流程 diagnose 完成 · 或 Micro 直入。

    v8.107:Bug 不再直入 dev —— 必先 diagnose(根因细查 + 修复方案 · 用户确认)· 防 fix 修偏。
    """
    contracts = state.get("stage_contracts", {})
    if contracts.get("blueprint", {}).get("output_satisfied") is True:
        return True
    if contracts.get("blueprint_lite", {}).get("output_satisfied") is True:
        return True
    flow = state.get("flow_type")
    if flow == "Bug":
        return contracts.get("diagnose", {}).get("output_satisfied") is True
    if flow == "Micro":
        return True
    return False


def _check_prd_or_bug_report(state: dict, args) -> bool:
    """v8.16 治本 INFRA-M001 case:按 flow_type 分支判 spec 文档存在性。

    - Micro:无 PRD / BUG-REPORT(改 1 行常量 · spec 在 init-feature 时记到 state.json)
              → 直接 PASS(R0:flow_type 可枚举 · 不要把 Micro 当 Feature/Bug 校验)
    - Bug:必有 bugfix/BUG-*.md(模板 templates/bug-report.md)
    - Feature / 敏捷需求 / 其他:必有 PRD.md(goal stage 产物)
    """
    flow = state.get("flow_type")
    if flow == "Micro":
        return True  # Micro 无 spec 文档 · skip(改 1 行常量 · 不需要长形式 PRD/BUG)
    feature_dir = Path(args.feature)
    if flow == "Bug":
        return bool(list(feature_dir.glob("bugfix/BUG-*.md")))
    # Feature / 敏捷需求:goal stage 必产 PRD.md
    return (feature_dir / "PRD.md").exists()


def _check_ui_consistent(state: dict, args) -> bool:
    """若 ui_design 已完成,UI.md 必须存在"""
    if state.get("stage_contracts", {}).get("ui_design", {}).get("output_satisfied") is True:
        return (Path(args.feature) / "UI.md").exists()
    return True  # ui_design 未启用,跳过此 check


def _dev_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Dev Stage

### 目标
按 TECH.md 实现代码 · TDD 红绿循环 · 测试全绿 · auto-commit 锚定证据。

### 结果(完成判定)
- 代码 + 测试一并 commit
- test exit-code = 0 · test stdout 非空
- artifacts 在 commit changeset 内
- 自查通过(规范 / 无回归 / build / linter)
- (Bug 流程额外)`bugfix/BUG-*.md` 报告

### 怎么做
**必读** `stages/dev-stage.md`(详细步骤 6 步 + 注意事项 5 条 · 含 TDD / UI 还原 / TECH 模糊 fallback)。

### 完成方式
```
state.py dev-complete --feature <path> --auto-commit <hash> \
  --artifacts <files> --test-stdout <log> --test-exit-code 0
```
"""


def _dev_transition(state: dict) -> Optional[str]:
    """dev 完成后的下一 stage。"""
    flow = state.get("flow_type")
    if flow == "Micro":
        return "pm_acceptance"  # Micro 跳过 review/test · 仍走 pm_acceptance(用户验收)→ ship
    return "review"  # Feature / Bug / 敏捷 都走 review


DEV_SPEC = StageSpec(
    name="dev",
    prerequisites=[
        StagePrerequisite(
            id="blueprint_or_alt_done",
            check_fn=_check_blueprint_or_alt_done,
            hint=(
                "Feature/敏捷流程:先完成 blueprint(-complete) 或 blueprint_lite(-complete)。"
                "Bug 流程:先完成 diagnose(-complete · 根因细查 + 修复方案确认)· 不再直入 dev。"
                "Micro 流程:无需前置 · 可直入 dev。"
                "当前 flow_type / stage_contracts 不满足任一条件。"
            ),
            description="blueprint/blueprint_lite output_satisfied · 或 Bug diagnose 完成 · 或 Micro",
        ),
        StagePrerequisite(
            id="prd_or_bug_report_exists",
            check_fn=_check_prd_or_bug_report,
            hint=(
                "Feature / 敏捷需求 流程必须有 PRD.md(回 goal-complete 起草)。"
                "Bug 流程必须有 bugfix/BUG-*.md(模板 templates/bug-report.md · "
                "含 frontmatter bug_id/symptom/root_cause/fix_summary + "
                "body §现象/§根因/§修复方案/§回归测试)。"
                "Micro 流程 skip(改 1 行常量 · 无 spec 文档)。"
            ),
            description=(
                "按 flow_type 分支:Feature/敏捷需求→PRD.md · Bug→bugfix/BUG-*.md · Micro→skip"
            ),
        ),
        StagePrerequisite(
            id="ui_artifact_consistent",
            check_fn=_check_ui_consistent,
            hint=(
                "ui_design 已完成但 UI.md 缺失 · 状态不一致 · "
                "跑 `state.py raw-read --field stage_contracts.ui_design` 确认 · "
                "或重跑 `state.py ui_design-complete` 修复"
            ),
            description="如 ui_design 已 satisfied · UI.md 必须存在",
            auto_fixable=False,
        ),
    ],
    artifacts=[
        # dev stage 的代码产物路径项目特异 · 不强制 path · 只校验 evidence
        # --artifacts 列出的文件由 evidence 校验是否在 commit 内
    ],
    evidence_checks=[
        StageEvidenceCheck(
            name="test_exit_code_zero",
            check_fn=_evidence_test_exit_code_zero,
            description="单测必须全绿 · --test-exit-code = 0",
        ),
        StageEvidenceCheck(
            name="test_stdout_non_empty",
            check_fn=_evidence_test_stdout_non_empty,
            description="--test-stdout 非空 · 证明真跑过测试",
        ),
    ],
    brief_template_fn=_dev_brief,
    auto_transition_fn=_dev_transition,
    authorized_pause_point="无暂停 · 完成后自动转 review(Micro 转 pm_acceptance)",
)


# ─── B2 · ui_design ─────────────────────────────────────────────────


def _ui_design_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## UI Design Stage

### 目标
Designer 产出 UI.md + HTML 预览 · sitemap 同步(如涉及全景变更)。

### 结果(完成判定)
- `UI.md`(frontmatter:`pages: [{{id, title}}]` + `panorama_medium`)
- 预览产物(按介质):`static-html` → `preview/*.html`(每 page.id 1 文件 · 可交互);`same-stack` → `{{panorama_path}}/preview-project/`(同栈可跑项目 + `preview.sh` + `package.json`)
- (条件)sitemap.md 已更新

### 怎么做
**必读** `stages/ui-design-stage.md`(详细步骤 6 步 + 注意事项 5 条)。

### 完成方式
```
state.py ui_design-complete --feature <path> --auto-commit <hash> \
  --artifacts UI.md[,preview/]   # same-stack 仅 UI.md(预览权威在 preview-project)
```
"""


def _evidence_panorama_changed_decided(state: dict, args) -> tuple[bool, str]:
    """校验 ui_design-complete --panorama-changed 已传(true/false)·
    写入 state.execution_hints.panorama_changed · 决定下一 stage 是否 panorama_sync。

    治本:历史 panorama 同步埋在 ui_design step 4 隐式动作 · 跨 Feature 影响无显式
    暂停点。v8.x 拆出 panorama_sync 条件 stage · 由本字段决定是否进入。
    """
    val = getattr(args, "panorama_changed", None)
    if val not in ("true", "false"):
        return False, (
            f"--panorama-changed 必传(true/false)· got {val!r}。"
            f"决策本 Feature UI 改动是否影响 workspace 级 panorama(sitemap/overview/IA):\n"
            f"  true  → 下一 stage = panorama_sync(更新 panorama 单源 + 跨 Feature 协调评审)\n"
            f"  false → 下一 stage = blueprint(本 Feature UI 不动 panorama)"
        )
    hints = state.setdefault("execution_hints", {})
    hints["panorama_changed"] = (val == "true")
    return True, ""


def _ui_design_transition(state: dict) -> Optional[str]:
    """ui_design 完成后 · 按 execution_hints.panorama_changed 分支:
    - true → panorama_sync(workspace 级 IA 同步 · 跨 Feature 评审)
    - false → blueprint(Feature) / blueprint_lite(敏捷需求)
    """
    hints = state.get("execution_hints", {})
    if hints.get("panorama_changed") is True:
        return "panorama_sync"
    flow = state.get("flow_type")
    if flow == "敏捷需求":
        return "blueprint_lite"
    return "blueprint"


def _evidence_panorama_artifact(state: dict, args) -> tuple[bool, str]:
    """按 UI.md frontmatter 校验 panorama 产物。

    v8.58(同栈 preview.sh 即唯一预览 · 用户拍板 option B · supersede v8.56 静态 build 物化):
      - `same-stack`:全景权威 = preview-project 源(committed 可跑独立项目)· 物化 =
        `{panorama_path}/preview-project/` + `preview.sh` + `package.json`(不再要静态 build 产物)·
        预览 = 跑 preview.sh 起 dev server(动态端口 · 不在 teamwork 层起 server)
      - `static-html`:
          - 有 `pages_changed[]`(v8.17 全景为权威)→ 校验每个 panorama_file 真实存在
          - 否则 → 要求 Feature 内 `preview/*.html` ≥ 1

    详 stages/ui-design-stage.md § Panorama 介质类型 / § 预览。
    """
    feature_dir = Path(args.feature)
    ui_md = feature_dir / "UI.md"
    if not ui_md.exists():
        return False, f"UI.md 不存在{_template_hint('UI.md')}"
    fm = parse_frontmatter(ui_md) or {}

    medium = fm.get("panorama_medium", "static-html")
    if medium not in ("same-stack", "static-html"):
        return False, (f"panorama_medium={medium!r} 非法 · 应 same-stack 或 static-html "
                       "(详 ui-design-stage.md § Panorama 介质类型)")

    if medium == "same-stack":
        # v8.58 option B:物化 = preview-project 可跑 + preview.sh 存在(不再要静态 build)
        # v8.61:+ auto_commit 校验(防 preview-project 源未提交 · ship 丢失)
        return _check_same_stack_preview_project(
            feature_dir, fm, getattr(args, "auto_commit", None))

    # static-html:v8.17 新模式 · 全景为唯一权威(有 pages_changed[])
    pages_changed = fm.get("pages_changed")
    if pages_changed and isinstance(pages_changed, list):
        return _check_pages_changed_authority(feature_dir, fm, pages_changed)

    # 老模式:Feature 内 preview/*.html ≥ 1
    preview_dir = feature_dir / "preview"
    if not preview_dir.exists() or not list(preview_dir.glob("*.html")):
        return False, (
            "panorama_medium=static-html · 需要 preview/*.html ≥ 1 · "
            "(若是 same-stack 项目 · UI.md frontmatter 改 panorama_medium: same-stack · "
            "或 v8.17 推荐:frontmatter 加 pages_changed[] 走全景为权威模式 · "
            "详 stages/ui-design-stage.md § 全景为唯一权威)"
        )
    return True, ""


def _resolve_panorama_subdir(feature_dir: Path, ppath_raw: str, sub: str) -> list:
    """resolve {panorama_path}/{sub} 候选路径(绝对 / 相对仓库根 / feature_dir 兜底)。"""
    import subprocess
    repo_top = None
    try:
        r = subprocess.run(
            ["git", "-C", str(feature_dir), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            repo_top = Path(r.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass
    ppath = Path(ppath_raw)
    candidates = [ppath / sub]
    if not ppath.is_absolute():
        if repo_top:
            candidates.insert(0, repo_top / ppath / sub)
        candidates.append(feature_dir / ppath / sub)  # 兜底
    return candidates


def _path_in_commit(repo_dir: Path, commit: str, abs_path: Path) -> Optional[bool]:
    """git ls-tree {commit} -- {abs_path}:非空 → True(路径在该 commit 树内)·
    空(rc=0)→ False(未提交)· git 失败/路径越界(rc≠0)→ None(无法判定 · 不阻塞)。"""
    import subprocess
    try:
        abs_path = abs_path.resolve()  # 归一 symlink(macOS /var→/private/var)· 防 git "outside repository"
    except OSError:
        pass
    try:
        r = subprocess.run(
            ["git", "-C", str(repo_dir), "ls-tree", commit, "--", str(abs_path)],
            capture_output=True, text=True, timeout=5,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    if r.returncode != 0:
        return None
    return bool(r.stdout.strip())


def _check_same_stack_preview_project(feature_dir: Path, fm: dict,
                                      auto_commit: Optional[str] = None) -> tuple[bool, str]:
    """v8.58 option B:same-stack 物化 = preview-project 可跑 + preview.sh 存在。
    v8.61:加 auto_commit 校验(治本 v8.58 物化漏洞:磁盘存在但没提交 → ship 丢失)。

    全景权威 = preview-project 源(committed 可跑独立项目)· 预览靠跑 preview.sh 起 dev server
    (动态端口 · 不在 teamwork 层起 server)。校验:
      - panorama_path 声明
      - {panorama_path}/preview-project/ 存在
      - preview-project/preview.sh(预览入口)+ package.json(可跑 JS 项目证据)存在
      - 🔴 上述文件**进了 auto_commit**(传了 auto_commit 时 · git ls-tree 校验 · 防源未提交)
    """
    ppath_raw = fm.get("panorama_path")
    if not ppath_raw:
        return False, (
            "panorama_medium=same-stack · 缺 panorama_path · 声明 "
            "panorama_path={子项目}/docs/design · 在其 preview-project/ 搭同栈可跑项目 + preview.sh。"
            "详 stages/ui-design-stage.md § Panorama 介质类型"
        )
    for proj in _resolve_panorama_subdir(feature_dir, ppath_raw, "preview-project"):
        if proj.is_dir():
            missing = []
            if not (proj / "preview.sh").exists():
                missing.append("preview.sh(预览入口 · 见 templates/preview-project-preview.sh)")
            if not (proj / "package.json").exists():
                missing.append("package.json(可跑项目证据)")
            if missing:
                return False, (
                    f"same-stack preview-project 存在但缺:{' · '.join(missing)} · 目录 {proj} · "
                    "预览靠跑 preview.sh 起 dev server(动态端口)。详 stages/ui-design-stage.md § 预览"
                )
            # v8.61:磁盘存在还不够 · 必须进 auto_commit(治本 v8.58 物化漏洞:
            # same-stack 全景权威 = preview-project 源 · 没提交则 ship 丢失)
            if auto_commit:
                uncommitted = [
                    f for f in ("preview.sh", "package.json")
                    if _path_in_commit(feature_dir, auto_commit, proj / f) is False
                ]
                if uncommitted:
                    return False, (
                        f"same-stack preview-project 文件在磁盘但**未进 auto_commit** "
                        f"{auto_commit[:8]}:{' · '.join(uncommitted)} · `git add {proj}` + commit "
                        f"后重试 —— 全景权威 = preview-project 源 · 未提交则 ship 丢失"
                        f"(治本 v8.58 物化漏洞)。详 stages/ui-design-stage.md § 预览"
                    )
            return True, ""
    return False, (
        f"panorama_medium=same-stack · 需 {ppath_raw}/preview-project/(同栈可跑独立项目 + preview.sh "
        f"+ package.json · 全景权威 = preview-project 源)· 不可只写 UI.md markdown。"
        "预览 = 跑 preview.sh 起 dev server(动态端口 · 不在 teamwork 层起 server)。"
        "详 stages/ui-design-stage.md § 预览"
    )


def _parse_flow_style_dict(s: str) -> Optional[dict]:
    """解析 `{key: value, key: value}` 简易 flow style dict · 失败返 None。

    支持:scalar value(string · 含引号)· list `[a, b, c]`。
    不支持:嵌套 dict / 多行 string。
    用途:teamwork frontmatter 常用 flow style `{k: v, k: v}`(parse_frontmatter
    简易解析器存为 string · 此 helper 在 evidence 检查时局部解析)。
    """
    s = s.strip()
    if not (s.startswith("{") and s.endswith("}")):
        return None
    body = s[1:-1].strip()
    if not body:
        return {}
    # 分割 commas · 跳过引号 / 嵌套括号内的
    parts: list = []
    current = ""
    in_quote: Optional[str] = None
    depth = 0
    for ch in body:
        if in_quote:
            current += ch
            if ch == in_quote:
                in_quote = None
        elif ch in ('"', "'"):
            in_quote = ch
            current += ch
        elif ch in "[{":
            depth += 1
            current += ch
        elif ch in "]}":
            depth -= 1
            current += ch
        elif ch == "," and depth == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += ch
    if current.strip():
        parts.append(current.strip())

    result: dict = {}
    for part in parts:
        if ":" not in part:
            return None
        k, _, v = part.partition(":")
        k = k.strip()
        v = v.strip()
        # 去引号
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            v = v[1:-1]
        elif v.startswith("[") and v.endswith("]"):
            # 简易 list 解析(scalar items)
            inner = v[1:-1].strip()
            if inner:
                items = []
                buf = ""
                iq: Optional[str] = None
                for ch in inner:
                    if iq:
                        buf += ch
                        if ch == iq:
                            iq = None
                    elif ch in ('"', "'"):
                        iq = ch
                        buf += ch
                    elif ch == ",":
                        items.append(buf.strip().strip('"').strip("'"))
                        buf = ""
                    else:
                        buf += ch
                if buf.strip():
                    items.append(buf.strip().strip('"').strip("'"))
                v = items
            else:
                v = []
        result[k] = v
    return result


def _coerce_pages_changed_items(pages_changed: list) -> list:
    """把 pages_changed[] 各项归一为 dict(容错 parse_frontmatter 把 flow style 存为 string)。

    返回归一后 list of dict · 无法解析的 item 保留原值(后续 schema 校验时报错)。
    """
    out: list = []
    for item in pages_changed:
        if isinstance(item, dict):
            out.append(item)
        elif isinstance(item, str):
            parsed = _parse_flow_style_dict(item)
            out.append(parsed if parsed is not None else item)
        else:
            out.append(item)
    return out


def _check_pages_changed_authority(feature_dir: Path, fm: dict,
                                    pages_changed: list) -> tuple[bool, str]:
    """v8.17:校验 pages_changed[].panorama_file 真实存在(全景为权威模式)。

    schema:
      pages_changed:
        - page_id: <str>            # 必 · 对应 frontmatter pages[].id
          panorama_file: <path>     # 必 · 全景权威文件路径(绝对 / 相对仓库根)
          change_range: <str>        # 可选 · 本 Feature 改动描述
          acceptance_criteria_refs:  # 可选 · 关联 AC
            - <AC-id>

    校验:每条 pages_changed[].panorama_file 在 git 仓库内真实存在。
    支持 flow style(`{key: value, ...}`)· parse_frontmatter 把 flow style 存为
    string · 此处 _coerce_pages_changed_items 局部解析为 dict。
    """
    if not pages_changed:
        return False, "pages_changed[] 为空 · 全景为权威模式至少 1 条"

    # 归一 flow style string → dict
    pages_changed = _coerce_pages_changed_items(pages_changed)

    # 算 git 仓库根(相对路径 resolve 用)
    import subprocess
    repo_top = None
    try:
        r = subprocess.run(
            ["git", "-C", str(feature_dir), "rev-parse", "--show-toplevel"],
            capture_output=True, text=True, timeout=5,
        )
        if r.returncode == 0 and r.stdout.strip():
            repo_top = Path(r.stdout.strip())
    except (subprocess.TimeoutExpired, FileNotFoundError, OSError):
        pass

    missing: list = []
    schema_errors: list = []
    for idx, pc in enumerate(pages_changed):
        if not isinstance(pc, dict):
            schema_errors.append(f"pages_changed[{idx}] 不是 dict(也无法解析 flow style)")
            continue
        page_id = pc.get("page_id")
        pf_raw = pc.get("panorama_file")
        if not page_id:
            schema_errors.append(f"pages_changed[{idx}] 缺 page_id")
            continue
        if not pf_raw:
            schema_errors.append(f"pages_changed[{idx}] page_id={page_id!r} 缺 panorama_file")
            continue
        pf_path = Path(pf_raw)
        if not pf_path.is_absolute():
            # 相对路径 · 用 repo_top 算绝对
            if repo_top:
                pf_path = (repo_top / pf_raw).resolve()
            else:
                pf_path = (feature_dir / pf_raw).resolve()  # 兜底
        if not pf_path.exists():
            missing.append(f"{page_id}({pf_raw})")

    if schema_errors:
        return False, "pages_changed[] schema 错误:" + " · ".join(schema_errors)
    if missing:
        return False, (
            f"pages_changed[].panorama_file 不存在: {missing} · "
            f"全景权威文件应在 panorama_path 下 · 检查路径或先建文件"
        )
    return True, ""


UI_DESIGN_SPEC = StageSpec(
    name="ui_design",
    prerequisites=[
        StagePrerequisite(
            id="goal_completed",
            check_fn=_check_stage_output_satisfied("goal"),
            hint="先完成 state.py goal-complete",
            description="goal output_satisfied",
        ),
        StagePrerequisite(
            id="prd_exists",
            check_fn=_check_file_exists("PRD.md"),
            hint="PRD.md 不存在 · 回 goal stage 起草",
            description="{Feature}/PRD.md 必须存在",
        ),
    ],
    artifacts=[
        StageArtifactSpec(
            path="UI.md",
            frontmatter_required=["pages"],
            description="UI 设计稿 · frontmatter pages[] + panorama_medium",
        ),
        # 预览产物由 _evidence_panorama_artifact 按介质条件化校验
        # (same-stack: preview-project+preview.sh · static-html: preview/*.html ≥1)
    ],
    evidence_checks=[
        StageEvidenceCheck(
            name="panorama_artifact",
            check_fn=_evidence_panorama_artifact,
            description="按 panorama_medium 校验:same-stack 要 preview-project+preview.sh · static-html 要 preview/*.html ≥ 1",
        ),
        StageEvidenceCheck(
            name="panorama_changed_decided",
            check_fn=_evidence_panorama_changed_decided,
            description="--panorama-changed 必传(true/false)· 决定下一 stage 是否 panorama_sync",
        ),
    ],
    brief_template_fn=_ui_design_brief,
    auto_transition_fn=_ui_design_transition,
    authorized_pause_point="完成后给用户预览 URL · 等确认",
)


# ─── B2.5 · panorama_sync(conditional · ui_design --panorama-changed=true 时进)─


def _check_panorama_changed_flag(state: dict, args) -> bool:
    """panorama_sync 前置:state.execution_hints.panorama_changed=true。"""
    return state.get("execution_hints", {}).get("panorama_changed") is True


def _evidence_sitemap_updated(state: dict, args) -> tuple[bool, str]:
    """sitemap.md mtime 晚于本 stage started_at(panorama 真被更新 · 治本「声称同步实际没动」)。

    panorama_path 从 UI.md body 的 `> 🔴 panorama_path: <路径>` 行抓(grep-based · 不强 yaml)。
    """
    import re as _re
    from datetime import datetime, timezone
    feature_dir = Path(args.feature)
    ui_md = feature_dir / "UI.md"
    if not ui_md.exists():
        return False, f"UI.md 不存在 · 找不到 panorama_path{_template_hint('UI.md')}"
    text = ui_md.read_text(encoding="utf-8", errors="replace")
    # 只在行首(允许 >, 🔴, 空白前缀)匹配 · 避免 prose 中"不动 panorama_path"类误匹配
    m = _re.search(r"(?:^|\n)[\s>]*🔴?\s*panorama_path[:\s]+(\S+)", text)
    if not m:
        return False, "UI.md 未声明 panorama_path · 无法定位 sitemap.md(在 UI.md 顶部加 `> 🔴 panorama_path: <绝对路径>`)"
    pp = m.group(1).strip().rstrip("/")
    if pp in ("null", "None", "{绝对路径", "(项目无全景)"):
        return False, f"panorama_path={pp!r} · 无效 · panorama_sync stage 不该被进入(应该 panorama_changed=false → blueprint)"
    sitemap = Path(pp) / "sitemap.md"
    if not sitemap.exists():
        return False, f"sitemap.md 不存在: {sitemap}"
    started = state.get("stage_contracts", {}).get("panorama_sync", {}).get("started_at")
    if not started:
        return True, ""  # 无 started_at · skip(不阻塞 · 罕见)
    try:
        started_dt = datetime.strptime(started, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return True, ""
    mtime = datetime.fromtimestamp(sitemap.stat().st_mtime, tz=timezone.utc)
    if mtime < started_dt:
        return False, (
            f"sitemap.md mtime ({mtime.strftime('%Y-%m-%dT%H:%M:%SZ')}) "
            f"早于 panorama_sync stage 开始 ({started}) · 未实际更新(panorama 没动就 complete)"
        )
    return True, ""


def _panorama_sync_brief(state: dict) -> str:
    return f"""## Panorama Sync Stage

### 目标
workspace 级 panorama(sitemap.md / overview.html / 设计 token)同步 ·
反映本 Feature 的 IA 变更 · 跨 Feature reviewer 协调评审。

### 触发
`ui_design-complete --panorama-changed=true` 时自动进入。

### 结果(完成判定)
- `panorama_path/sitemap.md` mtime > 本 stage started_at(panorama 真被更新)
- `panorama-change-summary.md` 存在 · frontmatter 含 reviewers + conclusion + change_level(L1|L2)

### 怎么做
**必读** `stages/panorama-sync-stage.md`(5 substep:加载上下文 / 更新 panorama 单源 /
起草 change-summary + 变更判级 / ⏸️ L2 才暂停(L1 不暂停 · WARN 留痕)/ complete)。

### 完成方式
```
state.py panorama_sync-complete --feature <path> --auto-commit <hash> \\
  --artifacts panorama-change-summary.md
```
"""


def _panorama_sync_transition(state: dict) -> Optional[str]:
    """panorama_sync 完成后 → blueprint(Feature) / blueprint_lite(敏捷需求 · 保险)。"""
    flow = state.get("flow_type")
    if flow == "敏捷需求":
        return "blueprint_lite"
    return "blueprint"


PANORAMA_SYNC_SPEC = StageSpec(
    name="panorama_sync",
    prerequisites=[
        StagePrerequisite(
            id="ui_design_completed",
            check_fn=_check_stage_output_satisfied("ui_design"),
            hint="先完成 state.py ui_design-complete --panorama-changed=true",
            description="ui_design output_satisfied",
        ),
        StagePrerequisite(
            id="panorama_changed_flag_true",
            check_fn=_check_panorama_changed_flag,
            hint=(
                "state.execution_hints.panorama_changed != true · 不该进 panorama_sync(应 → blueprint)· "
                "ui_design-complete 时漏传或传错 --panorama-changed?"
            ),
            description="execution_hints.panorama_changed=true",
        ),
    ],
    artifacts=[
        StageArtifactSpec(
            path="panorama-change-summary.md",
            frontmatter_required=["reviewers", "conclusion", "change_level"],
            body_min_lines=8,
            description="panorama 变更摘要 · 列变更/受影响 Features/协调结论 · change_level: L1|L2 判级留痕",
        ),
    ],
    evidence_checks=[
        StageEvidenceCheck(
            name="sitemap_updated",
            check_fn=_evidence_sitemap_updated,
            description="sitemap.md mtime > stage started_at(panorama 真被更新)",
        ),
    ],
    brief_template_fn=_panorama_sync_brief,
    auto_transition_fn=_panorama_sync_transition,
    authorized_pause_point=(
        "条件暂停:L2(节点增删移/路由/token/共享视觉基线变更 或 跨 Feature 冲突命中)"
        "需 reviewer 评审 + owner 协调确认;L1(节点内增量 · 三判据全过)不暂停 · WARN 留痕自动继续"
    ),
)


# ─── B3 · (Feature Planning 不进状态机 · 详 docs/feature-planning.md) ──


# ─── B4 · blueprint ─────────────────────────────────────────────────


def _blueprint_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Blueprint Stage

### 目标
QA 起草 TC(BDD) · RD 起草 TECH · 架构师 + External 多视角评审 · 实现前方案收敛。

### 结果(完成判定)
- `TC.md`(frontmatter:`tests` · verify-ac.py 通过)
- `TECH.md`(§模块 / §数据 / §接口 / §依赖 / §风险)
- `TECH-REVIEW.md`(frontmatter:`reviewer + verdict`)
- `{{artifact_root}}/external-cross-review/*.md`(至少 1 份)

### 怎么做
**必读** `stages/blueprint-stage.md`(详细步骤 + §7.5 DB schema 条件暂停点)。

🔴 **TECH 方案涉及数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration)·
blueprint-complete 前必 emit R5 用户确认暂停点(stage.md §7.5)· 不涉及则跳过。

### 完成方式
```
state.py blueprint-complete --feature <path> --auto-commit <hash> \
  --artifacts TC.md,TECH.md,TECH-REVIEW.md
```
"""


def _blueprint_transition(state: dict) -> Optional[str]:
    return "dev"


def _evidence_ac_test_binding(state: dict, args) -> tuple[bool, str]:
    """跑 verify-ac.py 校验 AC↔Test 绑定。

    v8.0+P0-14:verify-ac.py 不存在时 silent skip(install/dev sync 不影响校验)。
    v8.x:Bug / Micro 流程不产 PRD/TC(规格 = bugfix/BUG-*.md / 直改)· skip 校验。
        治本 case INFRA-B002:Bug 流程撞 ac_test_binding 门禁 = Feature 门禁泄漏。
    """
    flow_type = state.get("flow_type", "")
    if flow_type in ("Bug", "Micro"):
        return True, f"skipped({flow_type} 流程无 PRD/TC · 规格 = bugfix/BUG-*.md 或直改)"

    feature_dir = Path(args.feature)
    prd = feature_dir / "PRD.md"
    tc = feature_dir / "TC.md"
    if not prd.exists() or not tc.exists():
        return False, (
            f"PRD.md 或 TC.md 不存在 · 路径 prd={prd} tc={tc}"
            f"{_template_hint('PRD.md')}{_template_hint('TC.md')}"
        )

    # 查找 verify-ac.py(SKILL_ROOT/templates/verify-ac.py)
    import subprocess
    skill_root = Path(__file__).resolve().parent.parent
    verify_script = skill_root / "templates" / "verify-ac.py"
    if not verify_script.exists():
        # silent skip(install 位置可能未同步 dev · 不阻塞)
        return True, ""

    try:
        result = subprocess.run(
            ["python3", str(verify_script), "--prd", str(prd), "--tc", str(tc)],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode != 0:
            # 区分 verify-ac.py 自身 bug vs 真校验失败
            stderr = result.stderr.strip()[:300]
            stdout = result.stdout.strip()[:300]
            if "PRD.md 不存在" in stdout + stderr and prd.exists():
                # verify-ac.py 自身 placeholder 残留 bug · silent skip
                return True, ""
            return False, f"verify-ac.py FAIL · stdout={stdout!r} stderr={stderr!r}"
        return True, ""
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        return False, f"verify-ac.py 执行失败: {e}"


# v8.19:external review 异质性硬约束(治本 SVC-CORE-F034 case · AI 用同模型 subagent 自审)
# 白名单:已知模型族字面(case-insensitive · host-aware 判定时 host 同族会被排除)
EXTERNAL_REVIEW_HETERO_KEYWORDS = (
    "claude", "anthropic", "codex", "gpt", "openai", "gemini", "google", "bard",
    "deepseek", "qwen", "llama", "grok", "mistral",
)
# 同源「机制」字面:宿主自起 isolated/subagent 子进程 = 同模型自审 · 无论 host 全 BLOCK
EXTERNAL_REVIEW_SAME_CONTEXT_BLOCKED = (
    "isolated", "subagent", "general-purpose", "self",
)
# 各模型族字面(host-aware 同源判定:review model 与 host 同族 → 同源)
_MODEL_FAMILY_KEYWORDS = {
    "claude": ("claude", "anthropic"),
    "codex": ("codex", "gpt", "openai"),
    "gemini": ("gemini", "google", "bard"),
}
# 向后兼容别名(老引用 · = 默认 claude host 下的同源字面集)
EXTERNAL_REVIEW_SAME_SOURCE_BLOCKED = (
    _MODEL_FAMILY_KEYWORDS["claude"] + EXTERNAL_REVIEW_SAME_CONTEXT_BLOCKED
)


def _host_to_family(host) -> Optional[str]:
    """host → 模型族:claude-code→claude / codex-cli→codex / gemini-cli→gemini · 未知→None。"""
    h = (host or "").lower()
    if "claude" in h:
        return "claude"
    if "codex" in h or "openai" in h:
        return "codex"
    if "gemini" in h or "google" in h:
        return "gemini"
    return None


def _check_external_hetero(name: str, host=None) -> tuple[bool, str]:
    """v8.68:host-aware 校验文件名 / review_model 是否真异质模型 · 返 (is_hetero, reason)。

    治本 case(SVC-PLATFORM-F060 · host=codex-cli):external-review 已 host-aware
    (`EXTERNAL_HOST_TO_MODEL` codex-cli→claude)· 但本 checker 旧版**静态**黑名单把 claude
    一律判同源 → **误判** codex-cli 宿主下合规的 Claude external review = 同源自审。

    同源 = ① 机制字面(isolated/subagent 宿主自起子进程 · 无论 host 全 BLOCK)· 或
    ② review model 与 host **同族**(codex-cli host 下 claude 是异质 · 不再误判)。
    host 缺失 → 保守默认 claude-code(历史默认 · 不放宽老 case 的同源保护)。
    """
    low = name.lower()
    # 1. 同源机制黑名单(无论 host · subagent/isolated 是宿主自起子进程 · 非真异质进程)
    for kw in EXTERNAL_REVIEW_SAME_CONTEXT_BLOCKED:
        if kw in low:
            return False, f"命中同源机制字面 {kw!r}(宿主自起 isolated/subagent 自审 · 非异质进程)"
    # 2. host-aware 同源模型族(host 缺失 → 保守默认 claude)
    host_family = _host_to_family(host) or "claude"
    for kw in _MODEL_FAMILY_KEYWORDS.get(host_family, ()):
        if kw in low:
            return False, (
                f"命中宿主同源模型族字面 {kw!r}(host={host or '默认 claude-code'}/"
                f"{host_family} · 同模型评同模型 = 非异质)"
            )
    # 3. 必含某已知外部模型族字面 → 真异质
    for kw in EXTERNAL_REVIEW_HETERO_KEYWORDS:
        if kw in low:
            return True, ""
    return False, (
        f"未含已知模型族字面(白名单:{', '.join(EXTERNAL_REVIEW_HETERO_KEYWORDS)})"
    )


def _external_run_log_exists(feature_dir: Path, stage: str) -> bool:
    """v8.67:本 stage external 评审有「实跑证据」—— v8.55 _log_external_run 在
    ~/.teamwork/external-review-logs/<feat>/ 落的 codex-<stage>-*.log / claude-<stage>-*.log。
    用于 yolo 校验 external 真调了异质模型(不是 AI 手写/内化 external-cross-review)。"""
    feat_name = feature_dir.name or "unknown"
    log_dir = Path.home() / ".teamwork" / "external-review-logs" / feat_name
    if not log_dir.is_dir():
        return False
    for model in ("codex", "claude"):
        if list(log_dir.glob(f"{model}-{stage}-*.log")):
            return True
    return False


def _localconfig_disable_hetero(feature_dir: Path) -> bool:
    """v8.90:读 localconfig `disable_heterogeneous_review`(向上找到 .git 边界 · 默认 false)。

    内联实现(避免 _v8_stage_specs 循环 import state.py)· 与 state._read_disable_heterogeneous_review 同义。
    """
    import json as _json
    try:
        node = Path(feature_dir).resolve()
    except OSError:
        return False
    for d in [node, *node.parents]:
        cfg = d / ".teamwork_localconfig.json"
        if cfg.exists():
            try:
                return _json.loads(cfg.read_text(encoding="utf-8")).get(
                    "disable_heterogeneous_review") is True
            except (OSError, ValueError):
                return False
        if (d / ".git").exists():
            break
    return False


def _evidence_external_review_artifact(state: dict, args) -> tuple[bool, str]:
    """external-cross-review/ 至少 1 份 markdown · 且必须是真异质模型评审(v8.19 加强)。

    v8.90:`disable_heterogeneous_review:true`(localconfig · 单模型用户)时 · 接受
    external-review 写的**降级同模型自审**文件(frontmatter `degraded:true heterogeneous:false`)·
    跳过异质违规(用户已 opt-out · bootstrap 每次启动 WARN 持续提醒)。详 standards §11。

    联动 state.stage_review_roles:若当前 stage 的 reviewers 列表不含 'external'
    (通过 change-review-roles 调整去除) → skip 校验(audit 已在 stage_review_roles_adjustments)。

    v8.0+P0-14:external-cross-review/ 在 artifact_root 内(feature_dir 内 · 不是 parent)。
    v8.19 治本 SVC-CORE-F034 case:加文件名 + frontmatter review_model 双重校验 ·
    BLOCKED "AI 用 Agent subagent_type=general-purpose 起 Claude isolated context 自审 ·
    再标 review_model: claude-opus-4-isolated-context 透明伪装合规" 的反模式。
    硬约束源:standards/external-model-usage.md § 七 异质性硬约束。
    """
    current_stage = state.get("current_stage", "")
    stage_roles = state.get("stage_review_roles", {}).get(current_stage, [])
    if stage_roles and "external" not in stage_roles:
        return True, (
            f"skipped(external 不在 state.stage_review_roles.{current_stage}={stage_roles} · "
            f"已通过 change-review-roles 调整 · audit 详 state.stage_review_roles_adjustments)"
        )

    feature_dir = Path(args.feature)
    external_dir = feature_dir / "external-cross-review"
    if not external_dir.exists():
        return False, f"external-cross-review/ 不存在 · 路径:{external_dir}"
    md_files = list(external_dir.glob("*.md"))
    if not md_files:
        return False, (
            "external-cross-review/*.md 为空 · 跑 codex 外部评审或 change-review-roles 移除 external"
        )

    # v8.90:单模型用户 localconfig 禁异质 → 接受 external-review 写的降级同模型自审(跳过异质违规)
    het_disabled = _localconfig_disable_hetero(feature_dir)
    # v8.36 host per-feature · v8.68 host-aware 异质判定(治本 codex-cli host 下 claude 误判)
    state_host = state.get("host")
    # v8.19:逐文件校验异质性(文件名 + frontmatter review_model 双重 · v8.68 host-aware)
    violations: list = []
    for f in md_files:
        fm = parse_frontmatter(f) or {}
        # v8.90:config-disabled 项目 + 文件是合规降级自审(external-review 写 degraded:true
        # heterogeneous:false)→ 视作满足门禁(用户已 opt-out · startup WARN 持续提醒)· 跳过异质校验。
        # 注:parse_frontmatter 是朴素解析 · 值为字符串("true"/"false")。
        deg = (str(fm.get("degraded", "")).lower() == "true"
               and str(fm.get("heterogeneous", "")).lower() == "false")
        # v8.90:config-disabled 项目(het_disabled=true)→ 接受任何 degraded 自审(用户已 opt-out)。
        # v8.108:per-run subagent 降级(frontmatter degraded_mode=subagent-fallback)→ 接受(显式降级 ·
        # 即便项目未 opt-out · 因为是 --self-review-fallback 带 reason 的诚实降级)· 非异质 · 满足 P0-154。
        # 🔴 config-disabled marker 仍须 het_disabled 为真(防未 opt-out 项目用 stale config-disabled 标绕过);
        # 无 degraded marker / 非 subagent-fallback → 落下方黑名单(F034 伪装拦)。
        if deg and (het_disabled
                    or str(fm.get("degraded_mode", "")).lower() == "subagent-fallback"):
            continue
        # host 优先级:state.host(per-feature)> 文件 frontmatter host(external-review 写)> None(默认 claude)
        eff_host = state_host or (fm.get("host") or "").strip() or None
        ok_name, name_reason = _check_external_hetero(f.stem, eff_host)
        rm_value = (fm.get("review_model") or "").strip()
        rm_ok, rm_reason = True, ""
        if rm_value:
            rm_ok, rm_reason = _check_external_hetero(rm_value, eff_host)
        if not ok_name:
            violations.append(f"{f.name}:文件名 {name_reason}")
        if rm_value and not rm_ok:
            violations.append(f"{f.name}:frontmatter review_model={rm_value!r} {rm_reason}")

    if violations:
        # v8.95:het_disabled 项目的违规 = 文件缺降级标记(多半 AI 手写没打标)· 给**专属**修复指引
        # (不要走通用「调异质模型」分支 —— 那对单模型 opt-out 用户误导 · 正与 v8.90 初衷相悖)。
        if het_disabled:
            fix_section = (
                "\n  🔴 修复(本项目 `disable_heterogeneous_review=true` · 单模型 opt-out):"
                "external-cross-review 文件**缺降级标记** → 被判同源。"
                "\n  正解 = 跑 `state.py external-review --stage "
                f"{current_stage} --feature {args.feature}` —— config-disabled 模式会**自动**产出 "
                "`degraded:true heterogeneous:false` 的降级同模型自审(被门禁接受)· **别手写**"
                "(手写没实跑标记 · 看起来像伪造 → 拦)。"
                "\n  或给现有 external-cross-review/*.md 补 `degraded: true` + `heterogeneous: false` "
                "两个 frontmatter 键(注:写在 external-cross-review 文件里 · 不是 REVIEW.md)。"
                "\n  想恢复真异质把关 → 删 localconfig 的 `disable_heterogeneous_review`。"
            )
        else:
            fix_section = (
                "\n  规约(v8.68 host-aware):同源 = ① isolated/subagent 等机制字面(全 host BLOCK)· "
                "或 ② review model 与**宿主同族**(claude-code 宿主下 claude 同源 · "
                "**codex-cli 宿主下 claude 是异质 · 合规**)。"
                "\n  典型违规:AI 用 Agent subagent_type=general-purpose 起同模型 isolated context 自审 → 同模型自评有盲点。"
                "\n  修复:跑 `state.py external-review --stage <X> --feature <path>`"
                "(host 自动映射异质模型:claude-code→codex · codex-cli→claude · gemini-cli→codex)· "
                "或 change-review-roles 显式移除 external(留 audit)。"
                "\n  🔴 若本就是合规异质评审却被判违规 → 检查 state.json.host 是否 = 你的真实主对话宿主"
                "(host 错 / 缺 默认 claude · 会把 codex-cli 的 claude 评审误判同源)。"
            )
        return False, (
            f"external 异质性违规({len(violations)} 文件)· R3 红线 + standards/"
            f"external-model-usage.md § 七 异质性硬约束:\n  "
            + "\n  ".join(violations)
            + fix_section
        )

    # v8.67:yolo 严格按流程 · 不内化 —— external 必须真跑(state.py external-review 调异质模型)·
    # 不得 AI 手写 external-cross-review/*.md(文件名/frontmatter 能伪装合规 · 但无实跑日志)。
    # 治本 case(WS-002 yolo):AI 写 PRD-REVIEW "mode: yolo-internalized" 自盖章 APPROVE · 评审形同虚设。
    if state.get("yolo") and not _external_run_log_exists(feature_dir, current_stage):
        return False, (
            f"yolo 模式 external 评审缺**实跑证据** —— ~/.teamwork/external-review-logs/"
            f"{feature_dir.name}/ 无本 stage 日志(codex-{current_stage}-*.log / "
            f"claude-{current_stage}-*.log)。🔴 yolo 严格按流程 · **不得手写/内化** "
            f"external-cross-review/*.md —— 必须真跑 `state.py external-review --stage "
            f"{current_stage} --feature {args.feature}`(调异质模型 · v8.55 自动落实跑日志)。"
            f"\n  (artifact 文件名/frontmatter 能伪装合规 · 但实跑日志伪造不了 · 这是物化防内化)"
        )
    return True, ""


BLUEPRINT_SPEC = StageSpec(
    name="blueprint",
    prerequisites=[
        StagePrerequisite(
            id="goal_completed",
            check_fn=_check_stage_output_satisfied("goal"),
            hint="先完成 state.py goal-complete",
            description="goal output_satisfied",
        ),
        StagePrerequisite(
            id="prd_exists",
            check_fn=_check_file_exists("PRD.md"),
            hint="PRD.md 不存在 · 回 goal stage 起草",
            description="{Feature}/PRD.md 必须存在",
        ),
    ],
    artifacts=[
        # 文档类 artifact 多角色多 commit 是常态(QA 写 TC / RD 写 TECH / 评审改 TECH-REVIEW)·
        # must_be_in_commit=False 防 AI 被迫 git reset --soft squash;ship R-S7 保证最终 commit。
        StageArtifactSpec(
            path="TC.md",
            frontmatter_required=["tests"],
            must_be_in_commit=False,
            description="测试用例 · AC↔Test 绑定",
        ),
        StageArtifactSpec(
            path="TECH.md",
            must_be_in_commit=False,
            description="技术方案",
        ),
        StageArtifactSpec(
            path="TECH-REVIEW.md",
            frontmatter_required=["reviewers", "verdict"],  # reviewers 复数 · 对齐 reviewers_match evidence
            must_be_in_commit=False,
            description="架构师 Tech Review verdict",
        ),
    ],
    evidence_checks=[
        StageEvidenceCheck(
            name="ac_test_binding",
            check_fn=_evidence_ac_test_binding,
            description="AC↔Test 全覆盖(verify-ac.py 通过)",
        ),
        StageEvidenceCheck(
            name="external_review_artifact",
            check_fn=_evidence_external_review_artifact,
            description="external-cross-review/*.md 至少 1 份",
        ),
        # v8.0+P0-9:TECH-REVIEW.md reviewers 必含 state.stage_review_roles[blueprint]
        StageEvidenceCheck(
            name="reviewers_match",
            check_fn=_evidence_reviewers_match("TECH-REVIEW.md"),
            description="TECH-REVIEW.md frontmatter.reviewers 必含 state.stage_review_roles[blueprint]",
        ),
    ],
    brief_template_fn=_blueprint_brief,
    auto_transition_fn=_blueprint_transition,
    authorized_pause_point="无暂停 · 完成后自动转 dev(NEEDS_REVISION 主对话内 PM 回应循环)",
)


# ─── B5 · blueprint_lite(仅敏捷需求) ─────────────────────────────


def _check_flow_is_agile(state: dict, args) -> bool:
    return state.get("flow_type") == "敏捷需求"


def _blueprint_lite_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Blueprint Lite Stage

### 目标
敏捷需求精简版 blueprint · 只产 TC.md(精简) · 砍 TECH/TECH-REVIEW/External。

### 结果(完成判定)
- `TC.md`(frontmatter:`tests` · 每 AC 至少 1 test)

### 怎么做
**必读** `stages/blueprint-lite-stage.md`(详细步骤 4 步 + 注意事项 5 条 · 含敏捷准入校验)。

### 完成方式
```
state.py blueprint_lite-complete --feature <path> --auto-commit <hash> \
  --artifacts TC.md
```
"""


def _blueprint_lite_transition(state: dict) -> Optional[str]:
    return "dev"


BLUEPRINT_LITE_SPEC = StageSpec(
    name="blueprint_lite",
    prerequisites=[
        StagePrerequisite(
            id="flow_type_is_agile",
            check_fn=_check_flow_is_agile,
            hint="blueprint_lite 仅敏捷需求流程触发 · 检查 state.flow_type",
            description="flow_type == '敏捷需求'",
        ),
        StagePrerequisite(
            id="goal_completed",
            check_fn=_check_stage_output_satisfied("goal"),
            hint="先完成 state.py goal-complete",
            description="goal output_satisfied",
        ),
        StagePrerequisite(
            id="prd_exists",
            check_fn=_check_file_exists("PRD.md"),
            hint="PRD.md 不存在 · 回 goal stage 起草",
            description="{Feature}/PRD.md 必须存在",
        ),
    ],
    artifacts=[
        StageArtifactSpec(
            path="TC.md",
            frontmatter_required=["tests"],
            description="精简版测试用例",
        ),
    ],
    evidence_checks=[],  # 敏捷需求不强制 verify-ac.py
    brief_template_fn=_blueprint_lite_brief,
    auto_transition_fn=_blueprint_lite_transition,
    allowed_flow_types=["敏捷需求"],
    authorized_pause_point="无暂停 · 完成后自动转 dev",
)


# ─── B7 · review ───────────────────────────────────────────────────


def _check_dev_test_passed(state: dict, args) -> bool:
    """dev 的 evidence.test_exit_code == 0(防带 bug 进 review)"""
    dev_contract = state.get("stage_contracts", {}).get("dev", {})
    if dev_contract.get("output_satisfied") is not True:
        return False
    # v8 evidence 字段保存在 stage_contracts.dev.evidence(由 dev-complete 写入)
    ev = dev_contract.get("evidence", {})
    return ev.get("test_exit_code") == 0


def _review_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Review Stage

### 目标
三视角独立评审(Architect + QA + External 异质模型)· 收敛 verdict。

### 结果(完成判定)
- `REVIEW.md`(frontmatter:`reviewers + verdict: APPROVE|NEEDS_REVISION`)
- `REVIEW-arch.md` + `REVIEW-qa.md`
- `{{artifact_root}}/external-cross-review/*.md`(至少 1 份)

### 怎么做
**必读** `stages/review-stage.md`(详细步骤 6 步 + 注意事项 5 条)。

### 完成方式
```
state.py review-complete --feature <path> --auto-commit <hash> \
  --artifacts REVIEW.md,REVIEW-arch.md,REVIEW-qa.md \
  --verdict {{APPROVE|NEEDS_REVISION}}
```
"""


def _review_transition(state: dict) -> Optional[str]:
    """按 verdict 转移:APPROVE → test · NEEDS_REVISION → None(留 review · 走 fix-retry)。

    NEEDS_REVISION 不切 stage · 由 RD 走 review-fix + review-retry 在 review 内循环。
    review-fix 记录 fix commit · review-retry 加新 round 重置 gates · review-complete 写 verdict。
    完整 spec 见 stages/review-stage.md § fix-retry 循环。
    """
    review_contract = state.get("stage_contracts", {}).get("review", {})
    verdict = review_contract.get("evidence", {}).get("verdict")
    if verdict == "APPROVE":
        return "test"
    return None  # NEEDS_REVISION · 留 review-stage 走 fix-retry 循环


def _evidence_review_verdict(state: dict, args) -> tuple[bool, str]:
    """校验 --verdict 已落入 state(complete 时 stash 到 evidence)"""
    verdict = getattr(args, "verdict", None)
    if verdict not in ("APPROVE", "NEEDS_REVISION"):
        return False, f"--verdict 必须是 APPROVE 或 NEEDS_REVISION · got {verdict!r}"
    # 同时把 verdict 写入 stage_contracts.review.evidence
    contracts = state.setdefault("stage_contracts", {})
    review_c = contracts.setdefault("review", {})
    ev = review_c.setdefault("evidence", {})
    ev["verdict"] = verdict
    return True, ""


REVIEW_SPEC = StageSpec(
    name="review",
    prerequisites=[
        StagePrerequisite(
            id="dev_completed",
            check_fn=_check_stage_output_satisfied("dev"),
            hint="先完成 state.py dev-complete",
            description="dev output_satisfied",
        ),
        StagePrerequisite(
            id="dev_test_passed",
            check_fn=_check_dev_test_passed,
            hint="dev 测试未通过(evidence.test_exit_code != 0)· 回 dev stage 修",
            description="dev evidence.test_exit_code == 0",
        ),
    ],
    artifacts=[
        # review 三视角评审多 commit 是常态(architect/qa/external 各自落 commit)·
        # 强制单 commit 会导致 AI git reset --soft 揉碎 audit 颗粒度。
        StageArtifactSpec(
            path="REVIEW.md",
            frontmatter_required=["reviewers", "verdict"],
            must_be_in_commit=False,
            description="评审总结",
        ),
        StageArtifactSpec(
            path="REVIEW-arch.md",
            must_be_in_commit=False,
            description="架构师评审",
        ),
        StageArtifactSpec(
            path="REVIEW-qa.md",
            must_be_in_commit=False,
            description="QA 评审",
        ),
    ],
    evidence_checks=[
        StageEvidenceCheck(
            name="review_verdict",
            check_fn=_evidence_review_verdict,
            description="--verdict 必须是 APPROVE 或 NEEDS_REVISION",
        ),
        StageEvidenceCheck(
            name="external_review_artifact",
            check_fn=_evidence_external_review_artifact,
            description="external-cross-review/*.md 至少 1 份(v7.3.10+P0-154 沿用)",
        ),
        # v8.0+P0-9:REVIEW.md reviewers 必含 state.stage_review_roles[review]
        StageEvidenceCheck(
            name="reviewers_match",
            check_fn=_evidence_reviewers_match("REVIEW.md"),
            description="REVIEW.md frontmatter.reviewers 必含 state.stage_review_roles[review]",
        ),
    ],
    brief_template_fn=_review_brief,
    auto_transition_fn=_review_transition,
    authorized_pause_point="verdict=NEEDS_REVISION 时 · 用户选回 dev 还是接受",
)


# ─── B8 · test ─────────────────────────────────────────────────────


def _check_review_approved(state: dict, args) -> bool:
    """review 已完成且 verdict=APPROVE"""
    rc = state.get("stage_contracts", {}).get("review", {})
    if rc.get("output_satisfied") is not True:
        return False
    return rc.get("evidence", {}).get("verdict") == "APPROVE"


def _test_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。

    v8.111:按 flow_type 分支 —— Bug 流程无 PRD/TC(规格 = bugfix/BUG-*.md)·
    不能列「verify-ac.py 通过 / AC 全覆盖」(门禁对 Bug 自动 skip · brief 若列出
    = 假信号 · 实证有 agent 照着去跑 verify-ac.py 撞 PRD 不存在)。
    """
    if state.get("flow_type") == "Bug":
        return """## Test Stage(Bug 流程)

### 目标
QA 回归验证 —— **复现 bug 的用例修复后转绿** + 既有套件保持绿 · 防 fix 引入回归。

### 结果(完成判定)
- `TEST-REPORT.md`(记:复现用例 → 修复后 PASS · 既有套件结果 · 关联 BUG-*.md §回归测试)
- `e2e/*`(至少 1 文件 · 复跑触发 bug 的关键路径 · 语言无关)
- integration + e2e exit-code = 0
- 🚫 **无 PRD/TC → verify-ac / AC 全覆盖 N/A**(门禁对 Bug 自动 skip · 不要去跑 verify-ac.py · 规格依据是 BUG-*.md)

### 怎么做
**必读** `stages/test-stage.md`(详细步骤 + 注意事项 · 含 Bug 无 PRD/TC 分支)。

### 完成方式
```
state.py test-complete --feature <path> --auto-commit <hash> \
  --artifacts TEST-REPORT.md,e2e/ \
  --integration-test-exit-code 0 --e2e-test-exit-code 0
```
"""
    return f"""## Test Stage

### 目标
QA 集成测试 + API E2E · AC 全覆盖最终验证。

### 结果(完成判定)
- `TEST-REPORT.md`
- `e2e/*`(至少 1 文件 · 语言无关)
- integration + e2e exit-code = 0
- verify-ac.py 通过

### 怎么做
**必读** `stages/test-stage.md`(详细步骤 7 步 + 注意事项 5 条 · 含 skip 走捷径反模式)。

### 完成方式
```
state.py test-complete --feature <path> --auto-commit <hash> \
  --artifacts TEST-REPORT.md,e2e/ \
  --integration-test-exit-code 0 --e2e-test-exit-code 0
```
"""


def _test_transition(state: dict) -> Optional[str]:
    """test 通过(两 exit_code 都 0)→ next stage · 失败 → None(留 test 走 fix-retry · v8.10)。"""
    test_c = state.get("stage_contracts", {}).get("test", {})
    ev = test_c.get("evidence", {})
    int_code = ev.get("integration_test_exit_code")
    e2e_code = ev.get("e2e_test_exit_code")
    if int_code != 0 or e2e_code != 0:
        return None  # 失败 · 留 test stage · 走 test-fix → test-retry
    hints = state.get("execution_hints", {})
    if hints.get("browser_e2e_needed") is True:
        return "browser_e2e"
    return "pm_acceptance"


def _evidence_integration_test_present(state: dict, args) -> tuple[bool, str]:
    """v8.10:只校验 --integration-test-exit-code 已传 · 任何 exit_code 都允许 ·
    失败时 transition 返 None(留 test 走 fix-retry)而不是 die FAIL。"""
    code = getattr(args, "integration_test_exit_code", None)
    if code is None:
        return False, "缺 --integration-test-exit-code 参数"
    return True, ""


def _evidence_e2e_test_present(state: dict, args) -> tuple[bool, str]:
    """v8.10:只校验 --e2e-test-exit-code 已传 · 任何 exit_code 都允许。"""
    code = getattr(args, "e2e_test_exit_code", None)
    if code is None:
        return False, "缺 --e2e-test-exit-code 参数"
    return True, ""


TEST_SPEC = StageSpec(
    name="test",
    prerequisites=[
        StagePrerequisite(
            id="review_approved",
            check_fn=_check_review_approved,
            hint="review 未通过(verdict != APPROVE)· 回 review stage 处理 QUALITY_ISSUE",
            description="review verdict == APPROVE",
        ),
    ],
    artifacts=[
        StageArtifactSpec(
            path="TEST-REPORT.md",
            description="测试报告",
        ),
        StageArtifactSpec(
            glob="e2e/*",
            min_files=1,
            must_be_in_commit=False,
            description="API E2E 脚本(语言无关)",
        ),
    ],
    evidence_checks=[
        StageEvidenceCheck(
            name="integration_test_present",
            check_fn=_evidence_integration_test_present,
            description="--integration-test-exit-code 已传(失败 exit_code 留 test stage 走 fix-retry)",
        ),
        StageEvidenceCheck(
            name="e2e_test_present",
            check_fn=_evidence_e2e_test_present,
            description="--e2e-test-exit-code 已传(失败 exit_code 留 test stage 走 fix-retry)",
        ),
        StageEvidenceCheck(
            name="ac_test_binding",
            check_fn=_evidence_ac_test_binding,
            description="AC↔Test 全覆盖(verify-ac.py 通过)",
        ),
    ],
    brief_template_fn=_test_brief,
    auto_transition_fn=_test_transition,
    authorized_pause_point="无暂停 · 按 browser_e2e_needed 决定下一步",
)


# ─── B9 · browser_e2e(可选) ───────────────────────────────────────


def _browser_e2e_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Browser E2E Stage

### 目标
浏览器端 E2E 测试 + 截图证据(仅 `state.execution_hints.browser_e2e_needed=true` 启用)。

### 结果(完成判定)
- `screenshots/*.png`(至少 1 张 · 每 AC 一组关键路径截图)
- `BROWSER-TEST-REPORT.md`

### 怎么做
**必读** `stages/browser-e2e-stage.md`(详细步骤 6 步 + 注意事项 5 条)。

### 完成方式
```
state.py browser_e2e-complete --feature <path> --auto-commit <hash> \
  --artifacts screenshots/,BROWSER-TEST-REPORT.md
```
"""


def _browser_e2e_transition(state: dict) -> Optional[str]:
    return "pm_acceptance"


BROWSER_E2E_SPEC = StageSpec(
    name="browser_e2e",
    prerequisites=[
        StagePrerequisite(
            id="test_completed",
            check_fn=_check_stage_output_satisfied("test"),
            hint="先完成 state.py test-complete",
            description="test output_satisfied",
        ),
    ],
    artifacts=[
        StageArtifactSpec(
            glob="screenshots/*.png",
            min_files=1,
            must_be_in_commit=False,
            description="浏览器测试截图",
        ),
        StageArtifactSpec(
            path="BROWSER-TEST-REPORT.md",
            description="浏览器测试报告",
        ),
    ],
    evidence_checks=[],
    brief_template_fn=_browser_e2e_brief,
    auto_transition_fn=_browser_e2e_transition,
    authorized_pause_point="完成后给用户截图 · 等确认",
)


# ─── B10 · pm_acceptance ──────────────────────────────────────────


def _pm_acceptance_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## PM Acceptance Stage

### 目标
PM 站在用户视角逐条 AC 对照实现 · 验收后 **emit 三选项暂停点 · 用户拍板 decision**。

### 🔴 decision 是用户决策点(R5)· AI 不可自决
- PM 角色只做 AC 验收 + emit 三选项 markdown · 然后**停** · 等用户回 1/2/3
- 三选项(approved_and_ship / approved_no_ship / rejected_with_feedback)都是决策 ·
  哪怕选"保守"的 `approved_no_ship` 也是越权(它让 Feature 跳过 ship 直接 completed)
- "避免未授权 push" 不构成自选 `approved_no_ship` 的理由 ——
  `approved_and_ship` 进 ship 后 · Phase 1 仍有"等用户平台合并"暂停点 · push 不会自动发生

### 结果(完成判定)
- `state.stage_contracts.pm_acceptance.evidence.decision` 已落库(= 用户所选)
- (rejected_with_feedback 时)`--note` 含具体 finding

### 怎么做
**必读** `stages/pm-acceptance-stage.md`。

### 完成方式(用户拍板后才跑)
```
state.py pm_acceptance-complete --feature <path> --auto-commit <hash> \
  --decision {{用户所选}} --note "<rejected 时必填>"
```
"""


def _pm_decision_value(pm_c: dict):
    """读 pm_acceptance decision · **容错读两个 schema 位**:
    - v8 规范位:`evidence.decision`(`pm_acceptance-complete --decision` / `_evidence_pm_decision` 写处)
    - 旧位:contract 顶层 `decision`(v7 `cmd_pm_decision` 写处 · 或 v7→v8 migrate 漏迁的遗留)

    治本:已迁移的老 Feature 卡在旧位 → ship 门禁误判「PM 没批」(ADMIN-F013 case)。
    migrate-v7-to-v8 已补迁逻辑(后续迁移不漏)· 但 schema_version==v8 的已迁 Feature
    不会重迁,只能靠 reader 容错追溯性修好。
    """
    return pm_c.get("evidence", {}).get("decision") or pm_c.get("decision")


def _pm_acceptance_transition(state: dict) -> Optional[str]:
    """按 decision 转移。"""
    pm_c = state.get("stage_contracts", {}).get("pm_acceptance", {})
    decision = _pm_decision_value(pm_c)
    if decision == "approved_and_ship":
        return "ship"
    if decision == "approved_no_ship":
        return "completed"  # 不进 ship · 直接终态
    # rejected_with_feedback → None(暂停 · 用户选回 dev 还是放弃)
    return None


def _evidence_pm_decision(state: dict, args) -> tuple[bool, str]:
    """校验 --decision 合法 + 落 evidence"""
    decision = getattr(args, "decision", None)
    valid = ("approved_and_ship", "approved_no_ship", "rejected_with_feedback")
    if decision not in valid:
        return False, f"--decision 必须 ∈ {valid} · got {decision!r}"

    note = getattr(args, "note", "") or ""
    if decision == "rejected_with_feedback" and not note.strip():
        return False, "rejected_with_feedback 时 --note 必填"

    # 落 evidence
    contracts = state.setdefault("stage_contracts", {})
    pm_c = contracts.setdefault("pm_acceptance", {})
    ev = pm_c.setdefault("evidence", {})
    ev["decision"] = decision
    ev["note"] = note
    return True, ""


def _check_test_done_or_micro(state: dict, args) -> bool:
    """test output_satisfied · Micro 流程无 test stage(dev → pm_acceptance)· 直接放行。"""
    if state.get("flow_type") == "Micro":
        return True
    return state.get("stage_contracts", {}).get("test", {}).get("output_satisfied") is True


PM_ACCEPTANCE_SPEC = StageSpec(
    name="pm_acceptance",
    prerequisites=[
        StagePrerequisite(
            id="test_completed",
            check_fn=_check_test_done_or_micro,
            hint="先完成 state.py test-complete(Micro 流程无 test · 自动放行)",
            description="test output_satisfied(Micro 流程豁免)",
        ),
    ],
    artifacts=[],  # pm_acceptance 仅决策 · 无文件产物
    evidence_checks=[
        StageEvidenceCheck(
            name="pm_decision",
            check_fn=_evidence_pm_decision,
            description="--decision 合法 + rejected 时 --note 非空",
        ),
    ],
    brief_template_fn=_pm_acceptance_brief,
    auto_transition_fn=_pm_acceptance_transition,
    authorized_pause_point="三选项(approved_and_ship / approved_no_ship / rejected_with_feedback)",
)


# ─── B11 · ship ────────────────────────────────────────────────────


def _check_pm_approved_ship(state: dict, args) -> bool:
    """pm_acceptance decision == 'approved_and_ship' · 容错读 evidence/旧位(详 _pm_decision_value)"""
    pm_c = state.get("stage_contracts", {}).get("pm_acceptance", {})
    if pm_c.get("output_satisfied") is not True:
        return False
    return _pm_decision_value(pm_c) == "approved_and_ship"


def _check_ship_phase_terminal(state: dict, args) -> bool:
    """v8.145:ship.phase == 'archived'(ship1 终幕 archive 设置 · 即 ship1 全交付)。"""
    return state.get("ship", {}).get("phase") in ("archived", "pushed")


def _ship_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Ship Stage(v8.145 · ship1 全交付 / ship2 零内容清场)

### 目标
ship1(全在 worktree):净化 → 归档+翻牌进 feature 分支 → push + 创 MR · 终点 = MR 提交。
ship2(主工作区 · MR 合并后):验已交付 → 删 worktree → 净化主工作区。

### 结果(ship1 完成判定)
- `state.ship.phase = "pushed"`(archive → push 记录后)
- `current_stage = "completed"`(archive 时写入 · 随 MR 原子可见)
- 归档 zip + 规划翻牌 + 终态 state.json 全在 feature 分支(单 MR · 无第二收尾 MR)

### 怎么做
**必读** `stages/ship-stage.md`(ship1 三 action + ⏸️ 等 MR 合并 + ship2 一条命令)。

### 完成方式
```
# ship1(全在 worktree 内):
state.py ship-start --feature <path>
state.py ship-phase --action sanitize ...
state.py ship-phase --action archive --planning-artifacts <翻牌文件>|--no-planning-changes --archive-desc '<≤200 字>'
# → git push + gh/glab 创 MR(CLI-first)→
state.py ship-phase --action push --mr-url <真实 URL> ...
# ⏸️ 提示用户合并 MR —— feature 的 ship 到此结束
# ship2(用户合并后 · cd 回主工作区 · 零内容清场):
state.py ship-finalize --feature <worktree 内 feature 路径>
```
"""


def _ship_transition(state: dict) -> Optional[str]:
    return "completed"


SHIP_SPEC = StageSpec(
    name="ship",
    prerequisites=[
        StagePrerequisite(
            id="pm_approved_and_ship",
            check_fn=_check_pm_approved_ship,
            hint=(
                "pm_acceptance 未通过 approved_and_ship · "
                "重跑 pm_acceptance-complete --decision approved_and_ship"
            ),
            description="pm_acceptance.decision == approved_and_ship",
        ),
        # 注:ship1(sanitize/archive/push)全在 worktree 内跑;ship2(ship-finalize)
        # 由 _v8_ship.py _ship_finalize_precheck 独立拦截必在主工作区 · 职责分明(v8.145)。
    ],
    artifacts=[],  # ship 无 markdown 产物 · 看 state.ship 字段
    evidence_checks=[
        StageEvidenceCheck(
            name="ship_phase_terminal",
            check_fn=lambda state, args: (
                (True, "") if _check_ship_phase_terminal(state, args)
                else (False, "state.ship.phase 未达 archived(v8.145 ship1 终幕)· "
                             "先跑 ship-phase --action archive")
            ),
            description="state.ship.phase ∈ ('archived', 'pushed')(v8.145)",
        ),
    ],
    brief_template_fn=_ship_brief,
    auto_transition_fn=_ship_transition,
    authorized_pause_point="ship1 终点 · 等用户在平台 merge feature MR(合并后 ship2 清场)",
)


# ─── STAGE_SPECS 汇总 ──────────────────────────────────────────────────


STAGE_SPECS: dict[str, StageSpec] = {
    "goal": GOAL_SPEC,
    "ui_design": UI_DESIGN_SPEC,
    "panorama_sync": PANORAMA_SYNC_SPEC,
    "blueprint": BLUEPRINT_SPEC,
    "blueprint_lite": BLUEPRINT_LITE_SPEC,
    "diagnose": DIAGNOSE_SPEC,
    "dev": DEV_SPEC,
    "review": REVIEW_SPEC,
    "test": TEST_SPEC,
    "browser_e2e": BROWSER_E2E_SPEC,
    "pm_acceptance": PM_ACCEPTANCE_SPEC,
    "ship": SHIP_SPEC,
}
