# Codex Code Review Subagent：外部独立代码审查

> PMO 在 Dev Chain 通过后启动本 Subagent。使用 Codex CLI 对代码变更进行独立 Review，不接收架构师 CR 报告，从原始材料出发给出独立视角。
>
> `last-synced: 2026-04-14` · 对齐 SKILL.md / ROLES.md / RULES.md

---

## 一、设计意图

```
核心价值：用不同 AI 模型对代码做独立审查，发现同模型盲区。

├── 🔴 独立性：不给架构师 CR 报告，避免锚定效应
├── 🔴 互补性：不同模型关注点不同，能捕获各自盲区
├── 关键场景：
│   ├── 第三方依赖真实性验证（Claude 幻觉的包名，Codex 可能识别）
│   ├── 逻辑缺陷的不同视角
│   ├── 安全漏洞的交叉检查
│   └── 代码风格/惯用法的多元反馈
└── 定位：Dev Chain 之后、Verify Chain 之前的独立环节
```

---

## 二、触发条件

```
├── Dev Chain 返回 DONE / DONE_WITH_CONCERNS
├── PMO 确认 Dev Chain 产出完整
└── Codex CLI 可用（README.md §三 引擎检测已通过）
    └── ❌ Codex 不可用 → ⏸️ 用户选择：
        ├── 1️⃣ 解决环境问题后继续
        ├── 2️⃣ 降级到 Claude Sonnet 执行同等 Review（Sonnet 替代 Codex 视角）
        └── 3️⃣ 跳过 Codex Review
```

---

## 三、输入文件

```
PMO 启动时准备以下文件路径（Subagent 内读取并传给 Codex）：

必须提供：
├── docs/features/F{编号}-{功能名}/PRD.md           ← 需求文档
├── docs/features/F{编号}-{功能名}/TECH.md          ← 技术方案
├── docs/features/F{编号}-{功能名}/TC.md            ← 测试用例
├── 代码变更文件列表                                  ← Dev Chain 产出的新增/修改文件
│   └── PMO 从 Dev Chain 报告中提取，或通过 git diff --name-only 获取
│
🔴 不提供：
├── 架构师 CR 报告（保持 Codex 独立性）
├── RD 自查报告（同上）
└── 架构师的修复记录（同上）
```

---

## 四、执行流程

```
Step 1: 读取本文件 + agents/README.md（通用规范）

Step 2: 收集 Codex Review 输入
        ├── 读取 PRD.md / TECH.md / TC.md
        ├── 获取代码变更文件列表
        ├── 对每个变更文件读取完整内容
        └── 组装 Codex prompt（见§五 Prompt 模板）

Step 3: 调用 Codex CLI 执行 Review
        ├── 使用 codex 命令传入 prompt + 文件内容
        ├── 超时设置：10 分钟（可配置）
        ├── ✅ 正常返回 → 解析输出
        └── ❌ 异常 → 记录错误 → 返回 FAILED（PMO 决定是否跳过）

Step 4: 解析 Codex 输出
        ├── 提取问题清单（按严重程度分类）
        ├── 提取建议列表
        └── 结构化为标准报告格式（见§七）

Step 5: 输出 Codex Review 报告
        ├── 确定返回状态
        └── 返回给 PMO
```

---

## 五、Codex Prompt 模板

```
Subagent 组装传给 Codex CLI 的 prompt：

---prompt 开始---

你是一个独立的代码审查员。请对以下代码变更进行全面 Review。

## 需求背景
{PRD.md 的验收标准章节}

## 技术方案
{TECH.md 核心设计要点}

## 测试用例
{TC.md 用例摘要}

## 代码变更
{各变更文件的完整内容，标注文件路径}

## Review 要求

请从以下维度审查，输出结构化报告：

1. **逻辑正确性**：代码逻辑是否与需求/技术方案一致？有无遗漏的边界条件？
2. **安全漏洞**：SQL 注入、XSS、越权、敏感数据泄露等
3. **第三方依赖**：
   - 引用的包名是否真实存在？（请验证）
   - 版本是否有已知安全漏洞？
   - 许可证是否兼容？
4. **并发安全**：竞态条件、死锁风险、资源泄漏
5. **性能隐患**：N+1 查询、内存泄漏、不必要的全表扫描
6. **代码质量**：命名、结构、可读性、重复代码

## 输出格式

对每个发现的问题，按以下格式输出：
- 严重程度：🔴 阻塞 / 🟡 建议修复 / 🟢 建议优化
- 文件：{文件路径}
- 位置：{行号或函数名}
- 问题：{具体描述}
- 建议：{修复方向}

最后给出总体评价：PASS / PASS_WITH_SUGGESTIONS / NEEDS_FIX

---prompt 结束---

🔴 Prompt 组装原则：
├── PRD/TECH/TC 只提取关键内容（验收标准、核心设计、用例摘要），不传全文
├── 代码文件传完整内容（Review 需要看全貌）
├── 如果变更文件过多（>20 个），按优先级分批 Review：
│   ├── 第一批：核心业务逻辑文件
│   ├── 第二批：测试文件
│   └── 第三批：配置/工具文件
└── 单次 prompt token 超限 → 分批调用 → 合并结果
```

---

## 六、返回状态

```
| 状态 | 条件 | PMO 处理 |
|------|------|----------|
| ✅ DONE | Codex 未发现问题，或只有 🟢 优化建议 | 记录报告 → 进入环境预检 → Verify Chain |
| ⚠️ DONE_WITH_CONCERNS | Codex 发现 🟡 建议修复的问题 | PMO 评估 → 非阻塞则继续，可能的则进修复流程 |
| 🔁 NEEDS_FIX | Codex 发现 🔴 阻塞问题 | 进入三方修复流程（见§八） |
| ❌ FAILED | Codex CLI 调用失败/超时/输出无法解析 | ⏸️ 用户选择：解决后重试 / 降级 Sonnet / 跳过 |
```

---

## 七、输出格式

```
📋 Codex Code Review 报告（F{编号}-{功能名}）
================================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / NEEDS_FIX / FAILED}
├── 审查文件数：{N} 个
├── 发现问题数：🔴 {x} / 🟡 {y} / 🟢 {z}
└── Codex 总体评价：{PASS / PASS_WITH_SUGGESTIONS / NEEDS_FIX}

## 问题清单

| # | 严重程度 | 文件 | 位置 | 问题 | 建议 |
|---|----------|------|------|------|------|
| 1 | 🔴 | src/api/handler.rs | L42 | SQL 拼接未参数化 | 使用 prepared statement |
| 2 | 🟡 | src/service/order.rs | process() | 余额扣减非原子操作 | 改用 UPDATE ... SET balance = balance - ? |
| 3 | 🟢 | src/utils/helper.rs | — | 函数名 doStuff 不够明确 | 重命名为 processOrderPayment |

## 第三方依赖审查

| 包名 | 版本 | 真实性 | CVE | 许可证 | 说明 |
|------|------|--------|-----|--------|------|
| serde | 1.0.197 | ✅ 真实 | 无已知 | MIT/Apache-2.0 | — |
| fake-pkg-xxx | 0.1.0 | ❌ 不存在 | — | — | 疑似幻觉包名 |

## 总体评价
{Codex 的总体评价原文}
```

---

## 八、三方修复流程（NEEDS_FIX 时）

```
Codex 发现 🔴 阻塞问题时：

Step 1: PMO 对比架构师 CR 报告
        ├── 架构师也发现了 → 检查 Dev Chain 是否已修复
        │   ├── 已修复 → Codex 可能误判（代码已更新但 Codex 看到的是旧版）
        │   └── 未修复 → 确认为真实问题
        └── 架构师未发现 → Codex 独有发现，进入 Step 2

Step 2: PMO dispatch RD 评估 + 出修改方案
        ├── RD 逐条评估 Codex 问题：
        │   ├── 接受 → 给出具体修复方案
        │   ├── 拒绝 → 给出拒绝理由（如：Codex 误判、不适用当前场景）
        │   └── 替代方案 → 给出不同于 Codex 建议的修复方式
        └── 输出：RD 评估报告

Step 3: 架构师轻量审核 RD 方案
        ├── 只审核修复部分，不重做全量 Review
        ├── 确认修复方案合理性
        └── 输出：架构师审核意见

Step 4: 三方意见汇总 → PMO 决策
        ├── RD + 架构师都认可 Codex 问题 → RD 修复 → 重跑 Codex Review
        ├── RD/架构师认为 Codex 误判 → 记录理由 → ⏸️ 用户裁决
        └── 分歧较大 → ⏸️ 用户裁决

Step 5: 修复后重跑 Codex Review
        ├── 确认原问题已修复
        ├── 检查修复是否引入新问题
        └── 🔴 最多 3 轮（Codex Review → 修复 → 重跑）
            └── 超过 3 轮 → ⏸️ 用户裁决

修复循环：
  Codex NEEDS_FIX → RD 出方案 → 架构师审核 → RD 修复 → 重跑 Codex → ...（≤3 轮）
```

---

## 九、红线

```
🔴 独立性保障：
├── Codex 输入中禁止包含架构师 CR 报告、RD 自查报告
├── Codex prompt 中禁止暗示"架构师已通过"等引导性语句
└── Codex 的 Review 结论不受架构师结论影响

🔴 不盲从 Codex：
├── Codex 的问题必须经过 RD + 架构师评估，不能直接当结论
├── Codex 误判率可能较高（缺少完整项目上下文），需要人工（RD/架构师）过滤
└── 第三方依赖验证除外——Codex 说"不存在"的包应严肃对待

🔴 超时与降级：
├── Codex CLI 单次调用超时 10 分钟
├── 超时或异常 → FAILED 返回 → ⏸️ 用户选择：
│   ├── 1️⃣ 解决问题后重试
│   ├── 2️⃣ 降级到 Claude Sonnet 执行同等 Review
│   └── 3️⃣ 跳过 Codex Review
├── 降级到 Sonnet 时：使用相同的 prompt 模板（§五），仅替换执行引擎为 Claude Sonnet Subagent
└── 跳过 Codex Review 不阻塞后续流程（记录跳过原因即可）

🔴 修复循环控制：
├── Codex Review → 修复 → 重跑，最多 3 轮
├── 每轮修复后，RD + 架构师必须参与方案评估
└── 超过 3 轮 → ⏸️ 用户裁决
```
