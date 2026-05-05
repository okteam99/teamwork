# PMO 跨项目协调详规范（PMO Cross-Project · v7.3.10+P0-95 抽出）

> 🔗 **角色契约见 [roles/pmo.md](./pmo.md)**（PMO 项目管理 + 调度协调）。本文件是 PMO 在 triage Stage 处理跨子项目需求 + 变更归属的详细任务规范 · 是该任务的**权威源**。
>
> 本文件源流：原寄生在 roles/pmo.md 三段（跨项目依赖识别 / 跨子项目需求拆分 / 变更归属检查）→ **v7.3.10+P0-95 抽出本文件**（pmo.md 1231 → ~1030 向 ~500 cap 推进 · Wave 4 Phase 3）。
>
> 适用场景：
> - **场景 A 单 Feature 上游依赖**（§ 一）：本 Feature 单一归属 · 需上游子项目能力 → DEP 登记
> - **场景 B 跨子项目需求拆分**（§ 二）：需求横跨多子项目 · 无主 Feature 归属 → 拆分为多个并行 Feature
> - **变更归属检查**（§ 三）：triage Step 6.5 必做 · 防"边规划边启动"反模式（v7.3.10+P0-33 硬约束）
>
> 🔗 相关单源：
> - [stages/triage-stage.md § Step 6 / 6.5](../stages/triage-stage.md)（Stage 调度契约）
> - [templates/dependency.md](../templates/dependency.md)（DEPENDENCY-REQUESTS.md 格式权威）
> - [roles/product-lead-change-mgmt.md](./product-lead-change-mgmt.md)（PL 变更管理详规范 · v7.3.10+P0-92 抽出）
> - [templates/teamwork-space.md](../templates/teamwork-space.md)（多子项目模式索引）

---

## 一、跨项目依赖识别（场景 A · v7.3.9+P0-8 新增）

> 🔗 **本段是 [stages/triage-stage.md § Step 6](../stages/triage-stage.md) 的角色实现规范**（v7.3.10+P0-26）。triage-stage 定义阶段 IO 契约 · 本段定义 PMO 执行细节。

**触发**：PMO 在 triage-stage 处理需求时 · 识别到**当前 Feature 单一归属子项目**但**需要另一子项目提供能力**（场景 A · 区别于下方"跨子项目需求拆分"场景 B）。

**识别信号**：需求描述 / PRD 初稿 / 用户对话中出现 "调用 / 访问 / 接入 / 对接 / 需要 / 依赖 ... {其他子项目}的 {能力}"。

### 1.1 两种场景区分（必读）

```
场景 A：单 Feature 上游依赖（本章节覆盖）
├── 本 Feature 归属明确的子项目（如 PTR-F004 在 apps/partner/）
├── 需要上游子项目（如 services/core-api/ · services/platform-api/）提供已有或新开发能力
├── 处理方式：在上游子项目 {upstream}/docs/DEPENDENCY-REQUESTS.md 追加 DEP-N 条目
└── 适用大多数"下游消费方 Feature"

场景 B：横跨多子项目的新需求（走 § 二「跨子项目需求拆分」）
├── 需求 naturally 横跨多子项目 · 没有明确的"主 Feature"归属
├── 例：新增一条端到端业务链路 · 三个子项目各自有新能力
├── 处理方式：PMO 拆分为多个并行 Feature · 各走各的流程
└── 对应 ROADMAP 的跨项目追踪表
```

### 1.2 场景 A 处理流程

```
PMO 识别到上游依赖信号
    ↓
🔴 Read templates/dependency.md → 锁定 DEPENDENCY-REQUESTS.md 格式基准
    ↓
确认上游子项目路径（从 teamwork_space.md）
    ↓
检查 {upstream}/docs/DEPENDENCY-REQUESTS.md 是否存在
├── 存在 → Read 取最新 DEP 编号 · 准备 append
└── 不存在 → 新建（Read templates/dependency.md 为基准 · 🔴 禁止抄其他子项目的 DEPENDENCY-REQUESTS 为格式参考）
    ↓
Write {upstream}/docs/DEPENDENCY-REQUESTS.md · 追加 DEP-N 条目：
├── 请求方 = 本 Feature 所在子项目
├── 关联 Feature = 本 Feature 编号
├── 期望能力（消费方描述需要什么 · 不预设实现）
├── 接口定义留空（由上游方处理时填写）
└── 状态 = ⏳ 待处理
    ↓
本 Feature state.json.blocking.pending_external_deps 引用 DEP-N 编号
    ↓
PMO 告知用户：上游 DEP-N 已登记 · 上游方启动 teamwork 时 PMO 会扫描提醒
```

### 1.3 场景 A 硬规则

- 🔴 DEPENDENCY-REQUESTS.md **只放上游子项目目录**（`{upstream}/docs/`）· 不放消费方 Feature 目录
- 🔴 **禁止**在消费方 Feature 目录自创 DEPS.md / DEPENDENCIES.md / 其他非标文件名
- 🔴 Write 前必 Read [templates/dependency.md](../templates/dependency.md) 为格式基准（P0-7 红线）
- 🔴 多条上游依赖 → 多条 DEP 条目（可能分散到不同上游子项目）· 不要合并成一个大文件

### 1.4 与场景 B 的决策点

用户或 PMO 无法判定时 → ⏸️ 列出两种场景的特征 · 让用户选。

---

## 二、跨子项目需求拆分（场景 B · 多子项目模式）

**触发**：PMO 分析需求时发现涉及多个子项目（参考 [templates/teamwork-space.md](../templates/teamwork-space.md)）

**职责**：读取 teamwork_space.md 判断需求影响范围 · 输出拆分方案 · 暂停等用户确认。

### 2.1 拆分流程

```
PMO 读取 teamwork_space.md
    ↓
PMO 判断需求影响哪些子项目：
├── 单子项目 → 直接进入该子项目的标准流程
└── 多子项目 → 执行拆分
    ↓
PMO 输出拆分方案：
├── 各子项目需要做什么
├── 依赖关系
├── 推进顺序
    ↓
⏸️ 等待用户确认拆分方案
    ↓
用户确认后 · 逐个推进各子项目（按推进顺序）
    ↓
每个子项目走完整的现有流程
    ↓
全部完成 → PMO 输出跨项目整体完成报告
    ↓
更新 teamwork_space.md 跨项目追踪表（⏸️ 用户确认）
```

### 2.2 拆分方案输出格式

```
📋 PMO 跨项目需求拆分方案
============================

需求描述：[整体需求]
涉及子项目：X 个

## 子项目拆分

### 1. [缩写A] - [子项目名]
├── 需求描述：[该子项目需要做的事情]
├── Feature 编号：{缩写A}-F{编号}
├── 需求类型：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求
└── 预计产出：[PRD/TC/TECH/代码]

### 2. [缩写B] - [子项目名]
├── 需求描述：[该子项目需要做的事情]
├── Feature 编号：{缩写B}-F{编号}
├── 需求类型：Feature / Bug / 问题排查 / Feature Planning / 敏捷需求
└── 预计产出：[PRD/TC/TECH/代码]

## 依赖关系
├── [缩写B] 依赖 [缩写A] 的 [具体接口/数据/模块]
└── 推进顺序：[缩写A] → [缩写B]

## 联调要点
├── [接口对接说明]
└── [数据格式约定]

---
⏸️ 请确认以上拆分方案后 · 开始逐个推进。
```

### 2.3 跨项目整体完成报告格式

```
📊 PMO 跨项目完成报告
============================

需求：[整体需求描述]

## 各子项目完成状态
| 子项目 | Feature | 状态 | 完成日期 |
|--------|---------|------|----------|
| [缩写A] | {缩写A}-F{编号} | ✅ 已完成 | YYYY-MM-DD |
| [缩写B] | {缩写B}-F{编号} | ✅ 已完成 | YYYY-MM-DD |

## 跨项目知识沉淀
├── 联调经验：[跨项目联调的注意事项]
├── 接口约定：[确定下来的接口格式/协议]
└── 记录到：docs/KNOWLEDGE.md（全局知识库）

## teamwork_space.md 更新
├── 跨项目追踪表状态更新为：✅ 已完成
└── ⏸️ 请确认后更新

---
🔄 Teamwork 模式 | 角色：PMO | 跨项目需求：[需求简述] | 阶段：✅ 全部完成
```

---

## 三、变更归属检查（v7.3.10+P0-33 新增）

> 🔗 **本段是 [stages/triage-stage.md § Step 6.5](../stages/triage-stage.md) 的角色实现规范**。

**触发**：triage-stage Step 6 跨 Feature 冲突检查后 · PMO 必做变更归属检查（无论流程类型）。

**目的**：避免"边规划边启动"反模式（v7.3.10+P0-33 新增硬约束）。变更内子 Feature 必须等变更状态 = `locked` 才能启动；锁定前规划阶段 · 禁止启动子 Feature 浪费精力。

🔗 **变更管理 lifecycle 详规范** → [roles/product-lead-change-mgmt.md](./product-lead-change-mgmt.md)（v7.3.10+P0-92 抽出）。

### 3.1 Step 1：扫描变更文档

```bash
# 扫描所有 product-overview/changes/*.md
ls product-overview/changes/*.md 2>/dev/null
# 读每份的 frontmatter（YAML）· 提取 change_id / status / sub_features[]
```

### 3.2 Step 2：判断当前 Feature 是否归属某变更

匹配规则（PMO 智能判断）：
- **显式 ID 匹配**：当前 Feature ID（如 PROTO-F014a）出现在某变更的 sub_features[].id
- **范围语义匹配**：当前 Feature 描述与某变更某 sub_feature.scope 高度匹配（如"offer-id rust 重构"匹配 BG-015）
- **用户显式声明**：用户在需求消息中提及变更 ID（如「为 BG-015 启动 PROTO 部分」）

匹配命中 → 标记 `change_id`；不命中 → Feature 独立 · 不属于任何变更。

### 3.3 Step 3：按变更状态决策（硬阻塞 + 逃生舱）

| 变更状态 | PMO 行为 |
|---------|---------|
| `discussion` | 🔴 硬阻塞 + 引导用户完成 PL 讨论 |
| `planning` | 🔴 硬阻塞 + 引导用户完成 PM/RD 详细规划 + 锁定 |
| `locked` | 🟢 检查 launch_order 拓扑位置：<br>- 当前 Feature 是下一个可启动节点 → 通过<br>- 依赖未完成 → 硬阻塞 + 引导先做依赖 Feature |
| `in-progress` | 🟢 同 `locked` · 校验 launch_order |
| `completed` | 🟡 异常提示「变更已完成 · 建议创建新变更」 |
| `abandoned` | 🟡 异常提示「变更已放弃 · 本 Feature 不应启动」 |

### 3.4 Step 4：阻塞时的逃生舱

```
🔴 阻塞输出格式：

⚠️ 变更归属检查：当前 Feature {Feature ID/描述} 归属变更 {change_id}
变更状态：{status}
阻塞原因：{具体原因}

💡 1. 先去完成变更规划 / 依赖 Feature 💡（推荐 · 本 Feature 暂不启动）
   2. 🔓 强制启动本 Feature（绕过变更状态检查）
   3. 改成独立 Feature（脱离变更归属 · 但变更文档 launch_order 中保留占位符）
   4. 其他指示
```

🔴 **选项 2 强制启动**：
- 用户必须明确选「2」（不能用 ok / 默认推进自动选）
- state.concerns 加 WARN：`{ISO}：用户绕过变更状态检查（{change_id} 状态 {status}）· 强制启动 Feature {当前 ID}。原因：{用户提供 / 未提供}`
- state.json 顶层 `change_id = {change_id}` + `change_force_start = true`
- PMO 完成报告中显式标注「⚠️ 强制启动绕过变更检查」

🔴 **选项 3 改独立 Feature**：
- 当前 Feature 不再归属变更 · state.json `change_id = null`
- 但变更文档 launch_order 中对应位置保留占位符（标注「实际由独立 Feature {新 ID} 完成」）+ 状态备注

### 3.5 Step 5：通过后写 state.json

变更归属检查通过 → triage-stage Step 9 创建 Feature state.json 时写入 `change_id` 字段：
- 归属变更 → `change_id = "{变更 ID}"`
- 独立 Feature → `change_id = null`

### 3.6 硬规则

- 🔴 PMO 必须在 triage-stage Step 6.5 执行本检查 · 不可省略
- 🔴 状态 != `locked` 时硬阻塞（除非用户明确选「强制启动」）
- 🔴 强制启动 / 改独立 Feature 必须显式数字回复 · 不接受 ok / 默认推进
- 🔴 通过 launch_order 的依赖检查同样硬阻塞 · 不允许"乱序启动"
