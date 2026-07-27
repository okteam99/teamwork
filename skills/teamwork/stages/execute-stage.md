# Execute Stage(micro 唯一工作 stage · v8.250)

> 🧭 **四段结构**(v8.285 · 详 [STAGES.md §3](../STAGES.md))· 本 stage 的特色是 ②只有 2 条、③全自主。

> **位置**:仅 `Feature preset=micro` 用 · 链 = `execute → ship`(去 dev 门禁 + pm_acceptance)。
> **定位**:prepare 之后的**零门禁自由执行** —— 无 stage 约束、无评审、无强制测试、无 DEV-RULES。目标只有一个:**完成任务**,然后 ship。

---

## 为什么零门禁

micro 的准入白名单(prepare §2.2)已经在**入口**卡死了改动性质:零逻辑变更 + 仅 文案/样式/资源/配置常量/注释。安全前置到了准入,所以执行阶段不需要再叠质量门 —— 叠了就是给「改一行文案」背全套仪式(micro 的病根)。

## ① 目标(telos)

**完成任务**。prepare 已把意图/流程/worktree/ID 定好,你只管把这个零逻辑改动做完、commit、进 ship。

## ② 硬规则(白名单 · 仅 2 条 · 不可破)

1. 🔴 **代码写 worktree 内路径**(`{worktree}/...`)(why:并行 feature 的基线隔离不能破 · 相对路径落主工作区 = 污染别的 Feature · 详 [SKILL.md § worktree 纪律](../SKILL.md))。
2. 🔴 **不得超出 micro 准入白名单**:干着发现涉及逻辑/接口/结构变更(不再是零逻辑)= **误分诊**,停,升级 Feature(回 prepare)(why:micro 的零门禁是用「入口卡死改动性质」换来的 —— 白名单破了,零门禁就没有安全前提了)。

## ③ 建议手段菜单(AI 全自主 · 无框架限制)

> micro 的定位就是**把 HOW 完全交还模型** —— 本段不是菜单式建议,是明确的授权边界:

- **怎么做** —— 直接改 / 派 subagent / teammate / workflow,AI 自选最合理的方式。
- **用什么模型** —— 自选档位(micro 多是机械改 · 通常继承会话即可,不必刻意升降)。
- **要不要测/验证** —— 自决。零逻辑改动多数不需要;涉渲染/构建产物,顺手 build/预览验一眼也行。

## ④ Output Contract

无强制产物(改代码直改)。完成 = **有 commit**:
```
git commit → state.py execute-complete --feature <path> --auto-commit <hash>
```
→ 自动转 ship。**无 pm_acceptance** —— 用户验收落在 ship1 的 MR diff review(user_card + await-merge,合并前看 diff)。

## 相关

- 准入:[docs/prepare.md §2.2](../docs/prepare.md) · 流程闭集:[FLOWS.md](../FLOWS.md)
- 引擎:`tools/_v8_stage_specs.py` `EXECUTE_SPEC` · 链:`tools/state.py` `MICRO_FLOW`
