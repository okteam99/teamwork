# PMO 自动推进规则 + auto 模式详规范（PMO Auto Mode · v7.3.10+P0-94 抽出）

> 🔗 **角色契约见 [roles/pmo.md](./pmo.md)**（PMO 项目管理 + 调度协调）。本文件是 PMO 自动推进规则 + auto 模式（HITL/AFK 二分）的详细任务规范 · 是该任务的**权威源**。
>
> 本文件源流：原寄生在 roles/pmo.md L1051-1242 → **v7.3.10+P0-94 抽出本文件**（pmo.md 1415 → ~1230 行 · Wave 4 Phase 2）。
>
> 适用场景：
> - 阶段完成后 PMO 判断是否自动推进（无待确认 + 不在暂停条件 → 🚀 自动推进）
> - 用户通过 `/teamwork auto [需求]` 开启 AUTO_MODE 后 · PMO 在每个 ⏸️ 暂停点判定 HITL/AFK
>
> 🔗 相关单源：
> - **AUTO_MODE 入口** → [stages/init-stage.md § Step 0](../stages/init-stage.md)
> - **HITL 清单 / AFK 示例** → [rules/flow-transitions.md § ⏸️ HITL 清单 / AFK 示例](../rules/flow-transitions.md)
> - **决策点参考文档绝对路径** → [STATUS-LINE.md § 决策点参考文档绝对路径硬规则](../STATUS-LINE.md)

---

## 一、PMO 自动推进规则

### 1.1 核心规则

```
阶段完成后：
├── 🔴 二次校验：对照 RULES.md 暂停条件表 · 确认当前节点确实不在暂停条件中
├── 🟡 Test Stage 前置校验：若下一步 = Test Stage · 必须先输出「Test Stage 前置确认」
│   并等待用户选择 1/2/3 · 不得自动进入 Test Stage
├── 待确认 = 无 且 不在暂停条件中 且 不在 Test Stage 前 → 🚀 自动继续下一阶段（同一回复中）
└── 待确认 ≠ 无 或 命中暂停条件 或 处于 Test Stage 前置确认 → ⏸️ 暂停等待用户处理

⚠️ 关键：PMO 摘要只是进度追踪 · 不是暂停点！
   如果没有待确认项且二次校验通过（且不处于 Test Stage 前置确认）· 输出摘要后立即开始下一阶段的工作。
🔴 「待确认 = 无」是 PMO 自行判断的 · 为防误判 · 必须对照暂停条件表二次校验。
🟡 Test Stage 前置确认是强制暂停点 · 等价于「待确认 ≠ 无」。
```

### 1.2 示例（无待确认 → 自动继续）

```
📊 PMO 阶段摘要
├── ✅ 已完成：RD 开发+自查（Subagent 执行）
├── 📌 下一步：QA 代码审查（自动进行中...）
├── 🔴 待确认：无
└── 📋 整体进度：7/11

---
[立即开始 QA 代码审查 · 不等待用户]
```

### 1.3 示例（有待确认 → 暂停）

```
📊 PMO 阶段摘要
├── ✅ 已完成：QA 项目集成测试
├── 📌 下一步：等待用户确认
├── 🔴 待确认：
│   ├── 1. API /api/v1/login 返回 500 · 需确认是代码问题还是环境问题
│   └── 2. 测试账号权限不足 · 需用户提供管理员账号
└── 📋 整体进度：9/11（⏸️ 阻塞中）

请确认上述问题后继续。
```

---

## 二、auto 模式 ⏸️ 暂停点 mode 判定（v7.3.9+P0-11 / v7.3.10+P0-76 mode 字段化）

> 🔴 **入口**：用户通过 `/teamwork auto [需求]` 开启 AUTO_MODE（详见 [stages/init-stage.md § Step 0](../stages/init-stage.md)）。
>
> 🔴 **作用域**：**单次命令周期**。不持久化 · 不写 localconfig · 不写 state.json。
>
> 🔴 **mode 字段（v7.3.10+P0-76）**：每个 ⏸️ 暂停点二选一：
> - **⏸️ HITL**（Human-In-The-Loop）= 强制保留 · auto **不豁免** · 涉及新业务判断 / 技术分歧 / 破坏性授权 / 红线 / 决策类暂停点
> - **⏸️ AFK**（Away-From-Keyboard）= auto 模式可豁免 · 按 💡 建议自动推进 + 输出 `⚡ auto skip` 日志
>
> 单源在 [rules/flow-transitions.md § ⏸️ HITL 清单 / AFK 示例](../rules/flow-transitions.md)；决策类暂停点 ⊆ HITL（详见 [STATUS-LINE.md § 决策点参考文档绝对路径硬规则](../STATUS-LINE.md)）。

### 2.1 触发时机

```
PMO 在每个 ⏸️ 暂停点判定分支：
1. 检查 AUTO_MODE 当前值
   ├── false（默认）→ 走 ⏸️ 原流程 · 等用户确认
   └── true → 进入下方 2
2. 对照"强制保留清单"判定
   ├── 命中任一强制保留项 → 仍 ⏸️ · 输出「⚡ auto 模式但此暂停点强制保留」提示行
   └── 未命中 → ✅ 豁免：按 💡 建议自动执行 + 输出 ⚡ auto skip 日志行
```

### 2.2 🔴 元规则：意图承载豁免（v7.3.9+P0-11-A 修订）

```
判定暂停点保留 / 豁免前 · 先问一句：
"这个暂停点需要用户给出的决策内容 · 是不是已经被 auto 命令本身承载了？"

├── 是（只是「是否继续/恢复/启动」类）→ ✅ 豁免
│   └── 例：外部依赖已就绪 → 恢复 / 阶段切换确认 / Planning 最终汇总
└── 否（需要新的业务判断 / 技术分歧 / 破坏性授权 / 红线处理）→ 🔴 保留
    └── 例：PM 验收三选项 / Ship push 授权 / MUST-CHANGE / 破坏性操作 / 红线触发

🔴 反模式：把所有 ⏸️ 都当强制保留 → auto 模式坍缩为手动模式 · 违反设计意图
🔴 反模式：auto 命令里明说"推进到 X 完成" · 却被中间"恢复确认"卡住 → 把用户的命令意图当空气
```

---

## 三、✅ ⏸️ AFK 暂停点（按 💡 建议自动推进 · v7.3.10+P0-76 mode=AFK）

| 暂停点 | 豁免动作 | 归类 |
|--------|---------|------|
| triage-stage → Goal-Plan Stage（环境配置已在 triage 决定） | 按 💡 推荐的流程类型 + 环境配置自动进入 Goal-Plan Stage | 意图承载 |
| PRD 待确认 | 按 💡（有 UI → UI Design / 无 UI → Blueprint）自动流转 | 意图承载 |
| 设计批待确认 | 按 💡（有问题 → 重跑 / 通过 → Blueprint）自动流转 | 意图承载 |
| 方案待确认 | 自动进入 Dev Stage | 意图承载 |
| 问题排查梳理 → 排查待确认 | 按 💡 推荐路径（Feature / Bug / 结束）自动流转 | 意图承载 |
| Roadmap 待确认 / teamwork_space.md 待确认 / Workspace Planning 收尾 | 按 💡 自动确认 | 意图承载 |
| 精简 PRD 待确认（敏捷）| 自动进入 BlueprintLite | 意图承载 |
| Micro 分析 → PMO 执行改动（主对话直接改）| 按 💡 自动进入（PMO 自行判断执行方式 · 无需暂停）| 意图承载 |
| 阶段完成 → 下一阶段切换 | 自动流转（本来就是 🚀 自动 · auto 不影响）| 本就自动 |
| **外部依赖已就绪 → 恢复流程**（P0-11-A 修订）| auto 命令已承载"恢复"意图 → 按 💡 自动恢复 | 意图承载 |
| **Test Stage → Browser E2E Stage**（有 Browser E2E 场景 · P0-11-B 新增）| **默认跳过 Browser E2E · 直接进 PM 验收**；留痕到 state.json + review-log.jsonl | 成本取舍 |

---

## 四、🟡 Browser E2E auto 默认跳过（P0-11-B 新增专项规则）

```
触发：AUTO_MODE=true + Test Stage 完成 + TC.md 标注有 Browser E2E AC
    ↓
PMO 默认决策：⏭️ 跳过 Browser E2E Stage · 直接进 PM 验收
    ↓
留痕（3 处同步）：
├── state.json.stage_contracts.browser_e2e = {
│     status: "SKIPPED_BY_AUTO",
│     skipped_at: "{timestamp}",
│     skip_reason: "AUTO_MODE 默认跳过 Browser E2E（P0-11-B）"
│   }
├── review-log.jsonl append：
│   { stage: "browser_e2e", status: "SKIPPED", skip_reason: "AUTO_MODE 默认跳过", commit: "{HEAD}" }
└── PMO 输出 ⚡ auto skip 日志：
    ⚡ auto skip: Browser E2E Stage | 💡 auto 默认跳过 | 📝 避免 headless 浏览器启动成本；PM 验收可选择不通过回退补跑

后续影响：
├── PM 验收暂停点模板中「Browser E2E 状态」标注 ⏭️ 跳过（auto 默认）
├── PMO 完成报告「QA Browser E2E」行必须显式标注：⏭️ AUTO_MODE 默认跳过（非通过）
└── 用户验收时可选 3（不通过）+ 理由「需补 Browser E2E」→ PMO 派发 Browser E2E Stage 补跑

例外（不跳过的场景）：
├── 用户命令显式包含 "含 browser e2e" / "跑 e2e" / "跑 browser" 关键词 → 不跳过
├── TC.md 在 Browser E2E AC 条目显式标注 `required_even_in_auto: true` → 不跳过
└── 手动模式（AUTO_MODE=false）→ 走原 flow-transitions.md L29-L30 正常流程
```

**设计理由**：Browser E2E 启动成本高（headless 浏览器 / MCP 握手 / 脚本录制回放）· auto 场景多为快速推进验证主流程 · 默认跳过符合高频意图；留痕 + PM 验收兜底保证"必要时可回退补跑"。

---

## 五、🔴 ⏸️ HITL 暂停点（强制保留 · 即便 AUTO_MODE=true 也不豁免 · v7.3.10+P0-76 mode=HITL）

> 🔴 **修订原则**（P0-11-A）：仅需要**新决策内容**的暂停点才保留。"是否继续/恢复/启动"类 → 由 auto 命令语境承载 → 豁免。

| # | 暂停点 | 强制保留理由 |
|---|--------|------------|
| 1 | PM 验收三选项（通过+Ship / 通过暂不 Ship / 不通过）| 业务判断 · 非 PMO 可替用户决 |
| 2 | Ship Stage worktree 清理待确认 | 用户偏好不可替决 |
| 3 | Ship Stage push FAILED（v7.3.10+P0-15）| push feature 失败不可替决 · 用户决定手工处理/取消 |
| 4 | Dev Stage / Test Stage BLOCKED / FAILED | 环境/逻辑异常 · 人工诊断 |
| 5 | Review Stage 架构师输出 MUST-CHANGE | 架构级重大决策 |
| 6 | Blueprint Stage / Review Stage concerns 需用户判断 | 非阻塞问题但需人判断价值 |
| 7 | PL-PM 分歧项（Goal-Plan Stage 分歧分支）| 设计/产品分歧不可替决 |
| 8 | Test Stage 前置确认（立即 / 延后 / 跳过）| 跨 Feature 节奏决策 |
| 9 | Micro 流程「用户验收」和「升级确认」| Micro 唯一把关点 + 规模升级需用户拍板 |
| 10 | 15 条绝对红线触发时 | 红线不容豁免 |
| 11 | 破坏性 git / DB 操作（force push / hard reset / drop 表 / 删分支）| 不可逆操作 |
| 12 | 用户消息出现「？/ 确认下 / 等我看看 / 核对一下 / 先等等」等意图不确定语气 | 用户明确想参与决策 |

> 🗑️ **P0-11-A 移除项**：
> - ~~外部依赖已就绪 → 恢复流程~~ → 归入豁免（auto 命令已承载"恢复"意图）
> - ~~Planning / PL 模式的最终确认~~ → 归入豁免（上方"Roadmap / teamwork_space / Workspace Planning 收尾"行覆盖）

---

## 六、跳过日志格式

```
⚡ auto skip: {决策简述} | 💡 {建议原文} | 📝 {理由}
```

**示例**：
```
⚡ auto skip: PRD 待确认 → UI Design Stage | 💡 PRD 有 UI 标记 · 按 PRD 中「需要 UI: 是」路径进入 UI Design | 📝 无分歧项 · 无 MUST-CHANGE · 符合豁免条件
```

---

## 七、强制保留命中时的提示格式

```
⚡ auto 模式已开启 · 但此暂停点强制保留
├── 暂停点：{暂停点名}
├── 保留理由：{对照强制保留清单第 N 项：{理由}}
└── ⏸️ 仍需用户确认 · 请从以下选项中选择...
```

---

## 八、PMO 自检清单（每次暂停点判定必过）

```
□ AUTO_MODE 当前值已读取？
□ 已对照"强制保留清单 12 条"逐项核对？
□ 若豁免 → 已按 💡 建议生成决策内容 + 输出 ⚡ auto skip 日志行？
□ 若保留 → 已输出「强制保留」提示 + 原 ⏸️ 暂停点模板？
□ 用户消息中是否含「停/暂停/manual/等一下/先等等」？含则立即 AUTO_MODE=false
```

---

## 九、运行时关闭

用户在任意消息中出现下列关键词 → PMO 立即 `AUTO_MODE=false` · 当前和后续暂停点恢复 ⏸️：

- `停` / `暂停` / `manual` / `等一下` / `先等等` / `先确认一下` / `让我看看`

关闭后输出：

```
⚡ AUTO_MODE 已关闭（触发词：「{关键词}」）| 当前暂停点改为 ⏸️ 等确认
```
