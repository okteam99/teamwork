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

详细 schema 见 docs/v8-redesign/01-COMMAND-SCHEMA.md。
"""

from __future__ import annotations

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


def _check_prepare_completed(state: dict, args) -> bool:
    return "prepare" in state.get("completed_stages", []) or state.get("flow_type") is not None


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
            return False, f"{primary_artifact} 不存在"
        if not review.exists():
            return False, f"{review_artifact} 不存在 · review 未发生"
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
            return False, f"{artifact} 不存在"
        fm = parse_frontmatter(target)
        if not fm:
            return False, f"{artifact} 缺 frontmatter"
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
            return False, f"{review_artifact} 不存在 · 无法校验 reviewers"

        fm = parse_frontmatter(artifact_path)
        if not fm:
            return False, f"{review_artifact} 缺 frontmatter"

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
        missing = required_set - reviewer_set
        if missing:
            return False, (
                f"{review_artifact} frontmatter.reviewers 缺角色: {sorted(missing)} · "
                f"必含 state.stage_review_roles[{current}] = {required} · "
                f"补 reviewer 或在上一 stage complete 时跑 --next-stage-roles 调整"
            )
        return True, ""

    return _check


# ─── B1 · goal ─────────────────────────────────────────────────


def _goal_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Goal Stage

### 目标
PM 起草 PRD · PL-PM 讨论 · 多角色并行评审 · 收敛后用户确认 · 决策是否需要 UI Design Stage。

### 结果(完成判定)
- `PRD.md`(frontmatter:`acceptance_criteria` + `revision_history`)
- `PRD-REVIEW.md`(frontmatter:`reviewers` + `verdicts` · mtime > PRD.md)
- `state.execution_hints.ui_design_needed` 已决策(由 `--needs-ui`)

### 怎么做
**必读** `stages/goal-stage.md`(详细步骤 7 步 + 注意事项 5 条)。

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


GOAL_SPEC = StageSpec(
    name="goal",
    prerequisites=[
        StagePrerequisite(
            id="feature_initialized",
            check_fn=_check_feature_initialized,
            hint="先跑 state.py init-feature 创建 state.json",
            description="state.feature_id + state.flow_type 必须存在",
        ),
        StagePrerequisite(
            id="prepare_completed",
            check_fn=_check_prepare_completed,
            hint="先跑 state.py prepare --feature <path> --user-input <...>",
            description="prepare stage 必须先完成(扫 KNOWLEDGE/ADR + 流程类型识别)",
        ),
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
    ],
    brief_template_fn=_goal_brief,
    auto_transition_fn=_goal_transition,
    allowed_flow_types=["Feature", "敏捷需求"],  # Feature Planning 走 planning · 不进 goal
    authorized_pause_point="Substep 6 · 用户最终确认(全员 review 通过后)",
)


# ─── B6 · dev(完整模板示范) ─────────────────────────────────────────


def _check_blueprint_or_alt_done(state: dict, args) -> bool:
    """blueprint / blueprint_lite output_satisfied 或 Bug/Micro 流程直入"""
    contracts = state.get("stage_contracts", {})
    if contracts.get("blueprint", {}).get("output_satisfied") is True:
        return True
    if contracts.get("blueprint_lite", {}).get("output_satisfied") is True:
        return True
    flow = state.get("flow_type")
    if flow in ("Bug", "Micro"):
        return True
    return False


def _check_prd_or_bug_report(state: dict, args) -> bool:
    feature_dir = Path(args.feature)
    if (feature_dir / "PRD.md").exists():
        return True
    if list(feature_dir.glob("bugfix/BUG-*.md")):
        return True
    return False


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
        return "ship"  # Micro 跳过 review/test 直接 ship(简化分支)
    return "review"  # Feature / Bug / 敏捷 都走 review


DEV_SPEC = StageSpec(
    name="dev",
    prerequisites=[
        StagePrerequisite(
            id="blueprint_or_alt_done",
            check_fn=_check_blueprint_or_alt_done,
            hint=(
                "Feature/敏捷流程:先完成 blueprint(-complete) 或 blueprint_lite(-complete)。"
                "Bug/Micro 流程:无需 blueprint · 可直入 dev。"
                "当前 flow_type / stage_contracts 不满足任一条件。"
            ),
            description="blueprint 或 blueprint_lite output_satisfied,或 flow_type ∈ {Bug, Micro}",
        ),
        StagePrerequisite(
            id="prd_or_bug_report_exists",
            check_fn=_check_prd_or_bug_report,
            hint=(
                "Feature 流程必须有 PRD.md(回 goal-complete 起草)。"
                "Bug 流程必须有 bugfix/BUG-*.md(模板 templates/bug-report.md · "
                "含 frontmatter bug_id/symptom/root_cause/fix_summary + "
                "body §现象/§根因/§修复方案/§回归测试)。"
            ),
            description="PRD.md 存在(Feature)或 bugfix/BUG-*.md 存在(Bug)",
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
    authorized_pause_point="无暂停 · 完成后自动转 review(Bug/Micro 直接 ship)",
)


# ─── B2 · ui_design ─────────────────────────────────────────────────


def _ui_design_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## UI Design Stage

### 目标
Designer 产出 UI.md + HTML 预览 · sitemap 同步(如涉及全景变更)。

### 结果(完成判定)
- `UI.md`(frontmatter:`pages: [{{id, title}}]`)
- `preview/*.html`(每 page.id 对应 1 文件 · 可交互)
- (条件)sitemap.md 已更新

### 怎么做
**必读** `stages/ui-design-stage.md`(详细步骤 6 步 + 注意事项 5 条)。

### 完成方式
```
state.py ui_design-complete --feature <path> --auto-commit <hash> \
  --artifacts UI.md,preview/
```
"""


def _ui_design_transition(state: dict) -> Optional[str]:
    """ui_design 完成后 · 进 blueprint 或 blueprint_lite。"""
    flow = state.get("flow_type")
    if flow == "敏捷需求":
        return "blueprint_lite"
    return "blueprint"


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
            description="UI 设计稿 · frontmatter pages[]",
        ),
        StageArtifactSpec(
            glob="preview/*.html",
            min_files=1,
            must_be_in_commit=False,  # preview HTML 数量动态 · 不逐个 commit 校验
            description="HTML 预览(每页一文件)",
        ),
    ],
    evidence_checks=[],
    brief_template_fn=_ui_design_brief,
    auto_transition_fn=_ui_design_transition,
    authorized_pause_point="完成后给用户预览 URL · 等确认",
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
**必读** `stages/blueprint-stage.md`(详细步骤 8 步 + 注意事项 5 条)。

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
        return False, f"PRD.md 或 TC.md 不存在 · 路径 prd={prd} tc={tc}"

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


def _evidence_external_review_artifact(state: dict, args) -> tuple[bool, str]:
    """external-cross-review/ 至少 1 份 markdown(P0-154)。

    联动 state.stage_review_roles:若当前 stage 的 reviewers 列表不含 'external'
    (通过 change-review-roles 调整去除) → skip 校验(audit 已在 stage_review_roles_adjustments)。

    v8.0+P0-14 bug fix:external-cross-review/ 在 artifact_root 内(即 feature_dir 内 · 不是 parent)。
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
        return False, "external-cross-review/*.md 为空 · 跑 codex 外部评审或加 opt-out concerns"
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
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
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


def _pm_acceptance_transition(state: dict) -> Optional[str]:
    """按 decision 转移。"""
    pm_c = state.get("stage_contracts", {}).get("pm_acceptance", {})
    decision = pm_c.get("evidence", {}).get("decision")
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


PM_ACCEPTANCE_SPEC = StageSpec(
    name="pm_acceptance",
    prerequisites=[
        StagePrerequisite(
            id="test_completed",
            check_fn=_check_stage_output_satisfied("test"),
            hint="先完成 state.py test-complete",
            description="test output_satisfied",
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
    """pm_acceptance.evidence.decision == 'approved_and_ship'"""
    pm_c = state.get("stage_contracts", {}).get("pm_acceptance", {})
    if pm_c.get("output_satisfied") is not True:
        return False
    return pm_c.get("evidence", {}).get("decision") == "approved_and_ship"


def _check_cwd_main_worktree(state: dict, args) -> bool:
    """cwd 在主工作区(非 linked worktree)· 沿用 v7 P0-156 治本逻辑"""
    import os
    if os.environ.get("TEAMWORK_BYPASS_MAIN_WORKTREE") == "1":
        return True

    import subprocess
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if result.returncode != 0:
            return True  # 不在 git 仓库 · 跳过此检查
        git_dir = result.stdout.strip()
        # linked worktree 的 git_dir 形如 .git/worktrees/<name>
        # 主工作区的 git_dir 是 .git
        return "/worktrees/" not in git_dir
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return True  # 无 git · 跳过


def _check_ship_phase_merged(state: dict, args) -> bool:
    """ship.phase == 'merged'(由 v7 ship-confirm-merged 设置)"""
    return state.get("ship", {}).get("phase") == "merged"


def _check_ship_cleanup_done(state: dict, args) -> bool:
    """ship.worktree_cleanup IN ('cleaned', 'n_a')"""
    return state.get("ship", {}).get("worktree_cleanup") in ("cleaned", "n_a")


def _ship_brief(state: dict) -> str:
    """v8.0+P0-8 极简版:目标 + 结果 + 完成方式 · 怎么做归 stage.md。"""
    return f"""## Ship Stage

### 目标
push feature → CLI 创 MR → 等用户合并 → 验证合入 + 清理 worktree。

### 结果(完成判定)
- `state.ship.phase = "merged"`
- `state.ship.merge_commit_hash` 锚定
- `state.ship.worktree_cleanup ∈ {{cleaned, n_a}}`

### 怎么做
**必读** `stages/ship-stage.md`(详细步骤 10 步 + 注意事项 5 条 · 含主工作区拦截 / cleanup hard gate / CLI-first trap)。

### 完成方式
```
# 子动作链(详见 stage.md):
state.py ship-start --feature <path>
state.py ship-phase --action sanitize ...
state.py ship-phase --action push ...
# ⏸️ 等用户合并 · cd 回主工作区
state.py ship-phase --action confirm-merged ...
state.py ship-phase --action cleanup --status cleaned
state.py ship-complete --feature <path>
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
        # 注:ship-start 不再要求主工作区(Phase 1 sanitize/push 都在 worktree 内跑 ·
        # 因为 git push 必须从 feature branch checkout 位置)· Phase 2 (confirm-merged/cleanup)
        # 由 _v8_ship.py _require_main_worktree 独立拦截 · 保持职责分明。
    ],
    artifacts=[],  # ship 无 markdown 产物 · 看 state.ship 字段
    evidence_checks=[
        StageEvidenceCheck(
            name="ship_phase_merged",
            check_fn=lambda state, args: (
                (True, "") if _check_ship_phase_merged(state, args)
                else (False, "state.ship.phase != 'merged' · 先跑 ship-confirm-merged")
            ),
            description="state.ship.phase == 'merged'",
        ),
        StageEvidenceCheck(
            name="ship_cleanup_done",
            check_fn=lambda state, args: (
                (True, "") if _check_ship_cleanup_done(state, args)
                else (False, "state.ship.worktree_cleanup not cleaned/n_a · 先跑 ship-cleanup")
            ),
            description="state.ship.worktree_cleanup ∈ ('cleaned', 'n_a')",
        ),
    ],
    brief_template_fn=_ship_brief,
    auto_transition_fn=_ship_transition,
    authorized_pause_point="Phase 1 → Phase 2 间断点 · 等用户在平台 merge MR",
)


# ─── STAGE_SPECS 汇总 ──────────────────────────────────────────────────


STAGE_SPECS: dict[str, StageSpec] = {
    "goal": GOAL_SPEC,
    "ui_design": UI_DESIGN_SPEC,
    "blueprint": BLUEPRINT_SPEC,
    "blueprint_lite": BLUEPRINT_LITE_SPEC,
    "dev": DEV_SPEC,
    "review": REVIEW_SPEC,
    "test": TEST_SPEC,
    "browser_e2e": BROWSER_E2E_SPEC,
    "pm_acceptance": PM_ACCEPTANCE_SPEC,
    "ship": SHIP_SPEC,
}
