# Codex Agent 定义文件

> 本目录包含 Codex CLI 的自定义 agent 定义。
> 安装时由 `install.sh` 复制到项目的 `.codex/agents/` 目录。
> 
> 📎 这些 toml 文件定义了 Codex 版 Teamwork 的 Subagent，
>    与 Claude Code 的 Task 工具等价。PMO 在 prompt 中引用 agent name 即可 spawn。

## 文件索引

| 文件 | 对应 Stage | 说明 |
|------|-----------|------|
| rd-developer.toml | Dev Stage | RD TDD 开发 + 单元测试 |
| reviewer.toml | Review Stage | 架构师 CR ∥ QA 代码审查（并行） |
| tester.toml | Test Stage | 集成测试 ∥ API E2E |
| planner.toml | Goal-Plan Stage | PM PRD + PL-PM 讨论 + 评审 |
| designer.toml | UI Design / Panorama | Designer UI 设计 |
| e2e-runner.toml | Browser E2E Stage | 浏览器端到端测试 |
| **prd-reviewer.toml** | Goal-Plan Stage（PRD 交叉评审） | 外部视角审查 PRD.md（详见 templates/codex-cross-review.md）|
| **blueprint-reviewer.toml** | Blueprint Stage（TC+TECH 交叉评审）| 外部视角审查 TC.md + TECH.md（详见 templates/codex-cross-review.md）|

---

## 🔴 默认推理深度 + service_tier 配置（v7.3.10+P0-37 新增）

### 全局默认（所有 profile 统一）

```toml
model_reasoning_effort = "high"   # 避免 codex 默认 xhigh 深度思考导致卡死
service_tier = "fast"             # OpenAI API priority tier，加速响应
```

### 为什么默认 high + fast

**`model_reasoning_effort = "high"`（codex 内部推理深度）**

可选值：`low | medium | high | xhigh`

- 🟢 **`high` 是新默认**：质量足够 + 响应时间可控（实测 30-180 秒/调用）
- ❌ **`xhigh` 是 codex CLI 自身的默认**：极深度思考模式，单次调用可能 5-15 分钟，**容易卡死或被宿主超时杀掉**（用户实战 case）
- ⚠️ `medium` / `low`：响应更快但 cross-review 质量可能不足以发现深层 finding，不建议作为默认

**`service_tier = "fast"`（OpenAI API priority tier）**

可选值：`standard | fast`（仅 OpenAI 账户支持时生效）

- 🟢 **`fast` 是新默认**：API 层 priority tier，明显减少排队等待
- ❌ **`standard` 是 OpenAI API 自身的默认**：在 API 高负载时会排队，叠加 codex 自身推理时间放大耗时
- 📎 **配额关系**：`fast` tier 计费可能略高（按 OpenAI 当时的定价模型），但稳定性收益远超成本——卡死的代价是整个 Feature 流转中断 + 用户介入诊断

### 何时调整

```
默认 high + fast 适用绝大多数场景。以下例外考虑覆盖：

⏬ 调低（reasoning_effort = medium / low）：
  ├── 简单 Bug 流程的快速 PRD 评审（业务方向已明确）
  ├── 项目早期原型阶段，追求迭代速度
  └── OpenAI 配额紧张需要降本

⏫ 调高（reasoning_effort = xhigh）：
  ├── 极复杂业务逻辑的关键决策点（如新业务线启动的 Goal-Plan Stage 评审）
  ├── 必须配合宿主超时上调（gtimeout / timeout 至少 30 min）
  └── 仅作为单次 ad-hoc 覆盖，不建议作为 profile 默认

🔄 service_tier 调整：
  ├── 用户 OpenAI 账户不支持 fast tier → 改 standard（不会报错，但耗时上升）
  └── 注释掉 service_tier 行 → 走 codex 默认（即 standard）
```

### 用户级覆盖

如果用户希望对某个 profile 单独调整，可：

1. **就地编辑 `.codex/agents/{profile}.toml`**：直接改 `model_reasoning_effort` / `service_tier` 值
2. **临时命令行覆盖**（仅本次调用）：`codex -c model_reasoning_effort=medium ...`
3. **覆盖默认 + 不影响其他用户**：在项目根 `.codex/config.toml` 顶层覆盖（codex CLI 配置加载层级允许 profile 覆盖全局）

### 与红线 #14 的关系

红线 #14（AI Plan 模式 - Execution Plan）要求 AI 在 Stage 入口枚举子步骤 + cite 规范文件。当 codex profile 被 dispatch 时，**developer_instructions 段已包含必读 spec 列表**，但实际执行深度由 `model_reasoning_effort` 控制。high 是合理 baseline，xhigh 容易导致 AI 在 Plan 模式纸面分析阶段就卡住。

📎 **历史 case**：v7.3.10+P0-37 之前 7 个 profile 没显式设置 `model_reasoning_effort` → fallback 到 codex 默认 `xhigh` → 用户实战中 codex 调用经常超时或表面"无响应"（实际仍在深度推理）。本次统一显式默认到 high 解决这一问题。
