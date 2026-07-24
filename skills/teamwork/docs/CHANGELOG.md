# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.281 · 起草可预防性台账列 · 评审后记录 → ship 聚合 → 年检完善 teamwork

> 用户:每次评审后记录「为什么审出这么多 + 起草考虑点该不该补」,同步到台账供后续分析完善 teamwork。这是 v8.278 dev shift-left 的诊断层 —— 把「起草考虑点缺不缺」从猜变成数据。活体验证(aon-core Postback 会话):PRD 两路冷审 11 findings,该 session 手动归因出 4 条起草考虑点缺口(在旧分支 grounding / 未 trace 真实运行时路径 / 结算路径下游未枚举 / 兜底 miss 分支未落 AC)—— 正是本列要系统化采集的。

### 机制(非门禁 · 纯数据采集)
- 新命令 `state.py review-preventability --stage <goal|blueprint|review> --preventable N --total M --missing '缺的考虑点(分号分隔)'`:评审收敛后记录 findings 可预防率 + 缺哪条起草考虑点 → 追加 `state.authoring_preventability`。
- ship 聚合 `_authoring_preventability_summary`(跨评审求和 + 缺项去重)→ emit `ledger_authoring_preventability` → PROCESS-LEDGER 新列「🛡️ 起草可预防性(可预防/总·缺考虑点)」(rightmost · append-only schema · ledger-migrate 自动加列)。
- review harvest(v8.278 rule 8)+ 验证轮 brief + ship §16 台账口径接线;判据同 v8.278/279(findings 82% 真·砍轮=漏 bug·真杠杆=起草挡掉可预防子集)。
- **消费方 = 年检**:跨 feature 看「缺的考虑点」复发 → 补 PRD/TECH 起草考虑点(反复缺=真缺口补框架)· 全 emergent = 别动(避 v8.266 一刀切)。没记录列留空(有效前缀 · 非门禁)。

### 验证
- 新增 test_authoring_preventability_v8281(6:聚合去重/记录追加/非门禁/表头分隔一致)· pytest 976 passed。

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

## v8.279 · 安全加固/兜底降级 = external finding 过度设计高发区 · 采纳前必过 ROI

> 用户点破:安全、兜底降级也要防过度设计。缺口:blueprint §4 Architect counter-lens 已有「兜底按 ROI 审(含安全兜底)」,但 external **裁决单源 §12** + goal/review 的 finding 处理姿态只泛说「过度设计」—— 没点名 **安全加固 / 兜底降级是 external finding 里最容易过度设计的两类**:external 天然偏加防御层/校验/重试/fallback,这两类听着最「负责任」故**最难驳、最易盲采**,恰恰最该过 ROI。

### 改动(把 v8.265/266 兜底 ROI 接到 external 裁决路径)
- **裁决单源 §12**(external-model-usage.md · ① 质疑步 + 12.1 confirmed 判据):安全加固/兜底降级 finding 必过 ROI(保护场景 概率×后果 vs 实现维护成本)· 立不住 REJECT(「安全/兜底总没错」不是采纳理由)· 立得住 ADOPT + 兜底类落 §7.5 透出。
- **消费点点名**:goal external 简洁性 counter-lens · review finding 处理姿态 brief · blueprint §4 「别盲采」行(加校验→加校验/加安全/加兜底)· Architect telos 简洁性独占视角。
- 不变:「加安全/加兜底不天然正确」与别的 finding 同过质疑门;举证责任对称(ADOPT 也要实证)。

### 验证
- 新增 test_security_fallback_roi_v8279(4:裁决源/goal counter-lens/review brief/architect telos 各点名)· pytest 964 passed。

## v8.278 · 给 dev 装 shift-left · 复发 finding 沉淀 + 起草写时防(治多轮收敛)

> 用户课题:评审发现问题多、多轮收敛,如何优化。数据诊断(aon-core):665 条 external findings **82% 真实**(非挑刺 · 砍不得)· 多轮集中在 **code review** 且与 feature 大小强相关 · 🔴 **finding 类型反复撞**(stale×7 / timeout×6)· 沉淀防复发回路**断了**(DEV-RULES=0)。关键不对称:goal 靠 v8.262 shift-left 已 1 轮收敛,**dev 从没装这层** —— RD 只有 §完工自查(查实现全没全)· 没有「照评审会打的失败类写」。收敛成本一大块是**反复重新发现可预防的复发类**。

### 闭环(镜像 PRD 起草思考规范 v8.262)
- **沉淀端(喂料)**:KNOWLEDGE.md 新增 **§ 🛡️ 复发防御清单**(类|失败模式|写时怎么防|复发次数|触发 Feature);review 收敛(APPROVE)后确认 findings 里**可预防的复发类**沉淀进来(同类第 2 次即入 · 已在清单还复发 = 规避法不够硬,强化它)· review-stage 规则 8 + 验证轮 brief 消费点。
- **消费端(预防)**:dev 起草**必读**该清单(上下文入口从「KNOWLEDGE 按需」升级)· dev-stage 加 🛡️ 起草思考规范(写法非环节:照失败类写、不写完等抓)· dev brief 消费点 surface。
- 判断型非机械门:一次性/纯涌现 finding 不入清单;涌现的真问题仍照抓、轮数照留 —— 只打可预防的复发子集。

### 验证
- 新增 test_dev_shiftleft_v8278(6:模板有清单 / dev brief+stage surface / review harvest / 验证轮带 / round-1 不污染)· pytest 960 passed。

## v8.277 · 兜底清单加 💬 大白话列

> 用户指令(截图 §7.5 兜底暂停点):兜底清单加大白话解释列。同 v8.271 AC 大白话哲学 —— 兜底清单也是暂停点上给用户拍板用的,「refresh 换发校验 pwd_ver / ROTATE_LUA」这类技术名 + 「概率×后果」+「ROI 结论」拍板者读着费劲,加一句人话(这个兜底在防什么、不做会怎样 · 用户/运营视角)。

### 改动
- 兜底名后插 💬 大白话列(读:先看名 · 紧跟人话):`兜底 | 💬 大白话 | 保护什么失败场景 | 概率×后果 | ROI 结论`。
- 两处兜底表同步保持同构(templates/tech.md §兜底清单 + stages/blueprint-stage.md §7.5 暂停块 · v8.255 教训:同类表不同构则抄写丢列)· 引导语标注大白话逐项必填。

### 验证
- 新增 test_fallback_plain_v8277(4:两表各有大白话列 / 列集同构 / 大白话紧跟兜底名)· pytest 954 passed。
