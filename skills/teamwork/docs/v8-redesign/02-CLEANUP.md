# v8.0 清理清单

> 按"可枚举进脚本"判据,所有流程业务逻辑迁到 state.py。
> 本文列出**每个文件**的最终处置:🗑️ 删除 / 🔥 大幅减负 / ✏️ 轻度改写 / ✅ 保留 / 🆕 新增。

---

## tools/ Python 工具

| 文件 | 行数 | 处置 | 理由 |
|------|------|------|------|
| `state.py` | 1609 → ~7500 | 🔥 扩张承担全 stage start/complete | 流程业务逻辑全进此 |
| `init_triage.py` | 457 | 🗑️ 删除 | 职责并入 `state.py triage` |
| `render-flow-transition.py` | 247 | 🗑️ 删除 | xx-stage-start/complete 自 emit |
| `render-decision-pause.py` | 308 | 🗑️ 删除 | xx-stage-complete 自 emit 暂停点 markdown |
| `render-afk-skip.py` | 175 | 🗑️ 删除 | state.py 内部 AFK 判定 + emit |
| `render-status-line.py` | 322 | 🗑️ 删除 | state.py 每命令尾部自 emit 状态行 |
| `sync-drift.py` | 230 | ✅ 保留 | CLAUDE.md/AGENTS.md 注入段同步 · 框架自维护 |
| `post-feature.py` | 322 | ✏️ 轻度改写 | 并入 `state.py ship-complete` 内部调用 · 或独立保留 |
| `scan-spec-consumer.py` | 254 | ✅ 保留 | 框架自身 spec 引用一致性检测 |
| `verify-panorama.py` | 228 | ✅ 保留 | `ui_design-complete` 内部依赖 |
| `diff-html-vs-panorama.py` | 340 | ✅ 保留 | `ui_design` stage 内部工具 |
| `_feature_context.py` | 169 | ✅ 保留 | state.py 内部 utility module |

**净删除**:457 + 247 + 308 + 175 + 322 = **1509 行 Python 删除**。

---

## templates/ 模板

| 文件 | 处置 | 理由 |
|------|------|------|
| `verify-ac.py` | ✅ 保留 | blueprint-complete / test-complete 内部调用 |
| `detect-external-model.py`(若存在)| ✅ 保留 | state.py prepare 内部调用 |
| `prd.md` / `tc.md` / `tech.md` / `ui.md` 等模板 | ✅ 保留 | AI 创作时按需 Read |
| `troubleshooting.md` / `knowledge.md` / `glossary.md` 骨架 | ✅ 保留 | 项目级元文档空骨架 |
| `feature-state.json` | 🗑️ 删除 | state.py init-feature 内部生成 · 不再外置模板 |
| `dispatch.md` | 🗑️ 删除 | dispatch 协议进 state.py(subagent 调用封装) |
| `external-cross-review.md` | ✅ 保留 | External 评审产物模板 |
| `bug-report.md` / `change-request.md` / `adr.md` | ✅ 保留 | AI 创作时按需 Read |
| `roadmap.md` / `project.md` | ✅ 保留 | Planning 流程产出模板 |
| `host-instruction-injection.md` | ✅ 保留 | sync-drift.py 用 |
| `review-log.jsonl` 示例 | ✅ 保留 | 日志格式示例 |
| `retro.md` / `retros-index.md` | ✅ 保留 | 复盘文档模板 |
| `pl-pm-feedback.md` | ✅ 保留 | PL-PM 讨论模板 |
| `adr-index.md` | ✅ 保留 | ADR 索引模板 |
| `e2e-registry.md` | ✅ 保留 | E2E 注册模板 |
| `architecture.md` / `dependency.md` / `glossary.md` / `config.md` | ✅ 保留 | 项目级文档模板 |

---

## rules/ 规则文档

| 文件 | 行数 | 处置 | 理由 |
|------|------|------|------|
| `flow-transitions.md` | 295 | 🗑️ 删除 | 进 state.py LEGAL_TRANSITIONS dict |
| `gate-checks.md` | ? | 🗑️ 删除 | 进 state.py 各 stage-complete 函数 |
| `naming.md` | ? | 🗑️ 删除 | 命名规则进 state.py 校验函数 |

**rules/ 目录最终为空 · 可整个删除**。

---

## stages/ Stage 规范

| 文件 | 当前行数 | 处置 | 减负后行数 |
|------|---------|------|----------|
| `triage-stage.md` | ? | 🗑️ 删除 | 进 state.py triage 命令 |
| `prepare-stage.md` | ? | 🗑️ 删除 | 进 state.py prepare 命令 |
| `goal-plan-stage.md` | 765+ | 🔥 大幅减负 | ~80 行(只留 telos + Output Contract) |
| `ui-design-stage.md` | 286+ | 🔥 大幅减负 | ~60 行 |
| `panorama-design-stage.md` | 129+ | 🔥 大幅减负 | ~50 行 |
| `blueprint-stage.md` | 359+ | 🔥 大幅减负 | ~100 行 |
| `blueprint-lite-stage.md` | 105+ | 🔥 大幅减负 | ~50 行 |
| `dev-stage.md` | 204+ | 🔥 大幅减负 | ~80 行 |
| `review-stage.md` | 247+ | 🔥 大幅减负 | ~80 行 |
| `test-stage.md` | 174+ | 🔥 大幅减负 | ~70 行 |
| `browser-e2e-stage.md` | 119+ | 🔥 大幅减负 | ~50 行 |
| `ship-stage.md` | 1004+ | 🔥 大幅减负 | ~100 行(Ship 内部多 phase 但全进 state.py) |

stages/*.md 减负后只保留:
- **Stage Telos**(为什么这个 stage 存在 · rationale)
- **Output Contract**(产物形态描述 · 给 RD/QA/Designer 创作参考)
- 顶部一行 `auto-verified by: state.py {stage}-start/complete`

删除内容:
- Input Contract 校验项 → state.py xx-start
- Process Contract gate 时机 → state.py xx-complete
- 暂停点协议 / 决策菜单 → state.py emit
- Execution Plan 格式 → state.py emit
- 子步骤序列 → state.py 内部
- next_actions 列表 → state.py emit

---

## roles/ 角色规范

| 文件 | 处置 | 理由 |
|------|------|------|
| `pmo.md` + `pmo-*.md`(7 个 sub-file)| 🔥 整合为 `orchestrator.md` | PMO 实际是编排器 · sub-file 合并到 state.py 实现 |
| `pm.md` + `pm-prd-review.md` | 🔥 整合为 `pm.md` | review 进 state.py review-stage 校验 |
| `qa.md` + `qa-tc-review.md` + `qa-cr.md` | 🔥 整合为 `qa.md` | review/cr 进 state.py |
| `rd.md` | ✏️ 轻度减负 | 自查 checklist 进 state.py · 留 TDD 哲学 + 内容创作要点 |
| `architect.md` + `architect-tech-review.md` + `architect-cr.md` | 🔥 整合为 `architect.md` | review/cr 进 state.py |
| `designer.md` | ✏️ 轻度减负 | UI 还原校验进 state.py(verify-panorama.py 调用) |
| `external-reviewer.md` | ✏️ 轻度减负 | 调用协议进 state.py |
| `product-lead.md` + `product-lead-change-mgmt.md` | 🔥 整合为 `product-lead.md` | change-mgmt 进 state.py(Change Request lifecycle) |

**21 文件 → 7 文件**:
```
orchestrator.md   (替代 pmo.md + pmo-* 7 sub-file)
pm.md             (整合 pm-prd-review.md)
qa.md             (整合 qa-tc-review.md + qa-cr.md)
rd.md             (轻度减负)
architect.md      (整合 architect-tech-review.md + architect-cr.md)
designer.md       (轻度减负)
external-reviewer.md (轻度减负)
product-lead.md   (整合 product-lead-change-mgmt.md)
```

每文件 ~50-100 行,只保留:
- 角色 telos(PM=需求完整性 / QA=测试覆盖)
- 输出物的"内容创作要点"(不是格式校验)

删除内容:
- 必读 spec 清单 → state.py xx-start emit
- 自查 checklist → state.py xx-complete 校验
- 输出格式 → state.py emit
- review verdict 标准 → state.py review-complete

---

## standards/ 规范

| 文件 | 处置 | 理由 |
|------|------|------|
| `common.md` | ✅ 保留 | 技术规范(命名 / 错误处理 / 日志)· 不是流程 |
| `backend.md` | ✅ 保留 | 后端技术规范 |
| `frontend.md` | ✅ 保留 | 前端技术规范 |
| `tdd.md` | ✅ 保留 | TDD 哲学 + RED-GREEN-REFACTOR 步骤 |
| `evidence-binding.md` | 🗑️ 删除 | 全部进 state.py schema |
| `output-tiers.md` | 🗑️ 删除 | 主对话 Tier 1/2/3 进 state.py emit |
| `review-verdict.md` | 🗑️ 删除 | 进 state.py review-complete |
| `review-scope.md` | 🗑️ 删除 | 进 state.py review-stage |
| `prompt-cache.md` | 🗑️ 删除 | 进 state.py 内部 Read 顺序 |
| `stage-instantiation.md` | 🗑️ 删除 | 进 state.py xx-start |
| `external-model-usage.md` | 🔥 大幅减负 | 留 OpenAI ToS 合规 rationale(~30 行)· 配置进 state.py |
| `external-model.md` | 🗑️ 删除 | 进 state.py prepare |
| `discussion-mode.md` | 🗑️ 删除 | mode E discuss 进 state.py triage |
| `scripts-policy.md` | ✏️ 轻度改写 | 留 scripts 设计原则(~50 行)· 具体退出码规范在各脚本 |

**14 文件 → 5 文件**:
```
common.md           保留(技术规范)
backend.md          保留(技术规范)
frontend.md         保留(技术规范)
tdd.md              保留(TDD 哲学)
external-model.md   减负到 ~30 行(OpenAI ToS rationale)
scripts-policy.md   减负到 ~50 行(脚本设计原则)
```

---

## 顶层 markdown

| 文件 | 当前行数 | 处置 | 减负后 |
|------|---------|------|--------|
| `SKILL.md` | ~800 | 🔥 大幅减负 | ~200(改写为 v8 "Code-driven" 叙事) |
| `RULES.md` | 1883 | 🔥 大幅减负 | ~300(只留 rationale · 16/17 红线进代码) |
| `FLOWS.md` | 876 | 🔥 大幅减负 | ~80(只讲 6 流程 telos) |
| `ROLES.md` | ? | 🔥 大幅减负 | ~30(7 角色索引) |
| `STANDARDS.md` | ? | 🔥 大幅减负 | ~30(规范索引) |
| `TEMPLATES.md` | ? | ✅ 保留(模板索引) | 不变 |
| `REVIEWS.md` | ? | 🗑️ 删除 | 评审流程进 state.py |
| `STATUS-LINE.md` | ~450 | 🗑️ 删除 | 状态行格式进 state.py emit |
| `CONTEXT-RECOVERY.md` | ? | 🗑️ 删除 | recover 协议进 state.py |
| `PRODUCT-OVERVIEW-INTEGRATION.md` | ? | 🔥 大幅减负 | ~40(PL 引导模式 rationale) |

---

## 顶层文件最终结构(v8)

```
skills/teamwork/
├── SKILL.md                  ~200 行 · v8 叙事 + 命令总览
├── RULES.md                  ~300 行 · 红线 rationale(不再列细则)
├── FLOWS.md                  ~80 行  · 6 流程 telos
├── ROLES.md                  ~30 行  · 7 角色索引
├── STANDARDS.md              ~30 行  · 规范索引
├── TEMPLATES.md              保留 · 模板索引
│
├── stages/         (12 文件 · 总计 ~700 行 · 各 50-100 行)
├── roles/          (7 文件 · 总计 ~500 行)
├── standards/      (6 文件 · 总计 ~400 行)
├── templates/      (保留全部)
├── tools/          (8 文件:state.py / init_triage.py 删 / sync-drift.py / post-feature.py / scan-spec-consumer.py / verify-panorama.py / diff-html-vs-panorama.py / _feature_context.py)
│
├── docs/
│   ├── CHANGELOG.md          保留 · 加 v8.0 入口
│   └── v8-redesign/          本目录 · v8 设计文档
│
└── install.sh                ✏️ 更新版本号检测
```

---

## 减负总账

### Markdown
```
当前总行数(估算):
  SKILL.md (800) + RULES.md (1883) + FLOWS.md (876) + STATUS-LINE.md (450) + 
  REVIEWS.md + STANDARDS.md + ROLES.md + TEMPLATES.md +
  stages/* (~4000) + roles/* (~3000) + standards/* (~2500) + rules/* (~400) +
  其他顶层 (~500)
  
  ≈ 14400 行

v8 减负后:
  SKILL.md (200) + RULES.md (300) + FLOWS.md (80) + 
  ROLES.md (30) + STANDARDS.md (30) + TEMPLATES.md (~50) +
  stages/* (~750) + roles/* (~500) + standards/* (~400) + 
  其他顶层 (~150)
  
  ≈ 2490 行

净减:~11900 行(↓ 83%)
```

### Python
```
当前:
  state.py (1609) + init_triage.py (457) + render-* (1052) + 
  sync-drift.py (230) + post-feature.py (322) + scan-spec-consumer.py (254) +
  verify-panorama.py (228) + diff-html-vs-panorama.py (340) + 
  _feature_context.py (169) + templates/verify-ac.py
  
  ≈ 4661 行

v8 改造后:
  state.py (~7500) + sync-drift.py (230) + post-feature.py (322 或并入) +
  scan-spec-consumer.py (254) + verify-panorama.py (228) + 
  diff-html-vs-panorama.py (340) + _feature_context.py (~300) +
  templates/verify-ac.py
  
  ≈ 9200 行

净增:~4500 行(↑ 97%)
```

### 综合
```
markdown ↓ 11900 行
python   ↑ 4500 行
─────────────────────
净减     ~7400 行

且 python 部分**可单元测试覆盖**,markdown 删的是**靠 AI 自觉读**的部分。
```

---

## 删除前 sanity check 清单

按以下顺序验证,确认无引用后再删:

```bash
# 1. 检查 spec 引用
grep -rn "flow-transitions.md\|gate-checks.md\|naming.md" skills/teamwork/

# 2. 检查 render-* 引用
grep -rn "render-flow-transition\|render-decision-pause\|render-afk-skip\|render-status-line" skills/teamwork/

# 3. 检查 init_triage.py 引用
grep -rn "init_triage" skills/teamwork/

# 4. 检查 standards 引用
grep -rn "evidence-binding.md\|output-tiers.md\|review-verdict.md\|review-scope.md\|prompt-cache.md\|stage-instantiation.md\|discussion-mode.md\|external-model.md" skills/teamwork/

# 5. 检查 stages 引用(确认 stage spec 减负不破坏跨引用)
grep -rn "stages/triage-stage.md\|stages/prepare-stage.md" skills/teamwork/
```

每条 grep 结果应该全是"被删/被减的文件本身引用"(自引用),无来自 templates/ / tools/ / 顶层 markdown 的外部引用。如有外部引用 → 先迁移引用方,再删除。
