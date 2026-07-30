# Changelog Archive

> 📦 **定期清空**:本文件只暂存从 [CHANGELOG.md](./CHANGELOG.md) keep-5 轮转出的条目 · 膨胀时整体清空 —— 完整历史 = **git 提交历史**(永不丢 · `git log` / `git show` 按需追溯)· 工作区不热存。
> 上次清空:**v8.193**(2026-07-06 · 清除 v8.128 → v8.187 共 60 版条目 · 约 1.0k 行)。

---
## v8.304 · 回收零工具 reviewer profile + 区分「执行失败」与「评审失败」

> 用户提案:隔离 Reviewer 无文件读取能力 · 冷审返 `files_read: []` + `no authorized read-only file access`,
> goal 流程被阻断。**宿主 = codex。**

### 根因链(逐环读文件核实)

| 环 | 事实 |
|---|---|
| ① | 被删的 `codex-agents/prd-reviewer.toml` **故意零工具** ——「READ-ONLY · Cannot write files via shell · Cannot execute commands」。因为**旧架构把待评审文件 inline 进 prompt**,reviewer 不需要自己读。**零工具是设计,不是缺陷。** |
| ② | 现配方**只 inline 一部分**:`goal→[PRD]` · `blueprint→[TC,TECH]` · **`review→[]`**;**上游 WS 与真实代码从不 inline**。v8.291 改 subagent 冷审 + v8.303 立「读真实代码」硬要求 → 零工具 profile **架构性不兼容**,不是配置没调好。 |
| ③ 🔴 | **v8.293 删了 skill 侧的源,却没写回收逻辑** —— bootstrap 只有 hook 的清理,没有 `.codex/agents/*.toml` 的。已部署副本留在用户项目里继续被宿主选中。 |

③ 是本 session 反复抓的形态(**退役了源,没清理已部署的副本**)的又一例 ——
但这次的后果比前几例重:**它在用户项目里活着并阻塞真实流程**。

### 修两侧

**bootstrap:由「部署」改为「回收」**(签名守卫同 hook —— 仅列名文件 + 内容含 teamwork 签名才删,
**用户自建的同名 profile 不碰**)。原部署分支在 v8.293 后已是死代码(`is_dir()` 守卫下静默 no-op),
连同那句「codex-cli 仍部署 …(**活功能**)」的错注释一并更正。

**门禁:区分 CAPABILITY_BLOCKED(执行失败)与 NEEDS_REVISION(评审失败)** —— 三类信号任一命中:
① `files_read` 显式为空 · ② `status: FAILED|CAPABILITY_BLOCKED` · ③ 正文出现「no authorized…」类回执。
报错直接说清 **「这不是 NEEDS_REVISION,是 reviewer 没有文件读取能力,产出的 finding 不可信」**
+ 三条处置 + **「预算没被消耗」**。旧门禁只报「产物不合规」,**把能力缺失说成评审问题**,用户被迫自排一轮。

🔴 `files_read` **缺失不算**(存量产物没这个字段)—— 只在**显式为空**时判定。宁可漏判,不可误判。

**配方 + 模板**:`external-review` 配方明确要求起的 subagent **必须有文件读取能力**,产物记 `files_read`;
`claude-agents/reviewer.md` 头部那段过时描述(还在写 `claude -p` 与 `_run_claude_review` ——
前者 v8.291 退役、后者 v8.293 删除)一并更正。

### 提案里我没照做的三条,以及为什么

- **建议 1/2/5(给专用 Reviewer 配最小只读工具集 / 修 teamwork 的 Reviewer 源模板并重新 bootstrap)**:
  teamwork **不 ship 任何 agent 定义**(`claude-agents/reviewer.md` 是 **prompt 模板**,无工具授权字段)——
  **建议 5 已无处可修**;agent 能力属**宿主侧配置**,框架不该也不能替用户配。
- **建议 3(派发前能力检查)** → 换成**产物侧要证据**:preflight 过了不代表正式跑时能读,
  而 `files_read` 是**已发生的事实**,还省一轮往返。
- **建议 4(CAPABILITY_BLOCKED 不占评审预算)** → **已天然成立** ——
  evidence check 在 `rounds.append` **之前**(`_v8_engine.py` 1720 vs 1791),
  失败根本走不到计数。本版只是把这个事实**写进报错**,让用户不必猜。

### 一处自伤(判定首版静默漏判)

`parse_frontmatter` 是**行式解析不是真 YAML** —— `files_read: []` 会解析成**字符串** `'[]'`。
首版按 list 判空,实测**该红的绿了**。已改为两种形态都判,并加门锁住解析器行为
(解析器一变,判定逻辑必须跟着复核)。

### 测试

1079 → **1092**。

---

## v8.303 · 断言必须标注证据边界 + 测试输入必须来自真实链路

> 来源:SVC-CORE-F260728 的 AI 自省 —— 用户问「你为什么总出错」,它把本 session 犯的 **9 个错**
> 列成表(含谁发现的),然后归纳出**唯一共同点**。

### 一、它自己找到的根因,比「验证不够」准得多

> **「我读了旁边的代码,然后把结论说成读过那一行。」**

最典型那条:它确实跑了 grep、确实看到 BFF 是 `request_upstream::<GoalEventsData>` 类型化反序列化,
据此推出「每层都是可选字段的加法」—— **但没去看那个 struct 上有没有 `deny_unknown_fields`**
(实际有,新字段会 502)。**证据是真的,推论是自己加的,而两者用同一语气一起给了出去。**

它对自己的定性最关键:
> **「不是『验证不够』这种笼统问题。我的验证量其实不小(跑了几十次 staging 实测和 grep)。
> 问题是我不标注验证止于何处、推论始于何处。已验证的和推出来的,在我的输出里长得一模一样,
> 你没法分辨该信哪句。」**

**核对框架:这个定性成立。** 现有 7+ 条相关规则(grounded 真实代码 / 不轻信 Explore 摘要 /
decisive 前提必 Read 核验 / 消费方必 grep 不凭记忆)——**全在输入端**,
**没有一条管输出端怎么标**。

### 二、新增 `SKILL.md § R3-E · 断言必须标注证据边界`

🔴 **说某段代码/系统有某属性时,要么本次会话读过那一行,要么显式写「推断」——不许中间态。**

点名高发形态 **「读了旁边」**:grep 命中 / 看到类型签名 / 量了一个维度 → 据此一般化到
**没亲眼看过的属性**(serde 标注 · DB 约束 · 默认值 · 那个分支是不是死代码)。
并给出**分层写法**,让用户一眼知道哪句该打问号:

> 「BFF 是类型化反序列化(**已验证** · 读了 `xxx.rs:1255`);因此我推断可增量扩展(**未验证** —— 没看 serde 是否 `deny_unknown_fields`)」

**这条不随模型变强而衰减,反而更需要** —— 模型默认把事实与推论连成流畅叙述(那是流畅写作的本质),
而**模型越强、叙述越流畅,推论就越像事实**。已在条文里声明抗衰减属性,防下一轮减法误砍。

### 三、`HARD-RULES 7` 补上恒绿假绿的第二条路

原文只堵了「mock 掉被测组件自身」。新增:**测试输入必须来自真实链路**
(自造 fixture 要显式标注 + 说清与真实输入的差异)。

判据一句话:**验的是「我伪造的输入能被正确处理」,还是「真实链路会产生这样的输入」?**

> 实证:测试用 SQL 直插绕开真实摄入路径 → **11 测试 + 4 变异验证全绿,功能却全坏**。
> 🔴 关键的一句是 **冷审 / 变异验证 / CI 全在自己画的那个圈里** —— 最后靠**生产数据**发现。
> 不写这句,读者会以为「多加一道评审就能拦住」。

### 四、自我施用:新规则当场被自己的门拦了一下

加完 R3-E,SKILL 的 🔴 计数门(`< 55`)当场红。**正确做法不是抬阈值** ——
那个门写着「只有命中判据①-⑤才配标红」,是**价值判据不是体积门**。
故按它自己的判据裁掉 R3-E 里那个**解释性** 🔴(规则本身配标红,why 与注释不配)→ 54,过。

> 对照 v8.299:`tech.md < 250 行` 那个是**纯体积门**,度量错了东西,已换成价值门;
> 这个 🔴 密度门度量的是**注意力经济**(全是红等于没有红),是对的,所以服从它。
> **两个看起来都像"体积门"的门,该服从哪个取决于它度量的是什么。**

### 测试

1069 → **1079**。

---

## v8.302 · 任何抛给用户的决策项都必带「💡 建议 + 理由」

> 用户:**抛给用户的问题都应该有建议和理由。**
> 实证(SVC-CORE-F260728):AI 把 D-4~D-7 四条待决策项**光秃秃列出**,用户被迫追问
> 「这四条你的建议和理由是什么」。

### 根因是结构性的,不是 AI 偷懒

`SKILL.md` 的 R5 三选项格式**早就强制**「💡 推荐 + 理由」,红线甚至写着
「缺任一 = **把判断甩回用户** + `ok` 快捷词失灵」。**规则一直在。**

**但 PRD `§待决策项` 的表列是 `| ID | 问题 | 选项 | 决策 |`** —— **没有承载建议与理由的位置**。
AI 照表填,填出来必然是裸选项。注释里虽有一句「(原行为/新行为/为什么改/推荐)」,
那是散文里的括号,不是列。

🔴 **载体的形状决定内容会不会出现** —— 与 v8.297(归因塞进单行单元格)、
v8.298(判据算不出分子分母)是同一类:**规则写在哪不重要,结构承不承载才重要。**

### 修法两侧都要

- **结构承载**:`§待决策项` 表加 **💡 建议** + **理由(一句)** 两列 + 一行示例;
- **语义覆盖**:R5 红线从「三选项格式」扩到 **任何抛给用户的决策项** ——
  PRD 决策项逐条 · 多项一次性 escalate · 方案分叉 · 「要不要现在做 X」;
- **goal-stage 终确认导读**:「你要拍板的」那档早就要求「我的倾向」,而
  「剩余 §待决策项一次性 escalate」那半句**没有** —— 漏的正是它,已补齐(同一份导读里不该有两套标准)。

### 🔴 给「推荐不了」一个定义好的出口

不给逃生口,规则会被「这个我也不知道」绕过;给了就必须**说明是哪一种**:
① **缺信息**(缺什么 · 谁能给)· ② **纯偏好**(无技术优劣 · 产品/审美取舍)· ③ **等上游决策**。
**留空不算** —— 用户只会被迫追问。

### 测试

1061 → **1069**。

---

## v8.301 · 不在门禁的适用阶段之前跑它 + 命令按「AI 要不要记」重分类

> 用户:①「为什么在 goal 阶段调用 verify-ac」②「是否有必要降低脚本数量,AI 只需记流转脚本」

### 一、case:一个注定失败的调用

AI 在 **goal 阶段**手跑 `verify-ac.py`,必然 FAIL(TC.md 是 blueprint 产物),只能自辩「预期的失败」。
查下来三件事同时成立:

- **纯冗余** —— 它想验的「AC 机读块本身」**早已由 goal-complete 的 `prd_template_conformance` 校验**;
- **有诱导源** —— `templates/prd.md` 机读块头写着「**verify-ac + goal-complete 解析此块**」。
  陈述属实,但摆在 goal 阶段的 PRD 里就读成「去跑 verify-ac 验一下」· **属实的话摆错位置也会误导**;
- **工具给的是裸失败** —— 只说「TC.md 不存在」,没告诉调用方「你不该在这个时点调我」。

🔴 **危害不在浪费这一次**:注定失败的调用逼调用方把 FAIL 解释成「预期的」,
而**「预期的 FAIL」一旦被正常化,真 FAIL 就会被同样对待** —— 门禁的全部价值在于「红了就是有事」。

**修**:① 去诱导源(prd.md / templates/README 改成说清谁在什么时候跑)·
② 工具侧**保持 exit=1**(blueprint/test 的门依赖它)但把裸失败换成**路由信息**
(「TC 是 blueprint 产物」+「AC 块归 goal-complete 的 `prd_template_conformance`」+「覆盖校验在 blueprint/test-complete 自动跑」)·
③ 立 `standards/scripts-policy.md § R-SP-1c`:跑之前先问「这个门管的产物现在存在吗」+
「想验的东西是不是已经有门在管」;**工具侧的义务 = 给路由信息而不是裸失败**。

### 二、命令按「AI 要不要记」重分类 —— 该减的不是脚本数量

先测再答:**56 子命令 = 30 流转 + 26 辅助**;辅助里**只有 6 个**出现在流程 brief,20 个靠 AI 自己记。
但那 20 个要分开看 —— **10 个是逃生口**(`recover`/`raw-write`/`reset-prev`… · AI 主动跑才是问题,不记正确)·
**10 个是「该在时点推却没推」的真缺口**。

🔴 **删有用的命令 = 丢功能;让命令在正确时点被 emit = 零记忆负担 + 功能全留。**
而 verify-ac 那个 case 正是证明:**问题不是脚本多,是 AI 记住了一个它不该在那个时点跑的脚本** ——
减少总数解决不了它。

`SKILL.md` 命令段按**记忆义务**重分三类(不是按功能):
**A 必记**(30 流转)· **B 不必记**(流程在动作点推 · 带可直接跑的完整命令行)· **C 不必记也别主动跑**(逃生口)。
判据:**「这个命令有没有一个确定的动作时点?」** 有 → 归 B 并**接进那个时点的 emit(不许只写进文档)**;没有 → 归 C。

**补齐两个动作点推送**(照 v8.295 `stage_cost_hint` 形态):
- `review-preventability` → **评审收敛时**(goal/blueprint/review 的 complete 且 verdict 非 NEEDS_REVISION)·
  带真实路径 + 说明「零可预防也要记」(`--preventable 0` —— 「全 emergent」与「没记录」是两回事);
- `ledger-migrate` → **ship1 archive brief**,并写明「**写台账行之前**先跑,漏了新行会按旧表头错位」。

> **为什么「写进 stage 文档」不够**:文档在 stage-start 读,动作点常在几十个工具调用之后 ——
> **提醒与动作之间隔了太多 context**(v8.299 实证:agent 读过派发声明制仍然漏了)。
> `review-preventability` 本来就写在 `review-stage.md` 硬规则 8 里,照样没到达。

> 📌 反面用例:`add-concern`(auto skip 留痕)**故意不推** —— 它的动作点是「AI 自己决定跳暂停点那一刻」,
> 机器观测不到。按本版判据「没有确定动作时点 → 不进提醒」,留在文档里是**自洽的**,不是遗漏。已加门锁住这个判断。

### 测试

1046 → **1061**。

---

## v8.300 · 档位映射按厂商分列 + 清 v8.299 的三处自伤

> 用户:档位表的「当前映射」写清晰一点 + 发版。
> **这一版全是自伤修复** —— v8.299 引入新规则时留下三处不一致,而且**三处都是本 session 反复抓的形态**,
> 这次是自己种的。记下来不是自责,是因为「加新规则时忘了改旧的」有稳定的复发率,值得单独立门。

### 一、档位映射按厂商分列(用户给定型号)

原来两家挤在一格(`Claude: Fable/Opus · GPT: 最高推理档`),读者要自己拆;GPT 侧还是抽象说法。改成两列:

| 档位 | Claude | GPT / Codex |
|---|---|---|
| **深度档** | **主对话** / Fable / Opus | **主对话** / sol xhigh |
| **执行档**(默认) | Opus / Sonnet | sol xhigh / terra xhigh |
| **验证档**(轻) | Sonnet / Haiku | terra / luna |

🟢 判据仍是**任务性质,不绑型号** —— 型号随代际漂移,这两列只是当前落地示例。
下次代际一换改这两列即可,判据不动。

### 二、三处自伤(v8.299 引入 · 本版清理)

**① 单源侧还写着被取代的旧口径。** v8.299 把声明制改成「寄生 prompt 首行」,
但 `SKILL.md`(**被声明为单源的那份**)仍写「(派发语句 / dispatch 文件 Meta / workflow `agent()` 旁注释)」,
`agents/README` 📎 段同样。两处都还允许把声明放在**「另起一句」的位置** —— 正是新规则要取代的形态。
→ 已重写,并把单源侧补齐三件(寄生规则 / 白名单例外需授权 / 台账两桶口径)。

**② 数字宣称与实际不符。** v8.299 加了第 ④ 条硬边界(验证类白名单例外需用户授权),
标题却还写「**三条**硬边界」,`SKILL.md` 的反向引用跟着错。
→ 改四条 + 立门:**宣称条数必须等于实际圈号数**,且 SKILL 反向引用与 agents/README 一致。

**③ 断言锁死旧措辞。** 改 `DISPATCH_TIER_REMINDER` 措辞后两个测试假红
(`assertIn("声明 model", …)`)—— RETRO 里这类已记过三次。
→ 改为断言实质(白名单枚举在不在 / 有没有要求用户授权 / 声明是否寄生),不锁字面。

> 🔴 三处的共性:**加新规则时只写了新的,没回头改被它取代的旧的**。
> 本 session 前面抓的「指针 + 复制被指向内容」「退役声明贴头上正文没改」「stage 数 13→12 但 README 还写 13」
> 全是同一形态。它的复发率高到值得当成一类来防,而不是每次事后修。

### 测试

1041 → **1046**(新增:硬边界条数一致性 · 档位表按厂商分列 · 旧口径不得残留 · **静默死测试检测**)。

### 三、第四处自伤:新加的三个门**根本没在跑**

本版三个新门写完后落在了 `if __name__ == "__main__":` **之后且同缩进** —— Python 把它们解析成
那个 `if` 的**块内定义**,只在 `python file.py` 直跑时存在,**pytest 收集时看不到**。
**不报错 · 不红 · 就是不跑**,静默失效了一整轮;我还在两条 commit message 里报了**没验证过的**测试数。

这与本 session 反复抓的仍是同一形态 —— **产物存在但没接上消费方**,只是这次的"消费方"是 pytest 的收集器。

→ 立门 `TestNoSilentlyDeadTests`(用 **AST** 判 `__main__` guard 的 body 里有无 def/class ·
不靠猜缩进)+ 空壳测试文件检测(有文件、零用例)。
🔴 **门自身也做了注入自验**:往 guard 里塞一个方法确认它会红 —— 否则「立了个不会响的门」是同一个坑套娃。

> 中间版本按「`__main__` 之后的行」判,连报 7 个误伤(那些是**列 0 的模块级 class**,pytest 收得到)——
> **判据是结构不是位置**。

---

## v8.299 · 测试基建成本显性化 · 退役类改造纪律 · 并行派发第三问

> 来源:matrixpower BL-038/BL-039 的规范增补提案(已是条文形态)+ 用户「测试太多影响效率」。

### 一、七条提案:逐条过收录判据后**全部收下**

罕见的高质量提案 —— 每条都落在 v8.285 判据的**逆默认**或**不可知**格:

| 条 | 落点 | 模型的默认行为(= 为什么要写它) |
|---|---|---|
| A1 机械收敛与语义变更**分两步** | `templates/tech.md §实现步骤` | 默认**一起改**(反正都要动这些文件) |
| A2 退役类**按口径分张台账** | tech.md + `blueprint-stage ②` | 默认**算一个总数**,数字接近就以为核过了 |
| A3 测试基建税**必须记下来** | tech.md 新增 §测试基建成本 | 默认要么顺手改(范围失控)要么无视(税永远隐形) |
| B1 退役 BL 的 `current_state` 增记**测试痕迹规模** | `feature-planning` + `workstream.md` | 不可知:退役的成本主体在**测试改写**,只按新增能力估会低估 3~5 倍 |
| C1 派发**第三问:验证目标有重叠吗** | `SKILL.md` 并行段 | 默认**按产物切分就认为正交了** |
| C2 同编译单元并行的**三项声明** | `agents/README.md` | 不可知:独立构建目录**挡不住源目录 lock** |
| C3 三条硬约束的**中断安全**职责 | `agents/README.md` | 零成本 —— 不加规则,只补 why(防它被当官僚主义砍掉) |

**A2 是其中最硬的一条**:实证里 TECH 与 TC **各算出「35 处/7 文件」并都自称与 PRD 吻合**,
实为两个互斥 population;拆开是 25/6(调用面)、71/6(构造面)、18/5(约束面),
**第三张是评审才发现的**,对应 18 个必红测试。
条文因此写死:**总数不作验收门 · 不同口径不可互相印证** ——
**数字碰巧接近比对不上更危险,它让人以为核过了。**

### 二、🔴 元发现:体积门首次咬人就咬错了

三条新规则被 `tech.md < 250 行` 拦下 —— 而它们全是**逆默认 + 带实证**,正是 v8.283 分类学里最高价值的那类。

**体积门度量错了东西。** v8.283 的主张从来不是「文件要短」,是**收录判据 = 与模型默认行为的距离**:
300 行全是逆默认规则的模板,比 200 行全是填充示例的**更瘦**。
已换成**价值门**:每条硬规则必须带 `why`(无 why 的规则才是纯注意力税);
体积仍由内容型门守(教学示例 / 手段规定不得回归)。

### 三、测试效率:先测再定,数据推翻了前提

用户提「用例太多影响效率,考虑合并」。实测 1015 条 / 58s:

| | 条数 | 占比 | 耗时占比 |
|---|---|---|---|
| **< 5ms** | 623 | **61.4%** | **0.00s** |
| 最慢 50 | 50 | 4.9% | 51.4% |

**61% 的用例本来就免费** —— 合并它们省不到一秒,却把「哪条坏了」变成「有东西坏了」。
成本集中在**进程派生**(起 `state.py` 子进程 / `git init` 建仓),**不在用例数量**。

立 `standards/scripts-policy.md § R-SP-1b`:
① 默认不合并(失败定位是测试的主要价值)· ② **只优化 > 50ms 的**(29% 条数 / 96% 时间)·
③ **手段是共享 setup 不是合并断言**(昂贵的是 setup)· ④ 并行优先于任何改造。
🟢 本条是「手段规定」= v8.283 判定会衰减的那类,故**只写规范不配机器门**(用户拍板)。

**`tools/run_tests.py`**:有 `pytest-xdist` 走 `-n auto`,没有则按**实测耗时**贪心装箱并行 ——
🔴 **自学**:每跑写回 `.test-durations.json`,首跑按文件大小近似(27.5s · 分片差 17s),
第二跑起按真实耗时(**16.9s · 分片差 0.4s**)。**58s → 16.9s(3.4×)· 零测试改动 · 零定位损失。**

> 📌 未装 xdist:homebrew Python 被 PEP 668 拦,**没有用 `--break-system-packages`**(有搞坏用户 Python 的实际风险)。
> 手动分片已拿到 3.4×,装了 xdist 会自动切过去。
> 📌 初版把 runner 写成了 `.sh` —— **违反了我正在编辑的那条 `R-SP-1`「业务脚本一律 python3」**,已改写。

### 四、前一份提案的 D 区:**五条全部已落地**,一条诊断需修正

R1 收敛期归一 / R2 投机窗准入 / R3 fast_mode 可见 / R5 rival 设计强制 —— v8.294 已做。
🔴 **R4 的诊断需修正**:不是「门禁词表缺同厂商错开第三态」——**整个跨厂商机制已在 v8.291 退役**,
`degraded` 全库零命中,`review_via: subagent` + `review_model` 照实申报**就是**一等形态。
提案的 case 跑在 v8.287.1,早于它。

另:R3 的根因比提案诊断的**宽 5 倍** —— 不是 fast_mode 一处,是 **5 个 localconfig 读取者**
在默认 worktree 模式下**全部静默回退默认值**(v8.294 已修)。

### 五、派发声明制的三处修正(实证 + 用户拍板)

一个 agent **读过 v8.235 声明制仍然漏了**,并自我归因得很准:
> 「提醒在 test-start 的 emit 里,而我在 15 个工具调用之后才派 agent。
> 提醒和动作之间隔了太多 context —— **提醒的位置错了,不是措辞不够狠**。」

三处修正各治一个根因(**都不是加一条新规则** —— 同类散文补丁是反模式):

**① 位置:声明寄生到 prompt 首行**
`Meta: tier=<验证|执行|深度> · model=<留空则继承> · 理由=<一句>` —— 不再"另起一句说"。
prompt 是派发时**必然要写**的东西,寄生在它上面才不会被忘;
「另外记得声明一下」是**额外义务**,而**高频低显著性的义务必然衰减**。

**② 强度:验证类白名单一律降验证档 · 例外需用户授权**(🔴 用户拍板)
**写测试用例(TC 起草)· 执行测试 · 单测 · 集成测试 · e2e · TC 逐条对照 · 冷审执行 · 机械外化**
—— 默认**全部**降验证档并必须显式传 model。认为本次特殊(如首份 e2e 要逆向真进程启动配方)
→ 🔴 **不许 AI 自决,开 R5 暂停点请用户授权**。

> 这条推翻了 agent 的自辩(它 argue「首份 api-e2e 是探索+调试型,不该降」)。
> why:**「这次比较难、不该降」是最容易自我合理化的一步** —— 每次都成立就等于白名单不存在。
> 判断权归用户,不是因为 AI 判不准,**是因为这是花钱的决定**(v8.283 分类学第③类 · 用户主权 · 不衰减)。
> 枚举也比抽象类目(「校验/枚举型」)更难钻空子 —— 抽象类目留了「这次算探索型」的口子。

**③ 度量:拆 `inherited_declared` / `unspecified`**
旧代码的 docstring 直接写着「未记 model 的计 unspecified(**= 继承会话模型 · 正是要观测的「没分档」信号**)」
—— **把两件干预手段完全相反的事划了等号**:
- `inherited_declared` = 思考了 · 判定该继承(**正确行为** · 干预 = 无)
- `unspecified` = 真没分档(干预 = 加强档位判据)

本例正是前者(档位判断对、只漏声明),按 unspecified 归因会得出「该加强档位教育」的**错误结论**。
与 v8.297/298 同类:**度量口径把两件事混成一格,年检就会开错药方。**

> 📌 agent 提到「唯一能在动作点触发的是宿主 PreToolUse hook」—— **不捡回来**。
> hooks 曾污染共享仓库,那正是 v8.213 退役它的原因;为一条声明规则复活它是坏交易。
> 本版的解法是**把声明寄生到必写物上**,根本不需要动作点 hook。

### 测试

1013 → **1041**。

---

## v8.298 · 档位错配整体 review · 修「判据算不出来」两处 + 立类级门禁

> 用户:**整体 review 一遍流程文档,看有没有类似的档位错配。**

先把 v8.297 那个错配抽象成**可扫的四类形态**,否则又是印象派:

| 形态 | 症状 | 状态 |
|---|---|---|
| ① 叙述塞单行槽 | 表格单元格要求写多维判断 | v8.297 已修;`teamwork-space` / `pending` 本就配了「详情外迁」纪律 ✅ |
| ② **可算字段埋叙述** | 跨 feature 要算账的数字混在自由文本里 | 🔴 **本版找到两处** |
| ③ 只 emit 不落盘 | 产物瞬时而消费方在事后 | v8.297 已修(digest 四问)✅ |
| ④ 落盘但读不到 | 落机器本地 / 未跟踪路径 | v8.296 已退役 `docs/audit` ✅ |

### ② 的两处:都是「声明了判据,却取不出分子分母」

框架其他「率/占比」判据都把分子分母放在同一格 —— `external 总/采/驳`、`可预防/总`、`开销轮/总轮`。
唯独这两条没有落点,等于**判据写着好看、年检根本算不出来**:

- **PL-CHALLENGE 采纳率**:goal-stage 明写「进 PROCESS-LEDGER · 长期零采纳 = 过场信号,收紧判据」,
  但台账「角色真 finding」列的示例只有 review 侧(`arch:1 qa:0 ext:1`)—— **goal 侧的 `pl` 从没出现**,
  ship 也零 emit。
- **新判例频次**:kill criteria 明写「**连续数月无新判例** → 流程仪式砍半」,
  而「流程新判例」是叙述(v8.297 起落在复盘 §三),台账无字段 —— **数不出来**。

### 修法:都不加列

加列有成本(旧行留空 · 有效前缀语义变模糊),能用约定解决就不动 schema:

- **「角色真 finding」列按 `<goal 侧> / <review 侧>` 两段写全**(示例改 `pl:2 ext:1 / arch:1 qa:0 ext:1`)·
  🔴 **零也要写**(`qa:0`)—— 「零 finding」与「没这个角色」是两回事,而「某角色长期零真 finding →
  评审矩阵收缩」正是靠它区分。
- **有流程新判例时,「反思摘要」列以 `判例:` 前缀开头**(年检 grep 前缀即可计数 · 正文留在复盘 §三)。
  三处同步:台账约定 + kill criteria 的数法 + 复盘模板要求回填(**不要求回填 = 前缀永远不会出现**)。

### 类级门禁(本版真正的产出)

只修两条不值一版。立 `test_tier_placement_v8298`,锁的是**整类**:
- 每条「率/频次」判据必须映射到台账实有列(新增判据没落点 → 红)
- PL-CHALLENGE 与新判例的可取性各自成门
- 台账必须声明「什么不该写在这里 + 该写去哪」,复盘必须声明「不写业务内容」(两边都写明,下次才不会又塞错)
- 扫全库:凡声明「年检 / kill criteria」要用的产物,**不得同时标「只 emit 不落盘」**
- 🔴 锁台账列数 = 16:**修 ② 不许靠加列**

### 测试

1005 → **1013**。

---

## v8.297 · 耗时归因与流程反思搬出台账 · 落独立流程复盘文档

> 用户:**耗时归因和阶段流程反思不该写到 PROCESS-LEDGER,因为写不下 —— 应该单独一个文档放到项目的复盘目录下,台账做引用。**

判断成立。台账**一行一 feature、单元格 ≤1 行**,而「这 318 分钟花在哪」恰恰是最值钱的那段;
v8.295 把归因塞进单元格是错的档位 —— 压缩掉的正是它的全部价值。

### 新增:`templates/process-retro.md` → `{子项目}/docs/retros/<feature-id>-process.md`

四段:**各阶段耗时表**(机器数据照抄 `ledger_timing.per_stage`)· **逐 stage 耗时归因**(本文件核心)·
**流程反思四问** · **起草可预防性**。写入时机 = ship1 archive 规划 gate(与台账行同时 · worktree 内)·
🔴 **路径加进 `--planning-artifacts` 随 feature MR 原子合入**(不进 git = 白写)。

划清了与同目录**业务复盘** `docs/retros/<feature-id>.md` 的边界:后者复盘需求演进与技术选型(知识层),
**本文件只复盘 teamwork 流程本身** —— 时间花在哪、哪个环节没产生价值。

给了「什么算协调开销」的**可判定判据**:**「这一轮产生了新的设计判断或新的实现吗?」** 没有 = 协调开销。
不给判据则每人一把尺,跨 feature 数据不可比。

### 顺带:原本「只 emit 不落盘」的 digest 四问,终于有家了

ship-stage §16 的 digest 明写「不落 feature 目录」—— **说完就蒸发**,年检什么也读不到。
现在四问同时写进复盘文档 §三,emit 只作当场回显。

### 台账列收窄为「可算比值 + 指针」

`⏱️ 耗时归因` 从 `协调开销 2/9 轮 · blueprint:<一长串归因> · 类型:…` 收成 **`2/9 轮 · 详 <复盘路径>`**。
两头都保住:年检**查表即得**占比趋势(不必逐个开文档),要细节再顺指针展开。
🔴 未动 schema 结构(只改列语义与表头文案)—— 删列/插列会让旧行错位。

### 这一版的门禁是上一版刚立的

v8.296 收尾时我补了一条**反向锁**:「`_v8_ship.py` 里新增 `ledger_*` emit 字段 → 必须同步进台账指令」。
本版新增 `ledger_process_retro_path` 时**当场被它拦下** —— 接完 ship-stage §16 才放行。
立门禁的那一轮就用上了,算是它自己的第一个实证。

### 测试

998 → **1005**。

---

## v8.296 · `docs/audit/` 整条退役 —— 数据追踪不了 · 后续以 retro 为准

> 用户:**docs/audit/ 这个逻辑可以去掉了,数据没办法追踪,后续以 retro 为准。**

### 为什么它追踪不了

运行时文件落 **`~/.teamwork/audit/`(机器本地 · git 不跟踪)** —— 跨机器 / 跨人**根本聚不起来**,
而它的 telos 恰恰是「框架层面**跨项目**搜集流程质量」。代码里也早就自陈「**审计只写不读**」
(`_v8_ship.py`)。框架仓 `docs/audit/` 目录里 22 个文件中**只有 README 进过 git**,
其余 21 个是 gitignore 的残留。

**它原本要办的事,已经被两处覆盖**(且两处都真的在 git 里):
- `project-specs/PROCESS-LEDGER.md` —— 一行一 feature · 机器字段 · **随 feature MR 原子合入** · 可查表算账
- `docs/RETRO-LEDGER.md` —— 框架侧一行一版 · 永久 · 年检直接读

### 删了什么

| 位置 | 内容 |
|---|---|
| `_v8_ship.py` | `_write_audit_record`(86 行)+ `_capture_audit_sources`(27)+ `_audit_dir`(11)+ 调用点与 emit |
| `_v8_ship.py` | 🔴 **`--main-model` 死参数** —— 唯一消费者就是 audit record,help 还写着「写入 audit」= 在说谎 |
| `docs/audit/` | 整个目录(README + 21 个 gitignore 残留)· `.gitignore` 对应规则 |
| `update.py` | 对账豁免前缀收窄为 `("docs/retro/",)` |
| `ship-stage.md` | 「三处落点」→「两处落点」· ship2 的审计回收段删掉 |
| 测试 | `test_audit_sources_v8207.py` 整文件 + `test_ship_v8145_flow` 两例 + 残留 `TEAMWORK_AUDIT_DIR` env |

**保留**(同名不同物,别误伤):`_prepare_audit_path`(prepare-check 的 jsonl)是**活门禁** ——
主工作区 prepare → worktree init-feature 靠它对通,有真读者。

### 退役时发现的覆盖缺口(顺手补上)

`test_pause_mark_v8192` 里两个用例断言的是 audit 草稿渲染(user_email / AI-wait 三分 / host frontmatter),
删之前查了一下:这批数据的**活消费者** `ledger_timing`(→ PROCESS-LEDGER 四列)**零测试覆盖** ——
唯一的端到端保障挂在将死的那条线上。故不是删,是**改断言活路径**,并补一条「退役 audit 不能顺手砍掉台账数据源」。

> 教训进 RETRO:**退役一条链路前,先看它是不是别人唯一的测试宿主。**

### 反馈往哪走(替代口径)

框架级 bug / 工具判例 → 写进 PROCESS-LEDGER 行的「反思摘要」列(随 MR 进 git · 年检查得到);
真值得改框架的 → 开 issue 或在框架仓落 RETRO-LEDGER 行。**别再指望本机的审计文件被谁读到。**

### 测试

1001 → **996**(净减 5:删掉 7 条测已删机制的,补回 2 条测活路径的)。

---

## v8.295 · stage 耗时归因采集(补上「有数字没归因」那一环)

> 用户:**是否需要增加一个耗时复盘机制,每个阶段结束后总结耗时复盘,记录到固定文件夹 · 放到项目里进 git。**

### 结论:需要,但**不新建文件夹** —— 缺的是归因,不是载体

先盘已有的三层:`state.json.stage_contracts[stage]`(机器采 duration / await / **active_minutes** v8.276)
→ `project-specs/PROCESS-LEDGER.md`(一行一 feature · **已有「各阶段耗时」列** · 在项目里、进 git、
随 feature MR 原子合入)→ `docs/retros/`(业务/工程复盘)。

**缺的正是归因**:现有列只有**数字**(`blueprint 318m`),不回答「这 318 分钟花在哪」——
而 SVC-PLATFORM-F260726 复盘最值钱的恰恰是归因:blueprint 6 波往返里**波 5、6 是纯文档对齐、无设计价值**,
双档同步吃掉 ~35% 轮次 / ~25% token。

**不新建文件夹**:`docs/audit/` 是前车之鉴 —— 累了 22 个文件,代码自陈「**审计只写不读**」。
写了没人读的产物是纯成本。

**时机上用户是对的**:这类归因**只有 stage 结束时当场记得住**;ship 时回填要靠产物 mtime 反推
(那正是这次复盘干的苦活)。

### 机制(复用 v8.281 已跑通的形状:收敛后记录 → ship 聚合 → 年检分析)

```
state.py stage-cost --feature <path> --stage <goal|ui_design|blueprint|dev|review|test|browser_e2e> \
    --rounds <总轮次> --overhead-rounds <其中纯协调开销> \
    --kinds '双档同步;门禁重试' --note '最大的一笔开销是什么'
```

- 存 `state.json.stage_cost[]` → ship1 archive emit `ledger_stage_cost` → PROCESS-LEDGER **末尾新列**
  「⏱️ 耗时归因(协调开销轮/总轮·最大一笔)」(🔴 schema 演进纪律:只在末尾加列)
- **非门禁 · 纯采集**(不记不拦 ship · 台账列留空 = 有效前缀)· 零开销也要记(`--overhead-rounds 0`)——
  「这次没开销」和「没记录」是两回事,年检要分得开
- 物化护栏:`--overhead-rounds > --rounds` → FAIL

**提示放在 complete emit,不写进各 stage 文档** —— 机器在**正确的时刻**提醒(带本 stage 实际耗时 +
可直接跑的命令 + 「趁现在记」的时效说明),不靠文档记忆。且**只在有多轮往返成本的 7 个 stage 提**
(ship / pm_acceptance / panorama_sync / diagnose / execute 不提)。

### 🔴 为什么这不是又一道「环节化自检」

v8.283 的规则衰减分类学把「环节化自检」判为**会衰减、可砍**的那类。这条不同:
- 它**不让 AI 自查做得好不好** —— 采的是 **AI 自己算不出、事后也复原不了的事实**
- 它是**验证提效改动是否起效的唯一手段**:v8.294 的收敛期归一 / TC 职责边界 / 投机窗准入
  **都声称能砍这块协调开销**,没有这列数据就无法证伪

### 顺带修好一处既有不一致

新加的 schema 门禁(表头 / 分隔行 / 示例行列数必须一致)当场抓到:**v8.281 加「🛡️ 起草可预防性」列时
没补示例行的对应格** —— 示例行比表头少一格已经存在一版。已补齐。

### 测试

988 → **1001**。

---

## v8.294 · 复盘驱动:localconfig 在 worktree 里读不到(真 bug)· rival 设计强制 · TC 职责边界

> 来源:matrixpower SVC-PLATFORM-F260726(三级算力体系 + 锚定链定价 · 计费热路径 + 破坏性迁移)
> 的评审耗时复盘。逐条对着现行代码核过 —— 其中 R4(external 门禁词汇表)**已由 v8.291+293 修掉**
> (case 跑的是 v8.287.1),R5 是反面确认(5 条 high 全实锤 · 不因耗时降档)。

### 一、🔴 R3 是真 bug,且比复盘诊断的宽 5 倍

复盘报「fast_mode 静默失效,疑似 init-feature 快照链路问题」。实际根因更深:

`.teamwork_localconfig.json` 是**本地配置、不入 git**(bootstrap 自动 gitignore),因此**只存在于主工作树**。
而**五份独立实现**都是「从 feature_dir 向上找 · 遇 `.git` 停」—— linked worktree 的根有 `.git`
(**文件**形式)却没有配置 → 全部静默回退默认值。**teamwork 默认 `worktree: auto`**,
等于这五项配置在真实 feature 上**从来没生效过**:

| 读取者 | 配置项 | 起于 |
|---|---|---|
| `state.py _read_fast_mode` | `fast_mode` | v8.260 |
| `state.py _read_id_strategy` | `id_strategy` | v8.79 |
| `_v8_engine._idle_threshold_minutes` | `idle_threshold_minutes` | v8.276 |
| `_v8_engine._localconfig_max_review_rounds` | `max_review_rounds` | — |
| `_v8_ship._read_archive_on_ship` | `archive_on_ship` | v8.82 |

讽刺的是 `state.py` 里另有一段**正确**实现(`git worktree list --porcelain` 取主树再读 config)——
代码自己知道该怎么做,那五处没用它。**不是漂移,是五份副本生下来就都是错的。**

**修**:抽 `_v8_engine.load_localconfig()` 唯一解析器 —— 遇 `.git` **目录**才停(主仓根),
遇 `.git` **文件**(linked worktree)就解析 gitdir **跳到主工作树继续找**。纯文本解析不起 subprocess
(git 卡了不该让配置读取跟着不可用)。五处调用点全换,并加门禁锁「只准剩一份实现」。

**可见性**(复盘第二诉求 —— 静默回退是双输:用户既没拿到速度、也不知道为什么慢):
init-feature kickoff 回显三态且各自说明来源 —— `on(来源 localconfig)` /
`off(localconfig 为 true 但被 yolo 覆盖)` / `off(localconfig 未开)`。

### 二、rival 设计强制(复盘 §二 · 本轮最高价值的沉淀)

复盘问「为什么没先想到把标记打在 accounts 上」——「内部运营账户」被设计成 singleton 指针表 +
独立审计表(2 张新表),用户一句话 → 6 新表变 4 新表 + 2 列。

它自己诊断到了根因:**简洁性 checklist 是验证式的**(作者给的理由成立吗),四问确实跑了,
但**参照物由作者的叙事给定**(「能否并入 `monetization_config`」—— 一个冻结面,当然不能),
**没人问「这个设定的自然归属实体是谁」**。盲区只有**生成式**才破。

落 Architect 简洁性 lens + **blueprint 运行时 brief**(只改 stage doc 到不了 AI):
评审**新增结构**(新表/新模块/新抽象/新服务)必须**自己先生成 ≥1 个替代形态**
(并入宿主实体加列 / 现算不存 / 复用既有 / 根本不做)再裁决 ——
🔴 **「赢了作者列举的被否方案」不构成通过条件**。附:「全局唯一 / singleton 语义」**不等于**需要单独一张表。

### 三、TC 的职责边界(治 R1 的一半)· 不合并 TC/TECH

复盘算出双文档同步吃掉 blueprint **~35% 轮次 / ~25% token**,提议合并两文档。核过之后不合并 ——
拆开看同步的**内容**:表数 27→33→31、错误码命名回填、过期注、存储改选连锁,而
**TC 模板里根本没有表数/表清单/存储断言这些槽位**,是起草时自己加进去的。
即:**一半是 TC 越界**(划界直接**消除**),一半是真耦合(合并只是把跨 agent 往返变成同 agent 内往返)。
合并会让越界变得「合法」,把消除降级成缓解;而 `verify-ac.py` 这道 AC→测试的唯一机器门锚在
TC frontmatter,合并要重做 schema。

**新增 `templates/tc.md § TC 的职责边界`**(格式单源 · blueprint ④ / qa.md / rd.md 指过来):
- **telos**:把每条 AC 变成可执行、可判定的验收判据 —— 回答「怎么证明它满足了」,不回答「怎么做出来」
- 🔴 **一句话判据:换实现就要改的内容,不属于 TC** —— 假设 TECH 换实现方式,这条用例还成立吗?
  还成立 = 验行为归 TC;要跟着改 = 持实现形态归 TECH
- **关注**:AC↔用例绑定 / 可观测行为 / **边界与异常路径**(QA 核心价值)/ 测试层级与优先级
- **不关注**:表结构与表数 / 模块划分与选型 / 存储形态 / 性能实现手段(但性能**指标**若是 AC 则必须验)
- 🔴 **契约值的分寸**:断言到的错误码/状态码/字段名**必须写具体**(不具体就不叫断言);
  但**维护一份清单**(全部错误码、新表数量)= 复述 TECH,必删。**TC 从不需要知道有几张表。**

### 四、角色的两种用法(ROLES.md 新增判据)· 治 R1 的另一半

**同一个词在起草期和评审期不是一回事**:

| | 起草期 | 评审期 |
|---|---|---|
| 角色是 | **分工标签**(同一个 AI 切帽子) | **独立采样点**(不同上下文 / 不同模型) |
| 能否合并 | 🟢 能 —— 省跨 agent 冷启动往返 | 🔴 不能 —— 多视角退化成「一个视角 × N 份」 |
| 依据 | 产物有机器门兜底(verify-ac / build / 测试硬门) | v8.155 实证:in-context architect 在 goal 只产鼓掌 · 被冷审的 external/PL 反超 |

落地:blueprint/dev 的 **RD 与 QA 起草期合一**;blueprint ③ 改为
**「起草期并行 · 收敛期归一」** —— 复核后的修订由**同一 agent 顺序改两档**,
纯机械同步项**主编排直接 Edit 不派 agent**。评审席位照 roster 隔离冷审,不受影响。

### 五、R2 投机窗准入

投机窗原有**时点**纪律(只在终确认后)但无**开放决策数**条件。补:
§待决策项里**影响表结构/模块形态**的开放项 **≤1** 才投机;>1 或含结构分叉 → 等终确认再起草。
why:「终确认改:默 ≈ 全默」的统计前提**只在单决策上成立** —— 多个结构性开放项时草稿必须押某一组合,
用户改选任意一项都触发差量重写(实证:两项结构性改选 → 一整轮重写 · 该轮 token ~1.3× 初稿 = **投机变净亏**)。

### 测试

970 → **988**。

---

## v8.293 · 全库冗余清理:死岛 · 退役残留 · 敏捷需求 legacy 整条删除(净 −1600 行)

> 用户:**逐个文件整体 review 下,看下哪些冗余需要清理或者删掉。**
> 判据三条:**还有没有消费者** / **是否与现行规则矛盾** / **同一教义是否写了多遍**。

### 一、死岛 —— v8.291 只砍了入口,没砍被调链(−680 行)

| 位置 | 内容 |
|---|---|
| `state.py` | `_run_codex_review` / `_run_claude_review` / `_build_codex_prompt` / `_run_streamed_to_log` / `_build_claude_review_cmd` / `_detect_host` + `EXTERNAL_HOST_TO_MODEL` / `REVIEW-ACK` 协议 / `_prompt_doc_stale_reason`(`--prompt-doc` 参数早已删)/ `_FINDING_POSTURE_HINT` —— **586 行** |
| `state.py` | `scaffold-review-prompt` **整命令**(零文档引用 · 用途已被 external-review 自写 prompt-doc 取代) |
| `_v8_stage_specs.py` | `_check_external_hetero` + 4 个专属常量 —— **63 行** |

🔴 其中一颗雷:`EXTERNAL_REVIEW_SAME_CONTEXT_BLOCKED` 把 `"subagent"` 列为**必 BLOCK** 的同源字面 —— 而 v8.291 后 subagent 恰是**唯一合法形态**。谁把这 checker 重新接上,拦的就是唯一支持的路径。

`EXTERNAL_STAGE_TO_PROFILE` 三层嵌套 dict 折叠为两个常量:`codex-agents/` 已删,三个 stage 的 claude profile 本就全是同一个 `reviewer.md`。

### 二、退役声明贴在头上、正文一字未改(3 处)

- 🔴 **`review-stage.md` 硬规则 1** 仍要求「各自落 `REVIEW-{role}.md`」,而同一份白名单的**规则 8** 写着「v8.289 已取代该文件」—— **两条硬规则直接打架,漏在最高权重位置**。顺带修:编号出现两个 8。
- `roles/external-reviewer.md` 头部有 v8.291 退役声明,正文四条照旧写着「claude 主时调 codex」「OpenAI ToS 合规」「文件名必含 codex/gemini 字面」→ 整篇重写。
- `disable_external_review` 仍是 `teamwork_localconfig.json` 的活配置 + `config.md` 一整节 —— 能活一版是因为 v8.291 的退役扫描测试 **glob 只扫 `*.md`/`*.py`,漏了 `.json`**(已补)。

### 三、「敏捷需求」/ `lite` / `blueprint_lite` 整条 legacy 删除(−400 行)

删的理由**不是「没人用」**,是 audit 查出 **三份 flow-key 实现对同一输入解析出不同的转移图**:
`state.py` → `Feature+full`(无 blueprint_lite 的图)· `_v8_engine.py` → `Feature+lite`(含 blueprint_lite),
**而 engine 的注释还声称与 state.py「严格同口径」**。三份实现无一被测到该输入。

用户拍板:不选边,整条删。lite 档 v8.223 已退役,其链本就是 Feature 链的 `needs-ui=false` 剖面(纯冗余)。
删:`AGILE_FLOW` / `FLOW_BY_TYPE["Feature:lite"]` / `BLUEPRINT_LITE_SPEC` / `DEFAULT_REVIEW_ROLES` 5 条 / `STAGE_CHAIN_PREVIEW` 一支 / `stages/blueprint-lite-stage.md`。**stage 数 13 → 12**。
新增门禁:三份实现对同一 state 必须给出一致的内部键与转移图。

### 四、孤儿模板(用户逐个拍板)

- **`templates/architecture.md` 351 → 192 行**:产物 `{子项目}/docs/architecture/ARCHITECTURE.md` 是活的(SKILL 路由 + engine 读 + ship 门),模板却零消费者 —— 是**路由缺口**不是死文件。补 SKILL/architect 指针;**藏在里面的 68 行迁移起号纪律上提到 `standards/backend.md §五`**(那里才是权威);删 86 行 api-design/deployment 示例子模板;去掉「超 50 行必拆」的能力上限规则。
- **`templates/e2e-registry.md` 241 行整个退役**:全库零入口 —— 没有任何文档说 REG case 长什么样 / 放哪 / 怎么建,却只有 ship distill 在要求逐项申报。连 `DISTILL_KEYS` 的 `reg` 槽位一起删(6 项 → 5 项)。

### 五、模板层去重与矛盾(−330 行)

- 🔴 **`ui.md` 段落契约矛盾**(真 bug):模板明令「视觉描述一律归 HTML 预览产物 · **不在本文复述**」,而 `ui-design-stage.md` / `roles/designer.md` 要求 body 必含 §页面列表/§交互流/§视觉规范/§字段映射 —— **模板里没有这四段**。Designer 照哪边写都违反另一边。按「templates/ = 格式唯一真相源」改 stage 与 role。
- **`config.md` §localconfig −116 行**:是 JSON 模板 `_comment_*` 的逐字第二副本,且用 ` ```markdown ` 围栏把它描述成带 `## 负责人` 标题的 **markdown 文件**(真实文件是 JSON)—— 副本必漂,这次漂到了介质。改指针;第三份(`bootstrap.py` 的 DEFAULT dict,原靠一句「🔴 两处都加」的自觉)换成**物化对齐门**。
- 三份「起草要点」段自陈「v8.199 cite 仪式已废」却仍在逐条复述对应 stage 的硬规则 → 整删。
- `tc.md`:三个孤儿段(标「代码审查时填写」但 review 的产物契约是 REVIEW.md · 从不读)+ Gherkin 语法速查(HARD-RULES 判据:模型默认就会的一律不收)+ 一个 `standards` 里根本不存在的「后端覆盖率 > 80%」阈值。
- `adr-index.md` 66 行里「PMO 读本索引」写了 4 遍;`knowledge.md` 300 行上限与文档边界表各写两遍;`pm-note.md §3` 是 pm-acceptance-stage 暂停点脚本的逐字副本(PM-NOTE 是**已决策后的记录**)。
- ADR 落点权威分裂(`SKILL.md` 指 Feature 目录 vs `adr.md`/`architect.md` 定「`{子项目}/docs/adr/` 唯一落点」)—— 同 v8.205 sitemap case 复发,已归一。
- `preflight` 旧机制名 → `triage`(5 处);`tech.md` 实现步骤表的 TDD 红绿词表(与同节「节奏 AI 自定」自相矛盾)。

### 测试

962 → **970**(+8 类:死物不复活 / 退役声明与正文一致 / § 引用可解析 / 三份 flow-key 一致 / localconfig 单源 / ui 契约 / **markdown 围栏平衡**)。
最后一条是自伤实证:按 `## 标题` 切段时切掉了 `adr-index.md` 的围栏闭合 —— 切文档一律回来验围栏。

---

## v8.292 · WS 拆解按交付内聚 · 不按评审面 · 默认合并

> 用户拍板:**WS 拆解都按交付内聚方向拆,不要按评审面拆,尽量不要拆太多 feature。**
> 审出的问题:原判据虽已写「主判据 = 交付内聚」,却在**同一行**把「评审 blast radius」列为合法拆分理由,并把它放进「保持独立的硬理由」清单 —— 那恰恰就是按评审面拆。

### 为什么按评审面拆是错的(写进判据)
横切出来的件**各自不能独立上线**(前端等后端 / 后端没人用),feature 数与跨件协调成本上升,**而评审总量并没变少**。内聚单元确实大到评审吃不消时,正解是:① 找**更小的内聚切片**(仍是端到端可交付的**纵切**),或 ② 接受多轮评审(review 收敛协议管这个:severity 门 / 验证轮 / 轮次预算)—— **不要**为了好评审把不能独立交付的东西拆开。

### 改动
- `docs/feature-planning.md` Step 5.7 边界判据重写:**交付内聚 = 唯一主判据** · 🔴 **默认合并 · 拆分是例外**(每一刀都要说得出「为什么这两件不能一起交付」,说不出就并回去)· 显式列反模式(代码在不同子项目 / 前后端分属 / 改动面大不好评审 **都不是理由**)。
- **保持独立的硬理由从四类收到三类**:外部依赖 gate(不绑架宿主交付)/ 交付节奏不同(上线时点本就分开)/ 管辖边界(不同团队拍板)—— **删掉 blast radius**。薄承接件默认并入宿主件 · 含金量悬殊 = 强合并信号(保留)。
- **粒度反压加严**:BL > 8 → **> 6**;触发条件加「按评审面横切」;默认姿态明写为合并。
- 同步 `templates/workstream.md`(拆分按交付内聚 · 不按子项目切、**不按评审面切**)+ `state.py` planning-check 清单。

### 机器守护(反压从文本变物化)
`ws-lint` 新增 `granularity_warnings`:features > 6 → WARN(**不 FAIL** —— 拆得对不对是判断题,机器只负责把问题摆到台面,不代用户拍板),warning 正文直接给出复核清单(逐件问「为什么不能一起交付」+ 反模式提醒 + 薄件合并信号)。

### 验证
- 新增 test_ws_granularity_v8292(8:交付内聚唯一主判据 / 评审面显式禁止 / blast radius 已移除 / 超大内聚单元有正解指引 / 模板与清单同步 / 7 件 WARN / 6 件不 WARN / **WARN 不是 FAIL**)· pytest **964 passed**。

## v8.291 · 跨厂商异质模型评审彻底退役 · 第三视角唯一形态 = 错开模型 subagent 冷审

> 用户拍板:**跨厂商异质评审太耗时,效率影响严重,彻底去掉,改为 subagent 不同模型冷审。**
> 实证支撑(台账):`codex exec` 挂死 98m 后杀掉重试 · OpenAI「Additional safety checks」慢路径(代码评审 prompt 天然命中)· 反复踩未登录 / MCP spawn 卡死 / ARG_MAX。而**同厂商模型错开**(会话 fable5 → 外审 opus)已拿到独立采样的主要收益 —— 上下文隔离 + 权重错开,零 CLI 成本。

### 拆除量(不是加开关 · 是整条路径连机械一起删)
| 层 | 删除 |
|---|---|
| `state.py cmd_external_review` | **770 → 85 行**:host→model 映射 / `which <cli>` / `--preflight` 登录探测 / CLI exec 与超时 / stdout 质量检查 / `--self-review-fallback` 降级 / `degraded`·`heterogeneous` 语义 / dry-run |
| 死 helper | `_preflight_external` · `_external_timeout_sec` · `_detect_cli_version` · `_check_external_review_quality` · `_read_disable_external_review` · `_localconfig_disable_external`(合计 ~140 行) |
| 命令参数 | `--host` / `--model` / `--codex-model` / `--preflight` / `--self-review-fallback` / `--reason` / `--dry-run` / `--accept-quality-warnings` / `--prompt-doc` 全去(留 `--feature --stage --commit --base --verify-fixes`) |
| 产物门禁 | `_evidence_external_review_artifact` **136 → 30 行**:异质性硬约束(文件名模型白名单 / review_model 字面比对 / degraded 语义 / host 比对)整套删 —— **没有可冒充的对象了** |
| 配置 | `disable_external_review` 退役(自愈默认表 / 三处 helper / 五处文档 · 存量配置被忽略) |
| 规范 | `standards/external-model-usage.md` **286 → 63 行**(跨厂商机械全删 · **裁决纪律 §12 原样存活** —— 它与模型无关且被 5 处引用) |
| profile | `codex-agents/`(3 个 toml)整目录退役 · `claude-agents/reviewer.md` 去 codex 对照段 · `update.py` 白名单同步 |
| 测试 | 退役 94 条测已删机械的用例(`TestExternalReviewCommand` 30 · `TestHostAutoDetect` 7 · `TestExternalReviewHeteroEnforcement` 14 · `test_external_mech_v8191` 整文件 …)· 换 20 条新契约用例 |

### 新契约(收敛为两条 + 一条不变式)
- ① **必须隔离 subagent**(`review_via: subagent`)—— 主对话热审 = 同上下文 = 零独立性;
- ② **必须照实申报模型**(`review_model` 非空)—— 供台账核「错开」是否真发生;
- 🔴 **yolo 不内化律存活**(v8.67):无人值守时额外要 **prompt doc**(实跑证据 · 由 `external-review` 落盘)—— 防 AI 直接手写产物自盖章。证据载体从「CLI 子进程日志」换代为「配方 doc」;`ultra-ingest` 产物豁免(provenance 是会话转录)。

### 🔺 顺带的门禁增强(拆除的副产品)
「fix 后 APPROVE 必须有 external 验证证据」原有 `disable_external_review=true` 豁免 —— 那个豁免**只因跨厂商 CLI 太贵才存在**。外审变成廉价 subagent 后**豁免取消**:这道门现在无条件生效。同理 legacy 全局日志路径 `~/.teamwork/external-review-logs` 一并退役(它还会污染测试隔离)。

### 验证
- 新增 test_cross_vendor_retired_v8291(9:机械已删 / 配置退役 / codex-agents 删除 / 命令不 exec / 新契约成文 / **yolo 不内化律存活** / 裁决纪律存活 / 全库无残留活配置 / 唯一形态成文)· pytest **956 passed**。

## v8.290 · 流程文档整体精简 + PRD/TECH 设计文档档位规则

> 用户原则:**保住底线规则,其余不限制模型发挥,精简没必要的 HOW**(示例:架构视角只需「架构要合理、防止未来维护成本过高」· 至于怎么设计 AI 自决)+ 新规则:**PRD、技术方案必须主模型或高级模型出设计或参与评审**,其余尽量主对话编排 subagent 并行。

### ① 新规则:设计文档档位(5 处消费时点)
- **PRD 与 TECH 必须主模型 / 高级模型出设计或参与评审** —— 与 v8.268/269 模型错开复合:**错开也只在高档之间错**(fable5↔opus)· **不许降到验证档**;其余环节(TC 对照 / 测试执行 / 机械外化)该降就降,**主对话编排 · subagent 并行**。
- 落 `DISPATCH_TIER_REMINDER`(每 stage-start 自动附带)+ goal/blueprint 两 brief + 两 stage ②硬规则白名单。
- why 写明:PRD 定义「做什么」错了整条链在做错的东西 · TECH 是全局质量上限方案错了下游全错 —— **两份设计文档定质量天花板**。

### ② 文档精简(判据:证据/独立采样/主权/机械/逆默认 = 底线保留 · HOW-to/示例/重复/考古/铺陈 = 砍)
| 文档 | 行数 | 🔴 |
|---|---|---|
| SKILL.md | 754 → **544**(-28%) | 74 → **43** |
| docs/prepare.md | 412 → **365** | 33 → 26 |
| docs/feature-planning.md | 294 → **287** | 43 → 39 |
- **行 205 的 3173 字符怪物拆成 9 条**(最长 391)· v8.268 双路 + v8.269 单路合并成一条「**评审模型必错开(独立采样不变式)**」。
- 砍:v7/v8 范式对比图 · 45 处版本沿革标注 · 错误处理协议 ASCII 流程图(与 bypass 节同一件事)· 文档清单与路由速查两表合并(零文档丢失)· 31 处重复标红降级 · prepare「怎么侦察」的具体清单(**要不要侦察是底线 · 怎么侦察留给模型**)· feature-planning 里 IA 镜像律/分层同构律的展开(改指 ui-design 权威处)。
- `roles/architect.md` telos 改为用户示例形态:**底线「架构要合理——别让未来的维护成本过高」+ 显式「至于架构怎么设计 AI 自决」**;`roles/rd.md` 同款。其余 6 个 role telos 本就是「说视角 + 缺了会留什么问题」,未动。
- `docs/conventions.md` **如实不砍**:288 行几乎全是 ID/命名约定与路径/状态机接口(判据④ 模型不可能知道)。

### ③ 顺带抓到三个真问题
- 🐛 **SKILL 指向 `blueprint § 7.5`** —— 该章节已随 v8.284 四段结构重构消失 → 改指 `§④`。
- 🐛 **命令清单已漂**:自称「≈55 命令」,52 个真实子命令里 **11 个从未出现在 SKILL.md**(整个 micro 流程 `execute-start/complete` · `review-preventability` · `ws-lint` / `ws-progress` / `test-baseline` / `ledger-migrate` …)。文档自称「权威 = `state.py --help`」却抄了份过时副本 —— **又是「指针 + 复制」**。改分类概览(A 状态机入口 / B stage 流转 / C 维护与数据)+ 权威指针,保住 11 个 routing 级语义特殊命令。
- 🐛 **`UI-RULES.md` 从未进 SKILL 路由表**(既有缺口 · 非本次砍掉):它是 ui_design 必读 + bootstrap 七件骨架之一,用户问「设计规范在哪」路由不到 → 补入(连同 `test-baseline.md`)。

### 验证
- 新增 test_flow_doc_slimming_v8290(9:无超长行 / 🔴 密度 / 命令清单是指针非副本 / routing 级命令仍在 / 底线全在 / 断链已修 / role telos 底线+自决 / **project-specs 清单跨文件同步守护**〔SKILL 路由表 ↔ conventions §13 · 把 v8.259 的人工七点清单换成机器检查〕)· pytest **1041 passed**。

## v8.289 · REVIEW-<role>.md 退役 · 改为 REVIEW.md 内每角色 coverage 申报

> 用户:重新 review 流程,看哪些过程文档没必要写。用同一把尺子(**有没有真读者**)过完全部产物 —— 其余都有真消费方(PRD/TC/TECH 被 dev 照做 + verify-ac 机器读 · REVIEW.md findings 台账 70 处消费 · TEST-REPORT 是 pm_acceptance 逐条核对 AC 的实证来源 · verdicts 被门禁解析 · screenshots 是用户验收证据),**只有 `REVIEW-<role>.md` 是纯仪式**。(`docs/audit/<id>.md` 用户指示暂不动。)

### 四条证据
1. 门禁 `_evidence_review_role_artifacts` 只查**文件存在**(`.exists()`)· 不解析任何内容;
2. 角色归属**早已在 REVIEW.md** —— findings 台账每条带 `source: arch|qa|external`;
3. **实测就是写两遍**:aifriend `REVIEW-arch 37 行 / REVIEW.md 38 行` · aon-core `55 / 63`;
4. 内容形态是**确认性叙述**(「实现对齐 TECH」「架构一致」「无回归风险」…),不是 finding。

### 但保住了它的真价值
光秃秃 `APPROVE` + 零 finding,与「根本没评审」在产物上**无法区分** —— 这个防橡皮图章的性质不能丢。改用 external 早在用的 **coverage 申报**形式:REVIEW.md 内每个 roster 主审角色**一行**申报查过的方向(有问题列 finding · 无则「查过无发现」)。成本从 40 行降到 1 行,性质不变。

### 改动
- 门禁换代:`review_role_artifacts`(文件存在)→ `review_role_coverage`(REVIEW.md 内申报)· **roster-aware 语义原样保留**(移出的角色不查)· legacy state 无 roster 时跳过(不对存量加严)。
- REVIEW.md frontmatter schema 加 `coverage:` 段示例;review-stage ②规则 8 + Output Contract 改写。
- 全链清理:review brief 结果段与 complete 命令 `--artifacts REVIEW.md`(去 REVIEW-arch)· engine 产物模板表 / 归档文件名表 / complete 命令模板 / roster 注释 · fast 与 Bug brief 措辞 · SKILL fast 节 · templates/README。
- 常量正名 `_REVIEW_ROLE_ARTIFACTS`(role→文件名映射)→ `_REVIEW_MAIN_ROLES`(角色集)。

### 验证
- v8.241 的 4 条 roster-aware 测试改写为新机制 6 条(roster 移出不查 / 缺申报 FAIL / 申报形式宽松 / legacy 跳过 / 空 roster / **Bug 流 external-only 无需主审申报**)· pytest **1028 passed**。

## v8.288 · tdd.md 退役(三条规则已在白名单 · 留着就是第二份副本)

> 用户:「如果 TDD 只有三行,是否不用单独一个文件了」。核实后确认——**比预想的更该删**:v8.287 留下的三条结果规则里,**两条与 HARD-RULES 逐字重复**(每个 TC 有对应实现 / 测试必须真断言),第三条(≥3 次失败升级)也在。tdd.md 已经退化成我们一路在消灭的「指针 + 复制」第二份副本。

### 退役
- 删 `standards/tdd.md`(42 行)· 吸收其唯一独有内容:「结果由谁保证」表 → 压成 HARD-RULES #8 下的一行(AC 覆盖 → `verify-ac.py` · 真跑真绿 → `--test-exit-code 0` + `--test-stdout` 非空 + 差分基线 · 没作弊 → test-stage ②不走捷径 + 外审测试真实性)。
- **10 处入链改指 HARD-RULES**:STANDARDS.md 路由表 + 三条子项目加载链 · backend/frontend 的「TDD 流程唯一权威源」头注与 Subagent 加载指引 · common.md · dev-stage §相关 · blueprint ③菜单 · tech.md · 2 处测试。
- `standards/` 从 6 件 → 5 件:HARD-RULES(50 · 必读)+ common(354)+ backend(551)+ frontend(90)+ external-model-usage(286)+ scripts-policy(232)。

### 顺带:通用断链守护(治本)
- 新增 `test_all_standards_links_resolve`:全库扫 `standards/*.md` 引用,**指向不存在的文件即红**。
- 实证驱动:v8.285 删 stage heading 造成 6 处 cite 失效(靠 agent 报出才发现)· v8.287 退役 tdd.md 需手改 10 处入链 —— 这类操作该被自动拦,不靠人肉 grep。
- 另加 `test_tdd_md_retired`:退役前**必须确保三条规则已在白名单**(防「删了文件规则也跟着没了」)。

### 验证
- pytest **1026 passed**(+2)。

## v8.188 · 规划收尾:暂停问合入 merge_target → 建 MR → 提示用户合并 → 停(不自动起下一 feature)

> 实证 AON KA-PAGES:AI 规划完成后**自己** commit→push→建 draft MR,然后**立刻**跳进下一个 feature 的 prepare(还把新 feature 的 `merge_target` 设成**未合并的** `planning/ka-pages` 分支)—— 没有「是否合入 merge_target」确认暂停点,也没有「MR 建好 → 提示用户合并 → 停」。

### 改动(feature-planning Step 9 + planning-check)
- **规划收尾框成 3 步**(同 feature ship1):① R5 暂停问「**是否合入 `merge_target`**」② 确认后 worktree 内 commit+push planning 分支+开 MR(target=merge_target)③ 🔴 ⏸️ **提示用户合并 + 到此结束**。
- **🔴 不自动起下一 feature**:启动实施是**用户合并规划 MR 之后**的独立决策 · 🔴 **别叠 feature 在未合并 planning 分支**(feature `merge_target` = 集成分支 dev/staging · 非 planning 分支 · 否则实现 diff 混未合并规划、基线不稳)。
- `planning-check` `worktree_setup` + checklist item 6 同步(item 6 顺带修 v8.184 遗留的「主工作区直推」旧措辞)。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。
## v8.189 · 规划收尾 finalize:用户合并后切回主分支 + 清 worktree + 净化主分支(= ship2)

> 用户续 v8.188:规划 MR 建好提示用户后,用户说「已合并」→ 该进规划收尾流程:**切回主分支、清理 planning worktree、净化主分支**。补全 = 把规划收尾对齐 feature 的 **ship1→ship2** 两段。

### 改动(feature-planning Step 9 + planning-check)
- **收尾-2 finalize**(新 · = feature `ship-finalize`/ship2):用户说「已合并」→ 3 步镜像 ship-finalize:① `cd` 回主工作区 ② `git worktree remove` 清 planning worktree ③ `state.py main-sync --merge-target <mt>` 净化主分支(v8.145 起**不依赖 feature** · fetch + 按策略 pull 合并后规划产物 · 主工作区干净+最新)。
- **收尾-1** 的 MR 提示改成「合并完回来说『已合并』· 我进收尾」(引导第二段)。
- `planning-check` `worktree_setup` + checklist item 6 同步 finalize。

### 验证
- doc(feature-planning Step 9)+ code(`planning-check`)· `test_state` planning 4 passed · pytest 3 failed(baseline)/ 627 passed。
## v8.190 · main-sync 回收 teamwork auto-stash · 治 stash 累积无回收(harvest 跨两次最高频)

> 第二轮 harvest(163 条 · +74):「ship 收尾 / 主工作区 auto-stash 累积无回收」**26×**(上次 23×)· **跨两次 harvest 稳居第一**。main-sync `stash-pull` 每次备份 stash 但不 pop → 跨 feature/session 累积 **11+** · human 难判哪些可 drop。

### 改动
- **main-sync 回收 stash**(新 · 默认自动跑):`_reclaim_stashes` 只认 **teamwork 自建**的 main-sync stash(消息标识)· **drop 可证冗余的**(空 / 内容已在分支 · `git apply --reverse --check` 通过)· 剩含未合内容的 **surface**(feature 标签 + hint)· 🔴 **绝不碰用户自己的 stash**。
- **`--drop-stashes`**:用户确认不需要任何备份 → 全清 teamwork main-sync stash。
- ship-finalize / 规划 finalize / 独立 main-sync 都**自动回收**(emit `stash_reclaim`)· 不再累积。
- **测试** `test_stash_reclaim_v8190` +5(drop 冗余 / 留 live / 不碰用户 / drop-all / hint)。

### 验证
- code(`_v8_ship` `_reclaim_stashes` + main-sync emit + `--drop-stashes`)+ doc(ship-stage §6 · SKILL 命令行)· pytest 3 failed(baseline)/ 632 passed。
## v8.191 · external 机械成本三连修:preflight + 超时自动重试 + verify-fixes 增量重验

> 耗时归因(138 条 per-stage 数据)原因 2:external 的**机械 overhead**(非评审价值)—— 20× 实锤:「3 行改动跑 5 次 external(2 真轮+1 空跑+2 超时)review 墙钟 49m(80%)」「CLI 未登录到 review 才发现 → 降级折腾」「每采纳 finding 即全量重跑」。

### 改动(不动「评审必须真跑」原则 · 只砍机械成本)
- **`--preflight`**(①):review 干活前 which + **微 probe**(一次极小调用 · 秒级)验登录/网络/配额 E2E 通 · 失败此刻修环境 · 不烧完整评审墙钟才发现。
- **超时/空跑自动重试**(②):rc=124 / 空 stdout → **自动重试一次**(1.5x timeout · emit `attempts`/`timeout_sec_used`)· 省手动重跑轮;localconfig `external_review_timeout_sec` 调基础超时(长 review 项目)。
- **`--verify-fixes`**(③ · 仅 review):增量重验 —— base 锚**上一轮已评 commit**(结果文件 frontmatter `target_commit`)· prompt = 上轮 findings 全文 + 修复 diff · 任务 = 逐 finding 给 `fixed/not-fixed` verdict + 只查修复 diff 新问题 · **不全量重评**。结果落 `review-<model>-fixverify.md`(不 clobber 全量轮 · 供下轮再锚)· 锚点失效(rebase/同 commit)FAIL 提示退全量 · 与 `--prompt-doc` 互斥。
- review-stage.md 同步(external 步 + fix-retry 循环)。

### 验证
- code(`state.py` 4 helpers + cmd_external_review 三分支 + runners timeout/extra_prompt)+ doc · `test_external_mech_v8191` +12 · pytest 3 failed(baseline)/ 644 passed。
## v8.192 · pause-mark 计时排毒 · stage 内 R5 等待与工作分离(待优化 #5)

> 耗时归因:goal 均值 157m vs 中位 22m(max 128h)—— stage 内 R5 暂停(PRD 确认/预览确认/DB 确认)的**等用户墙钟全算成工作**(v8.172 只拆了 pm_acceptance)· 每次归因都要人肉排毒。

### 改动
- **`state.py pause-mark`**(新):emit R5 暂停点前打点(写 `open_pause`)· **下一个流程命令(start/complete/fix/retry)自动闭合**(`close_open_pause` 接进引擎 4 choke 点)· 等待累计进该 stage `await_minutes` —— resume 侧零纪律。
- **`_stage_durations`**:工作时长 = duration − await(breakdown 显示 `goal 20m(+等待30m)`)· 最耗时(工作)不再被等待污染。
- SKILL R5 协议加打点行。

### 验证
- code(engine helper+4 接线 · state.py 命令 · ship durations)· `test_pause_mark_v8192` +5 · v8.166 套件未破 · pytest 3 failed(baseline)/ 649 passed。
## v8.193 · skills 删减 batch:退役迁移器/收尾遗物/手写模板 + ARCHIVE 照章清空(−2.2k 行)

> 全量 review skills(29.6k 行):按自家律法(三层律 · 定期清空 · 工具自动落禁手写)删 🟢 批次。

### 改动
- **CHANGELOG-ARCHIVE 照章清空**(−1.0k):v8.128→187 共 60 版条目 · git 历史是冷库(章程自 v8.127 就这么写)。
- **删 `_v8_migrate.py` + migrate-v7-to-v8 命令**(−258):v7→v8 一次性迁移已过 190+ 版 · 无 v7 存量。
- **删 `post-feature.py` + 其测试**(−690):v7.3 时代收尾遗物 · v8.145 ship 重构漏删 · 仅自引用。
- **删 `templates/external-cross-review.md`**(−279):v8.20 起 external 产物**工具自动落**、手写是红线 —— 给禁止手写的文件留手写模板自相矛盾;engine scaffold 映射 3 处同步清。
- SKILL/TEMPLATES 引用同步清(migrate 3 处 + 1 处)。agents/README 瘦身(683→~150)留下批。

### 验证
- 净减 ~2.2k 行 · `test_v8_stage_specs` 90 passed · pytest 3 failed(baseline)/ 639 passed(删 post-feature 测试 −10)。
## v8.194 · agents/README 瘦身 683→64 行 · 删自标废止段 + v7.3 产物协议残留

> 承 v8.193 删减 batch 下批:agents/README(683 行 · 全仓仅 1 处历史引用)—— §三 Codex 调用规范**自标「历史记录 · 已被 §11 取代」仍躺 77 行**;§五主对话产物大半是 v7.3 产物命名(dev-report/acceptance.md 等 v8 已不产);§一模型偏好逐 stage 枚举(随模型代际漂移的拐杖);§四协议核心真实但三处重述 Progress Log、启动自问出现两遍。

### 改动
- 重写为 64 行紧凑协议:保留(dispatch 宿主速查 / 降级 WARN / 文件化 dispatch / Key Context 6 类 / Progress Log flush+轮询 / 状态分级 / 危险命令红线)· 删除(自标废止的 §三 · v7.3 产物命名表与 review-log schema · 模型逐 stage 枚举 · 重复段)· external 指针改指 standards §11。
- 净减 −619 行。零活引用(仅 external-model-usage 一处历史注)。

### 验证
- doc-only · pytest 3 failed(baseline)/ 640 passed。
## v8.195 · 🟡 待确认项裁决:删 diff-html-vs-panorama(static-html 退役工具)· 其余 3 件确认活消费保留

> 承 v8.193/194 删减:🟡 批次逐件消费点确认。**diff-html-vs-panorama.py**(340 行):仅 static-html 分支引用 · 163 条 audit 里 static-html 使用 = **1** · 前端栈已定项目强制 same-stack · verify-panorama 已 medium-aware 覆盖 → **删**(+测试 −10 · dev-stage/roles/ui.md 3 处引用改指 verify-panorama)。

### 确认保留(活消费实证)
- **e2e-registry.md**:ship §16 采写 `reg` 字段(REG-case)消费。
- **config.md**:conventions 3 处(缩写注册 + localconfig 模板)。
- **architecture.md**:含 database-schema 模板 = TECH §Schema 影响分析的上游。

### 验证
- 净减 ~700 行 · 引用清零 · pytest 3 failed(baseline)/ 630 passed。
## v8.196 · 规划链路 #1+#2:F↔BL 机读绑定(init --bl)+ ws-progress 可启动集

> 规划链路整体审视的两刀:① **F↔BL 绑定是链路最脆一环** —— 只存在于 ROADMAP 手填「对应F编号」单元格 · ship 自刷 WS/翻牌全押它填对;② **「下一个做什么」没有工具答案** —— execution_waves 是静态快照 · 执行中要人肉对照 DAG。

### 改动
- **`init-feature --bl BL-NNN`**(可选):写入 `state.json.bl` = F↔BL 机读绑定;`_resolve_ws_from_feature` **优先**走 state.bl → WS 名册反查(ROADMAP「对应F编号」降为兜底)—— 翻牌漏填单元格不再断链。
- **`ws-progress` 输出 `ready_to_start`**:名册里**依赖全 ✅ 已完成、自身待开始**的 feature(短名+BL)· emit 字段 + 进度块尾行「▶ 可启动(依赖已齐)」—— 并行调度/yolo 直接喂启动决策。
- 测试 +2(state.bl 解析 · ready 推导)。

### 验证
- code(`state.py` 3 处)· pytest 3 failed(baseline)/ 632 passed。
## v8.197 · 规划链路 #3+#4:执行线存在性 lint(幽灵 Line)+ 规划后变更成文路径

> 规划链路审视余下两刀:③ WS「承接执行线」写 Line 4 但业务架构里没有 → 无人查(愿景层→WS 的 taxonomy 是纯 doc 约定 · 断了不报);④ WS ✅ 规划完成后追加/砍 feature 无成文路径(实证 WS-03 追加 BL-006 · 合法性/是否重确认是灰区)。

### 改动
- **ws-lint 执行线存在性**(③):WS 承接的 `Line N` 必须在 `product-overview/*业务架构*.md` 的执行线列表存在 · 幽灵 Line → NONCONFORMANT(hint:新线先在业务架构登记)· 无业务架构文档 → skip 不误报。
- **feature-planning Step 10 规划后变更**(④):**追加 feature** = 轻量(R5 一句确认 → worktree 内改名册+ROADMAP+变更日志 → ws-lint/ws-progress → MR · 不重开全流程);**砍/改方向** = 回 feature-planning(WS 回 🔄 讨论中);🔴 已启动的 F 不在此列(执行层变更 · 别用规划变更掩盖执行返工)。
- 测试 +3(幽灵 Line / 存在 OK / 无架构 skip)。

### 验证
- code(`state.py` ws-lint)+ doc(feature-planning Step 10)· pytest 3 failed(baseline)/ 635 passed。
## v8.198 · loops 对照两修:await-merge 30s 轮询(合并自动下一步)+ yolo fix-retry 10 轮止损

> 对照 claude.com「Getting Started with Loops」:teamwork 是 Turn-based 最佳实践重度实现 · 缺口在 Time-based(结构性等待窗无人看:132h 等合并长尾 · CI 红无人接)+ Goal-based 的 max-attempts(yolo「持续自主解决」无轮次上限 · runaway 风险)。

### 改动
- **`state.py await-merge`**(新 · time-based loop):ship1 / 规划收尾 emit 等合并提示后**跑它** —— 30s 轮询 MR 状态(gh/glab · `--interval/--max-checks` 可调)· **MERGED → emit 下一步**(ship-finalize / 规划 finalize)· WAITING → 重跑续等(用户随时打断改人工)· CLOSED → surface · 连续 3 次查询失败 → FAIL(环境)。`--feature`(读 state.ship.mr_url)或 `--mr-url` 直传(规划场景)。
- **yolo fix-retry 止损**(goal-based max-attempts):同 stage fix-retry **≥10 轮**未收敛 → 硬停 surface(`yolo_rounds_exceeded` 接进 `execute_stage_fix` · 真·硬停的合法扩展:收敛失败 ≠ 继续死磕)· 非 yolo 不受影响(既有「3 次问用户」协议)。
- ship-stage §5 / feature-planning 收尾-1 / SKILL yolo 表同步。

### 验证
- code(`_v8_ship` await-merge · `_v8_engine` 止损)+ doc ×3 · `test_loops_v8198` +4 · pytest 806 passed(基线三失败已由并行修复清零)。
## v8.199 · 删 P0-11 cite 纪律(A 全删)+ brief 全面性核查

> 精简讨论首刀(用户拍板 A):cite 纪律 = 每 substep 动手前引 spec 原文自证「真读」+ 切角色重 cite —— 每 feature 几十次仪式输出。163 条 audit **零实证**拦到任何东西 · `cited_specs` 字段**零消费**(写了没人收)· 它想治的病(AI 不读 spec)已被 v8.151 起「brief 消费时点主动推」+ gate 物化接管。**模型越聪明 · 过时仪式越忠实执行 = 越有害**。

### 改动
- **全删**:STAGES.md §2 定义(~25 行)· 11 个 stage 的「必读 cite 清单」表(~140 行)· 各处 📎 指针行 · `stage-complete --cite` 参数与 `cited_specs` 死字段。
- **brief 全面性核查**(cite 表删后 brief = 唯一消费时点推送):13 个 brief **全部**指回对应 stage 文件(导航不丢)· 关键 🔴 推送就位(dev 3 / diagnose 3 / goal 2 / ui_design 3…)· 补 1 处:`_blueprint_brief` 的 TECH 结果行从老五段更新为 v8.181-183 全结构(现状基线/错误处理/依赖影响/查询性能/完工自查)。
- 误删回滚:roles/ 3 行 v8.155 冷审规范(「cite」为普通引用义)· git checkout 恢复。

### 验证
- 净减 ~180 行 + 每 feature 几十次仪式输出归零 · pytest 806 passed。
## v8.200 · 全模板加「🧩 补充洞察」自由区 · 模板是地板不是天花板

> 用户:模板是否可能限制模型能力?是否加一个 AI 自由发挥的补充板块(限制少 · 可留空)。判断:槽位不限能力 · 但「填完表=完成」的心智会 —— 模板外的重要发现(非常规风险/更好方案线索/跨 feature 影响)没处落就不会写。PRD 已有先例(v8.164 扩展区)· 推广到其余产物模板。

### 改动
- **tc / tech / ui / bug-report 四模板**统一加末段 `## 🧩 补充洞察(AI 自由发挥 · 可留空)`:模板槽位之外重要但没处落的 · 🔴 **地板不是天花板 · 填完槽位 ≠ 想完了** · 没有写「无」或删本节 · **不为凑内容而写**(防它自己变成新仪式)。
- PRD 不动(v8.164 `## 开工前必须想清的` 已是同物)。

### 验证
- doc-only(4 模板各 +5 行)· `test_v8_stage_specs` 90 passed。
## v8.201 · PRD canonical 到达率:goal brief 约束模板 + goal-complete 三命门校验

> 实测(v8.200 扩展区验证):post-v8.164 的 10 份 live PRD **仅 1 份**用 canonical 模板,其余自由结构/抄项目旧 PRD(同 WS-012 病根)—— 机读块/扩展区等新机制**到达不了**,加什么槽位都白加。

### 改动
- **goal brief 约束**(消费时点推):🔴 照 `templates/prd.md` 起草 · **别抄项目里旧 PRD**(附实测数据)。
- **goal-complete 校验**(`prd_template_conformance` evidence):只查**三个机读命门段**(不管字数/风格)—— `TEAMWORK-MACHINE` 机读块(或 legacy frontmatter)· 验收标准/AC(verify-ac 依赖)· 『开工前必须想清的』扩展区(可写「无」但段要在)· 缺 → FAIL + hint 指 canonical 模板。
- 测试 +3(自由结构拦三段 / canonical 放行 / legacy 缺扩展区仍拦)。

### 验证
- code(`_v8_stage_specs` check+接线+brief)· pytest 809 passed。
## v8.202 · 模板地址全 stage 到位:diagnose 补映射 + scaffold_hints 加「别抄旧」+ 4 brief 指针

> 用户:是否所有 start brief 都给模板地址?查实:`scaffold_hints`(v8.14)**早已**在 stage-start emit 绝对路径(10 stage 映射+validator)· 但 PRD 到达率 2/11 证明被忽略。真缺口三处。

### 改动
- **diagnose 补进 STAGE_TEMPLATES**(原漏:产 BUG-XXX.md 的 stage 反而 start 时不给 bug-report 模板)。
- **scaffold_hints 加 `usage` 警示**(单点 · 全 stage 生效):照绝对路径起草 · **别抄项目里同名旧产物**(旧文件 = 旧版模板快照 · 附到达率实测)。
- **4 个 brief 加统一指针**(blueprint_lite/test/browser_e2e/pm_acceptance):「📋 产物模板见 scaffold_hints.templates」—— 不在 brief 重复路径(防双源)· 只指向。

### 验证
- code(engine 映射+usage · specs 4 指针)· diagnose hints 冒烟 ✓ · pytest 809 passed。
## v8.203 · 规划收尾暂停点重构:头两项一步到位(自动合并 + 收尾 / 收尾+启动首个 BL)

> 实证 case(AON WS-14 MMP 规划):收尾是「终审 → 建 MR → 等你告知已合并 → 再收尾」的多段手动接力 · 用户被迫手动短路「你直接合并然后规划收尾」。收尾该把常用路径做成一等选项。

### 改动(feature-planning Step 9 + planning-check 双 emit 同步)
- **暂停点选项重构**:① **确认·合入 MR + 收尾**(commit+push+开 MR+**自动合并**+清 worktree+净化主分支 · 一步到位)💡 ② **确认·合入收尾 + 启动首个 BL**(同 ① · 收尾完直接 prepare 首波 ready BL〔execution_waves W1 / ws-progress ready_to_start〕)③ 建 MR 我自己平台合(await-merge 轮询 / 平台合)④ 先不提交 ⑤ 其他。
- 🔴 **自动合并硬门(选 1/2)**:仅 `merge_target` 非主分支(main/master)—— 集成分支纯文档/全景低风险 · 同 yolo 自动合入非主分支风险模型;平台拒(审批/CI/保护)→ **自动回退选项 3** · 绝不 force。
- 🔴 **启动首个 BL(选 2)守 v8.188 护栏**:必 finalize 完成后(集成分支已含规划产物)+ 用户显式选 + feature target=集成分支 —— 「别叠 feature 在未合并 planning 分支」仍成立(planning 分支已消亡)。

### 验证
- doc + planning-check 双 emit · 新选项出现在 emit ✓ · pytest 809 passed。
## v8.204 · external 异质评审默认关(用户拍板 · 全局一刀切 · yolo 也跟随)· 省 CLI 冷启动

> 用户:`disable_external_review` 默认改 true(默认关异质评审 · 太耗时)· yolo 也跟随默认关。厘清:开关只降级**第三视角 reviewer**(异质外部 CLI → 同模型 subagent 隔离冷审)· **架构师+QA 多角色评审完全不受影响照跑** · 耗时大头 = external CLI 冷启动。

### 改动(默认翻转 · 三处)
- **`_read_disable_external_review` + `_localconfig_disable_external` + bootstrap CONFIG_DEFAULTS**:key 缺省 / 无 config / 读失败 → **true**(禁用);**显式 `false` = opt-in 跨模型异质**。template localconfig seed 同步 true。
- **告警软化**(现在是默认常态 · 不再红字每次响):bootstrap heterogeneous_review status→`cold-review (default)` + note(非 warning)· 删 digest 🔴 行 · yolo kickoff `🔴🔴 醒目告警`→一行 `ℹ️ INFO`。
- **物化门禁不变**:第三视角**仍必真跑**(默认校验 `review_via: subagent` 冷审 · opt-in 异质校验实跑日志)· 去掉整个第三视角仍 BLOCK · 「非异质」也不许「不冷审」。

### 文档 reframe(避免变假话)
- README(中英)支柱表 / flow 表 / yolo 段:「异质 cross-review」→「第三视角独立 Review(默认同模型隔离冷审 · 跨模型异质 opt-in 升级)」。SKILL yolo 红线同步(第三视角默认冷审 · 异质 opt-in)。

### 验证
- pytest 809 passed(21 处 external 测试 setUp 改为显式 opt-in `disable_external_review:false` + 默认断言翻转)· 两读取器冒烟一致。
## v8.205 · 文档位置单源:SKILL 裸文件名误导修复 + sitemap 补模板(治 ROADMAP 落项目根)

> 实证 case(TermPro M5 规划):AI 把 `ROADMAP.md` 放**项目根**、来回挪。根因不是「没规范」而是**位置权威分裂** —— 模板阵营(templates/roadmap.md 头部「位置：docs/ROADMAP.md」)一致,但 SKILL.md 文档清单用**裸文件名**(`PROJECT.md`/`ROADMAP.md`/`sitemap.md` · 无路径)读起来像项目根,成了矛盾的第二源;sitemap 更糟 —— **连模板都没有**,全仓 3 个落点。

### 改动
- **SKILL.md 文档清单 + 路由速查**:三个裸名加 canonical 路径(`{子项目}/docs/PROJECT.md` · `docs/ROADMAP.md` · `{子项目}/docs/design/sitemap.md`)· 表头加 🔴「**位置权威 = 各 templates/*.md 头部「位置：」· 不在项目根裸放**」(单源指针 · 防再漂)。
- **新建 `templates/sitemap.md`**(补上唯一缺模板的产物 · 头部「位置：`{子项目}/docs/design/sitemap.md` 与全景同目录」+ IA 地图结构)· 全仓带路径引用本就一致指向 `panorama_path/sitemap.md`,conventions.md 是唯一异类 → 拉齐。
- **conventions.md** sitemap → `design/sitemap.md`(非 `docs/` 根)· **feature-planning Step 7** 写 ROADMAP 处加路径 + 指模板单源 · **templates/README** 登记 roadmap 位置 + sitemap 行。

### 验证
- doc-only(SKILL/conventions/feature-planning/templates)· pytest 809 passed。
## v8.206 · preview dev 工具面板改右下角悬浮(治顶栏 offset 布局 · 违 same-stack「零预览痕迹」)

> 实证 case(用户看预览页):dev 预览导航实际做成**右下角悬浮 Prototype Nav** · 比 spec 规定的**顶栏**合理。v8.187 理清了工具面板「放什么」(页面导航+状态注入 · 页内真实交互优先),但**位置写死「顶栏」**是错的。

### 治本
- **顶栏是 layout bar** —— 把真实页面内容**整体下推、offset 掉真实位置/尺寸**,恰恰违背 same-stack「**零预览痕迹 · 页面=真实代码**」核心目标(真实 app 没这条顶栏 → 加了预览就不像真实 app)。
- **右下角悬浮面板 = overlay** —— 不占布局流 · 不 shift 真实页面(页面在真实位置/尺寸渲染)· 右下角是 dev 工具通行惯例(devtools/toolbar 都在角落 · 一眼识别「工具非产品 chrome」)· 可折叠 · 半透明低层级。

### 改动(位置改 · 内容保 v8.187)
- ui-design-stage § 重命名 `preview dev 顶栏` → `preview dev 工具面板(右下角悬浮 · 非顶栏)` + 加位置治本段(顶栏反模式)· 页面区标注 `Prototype Nav`。
- 同步 same-stack 段 + `ui-rules.md` + `ui.md`(2 处)+ 新建的 `sitemap.md`:所有 dev shell 引用「顶栏」→「悬浮工具面板(右下角)」(RETRO 历史记录不动)。

### 验证
- doc-only · pytest 809 passed。
## v8.207 · ship2 审计源材料预抽(治「先删 worktree 再要三段判断 → AI 被迫 unzip 反读」)

> 实证 case(用户看 Codex ship2):ship-finalize 删 worktree **后**要 AI 补 audit 三段判断,但源材料(REVIEW.md/TEST-REPORT.md)随 worktree 删除只剩归档 zip 内 → AI 被迫 `unzip -p` 反读。反直觉的人机工学 bug(交付安全无问题 · 主工作区干净)。

### 治本
- **`_capture_audit_sources(feature_dir)`**(新):ship-finalize 在 **worktree-remove 之前**(feature_dir 尚在)抓 `REVIEW*.md` + `TEST-REPORT.md` 压成紧凑摘录。
- **嵌进 audit 草稿 `## 源材料摘录` 段** —— AI 读草稿即可填三段(做的好的/发现的问题/待优化的)· 三段占位 + emit brief 改指「照实抄草稿内 §源材料摘录 + 实际数据 · 🔴 **无需 unzip 归档**」。
- 读失败静默降级(绝不阻塞 ship2)· 无源材料 → 不加空段(三段仍在)。

### 为什么不移到 ship1
实际数据全来自内存 `state`(worktree 删了也在)· 只有三段的**源文档**随 worktree 消失 —— 预抽摘录是最小修复,保持 v8.145「ship2 out-of-repo bookkeeping」不变(audit 落 `~/.teamwork/audit/` 非仓库)。

### 验证
- code(`_v8_ship`)+ ship-stage §16 doc · `test_audit_sources_v8207` +4 · pytest 813 passed。
## v8.208 · 流程价值台账时长三分(总/AI自主/等待用户)+ 各阶段细粒度 + 用户邮箱列

> 用户:台账时长要细化 —— 各阶段细粒度耗时 · 区分等待用户 · 排除等待=AI 自主运行耗时;加一列 git 用户邮箱。基础设施(v8.192 pause-mark `await_minutes` + `_AWAIT_USER_STAGES`)已有 · 本版把它落进台账/审计。

### 改动
- **`_timing_split(state)`**(新):`AI 自主 = Σ 工作 stage(duration − await)` · `等待用户 = Σ stage 内暂停 + Σ 纯等待 stage(pm_acceptance)墙钟` —— 分离墙钟里的人工等待。
- **`_git_user_email(cwd)`**(新):`git config user.email`。
- **ship1 archive emit 加 `ledger_timing`**(total_wall / ai_autonomous_min / await_user_min / per_stage / user_email)—— 台账在 archive 采写 · AI 照抄确定性数据不肉眼算 state。
- **audit 记录**:frontmatter `user_email` + 正文「AI 自主运行:Xm · 等待用户:Ym」+「用户邮箱」行(跨项目 harvest 按人分析)。
- **PROCESS-LEDGER 模板**:`时长` 拆为 `时长(总·AI自主·待用户)` + 新增 `各阶段耗时` + `用户邮箱` 列 + 三分口径说明。ship-stage §16 同步。

### 验证
- code(`_v8_ship` 2 helper + archive emit + audit)+ 模板/§16 · `test_pause_mark_v8192` +4 · pytest 817 passed。
## v8.209 · PROCESS-LEDGER + audit 记录 AI 宿主类型(codex / claude / gemini)

> 用户:台账要记 AI 宿主(codex 还是 claude)。宿主已在 `state.host`(claude-code/codex-cli/gemini-cli · audit 正文也有)· 本版落进台账列 + archive emit 采写数据 + audit frontmatter(供 harvest 按宿主分析)。

### 改动
- **ship1 archive emit `ledger_timing` 加 `host`**(= state.host)· 与时长/邮箱同束 · AI 照抄确定性。
- **audit frontmatter 加 `host:`**(与 v8.208 `user_email` 并列 · harvest 按宿主筛)。
- **PROCESS-LEDGER 模板加 `宿主` 列** + 口径说明(供年检**按宿主对比流程质量** —— external 采纳率 / 过场率 / AI 自主时长在 claude vs codex 的差异)。ship-stage §16 同步。

### 验证
- code(`_v8_ship` archive emit + audit frontmatter)+ 模板/§16 · `test_pause_mark_v8192` +1(host frontmatter)· pytest 818 passed。
## v8.210 · PROCESS-LEDGER schema 演进纪律「只在末尾加列」+ 幂等 ledger-migrate(治旧项目台账不升级)

> 用户:模板升级了但旧项目台账没升级 · 要不要迁移逻辑。查实:台账**无按列位解析的代码**(冲突解是行级 union · 年检 AI 读)→ schema 漂移不 crash;但 v8.208/209 把新列**插在中间/前面** → 新行(13 列)追加到旧表头(10 列)**错位**、年检读错列。

### 治本:改 schema 纪律 = **只在末尾加列**
- **重排 v8.208/209 新列到表最右**(各阶段耗时/用户邮箱/宿主)→ 旧数据行天然是新 schema 的**有效前缀**(新列它们为空 = 该 feature 早于该指标 · 诚实)· 迁移退化为**仅换表头一行**。零成本(新 schema 刚上 dev · 无真实项目已落)。
- **`state.py ledger-migrate --feature <path>`**(新 · 幂等):旧 schema → 升级表头 + 分隔行(canonical 表头单源自 `templates/process-ledger.md`)· **旧数据行逐字不动** · 已最新 no-op · 无台账 SKIP。ship-stage §16 append 前必跑。

### 为什么不写重映射迁移器
「只在末尾加列」让旧行永远是有效前缀 → 永不需要 cell 级重映射 · 任何未来加列都只是表头一行替换。

### 验证
- code(`state.py` 2 helper + 命令)+ 模板重排 + §16 · `test_ledger_migrate_v8210` +4 · pytest 822 passed。
## v8.211 · 宿主指令文件注入退役(治共享仓库污染非 teamwork 用户)· 关键信息收进 SKILL.md

> 实证 case(commercial-data-warehouse):bootstrap 往 AGENTS.md/CLAUDE.md 注入 teamwork 段 · 共享仓库同事一 commit · **不用 teamwork 的用户也被迫吃到**。用户拍板:去注入 · 关键信息写进 SKILL.md(加载 skill 即生效 · 只影响用 teamwork 的 session —— 这才是正确的作用边界)。

### 改动
- **`maintain_host_injection` 反转为清理模式**:不再写入;发现历史 `<!-- TEAMWORK_BEGIN: -->` 块 → **移除**(marker 外用户内容一字不动 · 清后全空连文件删 · 幂等)· emit `cleanup_removed` + note。
- **SKILL.md 新增 § Subagent 默认授权**(载体自宿主注入块迁入 · v8.135 授权长期化的新家)+ 196 行引用改指本段;PMO 定位 / worktree 纪律 SKILL 本就有 · 不再依赖注入。
- **退役死资产**:`tools/sync-drift.py` + `templates/host-instruction-injection.md` + `test_sync_drift.py`;scripts-policy / templates/README / SKILL 工具清单 / README 中英措辞同步。
- 本仓根 `CLAUDE.md`(纯注入块)用新逻辑自清 → 已删。

### 验证
- 冒烟:移除保用户内容 ✓ 纯注入删文件 ✓ 干净不动 ✓ 幂等 ✓ 绝不创建 ✓ · 注入测试重写为清理语义(+4)· pytest 814 passed。
## v8.212 · SKILL 文档导航补全(注入退役后 SKILL = 唯一入口 · 导航必须无死角)

> 用户:skill 里有目录索引吗?答:有(两类三层:skill 自身 § 文档导航 + 二级索引 STAGES/ROLES/STANDARDS/TEMPLATES;用户项目侧 § 文档清单/路由速查/结构索引 + teamwork-space)。但核对发现 § 文档导航**缺口真实**:docs/ 只列 CHANGELOG —— prepare(mode B 必经)/ feature-planning / conventions / teamwork-space-guide 全不在;STAGES.md(编排单源!)/ agents/README(subagent 协议)/ PRODUCT-OVERVIEW-INTEGRATION / hooks/ / agents profile 目录也不在。v8.211 注入退役后 SKILL 是唯一载体 · 导航更须全。

### 改动
- **§ 文档导航 15 行 → 24 行**:补 STAGES.md · PRODUCT-OVERVIEW-INTEGRATION · agents/README · docs/{prepare,feature-planning,conventions,teamwork-space-guide} · hooks/ · codex-agents/+claude-agents(external profile · 核实为活资产非死目录)· RETRO-LEDGER;TEMPLATES 行指向 templates/README 全清单;_v8_ship 描述更新(+ship-finalize/await-merge)。

### 验证
- doc-only · 相关套件通过。
## v8.213 · Claude hooks 全退役(teamwork 不需要 hooks)· bootstrap 转清理 + codex toml 保留

> 用户拍板:去掉 Claude hooks 相关逻辑。Review 佐证:hooks 是「宿主独有事件的自动触发层」· 与跨宿主原则相悖(scripts-policy 本就限制它只当薄壳);post-compact 恢复已由 state.json 断点续跑覆盖;codex hooks.json 更是当年 codex 账号 "cyber abuse" 警告的诱因之一(external-model-usage §抽出来源)—— 且 spec §110 明令删它 · bootstrap 却还在拷(spec-代码矛盾)。

### 改动(退役三件套:停部署 + 清存量 + 功能找新家)
- **删 `hooks/`**(hooks.json + post-compact/post-stop/post-subagent/session-restore.sh · 5 件)。
- **`maintain_host_hooks` 反转清理模式**:绝不部署 hooks;清历史部署(`.claude/hooks/` 5 个列名文件 + `.codex/hooks.json` · 🔴 **签名守卫**:内容含 teamwork 生态标记〔eamwork/PMO/dispatch_log/STATUS.md〕才删 · 用户同名 hook 保留)· 空目录顺手删 · 幂等。
- **codex agent toml 部署保留**(`.codex/agents/*.toml` = subagent profile · 活功能 · 与 hooks 无关)。
- **git-hooks/pre-push 不动**(发版 auto-bump · git hook 非 Claude hook)。
- SKILL 导航删 hooks/ 行 · scripts-policy hooks 段改退役声明 · 本仓 `.claude/hooks/` 自清(5 件全删含 PMO 签名的 post-subagent)。

### 验证
- 冒烟:签名删 ✓ 外来保留 ✓ toml 照部署 ✓ hooks.json 绝不部署 ✓ 幂等 ✓ · hooks 测试重写为退役语义 · pytest 813 passed。
## v8.214 · 注入段/hooks 清理挪出 skip_maintain 版本门(每次 bootstrap 都清 · 治 merge 回流旧块)

> 用户问:升级后会清注入段么?答:**会**(升级 → 版本 marker 不匹配 → maintain 跑 → 清理触发 · E2E 实证)。但验证同时抓到真实边缘:清理挂在 `skip_maintain` 版本门内 —— **同版本内二跑不清**。实害:并行分支上旧版 bootstrap 注入过的 AGENTS.md 被 `git merge` 带回 · 同版本内永不清 · 要等下次升级。

### 改动
- **`maintain_host_injection` + `maintain_host_hooks` 挪出 skip_maintain**(每次 bootstrap 都跑 · 同 v8.91 localconfig backfill「无论 skip 与否」先例)—— 清理幂等且轻(字符串查找)· merge 回流的旧注入块/hook 当次 session 即被兜住。chmod/gitignore 仍在版本门内(真·一次性维护)。

### 验证
- 冒烟:同版本 skip 下 merge 回流块被清 ✓(CLAUDE.md 只剩用户内容 · hook 同清)· pytest 813 passed。
## v8.215 · 智能分诊 v1:clarity 维度(明确度)→ 评审强度比例化 + 分诊证据先行

> 实证 case(admin i18n):「**大而明确**」的需求走全重流程 —— 车道把「大」和「不确定」绑死(477 key/7 页 → Feature → goal 3 冷审 + PL 质疑 + blueprint external 全上 · 但需求零歧义)。智能分诊方向(用户确认):输出从「车道标签」走向「维度向量」· 证据先行 · 本版落 v1。

### 改动
- **prepare-check emit 加 `triage_evidence` 证据槽**(estimated_files/cross_repo/new_deps/has_ui/mechanical/clarity)——🔴「看过再判」:30 秒侦察后填 · **空着不给判**;prepare.md §1.5 判定标准(explicit=明确方案或机械映射类;ambiguous=方向词;normal=默认)。
- **`init-feature --clarity`**(explicit/normal/ambiguous · 默认 normal)→ `state.clarity`。
- **explicit 消费两处**(gate 自动放行 · 留痕):① goal **PL 对抗质疑跳过**(无产品歧义可质疑)+ brief 推「冷审 3→1(QA 边界)」;② **blueprint external 跳过**(架构师单审)。🔴 **review 三视角不动**(明确 ≠ 不会写错 · 拦真主力 92/163)。
- 解耦原则:改动面大 → Feature **骨架**照走;不确定性低 → **评审轻档**。预期 explicit 类膜时间 −30~40%。

### 验证
- `test_clarity_v8215` +4(PL 跳/PL 照拦/blueprint 跳/review 不受影响)· pytest 817 passed。
## v8.216 · 评审配置动态化:拆掉 clarity 硬编码 · AI 按「角色价值判据」逐角色配 roster

> 用户裁决(对 v8.215 的修正):`--clarity` 固定消费(跳 PL+跳 external)还是太规则化 —— 该**动态决策**,不一定去 PL,也可能去 QA / ARCH。机制其实早已存在:`stage_review_roles`(所有 gate 本就按它放行)+ `change-review-roles`(审计留痕)· v8.215 错在绕过它另立硬规则。

### 改动
- **删两处硬编码 clarity gate**(PL challenge / blueprint external)—— gate 回归纯 roster 路由:角色不在 `stage_review_roles[stage]` → 自动放行(既有逻辑)。
- **prepare-check emit 加 `role_value_criteria`**(给 AI 的判断框架 · 非规则):逐角色问「这个视角对本 feature 能拦住什么」—— pl=价值前提可质疑?qa=边界/可测性风险?architect=架构决策/跨模块?external=多触发点/同模型盲区?**每角色一行理由(有值留 · 无值去)**· review stage 从严(建议 ≥2 视角 · <2 需强理由)。
- **`triage_evidence.consumption` 改**:凭证据逐 stage 逐角色配 roster(`change-review-roles --reason` · 审计)· `--clarity` **仅记录**进 state(台账/年检校准 · 不触发硬编码行为)。
- goal / blueprint brief 推送同步(冷审派谁 = 按 roster · 非按 clarity 一刀切)。

### 验证
- 测试重写:clarity 单独**不再**跳过任何 gate ✓ · roster 去角色 → gate 放行 ✓(×4)· pytest 817 passed。
## v8.217 · 智能分诊 v2:台账「分诊校准(预测→实际)」列 + 降级触发(持续分诊)

> 承 v8.215/216(维度化+动态 roster):v2 落学习回路的数据侧 —— 分诊判定要能被事后打分,判据才能随数据校准而非拍脑袋。

### 改动
- **archive emit 加 `triage_calibration` 束**:预测侧 = clarity + roster 调整摘要(审计已留);实际侧 = diff 文件数(git 确定性)+ goal 修订轮数(PRD 被打回?)+ review 轮数。
- **PROCESS-LEDGER 末尾加「分诊校准(预测→实际)」列**(末尾加列纪律 · ledger-migrate 单源自模板**自动升级**——本版测试实证:旧表 10 列 → 新 canonical 自动 14 列)· 年检算**分诊准确率**(explicit 判定却 PRD 常打回/review 高轮次 → 判据收紧)。
- **降级触发**(持续分诊 · 补反向):blueprint brief 推「TECH 复杂度=简单且零架构决策而 roster 仍重 → 提议降级(R5 → change-review-roles)」—— 升级触发已有(§2.1)· 分诊不是一次性的。

### 验证
- `_triage_calibration` 测试 +2 · migrate 测试改不写死列数(canonical 单源验证)· pytest 819 passed(预期)。
## v8.218 · 四段结构试点:review + dev stage 重构(目标/硬规则白名单/建议手段菜单/契约)

> 用户方向(第一性重审):保留 stage 划分 · 每 stage 给**目标**(QA=保障质量)+ 保**必须规则**(如异常必有 log)· 评审方式拆细为**建议** · 降低强制比例给模型发挥空间 —— 更好也更快。现状:12 stage 1666 行 · 🔴×139(全是红线 = 没有红线)。

### 改动(试点 2/12)
- **review-stage 235→77 行**:①目标(拦质量盲区 · 独立采样 92/163)②硬规则 8 条白名单(独立性/定级实证/verdict 门槛/裁决举证对称/范围锁定/轮次预算/external 协议/汇总不替代 · **每条带 why**)③手段菜单 8 项(AC 对照/diff 走查/边界审查/对抗复现/简洁性 counter-lens/测试质量抽查/截图核对/KNOWLEDGE 对照 · 各标「何时值得」· AI 自选 + Execution Plan 留痕)④契约(findings schema/fix-retry 命令链)。
- **dev-stage 149→63 行**:①目标(设计→可验证实现)②硬规则 7 条(DEV-RULES/worktree 路径/测试证据硬门/设计↔实际核对/全景编译契约/Bug 不重写根因/完工自查打钩)③手段菜单 6 项(🔴 **TDD 红绿从强制降为强烈建议默认** —— 测试证据仍是硬门 · 手段自由)④dev-complete 契约。
- 「怎么做」步骤教程整段删(目标+菜单+契约足够 · 步骤模型自推)。
- 安全网:v8.217 分诊校准回路对冲(放权后质量掉 → 台账显形 → 判据回收)。

### 验证
- 370→140 行 · pytest 819 passed(stage 散文与机器层零耦合实证)· 余 10 stage 待数据后推开。
## v8.219 · goal-stage 四段结构(试点 3/12)+ 修 v8.216 roster 硬编码残留

> 用户问 goal 是否需调整 → 判定:比其余更迫切 —— 除四段欠账(🔴×24/153 行 · 密度第二)外还有 **v8.216 活冲突**:§3 写死「Feature 派 3 个/敏捷 2 个」固定组合 · 而 Output Contract 又说「按 stage_review_roles」—— 同 spec 两套口径 · brief 已 roster 驱动 · 旧文字每 feature 都在误导(照章办事风险)。

### 改动
- **goal-stage 153→85 行**:①目标(拦意图偏差)②硬规则 8 条白名单(PRD 三命门/冷审隔离**不喂心路**〔派谁派几个=按 roster〕/早问门三闸〔事实类上抛=R5 违规〕/物化门禁/既有行为变更必升级/AC>10 反压/收敛软上限/auto 留痕 · 每条 why)③手段菜单(调研四源按需/各角色 mandate 表**按 roster 派**〔质疑六问指 roles 单源〕/双向质疑/验证模式)④契约(PRD/PRD-REVIEW schema + 重点 review 指引压缩为契约段)。
- **roster 冲突修复**:删「3 个/2 个」硬编码与 external opt-in 特例段 —— 组合全部交给 prepare 的 role_value_criteria + change-review-roles 审计。

### 验证
- 试点累计:review 235→77 · dev 149→63 · goal 153→85(537→225 行)· pytest 819 passed。
## v8.220 · flow_type 机器层收缩 6→3(用户拍板「直接到位」):Feature/Bug + preset 重量档

> 数据:170 audit 里敏捷+Micro 合计 11% —— 它们是「同一种工作的重量档」非独立工作形态 · 与维度化(clarity/roster)形成冗余平行系统。Bug(diagnose 先行 · 结构不同)与 Planning(不进状态机)保留;问题排查退到 triage mode A 深度版。

### 改动(机器层 · 存量零迁移)
- **`FLOW_BY_TYPE` 键收编**:`Feature`(=full)/ `Feature:lite`(原敏捷)/ `Feature:micro`(原 Micro)/ `Bug` · 三份转移图**原样保留**(行为等价)。
- **`resolve_flow_graph(flow_type, preset)` + `normalize_flow`**:legacy 名(敏捷需求/Micro)传入自动归一 → state 只存 `flow_type∈{Feature,Bug}` + `preset∈{full,lite,micro}`;存量 state.json 读到 legacy 值同样归一(零迁移)。
- **`init-feature --preset`** 新参;legacy choices 保留作别名(肌肉记忆/脚本兼容)。
- **角色矩阵 preset-aware**:`build_default_stage_review_roles(flow_type, preset)`(内部键映射旧名)。
- **ID 字母收敛 F/B**(Micro 的 M 退役 · 存量 M-id 不受影响);specs `allowed_flow_types` 收编(blueprint/blueprint_lite → Feature · 链图限定可达)。
- SKILL/README/prepare 加机器层收缩注记(6 类型表转为语言层预设视图 · 全表重写下版)。

### 验证
- pytest 819 passed(M→F 断言更新 ×3)· R2 闭集红线新形态 = 枚举 2 + preset 有界。
## v8.221 · prepare 适配 v8.220:配置面板新词汇(flow=Feature·preset)+ 分支前缀统一 + 链预览归一

> 实证 case(用户看 INFRA CI 缓存 prepare):配置确认还在说旧语言 —— `flow=Micro` · `ID=INFRA-M…`(M 系)· `branch=micro/…`。v8.220 机器层合并后 prepare 面是适配缺口。

### 改动
- **prepare-check emit 加对外词汇**:`flow_type_public`(Feature/Bug)+ `preset`(full/lite/micro)+ `config_line_hint`(⚙️ 配置行照抄:`flow=Feature · preset=micro` · 非 full 才标)。
- **链预览归一**:legacy flow 名 → 内部链键映射(engine `FLOW_STAGE_CHAIN` 键保留 · `Feature:lite/micro` 归一)· micro 链照旧 `dev→pm_acceptance→ship`。
- **分支前缀统一**:`agile/`、`micro/` 退役 —— Feature 全 preset 一律 `feature/`(Bug=`fix/`)· prepare.md 分支表改。
- **关键词表改 preset 语言**:「换 logo/改文案…」→ Feature·preset=micro;「加按钮/加字段…」→ Feature·preset=lite。
- 冒烟:legacy `--flow-type Micro` → public=Feature · preset=micro · **ID=F 系** · 链正确。

### 验证
- pytest 819 passed。
## v8.222 · 物化校验 flow 归一审计:10 处 legacy 比较死门复活(含 Micro initial=goal 真 bug)

> 用户点名:检查 python 脚本物化校验是否匹配 v8.220 合并。审计实锤 **10 处失配** —— state 只存 `Feature+preset` 后,所有 `flow_type == "敏捷需求"/"Micro"` 直接比较**静默失配**:最重的是 `DEFAULT_INITIAL_STAGE` 查表 → **preset=micro 错拿 initial=goal(应 dev)**,真 bug;其余 9 处是死门(needs-ui×lite 拦截失效 / goal 转移 lite 走错 blueprint / dev-next micro 不再跳 review / test-done micro 放行失效 / TC-PRD skip 失效 / agile 判定失效 / ship distill micro 键失效)。

### 修法(一处逻辑 · 十处生效)
- **`internal_flow_key(flow_type, preset)`**(state.py)+ **`_flow_key(state)`**(specs):public/legacy → 内部图表键(敏捷需求/Micro 键保留 · 存量 state 兼容)。
- init 的归一提前到 `initial_stage` 查表**之前**(原在其后 → UnboundLocal · 测试首轮 50 failed 抓出)· 查表改内部键。
- specs 8 位点比较统一走 `_flow_key` · ship distill micro 判定补 preset 分支。

### 验证
- `test_flow_merge_v8222` +7(键映射 / micro initial=dev / 5 个死门复活断言)· pytest **826 passed**。
## v8.223 · blueprint_lite 并入 blueprint + lite preset 退役(preset 收为 full/micro)

> 用户两连问推到底:① blueprint_lite 还需要吗 —— 它与 blueprint **目标相同**(dev 前方案收敛)· 差异全是重量(评审组合=roster 已管 · verify-ac 分档=一行判断 · 文档深度=四段/模板已管)= 「stage 版的敏捷需求」;② 并入后 lite 链 = Feature 链的 **needs-ui=false 剖面**(一条冗余链)→ lite preset 整体退役。micro 保留(跳 review/test 是真结构差)。

### 改动(新路收口 · 存量三保留)
- **`FEATURE_PRESETS = (full, micro)`** · `LEGACY_FLOW_ALIASES:敏捷需求 → Feature·full`(轻量由动态 roster + clarity 承担)· `--preset` choices 同步。
- **存量兼容三保留**(in-flight 不断链):AGILE_FLOW 图原样(`resolve_flow_graph` 对 state.preset=lite 仍解析)· `internal_flow_key/_flow_key` 的 lite→敏捷需求 映射保留 · `BLUEPRINT_LITE_SPEC` 保持注册(标 DEPRECATED · 存量走完后删)。
- blueprint-lite-stage.md 挂 deprecated 横幅;prepare 关键词行(加按钮类 → Feature · 轻量由 roster/clarity)+ SKILL/README 注记同步。

### 验证
- pytest 826 passed(存量 lite 兼容断言全绿)。
## v8.224 · skill 全文件描述审计:A 类 7 项「变假话」清零 + FLOWS 重写薄壳(102→40)

> 用户:整体看 skill 各文件描述的冗余与不合理。盘点实锤:合并三连(v8.220-223)后 **7 项过时描述**在教旧规则 + 流程类型**三处平行描述**(FLOWS×SKILL×prepare)。另发现元教训:cite(v8.199)/顶栏(v8.206)/hooks(v8.213)各漏扫一个目录 —— 退役清扫必须覆盖全部内容目录。

### 改动
- **FLOWS.md 重写 102→40 行**:闭集表 = Feature(full/micro)/Bug/Planning/排查 · telos 一行化 · 判定权威显式指 prepare(结束三处平行:prepare=权威 · SKILL=视图 · FLOWS=薄壳)。
- **SKILL 类型段真重写**(吃掉 v8.220/223 两层过渡注记):新 5 行表 + 授权暂停点表(删敏捷需求行 · Micro→Feature·micro)+ DB 变更措辞。
- **STAGES.md** flow 列更新 + blueprint_lite 标 DEPRECATED;**roles/pmo.md** 六闭集行改;**conventions.md §1** ID 表(敏捷/M 行标 legacy · 存量 M-id 有效不迁)。
- **漏网残留清零**:cite 仪式 ×4(prepare + 三个 report 模板)· dev 顶栏 ×1(scripts-policy)· hooks ×1(prepare)。

### 验证
- pytest 826 passed。
## v8.225 · 模型档位判断框架(任务性质→档)+ 并行姿态翻转(鼓励 subagent/teammate)

> 用户两提案合一:① skill 层加模型建议(规划/方案/关键评审用高档 · 代码用执行档 · 测试验证用轻档 · GPT 同理);② 鼓励多用 subagent/teammate 提并行度。形态守 v8.194/216 判例:**「任务性质 → 档位」判断框架 · 非「stage → 型号」映射**(型号随代际漂移 · 跨宿主不通 · 逐 stage 映射是规则不是判断)。

### 改动
- **agents/README §一 重写为档位表**:深度档(创造+深度判断:规划/TECH/架构 CR/PRD/诊断/关键裁决)· 执行档(实现 · 主对话继承即是)· 验证档(校验/枚举:TC 对照/测试执行/机械外化)—— 型号列仅当前映射示例(Claude: Fable/Opus↔会话↔Sonnet/Haiku · GPT 对应档)+ 每档标**典型并行形态**。
- **三条硬边界**:架构 CR 与关键裁决不降档;**评审独立性优先于档位**(两个轻模型冷审 > 一个强模型热审);主对话模型 = 用户主权(AI 只建议)。
- **并行姿态翻转**(SKILL subagent 条目):从「⚠️ 非默认 · 不过度使用」改为「**默认考虑:每 stage 开工先问哪些子任务可并行**」(冷审 N 路同发/多模块 teammate/调研 fan-out)· 护栏原样(边界清晰且够大/worktree 路径/**流转与整合永归主对话**)。
- **prepare §1.4**:关键 Feature 建议主对话深度档 + prepare 时标出可并行子任务。台账 host+model(v8.208/209)= 档位建议的年检校准数据源。

### 验证
- doc-only · pytest 826 passed。
## v8.226 · external-ingest:ultra review 摄入为第三视角(session 主路径)+ ultracode workflow 姿态

> 让渡战略第一刀(评审执行让给更强的原生能力):`/code-review ultra` = 产品化多智能体独立评审(用户触发/计费/out-of-session)—— 接入为 external 第三视角的 **opt-in 增强源**。🔴 用户修正关键时序:**评审时 MR 多未创建** → 主路径 = **session 摄入**(用户在本 session 跑 ultra · findings 已在对话 · AI 转录)· paste 兜底(标 manual 降级)· pr-comments 留作 MR 窗口期增强(拉取即机器证据)。

### 改动
- **`state.py external-ingest --from session|paste|pr-comments [--label ultra]`**:归一化落盘 `external-cross-review/review-<label>.md`(frontmatter `review_via: ultra-ingest` + origin + 时间)· 过短拒收 · 🔴 **分层**:命令只做转录归一(确定性)· **裁决永远归 PMO**(emit 明示走 质疑→确认→裁决 管线 · ultra 也会 false positive · 盲采仍是反模式)。
- **门禁两处**:yolo 冷视角判定认 `review_via ∈ {subagent, ultra-ingest}`;异质文件名白名单校验对 ultra-ingest **豁免**(它非单一模型产物 · 独立性来自 out-of-session pipeline)。
- **review 手段菜单 +1 行**(关键/高风险改动 · 用户在场愿投入时建议);**agents/README 并行姿态 +1 句**:ultracode 开启的 session 冷审/验证 fan-out 优先用 Workflow(schema 化 findings · 契约不变 · 裁决归主对话)。
- 战略注记:review_engine 适配层(原 v8.227)确认**不建**(2-3 路负载下负 ROI · ultracode 下 PMO 手写 workflow 即可);workflow 改投**年检工具化**(harvest/spec 审计 50-200 路 fan-out 才是甜区)。

### 验证
- `test_external_ingest_v8226` +5(session 归一/paste 降级标/过短拒/缺 URL 拒/门禁认)· pytest 831 passed。
## v8.227 · README-EN 类型体系补改(v8.224 只改了中文侧的残留)

> backlog #2:EN「6 Flow Types」表 + R2 红线行 + 快捷启动例仍是六类旧口径(变假话残留 · v8.224 描述审计只扫了中文面)。

### 改动
- EN 类型表重写(Feature·full / Feature·micro / Bug / Planning / Investigation + 机器层收缩说明)· R2 行改 `{Feature,Bug}+preset` · 启动示例注释改 preset 语言。

### 验证
- doc-only · 词汇残留复扫清零。
## v8.228 · 管辖判据 + 直答通道:管辖外输入(尤其现状问答)零仪式直答

> 用户指令:输入不属 teamwork 该管的(非 功能/缺陷/排查/规划)—— 尤其**问现状类** —— 直接回答,不走流程。现状病:5-mode 把一切输入往流程装,连「X 怎么实现的」都套 audit_line/mode 宣告/状态行(仪式噪音)。

### 改动
- **SKILL Triage 新增「🔴 管辖判据 · 直答通道」**(分诊之前先过):不属四类工作 → 直答 · **零 teamwork 输出协议**(无 audit_line/mode 宣告/状态行/recap/流程推销);现状/知识问答明确归此;答后追问升级成工作才进分诊 · **不主动推销流程**;拿不准按直答(误加仪式代价 > 误省)。
- **audit_line 作用域**:「首条响应必含」→「承接 teamwork 工作时必含 · 直答免」。
- **状态行作用域**:「有活动 feature/流程时」才输出 · 管辖外轮次免。
- roles/pmo.md 同步一行。

### 验证
- doc-only · pytest 831 passed。
## v8.229 · 冷审 dispatch 档位推进 brief(治「goal 冷审全跑主对话模型」)

> 用户观察:goal 冷审实际都是主对话模型。根因 = v8.170 老病复发:档位框架(v8.225)躺 agents/README(被动)· goal/review brief 没推(主动)—— dispatch 不传 model 默认继承会话模型 · **常费而不自知**。

### 改动
- **goal brief +1 行**:dispatch 按角色性质分档 —— QA 冷审(可测性/边界 = 校验型)→ **验证档**(如 sonnet);**Architect / PL 不降档**(可行+简洁判断 · 价值前提对抗 = 深度判断)—— 三路冷审不该一刀切。
- **review brief +1 行**:QA code review 可派验证档;架构 CR 不降档(硬边界)。

### 验证
- brief 冒烟 ✓ · pytest 831 passed。
## v8.230 · dispatch 档位上移 SKILL 全局规则(撤 goal/review brief 散点 · 单源)

> 用户裁定:档位选择是**横切关注点**(任何 stage 任何 dispatch 适用)· 该放 SKILL.md 全局 · 不该散在 goal brief —— v8.229 的两处 brief 行是三处重复(agents/README 表 + 两 brief)· 必漂。

### 改动
- **SKILL subagent/teammate 条目追加「🎚️ dispatch 档位(全局规则)」**:不传 model = 继承会话模型(常费不自知)→ 派前按任务性质定档(校验/枚举型 → 验证档;判断/创造型 → 不降档)· 档位表与硬边界**单源 = agents/README §一**。
- **撤 v8.229 两处 brief 行**(goal/review)—— PMO 任何 dispatch 都在 SKILL 语境下 · 全局条目即消费点 · brief 保持极简。

### 验证
- brief 撤净冒烟 ✓ · pytest 831 passed。
## v8.231 · dispatch 模型分布观测(档位建议采纳率的数据闭环最后一块)

> 用户观察:很多时候还在用主模型跑 subagent。诊断三因:①到达率(v8.225-230 规则太新 · 副本未同步)②软约束惯性 ③**观测盲区 —— per-dispatch 的 model 无任何记录 · 「分档建议是否被采纳」无数据可验**。本版补 ③。

### 改动
- **`_dispatch_model_distribution(feature_dir)`**:从 `dispatch_log/*.md` 宽松解析每文件首个 `model:` 行 · 汇总分布;**未写 model 计 `unspecified(继承会话)`** —— 正是要观测的「没分档」信号;无 dispatch_log → {}(覆盖面 = 文件化 dispatch · 可审计路径)。
- **接进 `triage_calibration` 束**(archive emit)+ **audit 记录实际数据段** +1 行 + 台账「分诊校准」口径说明更新 —— 年检直接看 `unspecified` 占比 = 档位建议采纳率。

### 验证
- 冒烟(sonnet/opus/unspecified 分布 · INDEX 跳过 · 无目录空)· 测试 +2 · pytest 833 passed。
## v8.232 · ship1 终点输出物化为 user_card(URL 置顶 · 工具生成 · AI 原样贴)

> 实证 case(SVC-PLATFORM offer-goals):ship1 收尾 AI 自由发挥写「本轮总结」长段 · **MR URL 埋进段落** · 用户被迫问「你把 mr 地址发出来啊」。spec 旧模板也把 URL 放最底部「决策参考」行。暂停点内容要**易消费**:第一屏第一信息 = 用户要点的那个链接。

### 改动
- **push emit 加 `user_card`**(工具确定性生成 · 🔴 AI **原样贴给用户 · 禁自写总结段**):标题行 → **🔗 MR URL 独立行置顶** → 分支/包含/监控/异常口令各一行;交付摘要要加 → 卡片之后 ≤3 行。next_action_brief 首条指令 = 贴卡片。
- **ship-stage §5 模板重写**:旧「四选项 + URL 沉底」→ 卡片契约 + await-merge 语义收敛(用户无需回编号 —— **合并动作本身就是确认**;仅「冲突/撤回」两个异常口令需要回话)。
- 卡片构造容错(无 feature 路径/git 失败 → 占位符 · 不阻塞 push)。

### 验证
- `user_card` URL 置顶断言 +1 · pytest 834 passed。
## v8.233 · ship1 输出格式修正:卡片 + 交付总结**两段定序都必含**(撤 v8.232「禁总结」过度限制)

> 用户修正 v8.232 的理解偏差:不是让工具替掉总结 —— **总结是要的**(case 里那段链路/决策/解锁的内容本身有价值),要规范的是**格式结构**:URL 不能埋在总结里 · 两者都必含 · 各归其位。

### 改动
- **ship-stage §5 输出规范改为两段定序**:① MR 卡片(URL 置顶独立行 · 可直接用 emit `user_card` · 分支/URL 不抄错)② **📦 交付总结(必含 · AI 照实写 · 三槽结构:链路一行 / 关键决策与遗留 / 合并后解锁)**。🔴 **次序不可倒**(总结在前 = URL 埋段落 · 实证 case)。
- push emit 指令同步(「禁自写总结段」→「先卡片后总结 · 三槽」)· 测试断言同步。

### 验证
- pytest 834 passed。
## v8.234 · await-merge 全模式必跑:「停 ≠ 停监控」(治 auto 停在 pushed 无人收尾)

> 实证 case(KA-PAGES):auto_mode feature 停在 ship.pushed · 用户 5 分钟后合了 MR · **没人收尾**(worktree/过程目录残留)· 该 session 的 AI 还解释成「auto 不监控 MR · 只有 yolo 才会」。两层缺口:① await-merge 指令只活在 ship-stage 文档 · **push emit(AI 实际照做的那份)没提**;② SKILL「auto 也必停此暂停点」被读成「session 到此结束」。

### 改动
- **push emit 补必跑步**:贴完卡片+总结后**立即跑 `await-merge`** —— 🔴 **所有模式(普通/auto/yolo)都跑**:「停」= 不能替用户点合并 · **不是停止监控**;MERGED → 自动 ship-finalize;手动 ship-finalize 降为 await-merge 不可用时的兜底。
- **SKILL auto_mode 表 ship1 行**:`stop` → `stop + 监控`(语义澄清 + 实证注)。
- **ship-stage §5** auto 措辞同步。

### 验证
- emit 断言 +2(await-merge / 不是停止监控)· pytest 834 passed。

## v8.235 · dispatch 声明制:派 subagent/teammate/workflow 必声明「model + 一句为什么」+ 并行鼓励强化

> 用户指令:使用 subagent/teammate/workflow 时需给出匹配的模型并**说明为什么**;鼓励多用以提升并行度和效率。承 v8.230(全局档位规则)/v8.231(unspecified 观测)—— 规则有了、观测有了 · 缺**声明动作**逼出有意识选择。

### 改动
- **SKILL 全局条目升级为声明制**:每次派发必声明「model + 一句为什么」(主对话派发语句 / dispatch 文件 Meta / workflow `agent()` 旁注释)· 例 `model: sonnet(TC 对照 = 校验型 · 验证档够用)` · **不声明 = 默认继承没思考**(台账 unspecified 就在数这个)。⚡ 鼓励并行再强化:**能并行的不串行** · 并行度是效率的第一杠杆(ultracode 时 workflow 优先)。
- **agents/README**:并行姿态段声明制同步;文件化 dispatch **Meta 字段加 `model + model_reason`**。

### 验证
- doc-only · pytest 834 passed。
## v8.236 · dev brief 补并行提示(开工先问哪些模块可并行)+ 修 stale 措辞

> 用户问:dev brief 有提醒用 subagent/teammate/workflow 么?查实:**没有** —— 并行规则全在 SKILL 全局/agents/README(被动),而 dev 恰是并行红利最大的 stage(多端/多模块实现);顺带抓到 brief「详细步骤 6 步 + 注意事项 5 条」是 v8.218 四段重构前的 stale 旧话。

### 改动
- **dev brief +1 行**(stage 专属手段提示 · 指向全局不复制 · 不违 v8.230 单源判例):🧩 开工先问「哪些模块可并行」→ 多端/多模块各派 subagent/teammate(**ultracode → workflow 优先**)· 派发按 SKILL 🎚️ **声明 model + why** · 契约层/集成点留主对话 · 子 agent 只写 worktree 内路径。
- 必读行修正为四段结构措辞(6 步旧话清除)。

### 验证
- brief 冒烟 ✓ · pytest 834 passed。
## v8.237 · 升级检测缓存 TTL 24h → 8h(治缓存掩新版)

> 实证 case:发版节奏快(12 小时内 dev 推进 8 个 minor)· bootstrap 升级检测的 24h TTL 缓存命中 → 报 `up_to_date(from_cache)` · 实际已落后。用户拍板:TTL 改 8 小时。

### 改动
- `SKILL_UPDATE_CHECK_TTL_HOURS = 24 → 8`(失效条件不变:超 TTL / 无缓存 / 时钟回拨 / 本地版本或 channel 变 / `TEAMWORK_FORCE_UPDATE_CHECK=1` 强制实查)· 注释与测试措辞同步(测试逻辑用常量 · 零断言改)。

### 验证
- pytest 834 passed。
## v8.238 · stage-start emit 附派发档位提醒(治「冷审全跑主对话模型 · 零声明」)

> 实证 case(KA-PAGES goal):三路冷审 subagent 全跑 Fable 5 · 零声明 —— QA(校验型)本应验证档。暴露 v8.230 裁定的盲区:**SKILL 全局规则在 session 早期读一次 · 派发那一刻 AI 实际消费的是 stage-start emit/brief** · goal 冷审恰是最高频派发点 · 那里什么都不提醒。

### 改动(不回退 v8.230 · 不复制规则回各 brief)
- **engine 单源常量 `DISPATCH_TIER_REMINDER`** 接进**每个 stage-start 成功 emit**(`dispatch_tier_reminder` 字段):一行提醒「派发声明 model+why · 校验型→验证档 · 判断型→不降档 · 未声明=unspecified」+ 指针 SKILL/agents README —— **工具生成 · 所有 stage 消费时点覆盖 · 文本单源一处**。

### 验证
- 常量+接线断言 +1 · pytest 835 passed。
## v8.239 · WS 规划两道深度门:调研深度契约(ws-lint 抓占位)+ 拆解讨论暂停点(R5 必经)

> 用户观察:WS 规划调研浅 · 拆出的需求过散 —— **预期 WS 一定是「代码现状 × 用户深度讨论」的产物**。两病根:① Step 1 调研是软指令无深度证据契约;② 拆解本身没有用户讨论暂停点(用户只在收尾见成品 · 无法在拆解方向上纠偏)。

### 改动
- **调研深度契约**(Step 1 + 模板 + 机器抓):`features[].current_state` **必附来源文件路径**(浅调研拆出的 WS 必散);🔴 **ws-lint 新校验**:current_state **缺失**(条数 < features 数)或**仍是模板占位**(`<...>`/`...`)→ NONCONFORMANT(调研浅硬信号)。
- **Step 5.7 拆解讨论暂停点(R5 · 必经)**:拆解草案落 WS 文档**之前** emit 讨论稿(候选 BL + 每条边界理由 + current_state 摘要〔出自哪些实读文件〕+ 波次 + **粒度自检**)→ 用户就地讨论收敛(合并/砍/改边界)· 不落成品后返工;auto/yolo 按推荐 + WARN 留痕(同全景确认模式)。
- **粒度反压**(镜像 goal AC>10):BL > 8 或存在「无独立交付价值/纯机械半天活」的 BL → 草案必须给「为什么不合并」。
- planning-check checklist WS item 同步两道门。

### 验证
- ws-lint 深度校验测试 +3(占位抓/缺失抓/grounded 放行)· fixture 补 grounded current_state · pytest 838 passed。
## v8.240 · ship1 push user_card 防截断三重物化(治「AI 过滤 emit 丢卡片 · 用户看不到 MR 链接」)

> 实证 case(KA-PAGES-F260714041628 · aon-main):主对话习惯用 python key-filter 读 state.py emit,`ship-phase --action push` 的 `user_card` 字段被过滤丢弃 → AI 手写卡片把 MR URL 包进 markdown 加粗 → 用户「没看到链接」。v8.233 的纯 prose 防线(「先贴 user_card」)挡得住 head 截断、挡不住 key-filter —— 按「可枚举进脚本」物化。

### 改动
- **`_v8_ship.py` push emit 三重防御**:① `pmo_must_read` 置字段首位 + `user_card` 第二(survive head 截断);② 卡片同步**落盘** `<feature_dir>/SHIP-USER-CARD.md`(绝对路径 · untracked 随 worktree 消亡 · stdout 丢失时 `cat` 原样贴)+ emit `user_card_file`;③ `hint` 字段冗余同一指令(key-filter 惯选 verdict/hint —— 实证 case 的过滤器恰好选了 hint)。
- **ship-stage.md §5**:卡片段措辞升级为「原样用 + 禁 key-filter/截断 + 落盘兜底路径」。

### 验证
- 新增 `test_push_emit_user_card_materialized_v8240`(位置/落盘/hint/幂等 4 断言)· test_ship_safety 16 passed。
## v8.240 · 拆解边界判据:交付内聚>子项目边界 + 含金量对照 + id 不重排纪律

> 来源 case(JCB 卡片 WS · v8.239 门生效前的存量拆解):7 件逐 feature 代码审计发现 4 件薄(S2/S3/S6 薄配套 · S7 半运营 · 「其余四件加起来的代码量可能不如 S5 一件」),但 v8.239 粒度反压零触发(7<8 · 每件流程上都「站得住」);用户亲自解禁「feature 也可以跨子项目」才合成 5;且落盘后合并触发**第三次编号重排 = 整卷重写防漏引用**。三个判据缺口,不加新暂停点。

### 改动(Step 5.7 判据升级 + 模板 + checklist 同步)
- **边界判据**:主判据 = **交付内聚**,**feature 可跨子项目**(`target` 只是 ROADMAP 归属 · 「代码在不同子项目」不是拆分理由,评审 blast radius 才是);**薄承接件默认并入宿主件**(只承接另一件产物/同 surface 严格串行/协调点可内化为里程碑),保持独立须给硬理由之一:外部依赖 gate / 交付节奏不同 / blast radius / 管辖边界(四类全部萃取自该 case 的真实裁决:S1+S2 并 · S6 gate 独 · S7 节奏独 · S3 blast radius 独)。
- **含金量对照**:讨论稿每条 BL 标「真新增工程量 vs 薄配套(承接/枚举/配置级)」——**含金量悬殊 = 强合并信号**(反压 BL>8 抓不住 7 件 4 薄这类)。
- **id 纪律**:草案期编号随便改;**落盘后合并/砍件不重排幸存 id**——被并件留一行遗迹(`S2 → 已并入 S1`)· 缺号不补。
- 模板顺手修:`flow_type` 注释还是 v8.222 合并前旧词表(feature/agile/bug/micro)→ 现闭集(Feature/Bug · micro 是 preset)。

### 验证
- 文档+模板+checklist 消费点三处同步 · ws-lint 不消费 target/flow_type 注释(纯文案安全)· pytest 839 passed。
## v8.241 · 全库文档审计清扫:83 findings 修复 + 退役词表回归网 + 两处工具侧治本

> 用户令「整体 review 各文档找不合理/冲突/冗余」→ 5 路评审 subagent 按文档簇并行(SKILL/stages/docs/templates+roles/对外三件)+ 主对话词表扫描,共 **83 处经双边原文验证的 findings**。病灶高度聚簇:五次大改版(v8.204 外审默认反转 / v8.211 注入退役 / v8.219 四段化 / v8.220-223 流程收缩 / v8.233-234 ship 终点)各留扫尾债。机器契约层(FLOWS↔常量 · frontmatter↔物化校验 · 台账 schema)五路核验零冲突。

### 工具侧治本(2)
- **REVIEW-arch/REVIEW-qa roster 化**:静态必查与动态 roster(v8.216)互斥(角色可被合法移出 roster 而产物仍硬查)→ 新 `review_role_artifacts` evidence check 按 `stage_review_roles.review` 查(移出不查 · legacy 无 roster 全查不放松存量)。
- **close-unmerged 任意 stage 可走**:pm_acceptance rejected 的「放弃 Feature」选项此前是死路(emit 给的命令必被 `_require_ship_stage` 拒)→ 放宽该 action(幂等门仍由 phase 检查把守)。

### 文档修复(四大簇 + Tier1)
- **照抄即错**:规划层 auto 留痕 add-concern 不可执行(规划无状态机 · 全景确认与 v8.239 Step 5.7 同病)→ 改 WS frontmatter/背景节留痕;main-sync 示例与机器 hint 补 required `--strategy`;prepare §5 示例补 `--clarity/--preset/--bl` 落点;config_line_hint 机器残留 `lite` 清除;bug-report 模板补 `symptom/root_cause/fix_summary`(机器 gate 校验它们非空);config.md 外审开关说明与实例相反(「删此项恢复异质」在新语义下效果相反)重写。
- **v8.204 外审默认反转簇(7)**:blueprint §6 整段旧教义(无条件异质必跑)→ roster 三层条件式;blueprint Architect「主对话不走 subagent」→ 隔离冷审(对齐 goal 实证);roles/external-reviewer 补三层现实;standards/external-model-usage「默认 false + WARN 催恢复」重写;README-EN/ prepare/ ship 措辞。
- **v8.220-223 流程收缩簇(~20)**:SKILL §2.2 quick-ref 重写为 preset 词表 · 两处 F/B/M→F/B · micro「≤5 文件」两口径删阈值(FLOWS 同步);prepare §2.2 整节重写(敏捷需求准入档退役 · micro 白名单准入单源)· 编号断裂(1.4/1.5×2→1.6/1.7)· lite/M 字残留;conventions M 示例与 §8 补 legacy 标;roadmap 模板 v7 阶段名→v8 stage 名;README CN 6 行流程表→5 行闭集(与 EN 对齐)。
- **README 双语过时宣称(8)**:Ship 节还在描述 v8.145 已删的旧两-MR 链路 → 重写为 user_card+await-merge 两段现实;PENDING 外置 / TROUBLESHOOTING 收敛 project-specs / KNOWLEDGE 四类 / 执行手册废弃补 workstream/ / hooks 清理措辞 / EN sitemap→panorama 误译。
- **断链引用(~12)**:四段化后 ui-design→dev §3/§3.5、roles/pm→goal §4/§1;重编号后 conventions→ship-stage §坑1/§8、→feature-planning Step 5、feature-planning 自引 Step 5、checklist spec Step 8→9;三报告模板→roles 不存在小节;SKILL 自指不存在的 silent execution 节。
- **冗余与小项**:agents/README **保留**(§二/§三 dispatch 协议是 subagent 独立载体 · codex-agents toml 运行时指读)但 §一 姿态/声明制散文去重(指回 SKILL 单源 · 档位表+三硬边界仍单源本文件);SKILL 快速开始 ship 旧剧本→await-merge · auto 表删 browser_e2e 幽灵行 + 补 diagnose 行(skip+WARN)· 暂停点清单补 panorama_sync L2 · ≈40 命令→≈55 + B 类补 await-merge · 物化覆盖率两口径统一 · 状态行 2/3 行统一;pm-acceptance raw-write→jump-to-stage;tc.md TC-REVIEW 死段删;bug-report classification 零消费机制删;9 模板补「位置:」行;project-specs 清单三文档归一 conventions §13。

### 制度化(治「每次大改各留扫尾债」)
- **退役词表回归网**:新 `test_retired_vocab_sweep.py` —— 退役词(敏捷需求/Micro/blueprint_lite/teamwork_version/Goal-Plan)只许出现在带 legacy 标注的当句 · 裸残留 = pre-push 红。

### 验证
- 新测试 +7(roster 化 4 + close-unmerged 2 + 词表网 1)· pytest **846 passed**。
## v8.242 · 变更确认类暂停点必自带变更点明细(对象|变更|用途 · 治「概括 + 指针」逼用户追问)

> 来源 case:blueprint DB schema 确认点只 emit 四条分类概括(「增加诊断投影与快照序号」「增加日志序列、过期 tombstone、mutation 幂等、Tester durable queue 辅助表」)+ TECH.md 指针 → 用户被迫追问「DB 变更方案是什么」· 追问后 AI 才给出该有的 对象|变更|用途 明细表 + 迁移策略。**病根在 §7.5 模板本身没有变更点槽位**(从「请确认」直跳选项 · 决策参考=文件指针)—— case 里 AI 忠实执行模板仍失败 · 是模板的 bug。与 v8.232 ship1 同类:暂停点内容不可消费。

### 改动(消费点三件套)
- **blueprint-stage.md §7.5 模板重写**:选项之前必给 ①**变更点明细**(🔴 对象级每条一行:对象|变更|用途 —— 表/字段/索引/约束/新表核心列;分类概括 / 文件指针**不算**变更点)② **关键迁移策略**(≤6 行:有损与否 / 唯一约束前历史冲突预检 / 历史回填口径 / down migration / 清理周期);📚 指针降为深读补充 · 不替代明细。范式即 case 追问后的第二回。
- **SKILL R5(b) 新红线(全局)**:**方案/变更确认类暂停点必自带变更点清单** —— 情境一句 + 概括 + 指针不算 · 用户被迫追问「方案是什么」= 暂停点白跑一轮 · 决策材料在暂停点内自含。
- **机器消费点**:blueprint stage-start brief 的 §7.5 行机械附带「必自带变更点明细表」提醒(v8.238 消费时刻原则)。

### 验证
- pytest 846 passed(doc + brief 文案 · 无行为变更)。
## v8.243 · goal 冷审 3→2 路并行:PL 对抗质疑 + 覆盖方向制外审(QA/ARCH 视角并入 + AI 自主方向)

> 用户拍板:PRD 评审从 3 个(QA/Architect/PL)改为**两路并行**——保留 PL + 外审;外审至少覆盖**可实现、可验证**等,把 QA 和架构师考虑的点并进去,同时要有 **AI 自己的评审角度**。此前「角色→覆盖方向 coverage 化」讨论在 goal 的落刀:少一路冷审的编排/整合开销 · 覆盖不减(方向制)+ 增(AI 自主方向是三角色制没有的)。动态 roster 机制不动 —— 改的是默认值 + 外审内容契约,复杂 feature 仍可 `change-review-roles` 加回独立 qa/architect。

### 改动
- **默认 roster**:`("Feature","goal") = ["pl", "external"]`(engine · 史注保留 v8.155 三角色防鼓掌与 v8.149 去 external 脉络)。
- **外审内容契约(覆盖方向制)**:🔴 必覆盖 **可实现**(技术可行 / 架构影响 / **简洁性 counter-lens**——唯一防过度设计 lens 随方向保留)· **可验证**(AC 可测试性 / 边界场景 / 空值异常分支)+ 🔴 **AI 自主方向 ≥1**(按 feature 特性自选:安全/性能/数据一致性/兼容/运维…);每方向给 finding 或「查过无发现」;external 段记 `coverage: [...]`。默认同模型 subagent 冷审 · 异质 opt-in 不变(localconfig false 时改跑 external-review 落 external-cross-review/)。
- **物化门 `external_coverage_present`**(goal-complete):roster 含 external 时 PRD-REVIEW 必含 coverage 申报(对称 pl_challenge_present · 防外审退化成一段泛谈);roster 无 external 自动放行。
- **两路并行**:⚡ 同发两个隔离 subagent · 互不喂对方产出(brief/stage 文档明示)。
- 消费点同步:goal brief(specs)· goal-stage ③ mandate 表(qa/architect 行改「默认并入外审覆盖方向 · roster 加回时独立跑」)· templates/prd.md PRD-REVIEW schema(reviewers/verdicts 示例 + coverage 字段)· roles/qa+architect 席位行 · role_value_criteria(qa/arch 判强才加回 · external goal 默认在)。
- 顺带修:roles/architect.md 还宣称「blueprint/review 评审默认主对话」——与 v8.241 blueprint 隔离冷审矛盾(审计漏网)· 统一为隔离冷审。

### 验证
- 新测试 +6(默认 roster 两条 + coverage 门四态)· 旧断言 2 处按新默认更新 · pytest **852 passed**。
## v8.244 · blueprint/review 冷审 3→2 路并行:Architect 主审 + 覆盖方向制外审(review 从严清单)

> 用户拍板:tech review 与代码 review 同 goal(v8.243)改两路并行 · 审核内容不变提效率。沿用 v8.243 分界线:**判断型视角保持独立角色 · 枚举型视角方向化并入外审** —— blueprint/review 的判断型主线是 Architect(简洁性 counter-lens / 实现↔设计一致性),QA 视角(可测试 / 测试真实性)方向化。三点增强(评审时建议 · 用户 ok):①review 从严体现在必覆盖清单比 blueprint 重一档 ②AI 自主方向给 stage 特定候选菜单 ③coverage 物化门延伸成三 stage 统一闭环。

### 改动
- **默认 roster**:`blueprint/review(Feature)+ review(Bug)` 均 → `["architect", "external"]`(legacy 敏捷行不动);Architect 主审产物契约不变(TECH-REVIEW / REVIEW-arch)· REVIEW-qa 为 roster 加回项(v8.241 roster-aware 校验已铺路 · 机器零新改)。
- **外审内容契约(分 stage 从严)**:blueprint 必覆盖 **可测试**(TC 质量/测试策略 · AC↔TC 机械绑定归 verify-ac)· **方案盲区**(依赖/影响面/迁移风险)+ AI 自主方向 ≥1(候选:数据一致性/迁移风险/性能/安全边界);review 必覆盖 **测试真实性与覆盖**(测试真跑/覆盖真行为/边界回归)· **代码质量盲区**(错误处理/日志/并发)+ AI 自主方向 ≥1(候选:并发/资源泄漏/脱敏/兼容)。每方向 finding 或「查过无发现」。
- **物化门 `cross_review_coverage`**(blueprint-complete + review-complete):roster 含 external 时 `external-cross-review/*.md` 必含 `coverage: [...]` 申报 —— 与 goal 的 `external_coverage_present` 构成三 stage 统一「申报-物化-台账观测」闭环 · hint 按 stage 给对应从严清单。
- **消费点同步**:两 brief(specs)· blueprint-stage §5(QA 独立 TC Review 改 roster 加回项)/§6(外审契约)· review-stage 硬规则 7 + Output Contract 示例 · prepare Q3(external 已默认在 → 判据改升异质/加回 qa)· role_value_criteria(qa 三 stage 并入 · architect 注明 blueprint/review 主审席位保留)· roles/qa.md(三席位 generalize + TC 起草不受 roster 影响)· SKILL yolo 段(「三视角一个不少」→「roster 内全真跑一个不少」· 防削弱语义不变)。

### 验证
- 新测试 +8(三默认 roster + legacy 不动 + coverage 门四态含 stage 特定 hint)· 旧断言 1 处更新 · pytest **860 passed**。
## v8.245 · 排查升级暂停点:多候选逐一编号 + 斜杠并列即自由文本(治 ok 无从解析)

> 来源 case(问题排查 · codex 宿主):排查报告漂亮,收尾却 emit `⏸️ 请确认后续动作:Bugfix 流程 / 不处理代码(先修正 staging 配置)/ Feature 流程` —— 斜杠并列自由文本 · 无编号无 💡 推荐 → 用户回 `ok`(快捷词协议 = 选推荐项)无从解析 → AI 再问一轮 · 白耗两个来回。**模板其实早就存在**(SKILL Mode A/E 升级触发节 v8 早期就有 R5 格式),病根有二:①模板只有「进 X / 暂不升级」单流程形态 · case 是三候选动作 · 塞不进就退化成斜杠清单;②问题排查不进状态机 · 无机器 emit 可挂消费时刻提醒 · 长会话后凭记忆 emit 格式丢失。

### 改动(文本载体钉死 · 三处)
- **SKILL § Mode A/E 升级触发模板升级为多候选形态**:选项 1/2 = <按结论最可能的动作 · 具体化>💡 / <候选动作 B · 具体化>(不再绑死「进 X / 暂不升级」)· 新增三条规则:🔴 多候选动作**逐一编号**(斜杠并列 = 自由文本 · ok 无从解析 → 白问一轮)· 选项**具体化自排查结论**(「先修正 staging 配置(不改代码)」而非抽象流程名)· **💡 推荐必给**(排查者最有信息量 · 不给推荐 = 判断甩回用户 + ok 快捷词失灵)。
- **R5(b) 判定红线(全局)**:补「斜杠并列候选清单『A / B / C』同属自由文本」—— 不止排查 · 任何暂停点适用。
- **prepare.md 排查先行律**:升级暂停点行改为「候选动作逐一编号(R5 1/2/3 + 💡 推荐)」并显式点名反例(候选斜杠并列写进一行 = 自由文本)。

### 验证
- pytest 860 passed(纯文档 · 无行为变更)。
## v8.246 · 自动流转防歇脚:complete emit 机械附带「非暂停点 · 立即继续」提醒

> 来源 case:test→browser_e2e **自动流转**后 · AI 汇报完状态即结束回合(把回合边界当暂停点)· 用户被迫问「为什么暂停了」· AI 自己复盘用词与 SKILL R4 原文一致(「回合边界不构成暂停理由」)—— 规则早在 · 流转时刻无提醒 = 读过 ≠ 在场(与 v8.238 档位提醒同构的消费时点问题)。

### 改动
- **engine `AUTO_TRANSITION_CONTINUE_REMINDER`**:每次 auto-transition 的 stage-complete emit 附 `continue_reminder` 字段——「自动流转 · 非暂停点:本回合**立即继续执行 <next> stage**(汇报/总结完不停 · 回合边界/容量预算/让用户看进度都不是暂停理由 · R4)· 合法停点仅授权暂停点清单 · auto/yolo 同理」;fix-retry 未流转(transitioned_to=None)不附。
- SKILL R4「不膨胀」条款补实证与机器提醒说明。

### 验证
- 测试 +1(流转 emit 含 continue_reminder · 含下一 stage 名/非暂停点/回合边界关键词)· pytest **861 passed**。
## v8.247 · scratch 回收三件套:约定固化 + ship2 tmp-cleanup + bootstrap TTL 兜底(治 48GB 磁盘打满)

> 来源:另一 session 的完整提案(用户递交 · 基于真实事故)—— CI mac 磁盘 100% 打满(可用 51MB),下钻定位到 `/tmp/teamwork` 48GB 全是可无损重建的 cargo target(单 feature bl031 散落 7 目录 26GB · 躺了数月)。三条根因:①`/tmp/teamwork` 是事实约定但框架从未定义管理(agent 即兴命名 `bl031-*` · 无主命名空间「有人写没人收」)②ship2 只清 git worktree 不清 /tmp ③容器 /tmp 非 tmpfs 且无任何兜底回收。同类先例 = external-review-logs 膨胀 300MB(已治)—— 本版是同一模式在 160 倍量级上的复用,且提案给出关键设计差异:**cargo target 必须按目录整体删**(fingerprint 一致性 · 不能照抄 review-logs 的按文件删)。

### 改动(三处对应三根因)
- **A 约定固化**(standards/common.md 新 §六 + test-stage/conventions §12.5 消费点互链):临时产物统一 `${TMPDIR:-/tmp}/teamwork/<feature_id>/<用途>` —— 🔴 完整 feature_id(禁 `bl031` 类简称 · 实证即兴命名使按 ID 回收全落空)· 🔴 禁 scratch 根之外(实证 `/tmp/<项目名>-*` 泄漏 6GB)· 与截图约定同根;按 stage 隔离 target 是正确设计(防并行 cargo 锁争抢)只补回收。
- **B ship2 即时回收**(_v8_ship):`SHIP_FINALIZE_STEPS` 增 `tmp-cleanup`(worktree-remove 之后 · main-sync 之前)—— `_prune_feature_tmp()` 在 verify-delivered 通过后整树删 `<scratch>/<feature_id>/`(内容已上岸零对账价值)· 幂等(缺目录 n_a)· 失败不阻塞(warning)· emit 带 `tmp_cleanup.pruned_bytes`。
- **C bootstrap TTL 兜底**:`prune_teamwork_tmp()`(TTL 7 天 · 深度 2 mtime 判活跃〔cargo `.cargo-lock` 每次构建更新 · 全树 rglob 15GB target 会拖慢启动〕· 🔴 按目录整体删)—— 捞回放弃的 feature / 历史即兴命名孤儿 / 约定推行前存量;与 review-logs pruner 并列跑(git 守卫之前 · 与项目无关)· audit JSON 两处带 `teamwork_tmp_prune`。
- 参数取舍:TTL 7 天(review logs 45 天 —— 后者小且有对账价值 · cargo target 巨大且可重建);root 统一 `${TMPDIR:-/tmp}` 口径(比提案的硬编码 /tmp 多覆盖 macOS · 与 §12.5 一致)· `TEAMWORK_TMP_ROOT` env 测试注入。
- 已知局限照提案明示:scratch 根之外仍会泄漏(靠 A 约束)· 存量即兴命名靠 C 的 mtime 捞。

### 验证
- 新测试 +6(TTL 过期删/活跃留/浅层 mtime 防误删/缺根 n_a/ship 整树删含字节数/幂等 + 步骤时序断言)· pytest **867 passed**。
## v8.248 · 两个工具 bug 修复:ws-lint risks 误报 + ws-progress BL 撞号张冠李戴

> 用户在真实规划 session 报的两个 bug(没擅自改 skill · 用全局唯一编号绕开后回报):
> **①** ws-lint 的 v8.239 调研深度检查用 `^\s*-\s*id\s*:` 在**整个机读块**计数 feature —— `risks[]` 的 `- id: R1` 同写法(模板自带 risks 段)· 6 feature + 4 risk 误报「current_state 缺失(6/10)」——照模板写就必中(v8.239 我埋的)。
> **②** ws-progress 的 `by_bl.setdefault(r["bl"], ...)` 拿 BL 字符串当全局唯一键 · 但 conventions §4 明写「BL-NNN 各项目独立递增」—— 三子项目各有 BL-001 时先扫到的赢者通吃 · 且错的是标「勿手改」的自动生成块 · 每次刷新重新写错(更危险)。

### 修复
- **① features 段限定计数**:`- id:`/`current_state:` 只在 `features:` 段内统计(切片到下一个顶层键)—— risks/execution_waves 等列表不再串味;防矫枉过正:真缺失仍抓(0/1 测试锁定)。
- **② BL 撞号三级判别**(`_pick_bl_row` · 可单测):同号多候选时 ①target 缩写经 teamwork-space registry(`_parse_workspace_registry` 复用)映射 docs_root · 候选 ROADMAP 在其树下 → 命中;②行「对应 F编号」前缀 == target;③目录名 ci == target;④单候选/全不中兜底首个(不比旧行为差)。ready_to_start(v8.196)同一消费点一并修。

### 验证
- 新测试 +6(risks 不计入 · 真缺失仍抓 · registry 判别胜扫描序 · f_id 前缀回退 · 无 target 保旧 · 单候选直通)· pytest **873 passed**。
## v8.249 · 纠 v8.247:cargo target 按 feature 共享(不按 stage 切)· 恢复 stage 间增量编译

> 台账年检(用户:AI 自主时间太久)顺出的根因之一:v8.247 scratch 约定写「按 stage 隔离 target 是正确设计 · 防多 worktree 并行争抢文件锁」—— **推理错**。并行争抢发生在**不同 feature 的不同 worktree** 之间,而 scratch 路径里的 `<feature_id>` 已把它们隔开;同一 feature 内 stage 严格串行(状态机一次一个)、从不并发构建 —— 再按 stage 把 target 切成 `<feature_id>/test-stage`、`<feature_id>/dev-target`,唯一效果是 **test 拿不到 dev 编好的 target,每 stage 冷编整棵依赖树**(Rust 冷编 5-20min vs 热增量 <1min)。这正是台账里 test 阶段占 AI 自主耗时 23% + blueprint/test 编译重极值的主浪费来源。

### 改动(纯约定纠正 · 零代码逻辑 · GC 不受影响)
- **standards/common.md §六**:build target 改**按 feature 共享**(`<feature_id>/target` · 串行 stage 全复用);显式标注 v8.247 推理错(锁隔离只需到 `<feature_id>` 粒度)+ 例外说明(单 stage 内派多并行 cargo 构建才临时 sub-split);`<用途>` 示例去掉误导的 `test-stage`/`main-target`(那是 target · 不该 per-stage)。
- **stages/test-stage.md**:CARGO_TARGET_DIR 提示同步 —— target = `<feature_id>/target`(别切 `/test-stage`)· 测试日志等无缓存价值的才 per-用途。
- 回收不变:GC(`_prune_feature_tmp` / `prune_teamwork_tmp`)作用在 `<feature_id>/` 整目录级,target 是其下一个子目录名 · 改名无影响。

### 验证
- 纯文档 · pytest 873 passed(无回归)· 退役词表回归网通过。
## v8.250 · micro 流程重构:execute 零门禁自由执行 → ship(去 dev 门禁 + pm_acceptance)

> 用户拍板:micro 的病是「零逻辑改动却背全套 stage 门禁」。新 micro = **prepare → execute(自由执行 · 无规范限制)→ ship**。prepare 之后 AI 用它认为最合理的方式完成任务——自主决定用不用 subagent/teammate/workflow、自选模型、自决要不要跑测试,无任何框架规范限制,目标只有「完成任务」。然后 ship。

### 新 micro 链 = `execute → ship`(原 `dev → pm_acceptance → ship`)
- **新增 `execute` stage**(STAGE_SPECS 第 13 个 · allowed_flow_types=["Micro"]):零 prerequisites / 零 artifacts / 零 evidence 门 —— 唯一硬边界 2 条:① 代码写 worktree 内路径(并行隔离)② 不得超出 micro 准入白名单(超纲=误分诊·停·升 Feature)。brief 明写「自选 model/subagent/workflow/测试 · 无规范限制」。安全前置在准入白名单(prepare §2.2 卡死零逻辑),故执行阶段可无门禁。
- **去 pm_acceptance**:用户验收从 pm_acceptance 挪到 **ship1 的 MR diff review**(user_card + await-merge · 合并前看 diff)。`_check_pm_approved_ship` 加 micro 豁免(否则 ship-start 撞 pm_approved 前置)。micro 授权暂停点 3→2(prepare + ship1)。
- **去 dev**:micro 不再进 gated dev。`_dev_transition` 删死分支(Micro→pm_acceptance)· dev 一律 → review(去 micro 特例 · 防 v8.222 类死流程分支静默错误)。

### 改动面(两套流程图 + 初始 stage + 消费点)
- `_v8_stage_specs.py`:EXECUTE_SPEC + _execute_brief/_execute_transition + STAGE_SPECS 注册 + _check_pm_approved_ship micro 豁免 + _dev_transition 清死分支。
- `_v8_engine.py`:FLOW_STAGE_CHAIN["Micro"]=[execute,ship] + DEFAULT_REVIEW_ROLES 去 Micro/pm_acceptance 条目。
- `state.py`:MICRO_FLOW 转移图=execute→ship→completed + DEFAULT_INITIAL_STAGE["Micro"]=execute。
- 文档:新 stages/execute-stage.md · FLOWS/SKILL 流程表+暂停点清单+命令清单 · prepare §5 first_stage 映射 · STAGES.md 索引(+execute · 12→13)· README 双语计数。

### 验证
- 新测试 +10(链/转移图/初始 stage/execute spec 零门禁/transition→ship/brief 硬边界/pm 豁免仅 micro)· 旧断言 3 处更新(micro initial · no-pause 集 · dev-transition)· pytest **883 passed**。
## v8.251 · release-gated 裁决:拆开「代码门」vs「发版门」(治 review 磨不可闭合的 BLOCKER)

> 来源 case(aon-core Canonical-Offer):review 卡在物理上不可能本地关闭的 BLOCKER 上反复磨轮(round 4→5),用户被迫手动介入 4 次才把「真需发版」的 F-002 和「本地可 mock」的 F-004 拆开。病根:review 收敛协议把两种完全不同的「未闭合」混为一谈——代码缺陷 vs 发版证据。**review 只该 gate 代码完整性(本地/CI 能修的);发版证据(soak/rollout/prod-smoke)是独立发版门,不卡 APPROVE 但必须追踪到发版。**

### 改动(判据 + schema + carry-forward · 全做)
- **① release-gated 裁决**(review-stage.md 硬规则 3.5):证据物理上必须 post-deploy 的 BLOCKER/MAJOR → `status: deferred` + `deferred_reason: "release-gated · 欠<证据>"`,别磨轮,它是发版义务不是 review 阻塞。
- **② 双向护栏**(把 case 的分界线写成判据):**只有真部署/真墙钟/真生产平台能产的才算 release-gated**(真实 rollout/rollback · 24h/72h/7d soak · 不可 mock 的生产平台);**能 mock/fake/注入时钟复现的不算**(F-004 的 WireMock、soak 注入 clock 缩时)= 本地必须做完才 APPROVE,不许借 defer 逃。物化护栏:`deferred` 的 BLOCKER/MAJOR **必须写 deferred_reason**(空 defer → complete FAIL · 防扫地毯下 · hint 直接教 WireMock 反例)。
- **③ carry-forward**(release_gated_deferrals 抽取器):`deferred(release-gated)` 带结构化「欠什么证据」→ **pm_acceptance brief** 列「🚚 发版后待补证据 N 项」(用户验收知情)+ **ship1 user_card** 列同款(合并前看到)· 真追踪不消失。
- schema:findings 加 `deferred_reason` 字段(parse_review_findings 保留)。

### 效果
case 能自主收敛:F-002 识别 release-gated → deferred + 记义务(carry 到 pm/ship);F-004 识别本地可 mock → 空 defer 被物化门拦 → AI 自己写 WireMock → APPROVE。**零用户往返。**

### 验证
- 新测试 +7(空 defer 拦 · MINOR 不强制 · release-gated 放行 · open 仍拦 · 抽取剥前缀 · pm brief 含/不含)· 旧断言 1 处(findings +deferred_reason)· pytest 897 passed。
## v8.252 · ws-progress 健壮性两修:状态词表漂移 + .worktree 扫描污染

> 两个实战 bug(并行 session 修 · 本版一并发):
> **① 状态词表漂移**:项目 ROADMAP 混用「✅ 已交付」「已上线」被判「待开始」→ 进度假 0/N + `ready_to_start` 失灵(该起的 feature 起不来)。且词表外写法被静默吞,漂移无人发现。
> **② `.worktree` 未排除**:ws-progress/ws-lint 全仓 rglob 扫到并行 feature worktree 内的**旧基线副本** → 「算旧写旧」+ 把进度自动块**写进别人的 worktree**(工具污染他人工作区 · verdict 却 OK)。

### 改动
- **状态桶归一**(`_ws_status_bucket`):完成态收别名 `已完成/已交付/已上线`;剥前导 emoji 后按**起始词**匹配(防「基本已完成，待测试」子串误判完成);词表外 → 归「待开始」+ **标不可识别**(不静默吞)。
- **unrecognized 警告 surface**:`_render_ws_progress` 返回 `(block, unrecognized)`,总览顶部 emit `⚠️ 状态词不在词表(按待开始计 · 词表见 roadmap.md)` —— 漂移当场可见。
- **扫描排除单源**(`_ws_scan_ok` + `_WS_SCAN_SKIP`):显式目录名 + **任何隐藏目录段**(`.worktree` 及自定义 worktree 根都兜住)· WS/ROADMAP rglob 全走它。
- **正本判定 + 多候选 surface**(`_find_ws_file` 返回最优候选 + 全部候选):排序 product-overview 优先 → 段数少 → 字典序;多候选时列清单(治 rglob 无序取首把进度写错副本)。
- roadmap.md 模板状态词表同步(别名 + 起始位置规则 + unrecognized_status 警告说明)。

### 验证
- 新测试 `test_ws_scan_vocab.py`(worktree 污染 / scan_ok 排除 / find_ws_file 正本+候选 / 别名计完成 / 子串不误判 / bucket 单测)+ test_ws_progress_v8174 更新 · pytest 897 passed。
## v8.253 · ship 翻牌验收门:state.bl 的 ROADMAP 行必须真翻完成态(治「漏翻 → 进度误报 0/N」)

> 来源 case(WS-19):S1 早已交付合入 staging · 但 ship 时**漏翻 ROADMAP 状态格** → ws-progress 一直误报 0/4 · ready_to_start 失灵 · 直到人工查账翻旧账才发现并手工订正。病根:`--planning-artifacts` 是**自由声明**(AI 说翻了就算翻了)· 机器从没验收过「声明的翻牌真的翻了」。

### 改动
- **`_check_bl_flipped`(archive 新门)**:`state.bl`(v8.196 机读绑定)已知 → worktree 内 ROADMAP 对应 BL 行状态格必须已翻**完成态**(复用 v8.252 状态桶:已完成/已交付/已上线 · 起始词匹配防「基本已完成」假翻;复用 `_ws_scan_ok` 防 .worktree 旧副本假翻)· 未翻 → PENDING(hint:worktree 内翻状态 + 填「对应 F编号」+ 计入 --planning-artifacts 重跑)。
- **`--no-planning-changes` 不豁免**:有 BL 关联 = 必有 ROADMAP 行可翻 · 矛盾同拦(同一门顺带治)。
- **例外通道**:`--bl-flip-exception '<理由>'`(部分交付等)· 记 `state.ship.bl_flip_exception` 审计留痕 · 不静默。
- 跳过条件(不误拦):state.bl 未设(ad-hoc)/ worktree 内无该 BL 行(行在其他仓/legacy)。
- ship-stage.md §archive 步骤表补 1.5 翻牌验收门。

### 验证
- 新测试 +6(无 bl skip / 行缺 skip / 未翻拦 / 已交付别名算翻〔v8.252 复用〕/ .worktree 旧副本不算翻 / 「基本已完成」不算翻)· pytest **903 passed**。
## v8.254 · 并行姿态两问补丁:阶段演进重问 + 等待窗口不闲置

> 来源 case(WS-19-S2 dev):开工时并行判断做对了(双线 = 耦合度允许的最大并行),但进入**集成测试子阶段**时把整包塞给单 agent · 主对话自己裸等 —— 用户问「为什么只有一个 Agent 在干活」· AI 被点破后当场自查出完美拆法(两个测试任务零文件重叠 · 可独立 TEST_PG_DB_NAME 隔离 · 完全可拆)+ 主对话该填的完工自查证据行(6/8 当场落钩)· 三线并行就位。病根:v8.225/236 的「开工先问哪些可并行」只在**开工时刻**问一次 —— 耦合度随子阶段变 · 开工时的最优拆分会过期;且「等待 agent」被当成合法闲置。

### 改动(三处姿态单源/消费点)
- **SKILL 全局姿态条目**(v8.225 段):两问补丁 —— ①「哪些可并行」**每进新子阶段重问**(实现→测试编写→修复)②派发后**等待窗口主对话不闲置**(干自己能干的:自查证据 / 再拆剩余工作)。
- **dev brief**(消费时刻):🧩 段同步两问(dev 是并行红利最大 stage · 最易犯)。
- **dev-stage.md ③**:新增「并行姿态两问」段 —— 含子任务独立判据(零文件重叠 + 可独立隔离 → 满足就再派)与 case 实证。

### 验证
- 纯文本(姿态规则)· pytest 903 passed。
## v8.255 · DB 变更带目的 + 变更最小化四问(治「只写内容不写为什么 · 三张新表无人质询」)

> 用户看 DB 变更确认暂停点截图(表 = 表名|类型|内容|破坏性 · 三张新表)提两点:①每项变更要给**目的**——解决什么问题、为什么要这样变更;②设计方案时要**前移质询**——是否有更简单的、直接减少数据库变更的方案。溯源:截图表格正是 templates/tech.md「变更表清单」的列结构 —— 模板天生没有「为什么」列 · 项目照模板填自然就缺;v8.242 的暂停点明细虽有「用途」列 · 但项目直接抄 TECH 表 → 用途丢失。

### 改动(模板源头 + 设计前移 + 暂停点同构)
- **templates/tech.md §变更表清单**(源头):列升级 `表名|变更类型|变更内容|解决什么问题|为何非更简方案不可|破坏性`;表前置 🔴 **变更最小化四问**(①复用既有表/列〔加约束/局部索引〕②应用层/查询时计算 ③不入库〔缓存/TTL/内存〕④并入既有表 JSONB/扩展列 —— **全否才有资格入表**);「为何非更简」列 = 写否掉的最近一个更简方案 + 否的理由(写不出 → 该变更大概率不需要)。
- **blueprint-stage.md**:§数据模型标注行加「变更最小化先问 · 设计时前移不是确认时补 · DB 变更数是简洁性 counter-lens 重点审查对象」;§7.5 暂停点明细表列与 TECH 表**同构**(对象|变更|解决什么问题|为何非更简方案不可|破坏性)—— 用户拍板直接看动机。
- **specs blueprint brief**(消费时刻):TECH 结构行 + §7.5 提醒行同步(「只写内容不写为什么也不算变更点明细」)。

### 验证
- 纯模板/文档 · pytest 903 passed。
## v8.256 · 效率三刀:验证轮降档 + TC∥TECH 起草并行 + goal 终确认投机窗

> 台账年检第二批(用户令「整个流程还有什么办法提升效率」)· 提五刀 · 用户拍板:①④+投机 TECH 做;**②(ship1 等合并窗启动下一 BL)不做——是否启动下一个 prepare 不确定 · 用户主权**;**③(auto 推荐)不做——不启 auto 的目的就是人工确认 PRD 与 DB 变更 · 等待是有意设计不是浪费**;⑤(波次推广)不做。

### ① 验证轮降档(goal/review Round 2+ → 验证档模型)
- 数据:goal 占 AI 自主 44%(大头=冷审修订循环 · finding 采纳率 80-90% 必有 Round 2+)· review 33% 到 3 轮;验证轮任务性质 = 校验型(核实 fix + 范围锁定内找新 · 对照清单)· 按档位规则本该验证档 · 但文档从未点名 → AI 默认继承重档。
- 落点:`_review_verify_round_brief`(Round 2+ 的消费时刻 emit)+ goal-stage ③ / review-stage 硬规则 5 / goal brief。首轮全量冷审不降档。预估砍 goal+review 循环成本 ~10-15% AI 自主时间。

### ④ TC ∥ TECH 起草并行(blueprint)
- TC 锚 PRD.AC · TECH 锚设计方案 · 相互独立 → **并行同发**(subagent 各一)· 完成后互查 `covers_ac` ↔ §测试策略。blueprint 中位 27m · 预估省近半。

### 🔮 goal 终确认投机窗(上一轮提议 · 本版落地)
- 时点纪律:**只在 emit 终确认暂停点后投机**(冷审收敛前 PRD 是活靶 · v1 时点必返工);数据:终确认「改:默」≈ 全默(变动率≈0)· goal 等待中位 26m ≈ blueprint 起草中位 27m(等待窗恰好藏下)。
- 行为:等待窗后台派 TECH 草稿 subagent(worktree 内草稿 · 🔴 不跑 state 命令);用户 ok → blueprint 接续;有改 → 差量更新;auto/yolo 不适用(无等待窗)。落点:goal-stage ④ 投机窗 + goal/blueprint brief + SKILL 等待窗条目补例。

### 拍板否决留档(防未来再被「优化」)
- ship1 等待窗启动下一 BL:❌ —— 启动 BL = 用户拍板事项(feature-planning 坑 5 同源);auto 推荐判据:❌ —— 中间等待点是**有意设计的确认闸**(PRD/DB 变更)· 非浪费。

### 验证
- 纯文本/brief · pytest 903 passed。预估三刀合计:中位 feature AI 自主 182m → ~150m · 墙钟 -15% 左右。
## v8.257 · DEV-RULES 三项制:API 契约 / 错误处理 / 其他约定(架构归 ARCHITECTURE · 命名风格测试归 standards)

> 用户拍板简化:架构已有 ARCHITECTURE.md · DEV-RULES 只留三项。原六段(架构分层/命名/错误处理/测试策略/代码风格/其他)与 ARCHITECTURE.md、standards/ 缺省存在职责重叠 —— 项目真正需要人来强制注册的就三类:**对外契约、失败语义、杂项强制特例**。

### 改动
- **templates/dev-rules.md**:骨架六段 → 三段。新增 **API 契约** 段(响应包络/错误码结构/分页/字段 casing/版本兼容 —— 存量风格 = 对外契约 · 沿用并在此注册 · standards 覆盖声明唯一注册处);**错误处理** 保留;**其他约定** 兜底(命名/风格/测试策略若有偏离 standards 缺省的强制特例注册在此)。
- **去向声明**:架构/分层/依赖方向 → `ARCHITECTURE.md`(workspace/{子项目})+ ADR(边界表加行);命名/风格/测试策略 → standards/ 缺省。
- **五处消费点词表同步**:SKILL 文档信息架构表 + 路由表 · blueprint-stage 必读行 · knowledge 边界表 · 模板自身定位句。

### 验证
- 纯模板/文档 · pytest 903 passed(bootstrap 只建空壳 · 存量项目 DEV-RULES 不受影响——已存在绝不改动的原则不变)。
## v8.258 · RELEASE-GUIDE.md:版本发布规范(用户点单 · 默认 staging→main MR + URL 置顶 + 提醒合入)

> 用户拍板新增:RELEASE-GUIDE.md 作为版本发布规范 · 默认内容 = 发布到线上流程:创建 staging → main 的 MR/PR 后给出 URL · 提醒用户合入。填补的空档:「发布/上线」此前无任何流程覆盖(ship 只管 feature → 集成分支;集成 → 生产无人管)。

### 改动
- **templates/release-guide.md**(新):默认五步流程 —— ①核对 staging(列本次上线清单给用户过目)②创建 staging→main MR/PR(CLI-first)③🔴 URL 置顶独立行原样贴(同 ship1 user_card 纪律)④🔴 提醒用户合入(AI 不代点 · 可轮询监控)⑤发布后义务(核对各 feature REVIEW 的 release-gated 待补证据〔v8.251〕逐项补跑)。+ 环境分支段 / 项目特有步骤段(人维护)。
- **边界声明**:本文件管「集成分支 → 生产」;单 feature 交付(feature → 集成)归 ship stage · 别混。人维护原则同 DEV-RULES(bootstrap 无则建 · 已存在绝不改 —— 但模板自带可用默认 · 非空壳)。
- **bootstrap 骨架**:skeletons 六件 → **七件**(+RELEASE-GUIDE.md)。
- **消费点**:SKILL 信息架构表 + 路由表(「发布/上线/发版 → RELEASE-GUIDE.md · PMO 必读照办 · 合入归用户」)· conventions §13 · templates/README 索引。

### 验证
- 骨架测试 fixture +release-guide · pytest 903 passed。
## v8.259 · RELEASE-GUIDE 入图:DEV-RULES 协作区互链 + teamwork-space 知识入口登记

> 用户点单收尾:①DEV-RULES 关联发版规范 ②teamwork-space 目录加该文档。零死角律要求磁盘上的知识节点必在地图有指针 —— v8.258 建了文件 · 本版把它接进知识图谱。

### 改动
- **templates/dev-rules.md 协作区**:+`RELEASE-GUIDE.md` 互链(「本文件管怎么写码 · 它管怎么发版」)。
- **templates/teamwork-space.md 知识入口**:project-specs 行「内含」列更新 —— +RELEASE-GUIDE(发版)· 顺带纠旧清单(去已废 RESOURCES · 补 UI-RULES/PROCESS-LEDGER · 标注清单单源 conventions §13)。

### 验证
- 纯模板 · pytest 903 passed。
## v8.260 · fast mode:去掉所有评审环节(localconfig 配置 · 默认关 · 与 yolo 互斥)

> 用户点单:增加 fast mode · 去掉所有评审环节 · 默认关 · `.teamwork_localconfig.json` 配置开启。

### 语义
- **开关**:`fast_mode: true`(缺省/false = 关)· init-feature 时**快照进 `state.fast_mode`**(中途改配置不影响 in-flight feature)。
- **去掉**:goal 冷审(PL 质疑/外审 · 不产 PRD-REVIEW.md)· blueprint 评审(Architect 主审/外审 · 不产 TECH-REVIEW.md)· **整个 review stage**(dev 直进 test)。
- **保留**:测试证据硬门(exit 0/差分)· verify-ac · 全部用户暂停点(prepare/PRD 确认/DB 确认/pm_acceptance/ship1)· worktree 纪律 · ship 全链。
- 🔴 **与 yolo 互斥**(init-feature 硬拦):yolo 无人值守的唯一安全网 = 自动化评审 · fast 恰好拆掉它 —— 有人值守下 fast 才安全;与 auto_mode 正交可叠。

### 实现
- **state.py**:`_read_fast_mode`(默认 False · 显式 true 才开)· init-feature 快照 + roster 全清空(roster-aware 门自动放行 · adjustments 审计留痕)+ yolo 互斥拦;三链图 dev 边 +`test`(fast 转移合法)。
- **engine**:`StageArtifactSpec.review_artifact` 标记 + complete 校验循环 fast 跳过(PRD-REVIEW/TECH-REVIEW 标记)。
- **specs**:`_dev_transition` fast→test · `_check_review_approved`(test 前置)fast 放行 · `_evidence_prd_verdicts_all_pass` fast skip · goal/blueprint brief 条件提示行(⚡ fast_mode 生效 · 去了什么留了什么)。
- **配置面**:localconfig 模板 + config.md 文档段(含警示:质量安全网自拆 · 原型/个人适用)· SKILL 模式区新 fast 节(auto/yolo 并列)。

### 验证
- 新测试 +8(读取三态 / dev 跳 review / 图边合法 / test 前置放行 / PRD verdicts skip / 产物标记正反)· pytest **911 passed**。
## v8.261 · fast mode 语义修正:留两端单路合并评审(PRD:PL+外审合一 · 代码:Architect+QA 合一)

> 用户改逻辑:fast 不再全拆 —— **留 PRD 评审**(把 external 和 PL 关注点合并)+ **留代码 review**(把架构师和 QA 关注点合并);blueprint 评审仍去。从「零评审」修正为「两端各一路合并评审」:质量关口保住需求侧与代码侧两个最值钱的位置 · 砍掉的是多路独立性与中段方案评审。

### 语义(v8.261 覆盖 v8.260)
- **roster = `{goal: [fast], review: [fast]}`**(「fast」= 合并伪角色 · 单隔离 agent 兼多帽):
  - **goal 单路合并冷审**:兼 PL(质疑六问 ≥1 实质)+ 外审(可实现/可验证 + AI 自主方向)· 产单份 PRD-REVIEW.md(`reviewers: [fast]` · `verdicts: {fast: ...}`)· **verdicts 全 APPROVE 门照拦**(v8.260 的 skip 撤销 · PRD-REVIEW 恢复必产必查);
  - **review 单路合并评审**:兼 Architect(实现↔设计一致性 · 简洁性 counter-lens)+ QA(测试真实性与覆盖 · 代码质量盲区)· REVIEW.md 单份 · **findings/severity/验证轮/轮次预算协议照跑** · 无 REVIEW-arch/-qa/external 独立产物(roster-aware 门自动放行);
  - **dev → review 恢复正常转移**(v8.260 的跳 review 撤销 · 三链图 test 边还原)。
- 不变:blueprint 评审去(TECH-REVIEW 不产不查 · `review_artifact` 标记保留)· 测试硬门/verify-ac/全部用户暂停点/worktree/ship 全链保留 · 与 yolo 互斥 · 默认关。
- 消费点:goal/blueprint/review 三 brief 的 fast 条件行(合并关注点清单写死)· SKILL fast 节 · config.md/localconfig 注释。

### 验证
- 测试改写至 v8.261 语义(+1:三 brief 合并 mandate 断言)· pytest **912 passed**。
## v8.262 · yolo 忽略 fast + PRD 送审前自检(评审关注点前置)

> 用户两令:①yolo 模式忽略 fast(不再互斥报错);②优化 PM 写产品文档的约束 —— 把要评审的点提前考虑进去 · 不要等评审有问题再改。

### ① yolo 忽略 fast(v8.261 互斥 → v8.262 静默覆盖)
- `--yolo` + localconfig `fast_mode: true` → **不报错** · fast 静默不生效(无人值守回全量评审安全网)· kickoff concerns 记 INFO 留痕(用户知情)。修复顺带抓到的缩进 bug:原实现 yolo 分支后 roster 仍被改成 fast 伪角色 —— 已归位 else 内。
- SKILL fast 节 / config.md / localconfig 注释 三处同步。

### ② PRD 送审前自检(评审关注点前置 · 治 Round 2+ 修订循环)
- 数据:goal 占 AI 自主 44% · 大头 = 修订循环;finding 采纳率 80-90% = **多数问题可预见** · 前置消掉最省。
- **templates/prd.md 新增 §送审前自检**(起草完 · 送冷审前 · 逐项打钩):PL 六问自问(答不出先补 · 别指望冷审替你想)/ **可实现**自查(依赖的接口字段真实存在 · 读过真实代码非假设)/ **可验证**自查(AC 可测 · 无「尽量/合理/优化」含糊词 · 边界异常有归宿)/ 高频 finding 预检(术语已定义 · AC 无矛盾)。
- goal-stage ③ 起草段 + goal brief 8 步链(起草 v0.1 → **送审前自检** → 冷审)消费点同步。

### 验证
- pytest 912 passed。
## v8.263 · 修正 v8.262:起草思考规范是「写法」不是「环节」

> 用户修正:「不是加自检环节,是写 PRD 的时候按这个规范去思考」。v8.262 把评审关注点做成了**写完后过的自检清单段**(§送审前自检 · 逐项打钩)—— 形态错了:那是又加一道仪式;用户要的是**起草时的思考方式**,关注点织进写的动作里。

### 改动
- **prd.md**:删 §送审前自检 整段;模板头新增 **🧠 起草思考规范**(写的时候就这样想 · 非写完检查):写背景/方案时 PL 六问过脑(写不顺的地方就是冷审会打的地方)· 写每条 AC 时用可测判据(「尽量/合理/优化」**落笔即换**)· 涉依赖先读真实代码确认存在再写 · 术语当句定义;AC 表注释就地强化(写时即用可测判据)。
- **goal-stage ③**:「送审前自检」段改写为「起草思考规范(写法非环节)」;**goal brief**:撤独立自检步 · 思考规范并进「起草 v0.1」步内注。

### 验证
- 纯模板/文档 · pytest 912 passed。
## v8.264 · localconfig 两修:fast_mode 入自愈默认表 + 「可提交」文档漂移纠正

> 用户问「.teamwork_localconfig.json 什么时候创建」· 答题时撞出两个实质问题:①v8.260 加 fast_mode 时漏了 `LOCALCONFIG_CONFIG_DEFAULTS`(:708 明写「新增字段两处都加」)—— **存量项目的自愈永远不会补出这个新选项 · 用户看不到**;②conventions §13 说该文件「可提交」· 但 bootstrap 实际把它加 .gitignore(`_bootstrap` 段含 host/maintain 时间等机器态)—— 文档与机器行为相反。

### 改动
- **bootstrap `LOCALCONFIG_CONFIG_DEFAULTS` + `fast_mode: False`**:存量项目下次 session 自愈即补出字段(带注释 · additive 不覆盖已有值)。
- **conventions §13 纠正**:`.teamwork_localconfig.json` = **本机级 · bootstrap 自动 gitignore** · 团队共享档位靠各机自配(非 git 共享)。

### 验证
- pytest 912 passed。
## v8.265 · 兜底纪律:默认不做(复杂度×收益)· 确需的在暂停点透出拍板

> 用户令:产品方案和技术方案要考虑复杂度和收益 · **不要做没必要的降级兜底和安全兜底**;确需的兜底策略必须**在暂停点明确提出来**(不许默默做)。AI 天然偏加兜底(重试/降级/防御层)—— 每层兜底都是复杂度,且历来藏在方案正文里从不被拍板。

### 改动(写法 + 判据 + 暂停点透出 三层)
- **写法**(v8.263 形态 · 起草时思考):prd.md 🧠 起草思考规范 +1 条 —— 涉降级/兜底体验默认不做 · 确需的是**产品决策** · 列 §待决策项或终确认导读;tech.md 简洁性自查 +1 条 —— 每个 fallback/degradation/重试熔断/防御层过「真实概率×后果 vs 实现维护成本」· 写不出必要性 → 删。
- **判据落盘**:tech.md 新 **🛡️ 兜底清单**表(兜底|保护什么失败场景|概率×后果|为何值得)· 无则写「无兜底」—— 透出的单源。
- **暂停点透出**:blueprint **§7.5 扩展为双触发**(v8.265):DB 数据结构变更 **或 兜底清单非空** → R5 方案要素确认暂停点(两类命中一次给全 · 兜底块照抄 TECH 清单);goal 终确认导读余节 + 🛡️ 兜底策略行(PRD 层降级体验 · 无则「无」)。auto 模式同款 skip+WARN(消息含 兜底 摘要)。
- **评审侧**:blueprint §4 Architect 简洁性 counter-lens 点名「兜底是重点砍除对象」。
- 消费点:specs blueprint brief(§7.5 双触发 + TECH 结构行含兜底清单)· SKILL 授权暂停点清单 ④ + auto 表 blueprint 行改「方案要素确认(DB 变更/兜底)」。

### 验证
- 纯模板/文档 · pytest 912 passed。
## v8.266 · 修正 v8.265:兜底不是「默认不做」· 是逐项算 ROI

> 用户修正:「不是默认不做,需要考虑 ROI」。v8.265 把判据写成了先验偏向(默认不做 / 重点砍除对象)—— 正解是**中性算账**:每个兜底逐项算 保护场景的真实概率×后果 vs 实现维护成本,**ROI 立得住 → 做;立不住 → 砍**。两个方向都不许偷懒:AI 天然偏加兜底(别不算账就加),但高概率×高代价的兜底是正收益(别一刀全砍)。

### 改动(纯措辞纠偏 · 透出机制不变)
- prd.md 思考规范:「默认不做」→「按 ROI 取舍(立得住做 · 立不住砍)」。
- tech.md:判据条改「兜底按 ROI 取舍 · 两个方向都别偷懒」;清单表列「为何值得」→「ROI 结论(vs 实现维护成本)」;清单引导「确需保留」→「ROI 立得住而保留」。
- blueprint §4 lens:「兜底是重点砍除对象」→「兜底按 ROI 审 · 两个方向都要实证」(对齐既有裁决举证对称原则);§7.5 触发条与暂停点兜底块同步 ROI 措辞。
- specs brief TECH 结构行同步。
- 不变:兜底清单落盘单源 · §7.5 双触发透出 · 用户拍板 · auto skip+WARN。

### 验证
- 纯措辞 · pytest 912 passed。
## v8.267 · fast 模式评审最多 2 轮 · 轮尽未收敛决策点抛用户

> 用户指令:「fast 模式评审最多 2 轮,无法收敛的决策点抛用户」。fast 的提速语义补上收敛端:单路合并评审(v8.261)管宽度,本版管深度 —— 首轮全量 + 1 验证轮共 2 轮,轮尽不再循环,把未收敛的决策点直接交用户拍板。

### 引擎(硬拦)
- `FAST_MAX_REVIEW_ROUNDS = 2`:`review-retry` 处 `state.fast_mode` → 预算 = min(localconfig `max_review_rounds`, 2)(显式配更小则从小)。
- 超预算 R5 暂停点:标题带「⚡ fast 模式封顶」标记 · 首行明示「以下即未收敛决策点 · 请你拍板」(open findings 按 severity 列全 + 1/2/3 · 逃生 `--user-confirmed --reason` 照旧)。

### 消费时点提醒(brief)
- goal 首轮 brief fast 串:冷审最多 2 轮 · 第 2 轮末未收敛 → 停止循环 · 决策点列进终确认导读 🟡「你要拍板的」(goal 无引擎轮门 · 复用既有终确认暂停点作为抛出通道)。
- review 首轮 brief fast 串:评审预算封顶 2 轮(引擎硬拦)。
- 验证轮 brief(fast 时):「⚡ 本轮即最后一轮」置顶提醒。

### 文档
- goal-stage 规则 7(收敛软上限 3 轮)补 fast 2 轮分支;review-stage 规则 6(轮次预算)补 fast 封顶;SKILL fast 节 + localconfig 模板注释 + config.md 同步。

### 验证
- 新增 3 测试(默认 3→封顶 2 拦 round 3 / localconfig=1 取更小 / 三处 brief 提醒 + 非 fast 无)· pytest 915 passed。
## v8.268 · 正常模式双路评审模型错开 · 外审路 ≠ 主审路

> 用户指令:「正常模式双路评审时模型要错开,例如 PRD 一路是 fable5,另一路应该是 opus」。同模型双路 = 盲区相关(系统性偏差两路同瞎)—— 两路并行冷审(goal:PL+外审 / blueprint·review:Architect+外审)**模型必须不同**:主审路继承会话主模型 · 外审路错开一档(fable5 会话 → 外审 opus;opus 会话 → fable5/sonnet)。零 CLI 成本拿到近异质(上下文与权重双错开);跨厂商异质 opt-in(codex/gemini)时天然错开;fast 单路不适用;验证轮照 v8.256 降档(降档本身即错开)。

### 消费时点(规则到场)
- `DISPATCH_TIER_REMINDER`(每 stage-start 附带)加错开条。
- goal / blueprint / review 三 brief 的两路派发行加 🎭 标记。
- `external-review` subagent 配方 next_action:起 subagent 时 model 参数用 ≠ 主会话的档(降级路同享)。
- SKILL 🎚️ dispatch 档位节 = 单源全文(why + 配对示例 + 边界)。

### 措辞升级(「同模型 subagent 冷审」→「错开模型」)
- SKILL yolo 节 ×3 · goal-stage 外审行 + 两路并行行 · blueprint-stage §6②/§3 产物注 · review-stage §7 · roles/external-reviewer · standards/external-model-usage(默认语义块 + 代价自知句:非跨厂商异质 · 强于同模型 · 仍弱于 codex 级)· config.md · yolo-preflight · bootstrap/state.py 各 INFO。
- 不变:异质性硬约束(同厂商仍非「异质」· degraded/heterogeneous:false 诚实标注照旧)· self-review exec 兜底(客观同模型 · 保持)。

### 验证
- 新增 test_model_stagger_v8268(3:提醒/三 brief/配方)· pytest 918 passed。
## v8.269 · 单路评审与会话主模型错开 · 补全错开不变式

> 用户指令:「单路评审要和主模型分开」。v8.268 只管了双路(外审路 ≠ 主审路),把 fast 单路标了「不适用」—— 但单路是仅有的独立采样,跑会话主模型 = 起草者自审(盲区全相关)。本版补全:**不变式 = 任何评审配置至少一路 ≠ 会话主模型** —— 双路 = 外审路错开;**单路(fast 合并 / roster 减到一路)= 该路必须错开**(如 fable5 会话 → 评审 opus)。

### 改动
- SKILL 🎚️ 单源:「fast 单路不适用」→ 单路同样错开 + 不变式表述(顺修 v8.268 括号瑕疵)。
- `DISPATCH_TIER_REMINDER`:错开条改双路/单路两分支(消费时点)。
- goal / review 两个 fast brief 串加 🎭 单路错开行(消费时点)。
- SKILL fast 节「留两端」行 + localconfig 模板注释 + config.md 同步。
- 边界不变:验证轮照 v8.256 降档(降档即错开)· 跨厂商异质 opt-in 天然错开 · degraded 诚实标注照旧。

### 验证
- test_model_stagger 新增 3(提醒单路分支 / fast 两 brief / 正常 brief 不受污染)· pytest 921 passed。
## v8.270 · Bug 流 review 改单路评审 · 只留 external

> 用户指令:「bugfix 改为单路评审,只留 external」。Bug 流的质量重心在 diagnose(根因 + 修复方案经用户确认才许修)—— review 只需盯「fix 是否忠于已确认方案 + 是否引入新问题」,双路属重了。默认 roster `["architect","external"]` → `["external"]`:一路错开模型隔离冷审(≠会话主模型 · v8.269 单路不变式天然满足)。

### 改动
- `DEFAULT_REVIEW_ROLES` `("Bug","review")` → `["external"]`;Bug chain review 注同步。
- review brief 新增 🐛 `_bug` 条件行(flow_type=Bug 且非 fast):单路语义 + 覆盖必含**修复↔diagnose 方案一致性**(Architect 视角并入)+ REVIEW-arch 不产;fast 优先(fast 时 roster 已是 [fast])。
- 静态两路行标注 Feature 默认 · Bug 差异;review-complete `--artifacts` 注 ×2(Bug 单路 REVIEW.md 即可)。
- review-stage.md / FLOWS.md Bug 行同步;`change-review-roles` 可加回(审计留痕)。
- 协议不变:REVIEW.md findings 台账/severity 门/验证轮/轮次预算照跑 · cross_review_coverage 物化门照拦 · 门禁 roster-aware 自适应(REVIEW-arch 不再要求)。

### 验证
- test_bug_review_default 断言更新 + 新增 brief 条件测试(Bug 带注/fast 优先/Feature 不污染)· pytest 922 passed。
## v8.271 · PRD 每条 AC 配大白话解释 · 机器校验逐条非空

> 用户指令:「PRD 模板优化,每一个 AC 都需要大白话解释一下」。BDD(Given/When/Then)是给 QA 绑 TC 的机器友好写法,但用户终确认时读起来费劲 —— §验收标准表加 **💬 大白话列**:每条 AC 一句人话(这条在验证什么 · 用户能感知到什么变化),与终确认导读「说人话」哲学同源,拍板者逐条看得懂。

### 改动
- templates/prd.md:AC 表加 💬 大白话列(含示例:「登录成功后 3 秒内能看到自己的头像和昵称」)· 表注/🧠 起草思考规范 AC 条/自查清单同步(写时即配 · 非写完补)。
- goal-complete 新 evidence `ac_plain_words`:解析 §验收标准表 —— 缺列 FAIL(提示照模板加列)· 逐行空/占位(`{...}`/`-`/`无`)FAIL 并列出 AC id;段缺失/无 AC 行不重复报(归 conformance/verify-ac)。
- goal-stage 规则 1 + goal brief 起草思考行同步。
- 机读块不动:大白话属人读单源(body 表)· 不进 TEAMWORK-MACHINE(id 一致原则照旧)。

### 验证
- 新增 test_ac_plain_v8271(5:填齐过 / 缺列 / 空+占位列 id / 无段放行 / 关键词不误判)· pytest 927 passed。
## v8.272 · PRD 终确认暂停点回显 PRD 绝对路径

> 用户指令:「prd 确认的暂停点,回显一下 PRD 文件的绝对地址」。终确认导读再好也是摘要 —— 用户想核对全文时得自己找文件。导读**头部第一行回显 PRD 绝对路径**(格式 `PRD: /abs/.../PRD.md` · 🔴 绝对路径非相对 · worktree 内产物给 worktree 绝对路径),点开即达。

### 改动
- goal-stage ④ 终确认导读 spec 加头行回显要求;goal brief 步链「用户确认」步同步(消费时点);SKILL 暂停点清单 ② 标注。

### 验证
- brief 断言 ×1(fast/正常两态均携带)· pytest 928 passed。
## v8.273 · 审核员只审内容 · 不重复跑测试脚本

> 用户指令:「审核员只需要审核内容,不需要重复跑测试脚本」。测试执行已有归属:dev(TDD)与 test stage(硬门 exit 0/差分 · 证据落盘)—— 评审员再跑一遍 = 双倍时延零新增证据。评审 = **静态审读**(diff / 代码 / 测试代码 / 实跑证据日志);疑点开 finding 由流水线实跑验证。

### 改动
- 覆盖方向「测试真跑」措辞消歧 ×3(hint 表 / brief 产物注 / review-stage 外审契约):测试真跑 = **读实跑证据/日志** · 非评审自己重跑 —— 这是最容易诱导重跑的一处措辞。
- review-stage 新规则 8:只审内容(Architect / QA / external / 验证轮全适用)。
- review brief(round 1)+ 验证轮 brief 各加纪律行(消费时点):验证轮裁决 fixed/not-fixed 依据 = 读修复 diff + 引用流水线证据。
- external prompt 模板本已拦(reviewer.md「跑测试 → out of scope」)· 本版补齐主审路与验证轮。

### 验证
- 新增 test_review_content_only_v8273(3)· pytest 931 passed。
## v8.274 · teamwork-space.md 骨架带 teamwork 安装地址

> 用户指令:space 文件要包含 teamwork 安装地址 —— 没装 teamwork 的协作者拿到项目、打开知识地图根,第一眼就能看到怎么装。头部引言加一行:🧰 本项目使用 [teamwork](https://github.com/okteam99/teamwork) AI 协作框架 —— 未安装的协作者:`npx skills add okteam99/teamwork`(装完 `/teamwork` 启动)。

### 改动
- bootstrap `maintain_teamwork_space` 精简骨架 + templates/teamwork-space.md 完整模板骨架块(两处生成源都带 · 新项目自动携带)。
- 存量项目:AI 维护 space 时按模板对齐即可补上(不加自动迁移 · space 变更需用户确认 R5)。

### 验证
- test_bootstrap +2(生成物含安装行 / 模板含安装行)· pytest 933 passed。
## v8.275 · 暂停点投递位置红线 + migration 门目录级匹配 + 配方补 target_commit

> 实证 case(IOS-F005 会话三连):① ship1 卡片按模板写了、但贴在回合中段(随后又调 await-merge)—— 宿主不渲染回合中段文本,卡片被吞,用户被迫问「url 发下」:内容防了 · **投递位置没防**;② `OfflineOriginMigrationStore.swift` 类业务组件被 migration **子串**误伤触发 schema 门;③ degraded 外审配方产物缺 `target_commit` → 下轮 `--verify-fixes` 找不到上轮 FAIL。

### ① 投递位置(治整类 · 不只 ship1)
- SKILL R5(b) 新红线:暂停点 markdown / user_card 必须是**回合最后一条输出 · 其后零工具调用**;伴随的监控/标记类命令(pause-mark / await-merge)一律**先执行(后台/静默)再贴**。
- ship-stage §5 次序翻转:先后台启动 await-merge(30s 轮询不阻塞)→ 再把两段作为回合终文贴出;输出格式红线清单补第三条(必须是回合终文);卡片模板行改「已后台启动」。
- push emit `next_action_brief` 同步翻转(消费时点):①先启动 ②再贴 · 卡片后零工具调用 ·「次序不可倒」保留(现覆盖两层次序:监控先于卡 · 卡先于总结)。

### ② migration↔schema 门精确化
- 子串 `"migration" in f` → `_MIGRATION_PATH_RE`(目录级:`migrations/` `migration/` `migrate/` `alembic/`)—— 业务组件文件名含 Migration 不再误伤。

### ③ external-review degraded 配方
- frontmatter 必含清单补 `target_commit: <commit>` —— `--verify-fixes` 增量重验能锚到上轮。

### 验证
- 新增 test_ship_pause_delivery_v8275(5:业务组件不匹配 / DB 路径匹配〔含 Rails·Flyway·alembic〕/ hint 三关键词 / SKILL 投递位置 / 配方 target_commit)· pytest 938 passed。
## v8.276 · stage 耗时活动挖掘 · 扣跨 session 空闲 + 计时链路修 bug

> 用户令:仔细审当前统计逻辑,没别的问题再落扣除。审计结论:`duration = completed_at − started_at` 纯墙钟,而 AI 干活期间 state.py 不被调用(dev 只 start/complete 两次打点)—— 干活中途合上电脑过夜不是 R5 暂停、pause-mark 抓不到、也没法 mark(AI 那时没在跑),整段被算成「AI 自主」(实证 aon-core `goal 1012m / await +3m`)。直接扣一个数做不到,需活动信号。

### 活动时间戳挖掘(治主问题)
- `_mine_active_minutes`:stage 窗口 [started, completed] 内取 **git commit(committer-date)+ 产物 mtime(PRD/TECH/REVIEW/dispatch_log)+ round 边界** 作活动信号 · 排序后相邻间隔 ≤ `idle_threshold_minutes`(默 30 · localconfig 可调)累加为 `active_minutes` · 间隔 > 阈值判空闲扣除。
- 🔴 best-effort:窗口内无中间活动信号 / 异常 → 返 None(回退 duration−await · 不硬伤);`active ≤ span` 封顶。
- 消费:`_timing_split` / `_stage_durations` 优先 `active_minutes`(已排空闲含 R5 暂停 · await 仅作标签单列);ship §16 台账口径同步(`total_wall − ai − await = 未标记挂机空闲` · 不再冒充工作)。

### 顺带修计时 bug
- ② restart 重置计时锚:`started_at = now` + `await_minutes = 0`(旧逻辑保留原 started_at → duration 跨越已废弃首次尝试;await 残留污染 duration−await)。
- ③ 解析健壮性:duration 改宽松 `_parse_iso_flexible`(旧严格 strptime + except pass → 格式变体静默丢 duration · 整 stage 从计时消失)· 与 close_open_pause 口径统一。
- ④ 已知约束存档:pm_acceptance 整段算等待(PM 验收工作反向少算 · 保守可接受)。

### 落地
- localconfig 三点接线(json 模板 + config.md + 自愈默认表 `idle_threshold_minutes`)。
- 新增 test_active_mining_v8276(12:过夜扣除/密集全算/无信号回退/坏戳/阈值可配/split 优先 active/回退/breakdown)· pytest 950 passed。
## v8.277 · 兜底清单加 💬 大白话列

> 用户指令(截图 §7.5 兜底暂停点):兜底清单加大白话解释列。同 v8.271 AC 大白话哲学 —— 兜底清单也是暂停点上给用户拍板用的,「refresh 换发校验 pwd_ver / ROTATE_LUA」这类技术名 + 「概率×后果」+「ROI 结论」拍板者读着费劲,加一句人话(这个兜底在防什么、不做会怎样 · 用户/运营视角)。

### 改动
- 兜底名后插 💬 大白话列(读:先看名 · 紧跟人话):`兜底 | 💬 大白话 | 保护什么失败场景 | 概率×后果 | ROI 结论`。
- 两处兜底表同步保持同构(templates/tech.md §兜底清单 + stages/blueprint-stage.md §7.5 暂停块 · v8.255 教训:同类表不同构则抄写丢列)· 引导语标注大白话逐项必填。

### 验证
- 新增 test_fallback_plain_v8277(4:两表各有大白话列 / 列集同构 / 大白话紧跟兜底名)· pytest 954 passed。
## v8.278 · 给 dev 装 shift-left · 复发 finding 沉淀 + 起草写时防(治多轮收敛)

> 用户课题:评审发现问题多、多轮收敛,如何优化。数据诊断(aon-core):665 条 external findings **82% 真实**(非挑刺 · 砍不得)· 多轮集中在 **code review** 且与 feature 大小强相关 · 🔴 **finding 类型反复撞**(stale×7 / timeout×6)· 沉淀防复发回路**断了**(DEV-RULES=0)。关键不对称:goal 靠 v8.262 shift-left 已 1 轮收敛,**dev 从没装这层** —— RD 只有 §完工自查(查实现全没全)· 没有「照评审会打的失败类写」。收敛成本一大块是**反复重新发现可预防的复发类**。

### 闭环(镜像 PRD 起草思考规范 v8.262)
- **沉淀端(喂料)**:KNOWLEDGE.md 新增 **§ 🛡️ 复发防御清单**(类|失败模式|写时怎么防|复发次数|触发 Feature);review 收敛(APPROVE)后确认 findings 里**可预防的复发类**沉淀进来(同类第 2 次即入 · 已在清单还复发 = 规避法不够硬,强化它)· review-stage 规则 8 + 验证轮 brief 消费点。
- **消费端(预防)**:dev 起草**必读**该清单(上下文入口从「KNOWLEDGE 按需」升级)· dev-stage 加 🛡️ 起草思考规范(写法非环节:照失败类写、不写完等抓)· dev brief 消费点 surface。
- 判断型非机械门:一次性/纯涌现 finding 不入清单;涌现的真问题仍照抓、轮数照留 —— 只打可预防的复发子集。

### 验证
- 新增 test_dev_shiftleft_v8278(6:模板有清单 / dev brief+stage surface / review harvest / 验证轮带 / round-1 不污染)· pytest 960 passed。
## v8.279 · 安全加固/兜底降级 = external finding 过度设计高发区 · 采纳前必过 ROI

> 用户点破:安全、兜底降级也要防过度设计。缺口:blueprint §4 Architect counter-lens 已有「兜底按 ROI 审(含安全兜底)」,但 external **裁决单源 §12** + goal/review 的 finding 处理姿态只泛说「过度设计」—— 没点名 **安全加固 / 兜底降级是 external finding 里最容易过度设计的两类**:external 天然偏加防御层/校验/重试/fallback,这两类听着最「负责任」故**最难驳、最易盲采**,恰恰最该过 ROI。

### 改动(把 v8.265/266 兜底 ROI 接到 external 裁决路径)
- **裁决单源 §12**(external-model-usage.md · ① 质疑步 + 12.1 confirmed 判据):安全加固/兜底降级 finding 必过 ROI(保护场景 概率×后果 vs 实现维护成本)· 立不住 REJECT(「安全/兜底总没错」不是采纳理由)· 立得住 ADOPT + 兜底类落 §7.5 透出。
- **消费点点名**:goal external 简洁性 counter-lens · review finding 处理姿态 brief · blueprint §4 「别盲采」行(加校验→加校验/加安全/加兜底)· Architect telos 简洁性独占视角。
- 不变:「加安全/加兜底不天然正确」与别的 finding 同过质疑门;举证责任对称(ADOPT 也要实证)。

### 验证
- 新增 test_security_fallback_roi_v8279(4:裁决源/goal counter-lens/review brief/architect telos 各点名)· pytest 964 passed。
## v8.280 · 修 micro 状态机 preset-blind 死门(execute 链走不通)

> 实证 case(aifriends 4 行合规 bump 走 micro):init-feature preset=micro 建出 `flow_type="Feature" + preset="micro" + current_stage="execute"`,但 **execute-start 直接 FAIL** —— 用户被迫手动跳过状态机做完 micro 实质。根因:engine 通用 gate **用 raw `state.flow_type="Feature"`** 比 `EXECUTE_SPEC.allowed_flow_types=["Micro"]`(legacy 内部键)→ 恒 FAIL;且图查 `flow_by_type.get("Feature")` 拿 **full 图**(即便过①·execute→ship 转移错路由)。`resolve_flow_graph`/`internal_flow_key` 在 state.py 有,但 engine 的 `execute_stage_start/complete` 从没用 —— 现有 micro 测试只断言 spec 常量、**从没真跑 gate** → 漏网整整一版。

### 修复(engine gate preset-aware)
- 新增 `_internal_flow_key(state)` + `_resolve_flow_graph(state, flow_by_type)`(与 state.py resolve_flow_graph/internal_flow_key、specs _flow_key 严格同口径 · engine 不能 import state.py〔循环〕故本地实现)。
- `execute_stage_start` 三处:① allowed_flow_types 门用 `_internal_flow_key`(Feature·micro → "Micro" 匹配)· ② 转移图用 `_resolve_flow_graph`(micro 拿 Micro 图非 full)· 未知 flow_type/preset 仍显式 FAIL(保「已知流程表」措辞)。
- `execute_stage_complete` 转移同修(execute→ship 正确路由)。
- 正常 Feature·full / Bug 行为不变(`_internal_flow_key` 对它们恒等映射)。

### 测试补口
- 新增 test_micro_gate_v8280(6:resolver 单测 micro/full/bug/legacy + `_resolve_flow_graph` micro 拿对图 + **真跑 init micro → execute-start 过门** e2e)—— 补上「只断言常量、从没跑 gate」的集成盲区。
- pytest 970 passed。
## v8.281 · 起草可预防性台账列 · 评审后记录 → ship 聚合 → 年检完善 teamwork

> 用户:每次评审后记录「为什么审出这么多 + 起草考虑点该不该补」,同步到台账供后续分析完善 teamwork。这是 v8.278 dev shift-left 的诊断层 —— 把「起草考虑点缺不缺」从猜变成数据。活体验证(aon-core Postback 会话):PRD 两路冷审 11 findings,该 session 手动归因出 4 条起草考虑点缺口(在旧分支 grounding / 未 trace 真实运行时路径 / 结算路径下游未枚举 / 兜底 miss 分支未落 AC)—— 正是本列要系统化采集的。

### 机制(非门禁 · 纯数据采集)
- 新命令 `state.py review-preventability --stage <goal|blueprint|review> --preventable N --total M --missing '缺的考虑点(分号分隔)'`:评审收敛后记录 findings 可预防率 + 缺哪条起草考虑点 → 追加 `state.authoring_preventability`。
- ship 聚合 `_authoring_preventability_summary`(跨评审求和 + 缺项去重)→ emit `ledger_authoring_preventability` → PROCESS-LEDGER 新列「🛡️ 起草可预防性(可预防/总·缺考虑点)」(rightmost · append-only schema · ledger-migrate 自动加列)。
- review harvest(v8.278 rule 8)+ 验证轮 brief + ship §16 台账口径接线;判据同 v8.278/279(findings 82% 真·砍轮=漏 bug·真杠杆=起草挡掉可预防子集)。
- **消费方 = 年检**:跨 feature 看「缺的考虑点」复发 → 补 PRD/TECH 起草考虑点(反复缺=真缺口补框架)· 全 emergent = 别动(避 v8.266 一刀切)。没记录列留空(有效前缀 · 非门禁)。

### 验证
- 新增 test_authoring_preventability_v8281(6:聚合去重/记录追加/非门禁/表头分隔一致)· pytest 976 passed。
## v8.282 · PRD 起草思考规范补 2 条普适缺口(Postback case 归因)

> aon-core Postback 会话:PRD 两路冷审 11 findings,归因出 4 条起草考虑点缺口。按 v8.281 纪律筛(普适→补框架 · 情境/项目→进台账/KNOWLEDGE):① 在 ship 目标分支 grounding 和 ④ 兜底 miss 分支落 AC 是**普适 PRD 写作陷阱**(任何项目都会犯 · 单个锋利 case 足以过门),补进框架;② trace 运行时路径(情境)进台账观察、③ 结算下游枚举(项目特定)进 aon-core KNOWLEDGE,不动框架。

### 补入 prd.md 🧠 起草思考规范(+ goal-stage 镜像 + goal brief 同步)
- **① 依赖读真实代码 → 精确化**:「在**当前 worktree(ship 目标分支)**读,不吃跨分支/记忆的旧调研」—— 实证:PRD 基于 fix 分支旧调研写、staging 领先 233 commits → 状态码 404→422、rejected 桶去向全错(EXT-2/EXT-4)。
- **④ 兜底 line 加**:「**未命中/坏输入分支必须和命中分支一起落 AC**」—— 只写 happy path、miss 是大概率真实分支却漏进 AC = 冷审必打(EXT-2/PL-4)· 接 v8.279 兜底高发区。
- 不补:② trace 运行时(situational · 台账观察)· ③ 结算下游枚举(aon-core 项目 KNOWLEDGE)。

### 验证
- test_authoring_preventability +3(gap1 ship 分支 / gap4 miss AC / brief 双带)· pytest 979 passed。
## v8.283 · 模板减法批次一 · 砍掉限制模型能力发挥的约束(prd/tech)

> 用户课题:随着模型越来越聪明,这些规则是否反而有负向影响?讨论后确立**按规则类型分衰减速率**的判据 —— 不衰减必保留:① 证据/验证(信任架构:模型越强、主张越有说服力,越需要证明而非被相信)② 独立采样(相关盲区是统计属性非智力属性)③ 用户主权(谁决定 ≠ 谁能干)④ 纯机械操作;随模型变强而衰减可砍:⑤ 手段规定(HOW-to)⑥ 能力上限 ⑦ 教学示例 ⑧ 重复 ⑨ 环节化自检。本版按判据做 prd.md / tech.md 的减法,**门禁与暂停点一条未动**。

### prd.md 393 → 325 行(-68)
- 🔴 **砍能力封顶**(判据⑥ · 最锋利的一处):`❌ Read 5+ 个文件 / 1000+ 行`、`时间预算:5-10 min`、`不超过 10 min` —— 这是**直接给调研深度设天花板**,且与 v8.282 刚加的「在 ship 目标分支读真代码」**自相矛盾**(那个 aon-core Postback case 翻车根因恰恰是 grounding 不够深)。改为「读多深 / 怎么找 / 读几个文件由 AI 按本 feature 判断」。
- 砍 Step1-4 调研流程(判据⑤ 43 行 → 12 行):目标(把真实代码现状内化)+ 边界(只读不输出 / 不写技术细节 / code_context_read 痕迹)保留,HOW 交还模型。
- 砍三个完整 mermaid 示例(判据⑦ · 保留「什么时候必须画图」的触发判据 —— 那是判断)。
- 砍通用 checklist 的 AC 块(判据⑧ · 与 §验收标准表 + goal-complete 机器校验 100% 重复)。
- 「起草后必做自查」→「PM 自查字段(机读 · 非环节)」(判据⑨ · v8.263 已裁定「不是加自检环节,是写的时候就这样想」· 这是幸存的同类物;PRD-REVIEW 消费的机读字段保留)。
- 压缩 adversarial_self_check 的两个 worked example(规则本身属判据① 原样保留)。

### tech.md 277 → 238 行(-39)
- 砍填充示例(判据⑦):字段表 4 行(RFC 5322 等)· 跨层映射示例 · 错误处理表 4 行(压成「至少想过这几类」)· 文件树 · mermaid 时序图。
- 砍 TDD 粒度表 + ❌✅ 示例(判据⑤ · dev-stage v8.218 早把 TDD 从强制降为「强烈建议」,tech.md 没跟上)· 保留粒度原则一句。
- 完工自查去掉与机器门 100% 重复的两项(判据⑧ · test exit-code / commit changeset 已由 dev-complete 物化校验)。

### 一条未动(判据 ①②③④ 点名保留)
兜底 ROI 清单 · 现状基线 + decisive 前提核验 · 变更最小化四问的产出要求 · Schema 影响分析 · FK 决策 · 不静默吞异常 · 完工自查(review 真读它 = 产物契约非自检仪式)· 机读块 / verify-ac / AC 大白话机器校验 · 既有行为变更必入待决策项 · 「模板是地板不是天花板」。

### 验证
- 新增 test_template_slimming_v8283(12:封顶不得回归 / HOW-to 不得回归 / grounding 目标仍在 / 证据契约仍在 / 用户主权仍在 / 教学示例已清 / 核心契约仍在)· pytest 991 passed。
## v8.284 · 四段结构转正(解锁推广)+ 批次二 stage 减法

> 承 v8.283。审计挖到**推广卡死的根因**:`STAGES.md §3` 至今**必含**「怎么做 + 质量基线」两段 —— 已迁移四段结构的 dev/review/goal **反而不符合书面规范**,未迁移的 test/panorama_sync/pm_acceptance/diagnose **是在忠实遵守旧条款**,不是偷懒。v8.218 试点时写下「四段结构进 STAGES.md 定为标准」这一步没做,推广就此卡在 3/13 达六十余版。

### ① STAGES.md §3 四段结构转正
- 必含段改为:`① 目标(telos)` / `② 硬规则(白名单 · 每条一行 why)` / `③ 建议手段菜单(AI 自选 · 不强制 · 可省)` / `④ Output Contract` / `相关`。
- 明写 **②硬规则保留判据**(治结构风险不教干活):证据/验证 · 独立采样 · 用户主权 · 纯机械操作;**不该进②的**:怎么调研/怎么拆任务/怎么写代码(→③或交还模型)· 通用工程规范(→ `standards/` + 项目 `DEV-RULES.md`)。
- 明写**删「怎么做」与「质量基线」的理由**:前者是 HOW-to 教程「把强模型的地板变天花板」(v8.218 原话);后者把②的规则再复述一遍(实测未迁移文件因此把同一规则讲 2-3 遍)。**叙事在②一次 · 机器语法在④一次 · 没有第三处**。

### ② 批次二 stage 减法(门禁/暂停点一条未动)
- **ui-design 244 → 188**:🔴 21 行交互/视觉细则(hover/focus-visible/WCAG 4.5:1/触控 ≥44px/tabular-nums…)压成 **5 条判据** —— 原文自陈理由是「模型对交互体验缺天生判断力」,该前提已随模型能力失效;**v8.263 裁定的最后一处漏网环节化自检**(Designer 自查报告 A 段逐项过)改写法注;删「与老模式对比」论证表 / preview.sh 内部实现 / 工具面板 12 行设计品味论证与版本纠错史 / 纯目录式反模式清单 / 框架维护者 TODO;`roles/designer.md` 指针同步。
- **blueprint 120 → 98**:🐛 **修真实缺陷** —— §3 与 Output Contract 曾给 TECH.md **9 段 vs 5 段两份互相矛盾的清单**(「指针 + 复制被指向内容」的漂移实例);消除该模式(结构以模板为单源)· R5 三选项改引用式(与 ui-design 统一口径)· 删与 §4/SOP 重复的冷审与闭环条。
- **ship 235 → 221**:只砍旁白 —— 版本考古(旧两-MR 十二版沿革)· archive/ship-finalize 内部实现清单 · 投递次序**三处各说一遍**收敛为单源 · active_minutes 算法(同行已明写「不肉眼算」)· 已废弃配置墓碑 · 框架维护者 TODO。**门禁、命令序列、R5 暂停点、git add 红线一条未动**。

### ③ 兜底清单机制升级(v8.277 手段迭代)
- 原手段「blueprint 与 tech.md 两表同构」→ **单源 + 指针**(blueprint 改「照抄 TECH §兜底清单原样贴出 · 含 💬 大白话列」)。目的不变(暂停点贴出的表别丢列),但**只有一处定义才不会漂** —— 同一文件里刚实测到该模式的漂移(上述 9 段 vs 5 段)。测试同步为新不变式。

### 验证
- 新增 test_stage_slimming_v8284(12:四段结构转正 / 旧条款已废 / 判据成文 / 前端细则已删但判据保留 / 环节化已改写法 / 物化闸与主权暂停点保留 / blueprint 矛盾已修 / ship 门禁全在)· pytest **1002 passed**。
## v8.285 · 四段结构推广完成(11/13)+ standards 减法

> 承 v8.284 解锁。**批次三**:除两个记录在案的例外,全部 stage 迁到四段结构。**standards 减法**:按「与模型默认行为的距离」判据砍 —— 模型默认就会的(零价值·纯税)砍、模型不可能知道的(信息)留、**模型默认会做反的(最高价值·模型越强越需要)** 一条不动。

### 批次三 · 四段结构推广(3/13 → 11/13)
| stage | 行数 | ②硬规则 |
|---|---|---|
| test | 179 → **112**(-37%) | 9 条 |
| panorama-sync | 112 → **73**(-35%) | 5 条 |
| pm-acceptance | 107 → **77**(-28%) | 4 条 |
| ui-design | 188 → **175** | 8 条(补回被漏的分层同构律领域模型) |
| blueprint | 98 → **83** | 9 条 |
| browser-e2e | 65 → **55** | 5 条 |
| diagnose | 67 → **65** | 7 条(③整段省略 · 原文本就没水分) |
| execute | 38 → **42** | ②③ 归位(原写反:②=自主/③=边界) |

- **记录在案的例外**(STAGES.md §3 明写 · 测试守护「不许有沉默的例外」):`ship-stage.md`(主体是命令序列 + 物化门禁的**操作手册**,四段治的是 HOW-to 教程不是必要操作次序)· `blueprint-lite-stage.md`(v8.223 已废弃)。
- **顺带修断链**:删 heading 导致 6 处 `§ 测试体系` / `§ SOP` / `§ 怎么做` cite 失效(test-report / browser-test-report / e2e-registry / specs brief)· 全部改指四段段名;`test-baseline --add` 的 `--test-id` + `--reason` 必填在旧文档漏写,补齐与 CLI 一致。

### standards 减法 1773 → 1290(-27%)
- **common.md 767 → 354**:🔴 砍 **RD 自查规范 + 报告模板 216 行** —— 全库**零机器消费者**(grep 无任何工具校验它)、零文档引用、与 `tech.md §完工自查`(review 真读)职能重复。**但抢救两条真规则**:Build 必跑通才进 Code Review(证据类硬门)+ worktree lazy-install 缺 build 工具链(真踩坑)。另压缩 §二代码架构规范(SOLID/分层教科书)· §四D QA 检查项(与 verify-ac + review 覆盖方向重叠)· §五 mermaid 语法。
- **backend.md 725 → 655**:TDD 手艺单源 `tdd.md`(它本就声明整段吸收)· 集成测试报告模板压成字段清单。
- **对照组保留**(判据:模型默认会做反的 = 最高价值):`默认避免 FK`(模型训练默认「加 FK 保证引用完整性」· 本框架明确逆着走)· 降级/兜底必打 WARN 日志 · 统一响应格式与状态码表 · 测试脚本两层结构 · scratch 路径约定 · **Designer 自查**(有 `verify-panorama.py` 物理校验 → 判据①保留,与被砍的 RD 自查形成对照)。
- 全部入链锚点验过不断链(prd.md→§五 · verify-panorama→§四B · ship/conventions→§六)。

### 验证
- 新增 test_standards_slimming_v8285(13:RD 自查已删 / 抢救规则仍在 / Designer 自查保留 / 逆默认规则保留 / 锚点不断链 / **四段结构推广守护:全 stage 合规 + 例外必须写进标准**)· v8.284 两处**措辞脆断言**改实质导向。pytest **1015 passed**。
## v8.286 · standards 硬规则白名单 + 读取路径接通(工程规范并集 · 项目优先)

> 承 v8.285。用户设计:**AI 读「框架工程规范 + 项目 DEV-RULES」的并集,冲突以项目为准**。落地时**没有新建 `dev-rules-teamwork.md`** —— `standards/` 本就是框架级那层(DEV-RULES 模板早写明分工),再造一个会成**第三个家**(v8.284 刚实测过「指针+复制」的漂移)。真问题是**读取路径不对称**:项目 DEV-RULES 是必读、框架 standards 不是,所以框架自己的规范只能被复制进模板才到得了模型(实测同一条日志规则曾活在三处)。

### ① `standards/HARD-RULES.md`(47 行 · 唯一必读)
- **收录判据 = 与模型默认行为的距离**(只收两类):**逆默认**(模型会做反的 —— 它越强越笃定,越需要明确逆着写)· **不可知**(框架/项目约定 = 信息不是规范)。**模型默认就会的一律不收**(REST/SOLID/TDD 步骤/mermaid/WCAG 细则)—— 收了就是注意力税。
- 逆默认 9 条:默认避免 FK(项目可覆盖)· 降级/fallback 必打 WARN(缺失阻塞 CR)· 三方异常必 ERROR · 不静默吞异常 · **两个 adapter 才抽象**(模型默认提前抽象)· 安全/兜底必过 ROI · NEVER refactor while RED / 禁 horizontal slicing / 禁 mock 自身内部方法 · TDD Iron Law(例外须用户同意)· ≥3 次失败即升级。
- 不可知 7 条:scratch 根与 feature_id 纪律 · `[DEBUG-…]` 前缀 + ship 前 grep · 测试脚本两层结构 · 结构化日志必填字段 · 统一响应格式与状态码 · 迁移命名优先级链 · Build 硬门。
- 分册(common/backend/frontend/tdd/external/scripts-policy)降为**按需查**,不要求通读。

### ② 读取路径接通(这才是原来缺的)
- blueprint ②1 + dev ②1 改为:**工程规范 = `standards/HARD-RULES.md`(必读)+ 项目 `DEV-RULES.md` 的并集 · 🔴 冲突以项目为准**。
- `templates/dev-rules.md` 边界表同步(项目侧视角:冲突以本文件为准)。
- **删最后一处同源副本**:tech.md 的日志规则正文 → 改指白名单(该规则原散在 standards + 模板两处)。

### ③ standards 深度精简 1290 → 1135(累计 1773 → 1135 · **-36%**)
- backend 655 → 551:日志级别表与 JSON 示例(模型默认就会)· API 响应示例 · FK 理由 10 行压成 2 行(**逆默认规则的 why 必须留** —— 否则模型会反驳或"修正"它,只是不必铺开)。
- tdd 127 → 93:RED-GREEN-REFACTOR 5 步教程删,只留框架强调的两点(红要真红 / 一绿点一 commit)。
- frontend 154 → 90:测试规范流程教程删,留项目约定的阈值与清单(覆盖率 / 分层 / 必测场景)。
- WCAG 细则与 ui-design 刚砍的 rubric 同类,但 frontend 那份含「禁 div onClick / 禁 aria-hidden 键盘陷阱」等**逆默认**项,保留原样。

### 验证
- 新增 test_hard_rules_v8286(9:白名单够短可必读 / 并集与优先级成文 / 收录判据成文 / 逆默认 6 条在 / 框架约定 5 条在 / blueprint+dev 读取路径已接 / dev-rules 模板同步 / 模板副本已改指针 / 分册总量)· pytest **1024 passed**。
## v8.287 · TDD 手段规定整体撤除 · 只管结果(怎么测 AI 自觉)

> 用户:「TDD 是否不用写到规范里了,加一句确保每个 TC 用例都有对应实现即可」+「至于怎么做 TDD AI 自觉」。TDD 是**手段**,正是判据⑤(衰减类)的典型 —— 模型早已内建。框架该管的是**结果**,而结果已有机器门与评审兜着,所以撤手段不开洞。

### 撤除(手段规定)
- `standards/tdd.md` **93 → 42 行**:删 Iron Law(无失败测试不写实现)· RED-GREEN-REFACTOR · 自检清单 · 反模式 · **「跳过 TDD 须用户同意」的例外机制**(TDD 不再强制,例外机制自然失去意义)。
- dev ③菜单:「TDD 红绿循环 = 强烈建议的默认」→「**测试节奏 AI 自定**」(TDD 红绿 / 先骨架后补边界 / test-after 自选)。
- tech.md `## TDD 开发计划` → `## 测试与实现计划` · 节奏「AI 自定」;dev brief 目标行、`FLOW_STAGE_CHAIN` dev 描述、`roles/rd.md` telos、STANDARDS.md 路由表同步。

### 保留(结果规则 · 三条)
1. 🔴 **每个 TC 用例必须有对应实现** —— AC↔TC 由 `verify-ac.py` 管,**TC↔实现这一跳没有机器门**,靠本条(TC 写了没实现 = 需求链最后一米断掉,而「测试全绿」会盖住它)。
2. 🔴 **测试必须真断言 · 禁 mock 被测组件自身内部方法**(防假绿)——*模型默认倾向:为了让测试过,把正要验的那段 mock 掉。恒绿空壳测试比没测试更危险(门禁/评审/验收同时失效)。*
3. 🔴 **同一处失败修复 ≥3 次 → 停下升级**(这条**不是 TDD 规则**,是排障纪律 —— 模型默认会一直试)。
- HARD-RULES §一 的两条 TDD 方法论换成上述①②(③本就在)· tdd.md 补「结果由谁保证」表(verify-ac / test-exit-code + 差分基线 / 不走捷径 + 外审测试真实性 / TECH §测试策略)。

### 为什么撤手段不开洞(核实过)
假绿是唯一真风险,而它有三道结果侧防线:test-stage ②「不为凑 exit-code=0 走捷径」(skip 必含 reason · 不标 xfail)· review 外审**必覆盖**「测试真实性与覆盖」· review ③菜单「测试质量抽查(是否真断言 · 假绿检测)」。本版再加白名单第 ⑦ 条兜底。

### 验证
- 两处旧断言(锁 TDD 措辞)更新为新状态:白名单断言改结果规则 · v8.283 的「强烈建议的默认」改为**断言其不存在** + 断言「AI 自定 / 每个 TC 有对应实现」。pytest **1024 passed**。
