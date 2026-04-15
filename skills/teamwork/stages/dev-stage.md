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

```
PMO 启动时必须注入：
├── agents/README.md                                ← 通用规范
├── stages/dev-stage.md                             ← 本文件
├── agents/rd-develop.md                            ← RD 开发规范
├── docs/features/F{编号}-{功能名}/PRD.md           ← 需求文档
├── docs/features/F{编号}-{功能名}/TC.md            ← 测试用例
├── docs/features/F{编号}-{功能名}/TECH.md          ← 技术方案
├── .claude/skills/teamwork/standards/common.md     ← 通用开发规范
├── .claude/skills/teamwork/standards/backend.md    ← 后端规范（后端项目加载）
├── .claude/skills/teamwork/standards/frontend.md   ← 前端规范（前端项目加载）
│
可选文件（存在则读取）：
├── docs/features/F{编号}-{功能名}/UI.md            ← UI 设计
├── docs/KNOWLEDGE.md                               ← 项目知识库
└── docs/architecture/ARCHITECTURE.md               ← 架构文档
```

---

## 三、执行流程

```
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

## 五、红线

```
🔴 TDD 必须执行：先写测试再写实现，禁止先写实现再补测试
🔴 单测必须通过：Dev Stage 返回前单测必须全绿，不能带着失败的测试返回
🔴 不做 Code Review：架构审查在 Review Stage 执行，Dev Stage 不含 CR
🔴 实际输出：自查报告必须附带测试命令 + 结果，禁止空口"通过"
```

---

## 六、输出格式

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
