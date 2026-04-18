# Dev Stage：RD TDD 开发 + 单元测试

> PMO 在技术方案用户确认后启动本 Stage。RD 按 TDD 流程开发 + 跑单测确认通过，一次性返回代码 + 测试 + 自查报告。
> 🔴 架构师 Code Review 已拆到 Review Stage 并行执行，Dev Stage 不含 CR。

---

## 一、设计意图

```
Dev Stage 职责：RD 写代码 + 写测试 + 跑单测 + 自查
├── TDD 流程：先写测试（红）→ 实现（绿）→ 重构
├── 单元测试必须在本 Stage 内通过
├── 集成测试代码也在本 Stage 写，但执行在 Test Stage
└── 产出：代码 + 测试代码 + RD 自查报告
```

---

## 二、输入文件

> 🔴 PMO 必须先按 [Dispatch 文件协议](../agents/README.md#dispatch-文件协议) 生成 `{Feature}/dispatch_log/{NNN}-rd-develop.md`，
> 下方文件清单作为该 dispatch 文件的「Input files」段落内容。未生成 dispatch 文件不得 dispatch。

```
Input files（写入 dispatch 文件）：
├── agents/README.md                                ← 通用规范
├── stages/dev-stage.md                             ← 本文件
├── agents/rd-develop.md                            ← RD 开发规范
├── docs/features/F{编号}-{功能名}/PRD.md           ← 需求文档
├── docs/features/F{编号}-{功能名}/TC.md            ← 测试用例
├── docs/features/F{编号}-{功能名}/TECH.md          ← 技术方案
├── {SKILL_ROOT}/standards/common.md                ← 通用开发规范
├── {SKILL_ROOT}/standards/backend.md               ← 后端规范（后端项目加载）
├── {SKILL_ROOT}/standards/frontend.md              ← 前端规范（前端项目加载）
│
可选文件（存在则读取）：
├── docs/features/F{编号}-{功能名}/UI.md            ← UI 设计
├── docs/KNOWLEDGE.md                               ← 项目知识库
└── docs/architecture/ARCHITECTURE.md               ← 架构文档
```

---

## 三、执行流程

```
🔴 进度追踪：每个 Step 开始时报告进度（宿主支持 TodoWrite 时使用，否则输出 markdown 进度块），禁止黑盒执行。

Step 1: 读取所有输入文件
        ├── agents/README.md + dev-stage.md（本文件）
        ├── agents/rd-develop.md
        └── 项目文件（PRD/TC/TECH/standards）

Step 2: 【RD】按 rd-develop.md 完整执行 TDD 开发
        ├── TDD Red-Green-Refactor
        ├── 写单元测试 + 集成测试代码 + API E2E case
        ├── 跑单元测试确认全部通过
        ├── RD 自查（对照 TC 逐条验证）
        └── 🔴 必须包含实际测试运行输出

Step 3: 产出汇总
        ├── 代码变更清单（新增/修改文件列表）
        ├── 测试运行输出（单测全绿的证据）
        ├── RD 自查报告
        └── 确定返回状态
```

---

## 四、返回状态

```
├── ✅ DONE
│   ├── 条件：单测全部通过 + RD 自查通过
│   └── 返回：代码 + 测试 + RD 自查报告
│
├── ⚠️ DONE_WITH_CONCERNS
│   ├── 条件：单测通过但有非阻塞性问题（如上游文档疑似有误）
│   └── 返回：代码 + 报告 + concerns 清单
│
└── 💥 FAILED
    ├── 条件：环境异常 / 无法编译 / 单测持续失败
    └── 返回：错误信息（PMO 降级处理）
```

---

## 五、Worktree 集成（PMO 预检阶段执行，非 Subagent 内部）

```
🔴 以下逻辑由 PMO 在 dispatch Dev Stage Subagent 之前执行，不是 Subagent 内部步骤。

worktree 策略读取：从 .teamwork_localconfig.md 的 worktree 字段获取（off/auto/manual）

├── worktree = off → 跳过，直接 dispatch Subagent
├── worktree = manual → PMO 提醒用户：
│   💡 建议为 F{编号} 创建 worktree：git worktree add ../feature-{编号} -b feature/{编号}
│   ⏸️ 等待用户确认已创建 / 跳过
├── worktree = auto → PMO 自动执行：
│   1. 检查 worktree 是否已存在：git worktree list | grep feature-{编号}
│   2. 不存在 → 创建：git worktree add ../feature-{编号} -b feature/{编号}
│   3. 已存在 → 复用
│   4. 📁 记录 worktree 路径到 STATUS.md（新增字段：worktree_path）
│   5. dispatch Subagent 时 cwd 设为 worktree 路径

worktree 清理（PMO 在 Feature 完成时执行）：
├── worktree = auto → PMO 完成报告阶段自动执行：
│   1. git worktree remove ../feature-{编号}（如已 merge）
│   2. git branch -d feature/{编号}（可选，分支已 merge 时）
├── worktree = manual → PMO 提醒用户清理
└── worktree = off → 无操作

Review Stage / Test Stage 也使用同一 worktree 路径执行。
```

---

## 六、红线

```
🔴 进度可见：每个 Step 必须报告进度（TodoWrite 或 markdown 进度块），禁止黑盒执行
🔴 TDD 必须执行：先写测试再写实现，禁止先写实现再补测试
🔴 单测必须通过：Dev Stage 返回前单测必须全绿，不能带着失败的测试返回
🔴 不做 Code Review：架构审查在 Review Stage 执行，Dev Stage 不含 CR
🔴 实际输出：自查报告必须附带测试命令 + 结果，禁止空口"通过"
```

---

## 七、输出格式

```
📋 Dev Stage 执行报告（F{编号}-{功能名}）
============================================

## 执行概况
├── 最终状态：{DONE / DONE_WITH_CONCERNS / FAILED}
├── 单元测试：{通过数/总数}
└── 实际测试输出：{测试命令 + 结果}

## RD 自查报告
{按 rd-develop.md 输出格式}

## 代码变更清单
| 文件 | 操作 | 说明 |
|------|------|------|

## Concerns（如有）
{非阻塞性问题清单}
```
