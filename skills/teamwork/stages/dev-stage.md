# Dev Stage

> 🧪 **四段结构试点**(v8.218 · 目标 / 硬规则 / 建议手段菜单 / Output Contract):目标 + 契约给足,**手段 AI 自选** · 降低强制规则比例(如 TDD 节奏从强制降为强烈建议——**测试证据仍是硬门**)。

---

## ① 目标(telos)

**把已确认的设计变成可验证的实现**:代码如实落地 TECH/PRD 的设计(不偏离 · 不静默改设计),且交付时**带着机器可验的证据**(测试绿/差分零新增)。拦的风险:实现偏离设计、无证据宣称完成、污染并行基线。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **`project-specs/DEV-RULES.md` 存在则必读必遵**(why:人维护的项目强制规范 = 用户主权 · 冲突要么改实现要么 TECH 记原因)。
2. **worktree 内路径写文件**(推荐绝对路径 · 含派出的 subagent)(why:相对路径落主工作区 = 污染其他并行 Feature 的 baseline · 状态漂移)。
3. **测试证据硬门**(dev-complete 物化):`--test-exit-code 0`(红 base 走 `test-baseline` 差分「0 新增」)+ `--test-stdout` 非空 + `--auto-commit` 在 git history + artifacts 在 changeset(why:R7 证据闭环 —— 宣称完成必须机器可验)。测试与实现**一并交付**,不许「先实现后补测试债」。
4. **设计↔实际一致性核对**(UI feature · ui_design 完成时必做):起全景 dev server + 跑真实 app 目标路由 · **两边同开 browse 截图并排核对意图四要素**(布局结构/交互流/状态/字段映射)· 逐要素给「一致/背离」结论 · 背离不许静默放过(修掉 or 留 concerns);认为设计该改 → 回 ui_design / `--panorama-changed`,不在 dev 顺手改(why:治「设计稿≠实际效果」· 用户拍板的闸)。
5. **共享基建变更 → 全景编译契约**(diff 触及 preview-project 依赖的共享包时):dev 结束前 `preview-project` build/typecheck 须过;机械适配顺手修 · 视觉/交互变化走 panorama_sync · 不想适配就收回破坏性改动(why:改 API 者负责迁移所有消费者 · 全景是消费者之一)。
6. **flow_type=Bug:不重写 §根因/§修复方案**(那是 diagnose 经用户确认的产物 · 按方案写 fix + 追加 §回归测试/§修复记录;真发现根因判错 → `jump-to-stage --to diagnose` 复议)(why:用户拍过板的诊断不可被实现悄悄推翻)。
7. **完工自查在 TECH.md §完工自查 文档内逐项打 ✅**(每项指向证据 · 不适用写 N-A+原因)(why:产物契约 · review 据此核 · 防「设计了没实现」)。

---

## ③ 建议手段菜单(AI 按本 feature 自选 · 不强制)

| 手段 | 何时值得 |
|---|---|
| **TDD 红绿循环**(照 TC 逐 test:红→绿→重构 · 每绿点一 commit)| **强烈建议的默认**——TC 已备/逻辑类改动;绿点级 commit 便于 bisect 与 review 读节奏 |
| **先集成骨架后单测填充** | 跨层契约风险大于单元逻辑时(先打通端到端再补边界) |
| **subagent 并行拆分**(各写各的 · worktree 内路径)| 多端/多模块/相互独立且够大的子任务;小/耦合/强串行 → 自己串行做(协调开销反拖慢)。契约层/集成点留主对话 |
| **TECH 模糊处 fallback 决策树** | 实现遇设计未覆盖:KNOWLEDGE → ARCHITECTURE → standards/common → 全无 → concerns + 找架构师;不自行拍板 |
| **verify-panorama.py / 视觉回归工具** | UI feature 的机器辅助(结构核对必做是硬规则 4 · 工具是加速项) |
| **中途自查 TECH §依赖与影响** | 改契约类:每改一个 provider 顺手 grep 消费方 · 别攒到最后 |

🛡️ **起草思考规范**(v8.278 · 写法非环节 · 镜像 PRD 起草思考规范):写代码时**就照 review 会打的失败类写** —— 起草前必读 `project-specs/KNOWLEDGE.md § 复发防御清单`(本项目 review 高频 finding 类 · 如 stale closure / timeout 边界 / fail-open / 币种崩页),逐条在实现里主动规避,不是写完等 review 抓。why:findings 82% 真实、集中 code review、且反复撞同几类 —— 起草时防掉的类永不需要多轮收敛(goal 靠 shift-left 已 1 轮收敛 · dev 补齐)。

**并行姿态两问**(v8.254 · 实证:集成测试阶段整包塞单 agent · 主对话裸等 · 用户点破后当场拆出三线):
- **阶段演进重问**:「哪些可并行」不是开工问一次 —— feature 内每进入新子阶段(实现 → 测试编写 → review 修复)**重问一次**(耦合度随阶段变 · 开工时的最优拆分会过期;实证:两个测试任务零文件重叠 · 可独立 `TEST_PG_DB_NAME` 隔离 · 完全可拆却被打包)。
- **等待窗口不闲置**:派发后主对话**别裸等 agent** —— 填 TECH §完工自查的既有证据行 / 中途自查依赖消费方 / 把剩余工作再拆一刀(子任务独立判据:零文件重叠 + 可独立隔离 → 满足就再派)。

---

## ④ Output Contract(产物契约 · 机读)

### 代码 + 测试
- 源代码与测试**一并 commit** · commit message 含 Feature ID(如 `feat(login): add OAuth (PTR-F033)`)· 多 commit 允许,`--auto-commit` 传 stage 最终 head。

### dev-complete(必传证据)
```
state.py dev-complete --feature <path> \
 --auto-commit <hash> --artifacts <逗号分隔改动文件> \
 --test-stdout <log 或字符串> --test-exit-code 0 \
 [--current-failures "<id,id>"]   # 红 base 差分(test-baseline 登记集)
```

### Bug fix 报告(flow_type=Bug)
- `bugfix/BUG-*.md`(diagnose 已建)**追加** §回归测试 + §修复记录 · 模板 [templates/bug-report.md](../templates/bug-report.md)。

### 上下文入口(读什么)
PRD(AC)· TECH(方案+完工自查槽)· TC(测试用例)· UI.md+全景(若 ui_design 完成)· DEV-RULES(硬规则 1)· 🛡️ **KNOWLEDGE § 复发防御清单必读**(写时防 · v8.278)· KNOWLEDGE 其余/ARCHITECTURE 按需。Bug 流:`bugfix/BUG-*.md` 为权威输入。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py) · spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `DEV_SPEC`
- TDD 手艺:[../standards/tdd.md](../standards/tdd.md) · UI 还原:[./ui-design-stage.md](./ui-design-stage.md) § 分层同构律
- 工具:[../tools/verify-panorama.py](../tools/verify-panorama.py)
