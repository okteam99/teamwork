# Browser E2E Stage：浏览器端到端验收

> API E2E 通过且 TC.md 标注需要 Browser E2E 时，进入本 Stage。从最终用户视角验证真实页面的完整业务链路。
> 🔴 契约优先：执行方式由 AI 自主规划（半自动特性推荐主对话）。

---

## 本 Stage 职责

通过 AI 浏览器操作真实页面、截图取证，验证用户视角的业务链路。不看代码。

与其他测试阶段的区别：
```
项目集成测试 → 跑项目内 integration test cases（代码级）
API E2E → 脚本验证真实 API 链路（调用方视角）
Browser E2E → 浏览器操作真实页面（最终用户视角） ← 本 Stage
```

---

## Input Contract

### 必读文件（按顺序）

```
├── {SKILL_ROOT}/agents/README.md
├── {SKILL_ROOT}/stages/browser-e2e-stage.md（本文件）
├── {SKILL_ROOT}/roles/qa.md
├── {Feature}/TC.md（Browser E2E Scenarios 章节）
├── {Feature}/PRD.md
└── {Feature}/UI.md（如有）
```

### Additional Context

- 应用访问地址（URL）
- 功能编号和名称
- TC.md「Browser E2E 前置条件」中用户提供的值（账号 / 测试数据等）

### Key Context

- 历史决策锚点
- 本轮聚焦点
- 已识别风险
- 降级授权
- 优先级 / 容忍度

### 前置依赖

- API E2E 已通过（或 TC.md 标注 API E2E 不适用）
- TC.md「Browser E2E 判断」= 需要
- PMO 已收集 TC.md「Browser E2E 前置条件」中"用户提供"的项
- PMO 确认页面可访问
- state.json.current_stage == "browser_e2e"

---

## Process Contract

### 必做动作

1. **读取 TC.md 的 Browser E2E Scenarios 章节**
2. **执行前置条件准备**（登录、测试数据等）
3. **逐场景浏览器验证**
   - 导航页面
   - 执行用户操作
   - 验证页面可观测结果
   - 每个场景截图取证（通过和失败都要）
4. **输出 Browser E2E 验收报告**

### 过程硬规则

- 🔴 **角色规范必读且 cite**：必读 `roles/qa.md`，产出前 cite 要点
- 🔴 **按 TC 逐条执行**：必须按 FE-E2E 场景逐条验证
- 🔴 **每个场景必须截图**：通过和失败都要（作为审计证据）
- 🔴 **失败场景必须记录差异**：实际结果 vs 预期结果
- 🔴 **不修改任何代码或配置**：只验证不修改

---

## Output Contract

### 必须产出的文件

| 文件路径 | 格式 | 必需内容 |
|---------|------|---------|
| `{Feature}/browser-e2e-result.md` | Markdown + YAML frontmatter | `executor`, `started_at`, `completed_at`, `scenarios[]`（含 screenshot_path） |
| `{Feature}/browser-e2e-screenshots/*.png` | PNG | 每场景至少 1 张截图 |

### 机器可校验条件

- [ ] browser-e2e-result.md 存在且 YAML frontmatter 可解析
- [ ] `scenarios[]` 数量 ≥ TC.md 中 Browser E2E Scenarios 数量
- [ ] 每个 scenario 有 `screenshot_path`
- [ ] 每个 scenario 有 `expected` 和 `actual` 字段
- [ ] 失败 scenario 有 `diff` 字段

### Done 判据

- 所有 TC Browser E2E 场景已执行
- 所有通过 scenario 有截图；失败 scenario 有截图 + diff
- `state.json.stage_contracts.browser_e2e.output_satisfied = true`

### 返回状态

| 状态 | 条件 | 后续 |
|------|------|------|
| ✅ DONE | 所有 scenario 通过 | 进入 PM 验收 |
| ❌ NOT_PASS | 有 scenario 失败 | RD 修复 → 重新 Browser E2E（≤3 轮） |

---

## AI Plan 模式指引

📎 Execution Plan 3 行格式 → [SKILL.md](../SKILL.md#-ai-plan-模式规范v73-新增)。

本 Stage 默认 `main-conversation`（半自动需用户观察，可用 `mcp__gstack__*` 或 `mcp__Claude_in_Chrome__*`）。典型偏离：无人值守 CI 批量执行 → `subagent`。

**Expected duration baseline（v7.3.3）**：每场景 2-3 min（含截图 + 验证），3-5 个场景合计 10-20 min。失败场景 diff 分析 +3-5 min。

---

## 执行报告模板

```
📋 Browser E2E 验收报告（F{编号}-{功能名}）
============================================

## 概况
├── 最终状态：{DONE / NOT_PASS}
├── 执行方式：{主对话 / Subagent}
├── 应用地址：{URL}
├── 场景数：{总数}
├── 通过：{N}
└── 失败：{M}

## 场景验证结果
| # | FE-E2E 编号 | 场景 | 结果 | 截图路径 | 说明 |
|---|-------------|------|------|---------|------|

## 缺陷/阻塞项
| # | 编号 | 分类 | 问题 | 预期 | 实际 | 差异 | 建议 |
|---|------|------|------|------|------|------|------|

## Output Contract 校验
├── browser-e2e-result.md：✅
├── 所有场景有截图：✅
├── 失败场景有 diff：✅
└── scenario 数 ≥ TC 场景数：✅

## 结论
├── ✅ 通过 → 进入 PM 验收
└── ❌ 未通过 → RD 修复后重新 Browser E2E
```
