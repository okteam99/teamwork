# v8.0 迁移路线

> 全 stage 一次性重构 · 不分 phase 试点。
> 工作量集中 3-4 周。本文按"开发节奏"拆解。

---

## 阶段总览

```
Week 1   ──  state.py 扩张:核心 + B1-B6 stage 命令
Week 2   ──  state.py 扩张:B7-B12 + 测试覆盖
Week 3   ──  markdown 减负 + tools 清理 + spec 改写
Week 4   ──  迁移工具(v7→v8)+ 真实 Feature 验证 + 文档收尾
发布     ──  v8.0.0 标签 + CHANGELOG
```

---

## Week 1 · state.py 核心扩张(~3000 行新代码)

### 1.1 抽出常量与状态机定义

新建模块或在 state.py 顶部扩充:

```python
# stage_definitions.py 或 state.py 内
@dataclass
class StagePrerequisite:
    id: str
    check_fn: Callable[[dict], bool]      # 接受 state.json,返回 bool
    hint: str
    auto_fixable: bool = False

@dataclass
class StageArtifactSpec:
    path: str | None = None
    glob: str | None = None
    frontmatter_required: list[str] = field(default_factory=list)
    body_min_lines: int = 0
    min_files: int = 1
    must_be_in_commit: bool = True

@dataclass
class StageEvidenceCheck:
    name: str
    check_fn: Callable[[dict, args], tuple[bool, str]]   # 返回 (passed, error_msg)

@dataclass
class StageSpec:
    name: str
    prerequisites: list[StagePrerequisite]
    artifacts: list[StageArtifactSpec]
    evidence_checks: list[StageEvidenceCheck]
    brief_template: str    # next_action_brief markdown 模板
    auto_transition_to: Callable[[dict], str | None]   # 返回 next stage 或 None(多选)

STAGE_SPECS: dict[str, StageSpec] = {
    "goal_plan": StageSpec(...),
    "ui_design": StageSpec(...),
    ...
}
```

### 1.2 通用 stage-start / stage-complete 引擎

```python
def execute_stage_start(stage: str, args: argparse.Namespace) -> None:
    spec = STAGE_SPECS[stage]
    state = load_state(args.feature)
    
    # 1. 校验所有 prerequisites
    missing = []
    for prereq in spec.prerequisites:
        if not prereq.check_fn(state):
            missing.append({
                "id": prereq.id,
                "check": "...",
                "actual": False,
                "hint": prereq.hint,
                "auto_fixable": prereq.auto_fixable
            })
    
    # 2. bypass 协议
    if missing and args.bypass:
        require_user_confirmed(args)
        write_bypass_log(state, stage, "start", missing, args)
        write_concerns_warn(state, ...)
        # 通过
    elif missing:
        emit_fail({
            "verdict": "FAIL",
            "stage": stage,
            "phase": "start",
            "missing_prerequisites": missing,
        })
        sys.exit(1)
    
    # 3. 通过 → 自动 enter-stage(legal_next 校验)
    auto_enter_stage(state, stage)
    
    # 4. 渲染 next_action_brief
    brief = render_brief(spec.brief_template, state)
    
    # 5. emit
    emit_pass({
        "verdict": "PASS",
        "stage": stage,
        "phase": "start",
        "transition": f"{state.previous_stage} → {stage}",
        "next_action_brief": brief
    })


def execute_stage_complete(stage: str, args: argparse.Namespace) -> None:
    spec = STAGE_SPECS[stage]
    state = load_state(args.feature)
    
    # 1. 校验 current_stage == stage
    if state["current_stage"] != stage:
        die_with_hint(...)
    
    # 2. 校验 artifacts
    missing_artifacts = []
    for art_spec in spec.artifacts:
        if not check_artifact(art_spec, args, state):
            missing_artifacts.append(...)
    
    # 3. 校验 evidence(auto-commit / test-exit / 外部评审)
    failed_evidence = []
    for ev_check in spec.evidence_checks:
        passed, err = ev_check.check_fn(state, args)
        if not passed:
            failed_evidence.append({"name": ev_check.name, "error": err})
    
    # 4. bypass 同样支持
    if (missing_artifacts or failed_evidence) and args.bypass:
        require_user_confirmed(args)
        write_bypass_log(...)
    elif missing_artifacts or failed_evidence:
        emit_fail(...)
        sys.exit(1)
    
    # 5. 自动副作用:satisfy 三 gate + 写 review-log + auto transition
    auto_satisfy_gates(state, stage)
    write_review_log(state, stage, "completed")
    
    next_stage = spec.auto_transition_to(state)
    if next_stage:
        auto_enter_stage(state, next_stage)
        # 立即 emit 下一 stage 的 brief
        next_brief = render_brief(STAGE_SPECS[next_stage].brief_template, state)
    else:
        # 多选:emit 暂停点
        next_brief = render_decision_pause(state, stage)
    
    write_state(state)
    
    emit_pass({
        "verdict": "PASS",
        "stage": stage,
        "phase": "complete",
        "satisfied_gates": ["input", "process", "output"],
        "transitioned_to": next_stage,
        "next_stage_brief": next_brief
    })
```

### 1.3 实现 B1-B6 stage specs

按 01-COMMAND-SCHEMA.md 中的契约,逐个写 STAGE_SPECS 字典:

- B1 `goal_plan` ✅
- B2 `ui_design` ✅
- B3 `panorama_design` ✅
- B4 `blueprint` ✅
- B5 `blueprint_lite` ✅
- B6 `dev` ✅

每个 stage 约 200-300 行 spec 定义。

### 1.4 单元测试初稿

`tools/tests/test_v8_b1_b6.py`:
- 每个 stage 测 PASS 路径
- 每个 stage 测 missing prerequisites 路径
- 每个 stage 测 bypass 路径
- 状态机转移合法性测试

---

## Week 2 · state.py 完成 + 全测试覆盖

### 2.1 实现 B7-B12 stage specs

- B7 `review` ✅
- B8 `test` ✅
- B9 `browser_e2e` ✅
- B10 `pm_acceptance` ✅
- B11 `ship-start` / `ship-phase` / `ship-complete` ✅
- B12 终态(无命令)

Ship Stage 复杂度高 · 单独 ~600 行。沿用 v7 ship-* 物化拦截(P0-156 / P0-124)。

### 2.2 A 类初始化命令

- `init-feature` 升级 schema_version=v8.0
- `triage`(整合 init_triage.py 的核心 + 5 mode 分诊)
- `prepare`(整合 prepare-stage.md 内容)

### 2.3 C 类维护

- `migrate-v7-to-v8`:读 v7 state.json → 转换 → 写 v8.0
- 其他 C 命令(snapshot/validate/recover/raw-read/raw-write)沿用

### 2.4 全测试覆盖

- 各 stage start/complete 各 ~10 用例 = 200+
- bypass 协议测试
- 错误处理边界
- 状态机非法转移测试
- migrate-v7-to-v8 兼容性测试

### 2.5 集成测试(端到端)

新建 `tests/integration/`:
- 完整 Feature 流程(init → goal_plan → ... → ship → completed)
- 完整 Bug 流程
- 完整 Micro 流程
- 完整 敏捷需求 流程
- 完整 Feature Planning 流程
- 完整 问题排查 流程

---

## Week 3 · markdown 减负 + tools 清理

### 3.1 物理删除 tools/ 文件

```bash
cd skills/teamwork/tools/
git rm init_triage.py
git rm render-flow-transition.py
git rm render-decision-pause.py
git rm render-afk-skip.py
git rm render-status-line.py
```

### 3.2 物理删除 rules/ 目录

```bash
cd skills/teamwork/
git rm -r rules/
```

### 3.3 stages/*.md 大幅减负

每个 stage 重写为新模板:

```markdown
# {Stage Name} Stage

> auto-verified by: state.py {stage}-start / state.py {stage}-complete
> v8.0 起,本文档仅承担"Telos + Output Contract"职责。
> 详细校验逻辑在 state.py STAGE_SPECS["{stage}"]。

## Telos

{为什么这个 stage 存在 · 在整体流程中的角色 · 1-3 段}

## Output Contract(创作参考)

{artifact 形态描述 · 给 RD/QA/Designer 起草时的参考}

### {artifact_1}.md
- 必含 章节 A / B / C
- frontmatter 字段:...
- 内容要点:...

### {artifact_2}.md
...

## Rationale(为什么这么设计)

{设计取舍 · 历史 · 与其他 stage 的关系}

## 相关参考

- {上游 stage}-stage.md
- {下游 stage}-stage.md
- roles/{相关角色}.md
```

### 3.4 roles/* 整合(21 → 7)

合并步骤:
1. `pmo.md` + 7 sub-file → `orchestrator.md`
2. `pm.md` + `pm-prd-review.md` → `pm.md`
3. `qa.md` + `qa-tc-review.md` + `qa-cr.md` → `qa.md`
4. `architect.md` + `architect-tech-review.md` + `architect-cr.md` → `architect.md`
5. `product-lead.md` + `product-lead-change-mgmt.md` → `product-lead.md`
6. `rd.md` / `designer.md` / `external-reviewer.md` 直接减负

每文件结构:

```markdown
# {Role Name}

## Telos
{这个角色聚焦哪个专业方向 · 缺这个视角会留什么盲区}

## 内容创作要点
{产出物的关键内容要点 · 不是格式校验}

## 与其他角色的协作
{在哪个 stage 与谁交互}

## Rationale
{为什么需要这个角色 · 历史}
```

### 3.5 standards/* 删除流程类规范

```bash
cd skills/teamwork/standards/
git rm evidence-binding.md output-tiers.md review-verdict.md review-scope.md \
       prompt-cache.md stage-instantiation.md discussion-mode.md external-model.md
```

保留:
- `common.md` / `backend.md` / `frontend.md` / `tdd.md`(技术规范)
- `external-model-usage.md`(减负到 ~30 行 · OpenAI ToS rationale)
- `scripts-policy.md`(减负到 ~50 行 · 脚本设计原则)

### 3.6 顶层 markdown 改写

- `SKILL.md` 完全重写为 v8 叙事(~200 行)
- `RULES.md` 大幅减负(~300 行 · 只留 rationale)
- `FLOWS.md` 大幅减负(~80 行)
- `STATUS-LINE.md` / `CONTEXT-RECOVERY.md` / `REVIEWS.md` 物理删除
- `ROLES.md` / `STANDARDS.md` 减负为索引

### 3.7 templates/ 调整

```bash
cd skills/teamwork/templates/
git rm feature-state.json   # state.py 内部生成
git rm dispatch.md          # dispatch 协议进 state.py
```

---

## Week 4 · 收尾 + 验证

### 4.1 跑 sanity check

按 02-CLEANUP.md 的 grep 清单,逐项跑:
```bash
grep -rn "flow-transitions.md\|gate-checks.md\|naming.md" skills/teamwork/
grep -rn "render-flow-transition\|render-decision-pause\|..." skills/teamwork/
grep -rn "init_triage" skills/teamwork/
grep -rn "evidence-binding.md\|output-tiers.md\|..." skills/teamwork/
```

每条应无外部引用。有 → 修复引用方。

### 4.2 跑 scan-spec-consumer.py

```bash
python3 skills/teamwork/tools/scan-spec-consumer.py
```

检查 spec 引用一致性。零警告才能 ship。

### 4.3 install.sh 更新

```bash
# 检测 schema_version
# v7 项目跑 migrate-v7-to-v8
# v8 项目正常使用
```

### 4.4 真实 Feature 端到端验证

跑 2-3 个真实 Feature 走完完整流程:
- 简单 Feature(无 UI)
- 复杂 Feature(含 UI / Ship)
- Bug 流程
- Micro 流程

观察:
- AI 是否需要再 read 任何 spec markdown(应该不需要)
- 错误处理是否触发 bypass 协议
- next_action_brief 是否清晰

### 4.5 文档收尾

- `docs/CHANGELOG.md` 加 v8.0.0 入口(列出删除/新增/破坏性变更)
- `docs/v8-redesign/` 标 archive(留作历史)
- README.md / README-EN.md 改写为 v8 叙事

### 4.6 版本发布

```bash
git tag v8.0.0
git push origin v8.0.0
```

---

## v7 → v8 兼容性策略

### 老 Feature 自动迁移

```bash
# state.py 检测到 schema_version != v8.0 时:
$ state.py goal_plan-start --feature docs/features/F001-old

⚠️ Detected v7 state.json. Run migration first:
   state.py migrate-v7-to-v8 --feature docs/features/F001-old
```

migrate 逻辑:
1. 读 v7 state.json
2. 字段重命名(planned_execution / executor_history / detection_evidence 删 / 合并)
3. 添加 schema_version=v8.0
4. 添加 bypass_log=[] 空数组
5. stage_contracts.X.evidence 字段补全(从 ship.* / dispatch_log/ 等推断)
6. 备份原 state.json 为 state.json.v7-backup
7. 写新 state.json
8. emit 报告:迁移了哪些字段

### 跨版本 skill 注入

```
CLAUDE.md / AGENTS.md / GEMINI.md 注入段标 SKILL_VERSION=v8.0
sync-drift.py 自动检测 v7 注入段 → 提示用户跑 migrate
```

---

## 风险与缓解

| 风险 | 缓解 |
|------|------|
| state.py 单文件膨胀到 ~7500 行 | 拆分模块(stage_specs.py / stage_engine.py / ship_phase.py 等)· state.py 只保留 CLI 入口 |
| 老 Feature 迁移失败 | migrate-v7-to-v8 提供 --dry-run + 详细 diff · 失败时不动原文件 |
| AI 仍然 read 老 spec | spec 减负后留 stub markdown 指向 state.py · 主要内容物理删除 |
| 单元测试覆盖不足 | 每 stage 强制 80%+ 覆盖率 · CI 跑 pytest |
| Ship 流程 P0-156/P0-124 物化拦截破坏 | 沿用 v7 代码 · 仅重组为 ship-phase --action |

---

## 路标(交付物)

```
W1 Day 7:  state.py 含 B1-B6 stage 命令 + 基础测试 · 跑通 goal_plan→dev
W2 Day 14: state.py 全 stage + ~200 测试 · 跑通完整 Feature 流程
W3 Day 21: skill markdown 减负完成 · sanity check 全过
W4 Day 28: 真实 Feature 验证 · v8.0.0 标签 · CHANGELOG
```

---

## 立即可启动的 Day 1 工作

1. ✅ 创建 `docs/v8-redesign/` 文档(已完成 · 本目录)
2. 在 state.py 抽出常量(STAGE_SPECS / ARTIFACT_CHECKS / EVIDENCE_CHECKS 等)
3. 实现通用 stage-start / stage-complete 引擎
4. 编写 B6 `dev` stage 作为第一个完整模板(最简单 · 无 ship 复杂度)
5. 跑测试验证流程
6. 按此模板克隆 B1-B5 / B7-B12
