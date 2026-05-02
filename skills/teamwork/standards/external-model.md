# 外部模型 / External Model 规范（v7.3.10+P0-24 新增）

> **定位**：定义 teamwork 中"外部模型交叉评审"的概念、候选清单、调用规范。**不规定**具体宿主下应该用哪个外部模型——这由 PMO 在初步分析阶段直接判定后决策，用户在暂停点选定。
>
> **核心思路**（与 v7.3 哲学一致）：
> - 规范层定义：**有哪些候选 / 什么算合法 / 调用如何进行 / 失败如何降级**
> - PMO 运行时决策：**当前环境下哪个候选可用 / 推荐哪个 / 用户选哪个**
>
> **三条硬规则**：
> - 🔴 **E1 异质性约束**：外部模型与主对话**必须不同源**（Claude Code 主对话不能用 Claude 做外部）
> - 🔴 **E2 PMO 直接判定**：主对话宿主由 PMO 自报（PMO 就在宿主里运行，自知），候选 CLI 可用性由一行 bash `command -v {cli}` 检查；不依赖探测脚本（v7.3.10+P0-72 删除目录标记探测脚本）
> - 🔴 **E3 失败优雅降级**：调用失败（CLI 未认证、网络等）→ state.concerns WARN → 自动降级单视角 review，不阻塞流程

---

## 一、概念定义

**外部模型 (External Model)**：在主对话之外提供独立 review 视角的**异质** AI 模型。

外部模型 ≠ 主对话的另一个角色。区别在于：

| 维度 | 主对话角色切换（架构师 / QA） | 外部模型 |
|------|----------------------------|---------|
| 模型架构 | 同模型不同 system prompt | **异质模型**（不同训练数据 / 评估倾向 / 错误模式） |
| 独立性 | 弱（同模型的盲区是同源的） | 强（异质模型的盲区互补） |
| 价值 | 注意力重分配 + 强制重读 | **真正的盲区互补** |

外部模型的**核心价值**是异质模型架构差异带来的盲区互补。同模型不同上下文，训练数据 / 评估倾向 / 错误模式是同源的，发现盲区的能力受限。

---

## 二、候选模型清单

teamwork 当前支持的候选外部模型：

| ID | 对应 CLI | 命令名 | 同源宿主 |
|----|---------|--------|---------|
| `codex` | OpenAI Codex CLI | `codex` | `codex-cli` |
| `claude` | Anthropic Claude Code | `claude` | `claude-code` |

未来加新模型（如 Gemini）只需在本表加一行 + 在 PMO 判定流程的 `command -v {cli}` 步骤里加一行检查，PMO 逻辑无需改动。

🔴 **不在本规范定义"宿主→外部模型"对应表**。具体用哪个候选由 PMO 在运行时根据自身宿主 + CLI 可用性 + 用户决策给出。

---

## 三、E1 异质性（同源）约束

**外部模型与主对话必须不同源**。具体规则：

- Claude Code 主对话宿主下：`claude` 候选**不可用**（自身同源），`codex` 可用
- Codex CLI 主对话宿主下：`codex` 候选**不可用**（自身同源），`claude` 可用
- 通用 / 未知宿主下：所有候选可用

🟢 **v7.3.10+P0-64 简化**：external_model 由 PMO 直接判定 + E1 同源约束自动决定，**用户不可在 localconfig 覆写**。框架不开放该字段，PMO 不读 localconfig 中任何 external_model override。这避免了"用户硬塞同源 = WARN 降级"的虚构边缘场景，规则更简洁。

---

## 四、E2 PMO 直接判定（v7.3.10+P0-72 删除探测脚本）

> v7.3.10+P0-72 之前曾有 `templates/detect-external-model.py` 探测脚本，基于项目根的 `.claude/` / `.codex/` / `.agents/` 等**目录标记**判定主对话宿主。实证暴露根本性缺陷：目录标记反映**项目历史**（曾被哪些宿主访问过 / 装过 teamwork skill），不反映**当前对话宿主**。两者经常不一致，导致探测错误（实战 WEB-F028 / Codex 主对话被误判为 claude-code）。
>
> 修复方向：宿主探测不该是脚本职责——**PMO 自身就在宿主里运行，自知**。脚本反而是错误信号源。本 patch 直接删脚本，由 PMO 直接判定。同期废止 v7.3.10+P0-71 "Stage 入口重探测"硬规则（再探测错的还是错的，根因是探测方法不可靠）。

PMO 在 Feature 流程的**初步分析阶段**直接判定，三步完成：

```
Step 1: PMO 自报宿主（基于自身运行环境）
        ├── 主对话是 Claude Code → host_main_model = "claude-code"
        ├── 主对话是 Codex CLI → host_main_model = "codex-cli"
        ├── 主对话是 Gemini CLI → host_main_model = "gemini-cli"
        └── 通用 / 无法识别 → host_main_model = "unknown"
        🔴 依据当前运行时特征（system prompt / tool 集 / 环境变量），不读项目目录标记

Step 2: 检查候选 CLI 可用性（bash 一行）
        ├── command -v codex  （exit 0 → codex CLI 已装）
        ├── command -v claude （exit 0 → claude CLI 已装）
        └── 未来加候选只需新增一行 command -v {cli}

Step 3: 应用 E1 同源约束 + 写 state
        ├── 剔除与 host_main_model 同源的候选
        ├── 剩余 → state.external_cross_review.available_external_clis[]
        └── 写 state.external_cross_review.host_main_model
```

### 边界

🔴 **PMO 只回答两个确定性问题**：
1. 主对话宿主是什么（PMO 自报，不查目录标记 / 配置文件）
2. 候选 CLI 是否在 PATH（一行 `command -v`）

🔴 **不查 API key / OAuth 状态**。理由：
- Claude Code / Codex CLI 默认走 OAuth，不读对应的 env var
- shell 子进程环境继承不确定（取决于宿主 bash tool 实现）
- 配置文件位置多样（`~/.claude/.credentials.json` / `~/.codex/auth.json` 等）
- 强查会**误报**（OAuth 已登录但 env var 未设的用户被错标"不可用"）

🔴 **认证失败检测延后到运行时**：dispatch 时 shell 调用 CLI 失败 → 捕获 stderr → state.concerns WARN → 降级（见 §六）。

### 跨 session 切宿主的处理

PMO 在每个启用 external 的 Stage 入口实例化时**直接按当前宿主判定**（不读 state 旧值）。state.json 中 `host_main_model` 字段是**历史快照**，不是判定依据：

- Feature 启动时（triage Step 4）写入 host_main_model = 当前 PMO 自报宿主
- 后续 Stage 入口若 PMO 自报与 state 旧值不一致 → 按当前自报值更新 state + 写 concerns 记录"host_main_model 漂移：{old} → {new}"
- 主对话显式声明切换："external 候选已切换（{old_model} → {new_model}），主对话宿主从 {old_host} 变为 {new_host}"

🔴 **不依赖任何探测脚本来发现漂移**——PMO 在 Stage 入口本就要自我宿主感知（每次都自知）。这与"探测脚本+缓存"的复杂结构相比，少一层间接、少一类失败模式。

### PMO 渲染输出

PMO 在初步分析输出中加「🌐 外部模型判定」段：

```markdown
## 🌐 外部模型判定

主对话宿主: claude-code
外部 CLI 可用性：
- codex     ✅ 可用（运行时需已认证）
- claude    ⚠️ 与主对话同源，不可作外部模型

候选外部模型: codex
```

无任何可用候选时：

```markdown
## 🌐 外部模型判定

主对话宿主: claude-code
候选外部模型: 无（所有候选要么未安装，要么与主对话同源）
外部交叉评审: 不可用，本 Feature 流程将跳过此选项
```

---

## 五、调用规范

### 5.1 dispatch 文件协议

外部模型 dispatch 沿用 teamwork 现有的 dispatch 文件协议，文件命名：

```
{Feature}/dispatch_log/{NNN}-external-{model}-review.md
```

例如：`dispatch_log/003-external-codex-review.md` / `dispatch_log/005-external-claude-review.md`。

### 5.2 调用入口

按主对话宿主 + 选定外部模型组合，调用入口约定：

| 主对话宿主 | 外部模型 | 调用入口 |
|-----------|---------|---------|
| `claude-code` | `codex` | `{SKILL_ROOT}/codex-agents/reviewer.toml`（已存在） |
| `codex-cli` | `claude` | `{SKILL_ROOT}/claude-agents/invoke.md`（shell 调用范本） |
| 通用 | 任一可用候选 | 按上述映射 |

### 5.3 产物格式

外部模型 review 产物落盘到：

```
{Feature}/external-cross-review/{stage}-{model}.md
```

例如：`external-cross-review/blueprint-codex.md` / `external-cross-review/review-claude.md`。

产物头部 YAML frontmatter（机读）：

```yaml
---
external_model: codex
generated_at: <ISO 时刻>
reviewed_artifacts:
  - PRD.md
  - TECH.md
findings_count: 3
severity_max: high
---
```

### 5.4 state.json 字段（v7.3.10+P0-54 链接化）

> 🔴 **v7.3.10+P0-38 起 external 升格为评审角色**，启用条件改为 `external ∈ state.{stage}_substeps_config.review_roles[]`（不再用老的 `plan_enabled / blueprint_enabled / review_enabled` 三字段）。
>
> state.json 中 `external_cross_review` 对象仅保留：`model / host_main_model / host_detection_at / available_external_clis / reviewer_dispatches[]` 元数据 —— 完整 schema 见 [templates/feature-state.json](../templates/feature-state.json)。
>
> 各 Stage 启用决策详见对应 stage spec：
> - [stages/goal-plan-stage.md § 评审组合智能推荐表](../stages/goal-plan-stage.md)
> - [stages/blueprint-stage.md § Stage 入口实例化](../stages/blueprint-stage.md)
> - [stages/review-stage.md § Stage 入口实例化](../stages/review-stage.md)
>
> Fallback 兼容（老 state.json 读取规则）详见 [roles/pmo.md § 兼容性（旧字段）](../roles/pmo.md)，本文件不复述。

## 六、E3 失败降级策略

外部模型 dispatch 失败的可能原因：

1. CLI 未认证（OAuth 未登录、API key 未设）
2. 网络不可达
3. CLI 调用 timeout
4. CLI 内部错误（quota / 模型不可用 / 等）

**降级流程**：

```
PMO dispatch 外部 review
  ↓
shell 调用外部 CLI（如 claude --print 或 codex CLI）
  ↓
捕获 stdout/stderr + exit code
  ↓
exit code != 0 →
  - state.concerns 加 WARN（含 stderr 摘要）
  - state.external_cross_review.reviewer_dispatches[].status = "failed"
  - 跳过该 Stage 的外部 review，继续主对话 review 链路
  - 在 PMO 完成报告中显式列出"外部 review 降级"
```

🔴 静默降级（不写 state.concerns）违反 RULES.md 闭环验证红线。

---

## 七、与其他规范的协作

| 规范 | 协作点 |
|------|--------|
| `prompt-cache.md` | 外部模型调用属 L3 动态层，dispatch 文件不参与 prompt cache 命中 |
| `common.md` | 外部模型不参与代码生成，只参与 review；不影响 TDD / Lint 硬门禁 |
| `RULES.md` | 调用失败时的 WARN 落盘是闭环验证红线的一部分 |
| `stages/init-stage.md` | init-stage 只检测主对话宿主，不预设外部模型；外部模型由 PMO 在 triage-stage 运行时探测 |
| `roles/pmo.md` | PMO 在初步分析时直接判定（v7.3.10+P0-72 自报宿主 + `command -v` 检查 CLI）+ 渲染「🌐 外部模型判定」段 + 决策点呈现 + 失败降级 |
| `STATUS-LINE.md` | 启用外部 review 时 Status Line 显示 `[Ext: {model}]` 徽章 |

---

## 八、本规范不覆盖

- ❌ 跨 Feature 的外部 review 缓存复用（每个 Feature 独立探测）
- ❌ 外部模型选择的 A/B 评估自动化（哪个外部模型对当前 Feature 更有效）
- ❌ 外部模型自身的 prompt 优化（属于 `claude-agents/reviewer.md` / `codex-agents/reviewer.toml` 的内部）
- ❌ 同时启用多个外部模型（当前规范单 Feature 只用一个外部模型）

---

## 九、版本记录

- v7.3.10+P0-24（首次发布）：定义外部模型语义 + 候选清单 + PMO 运行时探测（基于探测脚本）+ 调用规范 + 失败降级
- v7.3.10+P0-71（已废止）：曾加 Stage 入口重探测硬规则（基于探测脚本）—— P0-72 删脚本时一并移除（再探测错的还是错的，根因是脚本不可靠）
- v7.3.10+P0-72：删除 `templates/detect-external-model.py` 探测脚本，改为 PMO 直接判定（自报宿主 + `command -v` 检查 CLI）；同期废止 P0-71 重探测硬规则
