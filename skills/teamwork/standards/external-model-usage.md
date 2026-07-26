# 第三视角冷审:形态与裁决纪律

> 🔴 **v8.291 重大变更(用户拍板):跨厂商异质模型评审彻底退役。**
> 退役理由:codex / gemini CLI 的冷启动 + 安全审查慢路径 + 登录/网络/MCP 故障面,**实测严重拖慢流程**
> (台账实证:codex exec 挂死 98m 后杀掉重试 · "Additional safety checks" 慢路径 · 反复踩未登录)。
> 原 286 行里的跨厂商机械(核心硬约束 / 合规架构 / profile 分类 / prompt 注入 / 配置约束 / 违规处置 /
> 异质性硬约束 137 行 / MCP 隔离 / .log 可观测性)**已整体删除**,连同代码侧 ~700 行
> (CLI exec / preflight / 超时 / 降级 / host 映射)、`disable_external_review` 配置项(已退役)与 94 条测试。

---

## 一、唯一形态:错开模型 subagent 冷审

| 维度 | 约定 |
|---|---|
| **怎么起** | `state.py external-review --feature <path> --stage <goal\|blueprint\|review>` → emit **subagent 配方**(本命令**不 exec 任何子进程**)· 落 prompt doc(评审指令 + 待评审文件已 inline) |
| **谁来审** | `Agent` subagent(isolated context)· 🔴 **model 必须 ≠ 会话主模型**(如 fable5 会话 → `model: opus`)—— 独立采样不变式详 [SKILL 🎚️](../SKILL.md) |
| **不喂什么** | 🔴 **不喂主对话起草心路** —— 白板效应恰是要的独立性(同一 AI 起草完审自己会脑补填缝) |
| **产物** | `external-cross-review/<stage>-<model>.md` · frontmatter 必含 `review_via: subagent` + `review_model`(照实写)+ `target_commit` + `coverage: [...]` |
| **门禁** | complete 校验:产物非空 · `review_via: subagent`(**禁主对话热审**)· `review_model` 非空(**禁伪造**)· coverage 申报;🔴 **yolo 额外要 prompt doc**(实跑证据 · 防手写自盖章) |
| **增量重验** | `--verify-fixes`(仅 review):只裁决上轮 open finding + 只回归审查修复 diff · 禁全量重扫 |

**为什么 subagent 够用**:独立采样有三层 —— 上下文隔离(冷审)< 同厂商权重错开(**本形态** · 零成本)< 跨厂商异质(已退役 · 成本不成比例)。**前两层已拿到主要收益**;第三层的边际增益不值它的时延。

**代价自知**:同厂商错开**不是**跨厂商异质 —— 错开的是权重档不是训练血统,盲区相关性低于同模型、高于跨厂商。这是**有意的效率取舍**,不是降级(故产物不再标 `degraded`)。

> 🟢 **`/code-review ultra` 摄入**:用户在会话内跑产品化多智能体评审 → `state.py external-ingest --from session` · 产物标 `review_via: ultra-ingest`(独立性由该管线保证 · 免模型申报与 yolo 实跑证据)。

---

## 二、裁决纪律(🔴 与模型无关 · 本节是被引用最多的存活核心)

> 🔴 第三视角冷审的价值 = **独立视角采样盲点**;但同一独立性 = 它**没有完整上下文**(不懂本项目 DEV-RULES / 不知某设计是 intentional / 可能 hallucinate finding)。**照单全收 = 把外部模型的误判 import 进来**。主对话消费第三视角 review(代码 / PRD / blueprint 通用)必须**逐条裁决**,不是 obey。
>
> 🔴 默认倾向是**相信**冷审产出(它语气笃定、又被 teamwork 当门禁跑)—— 这正是要纠的偏:reviewer 的 finding 是**待核实的断言**,不是事实。
>
> 🔴 **处理每条 finding 的固定思考顺序(默认姿态 = 质疑 · 不盲目认同)**:
> **① 质疑** —— 先假设它**不成立**:false positive?误解 intentional 设计?与 DEV-RULES 冲突?过度设计 / 责任焊错层?reviewer 没看全上下文?
> 🔴 **安全加固 / 兜底降级 = 过度设计高发区**(v8.279):external 天然偏加防御层/校验/重试/fallback · 这两类听着最「负责任」故**最难驳、最易盲采** —— 恰恰最该过 **ROI**(保护的失败场景 概率×后果 vs 实现维护成本 · 同 v8.265/266):立不住 → **REJECT**(「安全/兜底总没错」不是采纳理由);立得住 → ADOPT · 兜底类落 §兜底清单随 §7.5 透出。**「加安全/加兜底」不天然正确**,和别的 finding 同样过质疑门。
> **② 确认** —— 带着质疑**回读真实代码 / AC / DEV-RULES / 业务目标**核实(不轻信 reviewer 转述)。
> **③ 裁决 + 给理由** —— 经①②才落 ADOPT/REJECT/DEFER · **每个方向都写思考过程**(ADOPT 不是「改了什么」· 是「我质疑了 X · 回读 Y 确认它真成立 · 故采纳」)。
> 🔴 **举证责任对称**:旧规范只逼 reject 给依据 → ADOPT 成了无摩擦默认 = 盲采的温床。**confirmed 与 rejected 举证责任相同** —— 采纳也要给「为何确为真 + 为何这样改对」的实证,不是一句「reviewer 说得对」。

### 12.1 裁决三态(每条 external finding 落其一 · 带依据)

| 裁决 | 判据 | 处置 |
|---|---|---|
| ✅ confirmed | **先质疑**(是否 false positive / 过度设计 / 错层 / 不适用本项目 · 🔴 **安全加固/兜底降级 finding 必过 ROI** 概率×后果 vs 成本 · v8.279)→ 回读实际代码 / AC / DEV-RULES 核实**质疑不成立、确为真问题** | 修(进 fix-retry)· 🔴 REVIEW.md 记 finding + **采纳依据**(为何确为真 + 为何这样改对 · 与 rejected 举证责任对称) |
| ❌ rejected | false positive / 误解 intentional 设计 / 与 DEV-RULES 冲突 / reviewer 没看全上下文 | **不修** · 🔴 **必记驳回依据**(指真实代码 / 规约 / 业务目标)· 不静默忽略 |
| ⏸️ deferred | 真问题但**本 Feature 范围外** | → `product-overview/PENDING.md` · 不本轮强塞 |

### 12.2 两头都是反模式

- ❌ **盲采(over-trust · 默认倾向 · 🔴 最常踩)**:reviewer 说啥改啥 → import 误判 / 无谓 churn / 按错误 finding 改出 regression。**「reviewer 说得对所以采纳」不是理由** —— 没经过①质疑②确认的 ADOPT = 盲采。
- ❌ **盲驳(under-trust)**:嫌麻烦全 dismiss 让它过门禁 → 异质 review 形同虚设(等于没跑 · 违 P0-154 初衷)。
- ✅ **裁决(adjudicate)**:每条按①质疑→②确认→③裁决独立核实 → 带依据落 REVIEW.md。**举证责任在主对话 · 两个方向对称** —— rejected 给"为什么不是问题"的实证,**confirmed 给"为什么确是问题 + 为什么这样改对"的实证**(真实文件 / 规约 / 目标),都不是一句"我觉得"/"reviewer 说的"。

### 12.3 裁决 grounded 实际代码(不轻信 reviewer 断言)

- finding 是**待核实断言**:裁决前**回读真实代码 / PRD.AC / DEV-RULES 自己确认**,不轻信 reviewer 的转述/推断(同 [feature-planning](../docs/feature-planning.md) decisive 前提「核验真实文件 · 不轻信摘要」的 epistemics)。
- reviewer 与本项目 **DEV-RULES 冲突 → DEV-RULES 优先**(它是人定的项目真相;reviewer 给的是通用最佳实践 · 可能不适配本项目)。
- 高置信但与你核实结果**矛盾**的 finding:以**真实代码**为准 · 不被 reviewer 的笃定语气带走。

