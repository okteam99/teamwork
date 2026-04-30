# TDD 通用规范（v7.3.10+P0-63 抽取单源）

> 🔴 **本文件是 Teamwork 框架内 TDD（Test-Driven Development）的唯一权威源**。dev-stage / review-stage / standards/common.md / roles/rd.md / roles/qa.md 等所有涉及 TDD 的位置一律引用本文件，不在本文件以外另立约定。

> 🟢 **抽取自**（v7.3.10+P0-63）：原 stages/dev-stage.md §2 + standards/common.md §一 / §QA 代码审查 + roles/rd.md 散落措辞，三处合并去重。

---

## 一、Iron Law（不可妥协）

🔴 **NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST** —— 没有先写失败测试，禁止写实现代码。

🔴 **测试先于实现**（适用：后端 / 前端 / SDK / CLI / 库 等所有产出代码的 Stage）。

🔴 **不允许"先写实现再补测试"**（违反 = Dev Stage 流程偏离，QA Code Review 必发现并标记 ❌）。

---

## 二、RED-GREEN-REFACTOR 5 步流程

```
Step 1: RED — 读 TC.md，根据测试用例编写测试代码
        ├── 后端：先写单元测试 / 集成测试
        ├── 前端：先写组件测试
        └── 单一行为 / 命名清晰 / 真实代码避免不必要 mock

Step 2: VERIFY RED — 运行测试，确认全部失败（预期行为）
        ├── 命令模板：
        │   ├── 后端 Node：npm test path/to/test.test.ts
        │   ├── 后端 Python：pytest path/to/test_xxx.py -v
        │   ├── 后端 Go：go test ./path/to/...
        │   └── 前端：vitest path/to/component.test.tsx
        └── 校验：失败信息符合预期；失败原因是「功能未实现」（非 typo / 配置错）

Step 3: GREEN — 写最简实现让测试通过
        ├── 遵循 TECH.md 技术方案
        ├── 遵循 standards/common.md + 对应技术栈规范（backend.md / frontend.md）
        ├── 遵循 KNOWLEDGE.md 项目特定规则
        └── 禁止：本 step 内追加无关功能 / 重构无关代码 / 过度工程

Step 4: VERIFY GREEN — 运行测试，确认全部通过
        ├── 全部测试 PASS（不仅本次新增，整个测试套也不能 break）
        ├── 输出干净（无 warning）
        └── 失败 → 退回 Step 3 修实现，不是改测试

Step 5: REFACTOR — 保持绿态前提下清理代码
        ├── 消除重复代码
        ├── 改进命名 / 抽提辅助函数
        ├── 重构后必须重跑 Step 4 确认仍绿
        └── 不允许改变行为（行为变更 = 新一轮 RED）
```

🔴 **每个 TC 用例都对应一轮 RED-GREEN-REFACTOR**，不允许批量写多个测试再批量实现。

---

## 三、自检清单（提交前必查）

```
📋 TDD 自检（RD 完成 Dev Stage 前 / QA Code Review 时校验）：
├── [ ] 测试代码先于实现代码编写（git 提交顺序可验证）
├── [ ] 每个 TC 用例都有对应测试
├── [ ] 覆盖率达标（后端 > 80% / 前端 > 70%）
├── [ ] 测试可独立运行（无外部状态依赖 / 无测试间顺序耦合）
├── [ ] 测试命名清晰（说明被测行为，不是实现细节）
├── [ ] 包含边界条件测试（空 / null / 边界值 / 极值）
├── [ ] 包含异常场景测试（错误输入 / 上游失败 / 超时）
├── [ ] 断言质量（不能只有 toBeTruthy / 必须 assert 具体值）
└── [ ] 所有测试通过（exit 0）
```

---

## 四、反模式（必须杜绝）

| 反模式 | 正确做法 |
|---|---|
| ❌ 先写实现，再补测试（"测试驱动 → 测试附加"）| ✅ 先写 RED 测试，再写 GREEN 实现 |
| ❌ 测试只 assert 函数被调用 / 返回不为空 | ✅ assert 具体业务值（金额 / 状态 / 文案）|
| ❌ 简单方案 RD 自行跳过 TC + TDD | ✅ 必须申请用户同意后才能跳过（Dev Stage 入口暂停点）|
| ❌ 写一个测试，立即写实现，再写下一个测试（边写边实现）| ✅ 每个 TC 单独 RED → GREEN → REFACTOR 完整轮 |
| ❌ 测试用 mock 全部依赖（覆盖率高但 fake）| ✅ 真实代码 + 必要时 mock 外部（DB / HTTP），核心逻辑不 mock |
| ❌ 测试通过率 100% 但实际功能不工作（测试本身写错）| ✅ QA Code Review 读测试代码本身验证 assert 是否对得上 TC 描述 |

---

## 五、例外（仅以下场景允许跳过 TDD · 必须用户同意）

- **Throwaway prototype**（一次性原型 · 用完即扔）
- **生成代码**（脚本生成 / 模板代码 · 已有源 spec 验证）
- **配置文件**（.env / Dockerfile / 路由配置 · 由集成测试间接覆盖）
- **简单方案**（RD 在 Dev Stage 入口申请 + 用户显式同意 · 详见 [stages/dev-stage.md](../stages/dev-stage.md)）
- **Micro 流程**（零逻辑改动 · 文案 / 样式 / 资源 / 配置常量 · 详见 [SKILL.md 红线 #1 Micro 例外](../SKILL.md)）

🔴 例外必须在 `state.json.concerns[]` 落记录 `skip_reason: "..."` + 关联用户授权时间戳。

---

## 六、≥3 次失败修复 → 升级（v7.3.10+P0-63）

如同一 TDD 轮（Step 3 GREEN）失败修复 ≥ 3 次仍未通过，**停下来**：

1. 不再继续试错性修改实现
2. 重读 TECH.md 检查方案设计是否有问题
3. 必要时升级到 architect / external review（Dev Stage 输出"BLOCKED"状态 → PMO 调度架构师介入）

🔴 不允许"无意识尝试第 4 / 5 / 6 次修复"——这是症状性修复反模式，违反 standards/tdd.md。

---

## 七、各位置引用约定

| 位置 | 引用方式 |
|---|---|
| stages/dev-stage.md §2 TDD 开发流程 | 整段引用本文件 §二 + §三 + §四 |
| stages/review-stage.md QA Step 4 TDD 规范检查 | 引用本文件 §三 自检清单 |
| standards/common.md §一 TDD 检查清单 + §QA 代码审查 TDD 规范检查 | 整段引用本文件 §三 + §四 |
| roles/rd.md「测试先行」+ 反模式段 | 引用本文件 §一 + §四 |
| roles/qa.md QA 代码审查段 | 引用本文件 §三 |

末。
