# PMO 外部模型评审调度详规范（PMO External Model Orchestration · v7.3.10+P0-93 抽出）

> 🔗 **角色契约见 [roles/pmo.md](./pmo.md)**（PMO 项目管理 + 调度协调）。本文件是 PMO 在 triage / 各 Stage 入口实例化时调度 external 评审角色的详细任务规范 · 是该任务的**权威源**。
>
> 本文件源流：原寄生在 roles/pmo.md L498-678 → **v7.3.10+P0-93 抽出本文件**（pmo.md 1814 → ~1400 向 ~500 cap 推进 · Wave 4 Phase 1）。
>
> 适用场景：PMO 在 triage Step 4 角色可用性扫描 + 各 Stage 入口实例化（Plan / Blueprint / Review）时调度 external 评审角色。
>
> 🔗 相关单源：
> - **External 角色契约**（异质性 / 立场独立性）→ [roles/external-reviewer.md](./external-reviewer.md)
> - **异质性 + E1/E2/E3 规范** → [standards/external-model.md](../standards/external-model.md)
> - **Stage 调度契约** → [stages/triage-stage.md](../stages/triage-stage.md) + [stages/blueprint-stage.md](../stages/blueprint-stage.md) + [stages/review-stage.md](../stages/review-stage.md)

---

## 一、设计变化（v7.3.10+P0-38 重构 · 兼容层文档）

🆕 v7.3.10+P0-38 关键变化：external 升格为评审角色（[roles/external-reviewer.md](./external-reviewer.md)）· 与 PL/RD/QA/Designer/PMO/Architect 平级。

- **角色可用性扫描**移到 [stages/init-stage.md](../stages/init-stage.md) Step 1.x（一次性）
- **triage Step 8** 仅输出骨架（execution_hints 文本是否推荐 external · 由 triage Step 4 扫描的 available_roles 决定）
- **是否实际启用** 在各 Stage 入口实例化时由 PMO 决策（基于 execution_hints + 上游产物复杂度）
- **不再有** plan_enabled / blueprint_enabled / review_enabled 三字段（已删）
- **不再有** 独立"外部模型评审决策"暂停点（已合并到骨架决策块）

下方保留的内容是 P0-28 兼容层文档（含老 Feature 行为说明）· 新 Feature 走骨架 + 入口实例化模式。

🔗 **本段是 [stages/triage-stage.md § Step 4](../stages/triage-stage.md) 的角色实现规范**（v7.3.10+P0-26）。triage-stage 定义阶段 IO 契约 · 本段定义 PMO 执行细节。

**历史**：v7.3.9+P0-13 引入"Codex 交叉评审"开关 · 硬编码使用 Codex 作为外部模型。v7.3.10+P0-24 重构为"外部模型"语义——具体使用哪个外部模型由 PMO 在 triage-stage 阶段**运行时探测**决定 · 规范层不再硬编码"宿主→外部模型"对应表。规范见 [standards/external-model.md](../standards/external-model.md)。

---

## 二、影响范围（v7.3.10+P0-38 重构 / +P0-54 修正）

```
🟢 v7.3.10+P0-38 起：external 升格为评审角色 · 是否启用看
   state.{stage}_substeps_config.review_roles[] 是否含 external（不再用独立 _enabled 字段）

🟡 各 Stage 默认推荐：
   - Goal-Plan Stage：v7.3.10+P0-83 删 external（不再支持 Goal-Plan external 评审）
   - Blueprint Stage：默认不含 external / 推荐启用（架构层异质视角 · 教训密集区 / 跨子项目 / 触发 ADR）
   - Review Stage：默认推荐含 external（代码层最后 gate · 异质模型核心价值）

🔴 PMO 在 Stage 入口实例化时基于 execution_hints + 信号决策（详见 standards/stage-instantiation.md）
```

📎 老字段（plan_enabled / blueprint_enabled / review_enabled）已在 v7.3.10+P0-38 删除（state.external_cross_review 不再含此三字段）。如发现仍引用此三字段 · 视为漂移 · 应改为 `external ∈ review_roles[]` 单源判定。

---

## 三、Step 1：PMO 直接判定（v7.3.10+P0-72 删探测脚本）

PMO 自报当前主对话宿主（基于自身运行环境 · 不读项目目录标记）+ 一行 bash 检查候选 CLI 可用性：

```bash
command -v codex   # 候选 1
command -v claude  # 候选 2
```

应用 E1 同源约束识别异质 CLI（详见 [standards/external-model.md § 四 PMO 直接判定](../standards/external-model.md)）。

---

## 四、Step 2：PMO 渲染「🌐 外部模型判定」段

> 该段必须出现在 PMO 初步分析输出顶部（KNOWLEDGE 扫描之后 · 流程类型识别之前）。

**有可用候选时**：

```markdown
## 🌐 外部模型判定

主对话宿主: {host_main_model}
外部 CLI 可用性：
- {id}    {✅ 可用（运行时需已认证）/ ⚠️ 与主对话同源 / ❌ 未安装}
- ...

候选外部模型: {available_external 列表}
```

**无可用候选时**：

```markdown
## 🌐 外部模型判定

主对话宿主: {host_main_model}
候选外部模型: 无（所有候选要么未安装 · 要么与主对话同源）
外部交叉评审: 不可用 · 本 Feature 流程将跳过此选项
```

---

## 五、Step 3：PMO 智能推荐表（v7.3.10+P0-28 · 按 Feature 规模/风险）

PMO 用简单规则按 Feature 类型 + 关键词触发 · 输出推荐组合（v7.3.10+P0-83 删 Goal-Plan external · 仅 Blueprint/Review 适用）：

| Feature 场景 | 触发信号（任一命中） | Blueprint | Review |
|-------------|--------------------|-----------|--------|
| **大 Feature / 高风险** | 跨子项目 / ≥10 文件 / 新技术栈 / 重构 / 关键词 "支付/权限/数据一致性/性能/安全" / KNOWLEDGE.md 标注高风险领域 | ON 💡 | ON 💡 |
| **中 Feature** | 单子项目 + 5-10 文件 + 涉及 UI 或架构小改 | OFF | ON 💡 |
| **小 Feature / 敏捷需求** | ≤5 文件 / 无 UI/架构变更 / 复用既有模式 | OFF | ON 💡 |
| **Bug 修复** | Bug 流程（无文档评审需求 · 但代码改动需要外部 review）| OFF | ON 💡 |
| **Feature Planning / 问题排查 / Micro** | 不出代码 / 零逻辑变更 | N/A | N/A |

🟢 **核心原则**：Review 默认 ON（代码层最后 gate · 外部模型异质视角价值最高）；Blueprint 默认 OFF（文档评审有内部 4 视角支撑—— RD/Designer/QA/PMO + 架构师 · 外部模型边际价值低）。

---

## 六、Step 4：PMO 决策项呈现（v7.3.10+P0-28 · 两处独立 + 快捷选项）

有可用候选时：

```markdown
🌐 外部模型评审决策（影响 Blueprint / Review 两 Stage）

PMO 智能推荐（基于 Feature {规模/风险描述}）：
- Blueprint Stage（TC+TECH 评审）：{ON / OFF}
- Review Stage（代码评审）：{ON / OFF}

💡 1. 采用推荐组合 💡（详见上方）
   2. 两处全开（最高质量；典型 Feature ~+30 min + ~30K token）
   3. 两处全关（仅内部视角）
   4. 自定义（分别指定 Blueprint / Review）
   5. 其他指示
```

选项 4 进入二级决策：

```
🌐 自定义外部模型评审

请回复格式 "B=on/off R=on/off"
例如 "B=off R=on"（只开 Review）
或 "B=on R=on"（两处全开）
```

无可用候选时直接说明跳过 · 不出选项。

---

## 七、Step 5：用户选择 → state.json 写入（v7.3.10+P0-38 / +P0-54 修正）

```json
"external_cross_review": {
  "model": "codex" | "claude" | null,
  "host_main_model": "{PMO 自报宿主}",
  "host_detection_at": "{判定时刻 ISO 8601 UTC}",
  "available_external_clis": ["..."],
  "decided_at": "{ISO 8601 UTC}",
  "decided_by": "user",
  "note": "{用户选择理由 / PMO 推荐理由}",
  "reviewer_dispatches": []
}
```

📎 v7.3.10+P0-38 起 external 升格为评审角色 · 是否启用看 `state.{stage}_substeps_config.review_roles[]` 是否含 external —— 不再用 `plan_enabled / blueprint_enabled / review_enabled` 三字段（已删）。本对象仅保留 model / host / 探测元数据 + dispatch 历史。

---

## 八、Step 6：调用失败的运行时降级（E3 规则）

Blueprint / Review Stage 实际 dispatch 外部 review 时：

```
shell 调用外部 CLI（如 codex / claude --print）
  ↓
捕获 stderr + exit code
  ↓
exit code != 0 →
  - state.concerns 加 WARN（含 stderr 摘要 + 失败时刻）
  - state.external_cross_review.reviewer_dispatches[].status = "failed"
  - 跳过该 Stage 的外部 review · 继续主对话 review 链路
  - PMO 完成报告中显式列出"外部 review 降级"
```

🔴 静默降级（不写 state.concerns）违反 RULES.md 闭环验证红线。

---

## 九、兼容性（旧字段 · PMO 读取时 fallback 规则）

| 历史版本 | 字段位置 | fallback 处理 |
|---------|---------|---------------|
| v7.3.10+P0-24 之前 | `codex_cross_review` 字段 | 视为 model=codex |
| v7.3.10+P0-24 ~ P0-27 | `external_cross_review.enabled` 单字段 | 覆盖 Plan + Blueprint · Review 强制 ON |
| v7.3.10+P0-28 ~ P0-37 | `external_cross_review.{plan,blueprint,review}_enabled` 三字段 | 已废 |
| v7.3.10+P0-38 起（当前）| `state.{stage}_substeps_config.review_roles[]` 含 external | 单源判定 |

PMO 读老 state.json 时按以下优先级 fallback：

1. 优先看 `state.{stage}_substeps_config.review_roles[]` 是否含 external（P0-38 起的真相源）
2. 若 review_roles[] 缺失但有 `external_cross_review.{plan,blueprint,review}_enabled` 三字段（P0-28~P0-37 老 state）：
   - 老 enabled=true → 视为对应 stage 的 review_roles[] 含 external
   - 老 enabled=false → 视为不含
3. 若仅有 `external_cross_review.enabled` 单字段（P0-24~P0-27）：覆盖 Plan + Blueprint · Review 视为强制启用
4. 若仅有 `codex_cross_review`（P0-24 之前）：先 fallback 到 `external_cross_review.enabled` + model=codex · 再按上一步处理

🟢 **旧 Feature 不强制迁移** · 按 fallback 语义走完即可。

---

## 十、硬规则

- 🔴 PMO 初步分析必须**先自报宿主 + `command -v` 检查 CLI**（v7.3.10+P0-72）· 再渲染「🌐 外部模型判定」段 · 最后给决策项 · 三步不可省略
- 🔴 默认值（v7.3.10+P0-28 / +P0-83 修正）：blueprint_enabled=false / review_enabled=true（Goal-Plan external 已删）
- 🔴 用户未显式选择 → PMO 按智能推荐表给出的组合（不再是简单 OFF）· note 标注"用户未选择 · 取 PMO 推荐"
- 🔴 Review Stage 的外部模型代码评审受 review_enabled 控制（v7.3.10+P0-28）· 但默认 ON 不变
- 🔴 决策写入后各 Stage PMO 在入口 Read state.json 确认对应 *_enabled 值 · 不得推断
- 🔴 同源外部模型（如 Claude Code 主对话下选 claude）禁止启用 · PMO 渲染时不出该选项
- 🔴 dispatch 失败必须写 state.concerns + 降级 · 禁止静默
- 🔴 快捷选项「两处全开」/「两处全关」是用户便利 · 不影响 PMO 推荐逻辑
