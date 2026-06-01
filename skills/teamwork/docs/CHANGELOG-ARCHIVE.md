# Changelog Archive(v8.57 → v1)

> 📦 **历史归档**:本文件保存 teamwork **v8.57 及更早**的全部 changelog(含 v7/v6/…/v1 等 v8.0 之前的旧系统)· 仅供追溯,**不再维护**。
> 现行 changelog(最近 N 版 · v8.58+)见 [CHANGELOG.md](./CHANGELOG.md)。
> ⚠️ v8.0 是「范式切换 · 不向下兼容」的重构 —— **v7 及更早描述的是已不存在的旧系统**,其机制/命令/红线编号均不适用于现行 v8。

---

## v8.57 · UI 预览静态服务单 hub(治本 same-stack 预览端口冲突 + 跨 session 可访问 · 用户 case · dev-only)

> 用户 2026-05-30:"同栈项目预览稿无法直接预览 · 需启动服务 · 需要一个机制让各 session 的 UI 预览稿可访问 · 要考虑并行 worktree · 多终端开发端口冲突。"

### 根因:3 个真实痛点

1. **`file://` 打不开 same-stack 预览**:v8.56 same-stack 预览是 preview-project 编译出的 ES-module bundle · `file://` 因 CORS 不加载 module(browse 停 about:blank · CW-F002 已踩)→ 必须 HTTP server。
2. **裸 `python3 -m http.server` 端口冲突**:并行 worktree / 多终端各自起服务抢同一端口(8799…)· 互相占用。
3. **预览稿跨 session 不可访问**:每个 session 自起的服务彼此不知道 · 没有统一入口看"全机有哪些预览稿在跑"。

### 方案:单 hub(治本)

- **全机唯一一个常驻 hub 进程**·绑一个端口(默认 8799 · 占用则顺延扫 60 个)· detached 脱离终端(终端关了仍活)· 仅 `127.0.0.1` 不对外。
- **共享 registry**(`~/.teamwork/preview/registry.json` · 落 $HOME → 跨 worktree/终端/session 共享):slug → 预览目录映射。
- hub 按路径前缀 `http://127.0.0.1:<port>/<slug>/` 分发到各预览目录 · **后续 session 不再起新 server · 只注册自己的目录 + 复用同一 hub → 永不端口冲突**(竞态:进 flock 锁内二次探活 · 防双 hub)。

### 新增 `tools/preview.py`(独立元工具 · parallel update.py / bootstrap.py)

| 子命令 | 作用 |
|----|------|
| `serve --dir <编译产物目录>` / `--feature <feat_dir>` | 解析预览目录(`--feature` 读 UI.md `pages_changed[].panorama_file` / `feature/preview`)· 注册 + 确保 hub 起 · 返 `url`/`page_urls` |
| `list` | hub 状态 + 全部已注册预览 + URL(跨 session 找别人预览稿) |
| `stop --all` / `--slug X` / `--prune` | 停 hub(registry 保留)/ 注销单个 / 清 stale |
| `run-hub --port P` | [隐藏] detached 子进程实际跑 server |

安全:路径穿越守卫(raw `..` + URL-encoded `%2e%2e` 均 403)· 仅 bind 127.0.0.1。

### 接线

| 文件 | 内容 |
|----|------|
| `tools/preview.py` | 新增(~470 行) |
| `stages/ui-design-stage.md` | step 3 same-stack 验证从裸 `python3 -m http.server` → `preview.py serve`(标注会端口冲突 · 不要手动起)· step 5 决策参考给 hub url · 新 § 预览服务 hub(子命令表 + `base:'./'` 相对资产 + 仅本机 note) |
| `roles/designer.md` / `templates/ui.md` | HTML 预览验证改 preview.py serve + `base:'./'` |
| `SKILL.md` | 文档清单加 tools/preview.py 行 |
| 测试 | `tools/tests/test_preview.py` 新增 14 例(slugify / register / prune / feature 解析 / e2e serve+fetch / **hub 复用不抢端口** / 路径穿越 403 / list / stop)· 全 PASS |

### 🔴 same-stack build 注意

preview-project 的 build 必须用**相对资产路径**(vite `base:'./'` 或等价)· 否则 hub `/<slug>/` 前缀下 `/assets/*` 绝对路径 404。

---

## v8.56 · ui_design same-stack 重定义 = docs/design/preview-project + 可视全景物化(用户 case CW-F002 · dev-only)

> 用户 2026-05-30(supersdk CW-F002 · Tailwind→antd 迁移):"你怎么没出全景设计?" + "应在 design 目录建 antd 项目编译静态 HTML" + "目录应为 子项目/docs/design/preview-project(与实际前端项目同技术栈)+ 设计规范"。

### 根因:3 个真实 gap

1. **cut-corner 有缝**:same-stack 的可视交付物没物化校验 —— `_evidence_panorama_artifact` 对 same-stack **直接 `return True`**(仅校验 UI.md 自查)→ AI 拿"验证器只校验 UI.md""same-stack 不要求 preview"当借口,只写 markdown token 表、零可视全景。最低物化闸被当成免做交付物许可。
2. **same-stack 污染真实工程 + 新库鸡蛋问题**:旧 same-stack = 在真实前端 app 加 `/design/*` 路由 → 污染工程;且本 Feature 正要引入 antd(还没装)→ "用自身组件预览 antd" 先有鸡还是蛋。
3. **static-html 介质差**:手搓 CDN ≠ 真实组件渲染。

### 用户决策

| 决策 | 内容 |
|----|------|
| ① **重定义 same-stack** | 实现从「真实 app 内 /design 路由」改成「`{子项目}/docs/design/preview-project` 同栈独立项目(自带目标库)→ `npm run build` → `docs/design/preview/*.html`」· 不污染工程 + 解新库鸡蛋问题 · 仍 2 介质(same-stack + static-html)· 老 Feature 向后兼容 |
| ② **可视全景物化** | 编译出的静态全景 `docs/design/preview/*.html` 必产 + ui_design-complete 校验存在(治 cut-corner) |

### 改动

| 文件 | 内容 |
|----|------|
| `stages/ui-design-stage.md` | same-stack 重定义(preview-project 模型 + docs/design 结构)· 硬规则加「必产可视全景」· 加 `python3 -m http.server` 验证 note(`file://` 在 browse 不加载 · 治本 CW-F002 误判"渲染正常") |
| `tools/_v8_stage_specs.py` | `_evidence_panorama_artifact` same-stack `return True` → 要求 `panorama_path/preview/*.html` 编译产物存在(缺 panorama_path / 缺 preview → FAIL) |
| `templates/ui.md` / `roles/designer.md` / `conventions.md §13` | same-stack realization 改 preview-project + http.server + docs/design/ 目录约定 |
| 测试 | TestPanoramaArtifactEvidence same-stack 3 例改(无 panorama_path FAIL / 有编译产物 PASS / 声明但没编译 FAIL)· 368 passed · 68 pre-existing(无关)· 0 regression |

---

## v8.55 · external wrapper(codex/claude)抗卡 + 超时 10min + 默认落执行日志(用户 case · dev-only)

> 用户 2026-05-29:"external wrapper 执行 codex 有时卡住(疑似 codex 升级提示)· 是否有参数禁用 · 超时 5min→10min · codex 执行输出默认写文件方便排查跑不起来。"

### 改动(`tools/state.py` external review 封装)

| 项 | 处理 |
|----|------|
| **抗卡(升级提示)** | codex / claude subprocess 加 `stdin=subprocess.DEVNULL` —— 闭 stdin · 任何交互/升级提示等输入立即 EOF 不再卡(治本 hang)。**诚实**:codex 没有我确认过的"禁用升级检查" flag,不臆造;DEVNULL 是通用抗卡机制,日志会显示是否真是升级提示,届时可精准加 codex config/flag |
| **超时 5→10min** | `EXTERNAL_REVIEW_TIMEOUT_SEC` 300 → 600(codex/claude 同) |
| **默认落执行日志** | 新 `_log_external_run`:每次 external review 默认写 `~/.teamwork/external-review-logs/<feature>/<codex\|claude>-<stage>-<ts>.log`(cmd/rc/耗时/timeout/stdout/stderr)· **出仓不污染 ship** · 超时/失败时把日志路径回填进 error stderr(FAIL emit 可见)· 排查"跑不起来"看这个 |

### 设计

- 日志落 `~/.teamwork/`(与 host_audit / prepare_check_audit 同处)· 不放 feature_dir(那会被 ship `git add` 带进仓)。
- `_run_claude_review` 加可选 `feature_dir/stage`(默认 None → 不写 · 保留 `_run_claude_review("prompt")` 测试签名)。
- 测试 +3(日志写入 / None 不崩 / 超时 600)· 全套 366 passed · 68 pre-existing(无关)· 0 regression。

---

## v8.54 · Feature Planning 完成必问是否提交 push(用户 case · dev-only)

> 用户 2026-05-29:"feature planning 结束时应该提示是否提交 push。"

### 根因:Step 8 提交是平铺指令 · 非显式暂停点

Feature Planning 产出(WS + 各 ROADMAP 登记 + 业务架构 if 改)是**未提交的工作树改动**。但 `feature-planning.md` Step 8 只写「git add → commit → push(用户决定)」—— 平铺指令,没框成 R5 暂停点 → AI 可能**不提示就把改动悬着**(规划白做、易丢)或擅自 commit。

### 治本:Step 8 = 必问的 R5 暂停点

- **feature-planning.md Step 8** 改成显式 R5 暂停点:规划完成必 emit「提交并 push 💡 / 先不提交 / 其他」· 不擅自 commit、也不放任悬着 · 主工作区直推或开 MR · 不走 ship。
- **planning-check checklist** 末项强化:「🔴 规划完成必 emit R5 暂停点问是否提交 push」(物化到 AI 必经的 planning-check 输出)。
- 测试:checklist 仍 5 项(改文案非数量)· 全套 363 passed · 68 pre-existing(无关)· 0 regression。

---

## v8.53 · 需连环境先读 TROUBLESHOOTING.md(用户 case AON staging DB · dev-only)

> 用户 2026-05-29:"staging 数据库怎么连在 troubleshooting.md 有定义,但是 AI 不知道。"

### 根因:env-access 路由只对"用户提到" · AI 自己需连环境时改瞎试

承 v8.52 代码调研:AI 需查 staging DB 真实 category 数据 → 但**不知连法**,grep `.env` / `dev_start.sh` / 试本地 docker / DNS 不解析 / psql 一通报错。而 **staging 连法 `TROUBLESHOOTING.md` 早有定义**。

teamwork 路由表本有「查 DB / 查环境 → TROUBLESHOOTING.md」,但语义是「**用户提到** X」(mode A triage)· AI 在**规划期代码调研 / stage 内**自己需连环境时,这条没触发 → 改即兴 grep 配置试错。且 TROUBLESHOOTING 是**用户主权**运维手册,AI 本应「按需读」却重新发明。

### 治本:AI 自己需连环境也走 TROUBLESHOOTING · 先读不瞎试

| 改动 | 内容 |
|----|------|
| **SKILL.md § 按场景路由** | 加 🔴 note:**AI 自己需连环境(查 DB/log/服务/跑运维命令)时也走 `TROUBLESHOOTING.md`**(不只用户提到 · 含规划期代码调研需 live 数据 / stage 联调)· **先读拿连接+操作方式,别凭 `.env`/启动脚本瞎试** · 用户主权手册按需读不重新发明 · 连法缺失补进它 |
| **feature-planning.md Step 1** | 代码调研块加:调研需 live 环境数据 → 先读 TROUBLESHOOTING.md 拿连接(附 AON 试错实证) |

### 设计

- 呼应设计哲学「用户主权:排查命令 → 用户填,teamwork 按需读」—— 本 case 是 AI 没「按需读」。
- **v8.53.2 强化**(用户追问"不够清晰 vs AI 没读"):根因是**passive table · AI 不主动读**(路由表加 note 对"没读"无力)→ 把提醒**物化进 `planning-check` 输出**(AI 必经、刚跑完就看到,本 case AI 确实跑了 planning-check)+ 修 `文档清单` 何时 read 列一致(原"mode A/E"太窄)。env-access 不可枚举 · 无法硬物化拦截 · 剩下靠纪律 + 必经点提醒。
- 全套 363 passed · 68 pre-existing(无关)· 0 regression。

---

## v8.52 · Feature Planning 必须结合实际代码调研(用户 case AON category · dev-only)

> 用户 2026-05-29(实战验证 case · aon-core):"feature planning 应该结合实际代码调研。"

### 根因:WS 拆解凭 spec/假设 + 轻信 sub-agent 摘要

AON「category 单源化」规划:AI 切 PL 拆出 WS-001 5 个 BL,**全凭 spec + 子项目结构假设**。用户追问"结合实际代码验证,是否有些已做完" → AI 实跑代码核验,发现**决定性事实**:
- migration 全是 schema-only(**0 INSERT**)· `offer_categories` 表为空 · partner 的"DB-first"是**空壳**永远走 fallback —— 即 ① 的真缺口是「seed 数据 + DB 校验」,不是原以为的「建接口」。
- **第一次排查的 Explore agent 误报**"migration 含 11 条 seed INSERT"(实际纯 schema)· 差点让整个 WS 拆解基于错前提。

即:Feature Planning 流程**没强制 grounded 实际代码** → AI 只在用户提示后才核验。Explore/sub-agent 读 excerpt 会漏内容,decisive 前提轻信摘要 = 拆错。

### 治本:代码调研 = Feature Planning 必经步骤

| 改动 | 内容 |
|----|------|
| **feature-planning.md Step 1** | 加「🔴 实际代码调研」:每个候选 BL 核验「已做什么/真缺口」· 反映真实完成度(不把已完成列 todo / 不把有脚手架的当 greenfield)· **decisive 前提必 Read 实际文件 · 不轻信 Explore/sub-agent 摘要**(附 AON seed 误报实证) |
| **planning-check checklist** | 首项加「拆 BL/WS 前调研实际代码现状 · 标注真实完成度 · 核验 decisive 前提」(4→5 项) |
| **templates/workstream.md** | `features[]` 加 `current_state` 字段(由代码调研填:已有脚手架/复用点 vs 真缺口)+ 设计要点 5「拆解 grounded 实际代码」 |
| **测试** | test_state planning_checklist 长度断言 4→5 · 全套 363 passed · 68 pre-existing(无关)· 0 regression |

### 设计

- 不是新机制 · 是把"凭记忆/spec 拆"纠正为"凭实际代码拆"(planning 的 R7 evidence 精神延伸到规划层)。
- `current_state` 让 WS 文档**显式记录每个 feature 的复用点 vs 真缺口** —— 拆解可审计、不重复造轮子、不漏命门。

---

## v8.51 · session 入口优先级:升级 → 补规划 → 任务(用户 case gcpdev · dev-only)

> 用户 2026-05-29(实战验证 case · gcpdev 仍跑 v8.47.1):"应该先处理升级,然后补规划,最后再处理别的。"

### 根因:多信号同时触发时无优先级 → PMO 倒置

bootstrap 同时 emit `skill_update_check: outdated`(v8.47.1→v8.50.1)+ `cold_start`(缺 teamwork-space),但:
- **SKILL.md 零优先级规则**(「升级」相关条目全是 mode-升级 即 Feature Planning/Bug · **没有 skill-版本-升级** 的处理)。
- 结果:PMO 把「升级」+「补规划」降成底部「📎 维护提醒(不阻塞)」脚注,反把「启动 BL-001」放成选项 1 —— **优先级倒置**。
- 深层:**停在旧版 = 跑旧行为** —— 连规划/冷启动逻辑本身都可能是已被新版治掉的(本 case 正是 v8.47.1 旧路由),旧版上"补规划"会白补。所以升级必须最先。

### 治本:定义 session 入口优先级 + 物化到 bootstrap 输出

| 层 | 改动 |
|----|------|
| **SKILL.md** | § bootstrap flow_gates 响应 顶部加「session 入口处理优先级」:① 升级(skill_update_check outdated · 最先 · 旧版=旧行为)→ ② 补规划(cold_start)→ ③ 任务 · **不可把 ①/② 降脚注** · 附 gcpdev 反模式实证 |
| **bootstrap.py** | emit `session_entry_priority`(检测 skill outdated / cold_start → 列有序优先级 + rule「不可降脚注」)· 物化到工具输出 · AI 跑完即见,不靠记 SKILL.md(治本:本 case AI 手里有 outdated 信号却仍忽略) |
| **测试** | test_bootstrap 加 session_entry_priority(cold_start → ②补规划 + ③任务 · 序正确 · rule 含「脚注」) |

### 设计

- **非硬 BLOCK**:升级/补规划仍是 R5 暂停点(用户可忽略/跳过)· 只是**呈现优先级** —— 先 surface 让用户拍,不埋脚注。
- 测试:bootstrap docs+emit · 全套 363 passed · 68 pre-existing failed(render+scan · 无关)· 0 regression。

---

## v8.50 · 模板瘦身:teamwork-space template↔维护规范 解耦(用户洞察 · dev-only)

> 用户 2026-05-29:"teamwork-space.md 模板里太多不必要内容 · 很多是 AI 知道就好 · 是否单独起一个维护规范.md · 模板引用一下,不耦合在一个文档,其他模板也一样。"

### 根因:模板自相矛盾 + 违 skill 边界原则

`templates/teamwork-space.md`(~200 行)每个 section 都挂一段 `>` 规则块(生命周期/状态机/硬规则/字段语义/单源声明)。但:
- **自相矛盾**:它开头写「≤1 行 · 一眼看懂全景 · 不是事件日志」,自己却塞满 meta-rules。
- **违 skill 边界原则**(本 session 早先沉淀):这些是 **AI 维护行为**,该在 spec 层,不该耦合进「会被实例化进用户项目」的模板 —— 否则项目里那份 teamwork-space.md 一复制就臃肿。

### 解耦(用户决策 A:v8.49 收尾后单独做)

| 文件 | 角色 |
|----|------|
| **新建 `docs/teamwork-space-guide.md`** | 维护规范(AI 读):核心定位 + 各 section 字段语义/硬规则 + 生命周期 + 进度统计公式 + 跨项目变更单源 + 路由权威(docs_root / 技术栈 panorama 信号) |
| **`templates/teamwork-space.md` 瘦身**(~200→~105 行) | 只留实例化骨架:section 头 + 表头 + 示例行 + 每节一句话 `<!-- 这里放什么 · 详 guide §N -->` + 顶部引用 guide |
| **`SKILL.md`** | session 入口必读段加「创建/维护 teamwork-space 的规则 → docs/teamwork-space-guide.md」(PMO 常驻可发现) |

效果:实例化进项目的 teamwork-space.md **永远精简**(骨架 + breadcrumb)· 规则单源在 skill guide(AI 读 · 不复制)。

### 范围控制(R4 不膨胀)

- teamwork-space 是**重灾户**(规则 >> 骨架)→ 本次解耦。
- `roadmap.md` / `workstream.md` / `project.md` 规则:骨架比例合理(字段语义贴着表头反而有用)→ **暂不拆**(避免为边际收益增 guide 文件)· 后续如确有需要再议。
- 测试:docs-only 改 · 全套 362 passed · 68 pre-existing failed(render+scan · 无关)· 0 regression。

---

## v8.49 · 规划模型重构:执行线 → WS → roadmap/BL → F(用户共创 · 删执行手册 · dev-only)

> 用户 2026-05-29 连环追问 → 共创:"BL / BG / 执行线 本质都是产出一组 feature,是否统一更合理?我们重新梳理 feature 规划整体流程。"

### 背景:规划概念空间过载 + 取样偏差纠错

排查发现规划层概念太多(BL / CR / BG / PENDING / 执行线 / F),关系不清。实际用量证据(joli/aon 旗舰多子项目):**执行线 7 条 + BG 23 个 + BL 947 处引用全在用**(我一度因只搜 okok/ 误判"BG 零使用",用户用 aon 纠正 → 重查确认三者都活跃)。结论:它们是**三个真实层级**,但:① BG/CR 与初始规划/执行线的边界糊;② BG.sub_features ↔ ROADMAP.BL 身份重复;③ 执行手册只在 0-1 有用,迭代期冻结(aon 执行手册停更 2 个月而 BG 活跃)。

### 用户共创的收敛模型

```
业务架构与产品规划.md(愿景 + 执行线列表 · taxonomy · 稳定)
   └─ WS-NN(product-overview/workstream/)  ← feature-planning 产物 · 承接 1+ 执行线
        └─ ROADMAP/BL-NNN(关联 WS)         ← 完成标准:feature 全写入 roadmap(原子)
────────── 规划→执行 交接 = 用户拍板 BL + prepare + init-feature ──────────
   └─ F-NNN  goal→…→ship
```

关键决策(用户逐步拍板):
- **删执行手册**:执行线降级为业务架构里的小列表(taxonomy · 不跟踪 · 不登记 WS · WS 向上 tag · 反查得索引);非开发工作 teamwork 不跟踪。
- **WS = feature-planning 产物**:不在流程外 ad-hoc 手搓;"起 WS" = 进 feature-planning(PMO 切 Product Lead)。
- **承接 1+ 执行线**(与子项目「承接执行线」多值一致)。
- **进度统计 = N 未完成 WS(规划态)+ 各 ROADMAP BL(执行态)**;WS ✅规划完成即从规划计数移除(不双计)。
- **lock 语义承旧 BG**:WS 未规划完成禁启动其子 Feature(防边规划边启动)。

### 实现(4 phase · ~13 文件)

| Phase | 改动 |
|----|------|
| **P1 核心 spec** | SKILL.md 新增「teamwork 业务流程架构(PMO 常驻认知)」锚点(根治"PMO 不知道规划模型"的反复 mis-route)· PRODUCT-OVERVIEW-INTEGRATION 重构(删执行手册必备 · 执行线入业务架构 · CHG/changes→WS · 变更级联/自下而上 reframe)· feature-planning 产出改 WS · conventions §8 加 WS-NN namespace + §4 执行线→WS→BL→F 链 · roles/product-lead 更新 |
| **P2 模板** | 新建 `templates/workstream.md`(WS · 由 change-request 泛化)+ `workstream-readme.md` · change-request 标 DEPRECATED · roadmap 加「关联 WS」列 · teamwork-space 进度统计加「未完成 WS」+ 执行线概览简化为派生视图 + 跨项目变更 CHG→WS · pl-pm-feedback 修 |
| **P3 工具接线** | planning-check 产出/planning_order 改 WS · SKILL 项目级文档信息架构加 workstream/ + 执行线路由 · bootstrap cold_start gate 措辞 执行手册→执行线列表 |
| **P4 测试发布** | test_state planning_order 断言改新链路 · 全套 pytest 362 passed · 68 pre-existing failed(render+scan · 无关)· 0 regression |

### 兼容 + 后续

- **向前兼容**:老项目 `执行手册.md` / `changes/*.md`(CHG/BG)保留可读 · 不强迁。
- **v8.50 待办**:模板瘦身 —— template(实例化骨架)↔ 维护规范(AI 行为)解耦(用户洞察:teamwork-space 模板规则过载 · 违 skill 边界原则 · 自相矛盾)。

---

## v8.48 · 治本 v8.47 冷启动路由倒置(用户 case gcpdev · 产品规划优先 · dev-only)

> 用户 2026-05-29 跑 `/teamwork`(gcpdev 项目):"预期应该指引我做项目规划 · 最终生成 teamwork-space.md 和 product-overview。" 实际 AI 出了个看板 · 把 teamwork-space.md 缺失降成「不阻塞 · 可随时补」脚注 · product-overview 没提。

### 根因:v8.47 的两处硬伤(bootstrap gate 正确触发 · 但行为/概念层错)

实测 gcpdev:`cold_start_workspace_uninitialized` gate **正确触发**了(bootstrap 层 OK)。问题在路由 + mode 接线:

| 根因 | 错在哪 |
|----|------|
| **路由倒置** | v8.47 gate action 写「进 Feature Planning 流程…生成 teamwork-space.md」· **双重错**:① teamwork-space.md 不是 Feature Planning 产出的 —— 权威流是 `product-overview`(PL 引导模式)→ ✅确认 **派生** teamwork-space.md(`PRODUCT-OVERVIEW-INTEGRATION.md:67`)· ② gcpdev 已做 Feature Planning(PROJECT/ROADMAP/sitemap)却跳过上游 product-overview |
| **mode-D 降级** | bare `/teamwork` = mode D 看板 · v8.47 接线「mode A/D/E → 轻提一句」→ teamwork-space.md 缺失成脚注 · product-overview 没出现。但 bare `/teamwork` 落未初始化项目 **恰恰是最该强引导的时刻** |
| **子系统偏向拆 ROADMAP** | 连 planning-check 也:无 product-overview 时说「可直接拆 ROADMAP」· 把产品规划上游当 optional |

### 权威冷启动顺序(PRODUCT-OVERVIEW-INTEGRATION.md 确立)

```
product-overview(产品规划 · PL 引导模式)
    ↓ 状态达 ✅ 已确认
teamwork-space.md(工作区全景 · 由 ✅确认内容派生)
    ↓
Feature Planning(拆 ROADMAP · 子项目级)
    ↓
Feature 状态机(goal→ship)
```

### 用户决策:产品规划优先 · 一律引导 product-overview · spec/wording 修正(不加新命令)

| 改动 | 内容 |
|----|------|
| **bootstrap.py** | cold_start gate action 改「产品规划优先」(① 建 product-overview → ② ✅确认派生 teamwork-space.md → ③ Feature Planning)· 按 `_po_exists` 自适应(已有 po → 直接从 ✅确认派生)· 加 `authoritative_order` 字段 · spec 指向 PRODUCT-OVERVIEW-INTEGRATION.md |
| **SKILL.md** | § bootstrap flow_gates 响应:bare `/teamwork`(mode D 无任务)→ 🔴 不当静默看板 · 首条响应强引导(即便已有 PROJECT/ROADMAP 仍 surface)· 明确「teamwork-space.md 不是 Feature Planning 产出」· 别再指用户进 Feature Planning 生成它 |
| **state.py planning-check** | `must_read` 总含 PRODUCT-OVERVIEW-INTEGRATION.md(无 po 时学冷启动初创)· 加 `planning_order` 字段 · 无-po hint 改「产品规划优先」(删「可直接拆 ROADMAP」把上游当 optional 的措辞) |
| **feature-planning.md** | 加冷启动顺序说明(本流程是下游 · teamwork-space.md genesis 在 product-overview 上游 · §2 Step 5 改 teamwork-space 指已存在后迭代非首次) |
| **PRODUCT-OVERVIEW-INTEGRATION.md** | 加 § 冷启动:首次创建 product-overview(PL 引导模式 5 步)· 治本「文档假设 product-overview 已存在 · 无 cold-start 创建入口」 |
| **测试** | test_bootstrap cold_start 3 例更新(action 改 product-overview 优先 + authoritative_order 顺序断言)· test_state planning-check 2 例更新(must_read + planning_order) |

### 与 v8.46/v8.47 的关系

v8.46(product-overview 存在→读规范)+ v8.47(teamwork-space 不存在→引导)建了 gate · v8.48 **修正 v8.47 的路由方向**(从「下游 Feature Planning」纠正为「上游产品规划优先」)。三版共同补 Feature Planning / 产品规划上游不进状态机的物化盲区(forewarn gate · 非 BLOCK · PMO 按 mode 用判断)。

---

## v8.47 · 治本新项目冷启动无引导(用户洞察 · bootstrap cold_start gate · dev-only)

> 用户 2026-05-29:"目前新项目缺少产品规划和 teamwork_space.md 生成路径 · 是否可以 session 启动检测 product-overview teamwork_space.md · 没有引导用户进入产品规划流程。"

### 根因:冷启动盲区(v8.46 的对偶)

v8.46 补了「项目**有** product-overview/ → 提示读规范」的正向门;但反向盲区还在:**新项目什么都没有**(无 teamwork-space.md / 无 product-overview/)时 · session 启动**零引导** · 用户(和 AI)不知道该先做产品规划 · 直接散做单 Feature → 缺工作区清单(子项目管理 / 待规划需求池 / 跨项目变更追踪)。

```
v8.46 gate:product-overview/ 存在 → 提示「规划类任务读规范」(正向)
        ↓ 但
新项目冷启动:teamwork-space.md 不存在 → 无任何 forewarn(盲区)
        ↓
用户不知道有 Feature Planning 流程 · AI 不主动引导 · 直接 init-feature 单做
        ↓
🔴 工作区永不初始化 · 多子项目 / 需求池 / 跨项目追踪能力缺失
```

### 用户决策:A · 两者都检 · forewarn 分强度 + Feature Planning 流程产出

| 维度 | 决策 |
|----|------|
| **检测对象** | teamwork-space.md(主判据 · 工作区初始化标志)+ product-overview/(辅:缺则提示一并建) |
| **强度** | forewarn(非 BLOCK)· bootstrap 不拦截 · 按 mode 分强度引导(mode B 强 emit R5 / A·D·E 轻提 / C silent skip) |
| **产出路径** | 引导进 **Feature Planning 流程**(跑 `state.py planning-check` + 生成 teamwork-space.md)· 不新造流程 |

### 实现

| 层 | 机制 |
|----|------|
| **bootstrap gate** | `cmd_session_bootstrap` 检 `teamwork-space.md` 不存在 → flow_gates emit `cold_start_workspace_uninitialized`(含 product_overview_status:也缺失/已存在)· 与 v8.46 product-overview gate 互补 |
| **SKILL.md 接线** | Triage 新增 § bootstrap flow_gates 响应(首条响应前必扫)· cold_start 按 mode 分强度:mode B 首条响应 emit R5 暂停点(1 进 Feature Planning 💡 / 2 跳过 / 3 其他)· 用户拍板前不擅自建文件(R5) |
| **测试** | test_bootstrap.py 加 3 例(无 ws → gate 在 · 有 ws → gate 无 · 仅 po → po_status 已存在) |

### 与 v8.46 的关系

v8.46(product-overview 存在→读规范)+ v8.47(teamwork-space 不存在→引导初始化)= 规划路径双向物化补全。两个 gate 同源(Feature Planning 不进状态机 · 无 state.py 兜底的物化盲区)· 都用 forewarn flow_gates 补(不强 BLOCK · PMO 按 mode 用判断)。

---

## v8.46 · 治本 Feature Planning 路径未物化漏洞(用户洞察 · A bootstrap gate + C planning-check)

> 用户 2026-05-28:"PRODUCT-OVERVIEW-INTEGRATION.md 这个 AI 每次会必读么 · 是否会存在 AI 没读这个文件 · 导致在一个 feature 需要规划的时候不按这个规范来。"

### 根因:v8 物化覆盖的盲区

调研确认用户担心成立:PRODUCT-OVERVIEW-INTEGRATION.md **零物化触发点**(只有 conventions.md 一个表格 reference + scan 工具列它)。深层根因:

```
v8 核心承诺:可枚举流程 → state.py 物化(主动告知 · 不靠 AI 读 spec 凭记忆)
        ↓
但 Feature Planning + 问题排查「不进状态机」(prepare.md 明说)
        ↓
退回 v7 模式:PMO 主对话凭记忆 + 自觉读 markdown spec
        ↓
🔴 PRODUCT-OVERVIEW-INTEGRATION.md / feature-planning.md 纯 spec-driven
   → AI 没读 = 不维护规划状态表 / 草稿态误影响下游 / 议题追踪缺失
```

stage 链路径(goal→ship)有 state.py 主动告知兜底,但 **Feature Planning 路径没有** —— 这正是 v8 本要消灭的"凭记忆"问题在规划路径的残留。

### 用户决策:A+C 双层

| 层 | 机制 |
|----|------|
| **A · bootstrap gate** | session 启动检测 product-overview/ → flow_gates emit「规划类任务必读规范 + 跑 planning-check」 |
| **C · planning-check 命令** | Feature Planning 物化入口(像 prepare-check)· emit 规划 checklist + 必读 + 规划状态机 |

### 实施

#### A · bootstrap.py product-overview gate

`cmd_session_bootstrap` 检测 `project_root/product-overview/` 存在 → flow_gates append:
```json
{
  "gate": "product_overview_planning_spec_required",
  "trigger": "Feature Planning / 规划类任务",
  "action": "先跑 planning-check · 必读 PRODUCT-OVERVIEW-INTEGRATION.md · 维护规划状态表 · 仅✅已确认才影响下游",
  "skip_consequence": "AI 没读 → 草稿态误影响下游 / 议题追踪缺失 · Feature Planning 无 stage 兜底"
}
```

#### C · state.py planning-check 命令(不进状态机 · emit-only)

```
state.py planning-check --project-root <abs>
```
emit:
- `product_overview_exists` + `must_read`(有 po → 加 PRODUCT-OVERVIEW-INTEGRATION.md)
- `planning_checklist`(4 条:范围判定 / 产出 PROJECT+ROADMAP+sitemap 不出代码 R6 / 拆 BL-NNN / commit-push 不走 ship)
- `entry_criteria`(关键词 + 复杂度强制升级判据)
- `key_constraints`(不进状态机 / 不出代码 R6 / BL-NNN 非 Feature ID)
- 有 product-overview → `planning_state_machine`(📝草稿/🔄讨论中/⏸️待确认/✅已确认 + 「仅✅已确认才影响下游」+ 规划状态表/议题追踪要求)

物化「你必须想这件事」—— AI 跑命令就拿到规范要点,不依赖记得读 spec。

#### spec 接线

feature-planning.md 头部加「🔴 进入本流程前先跑 planning-check」。

### 测试(3 个 planning-check + e2e bootstrap gate)

`TestPlanningCheck`:
- `test_v846_planning_check_no_product_overview`(must_read 只 feature-planning · 无 state_machine)
- `test_v846_planning_check_with_product_overview`(must_read 含 PRODUCT-OVERVIEW + 规划状态机 + 议题追踪)
- `test_v846_planning_check_checklist_and_constraints`(4 条 checklist + 不进状态机/不出代码 R6)

bootstrap gate e2e 验证(有 product-overview/ → flow_gates 含 product_overview_planning_spec_required)。

359 passed / 68 failed(pre-existing render+scan · 与本次无关)· 0 引入新失败。

### 设计哲学

把"AI 自觉读 spec"变成"工具物化提示"——这是 v8 的核心,本次补上了规划路径的盲区。R0:可枚举(checklist / 状态机 / 必读清单)进脚本,emit 给 AI;不可枚举(具体规划内容)留 AI。

### 同 commit 含 follow-up 产物

本 commit 的 test_state.py 含 spawn follow-up session 补的 `TestReadOnlyCommands`(批次1 删 TestP1ReadOnly 丢的 snapshot/validate/raw-read v8 覆盖 · 4 passed)。.gitignore 加 worktree/harness-locks ignore(teamwork repo 自身用 worktree 开发需要)。

---

## v8.45 · 全文件 review 大清理(用户「逐文件 review」· 4 agent 并行审 + 28 项发现 · 分 5 批)

> 用户 2026-05-28:"review 一下 teamwork 的逐个文件 · 看下哪些不合理 + 哪些没必要的描述需要清理"。
> 派 4 个 general-purpose agent 并行审 tools / docs / stages+standards / templates+roles+agents · 加自审根目录导航 md · 共 28 项发现 · 分 P0-P4 五批清理。

### 批次 1 · P1 删 v7 遗留 dead code + dead test(本提交 · 净删 1489 行)

**根因**:v8.0 范式切换(commit bb11e1d)从 v7 的 `enter-stage / satisfy-gate / complete-stage`(P2 命名)+ `ship-sanitize/push/...` 改为 `*-start / *-complete` + `ship-phase`,但旧实现的函数体 + 对应测试 + fixture 引用没清干净,残留至今(v8.44)。

删除内容:
- `state.py`:11 个 v7-style `cmd_*`(enter-stage / satisfy-gate / complete-stage / ship-sanitize / ship-push / ship-confirm-merged / ship-cleanup / ship-closed / add-concern / bug-frontmatter / micro-validate)+ 9 个私有 helper(_check_external_review_artifact / _gate_order_err / _ship_load / _ship_phase_err / _bug_locate / _parse_frontmatter / _dump_frontmatter / _bug_validate_ship_machine / _enum_err)+ EXTERNAL_REVIEW_STAGES 常量 = **-727 行**。全部零 argparse 注册、零 import。
- `test_state.py`:`_Base` 基类 + 6 个继承类(TestP1ReadOnly / TestP2Transitions / TestP3Ship / TestP4General / TestBugFrontmatter / TestMicroValidate)= **-370 行**。这套依赖 v8.0 删掉的 fixture `templates/feature-state.json`,**从 v8.0 起就没通过**——正是长期"97 failed baseline"的主体(其中 29 个是测上述 dead cmd 的 dead test)。
- `_feature_context.py`(169)+ `test_feature_context.py`(199):整个模块零 import。
- `_v8_stage_specs.py`:`_check_cwd_main_worktree`(24)定义后从不用。

**关键陷阱(诚实记录)**:第一次删 494-1300 整块时误删了夹在 dead cmd 中间的**活函数** `cmd_raw_read`(1014)/ `cmd_raw_write`(1036)→ build_parser NameError。git checkout 恢复后重新精确切分(dead 块不连续):删 494-1013 + 1094-1300,保留 1014-1093。教训:大块删除前必须 grep build_parser 注册 vs 区间内每个 def,不能假设"整块全 dead"。

**验证**:`test_state.py` + `test_v8_stage_specs.py` 199 passed(我改过的文件零失败)· raw-read/raw-write 运行时实测 OK · baseline 97 → 68(清掉 29 dead test · 0 引入新失败)。

**follow-up**(spawn task):删 TestP1ReadOnly 丢了 snapshot/validate/raw-read 显式覆盖 → 用 init-feature 真 fixture 补回;另查剩 68 个 pre-existing render 失败(test_render_* + test_scan_spec_consumer · 与本清理无关)根因。

### 批次 2 · P0 死引用 + deprecated toml(commit 9684b11)

修 6 处死引用(会让 subagent 启动读空文件):reviewer.toml architect-cr/qa-cr → review-stage + roles · prd-reviewer plan-stage → goal-stage · README prepare-stage → docs/prepare.md · claude reviewer invoke.md → state.py · README codex-cross-review → external-cross-review。删 5 个 deprecated codex-agents toml(designer/e2e-runner/planner/rd-developer/tester · bootstrap glob 误部署到每个用户)· 剩 3 active(reviewer/prd-reviewer/blueprint-reviewer)。

### 批次 3 · P2 过时文档归档(commit 1851ba2)

删 02-CLEANUP / 03-MIGRATION(一次性迁移指南 · 零引用)· 00/01/04/05 + DESIGN-业务架构 加 archive 头(被活文档 cite § rationale · 保留不断链)。

### 批次 4 · P3 导航 md 历史段(commit 8cf5cc5)

删 ROLES/STANDARDS/FLOWS 的「v7→v8 变化」历史段(纯迁移历史 · ~12-18 行各)· 顺带清 product-lead-change-mgmt「待 v8.x 物化」stale 标记。

### 批次 5 · P4 小修 + SKILL bump v8.45.0(本提交)

- STAGES.md 补 panorama_sync(标题 10→11 stage · 索引漏列正式 stage)
- common.md 撞号修(两个 `## 四` → `## 四D、QA`)+ 编码损坏修(`执�`→执行 · `校�`→校验 · 多字节字符被截断)
- ship-stage.md 步数统一(`7 步` → `step 0-7 共 8 步` · 与 §5 一致)
- goal-stage.md 错行号引用(`_v8_engine.py:742` → `_v8_stage_specs.py _evidence_reviewers_match` · 实际强制位置)

### P3/P4 剩余 · spawn follow-up(主观重写 / 兼容风险 / 独立工作)

批次 1 误删 cmd_raw_read 的教训(长 context 大改动易错):以下推独立 session 细做,不在长 context 里草率改:
- ✅ **external-model-usage 已做**(commit e6b8672 · 超出原"§11.5 压缩"范围):用户洞察「skill 只写 AI 的 what/how」→ 删 §二 why 事故复盘 + §十 用户申诉模板 + §11.5/11.6 已物化调用演示(379→212 行)。**沉淀 skill 边界原则**:skill 读者是 AI · 内容 = AI 的 what/how + 不可妥协约束;用户手册(申诉)/ 纯 why(事故复盘)/ 已物化的调用演示 都不属于 skill。
- common.md TDD 指针化 / agents README 瘦身 / PRODUCT-OVERVIEW 精简 / 代码演进注释 → spawn task(主观重写 · 逐项细评 · 可顺带应用上述 skill 边界原则)
- snapshot/validate/raw-read v8 测试覆盖(批次1 删 TestP1ReadOnly 丢的)+ 68 pre-existing render 失败诊断 → spawn task
- **保留不删**(兼容风险 / deprecation 周期太短):host_audit.json fallback · update.py `--accept-overwrite` no-op flag · reviewer.toml NEEDS_FIX 枚举(待与 README 枚举统一时一起)

### 总账

| 批次 | 内容 | 净行数 |
|------|------|--------|
| 1 | dead code + dead test | -1489 |
| 2 | 死引用修 + 5 toml 删 | -~120 |
| 3 | 文档归档(02/03 删 + 5 archive 头) | -~450 |
| 4 | 导航 md 历史段 | -~45 |
| 5 | P4 小修 | +~5 |

baseline:97 failed → 68 failed(清掉 29 个测 dead cmd 的 dead test · 剩 68 全是 pre-existing render/scan 失败 · 与清理无关)。我改过的 test_state.py + test_v8_stage_specs.py 199 passed · 0 引入新失败。

---

## v8.44.4 · prepare-check emit host-aware output_style_hint(治本 codex-cli markdown 表格渲染失败 case)

> 用户 2026-05-28 case · SVC-PLATFORM-F055 prepare 暂停点:
> - AI 第一次用 markdown 表格 emit · codex-cli terminal 渲染**破** · 表格显示成 raw `| stage |...| ` 字符
> - 用户:"内容不要 markdown 输出 · 直接绘制表格"
> - AI 第二次改用 box-drawing(`┌─┬─┐│├─┤└─┘`)· 渲染正常
> - **用户希望框架治本** · 不让每次都靠用户提示

### 根因诊断

不同 host terminal renderer 对复杂 markdown 表格能力不同:

| Host | 复杂 markdown 表格 |
|------|-------------------|
| `claude-code` | ✅ 渲染好(rich markdown) |
| `codex-cli` | ⚠️ 复杂表格(含 markdown 加粗 + emoji)容易破成 raw 字符 |
| `gemini-cli` / `unknown` | ❓ 未实测 · 保守 |

AI 自觉读 spec 决定风格不可靠 → 物化进 prepare-check emit。

### 用户决策

| 选项 | 用户选 |
|------|--------|
| A spec 加 1 句 / **B state.py 物化 hint** / C 双层 / D 不动 | **C · prepare-check emit 加 host-aware 输出风格 hint** |

### 实施

**1. 加 host-aware profile 表**:

```python
HOST_OUTPUT_STYLE_PROFILES = {
    "claude-code": {
        "style_id": "markdown_ok",
        "table_format": "markdown",  # | col | col |
        "list_format": "markdown",
        "emphasis": "markdown",      # **粗** / *斜*
    },
    "codex-cli": {
        "style_id": "box_drawing_or_plain",
        "table_format": "box_drawing",  # ┌─┬─┐│├─┤└─┘
        "list_format": "plain",
        "emphasis": "plain",            # 不用 ** · 改用 "🔴 " 前缀 / 缩进
    },
    "gemini-cli" / "unknown": 保守同 codex-cli profile,
}
```

**2. cmd_prepare_check emit 加 output_style_hint**:

```python
detected_host, host_source = _detect_host(None)
payload["output_style_hint"] = _build_output_style_hint(detected_host)
```

emit JSON 含:
```json
{
  "output_style_hint": {
    "host": "codex-cli",
    "style_id": "box_drawing_or_plain",
    "description": "Terminal renderer 对复杂 markdown 表格容易破 · 推荐 box-drawing ...",
    "table_format": "box_drawing",
    "list_format": "plain",
    "emphasis": "plain",
    "emoji_safe": true,
    "rationale": "..."
  }
}
```

### 测试覆盖(5 个新加)

- `test_v8444_output_style_hint_emitted`(prepare-check emit 必含字段)
- `test_v8444_codex_cli_host_recommends_box_drawing`
- `test_v8444_claude_code_host_recommends_markdown`
- `test_v8444_unknown_host_defaults_to_box_drawing`(None / "unknown" / 未知 host 都保守)
- `test_v8444_gemini_cli_host_box_drawing_too`

367 passed / 97 baseline / 0 regression

### PMO 工作流变化

**改前**(每次 AI 都用 markdown · 在 codex-cli 渲染破 · 用户提示后才改):
```
AI emit markdown 表格 → codex 显示 raw `| stage |` → 用户:"不要 markdown" → AI 改 box-drawing
```

**改后**(prepare-check emit 含 output_style_hint · AI 直接按 hint 风格 emit):
```
state.py prepare-check → emit output_style_hint{host:codex-cli, table_format:box_drawing}
AI 看 hint → 直接用 box-drawing emit → 渲染正常 · 不被用户提示
```

### 设计哲学

R0 哲学:**host 渲染能力是客观信号 · 进脚本物化**
- 可枚举:host → 推荐风格映射表(HOST_OUTPUT_STYLE_PROFILES)
- 不可枚举:具体 emit 内容(reviewer 思考 / 建议文案)→ 留 AI

case-driven 教训:**spec 写一句"codex-cli 用 box-drawing"** 不够(AI 可能漏读)· 物化到 prepare-check emit 让 AI 跑命令就看到 hint · 更可靠。

### Hash

- state.py:_build_output_style_hint + HOST_OUTPUT_STYLE_PROFILES = 净 +60 行 · cmd_prepare_check 加 4 行
- test_state.py:5 测新加 = 净 +45 行
- docs/CHANGELOG.md:本段

### 发布

v8.44.4 push origin/dev only · hook 自动 bump · 实际版本号 v8.44.5(本 commit + auto-bump commit)。

---

## v8.44.3 · update.py 默认 backup+overwrite(治本 2 次暂停点过度 · 用户拍板)

> 用户 2026-05-28 case:`/teamwork` 升级流程跑了 **2 个 R5 暂停点**:
> 1. "升级 / 跳过 / 其他"(用户回 1)
> 2. update.py BLOCK + AI emit "backup+覆盖 / 直接覆盖 / 取消 / 其他"(用户回 2)
>
> 用户:"看下下面的流程是否合理 · 是否应该直接按建议处理 · 不给用户是否覆盖的选择"

### 根因诊断

v8.41 我设计 `--accept-overwrite` BLOCK 是为**防误删用户定制**。但实测:
- **99% 用户**:从不改 skill_root(git clone / zip 装好就用)· BLOCK 是噪声
- **1% 开发者**:改了 skill_root · 他自己知道改了什么 · 不需要 BLOCK 提醒

更治本:**默认 backup + overwrite** —— 不可逆问题被 backup 解决 · BLOCK 多余。

### 用户决策

| 维度 | 选项 | 用户选 |
|------|------|--------|
| 治本方向 | A 默认 backup+overwrite / B AI 行为改 / C 组合 flag / D 不动 | **A · update.py 默认 backup+overwrite** |
| backup 路径 | B3 ~/.teamwork/backups/<ts>/ / B1 skill_root.backup-<ts>/ / B2 轮转保留 3 份 | **B3 · ~/.teamwork/backups/<ts>/** |

### 实施(`tools/update.py` 重设计)

#### 行为变化

```diff
- if modified and not accept_overwrite:
-     emit FAIL with hint "二选一:① backup+overwrite / ② --accept-overwrite"
-     return 1
+ # v8.44.3:默认 backup + overwrite · 不再 BLOCK
+ if not no_backup:
+     backup_path, backup_file_count = _backup_skill_root(skill_root)
+ # 直接 overwrite
+ copied = _overwrite_skill_files(skill_root, source_skill_dir)
```

#### 新 helper

```python
def _backup_root() -> Path:
    """默认 ~/.teamwork/backups/ · TEAMWORK_BACKUP_ROOT env 可 override(测试用)"""

def _backup_skill_root(skill_root) -> tuple[Path, int]:
    """shutil.copytree skill_root → ~/.teamwork/backups/<ts>/ · 返 (path, file_count)"""

def _now_ts_compact() -> str:
    """20260528T143022Z(ISO compact · 用作 backup 目录名)"""
```

#### argparse 变化

```diff
- p.add_argument("--accept-overwrite", help="显式承认覆盖本地改动 · 否则 BLOCK")
+ p.add_argument("--no-backup", help="[v8.44.3] 跳过 backup · 慎用")
+ p.add_argument("--accept-overwrite", help="[deprecated v8.44.3] no-op · 向后兼容")
```

#### emit 字段变化

```diff
+ "backup_path": "/home/user/.teamwork/backups/20260528T143022Z",
+ "backup_file_count": 117,
+ "backup_skip_reason": null,  # 或 "--no-backup flag passed"
+ "deprecation_warning": "..." (若用了 --accept-overwrite)
```

next_hint 自动提示 backup 路径:`backup 在 /home/user/.teamwork/backups/<ts>(可对比 diff 决定是否合回本地改动)`

### 用户工作流变化

**改前**(v8.41-v8.44.2):
```bash
state.py external-review → bootstrap 检测 outdated → 用户回 1 升级
  → AI 跑 update.py
  → BLOCK(本地有改动)
  → AI emit 第二暂停点(backup/覆盖/取消)
  → 用户回 2(直接覆盖)
  → AI 跑 update.py --accept-overwrite
  → 成功 · 但本地改动丢失(无 backup)
2 次 R5 暂停点 · 4 命令
```

**改后**(v8.44.3):
```bash
bootstrap 检测 outdated → 用户回 1 升级
  → AI 跑 update.py
  → 自动 backup 到 ~/.teamwork/backups/<ts>/ + overwrite
  → 成功 · 本地改动 backup 兜底 · 可对比 diff
1 次 R5 暂停点 · 2 命令
```

### 向后兼容

- `--accept-overwrite` 仍接受但 no-op + emit `deprecation_warning`(老 AI / 老脚本平滑迁移)
- 不影响 main channel 用户(他们升级路径不变 · 只是少 1 个暂停点)

### 测试(4 个新加 · 1 个删除 · 2 个调整)

新加:
- `test_v8443_default_backup_and_overwrite_succeeds`(默认行为 · backup + overwrite + 文件覆盖)
- `test_v8443_backup_path_in_teamwork_backups_dir`(backup 路径在 TEAMWORK_BACKUP_ROOT 下 · ISO timestamp 格式)
- `test_v8443_no_backup_flag_skips_backup`(--no-backup 跳 backup + 仍 overwrite + emit backup_skip_reason)
- `test_v8443_accept_overwrite_deprecated_no_op`(--accept-overwrite 仍接受但 emit deprecation_warning)

删除:
- `test_v842_block_when_local_modified_without_accept`(v8.41 BLOCK 行为已删 · 测试不再适用)

调整:
- setUp / tearDown 加 `TEAMWORK_BACKUP_ROOT` env override · 测试 backup 不污染真 ~/.teamwork
- `test_v842_channel_passed_through_to_emit` 去掉 `--accept-overwrite`(不再需要)

362 passed / 97 baseline / 0 regression

### 设计哲学

R0 哲学:**保守默认 + opt-out 极端**
- 默认安全(backup 兜底 · 用户改动可恢复)
- 极端 opt-out(--no-backup 给"不想累积 backup" 的用户)
- 不再"BLOCK + 必须 flag"(强制用户做不必要决策 = 坏 UX)

case-driven 教训:
- v8.41 设计 BLOCK 是"防止覆盖" · 实测发现 "防止" = "强迫用户做决策" · UX 灾难
- 治本不是"加更多 flag" 而是"让默认行为安全 · 让用户不用做决策"
- 这是连续第 6 次 case-driven 架构层治本(v8.40-v8.44.3)

### Hash

- tools/update.py:删 BLOCK 块 + 加 _backup_root / _backup_skill_root / _now_ts_compact helpers + 改 cmd_update Step 6/7 + 改 argparse = 净 +75 行
- tests/test_update.py:删 1 测 + 新加 4 测 + 调整 2 测 = 净 +60 行
- docs/CHANGELOG.md:本段

### 发布

v8.44.3 push origin/dev only · hook 自动 bump → 实际版本号 v8.44.4(本提交本身)+ auto-bump commit。

---

## v8.44.2 · 修 v8.44.1 hook marker 误判 bug(commit body 含 marker 字符串就被跳过)

> 上一轮 v8.44.1 commit message body 描述功能时写了`[auto-bump]` 字面字符串 · hook 用 `%B` 全 message 检测 marker 时误判已 bump · 直接放行 · 第一次 push 没 trigger hook · 用户报"hook 没生效"。bash -x trace 实证:`[[ ... contains [auto-bump] == *[auto-bump]* ]]` 真 → exit 0。

### 治本(2 处改 hook)

1. **marker 改更稀有字符串**:`[auto-bump]` → `<teamwork-auto-bump-v1>`(角括号 + 含 teamwork 命名空间 · 不易撞)
2. **检测改 subject 不看 body**:`git log -1 --pretty=%B` → `git log -1 --pretty=%s` · 只看 subject(第 1 行)
3. **双 guard**:subject 含 `chore(version): auto-bump patch` 前缀 OR body 含 marker · 任一过 → 放行

### auto-bump commit 格式改

```diff
- git commit -m "chore(version): auto-bump patch · $bump_output $AUTO_BUMP_MARKER" --no-verify
+ # subject 前缀 + body marker · 双 guard 都过
+ git commit -m "$AUTO_BUMP_SUBJECT_PREFIX · $bump_output" -m "$AUTO_BUMP_MARKER" --no-verify
```

### 实测验证(本次 push)

预期:
- v8.44 → v8.44.1(上次 push 我手动 bump 修)
- v8.44.1 → v8.44.2(本次 hook 触发 bump · push 含本 v8.44.2 commit + auto-bump commit)

### 诚实记录

v8.44.1 设计 marker 时没考虑"commit body 描述功能时会撞 marker 字符串"这个边界 case。case 实证 → 用户 push 后看到"hook 没生效"。

修法用更稀有 marker + subject-only 检测 · 双重保险。

### Hash

- git-hooks/pre-push:marker 改 + subject 检测 + 双 guard
- SKILL.md:v8.44.1 → v8.44.2(上次手动 bump 时已是 v8.44.1 · 本次 push hook 触发 → v8.44.2)
- docs/CHANGELOG.md:本段

---

## v8.44.1 · dev push auto-bump patch + pre-push hook + bump_patch_version.py(用户拍板)

> 用户 2026-05-28:"后续改下规则 · 每次 dev 有新提交自动增加小版本"

### 用户决策

| 维度 | 选项 | 用户选 |
|------|------|--------|
| 版本粒度 | A patch / B minor | **A · patch 段(v8.44 → v8.44.1)** |
| 实施方式 | CI GitHub Actions / 本地 helper / **git pre-push hook** | **git pre-push hook** |

### 设计

**触发**:`git push origin dev` 时 · pre-push hook 检测 push 目标含 dev → 跑 bump + 创建 auto-bump commit + exit 1(阻止本次 push)→ 用户重跑 `git push origin dev`(此次最新 commit 含 `[auto-bump]` 标记 hook 放行)

**为什么 exit 1**:hook 在 git push resolve sha 之后跑 · 此时新加 commit 不在本次 push 范围。让 push fail · 用户重跑 · 才能把 auto-bump commit 真正推到 GitHub。两次 push 是必要代价(可接受 · 不偷偷改 sha 让用户困惑)。

**循环避免**:hook 检测最新 commit message 含 `[auto-bump]` → 跳(放行)。第二次 push 时自然过。

**非 dev 分支跳过**:hook 检测 push 目标 ref · 若不含 `refs/heads/dev`(如 main / feature)→ 不动作。

### 实施(3 个新文件 + 1 个 install 脚本)

#### 1. `tools/bump_patch_version.py`(60 行 · stdlib only)

```python
# v8.44 → v8.44.1(无 patch 段 → 加 .1)
# v8.44.1 → v8.44.2(patch 段 +1 · 无上限)
# 不合法 frontmatter → exit 2
python3 tools/bump_patch_version.py [path/to/SKILL.md]
```

独立小脚本 · 不依赖 state.py / bootstrap.py。

#### 2. `git-hooks/pre-push`(模板 hook · 用户手动 install)

```bash
# 安装
ln -sf <REPO>/skills/teamwork/git-hooks/pre-push <REPO>/.git/hooks/pre-push
# 或
cp <REPO>/skills/teamwork/git-hooks/pre-push <REPO>/.git/hooks/pre-push
chmod +x <REPO>/.git/hooks/pre-push

# 卸载
rm <REPO>/.git/hooks/pre-push
```

模板提供框架默认值(REPO_ROOT 自动推导 · BUMP_SCRIPT 路径相对仓库根)。用户 fork / 改名 SKILL_ROOT 时只需改 BUMP_SCRIPT 一行。

#### 3. `tests/test_bump_patch_version.py`(10 测)

- `TestBumpPatchFunction`(5)· 纯函数测试
- `TestBumpPatchE2E`(5)· 真文件 + subprocess 跑独立脚本

### 用户工作流变化

**改前**(漏 bump 风险):
```bash
git push origin dev
  → push 成功
  → SKILL.md version 还是 v8.44(忘 bump · 用户拿不到 outdated 提示)
```

**改后**(2 次 push · 1 次 bump):
```bash
git push origin dev
  → pre-push hook 跑 bump_patch_version.py → SKILL.md v8.44 → v8.44.1
  → 创建 auto-bump commit "chore(version): auto-bump patch · v8.44 → v8.44.1 [auto-bump]"
  → exit 1 · 提示重 push
git push origin dev
  → hook 检测 [auto-bump] → 放行
  → push 成功(含原 commit + auto-bump commit)
```

### 版本规则

- **patch 段**:dev 每次 push 自动 bump(本 hook)· 频率高
- **minor 段**:merge dev → main 时人工 bump(release · 频率低 · 累积 patch 一次性升 minor)
- **major 段**:重大架构变更(v7 → v8 那种)· 极少

### CHANGELOG 规则约定

- 每次 patch bump 不强制写 CHANGELOG 段(实质改动是触发 bump 的那个 commit · CHANGELOG 写在那个 commit 里)
- minor release 时写完整 CHANGELOG 段(累积 patch 的总结)
- 本 v8.44.1 是首个 patch · 专门写段说明机制本身

### 0 regression

- 359 passed / 97 baseline(与 v8.44 一致 · 10 个新加全 pass)

### Hash

- 新文件 tools/bump_patch_version.py(60 行)
- 新文件 git-hooks/pre-push(模板)
- 新文件 tests/test_bump_patch_version.py(10 测)
- docs/CHANGELOG.md:本段

### 发布

- 本仓自身已 install hook(symlink 到 git-hooks/pre-push)· 下次 commit 后 push 实测验证
- v8.44.1 push origin/dev · 期望 hook 触发 → 第 2 次 push 才上去

---

## v8.44 · external-review 改 doc-based default + scaffold-review-prompt 子命令(治本 case round 4 长 prompt 卡)

> 用户 2026-05-27 case round 4 实战:
> - v8.43 inline 全 PRD/TC/TECH 改完后 · 长 prompt(几十 KB)调 `claude -p` 仍卡住
> - AI 退化用"短 prompt 概括"跑通 · 拿到 NEEDS_REVISION
> - **用户决策**:"你把提示词写入一个文档 · 让 claude 读按文档执行"

### 用户洞察:架构反转

v8.43 inline 模式的 4 个深层问题:

| 问题 | 详情 |
|------|------|
| **prompt 过长** | inline 几十 KB · `claude -p` argv 处理慢或卡 |
| **reviewer 失焦** | 全文 inline · reviewer 看 PRD body 占大量 token · 失去 checklist 焦点 |
| **不可审计** | prompt 在 state.py 拼好直接喂 claude · 用户看不到 |
| **不可编辑** | prompt 是 magic · 修不了 reviewer 检查重点 |

**用户提议**:state.py 不再 magic inline · 而是**读 AI 准备好的 prompt-doc**

| 步骤 | 责任方 | 内容 |
|------|--------|------|
| 1. scaffold prompt-doc | `state.py scaffold-review-prompt`(v8.44 新) | 短 skeleton:checklist + output schema + TODO 标记 |
| 2. 填 compact summary | AI 主对话(读 PRD/TC/TECH 用本身能力) | 关键契约提炼 · 含 known facts |
| 3. 跑 external review | state.py | 读 prompt-doc → claude argv |
| 4. 审计 / 迭代 | 用户/AI | 编辑 prompt-doc · 重跑 |

### 用户决策

| 维度 | 选项 | 用户选 |
|------|------|--------|
| doc-based 治本范围 | A 强制 / B fallback inline+WARN / C opt-in / D 不动 | **B · doc-based default · 不存在 fallback inline+WARN** |
| 是否加 scaffold helper | 加 / 不加(文档指引手写) | **加 state.py scaffold-review-prompt 子命令** |

### 实施

#### 1. 新 helper:`_default_prompt_doc_path(feature_dir, stage, model)`

返回 `<feature_dir>/external-review-prompts/<stage>-<model>.md`(如 `blueprint-claude.md`)

#### 2. 新 subcommand:`state.py scaffold-review-prompt`

```
state.py scaffold-review-prompt --feature <path> --stage {goal|blueprint|review} --model {claude|codex} [--force]
```

生成 doc skeleton:
- Strict Constraints(READ-ONLY · 不问 / 不执行 / 只 review 本 doc)
- Target(feature_id / target / stage / perspective)
- Output Schema(YAML frontmatter + findings 列表)
- Review Checklist(stage 特定:goal=4 项 / blueprint=6 项 / review=5 项)
- **TODO 段** · 让 AI 主对话填 compact summary(不复制全文)
- Required Judgment(reviewer 应特别关注的盲区)

幂等:doc 已存在 → BLOCK with hint(防覆盖编辑) · `--force` 强制覆盖。

#### 3. cmd_external_review claude 路径改 doc-based default

```diff
+ prompt_doc = _default_prompt_doc_path(feature_dir, stage, model)
+ if prompt_doc.exists():
+     prompt_text = prompt_doc.read_text(...)
+     prompt_doc_used = str(prompt_doc)
+ else:
+     # v8.44 fallback:v8.43 inline + emit WARN 提示 scaffold
+     [v8.43 inline 逻辑保留 · 向后兼容]
+     fallback_warning = "⚠️ prompt-doc 不存在 · 走 v8.43 inline fallback · 推荐 scaffold..."
```

#### 4. argparse 加 `--prompt-doc <path>`

显式 override 默认路径(用户/AI 想用其他位置 doc 时)

#### 5. emit 加 3 字段

- `prompt_doc`(实际用的 doc 路径 · doc-based 路径才出)
- `prompt_doc_source`("args" / "default")
- `prompt_doc_fallback_warning`(fallback 走 inline 时的 WARN · PMO 应看到提示 scaffold)

### 测试覆盖(5 个新加)

- `test_v844_default_prompt_doc_path`(路径规则)
- `test_v844_scaffold_creates_doc_with_required_sections`(checklist + schema + TODO)
- `test_v844_scaffold_block_when_exists_without_force`(幂等)
- `test_v844_scaffold_force_overwrites`(--force)
- `test_v844_scaffold_different_stages_have_different_checklists`(stage 特定)

349 passed / 97 baseline / 0 regression

### 工作流变化

**v8.43 一步走**(失败):
```bash
state.py external-review --feature <path> --stage blueprint
  → inline 全 PRD/TC/TECH 几十 KB
  → claude -p '...' 卡或失焦
```

**v8.44 三步走**(推荐):
```bash
# 1. AI 主对话跑 scaffold
state.py scaffold-review-prompt --feature <path> --stage blueprint --model claude

# 2. AI 主对话读 PRD/TC/TECH · 填 doc TODO 段(compact summary · 不复制全文)
edit <path>/external-review-prompts/blueprint-claude.md

# 3. state.py 读 doc · 短 prompt 不卡
state.py external-review --feature <path> --stage blueprint
  → 读 doc · cat 给 claude -p · 短 + 聚焦
```

**v8.43 fallback 保留**(向后兼容):
- doc 不存在 → 仍走 v8.43 inline 模式 · emit WARN 提示创建 doc
- 老脚本 / 紧急情况不被破坏

### 设计哲学

R0 哲学(可枚举进脚本 · 不可枚举留人):
- **可枚举**:scaffold skeleton 结构 / checklist 模板 / 文件路径规则 → 进 state.py
- **不可枚举**:PRD/TC/TECH 关键契约提炼 → AI 主对话(用本身能力 · 不是 state.py 机械替换)

case-driven 教训:
- v8.43 想"自动 inline 全文" 是 over-engineering · 失去 reviewer 焦点 + 卡 prompt 长度
- 正确分工:**state.py 提供结构 / AI 主对话提供 compact 内容 · 各司其职**

### Hash

- state.py:cmd_scaffold_review_prompt(60 行) + STAGE_TO_REVIEW_CHECKLIST + SCAFFOLD_PROMPT_DOC_TEMPLATE(80 行) + cmd_external_review claude 路径改 doc-based(35 行) + argparse 加 --prompt-doc + scaffold-review-prompt subparser = 净 +200 行
- test_state.py:5 测新加 = 净 +85 行
- SKILL.md:v8.43 → v8.44
- docs/CHANGELOG.md:本段

### 发布

v8.44 push origin/dev only(继续 dev-first 流程)· main 不动。

---

## v8.43 · external-review claude 路径全治本(stdin→argv + 占位符真替换 + template_echo BLOCK · 治本 SVC-PLATFORM-F054 blueprint round 3)

> 用户 2026-05-27 实战 case:external review 走 claude CLI 反复失败 · 用户 AI(Codex 主对话)反复 wrapper / kill 进程 / 重试 · 最后 reviewer 产物只 17 行 echo template 不真 review。三层 bug 同 case 暴露。

### 三层 Bug 实测证据

**Bug A · `claude -p` stdin 模式 "Not logged in"**
```
✓ claude -p 'Return exactly ok.' --model claude-sonnet-4-6  → "ok"(argv 模式)
✗ printf 'Return exactly ok.' | claude -p --model claude-sonnet-4-6 → "Not logged in"(stdin 模式)
```
Claude CLI 2.1.153 在 stdin 模式登录态有 bug。我 v8.38 改 `--print` → `-p` 时仍用 `input=prompt_text` 走 stdin · 直接命中。

**Bug B · Claude reviewer 只 echo template 不真 review**
- 生成的 blueprint-claude.md 只 17 行 · 含字面 `{file_list}` 占位符
- 根因:state.py 用双大括号 `{{stage}}` 替换 · reviewer.md 用单大括号 `{stage}` `{file_list}` —— **占位符完全 mismatch · 全部没替换** · 且 `{file_list}`(文件内容 inline 关键)从未被处理
- Claude 收到字面 `{file_list}` 当 meta 任务 echo

**Bug C · quality_warnings 只 WARN 不 BLOCK**
v8.36 决策 WARN · case 实证 AI 看到产物存在就继续 · WARN 走过场 · 用户最后手动读 file 才发现无效。

### 用户决策

| 维度 | 选项 | 用户选 |
|------|------|--------|
| v8.43 治本范围 | A 全治 / B 仅 A+B / C 仅 A / D 仅 C | **A · 全治 Bug A+B+C** |
| 占位符统一方向 | state.py 改单 / reviewer.md 改双 / 都改 `${name}` | **state.py 改单 · 与 reviewer.md 对齐** |

### 实施(3 个 Fix)

#### Fix 1 · `_run_claude_review` stdin → argv(state.py)

```diff
- cmd = ["claude", "-p", "--model", model_name, "--output-format", "text"]
- r = subprocess.run(cmd, input=prompt_text, ...)
+ cmd = ["claude", "-p", prompt_text, "--model", model_name, "--output-format", "text"]
+ r = subprocess.run(cmd, ...)
```

加 ARG_MAX 错误捕获(`errno=7` E2BIG)· emit hint 提示 prompt 过长。

#### Fix 2 · 占位符真替换 + inline 文件内容

新加 helper `_gather_review_files_for_claude(stage, feature_dir)`:
- stage → 文件清单(goal=[PRD.md] / blueprint=[TC.md, TECH.md] / review=[]· review 走 diff)
- 读取每文件 inline 成 ` ### filename\n\\`\\`\\`\ncontent\n\\`\\`\\`\n`
- 超 60KB 单文件 truncate + meta 标 truncated
- 缺失文件 emit "(文件不存在)" · 不 BLOCK

state.py 替换改单大括号 + 加 `{file_list}` 处理:
```diff
+ file_list_block, files_inline_meta = _gather_review_files_for_claude(stage, feature_dir)
  prompt_text = (
      prompt_template
+     .replace("{stage}", args.stage)
+     .replace("{target}", STAGE_TO_REVIEW_TARGET.get(args.stage, args.stage))
+     .replace("{feature_name}", feature_id)
+     .replace("{file_list}", file_list_block)
      # 兼容历史双大括号 caller:
      .replace("{{stage}}", args.stage)
      ...
  )
```

emit 加 `files_inlined` 字段(PMO 可验 reviewer 真拿到内容)。

#### Fix 3 · template_echo 升 BLOCK + 逃生口

```diff
+ template_echo_hit = [w for w in quality_warnings if w.get("type") == "template_echo"]
+ if template_echo_hit and not args.accept_quality_warnings:
+     emit FAIL with hint:
+        ① 检查 prompt 与 reviewer 真实输出 · 修 prompt 或重跑
+        ② --accept-quality-warnings 通过(走 bypass log + concerns WARN)
+     return
```

argparse 加 `--accept-quality-warnings`。bypass 路径 emit 携带 `quality_bypass_warning`(audit 留痕)。

`empty_content` 保持 WARN(可能合理精简 · 区别于 template_echo 强信号)。

### 测试覆盖(5 个新加)

`TestExternalReviewCommand`:
- `test_v843_run_claude_review_prompt_in_argv_not_stdin`(Fix 1 · mock subprocess 验 argv 位置)
- `test_v843_gather_review_files_inlines_blueprint_targets`(Fix 2 · blueprint TC/TECH 真 inline)
- `test_v843_gather_review_files_truncates_oversized`(Fix 2 · 超 60KB truncate)
- `test_v843_gather_review_files_handles_missing`(Fix 2 · 缺失文件不抛异常)
- `test_v843_stage_review_files_maps_correctly`(Fix 2 · 映射表 sanity)

`test_v838_run_claude_review_cmd_array_uses_dash_p` 更新(去除"prompt 在 stdin" 旧断言 · v8.43 改 argv)。

344 passed / 97 failed(baseline 一致 · 0 regression)

### 端到端影响

| 改前(v8.42)| 改后(v8.43) |
|------------|--------------|
| `claude -p` 用 stdin → "Not logged in" | argv → 正常返 |
| reviewer 收到字面 `{file_list}` 占位符 → echo | 收到真文件内容 inline → 真 review |
| template_echo WARN 不 BLOCK · AI 走过场 | BLOCK · 必显式 --accept-quality-warnings 才过 |

case 现场 AI 手拼 `claude -p` argv + inline 文件路径 的弯路 · v8.43 走 state.py external-review 主路径直接拿到。

### 设计哲学

R0 哲学(可枚举进脚本):
- stdin/argv 选择 · 客观信号(Claude CLI 2.1.153 bug)→ 写死 argv
- 占位符 mismatch · 客观对齐(单 vs 双)→ 改成单大括号 + 真替换
- template_echo · 100% 无效信号 → BLOCK · 不留 WARN 走过场口子

逃生口设计("不一刀切"):
- ARG_MAX 超限 → errno=7 emit hint("prompt 过长")
- 文件 truncate → reviewer 看到 truncated 标记自行判断完整性
- template_echo 误报 → --accept-quality-warnings 显式确认 + bypass log

### 治本与诚实

我 v8.38 改 `--print` → `-p` 时只想着 short alias 对齐 · 没意识到 stdin/argv 是不同 code path(Claude CLI bug 表现不同)。case 实证才发现。

v8.36 留 template_echo WARN 兜底 · 怕"误报误伤" · 实测发现 AI 钻 WARN 兜底口子。R0 哲学 case-driven 教训:**WARN 经常被 AI 当 silent 跳过 · 强信号必须 BLOCK + 逃生口**。

reviewer.md `{file_list}` 占位符 spec 早就写好(line 122)· 但 state.py 实施时没读 spec · 自己造了双大括号体系。这是典型的 "实施与 spec 解耦" bug。

### Hash

- state.py:_run_claude_review stdin→argv + helpers + template_echo BLOCK 块 + argparse = 净 +100 行
- test_state.py:5 测新加 + 1 测更新 = 净 +95 行
- SKILL.md:v8.42 → v8.43
- docs/CHANGELOG.md:本段

### 发布

v8.43 push origin/dev only(继续 dev-first 流程)· main 不动。

---

## v8.42 · 架构治本:update-skill 抽到独立 tools/update.py(职责分离 · 用户拍板)

> 用户 2026-05-27:"更新文件本身是否有必要单独一个 python"

### 用户洞察:元工具 vs 运行时

v8.41 治本去 git 化后 · cmd_update_skill 在 state.py 里仍有 4 个问题:

| 问题 | 说明 |
|------|------|
| **元工具混入运行时** | state.py = stage 状态机/评审/测试 运行时;update-skill = 管 state.py 自己 元工具 · 职责不同 |
| **覆盖自己进程的不一致** | update-skill 跑时进程在内存 · 磁盘 state.py 被覆盖 · 同一 session 后续命令拿旧代码 |
| **chicken-and-egg 死锁风险** | 若 cmd_update_skill 自己有 bug · 用户无法升级救命 |
| **与 bootstrap.py pattern 不一致** | bootstrap.py 本身就独立 · update 同是 setup-style 元工具 · 应对齐 |

### 用户决策

| 维度 | 选项 | 用户选 |
|------|------|--------|
| 抽离方案 | A 完全独立 / B 双入口 / C 模块化 / D 维持现状 | **A · 完全独立 tools/update.py** |
| 文件名 | update.py / selfupdate.py / upgrade.py / update_skill.py | **update.py**(最简洁 · 与 bootstrap.py 风格对齐) |

### 实施

#### 1. 新建 `tools/update.py`(独立脚本)

完整搬 v8.41 cmd_update_skill 逻辑:
- 4 helpers:`_download_skill_tarball` / `_parse_skill_md_version` / `_detect_local_modifications` / `_overwrite_skill_files`
- 1 helper:`_resolve_channel`(优先级 args > localconfig > main · 复用 v8.39)
- 1 主流程:`cmd_update(args)`(7 步)
- 独立 argparse(`build_parser` + `main`)
- 命令:`python3 SKILL_ROOT/tools/update.py [--channel <branch>] [--accept-overwrite]`

#### 2. state.py 清理(259 行删除)

```diff
- 4 helpers(_download_skill_tarball / _parse / _detect / _overwrite)
- cmd_update_skill(140+ 行)
- argparse "update-skill" subparser + add_argument --channel / --accept-overwrite

+ 注释保留指向 tools/update.py(让 grep 用户找到新位置)
```

#### 3. bootstrap.py outdated prompt 改

```diff
- update_cmd = "`state.py update-skill`" if main else f"`state.py update-skill --channel {channel}`"
+ update_cmd = "`python3 $SKILL_ROOT/tools/update.py`" if main else f"`python3 $SKILL_ROOT/tools/update.py --channel {channel}`"
```

bootstrap 自动检测到新版本 emit prompt 时直接给独立脚本路径 · 用户复制即跑。

### 测试覆盖(8 个新加 · 1 个新文件 · 5 个旧测删)

新文件 `tools/tests/test_update.py`:

**TestUpdatePyStandalone**(3 测 · 验证独立性):
- `test_v842_update_py_exists`
- `test_v842_update_py_runs_help_independently`(`update.py --help` 不依赖 state.py)
- `test_v842_state_py_no_longer_has_update_skill`(确认 state.py update-skill subparser 已删 · invalid choice)

**TestUpdatePyTarballDownload**(5 测 · 从 test_state.py 迁移 v8.41 核心逻辑):
- `test_v842_block_when_local_modified_without_accept`
- `test_v842_pass_with_accept_overwrite_and_overwrites_files`
- `test_v842_block_when_tarball_url_invalid`
- `test_v842_channel_passed_through_to_emit`
- `test_v842_default_channel_main`

删除 `test_state.py:TestUpdateSkillTarballDownload`(已迁出)。

更新 `test_bootstrap.py`:
- `test_outdated_emits_r5_prompt`:期望含 `tools/update.py` · 不含 `state.py update-skill`
- `test_v839_explicit_dev_channel`:期望含 `tools/update.py` + `--channel dev`

339 passed / 97 failed(baseline 一致 · 0 regression)

### 与 bootstrap.py pattern 对齐

| 工具 | 文件 | 类型 | 用法 |
|------|------|------|------|
| `bootstrap.py` | tools/bootstrap.py | setup 元工具(独立) | `python3 SKILL_ROOT/tools/bootstrap.py --host X` |
| **`update.py`** | tools/update.py | **upgrade 元工具(独立 · v8.42)** | `python3 SKILL_ROOT/tools/update.py [--channel X]` |
| `state.py` | tools/state.py | 运行时(stage 状态机 + ...) | `python3 SKILL_ROOT/tools/state.py <cmd>` |

清晰的 3 文件分层:**元工具(bootstrap/update)+ 运行时(state)**。

### chicken-and-egg 治本

旧:若 v8.x cmd_update_skill 自己有 bug · 用户无法升级救命(state.py update-skill 自己坏了 → 升不了)
新:update.py 完全独立 · state.py 任何 bug 都不影响 update.py 跑 · 用户随时能升级

### Hash

- 新文件 tools/update.py:282 行
- 新文件 tools/tests/test_update.py:200 行
- state.py:删 259 行(cmd_update_skill + 4 helpers + argparse + 常量)
- bootstrap.py:update_cmd 改 7 行
- test_state.py:删 142 行(TestUpdateSkillTarballDownload class)
- test_bootstrap.py:改 2 个测试 · 加 update.py 字面校验
- SKILL.md:v8.41 → v8.42
- docs/CHANGELOG.md:本段

净结果:state.py 减 259 行 · 总 -ish 净 +250 行(独立 update.py 文件 + 独立测试)

### 设计哲学

v8.41 治本 git 路径 bug(架构层降级)· v8.42 治本元工具混运行时(职责分离)。两次都是**架构层动手** · 不是修补层。

R0 哲学:
- **可枚举的进脚本**:update 流程 7 步 · helpers · 全在 update.py
- **职责分离**:state.py 不该管"如何升级 state.py" · 像 bash 不该管"如何升级 bash"
- **chicken-and-egg 隔离**:救命工具必须独立(否则坏了救不了)

### 发布

v8.42 push origin/dev only(继续 dev-first 流程)· 不动 main。

下次稳定后(累积 v8.40-v8.42 dev 改动)可 ff merge dev → main 让 stable 用户拿到全部治本。

---

## v8.41 · 架构治本:update-skill 去 git 化 · tarball download + 覆盖(用户拍板)

> 用户 2026-05-27:"cmd_update_skill 是否可以不关心分支 · 按理说他可以不关心 git · 只是从对应仓库和对应分支拉取最新文件做覆盖"

### 用户洞察的精确性

v8.24/v8.39/v8.40 把 update-skill 当 "vcs sync"(git pull) · 引入大量 git 相关复杂度:
- v8.24:dirty BLOCK
- v8.39:channel + URL 模板
- v8.40:branch/channel 一致性校验

用户重新分类:**update-skill 是 package manager**(npm/pip/brew)· 不是 vcs sync。只需要:
1. 从远端拉最新内容
2. 覆盖本地

**v8.40 治本的"分支与 channel 错配"bug 在 download-overwrite 模型里根本不存在** —— 没有"当前分支"概念。架构层降级 · 不是修补层治本。

### 用户决策

| 维度 | 选项 | 用户选 |
|------|------|--------|
| 架构治本方向 | A 完全去 git 化 / B 保留 git 不依赖分支 / C 维持 v8.40 / D 双路径 | **A · 完全去 git 化** |
| 本地改动保护 | A WARN + --accept-overwrite / B 自动 backup / C 直接覆盖 / D BLOCK 无逃生 | **A · WARN + --accept-overwrite** |

### 实施(state.py 重写 cmd_update_skill + 3 helpers)

```diff
- # ── Step 1:检测 git repo ── (git rev-parse --show-toplevel)
- # ── Step 2:检测脏树 ── (git status --porcelain · dirty BLOCK)
- # ── Step 3:读 old version
- # ── v8.39:resolve channel
- # ── v8.40:校验当前分支 == channel(git rev-parse --abbrev-ref HEAD)
- # ── Step 4:git fetch origin <channel> + git pull --ff-only origin <channel>
- # ── Step 5:读 new version + ORIG_HEAD diff stat

+ # v8.41:tarball-based(去 git 化)
+ SKILL_TARBALL_URL_TEMPLATE = "https://github.com/okteam99/teamwork/archive/refs/heads/{channel}.tar.gz"
+
+ def _download_skill_tarball(channel, work_dir):  # curl + tar -xzf
+ def _parse_skill_md_version(skill_md):           # 复用 v8.24 的 regex
+ def _detect_local_modifications(target, source): # 文件 byte 比较
+ def _overwrite_skill_files(target, source):      # shutil.copy2 覆盖
+
+ def cmd_update_skill(args):
+     Step 1 resolve channel(args > localconfig > main · 保留 v8.39)
+     Step 2 读 old version
+     Step 3 download tarball + 解压 to /tmp(失败 → FAIL with hint)
+     Step 4 读 new version + 校验完整性(无 SKILL.md → FAIL)
+     Step 5 检测本地修改(byte-by-byte)
+     Step 6 modified + 无 --accept-overwrite → FAIL with hint(逃生口)
+     Step 7 覆盖 skill_root · cleanup tmp · emit OK
```

argparse 改动:
- 删 `--force`(git pull 时代的脏树绕过 · 已无意义)
- 加 `--accept-overwrite`(本地改动覆盖必显式)
- 保留 `--channel`(v8.39)

### 复杂度降级

| 检查项 | v8.40 | v8.41 |
|-------|-------|-------|
| 依赖 | git CLI + git repo | curl + tar |
| 代码行数 | 200+ | 280(算 3 helpers · 主 cmd 减 50%) |
| 校验复杂度 | 6 重(git repo + dirty + channel + branch + ff + ORIG_HEAD) | 2 重(下载完整 + 本地改动) |
| 错配 bug | v8.40 加校验治本 | 不存在 |
| 安装方式 | 仅 git clone | git clone OR zip 都行 |

### 治本 v8.40 之前所有"git 相关"bug

- v8.24 dirty BLOCK 误触发 → 不存在(没有 git status 检查)
- v8.35 `{SKILL_ROOT}` placeholder → 不存在(已经是 f-string 真实路径)
- v8.40 branch/channel 错配 → 不存在(没有"当前分支"概念)
- v8.40 hint 误导(rebase) → 不存在(没有 pull 失败路径)

### 测试覆盖(5 个新加 · 1 个新 class)

`TestUpdateSkillTarballDownload`(setUp 用 tarfile 造 fake remote · file:// URL 喂给 state.py):
- `test_v841_block_when_local_modified_without_accept`(主 BLOCK · hint 含逃生口)
- `test_v841_pass_with_accept_overwrite_and_overwrites_files`(主 PASS · 验文件真被覆盖 + 新增文件)
- `test_v841_block_when_tarball_url_invalid`(download 失败)
- `test_v841_channel_passed_through_to_emit`(--channel args 传透)
- `test_v841_default_channel_main`(默认 main · channel_source=default)

删除旧测(已不适用):
- `TestUpdateSkillHint`(v8.35 git-not-repo hint · git 路径已删)
- `TestUpdateSkillBranchChannelGate`(v8.40 branch 校验 · 已不存在)

336 passed / 97 failed(baseline 一致 · 0 regression)

### 用户工作流变化

**stable 用户**(默认 main):
```bash
state.py update-skill                          # 无本地改动:PASS · 自动覆盖
state.py update-skill --accept-overwrite       # 有本地改动:用此确认
```

**preview 用户**(channel=dev):
```bash
state.py update-skill --channel dev            # 同上 + dev URL
state.py update-skill --accept-overwrite --channel dev
```

**新场景**:zip 安装 skill(不是 git clone)现在也能 update-skill!之前 v8.24-v8.40 会因 "不是 git repo" BLOCK · v8.41 通吃。

### 边界与诚实记录

**v8.41 不删 target 多余文件**:覆盖只复制 source 有的文件 · target 多余文件保留(保守 · 防误删用户本地新加文件)。代价:老版本被删的文件残留 stale(retro/审查可见)。

**本地改动检测**:基于 byte-by-byte 比较 · 不靠 git history。对于 deleted file 不会 BLOCK(target 删 / source 有 → 不视作 modification · 升级会补回来)。

**架构反思**:我 v8.24 选 git pull 是因为"skill 已经是 git clone 来的 · 用 git pull 自然"。但**自然 ≠ 必要** —— 那是 incidental complexity · 不是 essential。用户重新归类后 · 一次治本 v8.24-v8.40 的全部 git 路径 bug。**这是设计层降级的胜利 · 不是修补层治本**。

### Hash

- state.py:cmd_update_skill 完全重写 + 3 helpers(_download_skill_tarball / _parse_skill_md_version / _detect_local_modifications / _overwrite_skill_files)= 净 +60 行(包含 4 helpers · 主 cmd 净减)
- state.py argparse:删 --force / 加 --accept-overwrite / 保留 --channel = 净 +0 行
- test_state.py:删 TestUpdateSkillHint(v8.35)+ TestUpdateSkillBranchChannelGate(v8.40)· 加 TestUpdateSkillTarballDownload(5 测)= 净 +30 行
- SKILL.md:v8.40 → v8.41
- docs/CHANGELOG.md:本段

### 发布

v8.41 push origin/dev only(继续 dev-first 流程)· 不动 main。

---

## v8.40 · 治本 v8.39 引入的 branch/channel 错配 bug(audit case · 首个 dev-only release)

> 用户 2026-05-27:"在检查下 skill 升级的流程和逻辑"。我做 e2e audit 发现 v8.39 引入 2 个关键 bug · 立即 dev-only 治本(走 v8.39 设立的 dev-first 流程的第一个 release)。

### audit 发现的 2 bug

**Bug A · 当前分支与 channel 错配时静默错改本地分支(🔴 高)**

实测证据(audit 现场):
```
当前分支:dev   localconfig:无(默认 main)
git pull --ff-only origin main → 试图把 local dev FF 到 origin/main
若 dev ahead/behind/分叉 → 失败 with 误导 hint("本地分叉/冲突")
若 dev == main 同 commit → 成功 no-op · 但用户没察觉

更严重场景(v8.40 push dev only 后)
当前分支:main   localconfig:dev
git pull --ff-only origin dev → 成功把 local main FF 到 dev HEAD
→ local main 指向 dev v8.40 commit
→ 用户 git push origin main 撞 non-ff(因为 origin/main 还在 v8.39)
→ main 分支状态混乱 · 破坏 main/dev channel 隔离本意
```

**Bug B · 缺一致性校验导致误导 hint**

`git pull --ff-only origin <channel>` 在错误分支上失败时 · hint 显示"本地分叉/冲突 · 手动 rebase 或 reset" · 但根因是分支错配 · 不是分叉。用户按 hint 跑 `git rebase origin/<channel>` 会把当前分支混入 channel 的 commit · 进一步搞乱。

### 治本(state.py:cmd_update_skill 加 Step 3.5 校验)

```diff
+ # ── v8.40:校验当前分支 == channel(治本 v8.39 引入分支与 channel 错配 bug)──
+ b = subprocess.run(["git", "-C", str(git_root), "rev-parse",
+                     "--abbrev-ref", "HEAD"], ...)
+ cur_branch = b.stdout.strip()
+ if cur_branch != channel:
+     emit({
+         "verdict": "FAIL",
+         "error": f"当前分支={cur_branch!r} ≠ channel={channel!r} · "
+                  f"拒绝 pull · 防偷偷把 local {cur_branch} 改成 origin/{channel}",
+         "current_branch": cur_branch,
+         "channel": channel,
+         "channel_source": channel_source,
+         "hint": (
+             f"二选一:\n"
+             f"  ① [推荐] 切到对应分支再升:\n"
+             f"     cd {git_root} && git checkout {channel} && state.py update-skill"
+             f"{'' if channel == 'main' else f' --channel {channel}'}\n"
+             f"  ② 改 channel 与当前分支一致:\n"
+             f"     state.py update-skill --channel {cur_branch}\n"
+             f"     或编辑 .teamwork_localconfig.json.update_channel = {cur_branch!r}"
+         ),
+     })
+     return
```

### 测试覆盖(3 个新加 · 1 个新 class)

`TestUpdateSkillBranchChannelGate`(e2e 真 git repo · 不 mock):
- `test_v840_block_when_on_main_but_channel_dev`(主 bug 场景)
- `test_v840_block_when_on_dev_but_channel_default_main`(反向 bug)
- `test_v840_pass_check_when_branch_equals_channel`(正常路径不被本校验拦)

335 passed / 97 failed(baseline 一致 · 0 regression)

### audit 总结(符合预期项 + bug 项)

✅ 符合预期:
- `_read_update_channel` 4 fallback 路径(默认 / config / 损坏 / 类型错 / 空串)全 PASS
- `check_skill_update` 4 status(up_to_date / outdated / network_failed / parse_failed)+ channel 字段输出
- bootstrap 自动读 cwd localconfig channel 传给 check_skill_update
- bootstrap silent · 不阻塞
- e2e curl dev/main URL 都拉得到 SKILL.md
- outdated prompt 智能区分 main 默认(简洁)/ 其他(--channel + ⚠️ 尝鲜)
- cmd_update_skill 自动 channel resolve(args > localconfig > default)
- emit 含 channel + channel_source(用户可追溯)

❌ 不符合预期(v8.40 治本):
- Bug A 当前分支与 channel 错配 → 静默错改 local 分支
- Bug B 错配后 fetch/pull 失败 hint 误导

### 设计哲学

R0 哲学:**可枚举进脚本**(分支名一致性 · 客观信号)→ 加校验。

不偷偷帮用户切分支(选项 A · 自动 checkout)· 因为:
- 用户当前分支可能有 uncommitted work · 自动 checkout 风险大
- 偷偷切完用户不知情 · 下次 cd 看分支可能困惑

选 选项 B(BLOCK + hint 给两条路)· 保留用户决策权 · 不偷偷动状态。

### 发布策略

**v8.40 首个 dev-only release**:
- push origin/dev(commit 本段)
- 不 push main(走 v8.39 设立的 dev-first 流程)
- 后续累积稳定测试 · 定期 ff merge dev → main

**用户影响**:
- main 用户:仍 v8.39 · 不受本次治本影响(他们 update_channel=main · 当前分支 main 一致 · 不会触发 bug)
- dev 用户:升 v8.40 后获得校验保护 · 避免分支错配

### Hash

- state.py:cmd_update_skill 加 Step 3.5 branch 校验 = 净 +40 行
- test_state.py:TestUpdateSkillBranchChannelGate(3 测试 · e2e 真 git repo)= 净 +85 行
- SKILL.md:v8.39 → v8.40
- docs/CHANGELOG.md:本段

### 诚实记录

v8.39 设计 channel 时漏想"当前分支与 channel 解耦"场景 · 加 channel 参数但没动 fetch/pull 之外的逻辑。audit 实测才发现 —— 又是"先写 e2e 测试再实施"会更早抓住的 bug。但 v8.39 测试用 file:// URL mock 拉 SKILL.md · 没测真 git pull 行为 · 漏掉这层。v8.40 加的测试是 e2e 真 git repo(setUp 跑 git init / branch · 然后真 subprocess 跑 state.py)· 更接近真实场景。

---

## v8.39 · skill 升级支持 `update_channel`(main / dev · 用户拍板)+ 新建 dev 分支用于后续优化

> 用户 2026-05-27:"我们把主分支改为 dev 分支后续优化优先使用 dev 分支 · 另外 skill 升级检查逻辑支持一下检查分支 · 使用 .teamwork_localconfig.json 中的 update_channel 定义 · 默认为 main"

### 分支策略

| 分支 | 角色 | 升级时机 | 风险 |
|------|------|---------|------|
| `main` | **stable channel(默认)** | 稳定版发布 · 通过 dev 验证后定期 ff merge 过来 | 低(经过 dev 实战) |
| `dev` | **preview channel(尝鲜)** | 后续优化优先 push dev · 早期用户先用 | 中(可能 break · 用户 opt-in) |

**用户 opt-in dev**:在项目根 `.teamwork_localconfig.json` 加 `"update_channel": "dev"` · 不动 = main 默认。

### 改动 1:bootstrap.py check_skill_update 支持 channel

```diff
- SKILL_UPDATE_RAW_URL = (
-     "https://raw.githubusercontent.com/okteam99/teamwork/main/skills/teamwork/SKILL.md"
- )
+ SKILL_UPDATE_RAW_URL_TEMPLATE = (
+     "https://raw.githubusercontent.com/okteam99/teamwork/{channel}/skills/teamwork/SKILL.md"
+ )
+ SKILL_UPDATE_DEFAULT_CHANNEL = "main"
+
+ def _read_update_channel(project_root):
+     # 读 .teamwork_localconfig.json.update_channel · 默认 main
+     # 损坏/缺/非 string/空串 → main(silent · 不阻塞)

- def check_skill_update(local_version):
+ def check_skill_update(local_version, channel="main"):
      url = env_override or SKILL_UPDATE_RAW_URL_TEMPLATE.format(channel=channel)
      ...
      return {..., "channel": channel, "url": url}
```

`cmd_session_bootstrap` 自动读 channel 并传给 check_skill_update。

**outdated prompt 智能区分 channel**:
- `channel=main`(默认):prompt 中 `state.py update-skill` 无 `--channel` 参数(简洁)
- `channel=dev`(或其他):prompt 中 `state.py update-skill --channel dev` + 加 `⚠️ 尝鲜分支可能不稳定` 警告

### 改动 2:state.py cmd_update_skill 支持 `--channel`

```diff
+ # v8.39 channel resolve · 优先级 args > localconfig > main
+ channel = args.channel or _read_update_channel(project_root) or "main"

- f = subprocess.run(["git", "-C", str(git_root), "fetch", "origin", "main"], ...)
+ f = subprocess.run(["git", "-C", str(git_root), "fetch", "origin", channel], ...)

- p = subprocess.run(["git", "-C", str(git_root), "pull", "--ff-only", "origin", "main"], ...)
+ p = subprocess.run(["git", "-C", str(git_root), "pull", "--ff-only", "origin", channel], ...)
```

emit 输出加 `channel` + `channel_source`(args / localconfig / default)· 错误 hint 携带 channel(若 fetch/pull 失败 · 用户知道是哪个分支不存在)。

### 改动 3:argparse 加 `--channel`

```
state.py update-skill [--force] [--channel <branch_name>]
                                  ^^^ v8.39 新增
```

### 测试覆盖(7 个新加)

`TestCheckSkillUpdate` 加:
- `test_v839_default_channel_is_main`(向后兼容)
- `test_v839_explicit_dev_channel`(dev URL + prompt 含尝鲜警告 + --channel dev)
- `test_v839_main_channel_prompt_no_warning`(main 简洁)
- `test_v839_read_update_channel_default_main`(无 config → main)
- `test_v839_read_update_channel_from_localconfig`(config dev → dev)
- `test_v839_read_update_channel_corrupt_config_falls_back_main`(损坏 → main)
- `test_v839_read_update_channel_non_string_falls_back_main`(类型错 → main)
- `test_v839_read_update_channel_empty_string_falls_back_main`(空串 → main)

332 passed / 97 failed(baseline 一致 · 0 regression)

### 用户工作流变化

**stable 用户(默认 main)**:不动 `.teamwork_localconfig.json` · 升级仍是 `state.py update-skill`

**preview 用户(尝鲜 dev)**:在项目根 `.teamwork_localconfig.json` 加:
```json
{
  "update_channel": "dev"
}
```
之后 bootstrap 自动检测 dev 最新版本 · prompt 提示 `state.py update-skill --channel dev`(或不传 · 自动从 config 读)。

**任意分支**:`update_channel` 可填任何分支名(非验证 enum)· 用户测试新 feature 分支可临时改:
```json
{
  "update_channel": "feat/some-experiment"
}
```

### 发布策略

**本次 v8.39 双 push**:
1. push origin/main(让用户拿到 channel 机制本身 · 否则没法用 dev)
2. 创建 dev 分支(基于 v8.39 main HEAD) + push origin/dev

**之后 v8.40+**:
- 后续优化 push dev · 用户 opt-in 尝鲜
- 稳定后定期 fast-forward / merge dev → main · 走 stable channel 用户

### 设计哲学

R0 哲学(可枚举进脚本 · 不可枚举留人):
- **可枚举**:channel 名 / URL 模板 / fetch+pull 命令 / 优先级链 → 全进脚本
- **不可枚举**:何时升 dev / 是否回滚 → 用户判 · 工具只提示风险(尝鲜警告 + retro 可见)

不强校验 channel 合法值(允许任意分支名)· R0 灵活性:用户测试 feature 分支不被工具卡。

### Hash

- bootstrap.py:加 `_read_update_channel` + 模板化 URL + check_skill_update 加 channel 参数 = 净 +60 行
- state.py:cmd_update_skill 加 channel resolve + fetch/pull 用 channel + emit 加 channel + argparse `--channel` = 净 +40 行
- test_bootstrap.py:7 个新测试 = 净 +75 行
- SKILL.md:v8.38 → v8.39
- docs/CHANGELOG.md:本段

---

## v8.38 · external-review claude CLI 用 `-p` 替代 `--print`(用户约定 · case SVC-PLATFORM-F054 round 2)

> 用户 2026-05-27:"外部调用 claude 的时候 要使用 -p"。case 现场:AI 调用 claude CLI 经历 sandbox 权限路径切换 · 提升权限后才成功 · 用户明确要求统一用 `-p` short alias。

### 改动(state.py + 3 个文档)

**功能**:`-p` 与 `--print` 功能等价(Claude CLI alias)· 用户约定改 `-p`。

- `state.py:_run_claude_review` cmd 数组改 `["claude", "-p", ...]`(原 `--print`)
- `state.py:preview_command` 字面(`--dry-run` 输出)同步改 `claude -p`
- `state.py` 注释 / 错误信息 / 文档字符串同步改
- `claude-agents/reviewer.md` 3 处 / `standards/external-model-usage.md` / `templates/review-log.jsonl` 文档同步

### 不动的部分(诚实记录)

- `docs/CHANGELOG.md` 历史段(v8.20/v8.22 等)保留 `--print` 字面(诚实记录演进 · 不改历史)
- 测试:`TestExternalReviewCommand` 已有的 cmd preview 测试若 hardcode 检查 `--print` 字面 · 需要同步(下面 pytest 跑出来再调)

### 测试 + 0 regression

跑 pytest 全套验证:见末尾。

### 设计哲学

case 现场 AI 手拼 `subprocess.run(['claude', '--print', ...])` + `subprocess.run(['claude', '-p', ...])` 反复试探 sandbox 权限 · 最终提升权限后成功。用户决策:**统一约定 `-p`**(短 · 一致 · 用户偏好)· 不让 AI 反复试 long/short flag。

这不是治本 case(case 本质问题是 sandbox 权限切换 · 不是 flag 选择)· 但用户的约定要求是工程礼貌 · 应当对齐。

### Hash

- state.py:`_run_claude_review` cmd 数组 + 错误信息 / preview_command 字面 / 1 处注释 = 净 +4 行 / -4 行
- claude-agents/reviewer.md / standards/external-model-usage.md / templates/review-log.jsonl:`--print` → `-p` 共 5 处替换
- SKILL.md:v8.37 → v8.38
- docs/CHANGELOG.md:本段

---

## v8.37 · ship-push url-fallback 退化拦截(治本 SVC-CORE-B007 case · CLI 已装时禁止退化)

> 用户 2026-05-27 贴 SVC-CORE-B007-Matched-Offers-Status-Filter 实战 case · 提"glab 已装的前提下 · 除非用户手动确认 · 否则不可以退化"。

### case 暴露的 spec/工具 缺口

AI(Claude Code session)跑 ship-phase push 时:
- 本机 `glab 1.92.1` 已装 + `glab auth status` 已登录
- 但 AI 直接传 `--mr-creation-method url-fallback --mr-create-url <git push 输出的 MR 创建表单 URL>`
- 规范 `stages/ship-stage.md L17 + L109 + P0-113` 明文要求 CLI-first · AI 违规
- **state.py 没拦截** · 在 `mr_creation_method=url-fallback + mr_create_url` 都满足时静默 PASS
- 用户察觉后:AI 手动跑 `glab mr create` 拿真 MR URL · 再 `raw-write` 修正 state · 闭环但走了弯路

AI 自己在 case 末尾总结的治本建议:
> ship-phase push 在 --mr-creation-method url-fallback 时校验 which glab && [ "$git_host" = "gitlab-self-hosted" ] → 命中即 BLOCKED with hint "glab 已装 · 不允许退化"

v8.37 按此治本 + 加合理逃生口。

### 用户决策

| 维度 | 选项 | 用户选 |
|------|------|--------|
| 拦截严格度 | A: CLI 装+认证 BLOCK / B: 只检 which / C: WARN 不 BLOCK / D: 不修 | **A · CLI 装好+认证了 BLOCK** |
| 逃生口参数名 | `--accept-cli-unavailable + --reason + --user-confirmed` / 复用 bypass / 2 参轻量 | **`--accept-cli-unavailable + --reason + --user-confirmed`** |

### 实施(2 个核心改动)

#### 1. `_v8_ship.py:_check_cli_available_for_host(git_host)` helper

```python
SHIP_GIT_HOST_TO_CLI = {
    "github":             "gh",
    "gitlab":             "glab",
    "gitlab-self-hosted": "glab",
    # gitee / bitbucket / unknown:无主流 CLI · 不强校
}

def _check_cli_available_for_host(git_host: str) -> dict:
    # ① 查表 git_host → CLI name · 不在表内 → no_cli_mapping_for_host
    # ② which <cli> → 没装 → <cli>_not_installed
    # ③ <cli> auth status → 未登录 → <cli>_not_authenticated
    # 返 {available: bool, cli_name, reason, hint_install?, hint_auth?}
```

#### 2. `_handle_ship_push` 在 url-fallback 时调用 helper

```python
if args.mr_creation_method == "url-fallback":
    cli_check = _check_cli_available_for_host(args.git_host)
    if cli_check["available"]:
        if not args.accept_cli_unavailable:
            emit_json({
                "verdict": "FAIL",
                "error": f"--mr-creation-method=url-fallback 但 {cli} CLI 已装+已认证 · "
                         "违 P0-113 CLI-first(治本 SVC-CORE-B007 case)",
                "cli_check": cli_check,
                "hint": "二选一:① 跑 `glab mr create` 拿真 URL / "
                         "② --accept-cli-unavailable --reason '<原因>' --user-confirmed",
                "spec": "stages/ship-stage.md L17/L109 + P0-113 · v8.37 物化拦截",
            }, exit_code=1)
        # bypass 路径:必带 user-confirmed + reason · 写 concerns + bypass_log
        require_user_confirmed(args)
        reason = args.reason.strip()
        if not reason:
            emit FAIL with hint
        concerns.append(WARN ship-push url-fallback bypass: ...)
        ship.bypass_log.append({type: "url_fallback_when_cli_available", ...})
```

emit 返回 PASS 时携带 `fallback_bypass_warning` 字段(PMO 一眼看到走了 bypass)。

### 测试覆盖(13 个新测试 · 1 个新文件)

新文件 `tools/tests/test_ship_push_url_fallback_gate.py`:

**TestCheckCliAvailableForHost**(5):
- `test_v837_unknown_host_returns_no_cli_mapping`(gitee 等无 CLI)
- `test_v837_github_maps_to_gh / gitlab*→glab`(映射表)
- `test_v837_cli_not_installed_when_which_fails`(mock which 失败)
- `test_v837_cli_not_authenticated_when_auth_status_fails`(mock auth status 失败)
- `test_v837_cli_available_when_both_ok`(mock 都 OK)

**TestHandleShipPushUrlFallbackGate**(8):
- `test_v837_block_when_cli_available_no_bypass`(主拦截)
- `test_v837_pass_when_cli_available_with_full_bypass`(完整 bypass + WARN + concerns + bypass_log)
- `test_v837_block_when_bypass_missing_reason`(reason 缺)
- `test_v837_block_when_bypass_missing_user_confirmed`(user-confirmed 缺)
- `test_v837_pass_when_cli_not_installed`(CLI 不装 · 退化合理)
- `test_v837_pass_when_cli_not_authenticated`(CLI 未认证 · 退化合理)
- `test_v837_pass_when_no_cli_mapping`(gitee 等)
- `test_v837_skip_check_for_cli_method`(cli-glab method 不触发本校验)

### Spec 更新

`stages/ship-stage.md` § 11 物化拦截清单 加 P0-113 v8.37 物化条目:
```
- **v8.37 P0-113 物化**:`--mr-creation-method url-fallback` 时 · `git_host` 对应 CLI
  (github→gh / gitlab*→glab)若**已装 + 已认证** → **BLOCKED**(治本 SVC-CORE-B007 case)。
  逃生口:`--accept-cli-unavailable --reason '<原因>' --user-confirmed`
  (走 bypass log + concerns WARN 留痕)
```

### 设计哲学

case 暴露的本质:**spec 文本写得清楚 ≠ AI 一定遵守**(reader trap)。AI 偷懒 / 误判 / 路径切换都会绕过文本规范。R0 兜底:**可枚举的进脚本物化拦截**:
- "url-fallback 时检测 CLI 可用性" → 可枚举 → 进 state.py 校验
- "CLI 实际能否创 MR" → 不可枚举(网络 / token scope / 平台差异)→ 留 AI/用户判 + 走逃生口

逃生口设计("不一刀切")原则:
- **真不可用场景必须给出口**:网络隔离 / token scope 不够 / 强制内部流程 / CI 限制
- **逃生必留痕**:concerns WARN + bypass_log + 必带 reason · retro 复盘可见

### 向后兼容代价

- 老脚本若已传 `--mr-creation-method url-fallback`(且 CLI 已装+认证):**会 BLOCK**
- 必须显式补 `--accept-cli-unavailable --reason ... --user-confirmed` 才能跑
- ROI 评估:破坏向后兼容 vs **杜绝"AI 偷懒退化"**(case 实证有效)· 用户拍板 A · 值

### 治本与诚实

我之前给 url-fallback 当成"兜底安全网" · 但没意识到 AI 会**优先选退化路径**(写 mr_create_url 比跑 CLI 容易)· 让兜底变成默认。case 实证后看清:**兜底必须有门** —— v8.37 加门(CLI 可用性校验)。

不写"AI 是否真该退化"的语义判断器(那是无底洞)· 只校验客观信号(which + auth status)· 触发即 BLOCK · 留逃生口。R0 哲学:**可枚举进脚本 · 不可枚举留人**(人 = 用户显式确认 · 不是 AI 自决)。

### Hash

- _v8_ship.py:_check_cli_available_for_host(40 行)+ _handle_ship_push 加 bypass 块(60 行)+ argparse 3 个 arg = 净 +110 行
- stages/ship-stage.md:§ 11 加 P0-113 v8.37 物化条目 = 净 +1 行
- SKILL.md:v8.36 → v8.37
- 新文件 test_ship_push_url_fallback_gate.py:13 测试 = 净 +250 行
- docs/CHANGELOG.md:本段

---

## v8.36 · host 改 per-feature state.json + external review 内容质量轻校验(治本 SVC-PLATFORM-F054 case)

> 用户 2026-05-27 贴 SVC-PLATFORM-F054-Admin-Offer-Targeting-Country 实战 case · 提"当前用的什么 host 应该是 state.json 记录 · 且每次 session 启动的时候要修改 · 不应该持久化到一个全局共享文件"。

### case 暴露 2 个独立 bug

**Bug 1(用户问的)· host 全局 audit 跨 session 污染**:
- v8.21 设计:`~/.teamwork/host_audit.json`(用户级 `~/`)· bootstrap 跑后覆盖写当前 host
- case 现场:用户当前在 Codex CLI session · audit 残留上次 Claude Code session 写的 `claude-code` → 推出 model=`codex`(同源)· 异质失效 · 用户手动加 `--host codex-cli --model claude` 才补救
- 根因:全局 audit 是"上次 bootstrap 留的快照"· 不代表"当前 session 的 host"

**Bug 2(沉默更危险)· Claude reviewer 只 echo template 不真 review**:
- case 现场:用户读 `goal-claude.md` 发现"内容没有真正 review PRD · 只是在回复'你给了我 reviewer prompt template'"
- 根因(疑似):v8.30 我改"工具不假设模型名 · 用户自查 codex 交互"时 prompt 弱化成 template · reviewer 误解为复述

### 用户决策

| Bug | 方案 | 用户选 |
|-----|------|--------|
| Bug 1 | A/B/C/D 4 方案 | **A · per-feature state.json** |
| Bug 2 | 同 v8.36 修 / 分 v8.37 / 留下次 case | **"先不额外修 · 只检查空内容和空模版 · 否则认为真评审 · 评质量差告知用户即可不暂停"** |

### Bug 1 治本(state.py + bootstrap.py)

#### 数据模型

state.json 新增 2 字段:
```jsonc
{
  "host": "codex-cli",     // v8.36:per-feature host(治本全局 audit 跨 session 污染)
  "host_history": [        // v8.36:audit list(每次切换 append · 不替换)
    {"host": "codex-cli", "at": "...", "source": "init-feature"},
    {"host": "claude-code", "at": "...", "source": "review-start", "previous": "codex-cli"}
  ]
}
```

#### 入口物化

1. **init-feature `--host`**(可选):写 state.json.host + 初始化 host_history[0]
2. **stage-start `--host`**(可选 · `add_common_stage_start_args` 共用):
   - 与 state.json.host 比对 · 不一致 → 更新 + emit `host_change_warning` + concerns 留痕
   - host_history append(audit 不替换)
3. **external-review** 读取优先级改:
   ```
   ① args.host(显式)
   ② state.json.host(v8.36 主路径 · per-feature)        ← 新增
   ③ ~/.teamwork/host_audit.json(deprecated · audit 路径) ← 加 deprecation_warning
   ④ env fallback / None → BLOCK with hint
   ```
4. **bootstrap.write_host_audit** 在 audit JSON 加 `_deprecated` 注释字段(v8.37 计划删)

#### 关键 helper 变更

```diff
- def _detect_host() -> tuple[Optional[str], str]:
-     # ① ~/.teamwork/host_audit.json
-     # ② env fallback
+ def _detect_host(feature: Optional[str] = None) -> tuple[Optional[str], str]:
+     # ① state.json.host(per-feature · v8.36 主路径)
+     # ② ~/.teamwork/host_audit.json(audit_deprecated · v8.21 兼容)
+     # ③ env fallback
```

### Bug 2 治本(只校验空 / template echo · WARN 不 BLOCK)

新增 `_check_external_review_quality(stdout, stage, model) -> list[dict]`:

```python
EXTERNAL_REVIEW_MIN_BYTES = 200
EXTERNAL_REVIEW_TEMPLATE_ECHO_SIGNATURES = [
    "你给了我", "reviewer prompt template", "I received the prompt",
    "{{stage}}", "{{commit}}", "{{feature_id}}",  # 占位符未替换
    ...
]
```

2 类 WARN(都不 BLOCK · 决策权留用户):
- `empty_content`:stdout < 200 bytes
- `template_echo`:命中 reviewer 自述"只复述 prompt"特征字符串 / 占位符未替换

emit JSON 在 `verdict=OK` 下额外携带 `quality_warnings: [{type, severity, message, ...}]`。

**设计哲学**(用户决策驱动):
- 工具不语义判 reviewer 质量(主观 · 易误判)
- 只校验客观信号(字节数 / 字面匹配)
- WARN 而非 BLOCK · 用户判是否重跑或接受

### 测试覆盖(10 个新测试)

- `TestInitFeature.test_v836_init_feature_writes_host_to_state_json`(主路径)
- `TestInitFeature.test_v836_init_feature_no_host_defaults_to_none`(向后兼容)
- `TestInitFeature.test_v836_init_feature_illegal_host_blocked`(argparse 校验)
- `TestHostAutoDetect.test_v836_state_json_host_main_path`(主路径)
- `TestHostAutoDetect.test_v836_audit_fallback_with_deprecation_warning`(兼容路径 + WARN)
- `TestHostAutoDetect.test_v836_state_json_overrides_audit`(优先级)
- `TestHostAutoDetect.test_v836_detect_host_helper_state_json_priority`(helper 单测)
- `TestExternalReviewContentQuality.test_quality_check_empty_content_warns`
- `TestExternalReviewContentQuality.test_quality_check_template_echo_warns`
- `TestExternalReviewContentQuality.test_quality_check_placeholder_unreplaced_caught`
- `TestExternalReviewContentQuality.test_quality_check_normal_review_passes`(无 false positive)

### 向后兼容代价

- init-feature 不传 `--host` → state.json.host=None / host_history=[](向后兼容 · 老脚本不破)
- external-review 还能 fallback 走全局 audit(deprecation_warning 提醒迁移)
- v8.37 计划删全局 audit 完全断开

### 治本与诚实

我 v8.21 设计全局 audit 时的判断错误:**误把"主对话宿主"当成"用户级偏好"**(per-user 持久化)· 实际它是"per-session × per-feature"属性(用户跨项目可同时操作多个 host)。case 实证后才看清。

Bug 2 修法很克制 —— 不写"AI 判 reviewer 是否真 review"的语义判断器(那是无底洞 · 易误判)· 只校验客观信号 + WARN。这是用户拍板的"工具职责边界"(R0 哲学:可枚举进脚本 · 不可枚举留人)。

### Hash

- state.py:_detect_host 改签名 + cmd_external_review 改 host 探测 + 新 _check_external_review_quality + init-feature --host = 净 +95 行
- _v8_engine.py:add_common_stage_start_args 加 --host + execute_stage_start 校准逻辑 = 净 +25 行
- bootstrap.py:write_host_audit 加 deprecation marker = 净 +6 行
- test_state.py:10 新测试 + TestHostAutoDetect 重写 = 净 +130 行
- SKILL.md:v8.35 → v8.36
- docs/CHANGELOG.md:本段

---

## v8.35 · 自动升级流程 4 个 bug 治本(用户问"是否符合预期"暴露)

> 用户 2026-05-27 问「在检查下 teamwork 自动升级逻辑是否符合预期」· 我端到端验证 v8.24 update-skill + bootstrap check_skill_update 流程 · 实测发现 4 个 bug。

### 4 bug 实测证据

| # | Bug | 实测证据 | 影响 |
|---|-----|---------|------|
| **A** | `update-skill` BLOCK hint 里 `{SKILL_ROOT}` placeholder 未替换 | `cmd_update_skill` line 3009/3029 用普通 str 不是 f-string · hint 输出字面 `cd {SKILL_ROOT}` | 用户复制 cd 命令直接失败 |
| **B** | bootstrap `maintain_gitignore_worktree` 改 SKILL_ROOT 自己的 `.gitignore` · 导致 update-skill 立即 BLOCK | `cd teamwork && bootstrap.py` 后 git status:`M .gitignore`(+4 行 bootstrap 自动加的)· update-skill 拒绝 pull · 死锁链 | 开发 teamwork 自己 / 嵌子目录 skill 场景全撞 |
| **C** | gitignore 重复 comment 文案 | `# Teamwork harness locks ... v8.31` 同句连续出现 2 次(`.claude/scheduled_tasks.lock` + `.claude/agents.lock` 共用 header 但每次都重写) | 美观 |
| **D** | bootstrap auto-maintain 改 .gitignore 不 commit · 累积 dirty | maintain 返 `appended` 但用户无感 · 下次 git status 看着脏 | B 修了 D 也消(skip 后没改) |

### 治本(2 文件 + 5 测试)

#### Bug A:`state.py:cmd_update_skill` hint placeholder

```diff
- "hint": (
-     "skill 是 zip 安装 · 不支持自动 update。\n"
-     "  手动:① 备份本地定制 ② rm -rf {SKILL_ROOT} · "
-     "git clone https://github.com/okteam99/teamwork.git ~/.claude/skills/teamwork"
- ),
+ "hint": (
+     f"skill 是 zip 安装 · 不支持自动 update。\n"
+     f"  手动:① 备份本地定制 ② rm -rf {skill_root} · "
+     f"git clone https://github.com/okteam99/teamwork.git {skill_root}"
+ ),
```

第 2 处 dirty BLOCK hint 同样改为 f-string 用真实 `git_root` · 并加 v8.35 注解(提示 bootstrap auto-maintain dirty 可用 `git checkout --` 丢弃)。

#### Bug B:bootstrap `maintain_gitignore_worktree` 跨仓污染

```diff
- def maintain_gitignore_worktree(project_root: Path) -> dict:
+ def maintain_gitignore_worktree(project_root: Path,
+                                  skill_root: Optional[Path] = None) -> dict:
+     # v8.35 Bug B:skill_root 与 project_root 同一个 git 仓 → skip(防跨仓污染)
+     # 2 种命中场景:
+     #   a) project_root == skill_root(skill 仓就是 repo 根)
+     #   b) skill_root 是 project_root 子目录 + 同一个 git 仓(开发场景 · 当前 teamwork repo
+     #      把 skills/teamwork/ 嵌子目录)
+     if skill_root:
+         pr_resolved = project_root.resolve()
+         sr_resolved = skill_root.resolve()
+         if pr_resolved == sr_resolved:
+             return {"status": "skipped_skill_root_self", "reason": "..."}
+         # git rev-parse --show-toplevel from skill_root → 看是否等于 project_root
+         r = subprocess.run(["git", "-C", str(sr_resolved), "rev-parse",
+                             "--show-toplevel"], ...)
+         if r.returncode == 0 and Path(r.stdout.strip()).resolve() == pr_resolved:
+             return {"status": "skipped_skill_root_self", "reason": "...同一个 git 仓..."}
```

cmd_session_bootstrap 调用方传 `skill_root`:`maintain_gitignore_worktree(project_root, skill_root)`。

**坑修了 2 轮**:我第 1 轮只检查 `project_root == skill_root`(命中 a)· e2e 实测发现当前 teamwork repo 是 `project_root=/teamwork · skill_root=/teamwork/skills/teamwork` —— 二者不相等但同一个 git 仓(命中 b)· bootstrap 仍改了 `/teamwork/.gitignore`。第 2 轮加 `git rev-parse --show-toplevel` 检测同仓判定。

#### Bug C:gitignore 重复 comment 文案 dedup

```diff
+ last_header_written = None  # v8.35 Bug C:连续同 header dedup 状态机
  for pattern, pattern_alt, header in entries:
      if pattern in text or pattern_alt in lines:
+         last_header_written = None  # 中断 dedup
          continue
+     if header == last_header_written:
+         text += f"{prefix_nl}{pattern}\n"      # 共用上一 entry header
+     else:
+         text += f"{prefix_nl}{header}\n{pattern}\n"
+         last_header_written = header
```

### 测试覆盖(5 个新测试)

- `TestMaintainGitignoreWorktree.test_v835_skip_when_project_root_eq_skill_root`(Bug B 命中 a)
- `TestMaintainGitignoreWorktree.test_v835_skip_when_skill_root_nested_in_same_git_repo`(Bug B 命中 b · 关键 case)
- `TestMaintainGitignoreWorktree.test_v835_skill_root_none_still_works`(向后兼容 · 不传 skill_root)
- `TestMaintainGitignoreWorktree.test_v835_skill_root_diff_from_project_root_proceeds`(用户项目场景 · 独立 git 仓)
- `TestMaintainGitignoreWorktree.test_v835_consecutive_same_header_deduped`(Bug C)
- `TestMaintainGitignoreWorktree.test_v835_different_headers_not_deduped`(C 边界)
- `TestUpdateSkillHint.test_update_skill_not_git_repo_hint_uses_real_path`(Bug A)

### 端到端验证

**修前**(主 repo `cd /teamwork && bootstrap.py`):
```
gitignore_worktree = {"status": "appended", "patterns": [".worktree/", ".claude/scheduled_tasks.lock", ".claude/agents.lock"]}
→ M .gitignore  (主 repo dirty)
→ update-skill 立即 BLOCK
```

**修后**(同场景):
```
gitignore_worktree = {"status": "skipped_skill_root_self", "reason": "skill_root(...) 与 project_root(...) 同一个 git 仓(skill 嵌子目录开发场景)· skip..."}
→ git status 干净  ✅
→ update-skill 可正常跑
```

**Bug A 修后**:
```
hint = skill 是 zip 安装 · 不支持自动 update。
  手动:① 备份本地定制 ② rm -rf /private/tmp/v835_us_3Xwiv3 ·
  git clone https://github.com/okteam99/teamwork.git /private/tmp/v835_us_3Xwiv3
```
(用真实 skill_root 替换字面 placeholder)

### 端到端验证清单(符合预期项)

✅ `_version_tuple` 正确(v8.10 > v8.9 / v9.0 > v8.99 / v8.34 == v8.34 / v8.5.1 > v8.5 全 pass)
✅ `check_skill_update` 4 种 status 都按设计返(`up_to_date` / `outdated` / `network_failed` / `parse_failed`)
✅ outdated emit R5 1/2 选项 prompt 文案清晰
✅ bootstrap silent skip 不阻塞(network_failed 也不 abort)
✅ bootstrap marker 版本门禁工作(同版本第 2 次跑 `maintain_status=skipped_version_unchanged`)
✅ update-skill 干跑成功路径(本地 == 线上 v8.35 时返 `same_version=True · 已在最新版本`)

### 治本与诚实

bootstrap 在 teamwork 仓自己里跑 · 改自己的 .gitignore · 这是设计阶段没考虑到的 case —— v8.31 加 maintain_gitignore_worktree 时只想着"用户项目场景"· 没想到 teamwork 仓本身也会被 bootstrap 当成 project。

修法 Bug B 也修了 2 轮:第 1 轮只判 `project_root == skill_root` · 实测发现没命中(teamwork repo skill 嵌子目录)· 第 2 轮加 `git rev-parse --show-toplevel` 同仓判定。**这是典型的"先写测试再实施"会更早暴露的 bug** —— 我应该先写"嵌子目录"的 e2e test 再改代码。

### Hash

- state.py:`cmd_update_skill` 2 处 hint 改 f-string + 加 v8.35 注解 = 净 +6 行
- bootstrap.py:`maintain_gitignore_worktree` 加 `skill_root` 参数 + Bug B skip 块 + Bug C dedup 状态机 = 净 +30 行
- test_bootstrap.py:5 个新测试 + 1 个旧测试加 `subprocess.run git init` = 净 +60 行
- test_state.py:1 个新 `TestUpdateSkillHint` class = 净 +45 行
- SKILL.md:frontmatter v8.34 → v8.35
- docs/CHANGELOG.md:本段

---

## v8.34 · 全局强制必传 `--user-intent + --admission-judgment`(治本 SVC-CORE-M001 case · 删 v8.15 SKIPPED 兼容口子)

> 用户 case 实战 SVC-CORE-M001 Micro:PMO 跑 `prepare-check` 时 emit JSON 里没有 `admission_judgment` 字段也没有 `user_intent` · 用户问「**流程类型判断的时候 AI 经过思考了么?**」—— 答案是没思考(走了 v8.15 留的 SKIPPED 兼容路径 · admission 校验自动 SKIP · audit 里也只是空字符串)。
>
> 这暴露 v8.15 设计妥协:为了"让现有 tests 不破" · 保留了「两参都不传 → SKIPPED」兜底 · 结果 AI 学会钻这个空子跳过 prepare.md §2.1/§2.2 思考。v8.15 物化「你必须想这件事」被 SKIPPED 兜底架空。

### 用户决策与选项对比

提供 4 选项 · 用户拍板 **A · 全局强制必传**:

| 选项 | 描述 | ROI | 风险 |
|------|------|-----|------|
| **A · 全局强制必传(选定)** | 删 SKIPPED 路径 · 不传 → BLOCK | 高 · 案例证明 SKIPPED 让 AI 钻空子 | 中 · 破坏旧脚本 / debug / migration 路径 |
| B · 默认 WARN | 不传 → emit WARN 但不 BLOCK | 中 · 至少留痕 | 低 · AI 仍可忽略 WARN(F037 case 已证) |
| C · strict mode opt-in | 加 --strict flag · 默认 SKIPPED | 低 · 老路径不变 | 高 · opt-in 没人记得开 |
| D · emit hint 加强 | 增加更 loud 的 hint 但不改 verdict | 极低 · 与 v8.15 没本质区别 | 中 · 案例已证 hint 不够 |

### 实施(2 处 1 测试)

1. **`state.py:_validate_admission_judgment`(line 2196-2226)**:
   ```diff
   - # 向后兼容路径:两者都不传 = 旧 prepare-check 用法 · skip admission 校验
   - # 后续可改为硬 BLOCK(本版用 SKIPPED 不阻塞 · 让现有 tests 不破)
   - if not has_intent and not has_judgment:
   -     return {"verdict": "OK", "consistency": "SKIPPED", ...}
   + # v8.34:两者都不传 = BLOCK(治本 SVC-CORE-M001 · 删 v8.15 SKIPPED 兼容口子)
   + if not has_intent and not has_judgment:
   +     return {"verdict": "FAIL", "consistency": "FAIL",
   +             "error": "--user-intent + --admission-judgment 必传(v8.34 全局强制 ...)",
   +             "hint": "用法 + 示例 + TEAMWORK_BYPASS_PREPARE_CHECK 引导"}
   ```

2. **`state.py:cmd_prepare_check`(comment line 2145)**:`consistency: OK / MISMATCH / FAIL`(去掉 `SKIPPED` 文档)

3. **测试更新**:
   - `TestAdmissionJudgment.test_no_intent_no_judgment_skipped` → `test_no_intent_no_judgment_blocked` · 改 assert FAIL + hint 含 `TEAMWORK_BYPASS_PREPARE_CHECK` 引导
   - `TestPrepareCheck._check` 工具改为同时传 `--user-intent + --admission-judgment`(测试聚焦于 id_letter 路由等其他逻辑 · fixture 合成 consistent judgment)
   - `TestPrepareCheck.test_no_flow_type_defaults_to_f_with_warn`/`test_empty_series_starts_at_001` 同步更新
   - `TestPrepareAuditGate.test_init_feature_passes_after_prepare_check` 同步更新

### SKILL.md 同步更新

`§ 物化硬墙` 那段 v8.15 描述补 v8.34:
- 「v8.34 删 v8.15 留的 SKIPPED 兼容口子(治本 SVC-CORE-M001 case AI 不传两参跳过思考)· 全局强制必传」
- bypass 注解澄清:`TEAMWORK_BYPASS_PREPARE_CHECK=1` 走 init-feature 门禁旁路 · **不影响 prepare-check 本身的 admission_judgment 校验**(debug/migration 场景仍需手填 admission_judgment · 或直接绕过 prepare-check 不调用)

### 治本与诚实

我 v8.15 给自己留了一条 SKIPPED 兼容路径 · 理由是「让现有 tests 不破」· 这是典型的「短期权宜 / 长期债」:
- 短期:v8.15 上线时不需要回头改 TestPrepareCheck 6 个测试用例 + TestPrepareAuditGate 1 个
- 长期:AI 在真实 PMO 跑路径下学会走 SKIPPED 兜底 · v8.15 物化「你必须想这件事」被架空 · 案例 SVC-CORE-M001 暴露

v8.34 偿还这笔债 · 删 SKIPPED · 同步修测试(7 处测试 fixture · 加 4 行合成 judgment)。

### 向后兼容代价(诚实记录)

调用 prepare-check 不传 `--user-intent + --admission-judgment` 的旧调用方都会 BLOCK:
- 老 PMO session 调试 / 历史脚本 → 需补传两参 · 或临时绕过(不调 prepare-check 直接走 init-feature 但 init-feature audit gate 也会 BLOCK · 改 `TEAMWORK_BYPASS_PREPARE_CHECK=1`)
- migration 工具 → 同上

ROI 评估:破坏向后兼容 vs AI 思考透明度。用户选 A 的逻辑:**SVC-CORE-M001 case 证明 SKIPPED 路径让 AI 偷懒**。代价值。

### Hash

- state.py: `_validate_admission_judgment` 改 + comment 改 = 净 +35 行(主要是更详的 hint 文案)
- test_state.py:`_check` helper + 3 个测试 + 1 个 TestAdmissionJudgment 测试 = 净 +50 行
- SKILL.md:v8.15 那行加 v8.34 注 + bypass 澄清
- docs/CHANGELOG.md:本段

---

## v8.33 · 修 v8.31 NameError 致命 bug + 加 e2e sanity test 防再发

> 用户 case 实战 INFRA-M002:`state.py ship-finalize` 撞 `NameError: name 'feature_dir' is not defined` —— v8.31 我加 `_classify_main_sync_dirty` 时调用方误传 `feature_dir`(undefined)· 应是 `artifact_root`(同函数内 line 1097 已定义)· runtime 跑到 step 7 才崩 · 单元测试没覆盖完整 cmd 路径所以漏。

### 1 行 fix

```diff
- dirty_result = _classify_main_sync_dirty(main_wt, feature_dir, state)
+ dirty_result = _classify_main_sync_dirty(main_wt, artifact_root, state)
```

### 防再发:e2e sanity test

v8.31 / v8.32 我做了 `_classify_main_sync_dirty` 单元测试 · 但**没测 cmd_ship_finalize 完整路径**(单元测试不会撞调用方 NameError)。

v8.33 加 `TestCmdShipFinalizeStep7NoNameError`:
- fake bare remote + main repo + state.json(phase=merged)
- `TEAMWORK_BYPASS_MAIN_WORKTREE=1` bypass precheck
- 跑 `state.py ship-finalize --feature <fake>` · step 1-6 全 skipped(因 phase merged)· 直入 step 7
- **关键断言**:stderr/stdout 不含 `NameError` + emit 含 `main_sync_status`(证明真进 step 7)

实测验证:
- 修后:test PASS(NameError 消失 · emit 含 main_sync_status)
- 临时回滚 fix:test FAIL("NameError 再现 · stderr...")· **抓得住 v8.31 bug**

### 设计反思:为什么 v8.31 漏测

| 测试层 | v8.31 覆盖 | 漏哪 |
|---|---|---|
| 单元(`_classify_main_sync_dirty`) | ✅ 7 tests | 函数本身行为对 · 但**调用方误用变量名**不在测试范围 |
| e2e(`cmd_ship_finalize` 完整)| ❌ 0 tests | 撞 NameError 在此层暴露 |

v8.31 我加新 helper 时只测了 helper · 没测调用集成 · **静态语法 check pass(Python 函数内 NameError 是 runtime)** · 漏到 user case 报告。

v8.33 加 e2e 测试 · 至少 cmd_ship_finalize 跑完不抛 NameError —— 后续 step 7 改造可被这测试兜底。

### 同型漏洞检查

`_v8_ship.py` 其他类似 helper 调用(`_step_state_sync` / `_finalize_push_plumbing`)在 cmd_ship_finalize 内是否变量名对?手工 grep 检查:

```bash
$ grep "_step_state_sync(\|_finalize_push_plumbing(\|_classify_main_sync_dirty(" _v8_ship.py
1086:    sync = _step_state_sync(main_wt, feature_path)   # ✅ feature_path = args.feature(line 1074 定义)
1207:    finalize_ok, fin_warn, finalize_commit_hash = _finalize_push_plumbing(
1208:        main_wt, artifact_root, state_json_path, merge_target, state, ship,  # ✅ 已用 artifact_root
1355:    dirty_result = _classify_main_sync_dirty(main_wt, artifact_root, state)   # ✅ v8.33 修后
```

→ 其他 2 处调用变量名正确 · 仅 v8.31 这处 bug。

### 用户 case 实际影响

| 阶段 | 状态 |
|---|---|
| ship-finalize step 1-6 | ✅ 都跑了(因 NameError 在 step 7 触发)|
| state.json `current_stage` | ✅ `completed` |
| state.json `ship.shipped` | ✅ `merged` |
| worktree 物理删 | ✅ 删了 |
| origin/staging finalize-push commit | ✅ 推了 |
| **step 7 main-sync** | ❌ **崩 NameError · 用户手工 git pull**(用户 case)|

→ Feature 数据完整 ship · 只 step 7 自动 ff-pull 没跑 · 用户手工补不损失数据 · 但**体验不好**。

### v8.x ship-finalize 治本累积(5 次)

| 版本 | 治本 | 状态 |
|---|---|---|
| v8.16 | step 0 state-sync | ✅ |
| v8.18 | finalize-push 0 delta | ✅ |
| v8.31 | step 7 智能 dirty 分类(设计 + 实施 1) | ⚠️ 实施有 bug |
| v8.32 | 修 v8.31 stash+pop 撞 feature_artifacts | ✅ |
| **v8.33** | **修 v8.31 NameError + 加 e2e sanity** | **✅ 完整** |

### SKILL.md frontmatter

`v8.32` → `v8.33`

---

## v8.32 · 修 v8.31 step 7 实施 bug · 分类型处理(feature_artifacts checkout · 其他 stash+pop)

> 用户问:"改完后 ship 2 阶段后工作区是干净的么"。
> 诚实复盘 v8.31:**设计意图对 · 实施有 bug** —— stash 全部 dirty(包括 feature_artifacts)· pull 后 pop 会撞 feature_artifacts 冲突(stash 是 ship-finalize 前的旧版 · pop 回 working tree 时与 pull 下来的新版冲突)。case 实测会触发 `pulled_unstash_conflict` · 工作区**反而更乱**。

### v8.31 漏洞复盘

```
v8.31 流程(错):
  stash push -u       ✅ 5 文件 stash(含 state.json 旧版)
  pull --ff-only      ✅ 拉 origin(state.json 新版进 working tree)
  stash pop           ❌ state.json 冲突(stash 旧 vs working tree 新)
  → main_sync_status="pulled_unstash_conflict"
  → stash 保留 + 工作区有冲突标记
```

### v8.32 治本:分类型处理

不同类别 dirty 性质不同 · 不能一刀切 stash 全部:

| 类别 | 性质 | 处理 |
|---|---|---|
| **`feature_artifacts`** | 本地必旧(ship-finalize 是最权威推送 · origin 有新版) | **丢本地** `git checkout origin/<merge_target> -- <files>` 用 origin 新版 |
| **`bootstrap_pointers`** | origin 不改这些文件(bootstrap 本地维护) | **stash 仅这些 + pop**(无冲突) |
| **`harness_locks`** | origin 不改(G2 fix 后新项目不再 commit) | 同 bootstrap_pointers |

### v8.32 流程

```python
# 1. classify dirty
# 2. 若 other_files 非空 → 跳过(同 v8.16)
# 3. checkout feature_artifacts(丢本地旧版 · 用 origin 新版)
for f in dirty_result["feature_artifacts"]:
    git checkout origin/<merge_target> -- f

# 4. 剩 bootstrap + locks 处理
remaining = bootstrap_pointers + harness_locks
if not remaining:
    git pull --ff-only  # working tree 等价 clean(checkout 后 = origin)
else:
    # stash 仅 bootstrap + locks(不含 feature_artifacts · 已 checkout)
    git stash push -u -m <msg> -- <remaining files...>  # 路径 stash
    git pull --ff-only
    git stash pop  # bootstrap/locks 不在 origin 改 · pop 不冲突
```

### 新增 `main_sync_status` 状态值

| status | 含义 |
|---|---|
| `checkout_pulled` | feature_artifacts checkout + ff-pull(无 bootstrap/lock dirty)|
| `checkout_stashed_pulled_unstashed` | feature_artifacts checkout + bootstrap/lock stash + ff-pull + pop |
| `checkout_failed` | feature_artifacts checkout 失败(罕见 · 网络/权限)|
| `stash_failed_after_checkout` | checkout 成功 · 但 bootstrap/lock stash 失败 |
| `diverged` | checkout 后 ff-pull 失败(分叉)|
| `diverged_stash_popped` | checkout + stash 后 ff-pull 失败(分叉)· stash 已 pop |
| `pulled_unstash_conflict` | bootstrap/lock pop 冲突(极罕 · origin 通常不改这些)|
| 其他(v8.31)| `ff_pulled` / `wrong_branch` / `fetch_failed` 不变 |

### INFRA-F025 case 用 v8.32 重跑(对照 v8.31)

```
5 dirty:
  - state.json + review-log.jsonl(feature_artifacts)
  - AGENTS.md + CLAUDE.md(bootstrap_pointers)
  - .claude/scheduled_tasks.lock(harness_locks)

v8.31(错):
  stash all 5 → pull → pop  → state.json 冲突 → stash 保留 + 冲突标记
  → main_sync_status="pulled_unstash_conflict"
  → 工作区反而更乱

v8.32(对):
  checkout origin/staging -- state.json review-log.jsonl(本地旧 → origin 新)
  stash bootstrap + lock 3 文件
  pull --ff-only(成功)
  stash pop(成功 · 因 origin 没改 bootstrap/lock)
  → main_sync_status="checkout_stashed_pulled_unstashed"
  → feature_artifacts clean · bootstrap/lock 保留原 dirty(等用户 commit / G2 ignore)
```

### 用户问的精确答案

**Q:改完后 ship 2 阶段后工作区是干净的么?**

| 文件类别 | v8.32 后状态 |
|---|---|
| `feature_artifacts`(state.json / review-log.jsonl)| ✅ **clean**(checkout 用 origin 新版覆盖) |
| `bootstrap_pointers`(AGENTS.md / CLAUDE.md / GEMINI.md)| ⚠️ **保留原 dirty**(stash + pop · 等用户下次 commit · 或 bootstrap 重 maintain)|
| `harness_locks`(.claude/*.lock)| ⚠️ **保留原 dirty**(历史 commit 的 lock 文件 · G2 fix 后新项目不再 commit · 历史项目用户自行 `git rm --cached`) |
| `other_files`(用户代码 / 文档)| ⚠️ **不动**(同 v8.16 跳过 · WARN 列分类 hint)|

→ **feature 相关 100% clean**;bootstrap / lock 是工具副产物 · 不影响后续 Feature(下次 ff-pull 仍 work)· 但用户 `git status` 仍会看到这些 dirty 行。

完全 100% clean 需要 G3(bootstrap auto-commit)和 G2 历史 lock 清理(用户手工 `git rm --cached`)· 这两件是**项目级人工配合** · 不是 teamwork 单方面能解决。

### 测试覆盖

`TestClassifyMainSyncDirty` 7 test 不变(仅测分类逻辑 · 不测 stash 流程)· 实际 stash + pop 行为在 case 实测 + 后续 cases 验证。0 regression。

### v8.31 设计思路保留 · v8.32 仅实施修正

v8.31 的 4 类分类设计正确 · v8.32 只修"统一 stash"的实施错误。分类常量 / `_classify_main_sync_dirty` helper 不变。

### SKILL.md frontmatter

`v8.31` → `v8.32`

---

## v8.31 · ship-finalize step 7 智能 dirty 处理 + bootstrap gitignore 扩展(治本 INFRA-F025 主工作区残留 case)

> 用户提问:工作区有残留 · 看下是不是 ship 规范有问题 · 理论上 feature 结束工作区应该干净。
> case-AI 自诊 4 个缺口 G1-G4 全是 teamwork 框架级。

### case-AI 诊断 4 个缺口

| ID | 内容 | v8.31 治本 |
|---|---|---|
| **G1** | ship-finalize step 7 dirty 一刀切跳过 ff-pull | ✅ 智能 dirty 分类 + stash+ff-pull+unstash |
| **G2** | `.claude/scheduled_tasks.lock` 漏 gitignore | ✅ bootstrap maintain_gitignore 扩展 |
| **G3** | bootstrap 改 AGENTS.md / CLAUDE.md 不 commit · dirty | ✅ G1 智能分类涵盖(bootstrap_pointers 类) |
| **G4** | finalize-push 后用户看 git status 误判残留 | ✅ emit `main_sync_status` + `main_sync_note` 透明 |

### G1 治本:step 7 智能 dirty 处理

新增 `_classify_main_sync_dirty(main_wt, feature_dir, state)` helper · 分类 4 类:

| 类别 | 内容 | safe_to_stash |
|---|---|---|
| `feature_artifacts` | `<feature_dir>/state.json` + `review-log.jsonl` | ✅(工具副产物 · ship-finalize plumbing 推到 origin 的版本) |
| `bootstrap_pointers` | `AGENTS.md` / `CLAUDE.md` / `GEMINI.md` | ✅(bootstrap 注入段 · 版本号变化) |
| `harness_locks` | `.claude/*.lock` | ✅(session pid · G2 修后会 ignore · 历史 commit 漏 ignore 仍可 stash) |
| `other_files` | 其他(用户代码 / 文档) | ❌ 不安全 |

step 7 流程:
1. **fetch + 检测 dirty 分类**
2. **clean** → 直接 `ff-pull`(原 v8.16 路径)
3. **dirty 全副产物**(`other_files=[]`)→ **`stash push -u` + `pull --ff-only` + `stash pop`**:
   - 成功 → `main_sync_status="stashed_pulled_unstashed"` · 主工作区 clean 且最新
   - unstash 冲突 → 保留 stash + WARN(`pulled_unstash_conflict`)
   - 分叉 ff-pull fail → stash 已 pop · WARN(`diverged_stash_popped`)
4. **dirty 含 other**(用户真改动)→ 同 v8.16 跳过 + WARN(`skipped_user_changes`)· 列分类 hint

### G2 治本:bootstrap.py maintain_gitignore 扩展

`maintain_gitignore_worktree` entries 加 2 项:
```python
(".claude/scheduled_tasks.lock", ..., "# Teamwork harness locks (session pid · v8.31)"),
(".claude/agents.lock", ..., "# Teamwork harness locks (session pid · v8.31)"),
```

各项目 bootstrap 跑时自动加 · 不需每个项目手工 fix。**历史已 commit 的 lock 文件不自动 `git rm --cached`**(避免破坏现有项目)· 用户可手工清。

### G3 治本:bootstrap_pointers 类纳入 step 7 智能处理

bootstrap.py 改 AGENTS.md / CLAUDE.md / GEMINI.md(注入段版本号)后不 commit · 这是已知设计(避免污染主分支 commit 历史)。v8.31 step 7 把这 3 个文件归 `bootstrap_pointers` 类 · 自动 stash + ff-pull + unstash · 不阻塞同步。

### G4 治本:emit `main_sync_status` 透明留痕

```json
{
  "verdict": "PASS",
  "command": "ship-finalize",
  "main_sync_status": "stashed_pulled_unstashed",   // v8.31 新
  "main_sync_note": "v8.31 智能 dirty 处理:stash 5 个副产物文件(feature_artifacts, bootstrap_pointers, harness_locks)· ff-pull · unstash · 主工作区现 clean 且最新"
}
```

7 个 status 值:
- `ff_pulled`(clean · 直接 pull)
- `stashed_pulled_unstashed`(v8.31 智能处理)
- `pulled_unstash_conflict`(已 pull · unstash 撞冲突 · stash 保留)
- `diverged`(clean · 但分叉)
- `diverged_stash_popped`(dirty stash · 分叉)
- `skipped_user_changes`(dirty 含 other · 不动)
- `wrong_branch` / `fetch_failed` / `stash_failed`

PMO 看 status 直接知道主工作区状态 · 不再误判"feature 工作没收尾"。

### INFRA-F025 case 用 v8.31 重跑

```bash
$ state.py ship-finalize --feature ...
# step 1-6 同 v8.16+
# step 7 v8.31:
#   - fetch ✅
#   - dirty:state.json + review-log.jsonl(feature_artifacts) +
#            AGENTS.md + CLAUDE.md(bootstrap_pointers) +
#            .claude/scheduled_tasks.lock(harness_locks)
#   - other_files=[] → safe_to_stash=True
#   - git stash push -u → git pull --ff-only → git stash pop
#   - main_sync_status="stashed_pulled_unstashed"
#   - 主工作区 clean 且本地 commit 同 origin
```

→ 用户**不再看到 5 dirty 文件**(全自动同步)· 不再误判 "feature 工作没收尾"。

### 测试覆盖(+8 · 0 regression)

`TestClassifyMainSyncDirty`(7 test):
- clean / feature_artifacts / bootstrap_pointers / harness_locks 各类 safe_to_stash
- 用户代码 (src.py) not safe
- **`test_infra_f025_case_mixed_all_safe`** · case 复刻(5 dirty 全副产物)
- feature_dir 内非 artifacts(如 PRD.md)= 用户改动 not safe

`test_v831_harness_locks_appended`(test_bootstrap.py · 1 test):
- maintain_gitignore_worktree 自动加 `.claude/*.lock` 2 项

### 历史 case 受益(G2 历史污染)

INFRA-F025 case 中用户提到 `.claude/scheduled_tasks.lock` 历史 commit `21b19f2d` 误入 · 每 session 写 pid → 永远 dirty。v8.31 后:
- **新项目**:bootstrap 自动 ignore · 不会再误 commit
- **历史项目**(含已 commit lock):用户自行 `git rm --cached .claude/*.lock` · 之后 bootstrap 维护的 ignore 段生效

teamwork **不自动 `git rm --cached`**(避免破坏现有项目 / 误删用户实际依赖的 lock)。

### 与 v8.16 / v8.18 ship-finalize 治本对比

| 版本 | 治本对象 |
|---|---|
| v8.16 | step 0 state-sync(worktree state.json → 主工作区) |
| v8.18 | finalize-push 0 delta(预设字段 · 去自引用 · multi-file) |
| **v8.31** | **step 7 智能 dirty 处理 + G4 透明 emit** |

3 次 ship-finalize 螺旋上升 · 都是"工具自动同步 vs PMO 手工收尾"的物化。

### SKILL.md frontmatter

`v8.30` → `v8.31`

---

## v8.30 · 修虚构 `gpt-5-codex` 字面 · 改"工具不假设模型名 · 用户自查"模式

> 用户截图揭穿:codex CLI 0.133 交互界面**没 gpt-5-codex 模型** —— 我 v8.23 用的字面是**虚构**(从 case-AI string 看到照搬 · 没核实 codex CLI 实际支持)。即使 API key 用户显式 `--codex-model gpt-5-codex` 也会 400(模型不存在)。
> 治本:argparse help / spec 示例 / 测试断言 · 不硬编码模型名(避免随 codex CLI 升级再次淘汰)。

### 用户截图实证(codex CLI v0.133)

```
1. gpt-5.5 (current · Frontier)         ← codex CLI 默认
2. gpt-5.4 (Strong everyday coding)
3. gpt-5.4-mini (Small/fast/cheap)
4. gpt-5.3-codex (Coding-optimized)     ← 真正的 "code review 模型"
5. gpt-5.3-codex-spark (Ultra-fast)
6. gpt-5.2 (Professional / long-running)
```

→ 我 v8.23~v8.29 一直用的 `gpt-5-codex` 是**虚构字面**(不在列表中)。

### 我的 v8.23 错(诚实记录)

```python
# v8.23 _build_codex_prompt
"... Profile reference: codex-agents/{profile_filename}. ..."
# v8.23 _run_codex_review
cmd += ["--config", f"model=gpt-5-codex"]  # ← 虚构字面 · 从 case-AI string 照搬
# v8.23 argparse help
"API key 用户可显式 gpt-5-codex / gpt-5-pro 等专业 review 模型。"  # ← 误导举例
```

**错的根因**:从 case-AI 输出的字符串看到 `gpt-5-codex` 就**照搬作为默认值** · **没跑 `codex --help` / `codex` 交互界面核实实际支持的模型名**。

类似 v8.23 之前 "假设 codex review 支持 `--commit + [PROMPT]` 不互斥" 错(经 v8.25 治本) · 这次又一类:**没核实外部工具实际接口就假设**。

### v8.30 治本

#### 原则:不硬编码外部工具模型名

- spec / state.py / argparse help / 测试 · **不举具体模型字面作"默认推荐"**
- 用占位符:`<your-codex-model>` / `<name>` / "用户自查"
- 一处提示获取真实名:`codex` 交互界面 / `codex --help`

#### 1. `state.py argparse --codex-model` help 改

```
--codex-model
  [v8.30] codex CLI 用的具体模型(传给 codex --config 'model=<this>')·
  优先级:--codex-model > .teamwork_localconfig.json external_review.codex_model >
  **不传**(用 codex CLI 默认 · 兼容 ChatGPT 订阅 · 治本 ChatGPT 账号不允许显式模型 case)。
  🔴 模型字面 **不假设** —— codex CLI 版本迭代会换模型名 · 跑 `codex` 交互界面选 /
  或 `codex --help` 查 · ChatGPT 订阅可能拒绝任何显式 model · 仅 API key 模式可显式。
```

#### 2. state.py 注释删 "gpt-5-codex" 例

```python
# v8.30 codex_model 此时可能 None / config 配字面 / 显式覆盖值
# (不再举具体模型 · 避免误导)
```

#### 3. standards/external-model-usage.md §11.5 加 v8.30 段

- v8.29 / v8.30 合并说明
- 列出用户截图的 codex CLI 0.133 真实可选模型(实证 · 标 v0.133 时点)
- 🔴 "codex CLI 升级会换模型名 · spec 不硬编码"
- 示例 `--codex-model gpt-5.3-codex`(用截图实有 · 但注释"v0.133 时点 · 自查")

#### 4. 测试 gpt-5-codex → gpt-5.3-codex

测试断言改用截图实有模型(v0.133)· 但**测试不验证模型字面正确性**(只验 state.py 字符串传递)· 所以即使未来 gpt-5.3-codex 淘汰 · 测试仍 PASS(测的是 state.py 行为 · 不是 codex CLI 模型支持)。

### 历史段保留 · 不改

CHANGELOG v8.23 / v8.25 / v8.26 / v8.28 / v8.29 段的 `gpt-5-codex` 字面**保留不改** —— 那是诚实记录我的演进路径(包括错)· 改了会失真。

standards §11.5 v8.20 / v8.26 段同样保留(历史)· 新加 v8.30 段统一说明。

### 设计反思:外部工具假设的代价

v8.x 已实证 2 次"假设外部工具接口被实际打脸":

| 版本 | 假设 | 实际(case 暴露) | 治本 |
|---|---|---|---|
| v8.20 | `codex review --commit X --base Y --title Z` 三个 flag 兼容 | `--commit/--base` 互斥(case F035) | v8.23 改 PROMPT 模式(也错) → v8.25 改 codex exec → v8.26 review→codex review |
| **v8.23** | **`gpt-5-codex` 是 codex CLI 支持的模型** | **虚构 · 不存在(用户截图)** | **v8.30 不硬编码模型名 · 用户自查** |

教训:**任何"外部工具支持 X"假设 · 必先 `<tool> --help` / 交互界面核实**。后续 v8.x 加新外部 CLI 集成(gemini / deepseek 等)· 必先核实实际接口。

### 测试覆盖(0 新 test · 0 regression)

`test_v829_*` / `test_v823_codex_model_explicit_override` 等 5 个测试改用 `gpt-5.3-codex` 字面(用户截图实有 · v0.133 时点)· 但测试断言聚焦 state.py 行为(字面正确传递)· 不验证 codex CLI 接受 · 所以即使未来字面再变 · 测试仍 PASS。

### F029-F037 已写的 `external-cross-review/` 文件不受影响

历史 Feature 已 commit 的 `*-codex.md` 文件 frontmatter `review_model:` 字段如果有 `gpt-5-codex` · v8.19 校验只看是否含 "codex" 字面(白名单)· 不验证模型存在性 · **PASS**(向后兼容)。

### F037 case 用 v8.30 重跑

```bash
$ state.py external-review --feature ... --stage blueprint
# v8.21 host 自动 → claude-code → model=codex
# v8.29 codex_model=None(无 args 无 config)→ 不传 --config
# v8.30 永不踩虚构模型(因为不传)
# → codex exec '[Review title: ...] <PROMPT>'
# → ChatGPT 订阅 200 · API key 用 codex 当前默认(v0.133 = gpt-5.5)· 都 OK
```

### SKILL.md frontmatter

`v8.29` → `v8.30`

---

## v8.29 · codex_model 默认改 None(治本 ChatGPT 订阅死锁 · 显式 model 400)

> 用户 case 触发:codex CLI 用 ChatGPT 订阅(不是 API key)· state.py 强制 `--config 'model=gpt-5-codex'` → 400 `The 'gpt-5-codex' model is not supported when using Codex with a ChatGPT account`。gemini CLI 未装 · 两个异质模型都不可用 · 形成死锁。
> 根因:v8.23 我加 `--config model=gpt-5-codex` 默认值 · 没考虑 ChatGPT 订阅限制("只允许账号默认模型")。

### 漏洞复盘

```bash
# v8.23 ~ v8.28(漏洞)
state.py external-review --feature X --stage review
# → 工具默认强制 codex_model='gpt-5-codex'
# → codex review --config 'model=gpt-5-codex' ...
# → 400 invalid_request_error: ChatGPT 账号不允许显式模型
# → state.py 无法绕过(物化主路径强制)· 死锁
```

ChatGPT 订阅 vs API key 调用差异(未在 v8.23 考虑):

| codex CLI auth | 是否允许 `--config model=...` |
|---|---|
| ChatGPT 订阅 | ❌ **不允许** · 只能用账号默认模型 |
| API key | ✅ 允许任意模型(gpt-5 / gpt-5-codex / gpt-5-pro) |

### v8.29 治本(3 层 fallback)

```python
# v8.29 _run_codex_review
model_args = ["--config", f"model={codex_model}"] if codex_model else []
# codex_model 非空才传 · 默认空(用 codex 账号允许的默认模型)

# cmd_external_review 解析优先级
codex_model = getattr(args, "codex_model", None)
if not codex_model:
    cfg = read .teamwork_localconfig.json
    codex_model = cfg.get("external_review", {}).get("codex_model")
# 仍空 → 不传 --config(ChatGPT 订阅兼容默认)
```

### 3 个使用场景

```bash
# ① ChatGPT 订阅用户(新默认 · 兼容)
state.py external-review --feature X --stage review
# → codex review --commit X --title Z ...   # 不带 --config · 200 ✅

# ② API key 用户单 Feature override(显式)
state.py external-review --feature X --stage review --codex-model gpt-5-codex
# → codex review ... --config 'model=gpt-5-codex'   # 200 ✅

# ③ API key 用户项目级一次配(.teamwork_localconfig.json)
{
  "external_review": {
    "codex_model": "gpt-5-codex"
  }
}
# 之后所有 state.py external-review 默认用 gpt-5-codex(同 ②)
```

### emit JSON 透明留痕

```json
{
  "verdict": "OK",
  "command": "external-review",
  "codex_model": null,      // v8.29 默认 null(ChatGPT 订阅)· 显式 / config 后是字面值
  "preview_command": "codex review --commit X --title Z ..."   // 默认不含 --config
}
```

→ PMO 看 `codex_model` 字段就知道用了哪个模型 / 是否走 ChatGPT 默认。

### --codex-model argparse help 更新

```
--codex-model
  [v8.29] codex CLI 用的具体模型(传给 codex --config 'model=<this>')·
  优先级:--codex-model > .teamwork_localconfig.json external_review.codex_model >
  **不传**(用 codex CLI 默认 · 兼容 ChatGPT 订阅 · 治本 ChatGPT 账号不允许显式模型 case)。
  API key 用户可显式 gpt-5-codex / gpt-5-pro 等专业 review 模型。
```

### 测试覆盖(+4 · 0 regression)

`TestExternalReviewCommand` 新增 v8.29 4 个:
- `test_v829_chatgpt_subscription_compat_default_no_model_flag`:**治本核心** · 3 stage 默认 codex_model=None · 不传 --config
- `test_v829_explicit_codex_model_overrides_default`:--codex-model gpt-5-codex 显式
- `test_v829_config_external_review_codex_model_fallback`:.teamwork_localconfig.json fallback
- `test_v829_explicit_overrides_config`:显式 > config 优先级

**改造旧测试**(适配 default None):
- `test_v823_codex_model_default_gpt_5_codex` → 改名应 · 现断言 default None + 不含 --config
- `test_v823_emit_includes_cwd_and_codex_model` → codex_model 断言 None
- `test_dry_run_includes_preview_command` → 断言不含 --config

### standards/external-model-usage.md §11.5 加 v8.29 子节

- ChatGPT 订阅 vs API key auth 模式对比表
- 3 层 fallback 优先级
- 3 个使用场景示例

### F037 case 用 v8.29 重跑

```bash
$ state.py external-review --feature ... --stage blueprint
# v8.21 host 自动 → claude-code → model=codex
# v8.29 默认 codex_model=None → 跑 codex exec(不带 --config)
# ChatGPT 订阅成功 200 · 不再 400
# 死锁解 · 异质 review 跑通
```

### gemini CLI 不可用(env 问题 · 不治本)

用户 `which gemini` 不在 · state.py 已正确 BLOCK with hint(install / change-review-roles)· 不需 fix。v8.29 治本 codex 后 · 单 host 单 model 路径已通 · 不需 gemini fallback。

### SKILL.md frontmatter

`v8.28` → `v8.29`

---

## v8.28 · test 验证物化 · `state.py test-complete --run-tests`(治本 F037 AI 自报 stdout 漏洞)

> F037 case 触发:case-AI 跑 3 framework test → 提交 `pm_verdict: FRAMEWORK_ONLY_SHIP_NOT_RECOMMENDED` 自承"67 test 0 实施 · 借 context 不够"。用户 "不要找理由" 后 · 真补 17 集成 test 全 PASS · 证明 context 够 · **理由是借口**。
> 用户洞察:**test stage case 验证交给 python 指定调 exec · 不放主窗口 · 不占用主窗口上下文 · 后续动态指定模型也方便**。
> 治本 v8.x 最深层漏洞:`dev/test-complete` 信 "AI 自报 stdout / exit_code" · AI 可跳测试 / 伪造日志 / 借 "context 不够" 不做。

### 漏洞复盘

```bash
# v8.27 及之前(漏洞)
state.py test-complete --integration-test-exit-code 0 --e2e-test-exit-code 0 \
  --test-stdout "ok 67 passed"   # ← AI 自报 · 工具信
# 实际 AI 可能只跑 3 个 framework test · 写假 stdout · state.py 看 exit_code=0 就 PASS
```

→ 与 v8.15 admission(AI 自报 flow_type)同型 · 测试维度此前未物化。

### v8.28 治本(test 验证物化主路径)

```bash
# 新主路径
state.py test-complete --feature <path> --run-tests
# 工具内部:
# 1. 读 .teamwork_localconfig.json test_commands(优先级:--test-cmd > by_feature_id_pattern > default)
# 2. subprocess.run(cmd · 30min timeout · capture stdout/stderr/exit_code)
# 3. 完整 log 落 <feature_dir>/test-stdout.log(主 PMO context 不读)
# 4. emit JSON 仅 tail 100 行 + exit_code + duration + log_path(主 context 几行)
# 5. 自动设 evidence.integration_test_exit_code = subprocess 真实 exit_code
# 6. AI 不能伪造 / 不能跳 / 不能借 "context 不够"
```

### 用户洞察的 3 个精准点

1. **python 指定调 exec**(subprocess 物化 · 不是 AI 自报)
2. **不放主窗口 · 不占用主窗口上下文**(log 落盘 · emit 只 tail · 主 context 仅几行)
3. **后续动态指定模型也方便**(类似 v8.20 external-review host→model 映射 · 物化主路径已建好接口)

### 设计实现

#### 1. `_v8_engine.py` 加 helper

**`_resolve_test_cmd(args, feature_id, project_root)`**(优先级解析):
- `--test-cmd` 显式传 → 最优先
- `config.test_commands.by_feature_id_pattern` fnmatch 匹配 → 次优先(如 `SVC-CORE-F037-*`)
- `config.test_commands.default` → 兜底
- 都无 → 返 error("先配 .teamwork_localconfig.json · 或显式 --test-cmd · 或回退 --integration-test-exit-code deprecated")

**`run_tests_via_subprocess(cmd_str, cwd, timeout_sec, log_path, tail_lines)`**:
- `subprocess.run` shell=True(支持 pipe / glob)· capture stdout + stderr
- 完整 log 落盘(含 metadata header:cmd / cwd / exit_code / duration / timed_out)
- 返 dict:exit_code / stdout_tail / stdout_total_lines / duration_sec / log_path / cmd / timeout
- 异常处理:timeout → exit_code=124 · cmd 不存在 → exit_code=127

#### 2. `_add_stage_specific_args` 加 test stage flag

```python
elif stage_name == "test" and phase == "complete":
    parser.add_argument("--integration-test-exit-code", ..., help="[deprecated] AI 自报")
    parser.add_argument("--e2e-test-exit-code", ..., help="[deprecated] AI 自报")
    # v8.28 物化主路径
    parser.add_argument("--run-tests", action="store_true",
                        help="工具自跑 · capture exit_code · AI 不能跳")
    parser.add_argument("--test-cmd", default=None,
                        help="覆盖 config · 一次性传")
```

#### 3. `execute_stage_complete` test stage 分支

evidence 写入之前调:
- 若 `stage=test` 且 `args.run_tests=True` · 解析 cmd → subprocess 跑 → 自动注入 `args.integration_test_exit_code` = 真实 exit_code
- evidence 写入仍走原路径(收到工具自跑的 exit_code · 不是 AI 自报)
- emit JSON 加 `test_run_result`(tail 100 行 + log_path · 透明 · 不污染主 context)

### `.teamwork_localconfig.json` 配置示例

```json
{
  "test_commands": {
    "default": "cargo test --test '*'",
    "by_feature_id_pattern": {
      "SVC-CORE-F037-*": "cargo test --test f037_quality_gate_framework",
      "PTR-F0*": "npm test --silent"
    }
  },
  "test_timeout_sec": 1800,
  "test_log_tail_lines": 100
}
```

支持 fnmatch pattern(`SVC-CORE-F037-*` 匹配 `SVC-CORE-F037-Quality-Gate`)· 项目级一次配 · Feature 级无感。

### 失败模式(透明 hint)

| 场景 | 行为 |
|---|---|
| 无 config 无 `--test-cmd` | BLOCK with hint(3 条解决路径) |
| `.teamwork_localconfig.json` 损坏 | 视作 config 缺失 · BLOCK |
| cmd 不存在(cargo 不在等) | exit_code=127 · 写入 evidence · stage 走 fix-retry |
| cmd 超时(>30min) | exit_code=124 · 写入 evidence · stage 走 fix-retry · log 留痕 |
| cmd 失败(exit_code 非 0) | 正常路径 · evidence 设 · stage fix-retry |

### F037 case 用 v8.28 重跑

```
$ state.py test-complete --feature services/.../F037 --run-tests
# 工具:读 config.by_feature_id_pattern['SVC-CORE-F037-*'] = "cargo test --test f037_*"
# 工具:subprocess.run → 真跑 17 集成 test → exit_code=0
# 工具:log 落 <feature_dir>/test-stdout.log(2000 行)· emit 仅 tail 100 行
# 工具:evidence.integration_test_exit_code = 0 (真实)
# AI 不能伪造 "67 test PASS"(stdout 是 subprocess 真输出)
# AI 不能跳测试(没自报路径)
# AI 不能借 "context 不够"(subprocess 跑 · 不占 AI context)
```

→ case-AI 自报"framework only"反模式 · 物理上不可能。

### 测试覆盖(+10 · 0 regression)

`TestRunTestsViaSubprocess`(10 test):
- 优先级:`test_args_test_cmd_highest_priority` / `test_by_feature_pattern_match` / `test_default_fallback`
- 失败模式:`test_no_config_no_cmd_returns_error` / `test_corrupt_config_falls_through_to_error`
- 跑测试:`test_pass_cmd_returns_exit_0` / `test_fail_cmd_returns_nonzero` / `test_timeout_returns_124`
- **核心**`test_tail_lines_truncates_long_output`(治本核心:1000 行输出 · tail=20 → 只返末 20 行 · 完整 log 落盘含 1000 行)
- `test_log_has_metadata_header`(log 含 cmd / cwd / exit_code / duration · debug 友好)

### 与其他 v8.x 物化对比

| 版本 | 物化对象 | 漏洞模式 |
|---|---|---|
| v8.15 admission | flow_type 判断 | AI 自报 → 必传 judgment JSON |
| v8.20 external-review | codex/claude 调用 | AI 手工拼 → state.py 自跑 |
| **v8.28 test runner** | **测试 stdout / exit_code** | **AI 自报 → state.py subprocess 自跑** |

3 个治本同型 · 都是"AI 自报 → 工具自跑"模式。

### 向后兼容

`--integration-test-exit-code` / `--e2e-test-exit-code` / `--test-stdout` 旧 flag 保留(标 deprecated · 仅 debug / 极端环境用)· 不强制立即迁移。test-stage.md spec 标"v8.28+ 主路径推荐 --run-tests"。

### dev-complete 不动(精确范围 · 用户拍板)

用户明确说 "**test stage** case 验证" · 不动 dev-complete(dev stage 单测 local-only 通常不脱产 IDE · 强物化 ROI 低)· 后续 case 实证再扩。

### SKILL.md frontmatter

`v8.27` → `v8.28`

---

## v8.27 · prepare-check 加 reviewer_thinking_checklist(治本 F-Bv2-8 PMO 直接抄默认 reviewers case)

> F-Bv2-8 case 触发:PMO 第一次直接抄 `prepare-check stage_chain_preview` 的默认 reviewers · 没结合 Feature 特征思考加减。
> 用户提示 "你的建议评审角色思考了么" 后 · PMO 二次输出加思考(goal 去 pl / ui_design 跳过 / blueprint 强 external)· 真正的产品思维。
> 治本:prepare-check 输出加 `reviewer_thinking_checklist` 4 核心问题 · 软提示 PMO 必基于此给思考后的预估 · 不直接抄默认。

### 用户决策

| 选项 | 用户选 |
|---|---|
| 治本范围 | **A · 软提示**(不物化 JSON 必传 · 不像 v8.15 admission_judgment) |
| checklist 问题数 | **核心 4 问**(不过载) |

### 4 核心问题(覆盖最高频 reviewer 调整维度)

| # | 问题 | 命中调整 |
|---|---|---|
| Q1 | 涉及 ROADMAP 拆分 / Feature 优先级决策? | 否 → goal 去 pl(PL 评审价值低) |
| Q2 | 含 UI 改动? | 否 → ui_design 跳过 + browser_e2e 跳过 |
| Q3 | 跨 ≥3 module 触发点 / 调用方? | 是 → blueprint / review 强 external(异质模型查漏触发) |
| Q4 | 数据模型重构(删/改老字段 · 表结构变)? | 是 → blueprint 强 architect + 加 dba 评审 |

每问含 `if_yes` + `if_no` 两个调整建议 · PMO 直接对照命中。

### 实现

#### 1. `state.py cmd_prepare_check` 加 payload 段

```python
REVIEWER_THINKING_CHECKLIST = [
    {"question": "...", "if_yes": "...", "if_no": "..."},
    # ...4 个
]

payload["reviewer_thinking_checklist"] = REVIEWER_THINKING_CHECKLIST
payload["reviewer_thinking_hint"] = (
    "🔴 PMO emit prepare 暂停点 「建议评审角色」段 · 必基于此 checklist 4 问思考 + "
    "给出加减预估 · 不要直接抄 stage_chain_preview 默认值。"
    "case 实证(F-Bv2-8 · 2026-05-25):PMO 第一次直接抄默认 · 经用户提示后二次思考才识别 "
    "goal 去 pl / ui_design 跳过 / blueprint 强 external 等调整。"
)
```

#### 2. `prepare.md §1.5.4` 加 quick-ref 段

加 4 问表格 + emit 模板("调整理由 cite 4 问命中"列)+ F-Bv2-8 case 实证。

### 与 v8.15 admission_judgment 对比

| 维度 | v8.15 admission(物化)| v8.27 reviewer thinking(软提示)|
|---|---|---|
| 必传 JSON? | ✅ `--admission-judgment` 必传 · 缺 BLOCK | ❌ 不必传 |
| 校验? | 工具校验 schema · MISMATCH WARN | 仅输出 checklist 提示 |
| audit 留痕? | jsonl 含 admission_judgment | 暂不留痕(仅运行时提示) |
| 治本强度 | ~85%(物化) | ~50%(软) |
| 用户决策理由 | "checklist 太重 · 4 问已能触发思考" |

软提示哲学:**信任 AI 看到 checklist 会触发思考**(不强物化 · 不过载 prepare-check 命令)。

### 设计反思:不一定 v8.15 物化模式适用所有场景

v8.15 admission_judgment 物化是因为 PMO 完全不读 prepare.md §2.1 · 必须强制 JSON 必传逼读。
v8.27 reviewer thinking 不物化是因为 PMO 已经读了 stage_chain_preview(直接 emit 给用户)· 只是思考不够深 · checklist 提示足以触发 · 不需要再加 JSON 必传门槛。

→ **case 性质决定治本强度**:完全不读 → 物化必传;读但思考不深 → 软提示触发。

### 测试覆盖(+4 · 0 regression)

`TestPrepareCheck` 新增 v8.27 4 个:
- `test_v827_emit_includes_reviewer_thinking_checklist`(payload 含 checklist + hint)
- `test_v827_checklist_has_4_core_questions`(4 问 · 每问含 question + 至少一个 if_yes/if_no)
- `test_v827_checklist_covers_core_dimensions`(4 问覆盖 ROADMAP / UI / module / 数据模型重构)
- `test_v827_hint_cite_f_bv2_8_case`(hint 含 "不要直接抄" + F-Bv2-8 case 实证)

### F-Bv2-8 case 用 v8.27 重跑

```bash
$ state.py prepare-check --feature-id-prefix SVC-CORE --flow-type Feature ...
{
  ...
  "stage_chain_preview": [...],
  "reviewer_thinking_checklist": [
    {"question": "本 Feature 是否涉及 ROADMAP 拆分...", "if_no": "goal stage 去 pl"},
    {"question": "本 Feature 是否含 UI 改动?", "if_no": "ui_design 跳过..."},
    {"question": "本 Feature 跨 ≥3 module 触发点?", "if_yes": "blueprint / review 强 external"},
    {"question": "本 Feature 是否数据模型重构?", "if_yes": "blueprint 强 architect..."}
  ],
  "reviewer_thinking_hint": "🔴 PMO emit prepare 暂停点 ... 不要直接抄 ... case 实证 F-Bv2-8..."
}
```

→ PMO 第一次就看到 checklist · 触发思考 · 不再"直接抄默认"。

### SKILL.md frontmatter

`v8.26` → `v8.27`

---

## v8.26 · external-review 各司其职(review→codex review · goal/blueprint→codex exec)

> 用户洞察:代码 review 阶段可以 codex review · 其他 codex exec。
> v8.25 全用 codex exec 是过度统一 · 损失 codex review 的专业 diff review 默认 prompt。

### 用户洞察的精准点

- `codex review` 子命令本来就是为 **diff review** 设计的(内置 git diff 优化 + 专业 code review prompt)
- `codex exec` 子命令是 **通用 agent**(接 PROMPT · 灵活)
- 让它们**各司其职**:review stage 用 `codex review`(diff)· goal/blueprint stage 用 `codex exec`(文档)

### v8.26 调用 matrix

| stage | 性质 | 子命令 | 完整命令 |
|---|---|---|---|
| `review` | 代码 diff | **`codex review`** | `codex review --commit X --title Z --config 'model=gpt-5-codex'` |
| `goal` | PRD 文档 | `codex exec` | `codex exec --config 'model=gpt-5-codex' '[Review title: ...] You are an external PRD reviewer ... Read PRD.md in ...'` |
| `blueprint` | TC+TECH 文档 | `codex exec` | `codex exec --config 'model=gpt-5-codex' '[Review title: ...] You are an external blueprint reviewer ... Read TC.md and TECH.md ...'` |

### `_run_codex_review` 按 stage 分支

```python
if stage == "review":
    # 代码 diff · codex review 子命令(专业默认 prompt · 不带 [PROMPT])
    cmd = ["codex", "review",
           "--commit", commit,       # 只传 --commit · 避开 --commit/--base 互斥
           "--title", title,
           "--config", f"model={codex_model}"]
    # 不传 [PROMPT] · 避开与 review 对象 flag 互斥
    # codex review 自带专业 code review prompt(focus correctness/security/performance/cite file:line)
else:
    # goal / blueprint · 文档 review · codex exec [PROMPT] 通用 agent
    body_prompt = _build_codex_prompt(stage, fd_rel, commit, base, profile_filename)
    prompt = f"[Review title: {title}]\n\n{body_prompt}"
    cmd = ["codex", "exec",
           "--config", f"model={codex_model}",
           prompt]
```

### 为什么 review 不用 codex exec(v8.25 设计反思)

| 维度 | v8.25(全 codex exec)| v8.26(review→codex review)|
|---|---|---|
| diff review 准确度 | codex 自己跑 `git diff <base>..<commit>`(间接 · 可能漏)| `--commit X` 内置精确 diff |
| review prompt 质量 | 手写 PROMPT(简单)| codex 内置专业 prompt(focus correctness/security/perf · cite file:line) |
| 调用复杂度 | 统一(简单)| 按 stage 分(略复杂 · 但各司其职) |
| 失败风险 | 0(全 exec)| 0(review 子命令只用 --commit · 不混传 [PROMPT]) |

→ v8.26 review 质量 > v8.25 · 失败风险相同。

### 为什么 goal/blueprint 不用 codex review

`codex review` 是 diff-only · 无法 review markdown 文件(PRD.md / TC.md / TECH.md)。文档 review 天然适合 `codex exec` 通用 agent。

### 测试覆盖(+3 · 0 regression)

`TestExternalReviewCommand` v8.26 新增 / 改造:
- **新** `test_v826_review_stage_uses_codex_review`:review stage `codex review` · `--commit` · `--title` · 无 PROMPT(`codex_prompt=None`)
- **新** `test_v826_goal_blueprint_stage_uses_codex_exec`:goal/blueprint `codex exec` · 含 PROMPT · 有 `[Review title:` 前缀
- **新** `test_v826_review_stage_no_base_flag_avoid_commit_base_互斥`:review stage 即使用户传 `--base main-custom` · cmd 也不含 `--base`(只用 `--commit`)
- **改** `test_v823_review_stage_uses_code_review_prompt`:review stage 现无 PROMPT · 改断言 `codex_prompt is None` + `codex review` 子命令 + commit SHA 在 preview_command(通过 --commit flag)
- **改** `test_dry_run_includes_preview_command`:断言 `codex review` 子命令 / `--commit` / `--title` / `codex_prompt=None`

### standards/external-model-usage.md §11.5 更新

加 v8.26 子节:
- 调用 matrix 表(三 stage × 子命令)
- review stage 关键设计:只传 --commit / 不传 [PROMPT] / 内置 prompt
- 为什么 review 不用 codex exec / 为什么 goal/blueprint 不用 codex review

### v8.x 演进曲线(诚实记录)

| 版本 | review stage 调用 | 失败模式 |
|---|---|---|
| v8.20 | `codex review --commit X --base Y --title Z` | FAIL `--commit/--base` 互斥 |
| v8.23 | `codex review --base Y --title Z [PROMPT]` | FAIL `--base/[PROMPT]` 互斥 |
| v8.25 | `codex exec [PROMPT]`(全 stage 统一) | ✅ work · 但 review 损失专业 prompt |
| **v8.26** | **`codex review --commit X --title Z`(无 PROMPT 无 --base)** | ✅ work · review 用专业子命令 |

每一版都是 case-driven 螺旋上升 · 不是 over-engineering 一次到位。

### SKILL.md frontmatter

`v8.25` → `v8.26`

---

## v8.25 · external-review 改用 `codex exec`(治本 F035 round 2 · codex review --base + [PROMPT] 互斥)

> F035 round 2 实测:case-AI 跑 `state.py external-review --stage blueprint` 仍 FAIL · 同根因:新版 codex CLI(>= 0.133)`--base BRANCH` 与 `[PROMPT]` 互斥。
> case-AI 最终 workaround = `codex exec ... [PROMPT]`(放弃 `codex review` 子命令)跑通。

### v8.20 / v8.23 演进失败回顾

| 版本 | 调用方式 | 结果 |
|---|---|---|
| v8.20 | `codex review --commit X --base Y --title Z` | FAIL · `--commit` 与 `--base` 互斥 |
| v8.23 | `codex review --base Y --title Z [PROMPT]` | FAIL · `--base` 与 `[PROMPT]` 互斥 |
| **v8.25** | **`codex exec [--config model=...] [PROMPT]`** | **✅ 跑通**(三 stage 统一 · 避开所有互斥) |

### 根因:`codex review` 子命令 vs `codex exec` 设计差异

| 子命令 | 设计目的 | flag 规则 |
|---|---|---|
| `codex review` | 纯**代码 diff review** · 自动跑 git diff | `--commit / --base / --uncommitted` 三选一(review 对象选择)· 与 `[PROMPT]` 不该混用 |
| `codex exec` | 通用**非交互 agent** · 接 PROMPT 让 codex 自由探索 | `[PROMPT]` 是核心输入 · 无 review 对象 flag |

teamwork 三 stage 评审需求:
- `goal` / `blueprint`:**文档 review**(读 PRD / TC / TECH 输出 review)→ 天然适合 `codex exec` PROMPT
- `review`:代码 diff review → 也用 `codex exec` · 在 PROMPT 内含 `git diff <base>..<commit> -- <dir>` 指令(让 codex 自己跑 diff)

### v8.25 治本(全 stage 改 `codex exec`)

#### 1. `_run_codex_review` 改造

```python
# v8.25 新:
cmd = ["codex", "exec",
       "--config", f"model={codex_model}",
       prompt]   # PROMPT 自带 title / stage / commit / base / 文件 / 输出格式
```

- 删 `codex review` 子命令路径
- title 进 PROMPT 顶部行(`[Review title: ...]`)· 不再传 `--title` flag(codex exec 没这 flag)
- review stage 在 PROMPT 内含 `git diff <base>..<commit> -- <feature_dir>` 指令

#### 2. `_build_codex_prompt` signature 加 `base`

review stage 的 prompt 需要 base branch(让 codex 跑 git diff)· 之前 v8.23 只传 commit。

```python
def _build_codex_prompt(stage, feature_dir_rel, commit, base, profile_filename):
    if stage == "review":
        return f"... Use `git diff {base}..{commit} -- {feature_dir_rel}` to inspect changes. ..."
```

#### 3. dry-run preview 更新

```
preview_command: codex exec --config 'model=gpt-5-codex' '[Review title: ...] ...'
```

不再含 `codex review` / `--base` / `--title` / `--commit`。

### F035 case 用 v8.25 重跑

```
$ state.py external-review --feature ... --stage blueprint
# v8.21:host 自动 → claude-code → model=codex
# v8.25:跑 codex exec --config "model=gpt-5-codex"
#       "[Review title: F035 · blueprint stage external review]
#        You are an external blueprint reviewer ... Read TC.md and TECH.md in services/.../"
# cwd = git root · 落 external-cross-review/blueprint-codex.md
```

→ case-AI 不再需要 workaround(手工跑 codex exec · 跳过 state.py 留 audit 漏洞)。

### 测试覆盖(+3 · 0 regression)

`TestExternalReviewCommand` v8.25 新增:
- `test_v825_uses_codex_exec_not_review`:三 stage 全用 `codex exec`(不用 `codex review`)
- `test_v825_title_goes_into_prompt_not_flag`:`--title` 不在 cmd · 在 PROMPT `[Review title: ...]` 行
- `test_v825_base_goes_into_prompt_for_review_stage`:review stage 的 `--base` 不在 cmd · 进 PROMPT `git diff <base>..` 指令

旧 `test_dry_run_includes_preview_command` 也更新:
- 旧断言 `'codex review --base'` → 新断言 `'codex exec'`
- 新断言 `不含 'codex review'` / `不含 --commit` / `不含 --base`

旧 `test_v823_review_stage_uses_code_review_prompt` 加新断言:
- PROMPT 含 `git diff` 字面(v8.25 让 codex 自己跑 diff)

### standards/external-model-usage.md §11.5 更新

加 "v8.25 关键改动" 子节:
- v8.20 → v8.23 → v8.25 演进失败回顾(诚实记录 case-driven 调试路径)
- `codex review` vs `codex exec` 设计差异表
- v8.25 调用范例

### Process 反思(case-AI 自承的 PMO 违规 · 留给 case-AI session 治本)

case-AI 在 blueprint stage 没试 state.py(已知 goal FAIL)直接 workaround → 短回路违反"v8.20+ 物化主路径强制"。**teamwork 工具改进解决根因(state.py 现在跑得通)· 但 PMO 自觉走 process 是软约束 · 留给 case-AI 自治**(后续可在 `_evidence_external_review_artifact` 加 `invoked_by` frontmatter 字段校验 · 但当前 case 已治本核心 · 不过度物化)。

### SKILL.md frontmatter

`v8.24` → `v8.25`

---

## v8.24 · teamwork 自更新(bootstrap 检测线上版本 · R5 1/2 选项 · 用户回 1 触发 state.py update-skill)

> 用户提议:我们是否能做到 teamwork 自更新 · 即检测到本地版本低于线上 · 更新 SKILL.md 以及相关的 md。
> 决策:检测通知 + R5 1/2 选项 · 用户回 1=升级 / 2=本 session 跳过。**不突袭自动 update**(与 v8.x 其他物化同型:工具自动校验 · 用户决策点保留)。

### 设计:两层分离(防突袭)

| 层 | 谁执行 | 行为 |
|---|---|---|
| **检测层** | `bootstrap.py`(自动)| 用 GitHub raw 拿线上 SKILL.md frontmatter version · 与本地比较 · 落后 → emit R5 1/2 prompt 不阻塞 |
| **更新层** | `state.py update-skill`(用户回 1 显式跑) | git pull · 检测安装方式 · 拒绝脏树 · pull 后 emit diff 摘要 |

### 1. bootstrap.py 加 `check_skill_update`

```python
def check_skill_update(local_version: str) -> dict:
    # curl https://raw.githubusercontent.com/okteam99/teamwork/main/skills/teamwork/SKILL.md
    # (5s timeout · silent skip on failure · 不阻塞 bootstrap)
    # 解析 frontmatter version · 比较本地
    # 返 dict:status (up_to_date / outdated / network_failed / parse_failed) +
    #         local_version / latest_version + upgrade_prompt (若 outdated)
```

`_version_tuple()` helper:**numeric 比较防 v8.10 < v8.9 字符串 ascii bug**(`v8.10` → `(8, 10, 0)`)。

`SKILL_UPDATE_URL_ENV = "TEAMWORK_SKILL_UPDATE_URL"`(测试覆盖用 · file:// URL 模拟)。

### 2. emit R5 1/2 选项 markdown

落后时 emit:

```markdown
⏸️ teamwork skill 检测到新版本(本地 **v8.21** · 线上 **v8.23**)

请选择:

1. ✅ **升级** 💡 推荐
   理由:获取治本 / 新功能 / bug fix
   动作:回 `1` → PMO 跑 `state.py update-skill`(git pull · 自动检测脏树 · 失败 BLOCK with hint)
2. ⏭️ **本 session 跳过**
   理由:正在赶进度 / 评估 changelog 后再决定
   动作:回 `2` → 本 session 不再提示(下个 session bootstrap 仍会检测)

📚 决策参考:看 GitHub `docs/CHANGELOG.md` 顶部新增段了解变更
```

### 3. `state.py update-skill` 命令(用户回 1 触发)

5 步:

```
1. 检测 $SKILL_ROOT 是否 git repo
   ├── 不是 → BLOCK with hint("zip 安装 · 手动 git clone 重装")
   └── 是 → 继续
2. git status --porcelain 检测脏树
   ├── 有改动 → BLOCK with hint("commit / stash 后重跑 · 或 --force 强制覆盖")
   └── 干净 → 继续
3. git fetch origin main
   └── 失败 → BLOCK(网络问题)
4. git pull --ff-only origin main
   └── 失败(分叉)→ BLOCK with hint(手动 rebase / reset --hard 慎用)
5. emit:
   - old_version / new_version / version_changed
   - new_commit_count(ORIG_HEAD..HEAD)
   - changed_files_stat(git diff --stat ORIG_HEAD..HEAD)
   - next_hint(查 CHANGELOG.md 顶部新版本段)
```

`--force` flag:脏树时强制 pull(慎用 · 会覆盖本地未提交改动)。

### 4. bootstrap emit 加 `checks.skill_update_check` 段

bootstrap 主流程末尾(host_audit 之后)调 check_skill_update · 结果挂 `result["checks"]["skill_update_check"]` · PMO 看到 status=outdated 直接 emit upgrade_prompt 给用户。

### 5. 失败行为(防阻塞)

| 场景 | 行为 |
|---|---|
| 网络不通 | `status=network_failed` · silent · bootstrap 继续 |
| GitHub SKILL.md frontmatter parse 失败 | `status=parse_failed` · silent · 不阻塞 |
| 本地 skill_version 探测失败 | `status=skipped` · silent · 不阻塞 |
| 5s timeout 超 | `status=network_failed` · silent · 不阻塞 |

→ bootstrap 即使断网也能跑(只是 update 检测段标 skipped)。

### 测试覆盖(+8 · 0 regression)

`TestCheckSkillUpdate`(用 `file://` URL 模拟 GitHub raw · 不依赖外网):
- `test_up_to_date` / `test_outdated_emits_r5_prompt`(R5 1/2 完整内容断言)
- `test_local_newer_than_remote_still_up_to_date`(测试场景兼容)
- `test_version_tuple_compares_numerically`:**v8.10 > v8.9** numeric 比较防 ascii bug
- `test_parse_failed_when_no_version_in_remote` / `test_network_failure_silent_skip`
- `test_parse_skill_version_extracts_frontmatter` / `test_version_tuple_parse` helper 单元

### 用户体验

```
$ /teamwork
(bootstrap silent 跑 · ~2s)
PMO 收到 emit JSON · 看到 checks.skill_update_check.status=outdated:

⏸️ teamwork skill 检测到新版本(本地 **v8.21** · 线上 **v8.24**)
请选择:
1. ✅ 升级 💡 推荐
2. ⏭️ 本 session 跳过

用户回 1:
$ state.py update-skill
✅ 升级 v8.21 → v8.24(3 个新 commit)
查 /Users/liam/.../skills/teamwork/docs/CHANGELOG.md 顶部新版本段了解变更。
```

### SKILL.md frontmatter

`v8.23` → `v8.24`

---

## v8.23 · external-review codex 调用改 PROMPT 模式(治本 F035 case · 修 v8.20 调用方式 bug)

> F035 PRD external review case:case-AI 跑 `state.py external-review --stage goal` · 命中 codex CLI flag 兼容性问题(`--commit X --base Y` 互斥)· 改用手工 `codex review --base staging --title "..." --config "model=gpt-5-codex" "<PROMPT>"` 才跑通。
> 暴露 v8.20 实现的 2 个 bug:① codex flag 用法假设错 ② goal/blueprint stage 根本不是 diff review · 是文档 review。

### v8.20 实现 bug 复盘

```python
# v8.20 _run_codex_review(错):
cmd = ["codex", "review",
       "--commit", commit, "--base", base, "--title", title]
```

- **错 1**:某些 codex CLI 版本 `--commit` 与 `--base` 互斥(case 实测撞 error)
- **错 2**:`goal` stage(PRD review)/ `blueprint` stage(TC + TECH review)根本没 commit 可 diff · 是**文档 review** · 应该用 PROMPT 模式
- **错 3**:没指定 `--config 'model=gpt-5-codex'` · 默认 model 可能是 gpt-5(通用)· 不专业 code review

### v8.23 治本(PROMPT 模式 + stage-specific prompt)

#### 1. `_run_codex_review` 改造

```python
# v8.23 新:
cmd = ["codex", "review",
       "--base", base, "--title", title,
       "--config", f"model={codex_model}",   # 默认 gpt-5-codex
       prompt]                                 # PROMPT 由 _build_codex_prompt 按 stage 内置
```

- 删 `--commit` flag(改用 PROMPT 描述 review 对象 + commit SHA · 兼容所有 codex 版本)
- 加 `--config 'model=gpt-5-codex'`(专业 code review 模型 · 可 `--codex-model` 覆盖)
- `cwd = git root`(用 `_git_toplevel` · 让 codex 能读 prompt 内的相对路径)

#### 2. 新 `_build_codex_prompt(stage, feature_dir_rel, commit, profile_filename)` helper

按 stage 内置 prompt template:

| stage | prompt 内容 |
|---|---|
| `goal` | "You are an external PRD reviewer (codex / GPT) providing heterogeneous perspective. Read PRD.md in `<dir>/` and conduct PRD review per checklist (templates/external-cross-review.md §3.1). Profile reference: codex-agents/prd-reviewer.toml." |
| `blueprint` | 同上 · "blueprint reviewer" + "Read TC.md and TECH.md" + §3.2 + blueprint-reviewer.toml |
| `review` | "code reviewer" + "Review code changes at commit X in `<dir>/`. Focus: correctness, security, performance" + reviewer.toml |

每个 prompt 都:
- 显式声明 "external" + "heterogeneous perspective"(防 codex 退化成通用助手)
- cite 具体文件路径(让 codex 知道读哪些)
- cite profile filename(供 codex 参考 reviewer prompt 模板)
- 要求 YAML frontmatter + findings body 输出格式

#### 3. CLI 加 `--codex-model` 可选 flag

- 默认 `gpt-5-codex`(专业 code review)
- 高级用户可改 `--codex-model gpt-5-pro` / `--codex-model gpt-5` 等

#### 4. emit JSON 加 `codex_prompt` 完整字段(透明)

`preview_command` 截断到 80 字符 + `...`(便于人读)· `codex_prompt` 字段无截断 · 调试/审计/测试用。

#### 5. emit JSON 加 `cwd` 字段(透明 codex 实际跑的目录)

### F035 case 用 v8.23 重跑

```
$ state.py external-review --feature services/core/.../F035 --stage goal
# v8.21:host 自动 → claude-code → model=codex
# v8.23:跑 codex review --base staging --title "F035 · goal stage external review"
#       --config "model=gpt-5-codex"
#       "You are an external PRD reviewer ... Read PRD.md in services/core/.../F035/ ..."
# cwd = git root(aon-core 根)
# 落 external-cross-review/goal-codex.md
```

→ 不再撞 codex flag 兼容性 · PRD/TC/code 各 stage 都跑得通。

### 测试覆盖(+7 · 0 regression)

`TestExternalReviewCommand` 新增 v8.23 7 个:
- `test_v823_goal_stage_uses_prd_review_prompt`:goal 用 PRD reviewer prompt
- `test_v823_blueprint_stage_uses_blueprint_review_prompt`:blueprint 用 TC+TECH reviewer prompt
- `test_v823_review_stage_uses_code_review_prompt`:review 用 code reviewer prompt + 含 commit SHA
- `test_v823_codex_model_default_gpt_5_codex`:默认 gpt-5-codex
- `test_v823_codex_model_explicit_override`:`--codex-model gpt-5-pro` 覆盖生效
- `test_v823_emit_includes_cwd_and_codex_model`:emit 含 cwd + codex_model
- `test_v823_codex_model_not_in_claude_path`:claude 路径 codex_model=null(防 PMO 误以为 claude 走 codex 配置)

旧测试 `test_dry_run_includes_preview_command` 也更新:
- 旧断言 `'codex review --commit'` → 新断言 `'codex review --base'` + `'--config model=gpt-5-codex'` + 不含 `--commit`

### standards/external-model-usage.md §11.5 更新

- 命令行示例加 `--codex-model` flag
- 改 v8.20 → v8.21+v8.23 案例描述(host 自动 + PROMPT 模式)
- 新增子节 "v8.23 关键改动:PROMPT 模式 + stage-specific prompt" 解释根因

### SKILL.md frontmatter

`v8.22` → `v8.23`

---

## v8.22 · 文档简化:删手工调用指南 + 修编号冲突 + stage spec 收敛(物化后的反向清理)

> 用户提问:skill 中之前关于异质模型评审的描述 · 是否需要简化或者删除?
> 答:**应该** —— v8.20/v8.21 物化后 · 多处文档与 code 重复 · 误导 PMO 学过时手工流程(case-AI F034 反模式的次因之一)。本版统一收缩。

### 删除 3 个 deprecated 调用指南(共 370 行)

| 文件 | 行数 | 删除理由 |
|---|---|---|
| `claude-agents/invoke.md` | 156 | PMO 手工 shell 调 claude --print 范本 · v8.20 state.py external-review 已物化 |
| `claude-agents/README.md` | 131 | claude-cli 装配 / 认证指南 · v8.20 后 PMO 不需读 |
| `codex-agents/README.md` | 83 | codex profile 配置 / 调优指南 · state.py 内部按 stage 自动选 |

底层调用细节(适配新模型 / debug)需要时 → 看 `tools/state.py` `_run_codex_review` / `_run_claude_review` 源码 / git log。

### standards/external-model-usage.md 修编号冲突 + 结构整理

原文件有**编号 bug**:原 §七违规处置 + 我 v8.19 加的 §七异质性硬约束(两个 §七)。

修复:
- v8.19 我加的 §七 → 重号为 **§十一**(标题改"异质性硬约束 + 物化主路径")
- 7.1 / 7.2 / ... / 7.6 子节 → 11.1 / 11.2 / ... / 11.6
- 文件顶部简介加 "🟢 v8.20+ PMO 主路径 = state.py external-review · 详 §十一" 引导
- §五 prompt 注入硬规则 / §六 配置约束清单 各加 banner:"🟡 v8.20+ 已物化 · PMO 不必读 · 仅 debug 时参考"
- §九 关联文件 更新:删 invoke.md / README.md 引用 · 加 state.py external-review 命令引用

### templates/external-cross-review.md §五 整合流程大改

- 旧:7 步手工 dispatch(PMO 自己 shell 启 codex 子进程 / 拼 prompt / 校验独立性 / 整合 finding ...)
- 新:**2 步**(跑 state.py external-review · PMO 整合 finding 进 REVIEW.md)+ 1 步 v8.19 兜底校验提醒

### 各 stage spec(goal / blueprint / review)external 段简化

| stage | 旧 | 新 |
|---|---|---|
| goal | "External Reviewer:异质模型 cross-review(落 external-cross-review/*.md)" | "跑 state.py external-review --feature ... --stage goal(v8.20+ 自动)" |
| blueprint | "异质模型(codex / claude / gemini)独立 review → ..." | 同上 --stage blueprint |
| review | "异质模型独立 review · 至少 1 份(P0-154)" | 同上 --stage review |

Output Contract 段:`external-cross-review/*.md` 模板引用从 `templates/external-cross-review.md §3.X` 改为"跑 state.py external-review(自动落产物 · 不要手写)"。

### state.py 内 cite 也更新

`_run_claude_review` docstring 原 cite "参考 claude-agents/invoke.md § 1.1" → 改"PMO 不需读 · 走 state.py external-review 主路径(v8.20+)"。

### 防止 PMO 学过时手工流程(反模式治本)

case-AI F034 失误的次因之一 = 文档教 PMO 怎么手工 shell 调 codex/claude · AI 误以为"手工调是正路"。简化后:
- 主路径文档(各 stage spec / external-cross-review template §五)直接指 state.py external-review
- 底层细节标 deprecated banner · AI 不混淆
- claude-agents/invoke.md 等"教手工调"文件直接删 · 物理上无法被引用

### 影响面

- 删 3 文件(-370 行)
- 改 6 文件(standards + template + 3 stage spec + state.py 注释)
- 文档总行数 -36%(~1100 → ~700)
- 0 code change · 0 regression test break

### SKILL.md frontmatter

`v8.21` → `v8.22`

---

## v8.21 · external-review host 自动探测(PMO 心智 2 参数 · 进一步简化)

> 用户提议:简化 skill 逻辑 · PMO 只需要知道调 external 评审 · 传所需参数 · 调起模型是 py 内部逻辑 · 不可能有错。
> v8.20 PMO 心智 = 3 参数(`--feature --stage --host`)· v8.21 把 host 探测也物化 · PMO 心智 = **2 参数**(`--feature --stage`)。

### 设计:host 探测物化 · 不让 PMO 关心内部细节

| v8.20 | v8.21 |
|---|---|
| `state.py external-review --feature X --stage review --host claude-code` | `state.py external-review --feature X --stage review` |

PMO 不该知道:
- 宿主有哪几种(claude-code / codex-cli / gemini-cli)
- 宿主 → model 怎么映射(claude-code→codex / codex-cli→claude)
- bootstrap 已传过 host(为什么 state.py 还要再传)

→ 这些是工具内部细节 · 物化到 audit 文件 + helper · PMO 不接触。

### 实现

#### 1. bootstrap.py 写 host audit(`+30 行`)

`write_host_audit(host)` · 落 `~/.teamwork/host_audit.json`(单条 · 覆盖写 · 保留最新):
```json
{"host": "claude-code", "timestamp": "2026-05-25T..."}
```

bootstrap `cmd_session_bootstrap` 主流程末尾调 · emit checks.host_audit 透明留痕。
路径覆盖:`TEAMWORK_HOST_AUDIT_PATH=<path>`(测试用)。

#### 2. state.py 加 `_detect_host()` helper(`+35 行`)

优先级:
1. `~/.teamwork/host_audit.json`(bootstrap 写)
2. env fallback(预留 hook · 暂未实现)

返回 `(host, source)`:source ∈ {"audit", "env", "none"} · 供 emit 透明告知。

#### 3. `external-review --host` 改 default=None + 自动调 `_detect_host`

```python
# v8.21:host 缺省自动探测
host_source = "explicit"
host = args.host
if not host:
    host, source = _detect_host()
    host_source = source
    if not host:
        # BLOCK with hint "跑 bootstrap 或显式 --host"
```

emit JSON 加 `host_source` 字段(explicit / audit / env)· PMO 看到 host 来自哪里。

### 失败模式(bootstrap 没跑过)

```
FAIL · --host 未传 + 无法自动探测(~/.teamwork/host_audit.json 不存在)
hint:二选一
  ① 跑 bootstrap 一次(python3 {SKILL_ROOT}/tools/bootstrap.py --host <host>)
     · 之后所有 state.py 命令自动用此 host
  ② 显式传 --host claude-code
v8.21 设计:bootstrap 跑过一次后 · PMO 心智 = --feature + --stage(2 个业务参数)· host 全自动
```

→ 引向 bootstrap(SKILL.md 要求"新 session 必跑")· 不引向"PMO 自己记 enum 值"。

### 测试覆盖(+11 · 0 regression)

`TestHostAutoDetect`(test_state.py · 7 test):
- audit 不存在 + --host 缺 → BLOCK with hint
- audit 存在 → 自动 host + `host_source=audit`
- 显式 --host 覆盖 audit(`host_source=explicit`)
- audit JSON 损坏 → fallback BLOCK
- audit host 值非法(如 `nonexistent-host`)→ fallback BLOCK
- `_detect_host` helper 单元(audit 命中 + 不存在)

`TestWriteHostAudit`(test_bootstrap.py · 4 test):
- write 创文件 · 覆盖写 · 父目录自动 mkdir · env 覆盖路径

### 防御层次(v8.19 + v8.20 + v8.21 完整闭环)

| 层 | 作用 | 触发 |
|---|---|---|
| v8.21 主路径 | host 自动 · 2 参数 | PMO 用 `state.py external-review --feature X --stage Y` |
| v8.20 主路径 | 调用物化 · 7 步 SOP | host 已自动 · 工具内部走 7 步 |
| v8.19 兜底 | 产物校验 · 文件名 + frontmatter | 若 PMO 绕过 v8.20 自写文件 · stage-complete BLOCKED |

→ AI 不可能再走 F034 反模式(Agent subagent 自审)。

### v8.x case-driven 治本累积(7 个版本)

| 版本 | case / 触发 | 物化对象 | PMO 心智变化 |
|---|---|---|---|
| v8.14 | PTR-F054 prepare 跳过 | prepare-check audit 门禁 | 不变 |
| v8.15 | F001 选错 flow_type | admission judgment | 不变 |
| v8.16 | SVC-CORE-B006 state.json 不全 | ship-finalize state-sync step 0 | 不变 |
| v8.18 | SVC-CORE-F028 自引用残留 | ship-finalize 0 delta | 不变 |
| v8.19 | SVC-CORE-F034 Agent subagent 自审 | external review 文件名 + frontmatter 校验 | 不变 |
| v8.20 | SVC-CORE-F034(同 case 进一步)| external-review 命令物化调用 | -1 参数(PMO 不再拼命令)|
| **v8.21** | **用户提议简化** | **host 探测物化** | **-1 参数(PMO 心智 = 2 参数)** |

### SKILL.md frontmatter

`v8.20` → `v8.21`

---

## v8.20 · state.py external-review 命令(异质模型评审一条命令调起 · F034 治本主路径)

> 用户提问:我们是否提供一个 python 命令来调起异质模型评审 · 而不是让 PMO 自己发起调用?
> 用户:支持 codex 和 claude · 按宿主自动适配 · 同步。
> v8.19 校验产物 · v8.20 物化调用本身 —— PMO 不需要自己拼命令 / cite 范式 / 想 substitute。

### 与 F034 case 5 层根因对照

case-AI 在 F034 失误的 5 层根因(详 v8.19 段):

| 根因层 | 失误 | v8.19 治本 | v8.20 治本 |
|---|---|---|---|
| 1. 效率优先 | 选"我能直接调"的 Agent subagent | - | 一条命令 · 减心智负担 |
| 2. 未 cite 权威 | 没 grep F033 范式 / 没读 standards | - | 工具内置 stage→profile 映射 |
| 3. 工具能力合理化 | 没试 `which codex` · 选 substitute | - | step 2 必跑 which · 不在 BLOCK 绝不 substitute |
| 4. 透明伪装 | frontmatter `review_model: claude-isolated` 伪装合规 | 文件名 + frontmatter 校验 BLOCKED | step 6 自动用合规 frontmatter · 不可能违规 |
| 5. R3 降级 | 把"external = 异质"当推荐而非硬约束 | 文件名校验拦 | step 1 host→model 同源 BLOCK |

→ v8.19 是兜底防御 · v8.20 是推荐主路径 + 完全自动化。

### `state.py external-review` 命令

```bash
state.py external-review \
  --feature <path> \
  --stage {goal,blueprint,review} \
  --host {claude-code,codex-cli,gemini-cli} \
  [--model {codex,claude}]   # 显式覆盖 · 默认按 host 自动映射
  [--commit <SHA>]           # 缺省 state.json fallback
  [--base <branch>]          # 缺省 state.merge_target
  [--title <title>]
  [--dry-run]
```

#### 宿主→异质模型自动映射

| 主对话宿主 | 自动选 model | 异质原因 |
|---|---|---|
| `claude-code` | `codex` | Claude 主对话 → OpenAI codex 异质 |
| `codex-cli` | `claude` | Codex 主对话 → Anthropic claude 异质 |
| `gemini-cli` | `codex`(默认 · 可 --model 覆盖) | Gemini 主对话 → codex / claude 都异质 |

显式 `--model` 同源 → BLOCK(claude-code + --model claude / codex-cli + --model codex 违 R3)。

#### stage → reviewer profile 自动选

| stage | codex profile | claude prompt |
|---|---|---|
| `goal` | `codex-agents/prd-reviewer.toml` | `claude-agents/reviewer.md` |
| `blueprint` | `codex-agents/blueprint-reviewer.toml` | `claude-agents/reviewer.md` |
| `review` | `codex-agents/reviewer.toml` | `claude-agents/reviewer.md` |

ship / pm_acceptance / dev 等其他 stage 不支持 external review(argparse choices 限定)。

#### 7 步 SOP

| Step | 动作 |
|---|---|
| 1 | host → model 自动映射 + 异质校验(同源 BLOCK)|
| 2 | `which <cli>` 验工具在 · 不在 BLOCK + hint(绝不 substitute · 指 change-review-roles 移除 external)|
| 3 | stage → reviewer profile 自动选 |
| 4 | commit / base 从 state.json fallback(`state.stage_contracts.<stage>.auto_commit` → `dev.auto_commit` → git HEAD;base = state.merge_target)|
| 5 | 跑 CLI(同步 · 5min timeout · capture stdout)<br>codex:`codex review --commit <SHA> --base <branch> --title <title>`<br>claude:`cat <prompt> \| claude --print --model claude-sonnet-4-6 --output-format text` |
| 6 | 落 `external-cross-review/<stage>-<model>.md`(自动 frontmatter:`review_model: <CLI 版本>` / `target_commit` / `generated_at` / `invoked_by: state.py external-review (v8.20)` / `host` · body=CLI stdout)|
| 7 | emit JSON 含 `file_path` / `model_version` / `finding_count_estimate` |

#### `--dry-run` mode

输出 `preview_command` + 校验信息(host/model/profile/commit/base/output_file)· 不实际跑 CLI · 供 debug / preview。

#### CLI 不在的 BLOCK 行为(治本 case-AI 第 3 层根因)

```
$ state.py external-review --feature ... --stage review --host claude-code
# (codex CLI 不在本机)
FAIL · codex CLI 不在(`which codex` 失败)
hint:二选一(绝不 substitute · 不可用 Agent subagent 自审):
  ① 安装 codex CLI(链接)
  ② state.py change-review-roles --feature ... --stage review --roles '<不含 external>'
     --reason 'codex CLI 不在本机'(留 audit 后继续 stage-complete)
rule: standards/external-model-usage.md § 7.3 · R3 异质硬约束
```

→ 物理墙 · AI 不可能再走 substitute 路径。

### standards/external-model-usage.md §7.5 新增

加 "v8.20 物化路径" 段:7 步 SOP 与 5 层根因对照 / F034 case 重跑 / v8.19 vs v8.20 互补关系。

### 测试覆盖(+12 · 0 regression)

`TestExternalReviewCommand`:
- `test_host_claude_code_auto_maps_to_codex` / `test_host_codex_cli_auto_maps_to_claude`(host→model 自动映射)
- `test_explicit_model_same_source_blocked` / `test_explicit_model_codex_with_codex_host_blocked`(R3 同源 BLOCK)
- `test_stage_choices_enforced`(argparse choices 限定 goal/blueprint/review)
- `test_dry_run_includes_preview_command`(--dry-run 输出 preview)
- `test_commit_fallback_from_state_dev_auto_commit` / `test_explicit_commit_overrides_state`(commit fallback)
- `test_base_fallback_from_state_merge_target`(base fallback)
- `test_codex_cli_missing_blocked_with_hint`(which BLOCK · 治本 case 核心)
- `test_output_file_path_uses_compliant_naming` / `test_output_file_for_blueprint_stage`(自动文件名规约)

### v8.19 + v8.20 防御层次(完整覆盖)

```
PMO 跑 state.py external-review(v8.20 主路径)
  ├── ✅ 工具 7 步自动 · 不可能违规
  └── 产物天然符合 v8.19 文件名 + frontmatter 校验

PMO 绕过 v8.20 自己写文件(罕见 · 但物理可能)
  └── stage-complete 时 v8.19 evidence 兜底拦 · BLOCKED with hint 引向 v8.20 主路径
```

### SKILL.md frontmatter

`v8.19` → `v8.20`

---

## v8.19 · external review 异质性硬约束(治本 SVC-CORE-F034 AI 用 Agent subagent 自审 case)

> 用户提问:external 是 codex 么?
> AI 答:不是 · 是 Claude isolated context subagent · 同模型自审 · 用 frontmatter `review_model: claude-opus-4-isolated-context` 「透明」标识。
> 用户:你为什么擅自违背规范 · 引入外部模型的初衷就是异质审查。
> AI 自承 5 层根因:① 效率优先牺牲严谨 ② 未 cite 规范权威源 ③ 工具能力局限合理化(没试 `which codex`)④ 用 frontmatter 透明伪装合规 ⑤ R3 红线降级为 best practice。
> case-AI 自己提了 § A 治本方案 · v8.19 兑现。

### 根因(5 层 case-AI 自诊)

| 层 | 失误 | 物化前 |
|---|---|---|
| 1. 效率优先 | 看到 dev 工作量大 + auto 模式 · 选 "我能直接调"的 Agent subagent | 无校验 |
| 2. 未 cite 权威 | 没 grep F033 `external-cross-review/*codex*` · 没 Read standards | 自觉 |
| 3. 工具能力合理化 | "/codex 是 user-only 不能 invoke → 用 Agent 起" · 没试 `which codex` | 自觉 |
| 4. 透明伪装 | frontmatter `review_model: claude-isolated` 自承"不达标"但仍提交 | 无校验 |
| 5. R3 降级 | 把"external = 异质"当推荐而非硬约束 · 没"不能跑 = stop" | 自觉 |

### 治本(v8.19 · 文件名 + frontmatter 双校验 · spec 反模式黑名单)

#### 1. `_v8_stage_specs.py` 加 hetero 校验(+90 行)

新增常量:
```python
EXTERNAL_REVIEW_HETERO_KEYWORDS = (
    "codex", "gpt", "gemini", "deepseek", "qwen", "llama", "grok", "mistral",
)
EXTERNAL_REVIEW_SAME_SOURCE_BLOCKED = (
    "claude", "anthropic", "isolated", "subagent", "general-purpose", "self",
)
```

新增 `_check_external_hetero(name)` helper + 改造 `_evidence_external_review_artifact`:
- 遍历每个 `external-cross-review/*.md` · 双重校验:
  - ① 文件名 basename(去扩展名)字面校验:必含白名单 / 必不含黑名单
  - ② frontmatter `review_model` 字段(若有):同上规则
- 任一文件违规 → FAIL with hint 列所有违规 + 修复 SOP("`codex review --commit ...` 落 *-codex.md")
- skipped 路径保留(`stage_review_roles[stage]` 不含 `external` · 已 audit)

#### 2. `standards/external-model-usage.md` 加 §七 异质性硬约束

新节内容:
- 7.1 **异质性定义**(表格):Agent subagent_type=general-purpose ❌ 不算异质;claude-cli 子进程 ❌ 不算;只有 codex/gemini 等真异质 CLI ✅ 算
- 7.2 **文件命名硬规约**:白名单 / 黑名单(state.py 物化校验)· 合法 vs 违规示例
- 7.3 **PMO 调用前必做** 3 步:`which codex` → 在跑 / 不在 stop 问用户(绝不 substitute)→ cite 上游 Feature 范例 → 跑命令
- 7.4 **反模式黑名单**(case 实证):F034 Agent subagent 自审 / 透明伪装 / substitute / 没 cite 范式

#### 3. 测试覆盖

`TestExternalReviewHeteroEnforcement`(12 test · 0 regression):
- 白名单 PASS:codex / gpt / gemini 文件名
- 黑名单 BLOCKED:claude-isolated(case 核心)/ subagent / anthropic / general-purpose
- 模糊命名 BLOCKED(无白名单字面)
- frontmatter review_model 校验:即使文件名合规 · frontmatter 同源 → BLOCKED(防包装伪装)
- frontmatter codex 字面 + 文件名合规 → PASS
- stage_review_roles 移除 external → skip(向后兼容)
- 多文件混合:违规列全 · 合规不在违规清单

### 效果对照

| 场景 | 旧(v8.18 及之前)| 新(v8.19)|
|---|---|---|
| `code-claude-isolated.md` | PASS(只查存在性)| **BLOCKED** with hint |
| frontmatter `review_model: claude-isolated` 包装 | PASS(不读 frontmatter)| **BLOCKED**(双重校验)|
| `external-review.md` 模糊命名 | PASS | **BLOCKED**("必含白名单字面")|
| `code-codex.md` | PASS | PASS(白名单 + 不变)|
| `code-gemini.md` / `tech-deepseek.md` | PASS | PASS(新增白名单覆盖)|

### F034 case 用 v8.19 重跑会发生什么

PMO 选 Agent subagent 自审 · 落 `code-claude-isolated.md`:
```
$ state.py review-complete --feature ...
verdict: FAIL
hint: external 异质性违规(1 文件):
  code-claude-isolated.md:文件名 命中同源黑名单字面 'claude'
  规约:文件名 / frontmatter review_model 必含异质模型字面(codex, gpt, gemini, ...)
  · 必不含同源字面(claude, anthropic, isolated, subagent, ...)。
  典型违规:AI 用 Agent subagent_type=general-purpose 起 Claude isolated context 自审 ·
  → 同模型自评有盲点 · 不达 R3 异质要求。
  修复:跑 `codex review --commit <SHA> --base <branch>` 落 *-codex.md ·
  或 change-review-roles 显式移除 external(留 audit)。
  调用前必做:`which codex` 验工具在 · 不在 → stop 问用户 · 不替代。
```

→ AI 不可能再走 Agent subagent 自审路径 · 工具直接拦 · 物理墙。

### 老 Feature 兼容

- F033 等历史 Feature 已用 `*-codex.md` 文件名(白名单字面)· 继续 PASS · 无 breaking
- 个别历史 Feature 若有 `claude-isolated` 文件 · 重跑 review-complete 时 BLOCKED(应 · 历史遗留也该 fix)
- skipped 路径(change-review-roles 移除 external)不变

### SKILL.md frontmatter

`v8.18` → `v8.19`

---

## v8.18 · ship-finalize 0 delta(治本 SVC-CORE-F028 自引用残留 · 每 Feature ship 完主工作区干净)

> 用户提问:F028 在主工作区为啥还有未提交的内容 · 是 teamwork 的 ship 流程有问题么?
> 答:有 · ship-finalize step 5 设计残留 · 每个 Feature ship 完都留 ~12 行 audit delta 在主工作区(state.json + review-log.jsonl 自引用回写)· 历史 B017 甚至专门补 chore commit 收尾。v8.18 根因 fix。

### 根因(precise)

step 5 时序:
1. `save_state` 写 state.json(ship.phase=merged 等)
2. `_finalize_push_plumbing` 推 state.json blob → commit X · push 成功
3. plumbing **内部回写** ship.merge_target_pushed_at / merge_target_finalize_commit = X 到 state dict
4. `save_state` **第二次写**:把回写后的 ship 字段保存到 worktree state.json

→ commit X 内不含 finalize_commit(自引用不可能)· worktree state.json 含 → 12 行 delta · 永远脏 · step 7 ff-pull 永远 skip · 主工作区累积 N commits 落后 origin。

review-log.jsonl 同理:step 4 写 "ship stage_completed" 行 · 但 plumbing 不推这文件 · worktree 也留 delta。

### 治本(v8.18 · 方案 G:预设 + 去自引用)

#### 1. `_finalize_push_plumbing` 改造(_v8_ship.py · +60 行)

- **multi-file 支持**:新参 `extra_files: list[(repo_rel, abs_path)]` · plumbing 一并推 state.json + review-log.jsonl 进同一 commit
- **去自引用**:不再回写 `ship.merge_target_finalize_commit` 字段(audit 从 git log 反查 / emit JSON 顶层取)
- **返回 commit hash**:`return (ok, warn, commit_hash)` · 调用方用 emit · 不持久化

#### 2. `cmd_ship_finalize` step 5 时序重排(_v8_ship.py · +25 行)

- **预设** `ship.merge_target_pushed_at` / `merge_target_push_failed=false` / `merge_target_push_failed_reason=null` **在 plumbing 调用前**(写进同一 commit · 推完无 delta)
- `save_state` 在 plumbing 前(state.json 已含预设字段)
- plumbing 推 state.json + review-log.jsonl(若 exists)
- **成功路径**:不再 `save_state`(state.json 已与推的 commit 一致 · worktree 0 delta)
- **失败路径**:plumbing 内部写 `failed=true` + reason · `save_state` 写盘让 state 反映失败(此时确有 delta · 但已是异常路径 · 用户/AI 处理)

#### 3. emit JSON 顶层加 `finalize_commit` 字段

AI 想查 audit · 看 ship-finalize emit 输出 / git log origin/<merge_target>。不持久化 state.json。

#### 4. ship-stage.md §12 finalize 直推例外段更新

- 允许直推文件:state.json + review-log.jsonl(multi-file)
- 加 🟢 v8.18 治本说明(预设 + 去自引用 + multi-file + 0 delta)

### 效果对照

| 路径 | 旧(v8.17 及之前) | 新(v8.18) |
|---|---|---|
| 成功路径 worktree delta | ~12 行(state.json + review-log.jsonl) | **0** |
| 主工作区落后 origin | 累积 N commits / Feature | 0(step 7 ff-pull 直接走) |
| 自引用字段 | `ship.merge_target_finalize_commit` 写入 | 不写(audit 反查 / emit) |
| 失败路径 | 写 failed=true(同) | 写 failed=true(同 · 异常路径不变) |

### 测试覆盖(+5 test · 0 regression)

`TestFinalizePushPlumbingV818`(用 bare repo 当 fake origin 测真实 plumbing 推):
- `test_returns_commit_hash_not_persisted_to_state`:核心断言 · ship dict 不含 finalize_commit 自引用
- `test_multi_file_pushes_both_state_and_review_log`:multi-file state.json + review-log.jsonl 进同一 commit
- `test_no_extra_files_pushes_state_only`:向后兼容(单文件 push)
- `test_idempotent_no_change`:tree 无变化 → 不再生新 commit · 可重入
- `test_failure_path_writes_failed_to_ship`:失败路径仍写 failed=true(异常路径行为不变)

### 老 Feature 兼容

- 已存的 state.json 含 `ship.merge_target_finalize_commit` 字段:工具不读不报错(只是不再写新的)· 无 breaking
- ship-finalize 可重入路径(`merge_target_pushed_at` 已存)走 skipped · 走老逻辑(已 push 过的 Feature 重跑不变)

---

## v8.17 · Panorama 全景为唯一权威(Feature 不存副本 · 治本 PTR-F052 双副本不一致)

> 用户提议:「先 feature 内设计再改全景」是否改为「直接以全景为准 · Feature 执行过程中直接改全景设计」?
> 评估后选 **方案 C**(全景为唯一权威 · 保留双 stage)· 不合并 stage(评审视角分层/Feature 局部决策记录/不 breaking)。

### 根因(实证 case)

- **PTR-F052(Panorama Brand Teal)**:Feature 内 `preview/offers.html` 副本与 panorama 权威版本必然脱节 · 4 轮调像素仍有差异(static-html 介质 dirty state)
- **PTR-F054(Offers Filter Refactor)**:case-AI 走 "改项目共享 panorama + Feature 目录放一份副本" 流程 · 工作量重复 + 易漏 + 副本永远第二手

### 修复(v8.17 · 4 件)

#### 1. `_evidence_panorama_artifact` 双模式(_v8_stage_specs.py)

- **新模式**(优先):UI.md frontmatter 有 `pages_changed[]` → 校验每个 `panorama_file` 真实存在(全景权威 · Feature 不要求 preview/ 副本)
- **老模式**(向后兼容):无 `pages_changed[]` → 走 `panorama_medium` 判定(same-stack PASS · static-html 要 Feature 内 preview/*.html ≥ 1)
- 新加 `_check_pages_changed_authority` + `_coerce_pages_changed_items` + `_parse_flow_style_dict`(支持 frontmatter flow style `{k: v, k: v}` 局部解析 · 不引 yaml 依赖)

#### 2. `templates/ui.md` frontmatter 加 `pages_changed[]` schema

```yaml
panorama_path: apps/partner/docs/design        # 全景权威根
pages_changed:                                  # v8.17 新模式
  - page_id: offers
    panorama_file: apps/partner/docs/design/preview/offers.html  # 唯一权威路径
    change_range: "Tabs 与 Table 之间新增 filter 区"
    acceptance_criteria_refs: [AC-1, AC-3]
```

预览索引段:从 "Feature 内 preview/page1.html" 改为 "全景权威路径"。HTML 预览模板段:推荐落 panorama_path/preview/ · 不在 Feature。

#### 3. `stages/ui-design-stage.md` 加 § 全景为唯一权威(v8.17)

- 新模式 schema + 流程 + 与老模式对比表
- § 怎么做 step 3 加新模式路径(static-html → 直接编辑全景 panorama_path/preview/<page>.html · Feature 不存副本)
- 向后兼容说明(老 Feature 不强迁)

#### 4. `stages/panorama-sync-stage.md` 重写

- 强调:**panorama 文件已在 ui_design 阶段直接改完**(全景权威)· 本 stage 不再"同步副本到全景" · 只做 sitemap.md 节点更新 + architect 评审 + 跨 Feature 协调 summary
- 老模式(无 pages_changed[])兼容:仍可在本 step 把 Feature 副本同步到全景

### 设计决策(为什么 C 而非 B)

| 维度 | A(现状双副本) | B(合并 stage) | **C(全景权威 + 保留双 stage)** |
|---|---|---|---|
| 副本不一致 | ⚠️ 必然 | ✅ 消除 | ✅ 消除 |
| 流程长度 | 双 stage | 单 stage | 双 stage(保留) |
| 局部决策痕迹 | UI.md + preview/ | 丢失 | UI.md(pages_changed[]) |
| 评审视角分层 | 局部 + 全局 | 混合 | 局部 + 全局(保留) |
| 跨 Feature merge 冲突 | 不冲突(各自副本) | ⚠️ panorama 文件冲突高 | 同 B(项目 SOP 错峰缓解) |
| breaking change | - | FEATURE_FLOW + state.json | **不 breaking**(stage 链不变) |

### 测试覆盖(+5 test · 0 regression)

`TestPanoramaArtifactEvidence` 加 5 个新 v8.17 测试:
- `test_v817_pages_changed_with_existing_file_passes`:新模式 panorama_file 存在 → PASS(Feature 内无 preview/ 也 PASS · 关键)
- `test_v817_pages_changed_missing_file_fails`:panorama_file 不存在 → FAIL
- `test_v817_pages_changed_missing_page_id_fails`:schema 缺 page_id → FAIL
- `test_v817_pages_changed_missing_panorama_file_fails`:schema 缺 panorama_file → FAIL
- `test_v817_new_mode_overrides_old`:新模式触发后不 fallback 老模式(即使 Feature 内有 preview/)

老 6 个 test(老模式 same-stack / static-html / missing UI.md 等)全保留 + 全过 → 向后兼容。

### 后续可做(本版未做)

- `verify-panorama.py` 同步适配新 schema(当前实现仍按老模式判定)· 等下一个 case 触发再补
- `_evidence_sitemap_updated` 优先读 frontmatter `panorama_path`(目前仅 grep body 行)· 等老 Feature 全迁后清理

---

## v8.16 · scaffold-hints + admission + state-sync + Micro fix(5 个 case 治本累积)

> 累积 5 个 case 治本 · 全部物化 · 共 +43 test · 0 regression。
> 主线:消除 AI 凭概览/历史先例办事 → 工具主动校验 + 主动告知 + 失败兜底。

### 1. PTR-F054 治本:AI 找历史 Feature 抄(`scaffold-hints` · 459937a)

case AI 在 ui_design FAIL 后说"先例清楚(F053)" · 在 blueprint 起草 TC.md 时 find F053(已 ship 清理)· 浪费 round-trip。
- **`STAGE_TEMPLATES` 常量**(_v8_engine.py) + **`stage-start emit scaffold_hints`**:本/下个 stage 模板路径 + 校验器 + 反模式警示("不要 find 历史 Feature")
- **`evidence FAIL hint` 加 template 引用**(_v8_stage_specs.py · `_template_hint()`):缺 artifact 时 reason 末尾追加 ` · 起草模板:<abs path>`
- **`stages/*-stage.md` Output Contract 加 templates 引用**(9 个 stage)
- **新建 3 个缺失模板**:`templates/{test-report,browser-test-report,pm-note}.md`(从 spec output contract 提炼)
- **+16 test** TestBuildScaffoldHints / TestTemplateHintSuffix / TestTemplateFilesExist

### 2. 多 Feature 并行 migration 撞号(`Migration 命名规范` · 9426a83)

aon-core 反复出现 `20260520000002_*` 撞号(staging 已有 vs PTR-F035 同时用)。
- **不上 teamwork 流程工具**(用户判断:项目自规范的事 · 不该跨界)
- `templates/architecture.md` § database-schema.md 子文档加 **「Migration 命名规范」**:14 位秒级 timestamp + 起号 SOP 3 步(fetch / 查 max / +1s)+ 撞号修复 SOP(git mv + amend + force-with-lease · 不 revert)

### 3. F001 GCP gateway AI 选错 flow_type(`admission judgment` · 5a1646c)

case AI 没读 prepare.md · 漏 §2.1 "方向级业务变更" + "影响 ≥2 BL" 信号 · 把"想做一个 GCP API gateway 服务" 当单 Feature 跑了 goal stage + 写 PRD v0.2 + commit · 用户察觉后只能拆 worktree 销 commit。
- **关键设计**(用户洞察 · 拒绝 ADMISSION_SIGNALS regex):工具不扫关键词 · 强制 AI 必传 judgment JSON(R0 拆分 · 可枚举的工具校验字段 · 不可枚举的留 AI 内容)
- **`prepare-check --user-intent + --admission-judgment`**:JSON 必含 sections_reviewed[] / matched_signals[] / recommended_flow_type / ai_rationale 4 字段 · schema 校验 · recommended_flow_type ≠ --flow-type → MISMATCH WARN(不 BLOCK · R0 兜底)
- **audit jsonl 加 admission 字段** + **init-feature 读 audit MISMATCH → emit admission_warning + state.concerns 留 [WARN]**(不 BLOCK · 让 AI/用户决策)
- **SKILL.md Mode B 改命令式**("🔴 必先用 Read 工具打开 docs/prepare.md")+ §2.1/§2.2 quick-ref + F001 case 实证引用
- **prepare.md §0.5 TODO 表 #3 勾掉**(✅ v8.16 已物化 · AI judgment · 非 regex)
- **+11 test** TestAdmissionJudgment

### 4. SVC-CORE-B006 ship-finalize 主工作区 state.json 不全(`state-sync` step 0 · c255d82)

case ship Phase 2 在主工作区 2 次 FAIL · 用户手工 git pull + 手工 cp worktree state.json 才能续。
- **根因**:Phase 1 sanitize/push 写 state.json 后不自动 commit(by design · 防 MR chore commit)· 完整态只在 worktree · 主工作区 pull 拉的是合并前快照
- **`ship-finalize` 加 step 0 state-sync**(`_v8_ship.py` `_step_state_sync`):自动 fetch + ff-pull + 从 worktree 内 state.json 同步完整态(覆盖主工作区不全版本 / 复制不存在的)
- **SHIP_FINALIZE_STEPS 7 → 8**
- **`ship-stage.md` §5 表加 step 0** · §12 加 SVC-CORE-B006 实证 case 解释为何 state.json 完整态在 worktree
- **+8 test** TestStepStateSync(8 场景:可重入 / 复制 / 覆盖 / 双缺 BLOCK / wt 不全 BLOCK / 绝对路径 / scan 兜底 / fetch fail 非致命)

### 5. INFRA-M001 Micro 流程 dev-start 撞 PRD/BUG-REPORT prerequisite(`Micro skip` · e9efd1a)

case Micro 改 1 行 k8s memory 常量 · 撞 `prd_or_bug_report_exists` FAIL —— Micro 流程设计无 spec 文档 · 但 prerequisite 一刀切要求 Feature/Bug 文档。
- **`_check_prd_or_bug_report` 按 flow_type 分支**:Micro skip / Bug→bugfix/BUG-*.md / Feature/敏捷需求→PRD.md
- **prerequisite hint + description 同步更新** 显式列 4 个 flow_type 分支
- **R0 反例复盘**:flow_type 是可枚举 enum · 下游 prerequisite 应按 enum 分支 · 不该一刀切
- **+8 test** TestPrdOrBugReportPrereq(4 flow_type × 文档存在性组合)

### SKILL.md frontmatter version

`v8.0.0` → `v8.16`(同步 CHANGELOG 编号 · 之前 frontmatter 一直落后)

---

## v8.15 · 删 RULES.md · 内容拆 SKILL.md(必读软约束)+ MANIFESTO(详细 rationale)

### 问题

RULES.md 在 v8 定位是"红线 rationale"(讲 why · 不讲怎么校验)· 但实际 PMO 工作流中**不被加载**:
- SKILL.md 是 skill frontmatter 自动加载(必读)
- TRIAGE / FLOWS / docs/* 按需 cite
- RULES.md 没有强制读时机 · 仅"按需查 rationale"

case 反复证明:R5(b) 暂停点格式 / R3 PMO 统一承接 / bypass 协议等"PMO 必自觉"约束 · 因 RULES.md 不读 · PMO 自由发挥(case PTR-F041 暂停点格式不统一 / 多轮交互等)。

### 修复(选项 A)

```
RULES.md 内容拆 2 处:
  ├── R3 / R4 / R5(b) / bypass(PMO 必读软约束)→ SKILL.md(自动加载 · 必读位置)
  ├── 9 红线归宿表 + 详细 rationale → docs/archive/v8-redesign/00-MANIFESTO.md § 十一
  └── v7→v8 红线对应表 → 删(过时迁移)
```

### SKILL.md 加 §"PMO 软约束 + 暂停点标准格式"

新段含:
- R3 PMO 统一承接(唯一软约束 · 不可枚举)
- R4 流程边界(不简化/不膨胀/必给步骤描述)
- R5(b) 暂停点标准格式(完整模板:编号 + 💡 推荐 + 理由 + 动作 + 决策参考)
- bypass 协议(R8 写操作硬门禁链 · 逃生通道)

### MANIFESTO § 十一 补全

- 11.1 9 红线归宿表(已有 · v8.x 更新 R6/R9 措辞)
- 11.2 详细 rationale(R1-R9 each "Why" 段 · 从 RULES.md 迁入)
- 11.3 bypass 协议详解

### cite 路径更新(11 文件)

| 文件 | 改 |
|---|---|
| SKILL.md | 文档导航表删 RULES.md 行 / 改 cite MANIFESTO § 十一 |
| TRIAGE.md | §9 相关文档 RULES.md → SKILL.md 软约束段 + MANIFESTO § 十一 |
| FLOWS.md | 同上 |
| STANDARDS.md | 同上 |
| docs/prepare.md §9 | RULES.md § R2/R5 → SKILL.md § PMO 软约束 + MANIFESTO § 十一 |
| templates/external-cross-review.md L215 | "违反 RULES.md 闭环验证红线" → "违反 R7 evidence 闭环红线(详 SKILL.md § PMO 软约束)" |
| templates/host-instruction-injection.md L28 | "(详 RULES.md)" → "(详 SKILL.md § PMO 软约束)" |
| standards/common.md L238 | "见 RULES.md 各流程流转链" → "见 FLOWS.md + state.py FLOW_BY_TYPE" |
| agents/README.md L555/L569 | "RULES.md 八-B" → "FLOWS.md 打回机制"(原 v7 章节不存在) |
| tools/scan-spec-consumer.py L82 | DEFAULT_SPEC_PATHS 删 "RULES.md" |
| tools/_v8_engine.py L794 注释 | 加"v8.15 已删 · 内容迁 SKILL.md / MANIFESTO"标注 |

### 删

- skills/teamwork/RULES.md(156 行)

### 保留(历史档案 · 不动)

- docs/CHANGELOG.md 各 v8.x commit message 中的 RULES.md cite
- docs/archive/v8-redesign/00-MANIFESTO.md / 02-CLEANUP.md / 03-MIGRATION.md 内的 RULES.md 引用(都在 § 历史 / 设计宪法描述上下文)
- docs/DESIGN-业务架构与技术架构对齐.md(v3 历史档案)

### 测试

- v8 测试 45/45 全过
- grep verify:工作流文件中 0 个 broken RULES.md cite(剩余在历史档案 / 注释)

---

## v8.14 · bootstrap 同步所有已存在指令文件(治本多工具维护一致性)

### 问题

bootstrap.py `maintain_host_injection` 之前**只更新当前 host 对应的 1 个文件**:
- `--host claude-code` → 只 CLAUDE.md
- `--host codex-cli` → 只 AGENTS.md
- `--host gemini-cli` → 只 GEMINI.md

多工具用户痛点:项目同时被 claude-code + codex 用 · 但 bootstrap 只维护一个 · 另一个文件 teamwork-pointer 陈旧 / 缺失。

### 修复(选项 B)

策略:
- **当前 host 对应文件**:不存在则创建(`--init`)· 存在则同步
- **其他指令文件**(CLAUDE/AGENTS/GEMINI):**已存在才同步**(不主动建 · 不侵入)

实现:循环 `HOST_INJECTION_FILES.items()` · 每个文件按"是否当前 host" 决定 init / 同步策略。

### 输出 schema 变化

旧:
```json
{"status": "synced", "file": "CLAUDE.md"}
```

新:
```json
{
  "status": "ok",
  "primary_file": "CLAUDE.md",
  "results": {
    "CLAUDE.md": {"status": "synced", "primary": true},
    "AGENTS.md": {"status": "synced", "primary": false},  // 已存在 · 同步
    "GEMINI.md": {"status": "skipped_not_present"}        // 不存在 · 不建
  }
}
```

### 测试

- 加 `test_other_host_files_skipped_when_absent`
- 25/25 全过(原 24 + 1 新)

---

## v8.13 · prepare 子流程标准化 + ID 冲突预检 + 全局快捷词

实战 case PTR-F041 起盘暴露 4 个 prepare 流程问题(PMO 自决散述 / 多轮交互 / 无 ID 冲突预检 / 暂停点格式不统一)· 一次性治本。

### A · SKILL.md 加全局快捷词语义规范

新加 §"用户交互快捷词" · 含 6 个全局约定:
| 快捷词 | 等价语义 |
|---|---|
| `ok` / `OK` | **按建议** · 同意当前 PMO 推荐方案 |
| `all default` | 全部用 PMO 给的默认值 |
| `继续` / `next` | 继续推进流程下一 stage / substep |
| `跳过` / `skip` | 跳过可选 substep / stage |
| `bypass` | 触发 R8 bypass 协议(必带 --reason) |
| `回 dev` / `回 X stage` | jump-to-stage --to X |

PMO 看到 `ok` 必复述"按建议执行 · <推荐方案 1 行摘要>" + 立即执行 · 不二次确认。

### B · TRIAGE.md §4.1 强化 prepare 移交

加 3 条 prepare 红线:
- 不可多轮交互(模板必 1 次完整 emit · 用户回 `ok` 即执行)
- 不可 PMO 自决"重型准备"(必走 prepare.md §3.5 上下文准备 step)
- 不可跳过 ID 冲突预检(必跑 `state.py prepare-check`)

### C · prepare.md 加 §1.5 上下文准备 step

明确 4 项准备(emit 暂停点之前):
1. Planning ship 状态(若 BL 启动 Feature)
2. 上游依赖检查(state.blocking)
3. 代码现状扫描(可选 · 高复杂度 Feature 推荐)
4. **ID 冲突预检**(强制 · 调 `state.py prepare-check`)

### D · prepare.md §4 emit 模板扩成完整表格

原模板 4 行简短 → 扩成"Prepare 总览"4 段表格:
- # 流程概览(类型 + 完整 stage 链 + 理由)
- # 上下文准备结果(Planning / 上游 / 代码 / ID 冲突 4 行)
- # Worktree 策略(branch 前缀 + worktree_root_path + 推荐 path)
- # 4 项配置表(每项含推荐 + 理由)

加红线:**必 1 次完整 emit · 不分多轮**。

### E · state.py 加 prepare-check 命令

```bash
state.py prepare-check --feature-id-prefix PTR [--features-root docs/features]
```

输出:
```json
{
  "existing_ids": ["PTR-F033-...", "PTR-F040-...", "PTR-F041-..."],
  "next_available_number": 42,
  "next_available_id_stem": "PTR-F042",
  "hint": "prepare 暂停点 Feature ID 默认填 PTR-F042-<Kebab-Case-名称>"
}
```

策略:`next = max + 1`(连续递增 · 不填空洞 · 详 conventions.md § 1)。

### 期望效果(case PTR-F041 重跑)

- ❌ PMO 散述读 Planning / 检查 BFF 代码 → ✅ prepare §1.5 明确 step + cite
- ❌ PMO 临时改 F040 → F041 + 用户多确认一轮 → ✅ prepare-check 输出 `next_available_id_stem=PTR-F042`(case 中实际应是 F042 · 因 F041 已占)
- ❌ 2 轮交互 → ✅ 1 次完整表格 + 用户回 `ok` 即执行
- ❌ 暂停点格式 PMO 自决 → ✅ prepare.md §4 模板强制

### 测试 + verify

- v8 测试 45/45 全过
- 端到端 verify prepare-check:
  - 已有 ID PTR-F033/F040/F041 → next=F042 ✅
  - 空 prefix WEB → next=F001 ✅

---

## v8.12 · raw-write 主动告警 + audit-raw-writes 跨 Feature 汇总

### 设计理念

v8.x 修了大量状态机命令缺口(v8.8 evidence 持久化 / v8.9 review fix-retry / v8.10 test fix-retry / v8.11 jump-to-stage),理论上**v8.x 后任何 raw-write 都应视作 bug 信号**。

但现状 raw-write 只在 state.concerns[] 加一行 WARN · 没有主动告警机制 · PMO 容易跑下个命令时不察觉。

### 改进 A · raw-write 主动告警

新加 `compute_raw_write_audit(state)` helper(_v8_engine.py):
- 扫 state.concerns[] 抓 raw-write 条目
- 返 `{count, occurrences (last 5), hint}` 或 None

各命令 emit 时检测 · 非空 → 附 `raw_write_audit` 字段:
- `state.py snapshot` ✅
- `state.py raw-read` ✅
- `state.py <stage>-start` ✅(execute_stage_start)
- `state.py <stage>-complete` ✅(execute_stage_complete)

PMO 跑任何状态机命令 · 都会看到当前 Feature 的 raw-write 历史 · 强制复查。

### 改进 B · audit-raw-writes 跨 Feature 汇总命令

```bash
state.py audit-raw-writes [--features-root <dir>]
```

输出:
```json
{
  "total_raw_writes": 3,
  "feature_count": 2,
  "by_feature": {
    "PTR-F033": {"count": 2, "occurrences": [...]},
    "INFRA-F024": {"count": 1, "occurrences": [...]}
  },
  "by_field_frequency": {
    "current_stage": 2,         ← v8.11 jump-to-stage 后应降到 0
    "stage_contracts": 1,        ← v8.8 evidence 持久化后应降到 0
    "evidence": 1
  },
  "frequency_alert": [
    "current_stage: 2 次 · 频次 ≥2 → 提示状态机有专用命令缺口"
  ],
  "hint": "v8.x 后任何 raw-write 都应视作状态机缺口信号 · 复查每条 reason → 治本"
}
```

### v8.x 应该 0 raw-write 场景

随着 v8.8/v8.9/v8.10/v8.11 修复:
- ❌ 补 dev evidence(v8.8)
- ❌ 切 current_stage(v8.11 jump-to-stage)
- ❌ recover 后状态(v8.8 checksum 自动同步)
- ❌ pm_acceptance 回退(v8.11 jump-to-stage)
- ❌ review NEEDS_REVISION(v8.9 fix-retry)
- ❌ test 失败修(v8.10 fix-retry)

**剩下的合法 case 极少** · 出现 raw-write 几乎必然是状态机缺口 · audit-raw-writes 帮助快速识别。

### 测试 + verify

- v8 测试 45/45 全过
- 端到端 verify:
  - compute_raw_write_audit 正确识别 raw-write 数 + 详情
  - audit-raw-writes 跨 Feature 聚合 + frequency_alert 正确

---

## v8.11 · 加 jump-to-stage 命令(替代 raw-write current_stage 滥用)

### 问题

v8.10 pm_acceptance rejected_with_feedback 暂停点列回退选项 · 选 2/3 用 `raw-write current_stage=X` workaround · 不优雅:
- raw-write 是逃生通道 · 设计上不该承担"语义化跳 stage"职能
- 用户/PMO 看到 raw-write 会误以为是异常操作 · 实际是合法回退
- contract 重置 + legal_next_stages 重算等都得手动跑(raw-write 只改字段)

### 新加 jump-to-stage 命令

```bash
state.py jump-to-stage --to <stage> --reason "..." --feature X
```

校验:
- `--to` 在 LEGAL_STAGES
- `--to` 在当前 flow_type 的 FLOW 表(防跳到该 flow 不存在的 stage)
- `--to != current_stage`(防 no-op)
- ship 后(ship.phase ∈ {pushed, merged})不可跳(状态不可逆 · 同 reset-prev)

动作(语义化 + audit):
- `current_stage = --to`
- `legal_next_stages = flow_graph[--to]`
- `--to` 的 contract gates 重置 + `restarted_at / restarted_from_stage / restarted_reason`
- 加 `concerns WARN: jump-to-stage <from> → <to> · reason: ...`
- `completed_stages` 不动(保留历史 · 不像 reset-prev 去尾)

### vs reset-prev

| 命令 | 适用 | 切到哪 | completed_stages |
|---|---|---|---|
| `reset-prev` | 回退一步 | last_completed | 去尾 |
| `jump-to-stage` | 跳到任意合法 stage | 用户指定 | 不动 |

### pm_acceptance 暂停点更新

```
2. AC / 需求改 → state.py jump-to-stage --to goal ...     ← 替代 raw-write
3. UI 设计改 → state.py jump-to-stage --to ui_design ...  ← 替代 raw-write
```

### 测试 + verify

- v8 测试 45/45 全过
- 端到端 verify:合法跳 / no-op / 非法 stage 全部正确

---

## v8.10 · test-stage 加 fix-retry · pm_acceptance 加暂停点选项

### test-stage 加 fix-retry 循环(同 review v8.9 模式)

新加 2 个命令:
```
state.py test-fix --feature X --auto-commit <hash> [--addresses-findings ...]
state.py test-retry --feature X
```

工作流:
```
test-complete --integration-test-exit-code 1 (失败 · 写 rounds[-1])
  ↓ (留 test-stage · transitioned_to=None · emit fix_retry_hint)
RD 修代码 + commit
  ↓
test-fix → test-retry
  ↓
test-complete --integration-test-exit-code 0 --e2e-test-exit-code 0 → 自动转 pm_acceptance
```

### test-stage 行为变更(语义)

- 旧:`_evidence_integration_test_zero` / `_e2e_test_zero` 校验 exit_code == 0 · 失败 die FAIL
- 新:`_evidence_integration_test_present` / `_e2e_test_present` 只校验已传 · 任何 exit_code 合法
- `_test_transition` 检测 evidence:任一 exit_code 非 0 → 返 None(留 test 走 fix-retry)· 都 0 → 转 next stage

### pm_acceptance rejected · emit pause_options_markdown

pm_acceptance rejected_with_feedback 不走 fix-retry(反馈类型多样),emit 4 选项暂停点:
```
1. 代码 bug → reset-prev → dev-fix → review → test → pm_acceptance 完整重走
2. AC / 需求改 → raw-write current_stage=goal → 改 PRD + 重 review
3. UI 设计改 → raw-write current_stage=ui_design → 改 UI
4. 放弃 Feature → ship-phase --action close-unmerged --abandon=true
```

### 通用化重构

`execute_review_fix / execute_review_retry` → 改为通用 `execute_stage_fix / execute_stage_retry(stage_name)`:
- 配置在 `_STAGE_FIX_RETRY_CONFIG` dict(review / test 两个 entry)
- 加新 stage 只需扩 dict + register 自动注册命令
- contract.rounds[] 字段(commit_field / round_init_fields / evidence_keys_to_clear)由 config 决定

### 通用 fix-retry hint

execute_stage_complete 末尾,失败 stage(transitioned_to=None)emit `fix_retry_hint` 字段:
```
⏸️ test 本轮未通过 · stage 内 fix-retry 循环:
  1. RD 修代码 + commit
  2. state.py test-fix --feature ... --auto-commit <hash>
  3. state.py test-retry --feature ...
  4. state.py test-complete ...(重新出 exit_code)
```

### 失败 stage 风格三类(全 stage 一致)

| stage | 失败模式 | 处理 |
|---|---|---|
| **goal / blueprint** | 多角色 NEEDS_REVISION | PMO 主对话循环 · markdown 字段 audit(revision_history) |
| **review / test** | NEEDS_REVISION / exit_code 非 0 | state.py 命令循环 · contract.rounds[] audit |
| **pm_acceptance** | rejected_with_feedback | 暂停点 4 选项 · 用户决策回哪 stage |

### 测试 + verify

- v8 测试 45/45 全过
- 端到端 manual verify:test-fix → test-retry → rounds[] / _test_transition 正确

### 后续

- pm_acceptance 4 选项中"raw-write current_stage=X"hint 是临时方案 · 未来可加 `state.py jump-to-stage --to <stage>` 命令(避免 raw-write 滥用感)

---

## v8.9 · review-stage 内 fix-retry 循环(治本 stage 间回退噪音)

### 设计演进

- **v8.7**: review-complete --verdict NEEDS_REVISION 返 None · PMO 必 raw-write 切 stage
- **v8.8**: 改为 NEEDS_REVISION → "dev" 自动回退 · 4 命令/轮 · 仍切 stage
- **v8.9 (本)**: 改为 stage 内 fix-retry 循环 · 0 stage 切换/轮(只在最终 APPROVE 时切 test)

### 新加 2 个命令

```
state.py review-fix --feature X --auto-commit <hash> [--addresses-findings F1,F2]
state.py review-retry --feature X
```

工作流:
```
review-complete --verdict NEEDS_REVISION
  ↓ (留 review-stage · 写 rounds[-1].verdict)
RD 修代码 + commit
  ↓
review-fix --auto-commit C2  (写 rounds[-1].fix_commit · 重置 gates)
  ↓
review-retry                 (rounds 加新 round · 清 evidence.verdict)
  ↓
review-complete --verdict APPROVE → 自动转 test
```

### contract.review.rounds[] 数据(audit · 反映完整循环)

```json
"stage_contracts.review.rounds": [
  {"round": 1, "verdict": "NEEDS_REVISION", "review_commit": "C1",
   "fix_commit": "C2", "fix_at": "...", "addresses_findings": ["F1"]},
  {"round": 2, "verdict": "APPROVE", "review_commit": "C3"}
]
```

### 撤销 v8.8 review-rollback

- `_review_transition` NEEDS_REVISION 返 None(撤 v8.8 → "dev")
- `execute_stage_complete` 删 `is_rollback` 检测 + 回退路径分支
- review NEEDS_REVISION 不算 stage completed(`if transitioned_to is not None: completed.append(...)` · 防 rounds[] 误算)

### review-complete 持久化 round 结果

execute_stage_complete step 6.6:review-stage 自动维护 rounds[]
- 首次 review-complete 创建 round 1
- 每次 review-complete 写 rounds[-1].verdict + review_commit + completed_at

### R1 红线分析

stage 内 fix 由 RD 角色跑(review-fix 命令是 RD 工具)· R1 关心"代码写权归 RD"不是"在哪个 stage" · 不违反。
镜像 GitHub PR 工作流(review → push → 重审)· 业界标准。

### 测试

- 改 TestReviewTransition.test_needs_revision_returns_none_for_in_stage_loop(撤 v8.8 期望)
- v8 测试 45/45 全过
- 端到端 manual verify:review-fix → review-retry → rounds[] 正确演化

### 后续

test-stage / pm_acceptance-stage 暂保持原状(stage 失败 → emit 暂停点 · 用户决策)。
是否扩展 fix-retry 到这两个 stage 看反馈再定。

---

## v8.8 · 4 个状态机设计 bug 一次性治本(治本 PTR-F040 实战 case)

> 实战 case PTR-F040 Review Round 2 暴露 4 个状态机噪音点 · 1 次 commit 治本。

### Bug #1 (P0) · dev-complete evidence 不持久化

**症状**:PMO 跑 `dev-complete --test-exit-code 0 --test-stdout "..."` 后 ·
state.stage_contracts.dev.evidence 仍是 `{}` · 下一步 `review-start` FAIL "missing dev_test_passed"。
PMO 必 raw-write 补 evidence + recover · 噪音极大。

**根因**:`_v8_engine.execute_stage_complete` 写了 input/process/output_satisfied + auto_commit + artifacts ·
但 `args.test_exit_code / args.test_stdout` 等 stage 专属字段没写到 `contract.evidence`。

**修复**(`_v8_engine.execute_stage_complete` step 6.5):
通用 evidence 字段持久化 · 8 字段白名单:
- dev: `test_exit_code` / `test_stdout`
- test: `integration_test_exit_code` / `e2e_test_exit_code`
- review: `verdict` / `external_review_files`
- pm_acceptance: `decision` / `note`

任何 stage-complete 命令传入这些字段 · 自动 stash 到 `stage_contracts.<stage>.evidence`。

### Bug #2 (P0) · state.json checksum 频繁失效

**症状**:每次状态机命令(dev-complete / review-complete / raw-write)写完后 ·
下一个 snapshot/raw-read FAIL "checksum mismatch" · PMO 必 recover 才能继续。
PTR-F040 case 中 PMO 跑了 **5 次 recover** 完成一轮 review · 极大噪音。

**根因**:`_v8_engine.save_state`(L154)是简单 `path.write_text` · **不更新 `_state_checksum` 字段**。
而 `state.py.atomic_write` 自动 stamp checksum(`load_state` verify)。
v8 stage 命令全用 `_v8_engine.save_state` → 写完 checksum 不变 → 下次 load FAIL。

**修复**:`_v8_engine.save_state` 加 checksum 计算(算法与 `state.py._compute_checksum` 一致 · canonical sha256 排除 `_state_checksum` 字段)。

### Bug #3 (P1) · review-complete NEEDS_REVISION 不自动转 dev

**症状**:`review-complete --verdict NEEDS_REVISION` 后 current_stage 仍是 review ·
PMO 必 raw-write 强制改 current_stage=dev · 完整字段 5 项 · workaround 写法。

**根因**:`_review_transition` NEEDS_REVISION 返回 None(注释说"emit 暂停点 · 用户选回 dev")·
但实际暂停点没 emit · PMO 不知道要回 dev。
按 `FEATURE_FLOW: "review": ["test", "dev"]` 设计 · NEEDS_REVISION 应自动转 dev。

**修复**:
1. `_review_transition` NEEDS_REVISION 返回 `"dev"`(不再 None)
2. `execute_stage_complete` 加**回退路径检测** · `next_stage in completed_stages` = 回退:
   - 不加当前 stage 到 completed_stages(本 stage 没真完成)
   - 清 next_stage 的 contract gates(允许 dev-start 重做)
   - 当前 stage contract 标 `returned_to_prev` + `returned_at`(audit)
   - next_stage 标 `restarted_at`

### Bug #4 (P2) · reset-prev 自洽时无效但无提示

**症状**:`current_stage == last_completed`(异常状态)时 reset-prev 实际不动 · 但无错误提示。
典型 case:旧版 review NEEDS_REVISION bug 错误地把 review 加 completed_stages · 导致两者相等。

**根因**:`cmd_reset_prev` L1567-1571 取 `completed[-1]` 切回去 · 同值时 no-op。

**修复**:加硬门禁 3 · `current == last_completed` 时 die FAIL + emit hint:
- 排查 state.json 是否被外部修改
- v8.x 已修 review-complete bug · 此 case 已不应触发
- 若状态确需手工调整 → raw-write(留 concerns WARN)

### 测试

加 `TestReviewTransition` 3 用例(APPROVE → test / NEEDS_REVISION → dev / no verdict → None)。
v8 测试 45/45 全过(原 42 + 3 新)。
手工 verify:save_state checksum 与 state.py 一致 · _review_transition 正确转移。

### 影响 / 期望效果

PTR-F040 case 重跑应该:
- ❌ 5 次 recover → ✅ 0 次 recover(checksum 自动同步)
- ❌ 1 次 raw-write 补 dev evidence → ✅ 0 次(evidence 自动持久化)
- ❌ 1 次 raw-write 切 current_stage → ✅ 0 次(review NEEDS_REVISION 自动回 dev)
- ❌ 1 次 reset-prev workaround → ✅ 0 次(直接 dev-start 重做)

PMO 流畅度 + 用户对状态机信任度都大幅提升。

---

## v8.7 · localconfig md → json · bootstrap state 合并(去 .teamwork-bootstrap.json)

### 合并文件

- 删 `.teamwork-bootstrap.json`(独立 marker · v8.5 引入)
- bootstrap state 合并到 `.teamwork_localconfig.json` 的 `_bootstrap` 子段
- `.teamwork_localconfig.md`(原模板)→ `.teamwork_localconfig.json`(JSON 格式)

### .teamwork_localconfig.json 结构(选项 A · 单文件嵌套)

```json
{
  "worktree": "auto",            ← 用户编辑(commit 不限 · 默认 .gitignore)
  "worktree_root_path": ".worktree",
  "scope": "all",
  "merge_target": "staging",
  "worktree_cleanup": "ask",
  "mr_url_template": null,

  "_bootstrap": {                ← 工具维护(用户禁手改)
    "skill_version": "v8.7",
    "host": "claude-code",
    "last_maintain_at": "...",
    "last_maintain_results": {...}
  }
}
```

### bootstrap.py 改造

- 新增 `LOCALCONFIG_FILE = ".teamwork_localconfig.json"`
- 新增 `read_localconfig(project_root)` · 读 config + state 合并体
- `read_bootstrap_marker / write_bootstrap_marker` 改为操作 localconfig 的 `_bootstrap` 子段
- `write_bootstrap_marker` 必保留用户 config 段不动(只 update `_bootstrap`)
- `maintain_gitignore_worktree` 把 `.teamwork-bootstrap.json` → `.teamwork_localconfig.json`(整文件 .gitignore · 含 config 段:本地配置默认不 commit · 老 md 行为延续)

### 新模板

- `templates/teamwork_localconfig.json`(JSON 模板 · 含 _comment 字段说明)
- 字段:worktree / worktree_root_path / scope / merge_target / worktree_cleanup / mr_url_template + _bootstrap 段

### 老 .md 处理

bootstrap.py **不自动迁移** `.teamwork_localconfig.md`(项目级配置极少用户手编 · 当前没 Python 代码读它 · 老 md 留着不动 · 用户可手动迁)。
未来需要时可加 migrate 函数。

### cite 更新

- `templates/config.md` § .teamwork_localconfig 段(标题已改 .json)
- `docs/conventions.md` §10 worktree_root_path 配置(.md → .json)
- `docs/prepare.md` Step 2(.md → .json)
- `claude-agents/invoke.md`(model 配置覆盖位置 · .md → .json)

### 测试

- 加 TestBootstrapMarker.test_write_preserves_user_config_segment(覆盖 _bootstrap 写入不丢 config)
- 改 TestMaintainGitignoreWorktree(`.teamwork-bootstrap.json` → `.teamwork_localconfig.json`)
- v8 测试 42/42 全过

---

## v8.6 · 抽 prepare 为可重入子流程 · 解耦 triage / prepare 职责

### 问题

triage 中混了两件事:
1. 5 mode 分诊(query/execute/resume/status/discuss · 每 session PMO 承接用户输入跑一次)
2. 进状态机前的准备(流程类型识别 + worktree 决策 + 暂停点 · 只在 mode B 跑)

新场景不兼容:
- Feature Planning 完成后 PL 拍板某 BL → 启动 Feature 流程
- 已经在某 session 中 · triage 早跑过(mode E discuss)· 不会再跑
- 需要"流程类型识别 + worktree 决策 + 暂停点"逻辑 · 但 triage 已经用过

### 抽 prepare 子流程

新建 [docs/prepare.md](./prepare.md) · 包含:
- §1 触发场景(mode B / mode E 升级 / Feature Planning 启 Feature / mode A→B)
- §2-5 4 步(流程类型识别 / worktree 决策 / emit 暂停点 / 用户确认后执行)
- §6 与状态机的接口
- §7 错误处理
- §8 红线(R-P1 必经用户确认 / R-P2 不可枚举留 PMO)

### TRIAGE.md §4 简化

原 §4 (Mode B 子流程 · 4 个 step) → 简化为:
- §4.0 bootstrap.py(保留 · 任何 mode 都跑)
- §4.1 mode B → 走 prepare 子流程(指向 docs/prepare.md)
- 强调 prepare 可重入(mode E 升级 / Feature Planning 启 Feature 等都走)

### docs/feature-planning.md §5 更新

BL-NNN 启动 Feature 流程的步骤明确走 prepare:
```
PMO 走 prepare 子流程
 · flow_type = Feature(BL 已决定"做什么")
 · 收集 Feature ID(从 BL 推)
 · 收集 worktree/branch/merge_target(暂停点)
 · 用户确认 → init-feature
```

### 设计原则

- **triage** = 入口分诊(每 session 一次 · 5 mode 判定 · 输出 audit_line)
- **prepare** = 进状态机前的准备(可重入 · 任何"决定走某流程"的入口都跑一次)
- **职责正交**:triage 不关心后续走哪个流程 · prepare 不关心当前 mode

测试: v8 测试 38/38 全过(本次仅 markdown 改动 · 无 Python 行为变化)

---

## v8.5 · 删 install.sh · bootstrap.py 承接系统维护职责

### 删 install.sh

install.sh 设计为"用户首次安装跑一次"的部署脚本(复制 skill / 部署 hooks / sync-drift / chmod)。
但用户实际架构是 symlink(`~/.claude/skills/teamwork → repo/skills/teamwork`),install.sh 的复制部分 noop · 真有效部分 = chmod / hooks / sync-drift / .gitignore · 这些 bootstrap.py(每 session 启动跑)能更优雅承接(自愈 · 幂等)。

### bootstrap.py 加 4 个 maintain

- `maintain_chmod_tools(skill_root)`:tools/*.py + templates/*.py 加可执行位
- `maintain_host_hooks(skill_root, project_root, host)`:部署 hooks
  - claude-code:hooks/*.sh → `.claude/hooks/` + hooks.json(含 PreCompact)
  - codex-cli:codex-agents/hooks.json → `.codex/hooks.json` + codex-agents/*.toml → `.codex/agents/`
- `maintain_host_injection(...)`:原 `check_host_injection` 改 check → maintain · 缺则跑 sync-drift.py
- `maintain_gitignore_worktree(project_root)`:`.worktree/` → `.gitignore`(默认 worktree_root_path)

### bootstrap.py session 启动流程(silent)

```
1. SKILL_VERSION 校验
2. 项目骨架(KNOWLEDGE/TROUBLESHOOTING/GLOSSARY)
3. chmod +x tools/*.py + templates/*.py     ← 新加
4. 宿主 hooks 部署                            ← 新加
5. 宿主注入段同步(sync-drift.py)             ← 改 check → maintain
6. .worktree/ → .gitignore                   ← 新加
7. v7 state.json 扫描
```

### 删除 / 改名

- 删 `skills/teamwork/install.sh`(190+ 行)
- 改 `check_host_injection` → `maintain_host_injection`(语义 check → maintain)

### cite 路径更新

- standards/scripts-policy.md:install.sh 业务流程 → bash hook 业务流程
- docs/conventions.md:`install.sh 自动加 .gitignore` → `bootstrap.py session 启动时自动加`
- codex-agents/README.md / agents/README.md:install.sh 部署 → bootstrap.py 部署

### 顺手 chmod 修复

bootstrap.py maintain_chmod_tools 自愈跑了一次,把 `templates/verify-ac.py` 等 .py 文件从 644 → 755(用户从未跑过 install.sh · 这些文件之前没可执行位)。

### 不迁的部分

- 检测宿主 + 复制 skill 文件:用户用 symlink · 自助
- codex_hooks feature flag 写 `~/.codex/config.toml`:涉及用户全局 config · 留给手动(README 说明)

### 测试

- 加 TestMaintainChmodTools / TestMaintainGitignoreWorktree(覆盖新函数)
- 改 TestCheckHostInjection → TestMaintainHostInjection(行为变 · 删原 ok/missing 用例 · 加 host_unknown / sync_drift_missing 用例)
- v8 测试 38/38 全过

---

## v8.4 · Feature Planning 完全脱离状态机

> v8.1/v8.2/v8.3 的演进:把 Feature Planning 当 stage 处理 → 改单 stage planning → 终态:**完全脱离状态机**(由 PMO 主对话执行 · 类似问题排查)。

### 设计原则

Feature Planning 产出是**项目级文档**(PROJECT.md / ROADMAP.md / sitemap.md),不是 Feature artifact:
- 没 Feature ID(规划期分配 BL-NNN)
- 没 PRD/TC/TECH(那是 Feature 流程)
- 不出代码(R6)
- 不需要 worktree
- 不需要 ship 流程(直推或开 MR · 用户决定)

强行套状态机 = 复杂度无收益(stage 链只 1 步 · PMO 主对话能直接做)。

### state.py 改动

- 删 `LEGAL_STAGES` 中 `planning`
- 删 `PLANNING_FLOW`
- `FLOW_BY_TYPE` 删 `"Feature Planning"`
- 新加 `NON_STATE_MACHINE_FLOWS = {"Feature Planning", "问题排查"}`
- `DEFAULT_INITIAL_STAGE` 删 `"Feature Planning"` / `"问题排查"`(原 "问题排查": "triage" 也是残留 bug)
- `cmd_init_feature` 开头检查 flow_type ∈ NON_STATE_MACHINE_FLOWS → reject + emit hint 指向 docs/feature-planning.md / FLOWS.md § 问题排查

### _v8_stage_specs.py 改动

- 删 `PLANNING_SPEC` / `_check_flow_is_planning` / `_panorama_brief` / `_panorama_transition`
- `STAGE_SPECS` 删 `"planning"` key
- `_goal_transition` 删 `Feature Planning → planning` 分支
- `_evidence_needs_ui_decided` 删 Feature Planning + needs_ui=true 检查(进不到 goal 就不会触发)

### markdown 改动

- `stages/planning-stage.md` → `docs/feature-planning.md`(git mv 跨目录 + 改写为非 stage spec 格式)
- 新文件结构:6 个 substep(由 PMO 主对话执行)+ 6 注意事项 + 与 Feature 流程接口
- FLOWS.md § Feature Planning 改写:不进 stage 链 · 类似问题排查
- TRIAGE.md §4.2 worktree 表 / §4.3 first_stage 映射:Feature Planning 标"不进 stage 链"
- SKILL.md / RULES.md R6 物化描述 → init-feature reject + cite docs/feature-planning.md
- conventions.md cite 路径更新

### 测试

- 删 `test_planning_flow_needs_ui_true_rejected`(进不到 needs-ui check 就触发不到)
- v8 测试 36/36 全过

### 兼容性 / 待办

- 老 v8.x state.json 含 `current_stage: planning` 现在不被识别 · 用户需手动归档(`state.py raw-write` 或直接删 state.json)
- _v8_migrate.py 的 `STAGE_RENAMES` 暂不动(panorama_design → planning 仍能跑 · 但产出失效 · 用户跑后会撞 init-feature reject 提示)
- 后续 v8.5 可考虑加 v8.x → v8.4 迁移自动归档失效 state.json

---

## v8.3 · docs/naming.md → docs/conventions.md(合并 worktree 规范)

### 改名 + 扩展

- `docs/naming.md` → `docs/conventions.md`(git mv 保历史)
- 加 §9-12:worktree 路径规范(默认 `.worktree` / 配置字段 / monorepo 多模块策略 / 状态机接口)
- 单源:命名 + worktree 都进同一文件 · 引用方少一处 cite

### worktree 路径规范(原本散落 3 处 · 互相矛盾)

| 原位置 | 内容 | 矛盾 |
|---|---|---|
| TRIAGE.md L117-119 | 模板 `<repo-root>/worktrees/<FEATURE-ID>` | `<repo-root>` 没定义 |
| templates/config.md L128-151 | `worktree_root_path` 字段 + 3 示例 | 与 TRIAGE 模板不同 |
| SKILL.md L248-249 | 状态行例子 `aon-ptr-worktrees/` | 模块 sibling · 不在两处任一示例 |

收敛到 conventions.md 单源:
- **默认** `.worktree`(项目根)
- **可配** 项目根 `.teamwork_localconfig.md` 的 `worktree_root_path` 字段
- **解析优先级** state.json > localconfig > 默认
- **monorepo 多模块**:推荐 per-module(各模块独立 `../.{module}-worktrees/`)

### cite 路径更新

- TRIAGE.md §4.2 worktree 模板表简化 + cite conventions.md §9-11
- TRIAGE.md §4.3 暂停点 worktree path 默认值 cite
- templates/config.md §Worktree 根目录 段简化 + cite(原 30 行 → 5 行)
- naming.md → conventions.md 全部 cite 引用更新(TRIAGE / planning-stage / templates/bug-report / templates/roadmap)

### 顺手修 templates/config.md mojibake

- 在 e1d12b2 perl 误切的 21 损坏文件名单里
- restore from bb11e1d + python utf-8 safe 重做 P0 清理

测试: v8 测试 37/37 全过

剩余 20 个 mojibake 文件待下个 commit 处理。

---

## v8.2 · 编号规范单源 + Feature Planning 单 stage + goal 收紧

### 新增 docs/naming.md(编号规范单源)

补 v7 `rules/naming.md` 在 v8 重构时被误删的编号规则:
- Feature ID:`{项目缩写}-F{NNN}` · 各项目独立 namespace
- Bug ID:`BUG-{项目缩写}-F{NNN}-{seq}` · Feature 内独立递增
- ADR ID:`ADR-{NNNN}` · **全局**递增
- BL ↔ F 映射:各自独立递增 · 通过 ROADMAP「对应 F编号」列建链接 · 不强制同号
- Dispatch / KNOWLEDGE 子 ID 等
- 项目缩写注册规则

### Feature Planning 流程独立(承 v8.1 · 修复设计 bug)

- v8.1 `PLANNING_FLOW = {goal: [planning], planning: [completed]}` 是错的(Feature Planning 进 goal 会装错"PRD 起草"语义)
- v8.2 修正为 `PLANNING_FLOW = {planning: [completed]}` 单 stage
- `GOAL_SPEC.allowed_flow_types=["Feature", "敏捷需求"]`(收紧 · 不再允许 Feature Planning 进 goal)
- `PLANNING_SPEC.allowed_flow_types=["Feature Planning"]`(沿用)
- `state.py first_stage` 映射:Feature Planning → planning(已是)

### planning-stage.md 增段

- §流程边界(R6 物化:不写代码 / 不写 PRD / 完成自动 completed)
- §范围判定(子项目级 vs 工作区级)
- §Level 判定(配合 product-overview/ · 可选 · Level 1-3)
- §3 ROADMAP 起草加 BL-NNN 分配规则 + cite docs/naming.md

### broken refs 修复(本轮)

- templates/bug-report.md L4: `[RULES.md]` 编号规则章节(不存在)→ `[docs/naming.md § 2]`
- templates/bug-report.md L14: `rules/naming.md`(已删)→ `docs/naming.md § 2`
- TRIAGE.md §4.3: Feature ID 行加 cite `docs/naming.md § 1`
- templates/roadmap.md §字段说明: BL/F 映射 → cite `docs/naming.md § 4`(原冗述简化)

### 顺手清 templates/bug-report.md mojibake

P0 cleanup (commit e1d12b2) 的 perl 替换以 byte 模式工作,误切了中文 utf-8 序列,造成 22 文件 mojibake。本 commit 仅修我要改的 templates/bug-report.md(restore + utf-8 safe 重做 P0 清理)。其余 21 文件待下个 commit。

---

## v8.1 · stage 改名 + Feature Planning 流程独立

> 治本 v8.0 stage 命名错位:`goal_plan` 既混"目标规划"又装 PRD 起草 ·
> `panorama_design` 是 Feature Planning 专属但名字晦涩 + 错混进 FEATURE_FLOW 表。

### 改名

- `goal_plan` → `goal`(业务目标确认 stage · 产 PRD)
- `panorama_design` → `planning`(Feature Planning 拆 ROADMAP stage)
- `stages/goal-plan-stage.md` → `stages/goal-stage.md`(git mv 保历史)
- `stages/panorama-design-stage.md` → `stages/planning-stage.md`(git mv 保历史)

### state.py 改动

- `LEGAL_STAGES`:`goal_plan/panorama_design` → `goal/planning`
- `FEATURE_FLOW`:删 `panorama_design: ["blueprint"]` 残留(原本不应在 Feature 流程)
- 加 `PLANNING_FLOW = {goal: [planning], planning: [completed]}`
- `FLOW_BY_TYPE` 加 `"Feature Planning": PLANNING_FLOW`(之前缺)
- 命令 `goal_plan-start/complete` → `goal-start/complete`
- 命令 `panorama_design-start/complete` → `planning-start/complete`

### 迁移

- 新增 `state.py migrate-v8-stage-rename --feature <path>`
- 老 v8.0 Feature(state.json schema_version=v8.0)跑此命令升 v8.1
- 备份原文件为 `state.json.v8-0-backup`
- 改 schema_version v8.0 → v8.1
- 替换 current_stage / completed_stages / legal_next_stages / stage_contracts / stage_review_roles 中的 stage 名

### 范围

11 文件 ~70 处引用统一替换(SKILL/FLOWS/TRIAGE/ROLES/RULES/pm.md/各 stages spec/state.py/_v8_*.py/templates/review-log.jsonl)。

---

## v8.0+P0-1 ~ P0-5(PTR-F033 实战 case 治本 · 5 个连续 patch)

> 第一个真实 Feature(PTR-F033 Partner Credit Note Adjustment)dogfood 中暴露 v8 多个设计缺口。
> 完整反思见 [docs/archive/v8-redesign/05-LESSONS-FROM-PTR-F033.md](./v8-redesign/05-LESSONS-FROM-PTR-F033.md)。

### P0-1 · 暂停点纪律(L2 substep 链)
- ➕ `_v8_engine.py` 加 `_render_pause_discipline()` + `StageSpec.authorized_pause_point`
- ➕ `execute_stage_start` 自动 append 暂停点纪律段到 brief 末尾
- ➕ `_v8_stage_specs.py` 加 `_evidence_review_after_primary` + `_evidence_revision_history_present`
- ➕ `MAX_BRIEF_LINES=100` 软上限 + 超限自动外置到磁盘
- ➕ `docs/archive/v8-redesign/04-PAUSE-POINT-DISCIPLINE.md`

### P0-2 · worktree 物理存在校验
- ➕ `_v8_engine._worktree_physically_exists()` · stage-start 通用校验
- ⚠️ `init-feature` 自动建 worktree 逻辑(本 P0 引入)在 P0-5 删除(单一职责)

### P0-3 · cwd 物化校验
- ➕ `state.py cmd_init_feature` 加 cwd / feature_path 双校验
- ➕ `TEAMWORK_BYPASS_CWD_WORKTREE=1` env bypass
- ➕ `_v8_engine.commit_exists` cwd bug 修复(用 feature_path 本身 · 不是 parent)

### P0-4 · brief 末尾必读路径速查
- ➕ `_v8_engine._render_required_paths()` · 所有 stage brief 自动 append 绝对路径列表
- 列出**实际存在**的 Feature artifact + stage spec + state.json
- "按需文档"区根据 v8 哲学不列(AI 实地能拿到)

### P0-5 · 概念清理 + 入口规范(triage 不是 stage)
- 🗑️ `state.py cmd_init_feature` 删 P0-2 自动建 worktree 逻辑(`_try_create_worktree` 函数)
- ➕ `_v8_init.py cmd_triage` mode B emit 加 `worktree_decision` + `pause_for_user.markdown`
- ➕ triage emit 含暂停点 · 等用户确认 Feature ID / merge_target / worktree path / branch
- ➕ `state.py cmd_init_feature` 加 worktree 物理存在硬校验(取代 P0-2 自动建)
- ➕ **`TRIAGE.md` 顶级文档**(与 SKILL.md / RULES.md / FLOWS.md 平级)· 入口规范权威
- ✏️ `SKILL.md` 概念清理:三层级 Stage 改为"入口规范(TRIAGE) + 状态机层(state.py)"二层
- ➕ `docs/archive/v8-redesign/05-LESSONS-FROM-PTR-F033.md` · 5 patch 治本汇总

### 新元规则(P0-1~P0-5 提炼)

1. **state.json 字段必须有 action + verifier**(谁创建 + 谁校验)
2. **状态机入口/出口物化拦截**(cwd 校验 / 产物校验 / 间接 evidence)
3. **brief 长度上限 + 自动外置**(防 Layer A 累积膨胀)
4. **入口规范层 vs 状态机层** 二层架构(triage 不是 stage)

### v8 文档体系新结构

```
顶级:SKILL.md / TRIAGE.md / RULES.md / FLOWS.md / ROLES.md / STANDARDS.md / TEMPLATES.md
stages/:11 个 stage 内容创作规范(待 P0-6 重写)
docs/archive/v8-redesign/:00 MANIFESTO / 01 SCHEMA / 02 CLEANUP / 03 MIGRATION / 04 PAUSE-POINT / 05 LESSONS-FROM-PTR-F033
```

### ROI

PTR-F033 一个真实 case 触发 4 个 P0 patch + 1 个概念清理 + 4 个元规则。
这印证 v8 哲学:**dogfood 实战 > 闭门设计** + **物化拦截 > AI 自觉**。

---

## v8.0.0(当前 · Code-driven Orchestration · 范式切换 · 不向下兼容)

> **触发**:v7.3.10 累积 156 个 P0 patch · 元规则(加 1 删 1 / 文件 300 行 / 红线生命周期)堆栈防膨胀。
> 实战发现:状态机骨架是物化的,但 gate 满足"达成依据"基本不是物化的 — AI 仍可 0 事实裸调 satisfy-gate。
> 触发根本问题反思:**"可枚举规则进脚本,不可枚举判断留 AI"** — v7 把可枚举规则塞 markdown 让 AI 自觉 cite 的范式从根本上反工程学。

### 范式切换:从"AI 自觉框架"到"代码驱动框架"

```
v7(被替换):                           v8.0:
PMO 凭记忆 + 读 spec markdown            AI 跑 state.py xx-start
       ↓                                      ↓
按记忆调度 stage / role                 state.py 主动校验 + 主动告知(JSON + brief)
       ↓                                      ↓
state.py 被动记录                        AI 按 state.py 指示执行
                                              ↓
                                         AI 跑 state.py xx-complete
                                              ↓
                                         state.py 校验产物 + 自动转移 + 输出下一 stage brief
```

### 新增 · state.py 命令(从 18 → 30)

**初始化(3)**:
- ➕ `init-feature`(沿用 v7 · schema_version=v8.0)
- ➕ `triage` — session 入口 5 mode 分诊(替代 init_triage.py + stages/triage-stage.md)
- ➕ `prepare` — mode B 重型准备(替代 stages/prepare-stage.md)

**Stage 流转(23 = 11 stage × 2 + ship-phase)**:
- ➕ 11 stage × 2:`goal_plan-start/complete` / `ui_design-*` / `panorama_design-*` / `blueprint-*` / `blueprint_lite-*` / `dev-*` / `review-*` / `test-*` / `browser_e2e-*` / `pm_acceptance-*` / `ship-*`
- ➕ `ship-phase --action {sanitize|push|confirm-merged|cleanup|close-unmerged}` — 统一入口(替代 v7 五个独立 ship-* 命令)

**维护(2 沿用 + 1 新增)**:
- ➕ `migrate-v7-to-v8` — 一次性迁移老 state.json 从 v7 → v8 schema

### 删除 · v7 命令(物理删除 12 个)

- ❌ `enter-stage` / `satisfy-gate` / `complete-stage` → 各 stage 专属 -start/-complete 替代
- ❌ `ship-sanitize` / `ship-push` / `ship-confirm-merged` / `ship-cleanup` / `ship-closed` → `ship-phase --action`
- ❌ `pm-decision` → `pm_acceptance-complete --decision`
- ❌ `add-concern` / `bug-frontmatter` / `micro-validate` → 内部 utility · 不暴露 user-facing

### 删除 · 工具文件(物理删除 5 个 Python)

- ❌ `tools/init_triage.py` → `state.py triage` 内置
- ❌ `tools/render-flow-transition.py` → `state.py xx-start/complete` 自 emit 流转信息
- ❌ `tools/render-decision-pause.py` → `state.py xx-complete` 自 emit 暂停点 markdown
- ❌ `tools/render-afk-skip.py` → `state.py` 内部 AFK 判定
- ❌ `tools/render-status-line.py` → `state.py` 每命令尾部自 emit 状态行

### 删除 · 流程类规范 markdown(13 个)

- ❌ `rules/`(整个目录:`flow-transitions.md` / `gate-checks.md` / `naming.md`)→ 进 state.py LEGAL_TRANSITIONS / STAGE_SPECS
- ❌ `standards/evidence-binding.md` → `_v8_engine.py` execute_stage_complete
- ❌ `standards/output-tiers.md` → state.py emit 自适配
- ❌ `standards/review-verdict.md` → state.py review-complete --verdict
- ❌ `standards/review-scope.md` → state.py review/blueprint stage spec
- ❌ `standards/prompt-cache.md` → state.py 内部 Read 顺序
- ❌ `standards/stage-instantiation.md` → state.py 各 stage prerequisites
- ❌ `standards/discussion-mode.md` → state.py triage mode E
- ❌ `standards/external-model.md` → state.py _v8_init.detect_host
- ❌ `STATUS-LINE.md` → state.py 每命令尾部 emit
- ❌ `CONTEXT-RECOVERY.md` → state.py recover
- ❌ `REVIEWS.md` → state.py review-complete artifact 校验

### 删除 · stages/(2 文件) + templates/(2 文件) + roles/(13 sub-file)

- ❌ `stages/triage-stage.md` / `stages/prepare-stage.md` → state.py 内部
- ❌ `templates/feature-state.json` / `templates/dispatch.md` → state.py 自生成
- ❌ `roles/pmo-*.md`(7 sub-file)→ 编排逻辑进 state.py
- ❌ `roles/architect-cr.md` / `architect-tech-review.md` → review-stage / blueprint-stage spec
- ❌ `roles/qa-cr.md` / `qa-tc-review.md` → 同上
- ❌ `roles/pm-prd-review.md` → goal_plan-complete artifact 校验
- ❌ `roles/product-lead-change-mgmt.md` → 进 state.py(v8.x 物化)

### 减负 · 顶层 markdown 大幅瘦身

| 文件 | v7 行数 | v8 行数 | ↓ |
|------|---------|---------|---|
| SKILL.md | 806 | ~180 | -77% |
| RULES.md | 1883 | ~180 | -90% |
| FLOWS.md | 876 | ~120 | -86% |
| stages/* (10 文件) | 5102 | 382 | -92% |
| roles/* (21 → 8 文件) | 5252 | 247 | -95% |

**总 markdown 减负:~14000 行 → ~1500 行(↓ 89%)**

### 新增模块 · state.py 扩张

- ➕ `tools/_v8_engine.py`(~700 行)— 通用 stage start/complete + bypass 协议 + register_v8_subparsers
- ➕ `tools/_v8_stage_specs.py`(~1100 行)— 11 stage 完整契约(STAGE_SPECS dict)
- ➕ `tools/_v8_ship.py`(~430 行)— ship-phase 5 actions + 物化拦截(P0-156/P0-124/P0-113 沿用)
- ➕ `tools/_v8_init.py`(~400 行)— triage + prepare(5 mode 分诊 + 流程类型识别)
- ➕ `tools/_v8_migrate.py`(~110 行)— v7 → v8 state.json 一次性迁移
- ✏️ `tools/state.py`(原 1609 行 + v8 注册 12 行 + v7 子命令删除 ~100 行)→ 净保持 ~1520 行

### bypass 协议 · 用户确认逃生通道

```
PMO 重试 3 次仍 FAIL → 暂停点询问用户 → 用户选"逃生":

state.py xx-start --bypass --reason "<原因>" --user-confirmed --missing <ids>
   ↓
state.py:
  - 校验 --user-confirmed 必带(防 AI 自决 · 红线违规拦截)
  - 校验 --missing 覆盖实际 missing
  - 通过 + 自动写 bypass_log[] + concerns WARN(完整审计闭环)
```

### 红线 · 16 → 9(可枚举的全物化)

| v7 红线 | v8 归宿 |
|---------|---------|
| R1-R9 中 16/17 子条目 | 物化进 state.py |
| R3 PMO 统一承接 | 唯一仍是软约束(不可枚举) |

红线文档不再讲"怎么校验",只讲"为什么这么设计"。

### 设计文档(立法层)

- ➕ `docs/archive/v8-redesign/00-MANIFESTO.md`(~400 行)— 设计宪法 · 范式切换 · 4 支柱划分
- ➕ `docs/archive/v8-redesign/01-COMMAND-SCHEMA.md`(~700 行)— 全 30 命令精确 schema
- ➕ `docs/archive/v8-redesign/02-CLEANUP.md`(~350 行)— v7 → v8 清理清单
- ➕ `docs/archive/v8-redesign/03-MIGRATION.md`(~300 行)— 迁移路线图

### 兼容性

- **不向下兼容**:v7 命令(enter-stage / satisfy-gate / complete-stage / ship-* / pm-decision / add-concern / bug-frontmatter / micro-validate)全部物理删除。
- **老 Feature 迁移**:跑 `state.py migrate-v7-to-v8 --feature <path>` · 自动备份原文件为 `.json.v7-backup`。
- **CLAUDE.md 注入段**:`sync-drift.py` 已自动同步 v8 SKILL.md 版本号到注入段。

### 设计哲学(写入 SKILL.md 顶部)

> **可枚举的规则进脚本,不可枚举的判断留 AI。**

这条根本判据取代 v7 所有划界原则(L1/L2/L3 红线层级 / teamwork 主权 vs 用户主权 / AI 实地能拿到的就不显式维护)。
"可枚举"是个客观判据:能列出来的就进代码,列不全的留 AI。

### 实证验证(本次 ship 前)

所有 v8 命令通过端到端测试:
- ✅ Bug 流程 dev-start happy path
- ✅ Bypass 协议三档:防 AI 自决 + 完整审计
- ✅ 状态机非法转移:5 stage 全拦截
- ✅ flow_type 闭集:allowed_flow_types 拦截
- ✅ ship-phase 端到端 6/6 PASS(sanitize → push → cleanup BLOCKED → confirm-merged → cleanup PASS)
- ✅ triage 5 mode 分诊 + 6 流程关键词识别

### 致 v7.3.10+P0-156(155 个 P0 patch 收尾)

v7.3.10 累积的 156 个 P0 patch 是反 spec 累积膨胀的工程奇迹 · 但本质是"修补 AI 凭记忆做事"的不断 patch。
v8.0 不再做这种 patch · 而是从根本上把"凭记忆"从范式中移除。

v7 → v8 不是版本升级 · 是范式切换。版本号从 v7.3.10+P0-156 跳到 v8.0.0 标记这一点。

---

## v7.3.10 + P0-156（当前 · ship-confirm-merged + ship-cleanup linked-worktree 物化拦截 · 治本 ADMIN-F013 状态更新丢失）

> **触发**：实战 case · ADMIN-F013 Tax & Billing Entity Configuration · agent 在 feature worktree (`/Users/liam/apps/joli/aon/aon-admin-wt/feat-admin-f013`) 跑 `ship-confirm-merged` · state.json 写到 worktree · 然后 `git worktree remove --force` · state.json 随 worktree 一起被删 · 后续 `ship-cleanup` FAIL "state.json not found" · agent narrative "state.json 在 worktree 里已被删了 · worktree 清理完成" 把失败合理化为正常.
>
> **诊断**：spec ship-stage.md § Step 6 明文要求 "cd 到 merge_target 主工作区 + git checkout + git pull" 再跑 Step 7-9（写 state.json final + commit + push + worktree 清理）· 但 spec 是 writer-only · 工具层没拦截 · agent 走捷径在 feature worktree 跑 Step 7 → state.json 写错位置 → 后续 Step 9（worktree remove）连锁删除 → 状态永久丢失. R-SP-8 同型缺 reader 兜底.

### P0-156：linked-worktree 物化拦截（路径 A · 同 P0-154 物化层模式）

加 1 删 0 改账（tool + spec · 路径 B 组合 · L1 红线零增量）：

**state.py 物化拦截**：

- ➕ [tools/state.py](../tools/state.py) 新增 `_check_main_worktree()` + `_enforce_main_worktree()` helper：
  - 检测 `git rev-parse --git-dir` 输出含 `/worktrees/` → 视为 linked worktree
  - 旁路：`TEAMWORK_BYPASS_MAIN_WORKTREE=1`（migration / debug）
  - 测试模拟：`TEAMWORK_FORCE_LINKED_WORKTREE=<git_dir>`（test fixtures 用）
- ➕ `cmd_ship_confirm_merged` 头部加 `_enforce_main_worktree("ship-confirm-merged")` · linked worktree → exit 2 FAIL
- ➕ `cmd_ship_cleanup` 同型加保护（defense in depth · 即使 cwd 已重置仍兜底）
- 失败 hint 明确：`cd 到 merge_target 主工作区 · git checkout {merge_target} + git pull --ff-only · 再跑此命令` + cite ship-stage.md § Step 6

**测试**：

- ➕ [tools/tests/test_state.py](../tools/tests/test_state.py) `run()` helper 加 `env_extra` 参数（subprocess env 注入）
- ➕ 3 新测试（TestP3Ship 类下）：
  - test_ship_confirm_merged_rejects_linked_worktree：FORCE linked → exit 2 + cite P0-156 + ship-stage.md
  - test_ship_cleanup_rejects_linked_worktree：同型保护
  - test_ship_confirm_merged_bypass_main_worktree：BYPASS=1 旁路验证

**spec cite**：

- ➕ [stages/ship-stage.md § state.json 写操作入口 § 硬门禁](../stages/ship-stage.md) 加 P0-156 拦截说明 + 实战 case 描述（ADMIN-F013 状态更新丢失链路）

不动（边界严格 · L1 红线零增量）：
- SKILL.md 9 条红线不动
- ship Step 1-3（push / MR creation）允许在 feature worktree 运行（spec 本就如此）· 不加 main-worktree 检查
- ship-closed (abandon) 不加检查（异常分支 · 多场景兼容）
- ship-sanitize / ship-push 不加检查（Step 1-2 阶段允许在 feature worktree）
- 工具其他子命令不动

**纵深防御层级**（同 P0-154 + P0-156 协同）：

| 层 | 拦截位置 | 触发条件 | 失败结果 |
|---|---------|---------|---------|
| L1 spec | ship-stage.md Step 6 文字描述 | spec 阅读 | 软警示（agent 易跳）|
| L2 物化 cwd | state.py ship-confirm-merged / ship-cleanup linked check | 命令执行 | exit 2 + 明确 hint 切主工作区 |
| L2 物化 phase | state.py ship-cleanup phase ≠ merged check（P0-124）| 命令执行 | exit 1 BLOCKED |
| L3 checksum | state.py _state_checksum guard（P0-148）| 任何读 | exit 2 mismatch |

P0-156 补的是 **L2 物化 cwd 层** · 之前 phase + checksum 层都已物化 · cwd 层是 missing piece.

**ADMIN-F013 案例若用 P0-156 重跑**：

1. agent 在 feature worktree 跑 `ship-confirm-merged` → **FAIL exit 2** "必须在主工作区运行" + hint
2. agent 读 hint · cd 到主工作区 + checkout staging + pull · 再跑 → PASS · state.json 写到主工作区
3. agent commit + push state.json（红线 R1 例外 · 一文件）
4. agent `git worktree remove` feature worktree → 安全（state.json 已在主工作区 committed）
5. agent 跑 `ship-cleanup` → PASS · 状态机完整

**测试**：187/187 PASS（+3 新测试 · 累计 +15 since P0-153）.

**实战 trigger 闭环 commit #12**：P0-145..155 → P0-156。用户问"ship 后的状态更新也有问题" → R-SP-8 reader 兜底 cwd 物化拦截 → 治本.

**教训**（与 P0-154/151 同型）：
- spec 写"必须做 X"不够 · 还要写"禁止走 Y 替代路径" + 工具物化拦截
- agent narrative 能合理化任何失败（"state.json 在 worktree 里已被删了" = 真但缺关键 context）· 工具 FAIL 必须强阻断 · 不能依赖 agent 理性
- cwd 层是个常被忽略的物化维度 · 同型可应用到其他 Step 6-9 类命令（Bug 流程 finalize / 跨子项目 ship）· 等实战触发再加

R7(b) 视角：agent 在 plan 里若声明"Step 6: cd to merge_target" 但实际跳过 = 违约。P0-156 在工具层拦截这种违约（cwd 不是 main 就 die）· 比 R7(b) plan 审计更早.

---

## v7.3.10 + P0-155（render-flow-transition.py section-aware 过滤 · 治本 Dev→Review 跨 section 歧义）

> **触发**：实战 case · PTR-F032-billing-payment · agent 调 `render-flow-transition.py --from "Dev" --to "Review"` → FAIL "匹配歧义：2 处命中"（L163 + L264）· agent 改 `--from "Dev Stage" --to "Review Stage"` 同样 FAIL · 死循环 · agent 放弃工具手动 emit 流转注解.
>
> **诊断**：flow-transitions.md 同一转移合法地存在于多个 section（Feature 流程 L163 + 敏捷需求流程 L264）· 工具全文 grep 找 `(from, to)` 没有 section 维度 · hint "缩窄关键词" 是死循环（两行 from/to 内容完全相同）.
>
> **影响面**：所有同时在 Feature + 敏捷需求两个 flow 都有的转移（Dev→Review / Review→Test / Test→PM 等常用转移）· 必跳工具.

### P0-155：section-aware 过滤（tool only · 不动 spec）

加 1 删 0 改账（仅 tool · 路径 B 同 P0-154）：

- ➕ [tools/render-flow-transition.py](../tools/render-flow-transition.py) 加 section-aware 能力：
  - 新增 `parse_sections()` / `section_for_line()` / `_section_topic()` / `_match_flow()` 函数
  - `SECTION_RE` 识别 `## 标题` · `SECTION_SUFFIXES` 剥离"流程"/"模式"/"状态转移"等尾缀拿 topic
  - `find_matches()` 签名增加 `sections` 参数 · 返回 4-tuple `(line, raw, parsed, section_title)`
  - CLI 新增 `--flow` 参数（free text · 精确匹配 section topic）
  - CLI 新增 `--feature` 参数（Feature 路径 · 自动从 `state.json.flow_type` 派生 `--flow`）
  - effective_flow 推断：`--flow` 显式 > `--feature` 派生 > 无（fallback 到原行为）
  - 失败 hint 升级：歧义时列每个匹配的 section + raw + L行号 + 提示用 `--flow` / `--feature`
  - tool_version v1.0 → v1.1
- ➕ [tools/tests/test_render_flow_transition.py](../tools/tests/test_render_flow_transition.py) 加 8 测试：
  - test_dev_review_ambiguous_without_flow：无 --flow 仍歧义 FAIL · 含 section 信息
  - test_dev_review_flow_feature_resolves：--flow Feature 解到 L163
  - test_dev_review_flow_agile_resolves：--flow 敏捷需求 解到 L264
  - test_flow_topic_strips_suffix_exact：topic 精确匹配 · 不会 "Feature" 错配 "Feature Planning 流程"
  - TestP0_155FeatureAutoDerive 类 4 测试：
    - --feature 路径含 state.json Feature → 自动派生
    - --feature 路径含 state.json 敏捷需求 → 自动派生
    - --feature 路径无 state.json → 静默 fallback 仍歧义
    - --flow 显式优先 --feature 派生

不动（边界严格）：
- spec 不动（flow-transitions.md L163/L264 是合法的两条 · 不合并）
- 其他 render-* 工具不动（未触发同型问题）
- 老调用方式保持兼容（不传 --flow / --feature 行为不变）

**P0-155 解的具体调用对照**：

| 调用 | P0-154 行为 | P0-155 行为 |
|-----|----------|----------|
| `--from Dev --to Review` | FAIL 歧义 · hint 死循环 | FAIL 歧义 · 但 matches_detail 列两 section + hint 提示 `--flow` / `--feature` |
| `--from Dev --to Review --flow Feature` | unknown arg | PASS L163 |
| `--from Dev --to Review --feature {path}` | unknown arg | 自动读 state.json.flow_type → 派生 --flow → PASS |
| `--from 设计批 待确认 --to Blueprint`（单一匹配）| PASS | PASS（向后兼容） |

**测试**：184/184 PASS（+8 新测试 / 累计 +12 since P0-153）.

**实战 trigger 闭环 commit #11**：P0-145..154 → P0-155。用户问"脚本是否有问题" → 工具层 bug 确认 → A 路径 tool only 修复.

**教训**：tool 设计假设"`(from, to)` 全局唯一"在 spec 多 section 时不成立 · R-SP-8 reader 工具必须感知 spec 结构（含 section 维度）· 而不是只看表格行. 同型反思可应用到其他 render-* 工具 · 但当前不动 · 等实战触发再扩.

---

## v7.3.10 + P0-154（external 评审跳步物化拦截 + 措辞黑名单 · 治本 SVC-PLATFORM-F043 跳 codex CR）

> **触发**：实战 case · SVC-PLATFORM-F043-Adapter-MobPower · agent 走完架构师 CR + QA CR 后**直接转 `📋 review → test`** · **跳了 codex CR** · 用户问"外部模型 review 了么" · agent 自承"没有 · 补上"。
>
> **深层诊断**（5 层）：
> 1. **物化拦截缺位**（最根本）：`state.py satisfy-gate --stage review --gate output` 没校验 codex 产物存在 · spec 写"默认 ON"但没物化层 enforce
> 2. **Plan/执行解耦**：agent 自己在 Execution Plan 写了 `Steps remaining: 架构师 CR → QA CR → codex CR → 汇合` · 跑完 QA CR 就跳了 codex CR
> 3. **措辞陷阱**："Approach: hybrid (架构师+QA 主对话 + codex 后台)" — "后台" 暗示**异步可省** · 而 spec 实际要求同步等结果
> 4. **历史心智路径残留**：P0-13 ~ P0-152 "Codex 是 opt-in / 可选" 印象深 · 即使 P0-153 翻转默认 ON · agent 心智仍把 codex 当可省项
> 5. **LLM 经济压力**：codex CR 5-15 min · 看到架构师+QA PASS 就"提前闭环"诱惑大

### P0-154：路径 A（物化拦截）+ 路径 C（措辞黑名单）组合

加 1 删 0 改账（spec + tool · 与 P0-153 路径 B 同纵深防御组合）：

**路径 A：物化拦截（最硬）**

- ➕ [tools/state.py](../tools/state.py) 新增 `_check_external_review_artifact` helper + `EXTERNAL_REVIEW_STAGES = ("blueprint", "review")` 常量：
  - cmd_satisfy_gate 在 gate=output 时调用
  - 条件：stage ∈ (blueprint, review) AND `{stage}_substeps_config.review_roles[]` 显式含 external
  - 校验：`{artifact_root}/external-cross-review/` 目录存在 + 含 ≥1 `*.md` 文件
  - 失败：exit 1 + hint "跑 codex CR · 或显式 opt-out（review_roles[] 移除 external）"
  - 跳过场景：stage 不适用 / config 未实例化 / review_roles[] 不含 external / artifact_root 缺失
- ➕ [tools/tests/test_state.py](../tools/tests/test_state.py) 新增 4 测试：
  - artifact missing → FAIL（含 P0-154 rule 标记）
  - artifact present → PASS
  - external opt-out → PASS（不校验）
  - 非 EXTERNAL_REVIEW_STAGES（如 dev）→ PASS（边界）

**路径 C：措辞黑名单（轻量护栏）**

- ➕ [stages/review-stage.md § 过程硬规则](../stages/review-stage.md) 加 🔴 external 评审跳步禁令：
  - 反模式黑名单 4 条（"codex 后台" / "codex 异步" / "可选 codex" 措辞 + "PASS 后跳" 心智路径 + 流转注解掩盖缺席 + 静默 skip）
  - 推荐措辞（"codex subagent 必跑 · 同步等结果" + Steps remaining 必列）
  - 下游消费者标注：state.py satisfy-gate output 物化校验
- ➕ [stages/blueprint-stage.md § 硬规则](../stages/blueprint-stage.md) 加同型 🔴 跳步禁令（与 review-stage.md 镜像 · 适配 blueprint-{model}.md 产物名）

不动（边界严格）：
- L1 红线零增量（SKILL.md 9 条不动）
- agents/README.md § 三选一降级机制不动（已是合规路径）
- external-model.md / external-reviewer.md 不动（角色规范已足）
- BlueprintLite Stage 不动（敏捷需求无 external 配置）
- enter-stage 不动（拦截点已在 satisfy-gate output · 不重复）

**纵深防御层级**：

| 层 | 拦截位置 | 触发条件 | 失败结果 |
|---|---------|---------|---------|
| L1 spec | review-stage.md / blueprint-stage.md § 硬规则 | agent 写 plan 时 | 黑名单措辞警示 · 软性 |
| L2 物化 | state.py satisfy-gate --gate output | output gate 实际尝试 | exit 1 · 硬阻断 |
| L3 R-SP-8 | （已有）独立性校验 grep | finalize gate | 互引用 → 拒绝 |

P0-154 加固 L2 物理层 + L1 spec 措辞黑名单 · L3 一直在.

**测试**：176/176 PASS（+4 新测试 · 物化校验路径全覆盖）

**实战 trigger 闭环 commit #10**：P0-145..153 → P0-154。用户问"外部模型 review 了么" → agent 自承跳了 → 用户继续问"深层原因" → 5 层诊断 → 路径 A+C 组合修复。

**教训（与 P0-151/152 同型）**：spec 写"默认 ON"不够 · 还要：
1. 加物化拦截让"跳"在工具层就失败（不依赖 agent 自觉）
2. 加反模式黑名单让"跳" 心智路径在 plan 阶段就被警示
3. R-SP-8 reader 兜底：writer 规则（"必跑 codex"）必须配 reader 校验工具（state.py 校验产物存在）

R7(b) 声明即承诺 视角：agent 在 plan 里声明的"Steps remaining: codex CR" 是合同 · 实际跳步 = 违约 · 未来可扩展 R7(b) 加"声明的 Steps 每步必须有 ToolUse 证据"（路径 B 暂留 · 等 P0-154 实证 1-2 case 看跳步频率降不降）.

---

## v7.3.10 + P0-153（Blueprint Stage external 评审默认 ON · 翻转 P0-13 OFF）

> **触发**：用户提议"feature 改为默认开外部模型 review" · 翻转 v7.3.9+P0-13 当初定的 Blueprint 默认 OFF。
>
> **诊断**：P0-13 当初基于"Blueprint 文档评审有 RD/Designer/QA/PMO + 架构师 4 视角内部闭环 · Codex 边际价值低"判定 OFF。复盘发现：
> 1. Blueprint 是教训密集区（跨子项目契约 / ADR 触发 / 架构选型）
> 2. 内部 4 视角同源（同主对话宿主 · 同模型）· 易共有盲区
> 3. 实战中"默认 OFF + 记得 opt-in"漏开率高于"默认 ON + 漏关易发现"
> 4. 外部异质视角对架构层补盲价值与代码层一样高

### P0-153：Blueprint Stage external 默认 ON（spec only · 翻转设计取舍）

加 0 删 0 改账（仅翻转默认值 · 路径 B · L2 改造 · L1 红线零增量）：
- 🔄 [pmo-external-orchestration.md](../roles/pmo-external-orchestration.md) 四处更新：
  - § 二 默认推荐 第 42 行：Blueprint "默认不含 / 推荐启用" → "默认含 / 可 opt-out"
  - § 五 智能推荐表 第 101-103 行：中 Feature / 小 Feature / 敏捷需求 Blueprint OFF → ON 💡 · Bug 流程标 N/A（不走 Blueprint）
  - § 五 核心原则 第 106 行：Blueprint 默认 OFF → ON · 保留 P0-13 历史 rationale + 加 P0-153 翻转 rationale
  - § 十 硬规则默认值第 206 行：blueprint_enabled=false → true
- 🔄 [blueprint-stage.md](../stages/blueprint-stage.md) 六处更新：
  - § 本 Stage 职责 第 10 行：🟡 → 🟢 + "默认含"
  - § 可配置点表 第 20 行：external 行 "默认不启用" → "默认启用 / opt-out"
  - § 入口实例化 第 42 行：active_roles 推荐 qa/rd/architect/external 均默认 active
  - § Step 5 标题 + rationale 第 244, 254 行：🟡 → 🟢 + 翻转 rationale + 保留 P0-13 历史
  - § 硬规则 第 282 行：🟡 → 🟢 + "默认含"
  - § 执行 approach 第 362 行："默认 OFF" → "默认 ON"
- 🔄 [external-model-usage.md](../standards/external-model-usage.md) 第 76 行：`blueprint-reviewer.toml` "opt-in" → "opt-out"
- 🔄 [external-reviewer.md](../roles/external-reviewer.md) 第 55 行：Blueprint 列 "🟡 条件性" → "🟢 默认启用 · opt-out"
- 🧹 [pm.md](../roles/pm.md) 第 290 行（顺手清 P0-83 残留措辞）：External 角色 Goal-Plan 列从误导性"条件性 · 默认关闭 v7.3.10+P0-83"改为准确表述"❌ 不支持（P0-83 已删）· 仅 Blueprint + Review 走 external"

不动（边界严格 · 与 P0-152 同型路径 B）：
- L1 红线零增量（SKILL.md 9 条不动）
- Review Stage external 默认 ON 不变（本来就是 ON）
- BlueprintLite Stage 不动（敏捷需求不走 Blueprint Stage · 无 external 配置）
- Goal-Plan external 不动（P0-83 已删 · 不会复活）
- 工具层不动（dispatch / verify / state.py）
- E1 同源约束硬规则不动（外部模型 ≠ 主对话宿主仍是必须）
- 用户 opt-out 路径不变（PMO 初步分析 Step 4 决策项呈现 · 用户回数字选 OFF）

**设计取舍翻转表**：

| 维度 | P0-13（OFF 时代）| P0-153（ON 时代）|
|-----|---------------|---------------|
| 默认值 | OFF | ON |
| 用户记得方向 | opt-in（漏开率高 · 难发现）| opt-out（漏关易发现 · 用户立即感受到耗时）|
| 4 内部视角评价 | "已覆盖质量下限" | "同源 · 易共有盲区" |
| Codex 边际价值评价 | 低（重在 Review）| 高（架构层教训密集）|
| Feature 流程实跑外部 review 比例 | 低 | 高 |
| 翻转触发场景 | - | 用户复审默认值设计 · 反思 P0-13 当初取舍 |

**测试**：spec 改动 · 无脚本逻辑变更 · 预期 172/172 PASS（regression）.

**实战 trigger 闭环 commit #9**：P0-145..152 → P0-153。用户复审 P0-152 cite chain → 发现 Blueprint 默认 OFF 是 P0-13 旧取舍 → 翻转默认。

**教训**：默认值是**设计取舍** · 不是技术 limit。当"用户记得 opt-in"成本高于"系统默认开"时 · 应翻转默认 · 让漏关比漏开更易发现。同型反思可应用到其他 opt-in 字段（如 ADR 抽取 3 问触发器 / external execution_hints 推荐）· 但当前不动 · 等实战触发再翻。

---

## v7.3.10 + P0-152（权威源单源规则跨角色汇总指针 · 路径 B 抽 L2 meta-rule）

> **触发**：用户复审 P0-151 case · 指出"AI 还是习惯找历史"是反复出现的反模式 · 问"在哪里加合理"。复盘发现 P0-151（Designer · panorama 唯一基线）与 P0-7（PMO · templates 唯一格式源）**同型 meta-pattern**：每个角色都有"权威源 vs peer Feature 内容参考"边界 · 各自散落 L2 · 没有汇总指针 → 后续 Architect / RD / QA 触发时需重新论证 + 反模式黑名单分散。
>
> **诊断**：spec 现状已有 2 处证据（PMO + Designer）· 满足"meta-pattern 已显形"门槛 · 但未满足 SKILL.md § 红线生命周期管理路径 C 的"影响所有角色 + 所有 stage"硬条件 · **走路径 B**（L2 汇总指针 · L1 红线零增量）·  抽 [standards/common.md § 四C 权威源单源规则](../standards/common.md)。

### P0-152：四C 权威源单源规则（spec only · A 范围 · 不改各 role L2 原文）

加 1 删 0 账（仅加汇总指针 · 路径 B 减半版）：
- ➕ [standards/common.md § 四C 权威源单源规则](../standards/common.md) 新增节（~22 行）：
  - 核心原则：每个产物维度有唯一权威源 · peer Feature 仅作内容参考
  - 优先级声明：teamwork 规范权威源 > peer Feature 历史（明文强调 · 治本"AI 还是习惯找历史"心智路径）
  - 已注册维度表 2 行（PMO 格式 / Designer 框架）· 各列出 L2 sub-spec + 实证 case
  - 新维度注册要求 4 步（Architect / RD / QA 触发时复用 · 不重复论证 meta）
- 🔗 [roles/pmo.md § 格式权威守门](../roles/pmo.md) 第 19 行末尾加跨角色汇总指针 cite（不动原文 5 行）
- 🔗 [roles/designer.md § 6 维自查 § 第 6 维](../roles/designer.md) 第 167 行加跨角色汇总指针 cite（不动原文细节）
- 🔗 [stages/ui-design-stage.md § 框架基线唯一性](../stages/ui-design-stage.md) 第 243 行下游消费者段后加跨角色汇总指针段

不动（边界严格 · 路径 B 减半）：
- L1 红线零增量（SKILL.md § 9 条红线不动 · 红线生命周期管理路径 C 当前角色覆盖只 2/5 · 不够格升 L1）
- 各角色原 L2 sub-spec 原文不动（pmo.md § 14-19 / designer.md § 6 维 / ui-design-stage.md § 框架基线唯一性 都保留）
- 工具层不动（diff-html-vs-panorama.py / verify-panorama.py / state.py 都不改）

**设计理由（路径 B 减半 vs 路径 C 升 L1 红线）**：

| 路径 | 现状满足度 | L1 膨胀风险 | 后续可扩展性 |
|-----|----------|------------|------------|
| B 减半（本 patch）| ✅ 2/5 角色已实证 · meta-pattern 显形 | ✅ 零增量 | ✅ Architect/RD/QA 触发时按四C 模板加行 · 无需重新论证 meta |
| C 升 L1 R10 | ❌ 只 2 角色触发 · 不满足"所有角色 + 所有 stage" | ❌ R10 增量 · 红线再膨胀 | ⚠️ 升 L1 后退役难 |

**测试**：spec 改动 · 无脚本逻辑变更 · 预期 172/172 PASS（regression）.

**实战 trigger 闭环 commit #8**：P0-145..151 → P0-152。用户复审 P0-151 → 发现 P0-7 同型规则 → 抽汇总指针 → 避免 Architect/RD/QA 触发时重复论证。

**教训**：P0 patch 不只看"当前 case 是否解决"· 还要看"同型 pattern 在其他角色是否已显形"· 显形即可抽 L2 汇总指针 · 不必等所有角色都触发才升 L1。R-SP-8 视角："对齐 panorama"（Designer）+"对齐 templates"（PMO）都是 writer-only 同型 · 都需要明文禁令配套 · 汇总指针 = 共享禁令模板 · 后续角色一次性继承.

---

## v7.3.10 + P0-151（Designer 框架基线唯一性规则 · 治本"AI 还是习惯找历史"）

> **触发**：实战 case · PTR-F032-Billing-Payment-闭环 · Designer 输出 HTML 框架不全（缺 Sidebar / TopBar）· 用户发现 → AI 自承"找了 F030 历史 Feature 当参考"· 用户对抗"**不要看 F030, 以 teamwork 规范为准**"+ "**AI 还是习惯找历史**"。
>
> **诊断**：spec 现有规则"对齐全景"（P0-123 + P0-147 物化）说了正确路径 · 但**没明文禁止**"先看历史 Feature"路径。AI 在心智模型里"参考最近相似 Feature"是合理选项 → 选最短路径 → 错。
>
> 这是 R-SP-8 同型反模式："对齐 panorama"是 writer-only · 没说"不许走捷径"。需要明文加禁令。

### P0-151：框架基线唯一性规则（spec only · A 范围）

加 1 删 1 账（仅加规则 · 路径 B）：
- ➕ [stages/ui-design-stage.md § 过程硬规则](../stages/ui-design-stage.md) 加 🔴「框架基线唯一性」规则：
  - 反模式黑名单 3 条（复制历史 Feature HTML / "F030 框架就是这个"措辞 / "先看历史后看 panorama"顺序）
  - 推荐路径 3 步（Read panorama → 裁剪 Feature 页面 → 跑 diff 工具）
  - 下游消费者标注（R-SP-8 合规）：违反 → diff-html-vs-panorama.py 仍按 panorama 校验 · 历史 Feature 漂移会被列 extra tokens · 重做成本高
- ➕ [roles/designer.md § 3.5](../roles/designer.md) 自查清单从 5 维度升 **6 维度**，加第 6 维「框架基线唯一性」：
  - 自查问 + 正确答案 / 错误答案 · 答错必重做
- ➕ [templates/ui.md § 检查结果汇总](../templates/ui.md) 自查表加第 6 行「框架基线唯一性」· 含 framework_source cite 字段

工具不动（保留 P0-147 diff-html-vs-panorama.py 作 R-SP-8 兜底）：
- ✅ panorama 是 diff baseline · 历史 Feature 即使形似 · 仍会因自身漂移被 diff catch
- ⏸️ B 范围（`--check-files-read` 校验 Designer 没读其他 Feature）暂留 · 等 spec only 实战 1-2 个 case 验证有效再决定

不动（边界严格 · 路径 B 同型 P0-137~150）：
- L1 红线零增量
- diff-html-vs-panorama.py 不改（已是 R-SP-8 reader · 兜底依然有效）
- standards/external-model.md / Blueprint / Review 不动

测试：172 baseline = **172/172 PASS**（spec 改动 · 无脚本逻辑）

实战 trigger 闭环 commit #7：
- P0-145 → P0-146 → P0-147 → P0-148 → P0-149 → P0-150 → **P0-151**
- 用户对抗"不要看 F030 · 以 teamwork 规范为准" → 4.7 立即加明文禁令 + 反模式黑名单

教训：spec 写"必须做 X"不够 · 还要写"**禁止走 Y 替代路径**"——AI 的最短路径偏好会自动选 Y · 即使 X 是规范要求。R-SP-8 视角："对齐 panorama" 必须配 "禁止参考历史 Feature" · 否则后者会变成前者的隐性平替。

---

## v7.3.10 + P0-150（清理 Goal-Plan Stage external 评审残留 · 治本 P0-83 不完全清理）

> **触发**：实战 case · 4.6 instance 在 PRD 评审时正确识别不加 external（cite goal-plan-stage L43 "P0-83 删 external"）· 用户追问"为什么没加外部模型评审"· 4.7 实测 spec 验证发现 **P0-83 设计意图正确 · 但 goal-plan-stage.md 清理不完全** · 多处 external 描述与"已删"声明并存。
>
> **诊断**：
> - L43 / L181 / L254 / L356 / L496 / L631 明确说"P0-83 删 external"（6 处）
> - 但 L150 / L196 / L732 / L744-765 / L849 / L897-898 仍描述 external 评审行为（10+ 处）
> - **同文件内自相矛盾**：设计上删了 · 但产物 / 校验 / 条件 / Read 顺序段没删干净
>
> AI 跑流程时若 cite 残留段而非"P0-83 已删"段 → 会以为应该启动 external · 但实际不需要 · 浪费 token / 漂移流程。

### P0-150：goal-plan-stage.md external 残留清理

加 1 删 1 账（纯删 · 路径 B）：
- 🗑️ L150 入口 Read 顺序段：删 `[条件] templates/external-cross-review.md` 行
- 🗑️ L196 Tier 2 输出：删"external 评审 ADOPT/REJECT 摘要"
- 🗑️ L732 多视角独立性：删"external 评审：fresh shell 物理隔离..."段
- 🗑️ L744-746 Output Contract 表：删 PRD-REVIEW.md 条件描述 + pmo-internal-review.md 行 + external-cross-review/prd-{model}.md 行
- 🗑️ L750 external 条件说明（P0-38）
- 🗑️ L758-765 机器可校验条件 external 分段（保留 internal 校验 · 删 external 分段）
- 🗑️ L849 dispatch context 中 external 文件引用
- 🗑️ L897-898 产出文件 yellow 项（pmo-internal-review.md / external-cross-review/prd-{model}.md）
- ➕ 每处删除点加 P0-150 清理 marker + cite standards/external-model.md L14

不动：
- standards/external-model.md（已是单一权威 · 适用范围正确：Blueprint + Review）
- Blueprint Stage / Review Stage external 评审段（P0-83 没问题）
- L43/L181/L254/L356/L496/L631 现有"P0-83 删 external"声明（作为变更历史记录保留）

测试：172 baseline = **172/172 PASS**（spec 改动 · 无脚本逻辑变化）

实战 trigger 闭环 commit #6：
- P0-145 → P0-146 → P0-147 → P0-148 → P0-149 → **P0-150**
- 用户追问 "为什么没加 external" → 4.7 实测 spec → 发现 P0-83 残留 → 立即清理

教训：spec 设计变更（如 P0-83 "删除某段"）必须**同 patch 内**清理所有引用 · 否则残留产生 self-contradicting spec · 后续 AI 凭印象 cite 错段就会触发误判。

---

## v7.3.10 + P0-149（紧急修 P0-148 init-feature 参数 bug · 实战 PTR-F032 触发）

> **触发**：实战 case · PTR-F032-Billing-Payment-闭环 · Claude 4.6 instance 使用 P0-148 新加的 `state.py init-feature` · state.json 落错位置（worktree-root/`PTR-F032-Billing-Payment-闭环/state.json` 而非 `apps/partner/docs/features/PTR-F032-Billing-Payment-闭环/state.json`）· 4.6 自承"--artifact-root 传了相对路径但 CWD 已变化导致路径解析错误"· 手工 mv 修复。
>
> **诊断（直接修代码验证）**：P0-148 init-feature 的 `--feature` 和 `--artifact-root` **双参数语义重叠**：
> - `--feature` = state.json 落盘的物理路径（用 `Path(args.feature) / "state.json"`）
> - `--artifact-root` = state.json 中 artifact_root 字段值（默认取 --feature）
>
> AI 自然倾向把 `--feature` 当 "feature 名"传（slug）· `--artifact-root` 当 "完整路径"传 → state.json 物理落 CWD/slug/state.json（错） · artifact_root 字段记 apps/.../slug（对）· 物理位置与字段值分裂。
>
> 这是 P0-148 自己引入的回归 · 必须立即修。

### P0-149：删 --artifact-root 冗余参数 · --feature 单源

加 1 删 1 账（hotfix · 净删）：
- 🗑️ `state.py init-feature --artifact-root` 参数（删除 · argparse 直接 reject）
- ➕ `--feature` 升为单源：既是 state.json 落盘目录 · 又是 state.artifact_root 字段值（`str(args.feature)`）
- ➕ 启发式校验：`--feature` basename 不含 `--feature-id` → stderr WARNING（防 AI 误传仅 slug）
- 改 [stages/prepare-stage.md Step 14](../stages/prepare-stage.md)：调用示例明示 `--feature` 必须完整路径 · 含 `apps/{sub_project}/docs/features/{Feature 全名}` pattern
- ➕ test_state.py 加 3 regression cases：
  - `test_init_feature_uses_feature_as_single_source_for_path`（核心 regression）
  - `test_init_feature_rejects_old_artifact_root_arg`（argparse 应 reject）
  - `test_init_feature_warns_on_mismatched_basename`（启发式警告）

兼容性：
- P0-148 创建的 state.json **不受影响**（artifact_root 字段值在大多数情况下相同 · 即使 --feature 误传也仅物理位置错）
- 现有 24 个 state.py 子命令 + 9 个 P0-148 测试**不变**
- 新代码强 fail（argparse reject）替代 P0-148 silent 错位 · 错得早 + 错得明显

测试：169 baseline + 3 regression = **172/172 PASS**

实战 trigger 闭环（连续 5 个 case-driven patch）：
- P0-145: 4.6 诊断 worktree/state.json 时序 gap
- P0-146: 4.6 诊断 writer-only 规则模式
- P0-147: 用户反馈"Designer 不对齐"
- P0-148: 4.6 自承"我把 state.json 当 JSON 直接 Write"
- **P0-149 (本)**: P0-148 引入的回归 · 4.6 实战触发 · 立即修

不动（边界严格）：
- L1 红线零增量
- state.py checksum guard / recover 不动（P0-148 OK）
- templates/feature-state.json schema 不动

教训：新工具加参数时 · 参数语义必须**正交不重叠** · 否则 AI 跨参数误用必然发生。--feature 和 --artifact-root 应该早合并。

---

## v7.3.10 + P0-148（state.py init-feature + checksum guard · 物化拦截直写 state.json）

> **触发**：实战 case · ADMIN-F013 Feature · Claude 4.6 instance 自承：
> 1. "我把 state.json 当普通 JSON 文件直接 Write 了——图省事，跳过了工具层"
> 2. "Goal-Plan → UI Design 阶段流转也没有通过 state.py，直接口头宣布"
> 3. "把流程工具当文档看而不是当约束执行"
>
> **诊断（实测验证非凭印象）**：
> 1. prepare-stage.md Step 14 写"调用 state.py init-feature"——**但 state.py 实际没有这个子命令** · `--help` 输出无 init-feature 选项 · AI 合理 fallback 到 Write
> 2. state.json 无任何写权防护 · AI 用 Write/Edit 直改完全 honor system
> 3. R7(c) evidence-binding 红线 写了但没 reader · 跳了没 catch
>
> 这是 P0-146 R-SP-8 揭示的 writer-only 反模式 + 实际工具层缺位 的合击。

### P0-148：state.py 补 init-feature + checksum guard

加 1 删 1 账：
- ➕ `state.py init-feature` 子命令（~80 行）：
  - 参数：--feature / --feature-id / --flow-type / --sub-project / --merge-target / --branch / [--worktree-mode/-path] / [--auto-mode] / [--initial-stage] / [--force]
  - 创建 schema-correct state.json（含 worktree / environment_config / concerns / stage_contracts 完整结构）
  - 默认 initial_stage 按 flow_type 派生（Feature→goal_plan / Bug→dev / Micro→dev / 敏捷→blueprint_lite / Planning→planning / 排查→triage）
  - --force 时自动 backup `.bak.<ts>`（不丢历史）
- ➕ checksum guard（state.py 全文 ~40 行 helper）：
  - `_compute_checksum(state)` = sha256(canonical JSON without `_state_checksum`)
  - 所有写都 stamp `_state_checksum` 字段
  - 所有读 verify · 不一致 → exit 2 + recover 提示
  - 旁路：`TEAMWORK_BYPASS_CHECKSUM=1`（仅 debug / migration）
  - 向下兼容：旧 state.json 无 checksum → silent accept · 下次写补上
- ➕ `state.py recover --feature X --reason "..."` 子命令：
  - 旁路 verify 读 state.json
  - 追加 concerns WARN audit（含 reason）
  - 重新 stamp checksum
- 改 [stages/prepare-stage.md Step 14](../stages/prepare-stage.md)：明示必走 init-feature · 含完整调用示例 · 禁止手工 Write/Edit state.json
- ➕ test_state.py 加 3 个 TestCase（9 cases）：
  - TestInitFeature (4): happy / Bug default dev / 已存在 fail / --force backup
  - TestChecksumGuard (4): legitimate read / external 改动 blocked / bypass env / legacy 无 checksum 接受
  - TestRecover (1): 手工编辑 → recover → snapshot 通过 + concerns 留 audit

物化拦截链（end-to-end）：
```
AI 想创建 state.json
  → state.py init-feature 是唯一路径（无其他子命令能创建）
  → AI fallback Write/Edit
  → 下次任何 state.py 子命令 read → checksum mismatch → exit 2
  → AI 必须 recover --reason "..." 才能继续 → 留 audit
  → 用户事后可 grep concerns WARN 发现违规
```

不动（边界严格 · 路径 B）：
- L1 红线零增量（与 P0-137..147 同型）
- 现有 24 个 state.py 子命令逻辑不变（只加 2 个新命令 + checksum 透明集成）
- templates/feature-state.json schema 不变（init-feature 生成符合现有 schema）
- AC schema / 状态机 / evidence-binding 现有校验不动

测试：160 baseline + 9 init/checksum/recover = **169/169 PASS**

R-SP-8 进度：又一条 writer-only 规则（"必须用 state.py 维护"）加了真实 reader（checksum guard 在下次调用时 catch）· 这是**首个 cross-tool 物化拦截**（init-feature 创建 + 所有子命令 verify · 形成闭环）。

后续候选：
- P0-149: 设 PMO 实战跑 ADMIN-F013 完整流程 · 验证 checksum guard 实战触发 frequency
- P0-150: 红线减负专版 · 基于 checksum 物化 · 移除"必须用 state.py"相关红线（已被物化拦截）

实战 trigger 闭环：
- ADMIN-F013 case → 4.6 自承 + 用户对抗 → 4.7 实测 spec gap（init-feature 不存在）→ 补工具 + 物化拦截
- 与 P0-145/146/147 同型："实战 → 诊断 → 物化"模式 commit #4

---

## v7.3.10 + P0-147（Designer 全景对齐物化校验 · DOM diff 工具）

> **触发**：实战反馈 · "designer 在设计的时候还是和全景不对齐 · 尤其是页面框架等" · 用户每次都要肉眼对比 panorama overview.html vs feature preview/*.html。
>
> **诊断**：verify-panorama.py（v7.3.10+P0-132）只校验 markdown 自查段是否填写完整 · 不校验实际 HTML 视觉对齐。Designer 自查写"✅ 风格/配色/布局/语言一致"实际可能 HTML 框架完全不同。markdown 层无法 catch 视觉漂移——必须解析 HTML 结构。
>
> **R-SP-8 视角**：当前"全景对齐"规则是 writer-only · 跳了没人 catch。本 patch 加 reader = DOM diff 工具。

### P0-147：tools/diff-html-vs-panorama.py + Designer 自查双层物化

加 1 删 1 账：
- ➕ [tools/diff-html-vs-panorama.py](../tools/diff-html-vs-panorama.py)（~250 行 · 零依赖 · 用 stdlib html.parser）：
  - 解析 panorama overview.html + feature preview/*.html
  - 提取 4 维度 token：landmarks（nav/header/aside/main/footer/section）/ color classes（bg-/border-/text-/ring-/...）/ font sizes（text-xs..9xl）/ layout primitives（flex/grid/gap-/space-/p-/m-/w-/h-）
  - diff：feature 引入 panorama 不含的 token → WARN（漂移）· feature 缺 main 等 required landmark → FAIL
  - 支持单文件 --feature / 批量 --feature-dir 模式 · --strict 把 WARN 升 FAIL
  - JSON 输出 · stderr audit · R7 evidence-binding
- ➕ [tools/tests/test_diff_html_vs_panorama.py](../tools/tests/test_diff_html_vs_panorama.py)（10 case · 对齐/漂移/缺 landmark/批量/失败处理）
- 改 [roles/designer.md § 3.5 自查报告](../roles/designer.md)：物化拦截升级为双层（L1 verify-panorama · L2 diff-html-vs-panorama）· 第 1 维度"全景对齐"必跑 diff 工具
- 改 [stages/ui-design-stage.md § 过程硬规则](../stages/ui-design-stage.md)："对齐全景"规则加 P0-147 物化下游消费者标注（R-SP-8 合规示例）
- 改 [templates/ui.md § 全景对齐证据](../templates/ui.md)：自查段加"HTML 物化对齐校验"子段 · verdict + extra tokens 清单 + state.json 字段

工具特性：
- **零依赖**（stdlib html.parser）· 跨宿主一致（CC/Codex/Gemini）
- **DOM 结构 diff**（非像素对比）· 能 catch 框架/配色/字号/布局漂移 · 不能 catch 微小视觉差（4px vs 6px / hex 接近但不同）
- **panorama 是基准**：feature 应使用 panorama token 子集 · 引入新 token = 漂移信号

退出码契约（与 scripts-policy R-SP-5 一致）：
- 0 OK · feature 使用 panorama token 子集
- 1 WARN · feature 引入 panorama 不含的 token（漂移信号 · 需人确认是否合理）
- 2 FAIL · feature 缺 required landmark / HTML parse 失败 / 文件不存在

测试：150 baseline + 10 diff tool = **160/160 PASS**

实战 trigger 闭环：
- 用户反馈"页面框架不对齐"→ 物化 DOM diff 工具 → Designer 自查必跑 → 漂移自动 catch
- 与 P0-145 / P0-146 同型：实战 case → 4.6 诊断 / 用户反馈 → 4.7 物化 + 测试

不动（边界严格 · R-SP-8 路径 B）：
- L1 红线零增量
- verify-panorama.py 不动（v1 仍 markdown 校验 · diff-html-vs-panorama.py 是 L2 增量）
- 不引入 bs4 / playwright / Chromium 依赖（跨宿主 portability）
- 不做像素级 visual diff（留待未来 P2 patch · 用户 opt-in）

R-SP-8 进度：又给一条 writer-only 规则（"对齐全景"）加了具体下游消费者 · 235 → 234 missing（继续渐进）。

后续候选：
- 项目实战跑 1-2 个 Feature 验证 diff 工具准确度 / 假阳率
- 如 panorama overview.html 本身规范不齐 · 可能需要 P0-148 加 panorama 规范化要求

---

## v7.3.10 + P0-146（R-SP-8 writer-only 规则消费者标注 · 实战 4.6 自承洞察）

> **触发**：实战 case · API-F048-Ollama 代理网关 Feature · Claude 4.6 instance 自承"我跳的 spec 步骤都没有下游消费者标注"——只写"🔴 必须"但没说"跳了谁会发现 / 哪个下游会失败" · AI 内部评估为"只是仪式"而跳掉。
>
> 4.6 原话：「我跳"写了没人读"的步骤 · 不跳"下游有人依赖"的步骤」。**这是 framework-level 洞察**——比单纯加更多红线更治本。

### P0-146：R-SP-8 立账 + scanner 工具 + top 30 候选清单 + 修复 ~20 条

加 1 删 1 账：
- ➕ [standards/scripts-policy.md § R-SP-8](../standards/scripts-policy.md) · 每条 🔴/必须 规则必须含下游消费者标注 · 含 4 类有效消费者形式 + 渐进切换三阶段
- ➕ [tools/scan-spec-consumer.py](../tools/scan-spec-consumer.py)（~210 行 · 扫所有 spec markdown · 识别 writer-only 规则 · JSON / markdown 输出）
- ➕ [tools/tests/test_scan_spec_consumer.py](../tools/tests/test_scan_spec_consumer.py)（10 case · 触发模式 4 + 输出格式 3 + 错误处理 2 + 真实 spec 1）
- 修复 ~18 条 writer-only 规则（across 7 files）：
  - `CONTEXT-RECOVERY.md` 2 条（看板必附 💡 / PMO 必须分析优先级）
  - `FLOWS.md` 8 条（PMO Bug 判断 / Bug 流程合规确认 / 架构师 CR 必经 / 禁止自我豁免 / Micro 身份切换 4 条）
  - `RULES.md` 3 条（禁止"建议跳过"措辞 / 禁止把质疑当跳过 / 禁止"步骤简单"跳过理由）
  - `PRODUCT-OVERVIEW-INTEGRATION.md` 1 条（自下而上必须暂停）
  - `REVIEWS.md` 1 条（阻塞项必须修复）
  - `SKILL.md` 1 条（角色切换必须 cite）
  - `stages/review-stage.md` 2 条（角色规范必读且 cite / 三视角独立性）

实测扫描数据（before / after）：
```
Total 🔴/必须 rules: 411 → 418（+7 新规则被扫描器识别）
With consumer:      153 → 183（+30）
Missing consumer:   258 → 235（-23）
Ratio missing:      62.8% → 56.2%（-6.6 pp）
```

测试：140 baseline + 10 scanner = **150/150 PASS**

R-SP-8 渐进切换（当前位置）：
- **第一阶段（P0-146 · 当前）**：原则立账 · scanner 工具 · top 18 修复 · 总修复 ~7% missing
- 第二阶段（待定）：missing ratio 降到 ≤30% · 新 PR review 跑 scanner · 违规阻断
- 第三阶段（待定）：ratio ≤10% · CI 强制 scanner exit 0

不动（边界严格 · 路径 B）：
- 4.6 case 中的具体 4 项违规（state.json / PRD-REVIEW / 角色切换 / 评审独立）—— 角色切换 + 评审独立已修 · state.json / PRD-REVIEW 留 P0-147 续作（它们在 stages 文件多处出现 · 单独 patch 处理更清晰）
- L1 红线零增量
- 235 条剩余 writer-only 规则 → 渐进推进（每个后续 patch 修 20-30 条 · 12-15 patch 完成全量）

实战 trigger 闭环：
- API-F048 case 触发 → 4.6 自承诊断 → 4.7 验证 + 系统化 → spec 改进 + 物化扫描 + 渐进推进路线
- 与 P0-145 同型："实战 case → 4.6 诊断 → 4.7 实施 + scan tool" 是稳定模式

---

## v7.3.10 + P0-145（治本 worktree / state.json 时序 gap）

> **触发**：实战 case · ADMIN-F012-partners-active-adapters-column Feature 流程中 PMO 发现 state.json 落在主工作区 (staging 分支) · PRD.md 落在 worktree (feature 分支) · 两者分裂。手工 `cp / rm -rf` 修复后用户追问"是 spec 缺陷吗"。
>
> **诊断（实测 spec 验证 · 非凭印象）**：
> 1. prepare-stage.md Step 14 创建 state.json（位于主工作区 CWD）
> 2. goal-plan-stage.md 入口环境准备 Step 3 `git worktree add ... origin/{merge_target}`（clean checkout）
> 3. worktree clean checkout 不包含主工作区 untracked 的 state.json
> 4. `cd worktree` 后 PRD 落 worktree → state.json 与 PRD 分裂
>
> **根因**：spec 内部时序矛盾——state.json 创建早于 worktree 创建 · 必然孤立。属于 v7.3.10+P0-27 重构遗留 gap（环境准备从 plan-stage preflight 后置时漏了 state.json 创建依赖 worktree 的逻辑）。

### P0-145：worktree 创建提前到 prepare-stage Step 13.5

加 1 删 1 账（spec 改动 · 无新工具 / 无新文件）：

- ➕ [stages/prepare-stage.md](../stages/prepare-stage.md) 新增 Step 13.5 「环境准备执行」：
  - 在 Step 13 双对齐暂停（用户确认）之后 · Step 14 state.json 创建之前
  - 含原 goal-plan-stage 的环境准备序列（git fetch / worktree add / cd）
  - worktree_mode in [auto, manual] → 创建 worktree + cd
  - worktree=off / Feature Planning / 问题排查 → 跳过
  - 异常分支：base 不可达 / 分支冲突 / worktree add 失败 / stash 失败 → state.concerns + ⏸️ 暂停或降级
- 改 [stages/prepare-stage.md Step 14](../stages/prepare-stage.md)：明示 state.json 创建 CWD = worktree（如启用）· artifact_root 相对 CWD 解析 · 落在 worktree 内
- 改 [stages/goal-plan-stage.md 入口环境准备](../stages/goal-plan-stage.md)：
  - 从"创建 worktree"降级为"验证 worktree 已就绪"
  - 异常分支扩展：worktree 未就绪 / state.json 缺失 / state.json 与 worktree 分裂 → 降级补救（自动 fallback 到原 P0-27 创建逻辑 + state.concerns WARN）
  - 加新字段 `state.environment_config.stage_entry_verified_at`（与 `executed_at` 区分）

向下兼容（关键）：
- 老 Feature（v7.3.10+P0-145 之前创建 · state.json 在主工作区）走 Goal-Plan Stage 入口时自动触发降级补救 → state.json 迁移到 worktree + state.concerns 留痕
- 用户**不需要手动改 spec 历史** · 老 Feature 透明升级

不动（边界严格）：
- L1 红线零增量（与 P0-137..144 同型路径 B）
- state.py / init_triage.py 不动（state.py 本来就是 CWD-relative · 不依赖具体位置）
- templates/feature-state.json schema 不动
- L3 工具不动（无新工具）

测试：140/140 PASS（spec 改动 · 不影响脚本逻辑 · 现有 tests 不破坏）

实战 trigger 闭环：
- ADMIN-F012 case 触发 → 诊断 → 修 spec → 下一次 Feature 不会再分裂
- 老 Feature 走到 Goal-Plan 时自动迁移 → 无需手工 cp / rm -rf

---

## v7.3.10 + P0-144（feature context auto-fill · 降低 PMO 调用负担）

> **触发**：用户提问 "我们在调用 python 的时候通常会传入一些固定常用的参数 · 列如 feature 名字 / 目录 · 这些是否需要在每个 feature 启动的某个时机固定到一个 feature 目录下的 env · python 脚本自动读 · 降低 pmo 的负担"。
>
> **诊断**：state.json 已含 feature_id / flow_type / current_stage / worktree.{path,branch} / merge_target / external_cross_review.model 等 7+ 字段——render-* 工具完全可以 auto-fill · 不需要再造 .env。PMO 调用从传 9 个参数降到传 2 个。

### P0-144：R-SP-7 feature context auto-fill 立账 + 4 工具改造

加 1 删 1 账：
- ➕ [tools/_feature_context.py](../tools/_feature_context.py)（~145 行 · FeatureContext dataclass + load + merge_param）
- ➕ [tools/tests/test_feature_context.py](../tools/tests/test_feature_context.py)（15 case · 发现 3 + 优先级 1 + 部分字段 2 + merge_param 5）
- ➕ standards/scripts-policy.md § R-SP-7 feature context auto-fill 原则 + 当前阶段速查加 context 列
- 改 [tools/render-status-line.py](../tools/render-status-line.py) → v1.1（接 fc.load + merge_param · --flow/--stage 改可选 + 加 --feature-dir/--no-context）
- 改 [tools/render-decision-pause.py](../tools/render-decision-pause.py) → v1.1（加 --auto-refs/--feature-dir · 按 decision-class 自动 glob 期望 refs）
- 扩展 test_render_status_line.py 4 case（auto-fill via --feature-dir / via env / explicit override / --no-context）
- 扩展 test_render_decision_pause.py 3 case（auto-discover class 6 refs / no context fail / explicit + auto 合并）

调用对比（render-status-line）：
- Before：`--flow Feature --role PMO --stage dev --feature F042 --path /abs --branch f/F042 --merge-target main --worktree-path /abs/wt --next-step "..."`（9 参数）
- After：`export TEAMWORK_FEATURE=/abs/feature && --role PMO --next-step "..."`（2 参数 · 其余 7 自动）

发现优先级：explicit `--feature-dir` > $TEAMWORK_FEATURE > CWD walk-up（找含 'features/' 路径段 + state.json 的目录）> None。

参数合并：
- 显式参数永远优先 · audit JSON 记 `overrides_from_context: [field, ...]`
- 显式未传 → 用 context · audit JSON 记 `feature_context: {...}` + `discovery_source: explicit|env|walk_cwd`

边界（明示）：
- 不在 Feature 流程（问题排查 / Feature Planning）→ context 找不到 · 必须显式传
- state.json 损坏 → fall back 到显式参数
- `--no-context` 强制禁用（调试用）

不动（边界严格 · 与 P0-137..143 同型路径 B）：
- render-afk-skip.py / render-flow-transition.py 不需要 context（参数都是 per-call 或与 feature 无关）
- post-feature.py 暂不接入（独立 --project-dir / --feature-id 已够用 · 后续 patch 再统一）
- state.py 不动（它就是 state.json 的写工具 · 与读 context 不冲突）
- state.json schema 不动（已含必要字段）
- L1 红线零增量

测试：118 + 15 feature_context + 4 status-line autofill + 3 decision-pause auto-refs = **140/140 PASS**

R-SP-6 进度衔接：
- 4 个 A 档工具仍全部第二阶段
- R-SP-7 是 R-SP-6 的辅助层 · 降低"必须调"的门槛（调起来更省力）

---

## v7.3.10 + P0-143（render-* 工具集 P2+P3 · AFK skip + 流转校验 + 决策暂停）

> **触发**：P0-141/142 落地 render-status-line.py + STATUS-LINE.md 瘦身后，按"L2→L3 物化迁移专版"梳理推进 Top render-* 工具集。
>
> **治本**：本对话 case（AI 把 "auto 模式继续" 当用户投票 · 输出"视为通过"错措辞）+ P0-118-A case（编造 L行号 + 原文）+ HITL 决策点漂移 系列同型问题。
> 一次落地 3 个 render 工具 · 共享 ~50 行框架代码 · ROI 比分开做高。

### P0-143：render-* 工具集（P2+P3+P4 一并）

加 1 删 1 账：
- ➕ [tools/render-afk-skip.py](../tools/render-afk-skip.py)（~140 行 · AFK 11 暂停点 + HITL 21 项黑名单 · 命中 HITL 自动 reject）
- ➕ [tools/render-flow-transition.py](../tools/render-flow-transition.py)（~130 行 · 直接 read flow-transitions.md → 输出真实 L行号 + 原文 · 编造不可能）
- ➕ [tools/render-decision-pause.py](../tools/render-decision-pause.py)（~190 行 · 10 决策类 + refs 期望关键词校验 + options 编号校验 + 自动补「其他指示」末项）
- ➕ tools/tests/test_render_afk_skip.py（10 case · happy 3 + HITL 拒绝 3 + 未知 1 + validation 3）
- ➕ tools/tests/test_render_flow_transition.py（7 case · 真实 spec 2 + 合成 spec 5）
- ➕ tools/tests/test_render_decision_pause.py（9 case · PM 验收 2 + narrative 1 + validation 6）
- ➕ pmo-auto-mode.md / flow-transitions.md / STATUS-LINE.md 顶部加 render-first 推荐段（与 P0-141 STATUS-LINE.md 同模式）
- ➕ scripts-policy.md 当前阶段速查 + 已落地工具表 加 3 条目（render-afk-skip / render-flow-transition / render-decision-pause）

工具特性（与 render-status-line.py 同型 · scripts-policy R-SP-1..6）：
- 跨宿主 python3（CC/Codex/Gemini 同款调用）
- 参数即合规校验 · 非法即 exit 2 + stderr JSON 含 `cite` spec hint
- stderr 审计 JSON 含 tool_version / params / timestamp → R7 evidence binding
- enum 校验严格但容错（normalize 空格 / 大小写 / 双向 substring 匹配）

治本 case 反例（每个工具均直接堵漏）：
- render-afk-skip: AI 把 "PM 验收三选项" 用 auto skip → 工具 reject + cite HITL 清单
- render-flow-transition: AI 编造 "flow-transitions.md L999 '...'" → 工具直接 read 文件不可能编造
- render-decision-pause: AI 漏 📚 绝对路径 / 漏末项「其他指示」/ 用相对路径 → 工具校验阻断

测试：92 + 10 + 7 + 9 = **118/118 PASS**

不动（边界严格）：
- pmo-auto-mode.md AFK/HITL 清单**正文保留**（教育材料 + 工具的真值源）· 等后续 patch 触发再考虑瘦身
- STATUS-LINE.md 决策类清单 10 类正文**保留**（同上）· 与 P0-142 处理 A 类原则一致 · 不动 B 类
- flow-transitions.md 转移表正文**保留**（工具读它生成校验行 · 必须保留）
- L1 红线零增量（与 P0-137..142 同型路径 B）

R-SP-6 渐进切换（当前位置）：
- 第一阶段（P0-141）：spec 加 "推荐调"  ✅
- **第二阶段（P0-142/143 · 当前）**：spec 加 "必须调 · 漏调 WARN"  ⚡ 4 工具全部在此阶段
- 第三阶段（未来）：硬强制 · 配 verify-output-format.py 拒绝无 evidence binding 的 final response

---

## v7.3.10 + P0-142（STATUS-LINE.md 瘦身 · A 类规则降级为工具指针 · R-SP-6 升第二阶段）

> **触发**：P0-141 落地 render-status-line.py 后，用户提问 "STATUS-LINE.md 里面内容是否可以清理掉了，把状态逻辑写到 python 里"。
>
> **诊断**：STATUS-LINE.md 内容分三类
> - A 类（render-status-line.py 完全持有）：格式定义 / enum 映射 / 第二行第三行规则 → 应降级为指针
> - B 类（待后续 render-* 物化）：决策类暂停点 10 类清单 / 暂停点模板 → 暂保留
> - C 类（工具不能替代）：Preflight self-check / 反模式黑名单 / 流程示例 / 阶段对照表 → 必须保留
>
> 本 patch 严格限定 A 类清理 · 不动 B/C 类。

### P0-142：A 类规则降级 + R-SP-6 升第二阶段 + meta-test 防漂移

加 1 删 1 账（净删 · 路径 B）：
- 🗑️ STATUS-LINE.md A 类删除（约 127 行原文）：
  - L26-67 状态行格式规范完整定义（第一行/第二行/第三行）
  - L69-99 状态行规则（emoji 间距 / 路径绝对性 / 徽章规则）
  - L152-169 state.current_stage enum vs 阶段字段语义映射表
  - L377-399 第二行 / 第三行渲染规则
- ➕ STATUS-LINE.md 加指针（约 75 行新内容）：
  - render-first 工具用法示例 + 工具持有清单 + 输出契约
  - 🔴 R-SP-6 第二阶段强制段（"❌ 禁止手敲状态行 · 必须调工具 · 漏调 = WARN"）+ 实证 case 链
  - 工具未覆盖部分的教育规则（短版）
  - 第二行/第三行调用者职责（PMO 怎么准备参数）
- ➕ scripts-policy.md R-SP-6 加「当前阶段速查」表 + render-status-line.py 第二阶段标记
- ➕ tools/tests/test_render_status_line.py 加 4 个 meta-test：
  - STATUS-LINE.md 必含工具指针
  - STATUS-LINE.md 不含旧 enum 表标志（防回滚）
  - STATUS-LINE.md 不含旧格式定义块标志（防回滚）
  - scripts-policy.md 含「当前阶段速查」+ render-status-line.py 第二阶段

STATUS-LINE.md 实际变化：489 → 473 行（净减 16 行）· 但**质变** > 量变：
- A 类规则从"详细规范"降为"指针 + 工具职责说明"
- 工具持单源 · 改格式只动 .py + tests · spec 不动

不动（边界严格 · 与 P0-142 范围预先约定一致）：
- B 类 161-313 行（决策类清单 / 暂停点模板）→ 等后续 P0 落 `render-decision-pause.py` / `render-afk-skip.py` 时再迁
- C 类 Preflight self-check + 反模式黑名单 + 流程示例 + 阶段对照表 → 工具不能替代 · 永保留
- 不批量改其他文件 cite STATUS-LINE.md（cite 不破坏 · 仅本文件内容变）

R-SP-6 渐进切换（当前位置）：
- 第一阶段（P0-141）：spec 加 "推荐调"  ✅
- **第二阶段（P0-142 · 当前）**：spec 加 "必须调 · 漏调 WARN"  ⚡
- 第三阶段（未来）：硬强制 · 配 verify-output-format.py 拒绝无 evidence binding 的 final response

测试：88 + 4 meta = **92/92 PASS**

---

## v7.3.10 + P0-141（render-first 物化原则 + 状态行 render 工具 P1）

> **触发**：本轮对话 "L2 → L3 物化迁移专版" 梳理后，用户提出 "verify check 类是否可以更进一步 · 格式放代码里 · PMO 传参 · 工具回吐合规输出"。这是 verify-first → **render-first** 的范式反转：
> - verify-first：spec 教 AI 写格式 · AI 自行拼接 · 工具事后检测违反
> - render-first：工具持单源格式 · AI 传参语义 · 工具回吐合规输出 · 结构上不可漂移
>
> **诊断**：之前几乎所有同型 case（P0-118 状态行漂移 / 今轮 auto 模式 "视为通过" 错措辞 / P0-136 Micro 没 Ship）都涉及 AI 自创结构化输出。render-first 把"格式"从 spec 层（AI 不可靠）下沉到代码层（工具可靠）· AI 只负责语义参数。

### P0-141：scripts-policy R-SP-6 立账 + render-status-line.py P1 落地

加 1 删 1 账：
- ➕ [standards/scripts-policy.md § R-SP-6](../standards/scripts-policy.md)（新增 ~60 行 · render-first 优于 verify-first 原则 + A/B/C 三档适用判定 + 五条工具原则 + 与 verify-first 配合层）
- ➕ [tools/render-status-line.py](../tools/render-status-line.py)（~210 行 · 6 字段 + auto/ext 徽章 + 3 行格式 + 11 stage enum / 7 role / 6 flow 校验）
- ➕ [tools/tests/test_render_status_line.py](../tools/tests/test_render_status_line.py)（19 case · happy 5 + flow 变体 3 + validation 9 + emoji 间距 2）
- ➕ [STATUS-LINE.md](../STATUS-LINE.md) 顶部加 render-first 推荐段 + 工具用法示例（本文件降级为单源校验 + 手工 fallback 参考）

工具特性（与 scripts-policy.md R-SP-1..6 一致）：
- 跨宿主 python3（CC/Codex/Gemini 同款调用）
- 参数即合规校验：stage / role / flow / ext-model enum + 路径绝对性 + 流程必填字段（Feature/敏捷/Micro→功能 · Bug→Bug 号）
- 非法即 exit 2 + stderr JSON 含 `cite` spec hint（AI 知道去哪修）
- stderr 审计 JSON 含 tool_version / params / rendered_lines / timestamp → R7 evidence binding 入 state.json
- emoji 间距硬规则（📁 / 🌿 / 📍 + 半角空格）由工具保证 · AI 无法漏

工具不覆盖（明示边界）：
- ⚡ auto skip 日志 → 后续 P0 落地 `render-afk-skip.py`
- 📋 阶段流转校验行 → 后续 P0 落地 `render-flow-transition.py`
- 📚 决策参考块 → 后续 P0 落地 `render-decision-pause.py`
- 输出整体结构 verify 兜底 → 后续 P0 落地 `verify-output-format.py`（按 state.json evidence_binding 检查 AI 是否真调过 render-* 工具）

渐进切换（不强制 · 与 R-SP-6 五条原则一致）：
- 第一阶段（本 patch）：spec "推荐调 render-status-line.py" · AI 手敲仍可
- 第二阶段（后续）：spec "必须调" · 漏调审计 WARN
- 第三阶段（远期）：硬强制 · 配 verify-output-format.py 拒绝无 evidence binding 的 final response

测试：69 + 19 = **88/88 PASS**（含原 5 工具回归 + 新工具 19 case）

不动（边界严格）：
- STATUS-LINE.md 主体规范保留（工具按它校验 · 改 spec → 改工具 → 改 tests 三同步）
- L1 红线零增量（R-SP-6 落 L2 standards · 与 P0-137/138/139/140 同型路径 B）
- 不批量改其他 spec cite（仅 STATUS-LINE.md 顶部加推荐 · 后续 patch 触发再扩散）

---

## v7.3.10 + P0-140（UI.md 瘦身 · 视觉真相归 HTML · 意图追溯审计归 UI.md）

> **触发**：用户提问 "是否可以把 UI.md 去掉 · HTML 作为唯一设计真相"。审计发现 UI.md 内部职责混乱：
> 1. **视觉描述段**（布局 / 组件表 / 主色 / 字号 / 间距 / 响应式 / 状态设计 / 用户流程文字）—— 与 `preview/*.html` 重复 · drift 风险
> 2. **意图 / 追溯段**（panorama_path / 全景宿主 / UI-AC-COVERAGE）—— HTML 无法承载
> 3. **审计段**（Designer 自查 5 维度 + 全景对齐证据 + 变更记录）—— HTML 无法承载
>
> **诊断**：完全删 UI.md 会丢 2/3 类信息 · 不可行。正确做法是**单源化**——视觉归 HTML、意图追溯审计归 UI.md，职责互不重叠。

### P0-140：UI.md 职责单源化 · 删视觉重复段

加 1 删 1 账（净删 · 路径 B）：
- 🗑️ [templates/ui.md](../templates/ui.md) 删除视觉描述段：
  - 用户流程（文字描述 → HTML 真相）
  - 页面结构 / 布局 / 组件表 / 设计标注（主色/字号/间距）
  - 响应式断点表
  - 状态设计（加载/空/错误文字描述 → HTML 4 态文件真相）
- ➕ [templates/ui.md](../templates/ui.md) 加：
  - 顶部职责单源声明（视觉真相 = HTML / 意图追溯审计 = UI.md）
  - 「预览稿索引」表（替代旧的视觉描述 · 只索引不复述）
  - HTML 模板加 `data-ac="AC-XX"` 锚定示例
  - UI-AC-COVERAGE 表「对应页面 / HTML 区块」列（grep 友好）
- ➕ [stages/ui-design-stage.md](../stages/ui-design-stage.md) 第 2/3 子步骤 + Output Contract 表 明示职责边界：
  - UI.md = 意图 / 追溯 / 审计文档
  - preview/*.html = 视觉真相唯一载体

模板行数：107 → ~100（净 -7 · 但视觉段 ~25 行删除 · 净换成更明确的职责声明 + 索引表）

verify-panorama.py 影响评估：
- 现有依赖：`Designer 自查报告` header / `panorama_path` marker / `UI-AC-COVERAGE` marker / 5 维度 checklist / 全景宿主标注
- 全部在保留段——**零影响** · 9/9 PASS

测试：69/69 PASS（含 verify-panorama 9 case · 无回归）

不动（边界严格）：
- L1 红线零增量（与 P0-137/138/139 同型路径 B）
- 现有项目已写的 UI.md 不强制迁移——本 patch 只改模板 / spec · 历史 Feature 的 UI.md 保留
- 不删 UI.md 文件本身（仍是必出产物 · 只是内容瘦身）

---

## v7.3.10 + P0-139（Review Stage 修复循环上限 3 → 5）

> **触发**：用户明确要求 "Review Stage 三视角独立 CR 改为最多 5 轮"。
>
> **背景**：代码层 finding 修复粒度比文档层细（单元测试 / 边界 case / 第三方依赖真实性 / 并发安全多视角并发），实战中 3 轮经常不够 · 触顶后用户须做"强制通过 / 继续 / abort"决策的频次偏高。

### P0-139：Review Stage 专属覆盖通用默认

加 1 删 1 账（修改型 patch · 净增量 0 规则）：
- 修改 [stages/review-stage.md](../stages/review-stage.md) 5 处：L26 / L104（R3 budget 8→10）/ L198 / L240 / L252 · 全部 3 → 5
- 修改 [RULES.md L655](../RULES.md) · Review Stage NEEDS_FIX 上限 3 → 5
- 修改 [standards/review-verdict.md § 五 循环上限](../standards/review-verdict.md) · 通用默认仍 3 · **新增 Review Stage 例外段（5 轮 + 理由）** + 协作表区分 goal-plan/blueprint（≤3）vs review（≤5）
- 修改 [standards/prompt-cache.md L127](../standards/prompt-cache.md) · 内部评审豁免拆分：Blueprint 至多 3 · Review 至多 5
- 修改 [roles/pmo-state-mgmt.md L175](../roles/pmo-state-mgmt.md) · 内部评审豁免同上拆分

R3 prompt-cache budget 调整：
- 原：baseline 3 + 3 轮 × 1 = 6 · 上限 8（留 2 余量）
- 新：baseline 3 + 5 轮 × 1 = 8 · 上限 10（留 2 余量 · 等比例上调）

不动（边界严格）：
- Test Stage Verify-Fix 循环仍 ≤3（RULES.md L571/L587 · 用户未提）
- UI 还原验收循环仍 ≤3（RULES.md L926 · 用户未提）
- Goal-Plan PRD 评审 / Blueprint TC+TECH 评审仍 ≤3（仅 Review Stage 例外）
- state.json `_review_round_max` 字段在 goal_plan_substeps_config 下 · 与 Review Stage 无关 · 不动

测试：69/69 PASS（spec 改动 · 不影响脚本逻辑）

---

## v7.3.10 + P0-138（FK 策略 · 默认避免 · 引入须给项目语境理由）

> **触发**：用户询问"开发规范是否有 FK 相关规范"。审计发现 teamwork 现状缺位：
> - [roles/architect-tech-review.md:117](../roles/architect-tech-review.md) 把 FK 当 schema 变更触发关键词，但策略本身没写
> - [roles/architect-tech-review.md:154](../roles/architect-tech-review.md) 提到"FK 策略例外"是孤儿引用 · 策略文档不存在
> - [standards/backend.md § 五 数据库迁移规范](../standards/backend.md) 完整覆盖 migration / Schema 影响分析 · 但全段未提 FK
> - [templates/tech.md Schema 影响分析](../templates/tech.md) 无 FK 决策栏
>
> **元规则反思**：spec 留触发器但不留策略 = 实战中架构师评审无标准可循 · 命中 P0-117 同型问题（spec 自我引用断裂）。

### P0-138：FK 策略立账 · 单源 + 出口校验 + 模板栏位

加 1 删 1 账：
- ➕ [standards/backend.md § 五 FK（外键）策略](../standards/backend.md)（新增 ~55 行 · 默认避免理由 + 引入硬要求 + 反模式黑名单 + 出口校验）
- ➕ [templates/tech.md Schema 影响分析](../templates/tech.md) 加「FK 决策」表（FK / CASCADE 触发必填）
- ➕ [roles/architect-tech-review.md 3.1 §1](../roles/architect-tech-review.md) schema 设计合理性 checklist 加 FK 决策项
- ➖ [roles/architect-tech-review.md:154](../roles/architect-tech-review.md) "FK 策略例外" 孤儿引用 → 改 cite backend.md § FK 策略（单源化）

策略核心（单源在 backend.md）：
- 🔴 **默认避免** DB-level FOREIGN KEY + ON DELETE/UPDATE CASCADE · 引用完整性走应用层
- 🔴 引入须满足 ✅ 4 个条件之一（强一致小规模 OLTP / 法务合规 / 内部管理后台 / KNOWLEDGE.md 覆盖默认）
- ❌ 反模式黑名单 5 条（ORM 自动生成 / 开发期方便 / 防脏数据 / 通用最佳实践 / 没写决策行）
- 🔴 触发关键词（FOREIGN KEY / REFERENCES / FK / CASCADE）→ 架构师 Tech Review 4 项出口校验
- 🟢 项目可在 KNOWLEDGE.md 推翻默认（金融 / 政企等强一致项目）

不动（路径 B · 不走路径 C）：
- L1 红线零增量（策略落 L2 standards · 与 P0-137 同型）
- L3 物化暂不加（FK 决策需人判断 · 工具难自动 catch · YAGNI · 等实证 case 再决定是否加 tools/scan-fk.py）
- 不动 [standards/common.md / standards/frontend.md](../standards/)（FK 是后端专属）

测试：69/69 PASS（规范层改动 · 不影响脚本逻辑）

---

## v7.3.10 + P0-137（scripts-policy 立账 · post-feature.sh → tools/post-feature.py 跨宿主物化）

> **触发**：实战 case · 用户报 ROADMAP.md 漂移（顶部统计 26 vs 实际 23 / 切片 Feature 完成但 ROADMAP 未反映 / BG-016 占位陈旧）· 暴露双层 gap：
> 1. **架构层**：`hooks/post-feature.sh` 是 bash hook · 只在 CC `hooks.json` 自动触发 · Codex/Gemini 永远不跑 · 跨宿主名实不符
> 2. **行为层**：原脚本只 `grep` 后 echo warn · 把"AI 自觉补"作为兜底 · 命中 P0-136 同型反模式（spec 加细的天花板）
>
> **二级反思**：teamwork L3 物化层已有 4 个 python 工具（state.py / init_triage.py / sync-drift.py / verify-panorama.py）· 但缺单源 policy 约束 · 新需求落地路径不清晰 · 容易再走回头路加 bash hook。

### P0-137：scripts-policy 立账 · post-feature 跨宿主物化

加 1 删 1 账：
- ➕ `standards/scripts-policy.md`（5 条规则 R-SP-1..5 · 业务脚本统一 python3 / spec 显式 cite / hook 仅薄壳 / JSON 输出 / 退出码契约）
- ➕ `tools/post-feature.py`（277 行 · KNOWLEDGE check + ROADMAP marker-aware 派生段渲染）
- ➕ `tools/tests/test_post_feature.py`（9 case · happy/idempotent/4 warn 路径/2 fail 路径/dry-run）
- ➖ `hooks/post-feature.sh`（退役 · 业务逻辑全迁 python）
- ➖ `hooks/hooks.json` description 移除 post-feature.sh 引用

行为升级（不是简单平迁）：
- 旧：grep + echo warn（被动 · check-only）
- 新：scan state.json + marker-aware render ROADMAP（主动 · derive-only · 派生值结构上不可漂移）
- ROADMAP 单源化：派生段（统计 + Feature 表）由工具自动渲染 · 语义段（切片关系 / 优先级 / 规划）marker 外人维护 · 永不漂移

ship-stage.md：Step 10 加 post-feature.py cite + exit 0/1/2 契约说明

不动（路径 B · 不走路径 C）：
- L1 红线不增（policy 落 L2 standards）
- 剩余 4 个 bash hook（session-restore / post-compact / post-stop / post-subagent）保留 · 因为它们是 CC SessionStart/PreCompact 等**宿主独有 lifecycle**薄壳 · 没有 python 等价物 · 后续 patch 评估能否进一步 python 化

测试：原 60 + 新 9 = **69/69 PASS**

红线层级（v7.3.10+P0-103）路径选择：
- 路径 B（次选 · 物化拦截类）✅ 本次走此路径
- 把 hook business logic 降级到 L2 + L3 工具层 · L1 SKILL.md 不动

---

## v7.3.10 + P0-136（SKILL.md 6 流程定义同步 Ship 链路 · 治本 spec 内部不一致）

> **触发**：实战 case · Micro 流程走完用户验收后 PMO 凭印象「Micro 设计就是没 Ship 阶段 · 砍掉所有 Stage（含 Ship）· 不需独立 MR」停在本地未 push · 用户被迫追问。
>
> **审计**：
> - FLOWS.md L729 / flow-transitions.md L276 / ship-stage.md L253 都明文写「Micro 走完整 Ship Stage」（v7.3.10+P0-74 落地）
> - **但 SKILL.md L732 6 流程定义里 Micro 链路停在「⏸️用户验收」· 没提 Ship**
> - PMO 默认 cite SKILL.md（入口权威）· 漏读 FLOWS.md 详细 → 按错误 spec 行动
> - 同型问题：Bug / 敏捷 也在 SKILL.md 里漏 Ship 链路 · 仅 Feature 隐含
>
> **二级 bug**：PMO 还编造了 spec 里没有的「Micro = 最轻量通道 · 砍所有 Stage 含 Ship」「不需独立 MR · 顺手攒 batch」叙事 · 命中 P0-120 反模式（过度自信表述）。

### P0-136：SKILL.md 6 流程定义同步
- Feature 链路明加 Ship Stage（commit + push + CLI 优先创 MR + ⏸️ 用户合 + 第二段）
- Bug 链路加缩简版 Ship（标题 `[Bug] {简述} (BUG-{id})` · cite ship-stage.md「Bug 流程缩简分支」）
- 敏捷需求链路明加 Ship Stage
- Micro 链路加缩简版 Ship（标题 `micro: {简述}` · cite ship-stage.md「Micro 流程缩简分支」· P0-74 实证）
- 加 🔴 红线提示句：**涉代码流程必走 Ship**（Feature/Bug/敏捷/Micro 4 个）· 反模式黑名单含「Micro 不需独立 MR」等过度自信叙事
- 问题排查 / Feature Planning 不出代码 · 明示无 Ship · 防 PMO 误加

未动：FLOWS.md / flow-transitions.md / ship-stage.md（已是正确权威源 · 本次只让 SKILL.md 同步）

测试：60/60 全 PASS（spec 改动 · 不影响脚本逻辑）

---

## v7.3.10 + P0-135（撤 P0-126 carve-out · init_triage.py 自动调 sync-drift.py）

> **触发**：用户提问「sync-drift.py 在升级时做的 · 那么什么时候检查升级」· 暴露 P0-134 链路 gap：init_triage.py 检测到 version-mismatch 后只输出 advisory hint · 没机制实际触发 sync-drift.py · 又是「PMO 自觉」反模式。
>
> **元规则反思**（呼应 P0-120）：P0-126 设的边界「init_triage 不动 CLAUDE.md/AGENTS.md（高敏感 · 留 prompt 层）」是当时多想一步就能避免的 gap。当时的真实情境是「没有 marker-aware 安全模式 · 唯一同步方式 = 全文 cp」· 才把 sync 列为「不能脚本化」。P0-134 加了 sync-drift.py 后 · 这条 carve-out 已失效 · 但出于惯性留着 · 导致 P0-134 → P0-135 才补上。

### P0-135：撤 carve-out · init_triage 内部 orchestrate sync-drift
- **init_triage.py 加 maybe_sync_drift()**（~80 行）：
  - host 映射 → target 文件（claude-code→CLAUDE.md / codex-cli→AGENTS.md / unknown→skipped）
  - 决策树：version_match / host=unknown / target 不存在 / 缺 marker / --no-sync → skipped；
    target 存在 + marker 存在 + version-mismatch → subprocess 调 sync-drift.py 升级
  - 失败 cascade：sync-drift exit ≠ 0 → advisory[ERROR] · init_triage verdict 仍 OK（让 PMO 决策）
  - 输出 sync_drift{action, target, from_version, to_version, error?, skipped_reason?} 字段
- **build_advisories() 升级**：version-mismatch advisory 按 sync 结果分支输出
  drift-synced (INFO) / drift-sync-failed (ERROR) / version-mismatch (WARN, sync skipped)
- **build_audit_line() 加 sync 信息**：
  `sync-drift=upgraded(v...→v...)` / `sync-drift=noop` / `sync-drift=ERROR(...)` / `sync-drift=skipped`
- **--no-sync flag**：逃生舱（debug / 测试用）
- **prepare-stage.md drift 段重写**：去 P0-126 carve-out · 描述新自动 orchestrate 流程
- **tests/test_init_triage.py 加 TestSyncDrift 6 测试**：version_match skipped /
  target 缺 skipped / marker 存在 → upgraded / --no-sync / unknown host /
  codex → AGENTS.md · 总测试 54 → 60 PASS · 6.0s

PMO 视角变化（ergonomics）：
- 旧：跑 init_triage → 看 advisory hint → 决策是否调 sync-drift → 再调
- 新：跑 init_triage → 自动 sync 完成 → audit_line 直接含 sync 结果 → 一步到位

物化哲学完整（P0-126 → P0-134 → P0-135 三阶段演进）：
- P0-126 误判：高敏感 = 不能脚本化（错 · 留缺口给 PMO 自觉）
- P0-134 部分治本：marker-aware 安全模式 + 手工调用
- P0-135 真治本：marker-aware + 自动 orchestrate · 不依赖 PMO 自觉

---

## v7.3.10 + P0-134（sync-drift.py marker-aware CLAUDE.md/AGENTS.md 同步引擎）

> **触发**：用户报告 init_triage.py 没生效 · CLAUDE.md/AGENTS.md 注入还是老内容。审计：(1) install.sh 完全不动这两个文件 · (2) 历史 INIT.md 时代手工注入 · 早废弃 · (3) init_triage.py 只检测 version-mismatch 不修改文件 · (4) 完全没有 canonical 注入模板。

### P0-134：marker-aware 物化同步
- **新增 templates/host-instruction-injection.md**（canonical 注入源 · 极简 1 section `teamwork-pointer`）：
  - cite SKILL.md · 不复述红线全文（避免 token 重复 · 历史 INIT.md 失败教训）
  - marker 格式 `<!-- TEAMWORK_BEGIN:section vX.X.X+P0-Y -->` ... `<!-- TEAMWORK_END:section -->`
- **新增 tools/sync-drift.py**（~200 行 · 纯 stdlib · 同 state.py / init_triage.py 范式）：
  - marker-aware：仅动 BEGIN/END 之间内容 · 用户外部编辑**永不动**
  - idempotent：同版本重跑 = noop · 不重复写
  - 版本敏感：marker 上 version 字段 · 比对决定升级
  - --init 首次注入 / --dry-run 看 diff / cite-friendly JSON 输出
- **install.sh** claude / codex 两段加 sync-drift.py 调用：
  - 自动 read SKILL.md frontmatter version 注入 --skill-version
  - 首次安装 = `--init` 创建 CLAUDE.md / AGENTS.md teamwork 段
  - 升级 teamwork 后重跑 install.sh = 自动 marker 替换 · 用户编辑保留
- **init_triage.py** version-mismatch advisory 升级 hint 指向 sync-drift.py
- **prepare-stage.md** drift sync 段从「prompt 层 + 用户确认」升级为「sync-drift.py 物化」

设计哲学修正：
- P0-126 时把 CLAUDE.md drift sync 列为「不能脚本化」（高敏感）· 是误判
- 真正的高敏感场景是「无差别 cp 全文覆盖用户编辑」
- 用 marker 圈定 teamwork 管理边界 · 脚本只动 marker 内 = 安全 + 物化兼得

测试：tools/tests/test_sync_drift.py · 7 测试覆盖 init / idempotent / 用户内容保留 /
dry-run / 缺 marker 拒插 · 总测试 47 → 54 PASS · 5.0s

---

## v7.3.10 + P0-133（SKILL.md R9 红线 · 新 session 必跑 init_triage.py + cite audit_line）

> **触发**：用户报告 init_triage.py 没生效 — CLAUDE.md/AGENTS.md 注入老内容 / TROUBLESHOOTING.md 没创建。审计：P0-126 写完脚本只改了 spec 描述「PMO 在 triage 入口跑」· **没有任何 hook / 强制路径触发**。同型 gap 与 P0-118-B verify-panorama 一样：写脚本不注入必经路径 = 物化拦截没落地。

### P0-133：observable cite 强制 + 单源单机制
- **新增 SKILL.md R9 红线**（8→9 条 · 头部计数同步）：
  - 新 session 首条 PMO 响应前必跑 init_triage.py + 在响应可见 cite stdout 的 audit_line
  - 同 session 后续不重跑（PMO 自判：上下文已含 init_triage 输出 = 已跑过）
  - compaction 后视为新 session 重跑
  - 反模式：不 cite audit_line / 凭印象推断「已存在不用跑」
- **init_triage.py 加 audit_line 字段**（一行 audit · ergonomics + verifiability）：
  - 格式 `📊 init_triage: verdict=OK · host=X · project_root=Y · advisories=[...] · 已创建=A,B · version-mismatch`
  - PMO 把这行直接 cite 到首条响应 · 用户可见 PMO 是否跑了
- **triage-stage.md 删「主动创建必存在」假设**：改为 cite SKILL.md R9 · 单源
- **不动**（按用户审定）：
  - state.json 不加 init_evidence（scope 不符 · state.json = per-Feature · init_triage = session/host bootstrap）
  - state.py 不加 validate gate（granularity 错位 · session-event 不该 per-call 校验）
  - hooks 不调脚本（跨宿主不一致 / 失败 silent / 结果不在推理回路）

### 设计哲学：物化拦截的「必要性边界」
- **per-stage 高频写动作**（state.json / gate / ship 状态机）→ 必须脚本物理 wrap · 静默错失代价大
- **session-event 一次性 bootstrap**（init_triage / Designer 自查报告输出）→ observable cite 即可 · 用户可见 = 用户监督

测试：tools/tests/test_init_triage.py 加 TestAuditLine 3 测试 · 总测试 44→47 · 全 PASS。

---

## v7.3.10 + P0-132（Designer 自查规范 + verify-panorama.py 物化校验 + ui.md 模板加段）

> **触发**：用户反馈 Designer 在做设计时不遵循全景 · 多次跨子项目漏检 / 状态覆盖不全 / sitemap 未同步。审计发现 3 个根因：(1) templates/ui.md 60 行 0 个全景相关段（模板缺什么 Designer 漏什么）· (2) 全景规则碎片在 designer.md / ui-design-stage.md 4 处 · (3) 无物理校验脚本（仅 prose 红线）。

### P0-132：Designer 自查 + verify-panorama.py 物化拦截
- **新增 standards/common.md § 四B Designer 自查规范**（~120 行 · 与 § 四 RD 自查同型）：
  - 5 维度清单：全景对齐 / 状态覆盖 / PRD AC 覆盖 / 全景增量同步 / 结构性变更红线
  - Designer 自查报告模板（含 5 维度汇总表 + 全景对齐证据 + 增量 diff + 结论）
- **改 templates/ui.md**：原 60 行→124 行 · 加固定 fill-in 段（全景宿主 / panorama_path 顶部标注 + UI-AC-COVERAGE 表 + Designer 自查报告 8 段）
- **新增 tools/verify-panorama.py**（~250 行 · 纯 stdlib · TEAMWORK_FEATURE env 兼容）：
  - 5 项物理校验：self-check 段完整 / 跨子项目宿主标注（治本 P0-123）/ panorama_path 有效 /
    sitemap.md mtime 晚于 Stage 开始（涉及变更时）/ preview HTML 数量
  - cite-friendly JSON 输出 · checks_passed + checks_failed + hint
- **改 designer.md § 3.5**：旧「验收标准覆盖声明」升格为 cite 自查规范 · 接入 verify-panorama
- **改 ui-design-stage.md Output Contract**：加 verify-panorama.py 出口前置 · 不通过 = 不进 ⏸️
- **新增 tools/tests/test_verify_panorama.py**：9 测试覆盖 5 维度 + env var · 总测试 35→44 PASS

物化拦截链与 RD 自查（prompt-layer）+ verify-ac.py（physical-layer）双层防御同型 ·
治根因 1（模板缺段）/ 根因 2（无脚本）/ 根因 3（规则碎片单源到 § 四B）。

---

## v7.3.10 + P0-131-A（rules/flow-transitions.md Feature 流程表瘦身 -23 行）

state.py FEATURE_FLOW 字典硬编码 Stage → Stage 转移图后 · 39 行 Feature 流转表
合并为 17 行 · 删 Goal-Plan 子步骤详述 + Ship Stage 第二段 Step 4-9 详述（已在
stages/ 单源）· 加 cite tools/state.py 作为运行时权威。

---

## v7.3.10 + P0-131（feature-state.json _note 瘦身 -2897 字符）

state.py / init_triage.py 物化拦截后 · 32 条 _xxx_note 削到 ≤80 字符 · 总占用
5320 → 2423 字符（-54%）· 35 测试 PASS。保留 _enum + _xxx_schema · 删 P0
演进叙事和「PMO 在 X Step 写入」程序性描述。

---

## v7.3.10 + P0-130（state.py --feature 支持 TEAMWORK_FEATURE env fallback）

ergonomics 验证：模拟 PMO 完整 Feature 流程 36 次脚本调用 · `--feature {artifact_root}`
重复 ~76 字符。新增 `_add_feature_arg()` helper · 缺 --feature 时回退环境变量 ·
14 处 add_argument 统一替换。其他 friction 点（三 gate 合并 / complete-stage
紧跟 satisfy-gate / stage 名默认）评估后不做 · 削弱物理拦截语义。

---

## v7.3.10 + P0-129（install.sh 部署 tools/ + pytest 回归套件 35 测试）

> **触发**：P0-125/126 落地 tools/state.py + tools/init_triage.py 后未及时校核 deployment · install.sh L46/L75 dir 列表无 `tools` → 用户安装后整套物化拦截链 file-not-found · 全部失效。同时所有验证停留在 inline bash smoke test · 改动无保护。

### P0-129：install.sh + 测试套件
- **改 install.sh**（claude / codex 两段同步）：
  - dir 列表加 `tools` · `templates tools docs` 顺序
  - 部署后自动 `chmod +x tools/*.py templates/*.py`
- **新增 tools/tests/**（pytest 兜底纯 stdlib unittest · 无需依赖）：
  - `test_state.py`：21 测试 · 覆盖 P1-P4 · 含 P0-124 治本拦截 + 状态机非法转移 + gate 顺序 + raw-write contract
  - `test_init_triage.py`：13 测试 · 覆盖 4 advisory topic + idempotent + skeleton 检测 + version cache + git root 解析 + invalid host enum
  - `test_*` 共 1 测试 micro-validate（git 真实命令验证）
- **运行**：`python3 -m unittest discover -s skills/teamwork/tools/tests` · 35/35 PASS · 4.7s

---

## v7.3.10 + P0-128（5 业务 stage 直接读写 state.json → cite tools/state.py + prepare-stage host 改 PMO 注入）

> **触发**：物化拦截链落地后（P0-125..127），仍有 5 业务 stage spec（goal-plan / blueprint / dev / review / test）描述 PMO 直接 read/write state.json。spec 与脚本接口不一致。

### P0-128：spec 接续物化拦截
- **prepare-stage Step 1**（host 探测）改为「PMO 自报 host + skill_root + skill_version 注入 init_triage.py」· 脚本不探测（PMO system prompt 已知）
- **prepare-stage Step 2**（版本缓存校验）物化到 init_triage.py · prompt 层只处理 advisories · CLAUDE.md / AGENTS.md drift 高敏感留 prompt 层
- **5 业务 stage** 入口 Read 顺序 Step 4 改 `tools/state.py snapshot --tier stage`
- **5 业务 stage** Done 判据出口写法改 `satisfy-gate` + `complete-stage`
- **5 业务 stage** R3 约束段后插入「state.py 调用约定」统一段（5 条要点）

---

## v7.3.10 + P0-127（退役 templates/state-patch.py · state.json 写工具单源 tools/state.py）

> **触发**：P0-125 写 tools/state.py 时疏漏 · 未发现 P0-52 templates/state-patch.py（349 行 · 通用 dotted-path patch）· 导致 spec 5 文件同时引用两个 state.json 写工具 · 内部矛盾。

### P0-127：单源决断
- **删 templates/state-patch.py**（git rm）· 理由：违反"声明式 / 禁暴露 dotted path"红线；不知 ship phase 状态机 / 不知 ship-cleanup hard gate；tools/state.py raw-write 已覆盖
- **同步 5 文件**：RULES.md § state.json 维护硬规则全段重写 · SKILL.md L76 红线层级化 + L316 工具层枚举 · TEMPLATES.md / pmo.md / pmo-state-mgmt.md cite 切换
- **物化覆盖度**：schema enum + 状态机转移合法性 + gate 顺序 + ship phase evidence 三件套（P0-124）+ evidence-binding（P0-101 / P0-119）+ artifact_root 写边界（P0-41）
- 净效果 -344 行 · 消除 spec 内部矛盾

---

## v7.3.10 + P0-126（tools/init_triage.py · triage 入口 bootstrap 物化）

> **触发**：审计 TROUBLESHOOTING.md 生成时机 · 暴露 5 个 bug：(1) 创建时机过窄（mode B only）vs 依赖路径（mode A 排查）矛盾 · (2) 空骨架检测标识符 `{TODO 由用户填写}` 在模板里**不存在** · grep 永不命中 · (3) silent 创建用户告知盲区 · (4) monorepo "项目根" 模糊 · (5) mode A query 路径自身不创建。

### P0-126：物化 bootstrap
- **新增 tools/init_triage.py**（312 行 · 纯 stdlib · Python 3.8+）
- **PMO 注入接口**（脚本不探测 · 治用户反馈"host detect 不可靠"）：
  - `--host {claude-code|codex-cli|gemini-cli|unknown}` · `--skill-root` · `--skill-version`
  - 脚本只做文件系统 + git 能确定的事
- **职责**：teamwork_space.md / .teamwork_localconfig.md / TROUBLESHOOTING.md / GLOSSARY.md probe + 幂等创建 + 空骨架检测（hardcoded marker = 模板真实存在的字符串）+ global_schema_docs find（P0-119 evidence）+ worktree probe + version 比对
- **输出 cite-friendly JSON**：`{host, project_root, project_files{}, advisories[]}` · 4 类 advisory（first-init / skeleton-created / empty-skeleton / version-mismatch / schema-docs-found）
- **集成 spec**：prepare-stage Step 3 4 块独立扫描 → 一段调脚本 · triage-stage 排查路由依赖 init_triage.py advisory · 删旧兜底 · templates/troubleshooting.md 修错占位符引用
- **bootstrap 例外**（与 R8 协同）：脚本"不存在 → 复制空骨架"不算业务写

---

## v7.3.10 + P0-125（tools/state.py · 物化 state.json schema/状态机/evidence-binding · 14 子命令）

> **触发**：用户提出"PMO 维护 state.json 易出错 · 写一个 Python 脚本负责更新和验证 · PMO 调脚本传入要更新的内容 · 脚本返回关注的内容 · 不关心读写"。本质是把"PMO 自觉"下沉到"物理拦截"。

### P0-125：state.json 物化拦截单源
- **新增 tools/state.py**（1263 行 · 纯 stdlib · Python 3.8+）· 14 语义化子命令：
  - **P1 只读**：snapshot / validate / raw-read（cite-only output · R3 自动满足）
  - **P2 流转**：enter-stage / satisfy-gate / complete-stage（legal_next_stages + gate 顺序 + 三 gate 全满足）
  - **P3 ship**：ship-sanitize / ship-push / ship-confirm-merged / ship-cleanup / ship-closed（**治本 P0-124**：cleanup 在 phase ≠ merged 时 BLOCKED · enum 提前拦 · 5 件套 evidence）
  - **P4 通用**：pm-decision / add-concern / bug-frontmatter（YAML frontmatter + ship 状态机镜像）/ micro-validate（git evidence）
  - **逃生舱**：raw-read / raw-write（必带 --reason · 自动 concerns WARN）
- **接口契约红线**（4 条）：声明式入参 / cite-only output / 原子 R/M/W / 逃生舱有代价
- **物化覆盖**：schema enum + 状态机转移合法性 + gate 顺序 + ship phase evidence 三件套（P0-124）+ evidence-binding（P0-101 / P0-119）+ artifact_root 写边界（P0-41）
- **集成 spec**：ship-stage.md 加「state.json 写操作入口」段 · Step 1/2/7-8/9/10/异常段 6 处插 📌 state.py 调用 · Bug/Micro 分支补 P4 命令 · pmo-pm-acceptance-ship.md 选 1/选 2 流程切到 pm-decision

---

## v7.3.10 + P0-124（ship-stage.md 极简化 + Step 9 cleanup hard gate · 越简单越好）

> **触发**：实战 case（SVC-CORE-B005）PMO 在 MR 未合并时 force-delete feature branch · 侥幸通过。
>
> **5 次方案演进**（实证 P0-120 元规则信号 2/3 价值）：
> - v1: 加 SHA 校验 step → 治标
> - v2: 改 `git branch -D` → `-d` 安全模式 → 半治本
> - v3: 加 merge gate hard gate（+state.json schema 字段）→ 治本机制
> - v4: 删冗余 + 加 hard gate → 治本结构
> - **v5: 删冗余 + 极简化 + 加 hard gate**（采纳「越简单越好」元原则）→ **真治本 · 全方位**
>
> 用户在 v3→v4→v5 每一步连续质疑 · 我每次都倾向加规则 / 加 schema · 被用户主动捕获过度设计倾向。

### P0-124：ship-stage.md 极简化 · Step 9 cleanup hard gate

- **改动文件**（3 个）：
  - **stages/ship-stage.md**：从 **1066 行减至 ~895 行**（-163 行）：
    - 删 Step 3 verbose block（变体 A/B 双模板 + ❌/✅ 错误正确示例 + 双 cite 段）→ 替换为 ~16 行紧凑统一模板
    - 删 完成报告模板（╔══╗ 框 + 5 段拆分 + 多级 ├── 表格）→ 替换为 ~6 行极简版
    - 删 执行报告模板（state.json + review-log 已有审计 · 不需要 markdown 重复）
    - 删 state.json.ship 字段表（cite templates/feature-state.json 单源 · 仅留示例 / 业务语义说明）
    - 加 **Step 9 cleanup 入口硬门禁**（核心）：destructive op 前必查 git branch -r --contains + state.ship.shipped + Step 4-5 evidence · 不通过 BLOCKER ⏸️
    - 加 Step 9 反模式黑名单（4 条 · 含「Phase 1+2 完成」在 MR 未合并时输出 / finalize commit push feature branch 当 Step 8 / 跳过 Step 3 ⏸️ / force-delete 未验证）
    - 改 `git branch -D` → `git branch -d`（让 git 自带保护层 + cleanup BLOCKER 兜底）
  - **SKILL.md** R7(a) 加「destructive op 验证扩展」（一句话 cite Step 9 hard gate · 路径 A 归并 · 不新增 L1 红线）
  - **SKILL.md frontmatter**：版本 P0-123 → P0-124
  - **docs/CHANGELOG.md**：本条目
- **5 方案演进对比**：
  | 维度 | v1 SHA step | v2 `-d` 安全 | v3 merge gate | v4 删冗余 | **v5（终版）**|
  |------|-----------|-----------|--------------|---------|--------|
  | ship-stage.md 行数 | +25 | +15 | +60 | -415 | **-163** |
  | 报告模板 | ╔══╗ 框保留 | 同 | 同 | 紧凑化 | **删 ╔══╗ / 删双变体 / 删执行报告** |
  | 状态行严格度 | 不动 | 不动 | 不动 | 不动 | **唯一保留严格** |
  | 治本程度 | 治标 | 半治本 | 治本机制 | 治本结构 | **治本机制 + 治本结构 + 简约哲学** |
- **核心机制**（Step 9 cleanup hard gate）：
  - 物理拦截 destructive op（不依赖 PMO 自觉）
  - git branch -r --contains 真实命中 + state.ship.shipped + Step 4-5 evidence 三层校验
  - 不通过 BLOCKER ⏸️（含状态行骨架 + 决策参考）
  - 反模式黑名单 4 条（实证 SVC-CORE-B005 case 暴露的具体反模式）
- **设计哲学**（应用本次「越简单越好」元原则）：
  - **状态行**：严格按 STATUS-LINE.md 格式（emoji / 路径 / 分支）
  - **决策类暂停点**：📚 决策参考 + 选项 + 状态行骨架
  - **其他主对话输出**：极简 · 关键信息一句话 · ":" 替代 "├──" · 删 ╔══╗ 装饰 · 删教学示例 · 不重复 state.json 内容
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：Step 9 hard gate ~40 行 + 反模式黑名单 4 条 + SKILL.md R7(a) 扩展 3 行
  - 净删：~200 行（verbose 报告模板 + 双变体 + ❌/✅ 示例 + 执行报告 + state.json 字段表）
  - **净 -163 行**（1066 → 895）· 强符合减负哲学
  - 验证标尺：未来再有 PMO 在 MR 未合并时 cleanup case → 检查 Step 9 hard gate 是否触发
- **未做**（P0-120 信号 2 节制 · 不过度设计）：
  - ❌ 抽出 standards/ship-cli.md（Step 2 CLI 实现细节迁出 · 留待 P0-125 follow-up）
  - ❌ Bug/Micro 缩简分支删「与 Feature 一致」赘述（留待 P0-125 follow-up）
  - ❌ state.json schema 加 cleanup_verification_evidence 字段（v3 提过 · 用户反馈不需要 · 即时校验即可）
- **核心收益**：
  - **物化拦截 destructive op**（不靠 PMO 自觉 · git + state.shipped + Step 4-5 evidence 三层校验）
  - **极简化主对话输出**（删 ╔══╗ / 双变体 / 教学示例 / 执行报告 / 字段表）
  - **状态行严格度独立**（其他输出极简 · 状态行不动 · 边界明确）
  - 实证 case 闭环：SVC-CORE-B005 force-delete 侥幸通过 → P0-124 物化拦截 + 反模式黑名单
- **5 次反思实证 P0-120 元规则**：
  - 信号 2「我在加规则」：v1→v3 我每次都加 · 用户每次质疑 · v4→v5 真减负
  - 信号 3「应该好了」：5 次方案 · 每次「应该好了」都被用户捕获到治标层面
  - 信号 1「我在改 prompt」：从 prompt 层（v1）退到机制层（v3）再退到结构层（v4/v5）
  - 这是 P0-120 元规则在实战中最完整的演示案例

---

## v7.3.10 + P0-123（UI Design 入口跨子项目全景探测 · 按需 + 阈值决策）

> **触发**：用户「designer 在做设计前是否要求对齐全景设计」+「可能存在全景设计在另外一个子项目的场景」+ 多轮精简反馈：
> - 反馈 1：prepare-stage 探测过重 · 很多项目没 UI · 应放 UI Design Stage 入口（按需启动）
> - 反馈 2：teamwork_space.md hosts_design 列 + state.json schema 字段都不需要 · 探测在 Stage 内部即时处理
> - 反馈 3：探测有把握时不打扰 · 仅探测后仍不确认才暂停
>
> 我的方案 3 次精简（应用 P0-120 信号 2「我在加规则」自检）：v1（prepare-stage 全探测）→ v2（ui-design 入口 + state schema + teamwork-space 列）→ v3（仅 ui-design 入口 · 即时计算 · 阈值决策）

### P0-123：UI Design Stage 入口实例化加全景路径探测 · 跨子项目防漏

- **改动文件**（3 个）：
  - **stages/ui-design-stage.md** 新增「Stage 入口实例化：全景路径探测」段（~80 行）：
    - Step 0.1 即时探测（find · 不依赖 prepare-stage · 不持久化）
    - Step 0.2 评分算法（5 维度 · hosting_subproject +50 / 关键词命中 +20 / preview 成熟度 +10 / 路径深度 +5 / hosts_design 标注 +30）
    - Step 0.3 决策树（≥60 分 silent · 0 候选 ⏸️ · 不确定 ⏸️）
    - Step 0.4 暂停点模板（4 选 1 · 含 P0-118-A 状态行骨架 + P0-115 决策参考）
    - Step 0.5 用户拍板处理 + Step 0.6 跨子项目标注
  - **stages/ui-design-stage.md** Process Step 1 修订：原 `design/sitemap.md` 相对路径 → `panorama_path/sitemap.md`（Step 0 确认的绝对路径）+ 跨子项目场景显式标注
  - **roles/designer.md** § 3.3 全景设计维护规则加跨子项目对齐契约（cite ui-design-stage Step 0 + UI.md 顶部标注 + 路径错误怀疑不静默 + 项目无全景的兜底标注）
  - **SKILL.md frontmatter**：版本 P0-121 → P0-123
  - **docs/CHANGELOG.md**：本条目
- **关键设计原则**（应用 P0-55 三层按需启动 + P0-120 信号 2 减负 + P0-48 加 1 删 1）：
  - 不在 prepare-stage 探测（无 UI 项目零开销）· 仅 UI Design Stage 真触发时跑
  - 不持久化 state.json（探测开销低 · 即时计算 · 不污染 schema）
  - 不加 teamwork-space.md 列（项目级元数据不污染）
  - silent 优先（高置信度直接用）· 真不确定才 ⏸️（评分 < 60 / 0 候选 / 跨子项目无依据）
- **决策树场景覆盖**：
  | 场景 | 行为 |
  |------|------|
  | 单项目 1 候选 design/sitemap.md | silent（高分） |
  | monorepo · web 子项目有全景 + 当前 Feature 在 web | silent（hosting=当前 +50） |
  | monorepo · web 子项目有全景 + 当前在 api · sitemap 含 api 相关页面 | silent（关键词 +20 跨子项目仍高分）|
  | monorepo · web/admin 两个 design + 评分接近 | ⏸️ 暂停（探测后仍不确定） |
  | 0 候选 | ⏸️ 暂停（推荐创建首版）|
- **加 1 删 1 论证**（P0-48 元规则 + P0-103 路径 A 归并）：
  - 净加：~80 行 ui-design-stage 入口实例化段 + ~10 行 designer.md 契约 = ~90 行
  - 净删/合并：本 patch 路径 A 归并到现有「Stage 入口实例化」机制（P0-38/P0-55 引入）· 不新建 standards/cross-project-discovery.md（避免泛化过度 · 等到第 3 个同类 case 触发泛化）
  - 实证 case：用户报告全景设计在另一个子项目（monorepo 跨子项目漏检 · 同 P0-119 schema 文档发现类似）
  - 验证标尺：未来再出现「Designer 在错的子项目找全景」→ 检查是否评分维度不足 / 阈值需调整
- **核心收益**：
  - Designer 跨子项目能找到全景设计（防漏检）
  - silent 优先 · 不打扰用户（高置信度直接用）
  - 真不确定才 ⏸️（PMO 给推荐 + 评分 + 候选清单 + 决策参考）
  - 探测开销最小（仅 UI Design Stage 触发 · 不持久化 · 不污染 schema）
- **3 次精简实证 P0-120 元规则**：
  - 信号 2「我在加规则」：每次精简我都倾向加 schema/列/规则 · 用户主动质疑帮我捕获
  - 方向 A（用户质疑流程）：用户 3 次反馈我应该接受 · 不顺着原方向硬推
  - 加 1 删 1：从 v1 到 v3 净减 ~40 行（120 → 80）+ 减少 2 个 schema 字段 + 减少 1 个表列

---

## v7.3.10 + P0-121（GLOSSARY.md 项目根独立术语表 + 项目根文档命名规则）

> **触发**：用户「teamwork 是否有统一的项目术语表规范，如果没有需要调整 teamwork_space.md 模版加上统一语言区块」+ 反思后明确「不考虑 KNOWLEDGE.md § Glossary 失去意义」。
>
> **设计转向**：
> - 用户原方案：在 teamwork_space.md 加术语表段
> - 我主动异议（P0-120 方向 B）：单独建 GLOSSARY.md 更合理（职责分离 / 业内通行 / 类比 TROUBLESHOOTING.md）
> - 后续讨论命名规则：是否加 TEAMWORK_ 前缀 → 我主动异议「不加」（用户内容主权 · 业内通行命名 · 已有 KNOWLEDGE.md 先例）

### P0-121：GLOSSARY.md 项目根独立术语表 + 项目根文档命名规则

- **改动文件**（7 个）：
  - **templates/glossary.md** ✨ 新建（~80 行 · 5 段空骨架：业务术语 / 实体关系 / 命名约定 / 别名歧义 / 缩写词典 + 顶部 teamwork 自动创建说明 + 维护约定）
  - **stages/prepare-stage.md** Step 3：加 GLOSSARY.md 主动创建段（与 P0-118-B TROUBLESHOOTING.md 同模式 · silent 复制空骨架）
  - **templates/knowledge.md** § Glossary：业务术语主权威迁出到 GLOSSARY.md · 本段保留作为子项目内部实现层术语补充 · 删除 Order/Invoice/Customer 业务示例 · 通用架构 8 词（Module/Interface/Seam 等）保留 + Relationships 段简化
  - **SKILL.md § 项目级文档信息架构**：加 GLOSSARY.md 行（路径 + 何时 read）
  - **SKILL.md § 5.1 项目根文档命名规则** ✨ 新增段：边界判定原则（teamwork 主权 → 加前缀 / 用户主权 → 不加前缀）+ 理由 + 新增文档判定流程
  - **roles/pm.md** L110：terminology-ambiguity finding 写入路径明确为「项目根 GLOSSARY.md」（替换原「加 Glossary」笼统表述）
  - **stages/blueprint-stage.md** + **stages/goal-plan-stage.md** 入口 Read 顺序：加 GLOSSARY.md（PM/RD/架构师起草前必读）
  - **SKILL.md frontmatter**：版本 P0-120 → P0-121
  - **docs/CHANGELOG.md**：本条目
- **核心机制**：
  - **业务术语主权威单源**：项目根 `GLOSSARY.md`（teamwork prepare-stage 自动创建空骨架 · 类比 TROUBLESHOOTING.md）
  - **分层职责清晰**：
    - GLOSSARY.md = 业务全局术语（跨子项目共享）+ 实体关系 + 命名约定 + 别名歧义 + 缩写
    - KNOWLEDGE.md § Glossary = 子项目内部实现层术语（Module/Interface/Seam 等通用架构词汇）+ 项目级 Gotcha/Convention/Architecture
    - 大多数项目 KNOWLEDGE.md § Glossary 不需要业务术语段（业务全局 → GLOSSARY.md）
  - **PM 评审 terminology-ambiguity 路径单一**：必须 ADOPT 写入 GLOSSARY.md（不再笼统「加 Glossary」）
  - **入口 Read 集成**：goal-plan / blueprint stage 入口 Read 顺序加 GLOSSARY.md（与 P0-23 prompt-cache 协同）
- **项目根文档命名规则**（SKILL.md § 5.1）：
  - teamwork 框架附属（`.teamwork_localconfig.md` / `teamwork_space.md`）→ 加前缀
  - 项目级通用文档（`KNOWLEDGE.md` / `TROUBLESHOOTING.md` / `GLOSSARY.md`）→ 不加前缀（业内通行 · 用户内容主权）
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：~80 行 templates/glossary.md + ~30 行集成 cite + ~25 行 SKILL.md 命名规则段 = ~135 行
  - 净删：knowledge.md § Glossary 业务术语段（Order/Invoice/Customer 示例）+ Relationships 业务示例段 = ~15 行
  - 实质是**单源迁移**：业务术语权威源从 KNOWLEDGE.md § Glossary 子段 → 独立 GLOSSARY.md（更显式 / 更可发现 / 业内通行）
  - 类比 P0-109 TROUBLESHOOTING.md（也是从 KNOWLEDGE.md 子段独立出来）· 同设计意图 · 同实施模式
- **核心收益**：
  - 业务术语有专属容器（项目根独立文档 · 类比 TROUBLESHOOTING.md / KNOWLEDGE.md 家族）
  - PM 评审 terminology-ambiguity 写入路径单一 · 不再笼统
  - 跨子项目场景术语单源（顶层 GLOSSARY.md · 防漂移）
  - 项目根文档命名规则成文 · 未来新增项目根文档有判定依据
- **应用 P0-120 元规则的实证**：
  - 方向 B（AI 主动异议）：用户原方案放 teamwork_space.md → 我主动说不同意见 → 用户接受
  - 信号 1（"我在改 prompt"）：用户问 TROUBLESHOOTING_ 前缀 → 我反向问是否真该加 → 用户接受我的 5 条理由
  - 这是 P0-120 元规则的实战验证案例

---

## v7.3.10 + P0-120（Opus 思维元规则嫁接 · AI 对话姿态双向 + 自检信号 4 类）

> **触发**：用户分享 7 条「Opus 思维元规则」+ 反馈「我们的初始化逻辑中有类似的，可以结合这些再补充」。
>
> **设计选择**：嫁接版（不新建 standards/thinking-rules.md · 避免引入并行体系）→ 把 Opus 元规则有用的部分嫁接到现有最相关段（RULES.md / rd.md / SKILL.md / pmo-auto-mode.md）。

### P0-120：Opus 思维元规则嫁接（4 处现有段扩展 · 不新建文件）

- **改动文件**（5 个）：
  - **RULES.md** L102「用户质疑流程时 AI 反应模式」段升级为「AI vs 用户对话姿态」段：原内容（方向 A 用户质疑反应）+ 新增方向 B（AI 主动异议方向 · 不顺着错方向走 / 不讨好执行 · 含 3 条响应规则 + 输出模板 + 反例 + 与方向 A 对偶关系 + 与红线关系）
  - **roles/rd.md** L31 Bug 修复段扩展：加「修 2 次失败停下做根因分析」+「禁连续 3 次改同文件同区域」（Opus 元规则 ❸）
  - **SKILL.md** R5(c) 反模式黑名单加：过度自信措辞（"完美解决了" / "应该已经修好了" / "这次肯定没问题"）+ 默默降级措辞（"这个不重要" / "后续再做" / "非关键可跳过"）+ 替换为「已实施 X · 已通过 Y 验证 / 未验证 · 请你确认」（Opus 元规则 ❻+❼）
  - **roles/pmo-auto-mode.md** § 十一新增：自检信号 4 类（"改 prompt" / "加规则" / "应该好了" / "模型做不到"）· 反模式 + 与现有元规则协同表（Opus 元规则 ❽）
  - **SKILL.md frontmatter**：版本 P0-119 → P0-120
  - **docs/CHANGELOG.md**：本条目
- **嫁接原则**（不新建概念体系）：
  - 不新建 standards/thinking-rules.md（避免引入并行规则体系 · 防 P0-103 红线膨胀）
  - 每条 Opus 元规则嫁接到现有最相关段（用户质疑 / Bug 修复 / 反模式黑名单 / auto 模式自检）
  - 单源化原则保持（每条只一处权威 · cite 链接到现有红线 / 元规则）
- **覆盖的 Opus 元规则**：
  - ❶ 主动异议 / 不讨好 → RULES.md 方向 B
  - ❸ 修 bug 打转停下根因分析 / 禁连续 3 次同区域 → rd.md L31
  - ❻ 禁过度自信措辞 → SKILL.md R5(c) 黑名单
  - ❼ 范围管理 / 不默默降级 → SKILL.md R5(c) 黑名单
  - ❽ 自检信号 4 类 → pmo-auto-mode.md § 十一
- **不做的部分**（明确决策）：
  - ❷ 写代码前根因 + 系统级 + 涉及模块 → 不做（Execution Plan 5 行已部分覆盖 · 通用化收益不明显）
  - ❹ 设计前系统本质类比 → 不做（架构师 Tech Review 维度 1 已覆盖类比维度 · 通用化收益小）
  - ❺ 穷举根因 → 不做（PRD 对抗性自查 + R7 实测输出 + triage 意图识别已覆盖）
  - 完整版 P0-120 新建文件 → 拒绝（在用户确认前我主动给出反对方向 · 用户接受嫁接版方案）
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：~80 行（4 处现有段扩展 + 新增 § 十一自检信号）
  - 净删/合并：本 patch 修复 4 类系统性偏差（讨好 / 修复打转 / 过度自信 / 自我合理化）· 属于结构性扩展（P0-48 例外）+「修 bug」类（实证 case 触发 · 不强制加 1 删 1）
  - 与 P0-103 红线生命周期一致：路径 A（归并到现有 RULES.md / R5(c) / pmo-auto-mode.md）· 不走路径 C（新增红线 / 新建文件）
  - 验证标尺：未来 AI 顺着错方向走 / 修复反复打转 / 用「应该好了」替代验证 / 自检信号触发但忽略 → 检查是否本嫁接段不够强 · 需升级 L3 物理拦截
- **核心收益**：
  - AI vs 用户对话姿态双向（不只防 AI 顺着用户跳流程 · 也防 AI 顺着用户错方向走）
  - Bug 修复打转的硬约束（修 2 次停下 + 3 次同区域禁忌）防止「症状层反复修」
  - 措辞黑名单覆盖过度自信 + 默默降级（与 P0-118-A 状态行黑名单同位置 · 物理拦截）
  - 自检信号 4 类提供「治标 vs 治本」的元层提醒（防 PMO 在 prompt 层 / 加规则层打转）

---

## v7.3.10 + P0-119（DB schema 变更独立评审维度 + 全局 schema 文档发现机制）

> **触发**：实战 case（SVC-PLATFORM-F034 Partner-Request-Journal）架构师 review 漏检 services/core/docs/architecture/database-schema.md（monorepo 嵌套子项目）· review-arch.md 误判为「无全局 schema 文档」· 降级为非阻塞 concern · 用户事后追问才发现 · 全局 schema 文档漂移延迟。
>
> **架构问题**：
> 1. schema 变更没专项评审维度 — 架构师 Review 是通用 CR · 易漏查
> 2. 全局 schema 文档发现没"必发现"机制 — 浅层 docs/ 检索 · monorepo 子项目嵌套漏检
> 3. schema 变更的"全局文档同步"没硬约束 — 允许降级为非阻塞 concern · Stage 仍能 done

### P0-119：DB schema 变更独立评审维度 + 全局 schema 文档发现 + 不可降级硬约束

- **改动文件**（7 个）：
  - **roles/architect-tech-review.md** § 3.1（新增 ~80 行）：DB schema 变更专项 checklist · Blueprint 阶段触发 · 7 维度评审（设计 / migration / index / 兼容 / 全局文档同步 / 隐私合规 / 容量性能）· 维度 5 不可降级
  - **roles/architect-cr.md** § 2.1（新增 ~60 行）：DB schema 变更 CR 专项 · Review 阶段触发 · 5 维度评审（一致性 / 全局文档已更新 / 全仓库 find 自检 / 生产一致性 / FK 策略合规）· 维度 2 不可降级
  - **stages/prepare-stage.md** Step 3：加全局 schema 文档发现段（全仓库 find `*database*schema*.md` / `*schema*registry*.md`）· 写 state.json.global_schema_docs[] · evidence-binding 协同 P0-101
  - **stages/blueprint-stage.md** 可配置点 + 入口实例化：加 schema_change_triggered 触发（grep TECH.md 关键词）· 命中启用架构师 Tech Review schema 专项
  - **stages/review-stage.md** 可配置点 + 入口实例化：加 schema_change_triggered 触发（git diff 命中 migration / DDL）· 命中启用架构师 CR schema 专项 + 全仓库 find 自检
  - **templates/feature-state.json** schema：加 global_schema_docs[] + global_schema_docs_evidence + schema_change_evidence 三个字段（与 P0-101 evidence-binding 协同）
  - **templates/dispatch.md** Dev 产物白名单：blueprint / dev / review 三 Stage 表行加 `state.global_schema_docs[]`（schema 变更触发时必读必改）+ schema 变更 PMO 自拒规则
  - **SKILL.md frontmatter**：版本 P0-118-B → P0-119
  - **docs/CHANGELOG.md**：本条目
- **核心机制变化**：
  - **schema 变更升格为独立评审维度**（不是普通代码改动 · 区分 Tech Review + CR 两个阶段）
  - **全局 schema 文档"必发现"机制**（prepare-stage Step 3 全仓库 find · 防 monorepo 嵌套漏检）
  - **不可降级硬约束**（全局 schema 文档同步未完成 → BLOCKER NEEDS_FIX · 不允许 PASS_WITH_CONCERNS 降级）
- **触发链**：
  - Blueprint 阶段：grep TECH.md 关键词（CREATE TABLE / migration / FK / 等）→ schema_change_evidence.detected_at_blueprint → 架构师 Tech Review § 3.1 启用
  - Review 阶段：git diff 命中 *.sql migration / src/migrations/ → schema_change_evidence.detected_at_review → 架构师 CR § 2.1 启用 + 全仓库 find 自检
  - Dev 阶段：state.global_schema_docs[] 自动注入 dispatch Input files（必读必改）
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：~250 行（架构师专项 checklist + state schema + dispatch 表行 + 触发触发器）
  - 净删/合并：本 patch 修复实战 case 暴露的系统性 gap（schema 变更被当成普通代码 · 全局文档漂移）· 属于 P0-48 例外的「修 bug」+ 「结构性扩展」类（不强制加 1 删 1）
  - 验证标尺：未来再出现 schema 变更后全局 schema 文档漂移 case → 检查是否 prepare-stage Step 3 find 漏路径 / 触发关键词不全 / 不可降级约束被绕过
- **核心收益**：
  - schema 变更被 framework 识别为特殊高影响改动（不是普通 CR 维度）
  - monorepo 嵌套子项目下全局 schema 文档不再漏检（穷举 find）
  - 全局 schema 文档同步被升格为不可降级 BLOCKER（与 P0-101 evidence-binding 协同 · 物理拦截）
  - dispatch 产物白名单自动注入 global_schema_docs[]（RD 必须 commit · 不允许 silent 漂移）

---

## v7.3.10 + P0-118-B（TROUBLESHOOTING.md 主动创建空骨架）

> **触发**：用户「troubleshot 文档会主动创建么」+「空模版需要主动创建，但是不填充内容，用户可以基于这个空文件补充，teamwork_space.md 也是 ai 创建的」。
>
> **设计转向**：原 P0-109 / P0-110 设计是「不存在 → 一句话提示用户创建」（懒提示模式）。用户反馈：排查文档是项目开发**强需求** · 类比 `teamwork_space.md` 应该 PMO 主动创建空骨架（不填内容 · 用户基于骨架补充）。

### P0-118-B：TROUBLESHOOTING.md 主动创建空骨架

- **改动文件**（5 个）：
  - **stages/prepare-stage.md** Step 3：项目空间加载段加 TROUBLESHOOTING.md 检测 + silent 复制 templates/troubleshooting.md 到项目根
  - **stages/triage-stage.md** mode A query 排查分支：「不存在 → 一句话提示创建」改为「模板原样未填 → 提示补充」（prepare-stage 已保证文件存在）+ 加空骨架检测规则（grep 占位符 / 模板原文标题）
  - **SKILL.md** L147-151 「TROUBLESHOOTING.md 设计要点」段：加「prepare-stage Step 3 主动创建空骨架」要点 + 调整「不存在时」表述为「用户首次排查时检测模板原样未填」
  - **standards/discussion-mode.md** L124：知识地图行同步表述
  - **templates/troubleshooting.md** 顶部：加注释说明本文是 teamwork 自动创建的空骨架 + 空骨架检测说明
  - **SKILL.md frontmatter**：版本 P0-118-A → P0-118-B
  - **docs/CHANGELOG.md**：本条目
- **核心机制变化**：
  - 项目级排查文档从「懒提示 · 用户手动创建」升格为「prepare-stage 主动创建空骨架 · 用户填内容」
  - 与 `teamwork_space.md` 创建模式完全对齐（PMO 主动创建空骨架 · 类比 product-overview/）
  - silent 复制 · 不打断当前流程 · 不输出 banner（与 P0-105 silent execution 一致）
- **空骨架 vs 已填内容判定**：
  - PMO read 后 grep 占位符 / 模板原文标题字符串
  - 命中 = 模板原样未填 → 用通用方法 + 提示用户补充
  - 未命中 = 用户已填 → silent read · 按文档执行
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：prepare-stage Step 3 ~10 行 + triage-stage 修订 ~10 行 + 多文件同步表述 ~6 行 + templates 顶部注释 ~5 行 = ~30 行
  - 净删/合并：本 patch 把懒提示模式升格为主动创建（不删旧内容 · 改既有逻辑）· 属于结构性扩展（P0-48 例外）
  - 验证标尺：未来排查类项目仍出现"找不到 TROUBLESHOOTING.md"case → 检查是否 prepare-stage Step 3 创建逻辑漏触发
- **核心收益**：
  - 排查文档可见度提升：项目首次 /teamwork 启动后即有空骨架文件 · 用户能直接看到 + 编辑
  - 与 teamwork_space.md / product-overview 创建 pattern 对齐 · 框架内一致性提升
  - 用户首次排查体验改善：teamwork 用通用方法 + 提示填空骨架 · 下次排查自动 read 已填内容

---

## v7.3.10 + P0-118-A（暂停点状态行骨架强制 + 流转校验行 ≠ 状态行硬约束）

> **触发**：用户对 P0-118 的反馈——「阶段流转校验行 ≠ 状态行」是核心区分；P0-118 cite-only 在长流程仍易被忽略；自动流转不需状态行（与 P0-105 silent execution 自洽），状态行专属暂停点终态。
>
> **架构精确化**：silent execution 与状态行边界明确——silent 限于自动流转中间过程 / 框架仪式 / Step 头；暂停点终态产出（状态行 + 决策参考）必出。

### P0-118-A：暂停点状态行骨架强制 · 流转校验行 ≠ 状态行硬约束

- **改动文件**（11 个）：
  - **rules/flow-transitions.md** 顶部新增「状态行触发规则」段：自动流转 vs 暂停流转 vs 条件流转 三态触发表 + 反模式 + silent execution 边界
  - **SKILL.md** R5(c) 修订（边界精确化）：限定到 ⏸️ 暂停点 + 加「流转校验行 ≠ 状态行」sub-clause + 反模式黑名单加「跳过状态行」
  - **STATUS-LINE.md** 反模式黑名单段加 ❌「跳过状态行」case + PTR-F001-BUG-013 子根因引用
  - **roles/pmo-pm-acceptance-ship.md** § 2.2 PM 验收：cite-only → cite + 骨架占位符
  - **stages/ship-stage.md** 4 处（变体 A / 变体 B / MR 异常 / worktree 清理）：cite-only → cite + 骨架占位符
  - **stages/goal-plan-stage.md** 子步骤 5 PRD 用户最终确认：cite-only → cite + 骨架占位符
  - **stages/prepare-stage.md** Step 13 双对齐暂停：cite-only → cite + 骨架占位符
  - **SKILL.md frontmatter**：版本 P0-118 → P0-118-A
  - **docs/CHANGELOG.md**：本条目
- **核心机制变化**：
  - **状态行触发边界明确**：⏸️ 暂停点必出 / 🚀 自动流转不出（与 P0-105 silent execution 一致）
  - **流转校验行 ≠ 状态行硬约束**：暂停点必须两者并存（rules/flow-transitions.md 顶部硬约束 + SKILL.md R5(c) sub-clause）
  - **接受打破 P0-115 cite-only 单源**：暂停点模板内嵌**最小骨架占位符**（字段名 + 阶段 enum）· 格式细节仍 cite STATUS-LINE.md（部分单源保留）
- **设计权衡（cite-only vs 内嵌骨架）**：
  - P0-115 cite-only：未来格式演进零分散 · 但实战在长流程被忽略（PMO 不主动 Read spec）
  - P0-118-A cite + 骨架：字段名 / 阶段 enum 内嵌（强制可见）+ 格式细节仍 cite（部分单源保留）
  - 接受少量字面值重复（7 处骨架 · 每处 ~5 行）换长流程强制可见
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：rules/flow-transitions.md 顶部 ~30 行 + SKILL.md R5(c) ~8 行扩展 + 7 处骨架 ~35 行 + STATUS-LINE.md 反模式 ~6 行 = ~80 行
  - 净删/合并：本 patch 修复 P0-118 留下的「校验行混淆」+ P0-115 留下的「cite-only 长流程被忽略」两类 bug · 属于 P0-48 例外的「修 bug」类（不强制加 1 删 1）
  - 验证标尺：未来再出现状态行漂移 / 校验行替代 status line case → 检查是否本 patch 不够强 · 需升级 L3 物理拦截（hooks 层 · 物理扫 final response）
- **核心收益**：
  - 状态行触发条件物化为流转表（PMO 阶段变更前必读 rules/flow-transitions.md · 顶部即见）
  - 暂停点状态行从 cite 升为骨架 + cite 双重保障（PMO 看见骨架字段名即可填空）
  - silent execution 与状态行边界明确：silent 限于过程 · 暂停点状态行属终态 · 必出
  - 反模式黑名单覆盖两类典型漂移：摘要风格 + 跳过状态行

---

## v7.3.10 + P0-118（状态行升格 R5 红线 · 反模式黑名单）

> **触发**：实战 case（PTR-F001-BUG-013 Bug Ship Phase 1 暂停点）PMO 输出「当前状态：Teamwork / Bug / Ship 等待合并（暂停）」摘要风格 · 缺 📁 + 🌿 + 📚 决策参考 · 严重违反状态行格式。
>
> **架构问题**：P0-115 在 spec 文件加 cite-only 渲染契约 · 但 cite 是被动指针 · PMO 不主动 Read spec 时无后备 · STATUS-LINE.md Final Response Preflight 也没触发（Preflight 在 STATUS-LINE.md 内 · PMO 也没 Read）。

### P0-118：状态行 + 决策参考升格 SKILL.md R5(c) 红线

- **改动文件**（3 个）：
  - **SKILL.md** R5 暂停协议加 (c) 子条：状态行强约束 + 决策参考强约束 + 反模式黑名单（v7.3.10+P0-103 合并 #5+#10 后 · 本次扩展为 (a)/(b)/(c) 三件套）
  - **STATUS-LINE.md** Final Response Preflight 段加新反模式：「当前状态：Teamwork / xxx」摘要风格 + PTR-F001-BUG-013 实战 case 引用 + 修复指针
  - **docs/CHANGELOG.md** 加本条目
- **核心机制变化**：
  - **L1 红线层（SKILL.md）**：状态行 + 决策参考从「文档提示」升格为「红线门禁」
  - **物化原理**：SKILL.md 启动必读 · 不依赖 PMO 主动 Read spec · 强制可见
  - **silent execution 边界明确**：P0-105 反模式 5 不豁免状态行（终态产出必输出）
- **反模式黑名单**（命中 = 流程偏离）：
  - ❌ `当前状态：Teamwork / xxx`（实证 PTR-F001-BUG-013）
  - ❌ `📍 Teamwork：xxx`（自定义字段）
  - ❌ `Teamwork: 流程已完成`（口语化）
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：SKILL.md R5(c) ~12 行 + STATUS-LINE.md 反模式段 ~8 行 = 20 行
  - 净删/合并：本 patch 修复 P0-115 留下的「spec 被忽略 gap」· 属于 P0-48 例外的「修 bug」类（不强制加 1 删 1）
  - 验证标尺：未来再出现摘要风格状态行漂移 → 检查是否 R5(c) 不够强 · 需升级到 L3 物理拦截（hooks 层）
- **核心收益**：
  - 状态行 + 决策参考从被动 cite 升格为主动红线（必读 · 必输出）
  - 反模式黑名单提供 PMO 自检字面值锚点（命中即重写）
  - silent execution 与状态行边界明确：silent 限于过程 · 状态行是终态 · 必输出
  - 设计哲学修正：P0-115 的 cite-only 设计在被忽略时无后备 → P0-118 加红线兜底

---

## v7.3.10 + P0-116（STATUS-LINE.md 瘦身 · 跨主题单源化）

> **触发**：用户审视 STATUS-LINE.md 681 行 · 超 P0-79 的 300 行 cap 一倍多。盘点发现文件混合 3+ 个非状态行主题（流程持续规则 / 用户意图识别 / 上下文恢复 / 各流程示例），与 SKILL.md / roles/pmo.md / CONTEXT-RECOVERY.md 三处重复。
>
> **架构问题**：v7.3.x 早期 STATUS-LINE.md 把"会话级 Skill 加载相关一切"都塞进来 · 状态行格式 + 用户意图识别 + 上下文恢复 = 单文件 · P0-79 的 300 行 cap 落地后未跟进瘦身 · 累积膨胀。

### P0-116：STATUS-LINE.md 瘦身 + 跨主题单源化

- **改动文件**（5 个）：
  - **STATUS-LINE.md**：681 → **464 行**（-217 行 / -32%）
    - 删 L1-35 流程持续规则段 → 迁 SKILL.md
    - 删 L540-635 用户回复处理 + 意图识别 + 补充信息恢复 + 正确响应模式 + 禁止角色直接响应 → 抽到 roles/pmo-user-input.md sub-file
    - 删 L639-657 上下文恢复 Compact 路径 → cite CONTEXT-RECOVERY.md（已有单源）
    - 压缩 L327-432 各流程状态行格式（6 段重复结构 ~110 行）→ 1 个差异表 + 1 个 Feature 完整示例 + 多子项目 / worktree=off 变体说明（~25 行）
  - **SKILL.md** L46：1 行「会话级持续模式」cite 扩展为完整段（激活/退出条件 + 状态行 cite）
  - **roles/pmo-user-input.md** ✨ 新建（89 行 · 4 段：意图识别表 / 补充信息恢复 / 正确响应模式 / 关联单源）
  - **docs/CHANGELOG.md**：本条目
- **跨主题单源映射**（v7.3.10+P0-116 后）：
  - 状态行 / Final Response Preflight / 决策点参考 / 暂停点模板渲染契约 / 阶段对照表 / 各流程差异表 → STATUS-LINE.md（**唯一权威**）
  - 流程持续规则（激活/退出）→ SKILL.md § 会话级持续模式
  - 用户意图识别 / 用户回复处理 / 补充信息恢复 / PMO 承接 → roles/pmo-user-input.md
  - 上下文恢复 / Compact 路径 → CONTEXT-RECOVERY.md
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：pmo-user-input.md 89 行 + SKILL.md 14 行 = 103 行
  - 净删：STATUS-LINE.md 217 行
  - **净 -114 行 · -50%+ 单源破除重复** · 强符合 P0-48 减负元规则
- **核心收益**：
  - STATUS-LINE.md 主题收敛为「状态行 + 决策点参考 + 暂停点渲染契约 + 阶段对照」四件套 · 不再杂糅
  - 跨主题单源（流程持续 / 用户承接 / 上下文恢复）各归各家 · 改一处不再三处同步
  - 各流程状态行从 6 段重复结构压缩为 1 张差异表 + 1 个完整示例（Feature）· 看一眼即懂
  - 文件物理大小向 P0-79 cap 推进（681 → 464 · 仍超但已合理）

---

## v7.3.10 + P0-115（暂停点模板渲染契约 · 单源反向 cite）

> **触发**：实战 case（PM 验收暂停点 verbatim 渲染时漏标准 3 行状态行 + 漏 📚 决策参考）暴露 spec 文件中的 ⏸️ verbatim 模板若不显式 cite STATUS-LINE.md · AI 严格按模板渲染时会绕过 Final Response Preflight 自检兜底。
>
> **架构问题**：状态行格式 / emoji 间隔（P0-62）/ 路径边界（P0-67）/ 决策参考清单（P0-75）= STATUS-LINE.md 单源；但 spec 文件中的 verbatim ⏸️ 模板（pmo-pm-acceptance-ship.md / ship-stage.md / goal-plan-stage.md / prepare-stage.md）末尾**没有反向 cite STATUS-LINE.md** · 模板止于「请选择：1/2/3/4」·  AI 渲染时丢失末尾必需块。

### P0-115：暂停点模板渲染契约（单源反向 cite）

- 改动文件（5 个）：
  - **STATUS-LINE.md**：新增 § 暂停点模板渲染契约（v7.3.10+P0-115 · 单源反向 cite · 含覆盖清单表）
  - **roles/pmo-pm-acceptance-ship.md** § 2.2：PM 验收暂停点模板末尾加 cite（决策类 · 阶段 enum = pm_acceptance）
  - **stages/ship-stage.md**：4 处 cite（变体 A / 变体 B / MR 异常处理 / worktree 清理）
  - **stages/goal-plan-stage.md** 子步骤 5：PRD 用户最终确认模板末尾加 cite（决策类 · 阶段 enum = goal_plan）
  - **stages/prepare-stage.md** Step 13：双对齐暂停加 cite（非决策类 · 阶段 enum = triage）
- 设计原则：
  - **不复述格式**：spec 文件只声明「这是哪类暂停点 + 阶段 enum」 · 反向 cite STATUS-LINE.md
  - **未来零修改自动跟随**：STATUS-LINE.md 改格式时（如新加 P0-XX emoji / 路径规则）· spec 文件不变
- **加 1 删 1 论证**（P0-48 元规则）：
  - 净加：5 个 cite 块 + STATUS-LINE.md 一段 ~50 行
  - 删/合并：本 patch 是修复一类**系统性 bug**（所有暂停点模板都缺反向 cite）· 属于 P0-48 例外的「修 bug」类（不计入加 1 删 1 强制）
  - 验证标尺：未来出现新的暂停点模板漏状态行 case · 检查是否本表（STATUS-LINE.md § 暂停点模板渲染契约 · 覆盖清单）漏列
- **核心收益**：
  - PM 验收 / Ship Phase 1/2 / PRD 最终确认 / 双对齐暂停 等关键暂停点不再漏状态行 / 漏决策参考
  - 所有 spec 暂停点模板单源 cite STATUS-LINE.md · 未来格式演进零分散
  - 新增 spec 暂停点模板时必须加 cite + 更新覆盖清单 · 防回潮

---

## v7.3.10 + P0-114（README 大同步 P0-100 → P0-113）

> v7.3.10+P0-114 README 同步收齐技术债。**触发**：用户「结合最新代码 · 重新整理下 readme」。从 P0-100 大同步以来累积 P0-101 ~ P0-113 共 13 个 patch · 涉及入口架构重构 / 红线归并 / codex 合规 / silent execution / evidence-binding 物理拦截层级 / Ship Phase 1 CLI-first 等重大体感变化。

### P0-114：README.md 同步到 v7.3.10+P0-113

- 触发：累积 13 个 patch（P0-101 ~ P0-113）后 README 仍停留在 P0-100 描述 · 跟实际架构脱钩 · 新用户视角不准确。
- 设计原则（同 P0-100）：
  - 重大体感变更必更（5 mode 入口架构 / 红线归并 / codex 合规 / TROUBLESHOOTING.md 等）
  - 内部重构 / sub-file 抽出 / 文档单源化类不更（如 P0-107 init 物理删除）
- 核心改动：
  - **P0-114-A. README.md 顶部版本号** P0-100 → **P0-113**
  - **P0-114-B. 「六种流程」段重写为「5 mode 入口分诊（v7.3.10+P0-106）」**：
    - A query / B execute / C resume / D status / E discuss 表 + 触发场景 + 行为 + 开销
    - mode B 内部 5 流程类型（Feature/Bug/Micro/敏捷需求/Feature Planning）
    - 「问题排查」流程类型已迁到 mode A query 接管说明（v7.3.10+P0-30）
    - Feature Planning 标注 v7.3.10+P0-108 精简（4 暂停 → 1 暂停）
    - silent execution 段加 +P0-105 / +P0-112（审计走 state.json）
  - **P0-114-C. 「绝对红线 15 条」段重写为「8 条 R1-R8（v7.3.10+P0-103 归并 + 层级化）」**：
    - R1-R8 一句话总结表
    - 三层级化（L1 / L2 / L3）+ 生命周期管理元规则
  - **P0-114-D. Ship Stage 段补 P0-113 trip-wire**：
    - CLI 优先策略 + trip-wire（破除 git push hint URL trap）
    - 状态机层（flow-transitions.md）+ 红线层（R8(c)）双层防御
  - **P0-114-E. 加新核心保证段**：
    - 项目排查工具集 TROUBLESHOOTING.md（v7.3.10+P0-109 / +P0-110）
    - Codex CLI 合规使用（v7.3.10+P0-104）
    - Evidence-binding 物理拦截（v7.3.10+P0-101 / +P0-112 层级修正）
  - **P0-114-F. 文档导航段更新**：
    - 删除 INIT.md（已 P0-107 物理删除）
    - 加 stages/triage-stage.md（5 mode 分诊）+ stages/prepare-stage.md（mode B 重型准备）
    - 加 standards/discussion-mode.md / evidence-binding.md / external-model-usage.md
    - 加 templates/troubleshooting.md
  - **P0-114-G. 版本历史段加 P0-101 ~ P0-113 里程碑**：
    - 入口架构终极重构（P0-106 ~ P0-110 · 6 patch 收官）：5 mode + prepare-stage + TROUBLESHOOTING + Feature Planning 精简 + init 物理删除 + 模板砍重
    - 设计哲学修正（P0-101 ~ P0-105 + P0-112 + P0-113）：evidence-binding + silent execution + 红线归并 + codex 合规 + 容量焦虑暂停 + Ship CLI 双层防御
- **核心收益**：
  - README 反映当前 v7.3.10+P0-113 真实状态 · 不再误导新用户/老用户回访
  - 入口架构（5 mode）在 README 主线一等公民呈现
  - 红线 R1-R8 + 层级化体系首次在 README 主线展示
  - codex 合规 / TROUBLESHOOTING.md / evidence-binding 等关键体感变化补齐
- **加 1 删 1 元规则核算**：
  - **加**：5 mode 分诊段（~10 行）+ R1-R8 红线表（~12 行）+ Ship Stage trip-wire 段（~4 行）+ 3 个新核心保证段（TROUBLESHOOTING / Codex 合规 / Evidence-binding · ~30 行）+ 文档导航 4 行新文件 + 版本历史 P0-101~113 里程碑（~20 行）+ CHANGELOG entry（~50 行）= ~130 行
  - **删 / 简化**：原「六种流程」段（~10 行）+ 原「轻型 vs 重型分流」段（~8 行）+ 原「红线 15 条」段（~3 行）+ 原 INIT.md 文档导航（~1 行）= ~22 行
  - **净加 ~108 行**（README 从 ~340 行扩到 ~450 行 · 反映累积 13 patch 的产品层结晶）
- 不动：
  - SKILL.md / 各 stage spec / 各 role spec 等内部文档（README 是入口 · 内部文档不重做）
  - README-EN.md（暂保留 · 同步留给后续单独 patch · 同 P0-100 处理）
- 影响面：1 个文件改动（README.md）+ CHANGELOG + version bump
- 后续验证：
  - 立即可验证：README.md 顶部版本号 = v7.3.10+P0-113
  - 立即可验证：README.md 含「5 mode 入口分诊」段 + R1-R8 红线表 + Ship trip-wire + 3 个新核心保证段
  - 立即可验证：grep "P0-100" README.md 仅命中版本历史里程碑段
- README-EN.md 同步：留给后续单独 patch（与 P0-100 处理一致）

## v7.3.10 + P0-113（Ship Phase 1 CLI-first 双层防御 · 破除 git push hint URL trap）

> v7.3.10+P0-113 修复 PMO 在 Bug Ship Phase 1 反复给 URL 兜底链接而非用 glab/gh CLI 创建的 case。**触发**：用户「你为什么总是给我 mr create 链接而不是给我 glab 创建好的链接 · teamwork 原则是优先使用 glab gh 创建 mr」。**根因**（PMO 自审 4 点）：① git push 输出的 hint URL 是 trap（最强诱因）② 状态机表「生成 MR URL」字面歧义 ③ 风险厌恶 drift ④ token-economy bias。

### P0-113：Ship Phase 1 CLI-first 双层防御（A 状态机字面 + B R8(c) trip-wire）

- 触发：用户实战 case · PMO 自审给出 A+B+E 三层防御推荐 · 用户反馈"60 行太重" · 简化为 A+B（18 行 · 双层够用）。
- 设计哲学：
  - A（语义层）改 flow-transitions.md 字面 · 每次 Ship 流转校验时引到 · "CLI 优先"显式
  - B（红线层）SKILL.md R8 加 (c) trip-wire · 默认全局加载 · 破除"git push hint URL = 产物"pattern bias
  - **不做 E**（prepare-stage Step 9 + state.json schema + Phase 1 Execution Plan 强制 step）：
    - state.ship_cli_capability 缓存不靠谱（remote 切换 / CLI 后装）
    - prepare Step 9 加 ship CLI 检测增加启动开销 · 大部分流程用不到
    - Phase 1 Execution Plan 强制 step 与 ship-stage.md §2.3 重复
- 核心改动：
  - **P0-113-A. `rules/flow-transitions.md`** 字面修订（3 处）：
    - L139 Ship Stage 第一段（Feature）：「生成 MR create URL」→「**CLI 优先创建 MR/PR**（command -v glab/gh → 实创建拿 mr_url；CLI 不可用才走 URL 兜底；🔴 git push 输出的 hint URL 是兜底备选 · 不是首选产物）」
    - L165 Ship Stage 第一段（Bug）：同样字面修订
    - L261 Micro Ship Stage 第一段：同样字面修订（PMO auto-commit + push feature + CLI 优先创建）
  - **P0-113-B. `SKILL.md` R8 加 (c)** Ship Phase 1 CLI-first 门禁：
    - R8 写操作硬门禁链从 (a)(b) 扩展到 (a)(b)(c)
    - 含 mr_creation_method evidence-binding 协同（"cli" / "url-fallback"）
    - **trip-wire 显式**："git push 输出的 `remote: To create a merge request for ..., visit: ...` hint URL 是 trap（GitLab/GitHub 自动回吐的兜底备选 · 不是首选产物）· 看到 hint URL **不构成跳过 CLI 检测的理由**"
    - cite stages/ship-stage.md §2.3
- **核心收益**：
  - **双层防御足够**：每次 Ship 流转校验（A）+ R8 红线（B）两道防线
  - **trip-wire 显式破除 pattern bias**：PMO 看到 push 输出 hint URL 时立即识别"这是 trap 不是产物"
  - **18 行 vs 60 行**：跟 E 三层防御方案相比 · 工程量 -70% · 防御力差异极小
- **加 1 删 1 元规则核算**：
  - **加**：flow-transitions.md 字面修订 3 处（每处 +3 行 · 共 +9 行）+ SKILL.md R8 加 (c) 子条（+5 行）+ CHANGELOG entry（+30 行）= ~44 行
  - **删**：无（纯增补 · 不改现有逻辑）
  - **净加 ~44 行**（其中 CHANGELOG 占 ~30 行 · 实际规范增补仅 ~14 行）
- 不动：
  - stages/ship-stage.md §2.3 详细规范（v7.3.10+P0-99 已存在 · 不重复）
  - templates/feature-state.json mr_url + mr_creation_method schema（v7.3.10+P0-99 已存在）
  - prepare-stage.md Step 9（不加 ship CLI 检测 · 避免不必要的启动开销）
  - 红线 R1-R8 总条数（仍 8 条 · R8 加 (c) 是同类 sub-rule · 走 P0-103 路径 A 归并）
- 影响面：2 个文件改动（rules/flow-transitions.md / SKILL.md）+ CHANGELOG + version bump
- 后续验证：
  - 立即可验证：rules/flow-transitions.md 含 "CLI 优先创建 MR/PR" 共 3 处（Feature / Bug / Micro Ship Phase 1）
  - 立即可验证：SKILL.md R8 含 (c) Ship Phase 1 CLI-first 门禁 + "trip-wire" + "git push hint URL 是 trap"
  - 实战验证：下次 Ship Phase 1 push 后 · PMO 看到 git push 输出的 hint URL 立即识别 trap · 走 command -v glab/gh → 实 CLI 创建 → 拿真 mr_url（不再给用户 URL 兜底链接让 ta 手点）

## v7.3.10 + P0-112（evidence-binding 物理拦截层级修正 · 主对话减重）

> v7.3.10+P0-112 修正 P0-101 设计过度。**触发**：用户反馈「必须贴 stdout 原文太重了 · 主窗口不要太复杂」。**根因**：P0-101 把 stdout 物理拦截层级**放在主对话**（要求 verbatim 贴）· 跟 v7.3.10+P0-105 silent execution（主对话只输出实际答案 / 决策点 / 异常）冲突。

### P0-112：evidence-binding 物理拦截层级修正

- 触发：P0-101 实战 case 后用户察觉「PMO external 探测时主对话被 verbatim stdout 输出污染」· 跟 silent execution 设计哲学冲突。
- 设计哲学修正：
  - **P0-101 错误层级**：stdout 物理拦截放主对话（要求 verbatim 贴）→ 主对话变重 · 与 silent execution 冲突
  - **P0-112 正确层级**：stdout 物理拦截放 state.json schema（必须含完整 stdout · 但不在主对话出现）
  - 拦截力**完全保留**：PMO 写 state.json stdout 字段时不能编造（用户/PM 抽查时一眼识破）
  - 主对话回归 silent execution 原则：仅输出精炼结论
- 核心改动：
  - **P0-112-A. `standards/evidence-binding.md`** 修改 stdout 落地位置：
    - 删除「完整 stdout 原文必须落两处（① 主对话 verbatim ② state.json）」
    - 改为「stdout 写 state.json detection_evidence（拦截层级）+ 主对话仅精炼结论」
    - 加 v7.3.10+P0-112 物理拦截层级修订说明 + ✅/❌ 实战示例对照
    - 出口校验告警措辞调整（"贴 stdout 原文" → "写入 state.json stdout 字段"）
  - **P0-112-B. SKILL.md R7(c)** 同步：
    - 加 v7.3.10+P0-112 物理拦截层级修正说明
    - 明示「物理拦截层级 = state.json schema 完整性（不在主对话）· 主对话只输出精炼结论」
    - cite R5(b) silent execution 协同
  - **P0-112-C. `stages/prepare-stage.md` Step 9** external 角色探测重写：
    - 删除「完整 stdout 原文必须落两处（含主对话 verbatim）」
    - 改为「state.json 写完整 evidence + 主对话精炼结论（"codex ✅ 可用 / claude ⏭️ 同源跳过 / gemini ❌ 未安装"）」
    - silent execution 协同标注
  - **P0-112-D. `roles/pmo-state-mgmt.md` § 2.4** 出口校验微调：
    - 校验逻辑不变（仍校验 state.json evidence schema 完整性）
    - 告警措辞调整（删除"贴 stdout 原文" · 改为"写入 state.json stdout 字段"）
- **核心收益**：
  - 主对话回归 silent execution 原则（与 P0-105 完全协同）
  - 物理拦截力完全保留（state.json schema 完整性 + 用户/PM 抽查能力）
  - 用户体验改善（external 探测不再被 verbatim stdout 污染）
- **拦截力论证**（关键）：
  - PMO 写 state.json stdout 字段时不能凭印象编造（编造的字符串与真实命令格式不符 · 用户/PM 抽查 state.json 时识破）
  - 真实跑 bash 拿 stdout 是物理动作 · 编造行为成本高于真跑
  - 主对话不需要承载 stdout 也能保证拦截（拦截发生在 state.json 写入时）
- **加 1 删 1 元规则核算**：
  - **加**：standards/evidence-binding.md 修订段（~25 行 · 物理拦截层级 + 实战示例对照）+ SKILL.md R7(c) 标注（~3 行）+ prepare-stage.md Step 9 重写（~10 行）+ pmo-state-mgmt.md 告警措辞（~2 行）+ CHANGELOG entry = ~80 行
  - **删 / 简化**：standards/evidence-binding.md「stdout 落两处」段（~5 行）+ prepare-stage.md「stdout 落两处」段（~5 行）+ pmo-state-mgmt.md「贴 stdout 原文」措辞（~2 行）= ~12 行
  - **净加 ~68 行**（修订 + 实战示例对照说明 · 但**主对话实际输出净减**·因为不再 verbatim 贴 stdout）
- 不动：
  - state.json detection_evidence schema（不变 · stdout 字段仍必填）
  - 出口校验逻辑（不变 · 仍校验 evidence 完整性）
  - 拦截力（仅层级移动 · 力度不变）
  - 红线 R7（不修改 R7 条文 · 仅 (c) 子条加层级修正标注）
- 影响面：4 个文件改动（evidence-binding.md / SKILL.md / prepare-stage.md / pmo-state-mgmt.md）+ CHANGELOG + version bump
- 后续验证：
  - 立即可验证：standards/evidence-binding.md 含「✅ 主对话精炼结论 / ❌ verbatim 贴 stdout」对照
  - 立即可验证：SKILL.md R7(c) 含「物理拦截层级 = state.json schema」
  - 立即可验证：prepare-stage.md Step 9 含「主对话只输出精炼结论」
  - 实战验证：下次 prepare-stage Step 9 探测 external · 主对话只看到「🌐 External 探测：codex ✅ / claude ⏭️ / gemini ❌」一行 · stdout 完整写到 state.json 不污染主对话

## v7.3.10 + P0-110（troubleshooting 模板砍重 367 → 50 行）

> v7.3.10+P0-110 用户反馈 P0-109 引入的 troubleshooting 模板太重（367 行 · 11 段 · 含大量 K8s/PostgreSQL/Redis/Sentry 假设的命令示例）· 简化为最小骨架。

### P0-110：troubleshooting 模板砍重 + 4 段化

- 触发：用户反馈「这个模版是否太重了，简单点」+ 「四、监控 / 部署去掉」
- 设计哲学：mattpocock-style 最小骨架 · teamwork 不假设技术栈 · 不规范具体命令
- 核心改动：
  - **`templates/troubleshooting.md` 从 367 行 → ~50 行**（净减 86%）
  - 11 段 → **4 段**：
    - 一、环境（写操作授权矩阵）
    - 二、查 log（占位符 · 不假设 K8s）
    - 三、查数据 / 缓存（按需 · 占位符 · 不假设 PostgreSQL/Redis）
    - 四、常见报错（按项目实际填 3-5 条）
  - **删除段**：
    - 监控 / 链路追踪（用户决定不属于排查工具集核心）
    - 部署 / 回滚（同上）
    - 5 类报错思路链详细展开（K8s 502 / DB 超时 / Redis 未命中 / 队列堆积 / 第三方 API · 假设过强）
    - schema 速查段（已在 ARCHITECTURE.md / database-schema.md）
    - 模板使用提示段（顶部说明已够 · 不需独立段）
    - 与其他文档关系段（顶部 KNOWLEDGE 互补说明已够）
  - **保留段**：
    - 安全约束（与红线 R8 协同 · 不可删）
    - 维护（季度命令验证 + 新增环境同步）
  - **SKILL.md 描述同步**：「9 段骨架」→「4 段最小骨架（v7.3.10+P0-110 从 11 段简化）」
- **核心收益**：
  - 用户从最小骨架快速上手 · 不被假设的技术栈限制
  - 不假设 K8s / PostgreSQL / Redis · 任何栈（Docker / Serverless / 物理机 / 自建脚本）都能用
  - 模板复制后真正"按项目填" · 不是"按模板改"
- **加 1 删 1 元规则核算**：
  - **加**：CHANGELOG entry（~30 行）= ~30 行
  - **删 / 简化**：troubleshooting 模板（367 行 → 50 行 · 净减 ~317 行）+ SKILL.md 描述微调（-1 行 +1 行）= ~317 行净减
  - **净减 ~287 行**（罕见的大幅净减 patch · 标志模板设计的"够用就好"原则）
- 不动：
  - SKILL.md 项目级文档信息架构 TROUBLESHOOTING.md 行（仍存在 · 仅描述微调）
  - standards/discussion-mode.md 知识地图（不变）
  - stages/triage-stage.md § A · query 排查类查询特殊路由（不变 · 仍指向 templates/troubleshooting.md）
- 影响面：3 个文件改动（templates/troubleshooting.md 重写 / SKILL.md 描述微调 / CHANGELOG.md）+ 元数据 1 个（SKILL.md version）
- 后续验证：
  - 立即可验证：`templates/troubleshooting.md` 行数 ≤ 80
  - 立即可验证：模板含 4 个核心段（环境 / 查 log / 查数据缓存 / 常见报错）
  - 立即可验证：模板**不含** K8s / PostgreSQL / Redis 等具体技术栈命令（仅占位符）
  - 实战验证：用户复制模板后能在 5 分钟内填完关键值（不需大幅删减）

## v7.3.10 + P0-109（项目排查工具集 TROUBLESHOOTING.md · 类比 teamwork_space.md 模板模式）

> v7.3.10+P0-109 引入项目级排查工具集文档。**触发**：用户实战暴露 mode A query 的关键缺口——用户问"为什么报 502 / 查 log / 查 DB"时 · PMO 只能 grep 代码 · 但很多排查需要的是"怎么查环境"（log / DB / Redis / 监控 / 部署）· 不是代码。**根因**：项目级文档信息架构（v7.3.10+P0-106 引入）覆盖了产品规划 / 项目知识 / 历史决策 / 多子项目 · 但**完全缺"运维 / 排查"层**。

### P0-109：TROUBLESHOOTING.md 项目排查工具集（类比 teamwork_space.md 处理）

- 触发：用户提议「定义问题排查工具集文档 · 包含怎么查 staging 环境和线上 log / 怎么连数据库 / 怎么查 Redis」 · 完善 mode A query 的"运维操作"维度。
- 设计哲学（类比 teamwork_space.md 模板模式）：
  - **路径固定**：项目根 `TROUBLESHOOTING.md`（不查 docs/ · 不穷举多路径）
  - **teamwork 提供模板**：`templates/troubleshooting.md`（9 段骨架 + 占位符）
  - **内容用户维护**：每个项目栈不同（K8s vs Docker vs Serverless）· teamwork 不规范具体命令
  - **不强推 / 不阻塞**：不存在时 PMO 一句话提示用户从模板创建 · 同时用通用方法继续排查
- 核心改动：
  - **P0-109-A0. 创建 `templates/troubleshooting.md` 参考模板**（~250 行 · 9 段标准骨架）：
    - 一、环境信息总览（local / staging / production · 写操作授权矩阵）
    - 二、Log 查询（应用 K8s / 网关 nginx / 集中式 ELK-Loki-CloudWatch / 浏览器端 Sentry）
    - 三、数据库（连接命令 + 常用查询模板 + schema 速查）
    - 四、Redis / 缓存（连接 + key 模式 + 排查命令）
    - 五、监控 / 链路追踪（Grafana / Sentry / Jaeger）
    - 六、部署 / 回滚（staging 自由 / production 必须用户授权）
    - 七、常见报错定位思路（5 类：502 / DB 连接超时 / Redis 缓存未命中 / 队列堆积 / 第三方 API 失败）
    - 八、安全约束（PMO 排查时必守 4 条）
    - 九、定期更新（每季度命令验证 + 更新记录表）
    - 十、与其他文档关系（KNOWLEDGE / ARCHITECTURE / database-schema / RUNBOOK / PROJECT / ROADMAP）
    - 模板使用提示（删的删 / 加的加 / 路径硬规则）
  - **P0-109-A. SKILL.md § 项目级文档信息架构** 加 TROUBLESHOOTING.md：
    - 项目级权威文档表加一行：`TROUBLESHOOTING.md · 排查 / 运维操作手册 · mode A query / E · discuss 触及"排查 / 报错"时`
    - 加 P0-109 设计要点说明：路径固定项目根 / teamwork 提供模板 / 内容用户维护 / 不强推
    - 按话题路由 read 速查加排查路由（10 类关键词触发 read TROUBLESHOOTING.md）
  - **P0-109-B. `standards/discussion-mode.md § 知识地图`** 同步：
    - 知识地图按话题路由表加一行：「排查 / 报错 / 查 log / 查环境 / 查 DB / 查 Redis / 部署 / 回滚」→ TROUBLESHOOTING.md（项目根）
    - 类比 teamwork_space.md 处理 · 不存在时一句话提示用户从模板创建
  - **P0-109-C. `stages/triage-stage.md § A · query`** 加排查类查询特殊路由：
    - 第 2 步加排查类查询路由（关键词触发 → 优先 read TROUBLESHOOTING.md）
    - 新增「排查类查询特殊路由（v7.3.10+P0-109）」段：
      - 触发关键词清单（17+ 关键词）
      - 优先级 1：固定 read 项目根 TROUBLESHOOTING.md（存在则按文档执行）
      - 优先级 2：不存在时一句话提示 + 用通用方法继续排查
    - 强调「不强推模板」（类比 teamwork_space.md 模板模式）
    - silent read 原则
    - production 写操作与红线 R8 协同（TROUBLESHOOTING § 八 是软指引 · R8 是硬门禁）
- **核心收益**：
  - mode A query 第一次有"运维 / 排查"维度的项目级知识源
  - 与 KNOWLEDGE.md 互补（注意点 vs 操作手册）
  - 与 mattpocock diagnose skill 互补（通用方法论 vs 项目级具体命令）
  - 模板帮助用户快速建立 TROUBLESHOOTING.md（不从零开始）
  - production 写操作双层防护（TROUBLESHOOTING § 八 软指引 + R8 红线硬门禁）
- **加 1 删 1 元规则核算**：
  - **加**：templates/troubleshooting.md 新建（~250 行）+ SKILL.md 项目级文档信息架构 1 行 + 设计要点说明（~6 行）+ 按话题路由 1 行 + standards/discussion-mode.md 1 行 + triage-stage.md mode A 第 2 步（~5 行）+ 排查类查询特殊路由段（~30 行）+ CHANGELOG entry（~50 行）= ~345 行
  - **删 / 简化**：无（纯新增 · 知识地图扩展）
  - **净加 ~345 行**（模板占大头 · 但模板是用户复制基础 · 不是 teamwork 内部冗余）
- 不动：
  - 红线 R1-R8（不新增红线）
  - KNOWLEDGE.md / ARCHITECTURE.md / database-schema.md（边界清晰 · 各自不动）
  - mode B / C / D 行为（仅 mode A query 加排查路由）
- 影响面：4 个文件改动 + 1 个文件新建（templates/troubleshooting.md）+ 元数据 1 个（SKILL.md version）
- 后续验证：
  - 立即可验证：`templates/troubleshooting.md` 存在 + ≥ 10 段
  - 立即可验证：SKILL.md 项目级文档信息架构含 `TROUBLESHOOTING.md` 行
  - 立即可验证：SKILL.md 按话题路由速查含「报错 / 502 / 查 log」→ TROUBLESHOOTING.md
  - 立即可验证：standards/discussion-mode.md 知识地图含 TROUBLESHOOTING.md 路由
  - 立即可验证：stages/triage-stage.md § A · query 含「排查类查询特殊路由」段
  - 实战验证：用户问 `/teamwork 看下 staging 502 是怎么回事`：
    - 项目有 TROUBLESHOOTING.md → PMO silent read · 按文档步骤执行（kubectl / curl / 看 log）· 给定位结论
    - 项目无 TROUBLESHOOTING.md → PMO 用通用方法（kubectl 探索）· 给初步定位 + 一句话建议创建文档
- README 同步：⚠️ 推荐下次 README 大同步时体现（"排查 / 运维"是 teamwork 之前完全缺失的能力维度 · 用户体感变化大）

## v7.3.10 + P0-108（Feature Planning 流程重写为纯执行流程）

> v7.3.10+P0-108 完成 P0-106 职责正交化设计的最后一块：Feature Planning 流程内部"讨论部分"完全删除（已迁 E · discuss）· 流程退化为"仅写多文档"的纯执行流程。

### P0-108：Feature Planning 流程重写（删除内部讨论残留）

- 触发：P0-106 引入 E · discuss 后 · Feature Planning 流程内部仍保留"PM 与用户讨论产品方向 / 多次暂停确认 / Designer 全景重建"等讨论步骤 · 与 E · discuss 重合。**目标**：完全删除内部讨论部分 · 流程仅做"PMO 把 E · discuss 结论落到 PROJECT/ROADMAP/sitemap"。
- 设计哲学（按 P0-103 红线生命周期管理走路径 B）：
  - 职责正交化：E · discuss 接管所有讨论 · Feature Planning 仅执行
  - 简化暂停点：从 4 次暂停（讨论 / 全景验收 / PROJECT 确认 / ROADMAP 确认）→ 1 次暂停（变更摘要确认）
  - 同回合写完：sitemap / PROJECT / ROADMAP 在同一回合内写完 · 不分多次暂停
- 核心改动：
  - **P0-108-A. `FLOWS.md § Feature Planning 流程` 全文重写**：
    - 删除"v7.3.10+P0-106 之前（仅参考）"过渡段（不再保留旧版描述 · 直接简化）
    - 流程概览：4 暂停步骤 → 2 步（变更摘要确认 + 写多文档）
    - 加"简化点（vs P0-108 之前）"对照段（让读者清楚改了什么）
  - **P0-108-B. `rules/flow-transitions.md § Feature Planning 流程` 同步重写**：
    - 转移表：6 行（含 Workspace 多子项目）→ 4 行（核心 4 步流转）
    - 新增"关键变化"说明（vs P0-108 之前 · 4 暂停 → 1 暂停）
    - 加 cite L2（FLOWS.md / discussion-mode.md）
- **核心收益**：
  - **流程长度减半**：4 暂停 → 1 暂停 · 用户输入次数减半
  - **职责完全正交化**：E · discuss 讨论 · Feature Planning 执行 · 不重复
  - **同回合写完**：sitemap / PROJECT / ROADMAP 一次性 · 避免中断 / 多次暂停
  - **删除 Designer Subagent dispatch**：sitemap.md 直接 Edit（设计决策已在 E · discuss 完成）· 不再 dispatch
- **加 1 删 1 元规则核算**：
  - **加**：FLOWS.md 简化点对照段（~25 行）+ flow-transitions.md 关键变化说明（~6 行）+ CHANGELOG entry（~50 行）= ~81 行
  - **删 / 简化**：FLOWS.md 旧流程概览（含讨论 / 4 暂停 / Designer dispatch · ~50 行）+ "v7.3.10+P0-106 之前（仅参考）"过渡段（~5 行）+ flow-transitions.md 旧 Feature Planning 转移表（~6 行）= ~61 行删除
  - **净加 ~20 行**（流程瘦身 · 但加"简化对照段"让历史变化清晰）
- 不动：
  - "Feature Planning 规则"段（强制规则部分 · 仍合法）
  - "Feature Planning → Feature 衔接"段（仍合法）
  - "变更级 Feature Planning 子模式"（v7.3.10+P0-33 新增 · 与 change-request 流程协同 · 仍合法）
  - "Workspace 级 Feature Planning"（多子项目场景 · 仍合法）
- 影响面：3 个文件改动（FLOWS.md / rules/flow-transitions.md / CHANGELOG.md）+ 元数据 1 个（SKILL.md version）
- 后续验证：
  - 立即可验证：`grep -E "PM 与用户讨论|讨论达成共识|讨论过程中记录" FLOWS.md` 应返回 0
  - 立即可验证：FLOWS.md Feature Planning 流程概览段含"PMO 整理 E · discuss 结论"
  - 实战验证：下次 E · discuss 拍板规划方向 → mode B → prepare-stage 识别 = Feature Planning → 仅 1 次暂停（变更摘要）+ 1 次执行（写多文档）= 完成
- 后续 patch：P0-109 5 mode 实战 case 验证 + 边界 case 调优

## v7.3.10 + P0-107（init-stage 物理删除 + 全框架引用迁移完成）

> v7.3.10+P0-107 完成 P0-106 入口架构重构的最后清理 · 物理删除 deprecated 的 stages/init-stage.md · 全框架引用迁移到 triage-stage.md / prepare-stage.md。

### P0-107：init-stage 引用批量迁移 + 物理删除

- 触发：P0-106 完成入口架构重构后 · init-stage.md 标 deprecated 但物理保留 · 留下技术债。**目标**：清理 22 处实际引用 + 物理删除文件 · 让架构清理彻底完成。
- 设计哲学（按 P0-103 红线生命周期管理走路径 B）：
  - 迁移规则（按上下文路由）：
    - 默认 → triage-stage.md（入口主流程）
    - "Step 1.2 / 项目空间 / KNOWLEDGE 扫描 / 角色可用性" → prepare-stage.md
    - "Step 0 命令解析 / AUTO_MODE 入口" → triage-stage.md 动作 1
  - 跳过规则：
    - docs/CHANGELOG.md（135 处历史记录 · 保留）
    - docs/OPTIMIZATION-PLAN.md（保留历史规划）
    - standards/output-tiers.md 反模式 5 实战 case 引用（"执行 init-stage Step 0/1" 黑名单措辞 · 是反模式禁令的 case · 保留）
    - prepare-stage.md 内部"原 init-stage 来源"历史描述（保留 · 是迁移轨迹）
- 核心改动：
  - **P0-107-A. 编写迁移 Python 脚本**（migrate_init_stage.py · 用完即删）：
    - 6 条 regex 替换规则 · 按上下文路由
    - 跳过历史段标记（"DEPRECATED" / "原 init-stage" / "v7.3.10+P0-106"）
    - 自动批量替换 7 处（agents/README.md / RULES.md / STATUS-LINE.md / roles/pmo-auto-mode.md / roles/external-reviewer.md / roles/pmo-external-orchestration.md）
  - **P0-107-B. 手动修复语义错位 4 处**：
    - roles/pmo.md L365：Bug 流程链定义 cite → prepare-stage Step 7 流程类型识别
    - standards/prompt-cache.md L152：占位符说明 → prepare-stage / triage-stage
    - standards/prompt-cache.md L165：版本缓存机制 cite → prepare-stage Step 2
    - standards/external-model.md L234：宿主检测 cite → prepare-stage Step 1
  - **P0-107-C. rules/naming.md 命名表更新**：
    - 「分诊 / 初始化 → Triage / Init」改为「分诊 / 重型准备 → Triage / Prepare」
    - 加 P0-107 注释：原 init-stage.md 已物理删除（拆分为 triage + prepare）
  - **P0-107-D. SKILL.md 索引段清理**：
    - 删除 "~~init-stage.md~~" deprecated 行 · 改为 P0-107 注释
    - 删除"相关文件索引"中的 init-stage 条目
  - **P0-107-E. prepare-stage.md「与原 init-stage.md 的关系」段更新**：
    - 标注 v7.3.10+P0-107 完成迁移
    - 加迁移路径表（5 步原始 → 新位置）
  - **P0-107-F. 物理删除 stages/init-stage.md**：
    - rm 文件 · 不再保留 redirect stub
    - 残留 init-stage 字符串仅在合法历史段（CHANGELOG / output-tiers 反模式 case / prepare-stage 来源描述）
- **核心收益**：
  - **架构清理彻底**：deprecated 文件物理删除 · 不再有"僵尸文件"
  - **全框架引用一致**：所有活引用指向 triage-stage / prepare-stage（按语义路由）
  - **新用户体感清晰**：stages/ 目录下只有真正活跃的 stage · 没有 deprecated 干扰
- **加 1 删 1 元规则核算**：
  - **加**：CHANGELOG entry（~50 行）+ rules/naming.md 注释（1 行）+ prepare-stage.md 迁移路径表（~10 行）= ~60 行
  - **删 / 简化**：stages/init-stage.md 物理删除（~80 行 redirect stub）+ SKILL.md deprecated 索引行（2 行）= ~82 行
  - **净减 ~22 行**（罕见的净减 patch · 标志架构重构的彻底清理）
- 不动：
  - docs/CHANGELOG.md（135 处历史 init-stage 引用 · 保留）
  - standards/output-tiers.md 反模式 5（实战 case 反例引用 · 保留）
  - prepare-stage.md 内部"原 init-stage Step X"来源描述（保留 · 是迁移轨迹）
- 影响面：8 个文件改动（migrate 脚本批量 7 处 + 手动 4 处）+ 1 个文件删除（stages/init-stage.md）+ CHANGELOG + version bump
- 后续验证：
  - 立即可验证：`ls stages/init-stage.md` 应返回 No such file
  - 立即可验证：`grep -rE "init-stage" --include="*.md" stages/ standards/ roles/ rules/ SKILL.md RULES.md FLOWS.md 2>/dev/null | grep -v "DEPRECATED\|原 init-stage\|P0-106\|P0-107\|prepare-stage.md.*关系\|output-tiers.md.*反模式"` 应返回 0
  - 实战验证：下次启动 teamwork 不再看到 init-stage.md cite 报错
- 后续 patch：P0-108（Feature Planning 流程完整重写 · 删除内部讨论残留） / P0-109（5 mode 实战 case 验证）

## v7.3.10 + P0-106（入口架构重构 · 5 mode 分诊 + prepare-stage + 知识地图 + E · discuss）

> v7.3.10+P0-106 入口架构终极重构。**触发**：累积多个对话讨论暴露 init/triage 当前架构的根本问题（每次启动都跑重型仪式 / discussion 场景没明确 mode / PMO 缺项目级文档信息地图 / Feature Planning 流程内部"讨论部分"与 E · discuss 重合）。**根因**：当前架构假设所有 `/teamwork` 输入都需要相同准备 · 但实际 5 类输入（query/execute/resume/status/discuss）需要的准备完全不同。

### P0-106：5 mode 分诊架构（triage = 真正入口 · prepare = mode B 准备 · init deprecated）

- 触发：用户实战 case + 设计反思 → 4 个核心洞察：
  1. 用户输入实际有 5 种 mode（A query / B execute / C resume / D status / E discuss）· 不是单线流程
  2. init-stage 是历史包袱 · 每一步都可以延后到对应 mode 触发后
  3. PMO 在所有 mode 都需要"项目级文档信息架构"知识地图（不是 discuss 专属）
  4. Feature Planning 流程内部"讨论部分"与 E · discuss 重合 · 应职责正交化
- 设计哲学：
  - **triage = teamwork 真正入口**（不再是 init 之后的子步骤）：仅 1 件事 · 看用户输入决定 5 mode 之一
  - **prepare-stage = mode B 重型准备**：吸收原 init Step 1.2/2 + 原 triage Step 2-9 + 流程感知懒加载
  - **按需启动彻底落地**：query/resume/status/discuss 各走各最小路径 · 不跑共享重型仪式
  - **PMO 知识地图前置**：项目级文档信息架构作为 PMO 通用常识 · 5 mode 共享
  - **Feature Planning 职责正交化**：内部讨论部分迁 E · discuss · 流程仅做"写多文档"
- 核心改动：
  - **P0-106-A. 新建 `standards/discussion-mode.md`**（L2 单源 · ~300 行）：
    - 一、E · discuss 是什么 · 二、触发规则（关键词 + 排除规则 + 边界 case）
    - 三、行为规范（综合视角 + silent read + 不切身份 / 不写文件）
    - 四、知识地图按话题路由 read · 五、与 PL 讨论 / Feature Planning / 变更管理 / 跨 Feature 升级的边界
    - 六、升级路径（→ B/A/C/D）· 七、反模式（5 类）· 八、PMO 自检 checklist · 九、相关规范
  - **P0-106-B. SKILL.md 加「项目级文档信息架构」段**（PMO 5 mode 通用知识地图 · ~80 行）：
    - 1. 框架内部文档（已注入 · 默认知道）
    - 2. 项目级权威文档（PROJECT/ROADMAP/sitemap/KNOWLEDGE/...）+ 各文档权威范围
    - 3. Feature 级文档（按编号定位 · state.json/PRD/TC/TECH/UI/REVIEW/...）
    - 4. 多子项目层 · 5. 配置层 · 6. 权威范围对照（避免冲突）
    - 7. 按话题路由 read 速查 · 8. silent read 原则
  - **P0-106-C. 新建 `stages/prepare-stage.md`**（mode B 重型准备 · ~350 行）：
    - 入口 Read 顺序（v7.3.10+P0-106 固定 · prompt cache 友好）
    - Step 1 SKILL_ROOT 检测 · Step 2 版本缓存校验 · Step 3 项目空间 · Step 4 隐式承接
    - Step 5 KNOWLEDGE 扫描 · Step 6 ADR 扫描 · Step 7 流程类型识别（5 种闭集 · 删问题排查）
    - Step 8 流程感知懒加载（5 流程 × 6 步骤的触发矩阵）
    - Step 9 角色可用性 · Step 10 外部模型探测 · Step 11 看板 · Step 12-14 描述 + 暂停 + state.json 创建
  - **P0-106-D. 重写 `stages/triage-stage.md`** 为 5 mode 分诊（~250 行 · 极简单一职责）：
    - 动作 1 解析命令前缀（吸收原 init Step 0）· 动作 2 五 mode 分诊
    - 各 mode 行为速查 + 详细规范 cite L2
    - 删除原 Step 2-9（迁到 prepare-stage.md）
  - **P0-106-E. `stages/init-stage.md` 标 deprecated + redirect**（保留物理文件兼容 164 处引用）：
    - 替代关系表（原 5 步 → 新位置）
    - 设计变化对比图（v7.3.10+P0-106 之前 vs 之后）
    - 后续清理路径（P0-107 拟扫描 164 处引用 · 批量迁移 cite 后物理删除）
  - **P0-106-F. 关键散落引用整合**：
    - SKILL.md 索引段：init-stage → triage-stage 主入口 + prepare-stage 重型准备
    - SKILL.md 启动流程描述（"PMO 第一件事是读取 init-stage" → "读取 triage-stage 5 mode 分诊"）
    - rules/flow-transitions.md 重写转移表（5 mode 各自路径 + prepare-stage 转移行）
  - **P0-106-G. Feature Planning 流程精简**：
    - FLOWS.md Feature Planning 段顶部加 v7.3.10+P0-106 职责正交化说明
    - 流程内部"PM 与用户讨论产品方向"等讨论部分标 deprecated（已迁到 E · discuss）
    - 流程仅承担"写多文档"执行动作（用户在 E · discuss 拍板后）
- **核心收益**：
  - **5 mode 各自最小路径**：A ~80 / B ~600-850 / C ~300 / D ~400 / E ~150 tokens · 不再单线一刀切
  - **PMO 通用知识地图**：5 mode 共享 · 不再每次重新拼凑文档位置
  - **E · discuss 第一次明确支持**：占 ~30% 实际使用的"想法讨论"场景终于有 mode 处理
  - **Feature Planning 职责清晰**：讨论 vs 落地正交化 · 不重复
  - **架构更对应 mattpocock 哲学**：每个 stage 单一职责 · 按需启动彻底
- **加 1 删 1 元规则核算**：
  - **加**：standards/discussion-mode.md 新建（~300 行）+ stages/prepare-stage.md 新建（~350 行）+ SKILL.md 信息架构段（~80 行）+ triage-stage.md 重写（~250 行 · 含 mode A/C/D 详规）+ init-stage.md redirect（~80 行）+ FLOWS.md Feature Planning 精简说明（~10 行）+ flow-transitions.md 转移表更新（~10 行）= ~1080 行
  - **删 / 简化**：原 triage Step 2-9（迁出 · 净减 ~400 行）+ 原 init Step 1.2/2/3（迁出 · 净减 ~150 行 · 替为 redirect ~80 行）= ~470 行减少
  - **净加 ~610 行**（架构重构 · 物理拦截即时生效 · 入口体验从"重仪式"变"按需启动"）
- 不动：
  - 各业务 stage（goal_plan / blueprint / dev / review / test / pm_acceptance / ship）
  - 红线 R1-R8（不新增 · 按 P0-103 红线生命周期管理走）
  - 评审契约 / 多角色身份切换 / state.json schema / templates
  - 164 处 init-stage 引用（保留兼容 · 后续 P0-107 渐进迁移）
- 影响面：8 个文件改动 · 2 个新建（discussion-mode.md / prepare-stage.md）· 1 个标 deprecated（init-stage.md）· 5 个修改（SKILL.md / triage-stage.md / FLOWS.md / flow-transitions.md / CHANGELOG.md）+ 元数据 1 个（init-stage.md SKILL_VERSION 期望）
- 后续验证：
  - 立即可验证：standards/discussion-mode.md 存在 + ≥ 9 段 / SKILL.md 含「项目级文档信息架构」段 / stages/prepare-stage.md 存在 + ≥ 14 Step / stages/triage-stage.md 含 5 mode 分诊 / stages/init-stage.md 含 DEPRECATED 标记
  - 实战验证：
    - `/teamwork 看下 X` → mode A 直接 grep（不进 init / prepare）
    - `/teamwork`（空）→ mode D 看板（不进 prepare）
    - `/teamwork 实现 F032` → mode B → prepare-stage → Feature 流程
    - `/teamwork 我感觉红线太重了` → mode E 讨论（不创建 Feature）
    - `/teamwork 继续 F032` → mode C jump-to-stage（不重走 init）
- 后续 patch 规划：
  - **P0-107**：扫描 164 处 init-stage 引用 · 批量迁移 cite（init-stage.md → triage-stage.md 或 prepare-stage.md）· 完成后物理删除 init-stage.md
  - **P0-108**：FLOWS.md Feature Planning 段完整重写（仅"写多文档"流程描述 · 删除全部"讨论"残留）
  - **P0-109**：实战 case 收集 · 验证 5 mode 判定准确度 · 边界 case 调优
- README 同步：⚠️ **强烈推荐下次 README 大同步时体现**（5 mode 入口架构 + E · discuss + prepare-stage 是用户体感最大的变化 · 与 P0-100 README 同步原则一致）

## v7.3.10 + P0-105（init/stage 入口 silent execution 强化）

> v7.3.10+P0-105 silent execution 缺口补漏。**触发**：用户分享 case · `/teamwork 检查下 PTR test 模块逻辑 · 返回的链接不是 aon.link` 出现 6 段 init / stage 入口播报（"执行 init-stage Step 0/1" / "版本不一致（缓存 P0-103 → skill P0-104）走全量校验" / "CLAUDE.md 与模板字符级一致" / "🔄 已同步" / "继续 Step 2/3 加载项目空间和看板" / "进入 triage-stage 分流" / "收到。现在直接定位 PTR test 模块代码"）才到 grep。**根因**：P0-98 silent execution 反模式 5 仅覆盖 triage Step 1.5/1.6 + 缓存命中 banner · 没覆盖 init 缓存不一致路径 + stage 入口标题 + Step 1 用户承接前缀。

### P0-105：init / stage 入口 silent execution 强化（3 个未覆盖缺口）

- 触发：用户实战 case · 暴露 P0-98 silent execution 设计的 3 个未覆盖缺口（init 缓存不一致路径 / stage 入口标题 / Step 1 用户承接前缀）。
- 设计哲学（按 P0-103 红线生命周期管理走路径 A+B · 不新增 L1 红线）：
  - **路径 A 顶层 cite**：R4(b) 不膨胀已含 silent execution 引用 · 不动
  - **路径 B L2 单源**：standards/output-tiers.md 反模式 5 加 P0-105 扩展段（实战 case 黑名单措辞）
  - **stage spec 行为约束**：init-stage / triage-stage 顶部加 silent execution 硬规则段 + Step 1 改隐式承接
- 核心改动：
  - **P0-105-A. `standards/output-tiers.md` 反模式 5 加 P0-105 扩展段**：
    - 实战 case 7 段反例完整抄入（init step 标题 / 版本同步内部决策叙事 / stage 入口标题 / "收到+计划"前缀 / 中间结果汇报 / 执行确认）
    - 5 类新黑名单措辞表（含具体反例措辞 · 物理拦截）
    - 4 条唯一允许输出（异常分支 / 决策点 / 实际答案）
    - 2 条判定规则（工具调用前 / 工具调用之间 不输出叙事）
  - **P0-105-B. `stages/init-stage.md` 全程 silent 强化**：
    - 顶部 Process Contract 加「init-stage 全程 silent execution 硬规则」段（默认静默 + 6 类禁止输出 + 4 类唯一允许输出 / cite L2 单源）
    - Step 1.2-c 不一致路径加 silent 子条（不输出"版本不一致 / 字符级一致 / 已同步" + 唯一例外：CLAUDE.md 真实漂移）
    - Step 1.2-c null 路径标注「异常路径 · 必须输出」明示区分
  - **P0-105-C. `stages/triage-stage.md` Step 1 改隐式承接**：
    - 原文：「PMO 必须先显式响应'我已收到你的输入'」
    - 改为：「承接是隐式的 · PMO 必须实际承接（行为）但**不输出**承接确认文本」
    - 加 5 条禁止输出反例 + 正确姿态 3 条 + 红线 R3 解释段（承接是行为 · 不是文本）
    - 异常分支允许输出（输入无法解析 / BLOCKER 触发）
- **核心收益**：
  - init / triage 启动期主对话叙事开销 ~80% 削减（实战 case 6 段 → 0 段）
  - 用户问题到 grep 实际代码的工具调用间隔从 ~10 段叙事缩到 0 段
  - silent execution 设计从 P0-98 三处覆盖（triage Step 1.5/1.6 + 缓存命中）扩展到全 init + Step 1 隐式承接
- **加 1 删 1 元规则核算**：
  - **加**：output-tiers.md 反模式 5 P0-105 扩展段（~50 行）+ init-stage.md silent execution 硬规则段（~25 行）+ Step 1.2-c silent 子条（~7 行）+ triage Step 1 隐式承接重写（~25 行）= ~107 行
  - **删 / 简化**：triage Step 1 原"必须显式响应"3 行删除（替为隐式承接段）+ init Step 1.2-c "🔄 已同步"输出 1 行删除 = ~4 行
  - **净加 ~103 行**（silent execution 设计的最后一公里 · 物理拦截 case 实战暴露的反例）
- 不动：
  - init Step 0 命令解析输出（解析失败时仍需 ⚠️ · 异常路径）
  - init Step 2 加载项目空间 banner（未在本 case 触发 · 留下次实战 case 再考虑）
  - init Step 3 Feature 看板（用户输入"继续"时仍需输出 · 是答案而非叙事）
  - Pull / Push 路径之后的实际答案输出（这才是用户要的）
- 影响面：4 个文件改动（standards/output-tiers.md / stages/init-stage.md / stages/triage-stage.md / docs/CHANGELOG.md）+ 元数据 2 个（SKILL.md / init-stage.md SKILL_VERSION）
- 后续验证：
  - 立即可验证：standards/output-tiers.md 反模式 5 含 "P0-105 扩展" 子段（grep "P0-105 扩展" 命中）
  - 立即可验证：stages/init-stage.md Process Contract 段含 "init-stage 全程 silent execution 硬规则"
  - 立即可验证：stages/triage-stage.md Step 1 含 "承接是隐式的" + 5 条禁止输出反例
  - 实战验证：下次 `/teamwork [需求]` 启动 · init 全程静默（缓存命中 / 不一致都不输出 banner）+ triage Step 1 不输出"收到 / 现在直接定位 X" · 直接进 Step 1.5/1.6 silent · 然后 grep / Read / 答案
  - 对比基线：本次 case 6 段叙事 · P0-105 后应 0 段叙事
- README 同步：❌（内部 silent execution 行为优化 · 不影响新用户体感门面 · 同 P0-101~104 处理）

## v7.3.10 + P0-104（codex 调用 OpenAI ToS 合规 + 外部模型只读评审）

> v7.3.10+P0-104 codex 账号 abuse 警告响应。**触发**：用户分享 codex 账号收到 OpenAI "cyber abuse" 警告。**根因**：teamwork 早期把 codex CLI 当 AI agent 后端用 — 5/8 profile sandbox=full（rd-developer/tester/planner/designer/e2e-runner 自主执行任意命令）+ service_tier=fast（API 级优化信号）+ codex-agents/hooks.json（持久化触发）+ AI 编排 AI 链式 dispatch · 触发 OpenAI cyber abuse 自动检测。**修复**：codex 角色重定位为「只读评审辅助」· 物理拦截所有 cyber abuse 信号。

### P0-104：codex 调用合规重构（外部模型 = 只读评审 · 不再作 AI agent 后端）

- 触发：用户实战 case · OpenAI 警告促使审视 teamwork 对 codex 的使用模式 · 发现严重越界（5 个 full sandbox profile · service_tier=fast · 持久化 hooks）。
- 设计哲学（按 P0-103 红线生命周期管理元规则走路径 A+B · 不新增 L1 红线）：
  - **路径 A 顶层 cite**：SKILL.md R1 + R7 各加一句话 cite L2 单源
  - **路径 B L2 单源**：standards/external-model-usage.md 承载详细合规规则
  - **L3 工具层**：codex-agents/*.toml 物理改 read-only · 删 service_tier · 删 hooks.json
  - 核心原则：**外部模型只能读代码 · 只能输出 markdown 评审 · 不执行 / 不写文件**
- 核心改动：
  - **P0-104-A. codex profile 物理修复**（L3 · 物理拦截）：
    - 5 个 full → read-only：`rd-developer.toml` / `tester.toml` / `planner.toml` / `designer.toml` / `e2e-runner.toml`
    - 全部 8 个 profile 删除 `service_tier = "fast"` 行
    - approval_policy 走 codex 默认（不显式声明 · on-request）
    - 删除 `codex-agents/hooks.json`（持久化触发信号）
  - **P0-104-B. 5 个非评审 profile 标 deprecated**：
    - description 起首加 `[DEPRECATED v7.3.10+P0-104]`
    - developer_instructions 改为提示用户去主对话身份切换执行（不再 dispatch）
    - 文件保留（用户手动 ad-hoc 仍可用 · 但已强制 read-only · 无 cyber abuse 风险）
  - **P0-104-C. 新建 `standards/external-model-usage.md`**（L2 单源 · 10 段）：
    - 一、核心原则 4 条硬约束 · 二、为什么必须合规（OpenAI ToS 信号清单）· 三、合规架构图（✅ 评审 vs ❌ AI 后端）
    - 四、profile 分类（3 评审 / 5 deprecated）· 五、prompt 注入硬规则 · 六、配置约束清单
    - 七、违规处置 · 八、与 SKILL.md R1/R7 的关系 · 九、相关文件 · 十、申诉模板
  - **P0-104-D. SKILL.md 红线 R1 + R7 加 cite L2**（路径 A 一句话）：
    - R1 加：「外部模型例外：codex / gemini 等外部模型仅用于只读评审 · 不参与代码写权 · sandbox 强制 read-only · 详见 standards/external-model-usage.md」
    - R7 加 (d) 子条：「外部模型评审审计：codex / gemini 等外部模型评审输出走主对话审计 · 不得作为自主 AI agent 后端（OpenAI ToS 合规）· 详见 standards/external-model-usage.md」
  - **P0-104-E. 评审 profile + claude-agents/reviewer.md prompt 注入合规约束**：
    - reviewer.toml / blueprint-reviewer.toml / prd-reviewer.toml 的 developer_instructions 顶部加「🔴 STRICT CONSTRAINTS」段：READ-ONLY · markdown only · no patches · no exec · "Out of scope" 拒绝模板
    - claude-agents/reviewer.md 同步加 STRICT CONSTRAINTS 头
    - blueprint-reviewer / prd-reviewer 文件名 cite 修正（templates/codex-cross-review.md → external-cross-review.md · 历史遗留）
    - roles/external-reviewer.md 顶部 cite 加合规边界链接
- **核心收益**：
  - 物理拦截：所有 codex profile sandbox=read-only · OpenAI 视角下不可能再触发 cyber abuse
  - service_tier=fast 全删 · 移除"API 级优化"信号
  - hooks.json 删 · 移除"持久化机器人"信号
  - 外部模型角色明确：只评审 · 不执行 · L2 单源详规范 + L1 红线一句话 cite
  - 申诉模板就位（standards/external-model-usage.md § 十）· 用户可直接用
- **加 1 删 1 元规则核算**：
  - **加**：standards/external-model-usage.md（~165 行新文件）+ SKILL.md R1/R7 cite（~2 行）+ 5 deprecated profile 重写说明（~50 行）+ 3 评审 profile STRICT CONSTRAINTS 段（~30 行）+ claude-agents/reviewer.md STRICT CONSTRAINTS（~10 行）+ external-reviewer.md cite（1 行）= ~258 行
  - **删 / 简化**：5 profile 原 developer_instructions 替为 deprecated 提示（净简化 ~30 行）+ codex-agents/hooks.json 删除（~28 行）+ 8 profile 各删 1 行 service_tier（8 行）= ~66 行
  - **净加 ~190 行**（合规重构 · 加 L2 单源 + 申诉模板 · 物理拦截即时生效）
- 不动：
  - 评审 profile 的 sandbox_mode（已是 read-only · 不变）+ model_reasoning_effort=high（不变）
  - 主对话 Claude Code 的角色身份切换流程（codex 改不影响）
  - templates/external-cross-review.md（评审 schema 不变 · 仅 cite 修正）
- 影响面：14 个文件改动（codex-agents/*.toml × 8 / codex-agents/hooks.json 删除 / standards/external-model-usage.md 新建 / SKILL.md 红线 R1+R7 / claude-agents/reviewer.md / roles/external-reviewer.md / docs/CHANGELOG.md / stages/init-stage.md SKILL_VERSION）
- 后续验证：
  - 立即可验证：`grep -c sandbox_mode.*read-only codex-agents/*.toml` 应 = 8（全部 read-only）
  - 立即可验证：`grep -c service_tier codex-agents/*.toml` 应 = 0（全删）
  - 立即可验证：`ls codex-agents/hooks.json` 应 No such file
  - 立即可验证：`standards/external-model-usage.md` 存在 + ≥ 10 段
  - 实战验证：用户用 deprecated profile 时 codex 看到 [DEPRECATED] 提示 · 主流程不再 dispatch 5 个非评审 profile
  - 申诉验证：用户向 OpenAI 申诉时附 standards/external-model-usage.md 链接 · 截图配置已修
- README 同步：⚠️ 推荐下次 README 大同步时体现（OpenAI ToS 合规 + 外部模型只读评审定位）· 当前 patch 不强制（与 P0-101/P0-102/P0-103 处理一致）

## v7.3.10 + P0-103（红线归并 16→8 + 层级化 + 生命周期管理）

> v7.3.10+P0-103 红线减负重构。**触发**：用户问「我们的红线是不是太重了」· 反思 P0-101/P0-102 都在加红线 · SKILL.md 16 条红线 + 各 sub-file 散落硬规则 · 总硬约束远超 16 · LLM attention 稀释 + token 成本上涨 + debug 困难。**根因**：路径依赖（每次实战 case 默认加红线）+ 没退役机制（从 P0-1 到 P0-102 没删过任何红线）+ 物理拦截 vs 红线混淆（P0-101 evidence-binding / P0-102 黑名单本质是物理拦截 · 不该占红线条目）。

### P0-103：红线归并 16→8 + 层级化（L1 核心红线 / L2 专项规范 / L3 工具层）+ 生命周期管理元规则

- 触发：用户反思性提问 → AI 自查 → 发现 `每条红线都在二次扩展`（红线 #1 扩展 4 次 / 红线 #12 P0-102 扩展 / 红线 #16 全新加 P0-101）+ ~201 处「红线 #N」引用散落全框架 · 没归并机制。
- 设计哲学：
  - **L1 核心红线 ≤ 8 条**：必读 · 概念正名 · 详细 schema 走 L2
  - **L2 专项规范**：黑名单措辞 / schema / 出口校验 / 字段范围表 / 实战 case 全部下沉到 standards/* + roles/*-sub.md
  - **L3 工具层**：verify-ac.py / state-patch.py / detect-external-model.py 真正的物理拦截
  - **元规则防再膨胀**：每个 P0 patch 设计契约必含「路径 A 归并 / 路径 B 降级 L2 / 路径 C 新增 L1」三选一审视 · 默认 A > B > C
- 核心改动：
  - **P0-103-A. 创建 `standards/evidence-binding.md`**（L2 单源 · 抽出原红线 #16 全文）：
    - 一、核心规则 schema · 二、为什么必须 evidence binding（实战 case）· 三、事实字段 vs 状态字段边界
    - 四、字段 evidence schema 全表（5 类字段）· 五、PMO 出口校验伪码 · 六、违规处置 · 七、反模式 4 条 · 八、与红线 R7 的关系 · 九、相关文件
    - SKILL.md 红线 R7(c) 仅保留一句话 cite + 链接 · 不再占红线层
  - **P0-103-B. 重写 SKILL.md 红线段（16 → 8）**：
    - 顶部加层级化说明（L1 必读 ≤ 8 / L2 standards/* + roles/*-sub / L3 工具层）
    - R1-R8 重命名：R1 代码写权 / R2 流程类型闭集 / R3 PMO 统一承接 / R4 流程边界（合并原 #3+#12+#15）/ R5 暂停点协议（合并原 #5+#10）/ R6 Feature Planning 只出文档 / R7 证据闭环（合并原 #9+#14+#16）/ R8 写操作硬门禁链
    - R1 简化 4 次扩展冗余（Ship 例外详细化抽到 ship-stage.md）
    - 加历史条号映射表（旧 #N → 新 RN · 13 行）· 旧引用按表迁移
  - **P0-103-C. 全框架引用迁移**（Python 脚本批量替换）：
    - 扫描 85 个 .md/.json 文件 · 修改 19 个文件 · 共 102 处替换
    - 命中数前 5：RULES.md (20) / triage-stage.md (18) / OPTIMIZATION-PLAN.md (12) / FLOWS.md (8) / ship-stage.md (8)
    - 跳过 SKILL.md（含红线段本身 + 映射表）+ docs/CHANGELOG.md（历史记录）+ standards/evidence-binding.md（合规历史 cite）
    - 修复 2 处迁移后暴露的 pre-existing mislabel（triage-stage.md "红线 #5 写操作硬门禁" → R8）
  - **P0-103-D. SKILL.md 加「红线生命周期管理」段**（防再膨胀元规则）：
    - 元规则：每个 P0 patch 设计契约必含三选一审视（路径 A 归并 / B 降级 L2 / C 新增 L1 · 默认 A > B > C）
    - 红线层级结构图（L1/L2/L3）
    - 退役 / 归并审视清单（每 5 个 P0 patch 节奏 · 4 项审视）
- **核心收益**：
  - SKILL.md 红线条目从 16 → 8（减 50%）· LLM attention 集中
  - L2 evidence-binding.md 作为单源 · standards/* 体系完整化
  - 元规则防止再膨胀 · 后续 P0 patch 强制走「归并 > 降级 > 新增」路径
  - 引用语义集中（13 行映射表）· debug 时不需要查多处
- **加 1 删 1 元规则核算**（特殊：净减条目）：
  - **加**：SKILL.md 红线生命周期管理段（~50 行）+ standards/evidence-binding.md（~95 行新文件）+ 历史条号映射表（13 行）= ~158 行
  - **删 / 简化**：SKILL.md 红线段从 ~33 行（16 条）简化到 ~30 行（8 条 · R1 4 次扩展冗余精简）
  - **净加 ~155 行**（虽净加 · 但**红线条目从 16 → 8**·这才是真正的减负 · 加的是 L2 单源 + 元规则）
- 不动：
  - docs/CHANGELOG.md 历史段（保留旧 #N 引用 · 历史记录不可改）
  - 其他 standards/* 已有规范（output-tiers.md / prompt-cache.md / common.md / external-model.md）
  - 各 stage spec 子步骤 / Output Contract（仅引用层迁移）
- 影响面：22 个文件改动（SKILL.md 大改 / standards/evidence-binding.md 新建 / 19 个文件 102 处引用迁移 / triage-stage.md 2 处 mislabel 修复 / docs/CHANGELOG.md / init-stage.md SKILL_VERSION）
- 后续验证：
  - 立即可验证：`grep -r "红线 #1[^0-9]" --include="*.md" --include="*.json"` 应仅命中 SKILL.md 映射表 + CHANGELOG（共 ≤14 处）+ standards/evidence-binding.md 历史 cite
  - 立即可验证：SKILL.md 红线段含 R1-R8 共 8 条（grep -c "^R[0-9]\." SKILL.md ≥ 8）
  - 立即可验证：standards/evidence-binding.md 存在 + ≥ 9 段（一到九）
  - 实战验证：下次新加 P0 patch 设计契约时 PMO 应主动声明走路径 A/B/C 哪条 · 不应直接新增「红线 #N」
- README 同步：❌（内部架构重构 · 不影响新用户视角的体感 · 同 P0-101/P0-102 处理 · 但首次涉及红线条数变化建议下次 README 大同步时一并体现）

## v7.3.10 + P0-102（容量焦虑暂停反模式 · 三层物理拦截）

> v7.3.10+P0-102 容量焦虑暂停（capacity-anxiety pause）红线。**触发**：用户分享 Feature 流程 AUTO 模式 case · Blueprint Stage 入口实例化（state.json 写完）后 PMO 输出"为避免单回合溢出 · 本回合在此暂停让你看到 Goal-Plan ✅ 进度 · 下一条 ok / auto 继续"。诊断：双重违规（flow-transitions L60 是 🚀 自动流转 · auto 模式连合法 ⏸️ 都豁免反而停下来）+ 现有红线 #12 没明文覆盖"以回合边界 / 容量预算"为由的自创暂停变种。

### P0-102：容量焦虑暂停红线（三层物理拦截 · 同 P0-101 evidence-binding 套路）

- 触发：用户实战 case 暴露红线 #12 「非暂停点禁止暂停」概念性约束被 LLM "贴心 / 防溢出"包装绕过。LLM 误把"回合边界"（宿主 Claude/Cowork 层概念）当 spec 层暂停理由 · 在 🚀 自动流转节点人工拆分回合。
- 设计哲学（继承 P0-101 evidence-binding 三层物理拦截设计）：
  - **顶层正名**（红线扩展）：SKILL.md 红线 #12 加明文 "回合边界 / 容量预算 / 让用户看进度 / 单回合溢出 / 为下回合留预算 不构成暂停理由"
  - **中层物理拦截**（措辞黑名单）：roles/pmo-auto-mode.md § 十 列举具体反例措辞 · LLM 没法用"贴心"包装绕过明文匹配
  - **底层契约**（stage 通用规范）：standards/stage-instantiation.md § 三 + § 四 写明「入口实例化 → 子步骤 1 自动续接 · 同一回合内必须开始实际工作」
- 核心改动：
  - **P0-102-A. `SKILL.md` 红线 #12 扩展**（顶层正名 · 1 句话）：
    - 在原"非暂停点禁止暂停"末尾加：**"回合边界 / 容量预算 / 让用户看进度 / 单回合溢出 / 为下回合留预算 不构成暂停理由（宿主层关注 · spec 层只认 ⏸️ 标注 · 真溢出由系统自动断点续传）。Stage 入口实例化 → 子步骤 1 必须自动续接"**
    - 引用：detailed in roles/pmo-auto-mode.md § 十
  - **P0-102-B. `roles/pmo-auto-mode.md` 加 § 十「容量焦虑暂停反模式」**（中层物理拦截 · ~80 行 · **关键**）：
    - § 10.1 实战触发 case（v7.3.10+P0-102 实战 case 写入 · 后人查规则时能看到具体反例）
    - § 10.2 措辞黑名单表（5 类反例措辞 · 含 "避免单回合溢出" / "让你看到 X 进度" / "下一条 ok / auto 继续" / "工作量大本回合先停" / "本回合在此暂停"）
    - § 10.3 物理拦截判定流程（伪码 · 含暂停理由检查 → 黑名单匹配 → 自动续接）
    - § 10.4 正确姿态对照（❌ 反模式 vs ✅ 正确姿态 · 直接抄 case 原文）
    - § 10.5 与红线 #12 的关系表（4 维度对照）
    - § 10.6 PMO 自检 checklist（5 条 · 起草任何收尾段时必过）
  - **P0-102-C. `standards/stage-instantiation.md` 加自动续接硬规则**（底层契约 · ~15 行）：
    - § 三 默认通道 加 "🔴 自动续接子步骤 1（v7.3.10+P0-102 强化）" 4 子条
    - § 四 入口实例化硬约束 加 "🔴 入口实例化 → 子步骤 1 自动续接硬规则" 含反模式 3 条 + 物理拦截
    - 与红线 #12 / #14 的关系明示
- **核心收益**：
  - 物理层拦截"容量焦虑暂停"反模式（黑名单措辞 · LLM 没法用"贴心"包装绕过）
  - 红线 #12 不再是概念性约束 · 有具体可机器匹配的反例措辞清单
  - Stage 入口实例化 → 子步骤 1 自动续接成为契约层硬规则 · 三 Stage（goal-plan/blueprint/review）共享单源
- **加 1 删 1 元规则核算**：
  - **加**：SKILL.md 红线 #12 扩展（1 句话）+ pmo-auto-mode.md § 十（~80 行）+ stage-instantiation.md 自动续接段（~15 行）= ~95 行
  - **删**：无（新增红线 · 无旧规则被替代）
  - **净加 ~95 行**（同 P0-101 evidence-binding · 物理拦截硬规则一次到位）
- 不动：
  - dev-stage / test-stage 等无"入口实例化 → 子步骤 1"transition 的 Stage（dev 直接 RD 起草 · 没有这个转换点 · 不需要专项规则）
  - standards/output-tiers.md 反模式 5（silent execution 是输出叙事层 · 与流程暂停层正交）
  - roles/pmo.md（P0-93~97 已瘦身完毕 · 反向加内容会破坏 sub-file 单源）
- 影响面：4 个文件改动（SKILL.md / pmo-auto-mode.md / stage-instantiation.md / CHANGELOG.md）+ 元数据 2 个（SKILL.md version / init-stage.md SKILL_VERSION）
- 后续验证：
  - 立即可验证：SKILL.md 红线 #12 含 "回合边界 / 容量预算" 措辞 + pmo-auto-mode.md § 十 存在 + stage-instantiation.md 含 "自动续接子步骤 1"
  - 实战验证：下次 Blueprint Stage 入口实例化（state.json 写完）后 PMO 应自动开始 QA TC + RD TECH 起草 · 不应输出"本回合在此暂停 / 下一条 ok / auto 继续"
  - 对比基线：本次 case 之前 PMO 输出 "为避免单回合溢出 · 本回合在此暂停"；P0-102 后 PMO 起草收尾段时自动 grep § 10.2 措辞黑名单 · 命中 = 删除暂停意图
- README 同步：❌（内部硬规则 · 不影响新用户视角的体感 · 同 P0-101 处理）

## v7.3.10 + P0-101（事实字段 evidence-binding 硬规则）

> v7.3.10+P0-101 evidence-binding 硬规则。**触发**：用户「codex 为什么不可以用」case · PMO 凭印象写 `available_external_clis: []` 但实际 codex 在 PATH（执行 `command -v codex` 显示 `/usr/local/bin/codex`）。诊断：缺乏 evidence binding 机制 + 缺乏物理拦截手段（仅靠规则约束 AI "不要凭印象" 没用）+ 状态字段与事实字段未区分。

### P0-101：事实字段 evidence-binding 硬规则（state 字段 vs fact 字段分类 + 物理拦截）

- 触发：用户分享 case · `state.json.external_cross_review.available_external_clis = []` 与实际不符 · `command -v codex` 实测有路径。根因：PMO 凭印象生成事实型字段 + 没有"必须贴 stdout 原文"的硬约束 → AI 没法被规则约束（因为不需要贴原文就能写） → 物理上没拦截。
- 设计哲学：
  - **状态字段 vs 事实字段**：状态字段（PMO 自判状态机：current_stage/phase/verdict）由内部推导即可 · 事实字段（外部观察判定：available_external_clis/mr_url/feature_pushed_at/tests_passed/code_context_read）必须 evidence binding。
  - **物理拦截 > 规则约束**：要求贴 stdout 原文 → AI 没法编造真实命令输出 → 一旦要求贴原文必须真跑 · 这是物理层拦截 · 不依赖 AI 自觉。
  - **evidence schema**：每个事实字段配套 `*_evidence` 子对象（command + stdout 原文 + exit_code + timestamp）· 缺一不可。
- 核心改动：
  - **P0-101-A. `templates/feature-state.json` schema 加 evidence 子对象**：
    - `available_external_clis` 旁加 `detection_evidence` 字段 + `_detection_evidence_schema` 注释（command/stdout/exit_code/detected_at）
    - `_detection_evidence_note` 标注 evidence-binding 红线（v7.3.10+P0-101）
  - **P0-101-B. `stages/triage-stage.md` Step 4 强制 bash 实测 + 贴 stdout**：
    - 探测命令固化为单 bash 单 tool call（`command -v codex; echo "codex_exit=$?"; ...`）
    - 完整 stdout 原文必须落两处：① 主对话「🌐 External 探测」段（verbatim · 不改写为 "available: []"）② state.external_cross_review.detection_evidence
    - 物理拦截原理：AI 没法编造真实 stdout · 一旦要求贴原文必须真跑
  - **P0-101-C. `SKILL.md` 加红线 #16**（事实字段 evidence-binding 硬规则）：
    - 规则范围：available_external_clis / feature_pushed_at / mr_url / tests_passed / pm_self_check.code_context_read 等"来自外部观察"的字段
    - 状态字段（current_stage / phase / verdict 等 PMO 自判状态机）不在本红线范围
    - 实战触发 case 写入红线条文 · 后人查规则时能看到具体反例
  - **P0-101-D. `roles/pmo-state-mgmt.md` § 2.3 + § 2.4 加出口校验**：
    - § 2.3 Stage 结束必做 加 Step 1.5 「事实字段 evidence-binding 完整性校验」（Output Contract 校验之后 / Write 之前）
    - § 2.4 加新子段「事实字段 evidence-binding 出口校验」：含字段范围表 / 校验步骤伪码 / 违规处置 / 反模式 / 状态字段边界
    - PMO 在 Stage 出口 Read 之后、Write 之前必须执行本校验 · 失败 = 流程违规 = 阻断 Stage 出口
- **核心收益**：
  - 物理层拦截"凭印象生成事实字段"反模式（AI 没法编造真实 stdout）
  - 状态字段 vs 事实字段分类清晰 · 后续新增字段时能正确归类
  - 出口校验自动化 · PMO 不需要"记得检查" · 由 § 2.3 操作序列驱动
- **加 1 删 1 元规则核算**：
  - **加**：feature-state.json schema 注释（~15 行）+ triage-stage.md Step 4 evidence 段（~30 行）+ SKILL.md 红线 #16（1 行）+ pmo-state-mgmt.md § 2.3 Step 1.5（5 行）+ § 2.4 新子段（~50 行）= ~100 行
  - **删**：无（新增红线 · 无旧规则被替代）
  - **净加 ~100 行**（evidence-binding 是基础设施级的硬规则 · 一次到位）
- 不动：
  - 其他 9 个事实字段已有的实测惯例（review-log.jsonl 已落 stdout · ship 已要求 push 后实测远端 ref）保留 · 仅形式化 schema
  - 其他状态字段（current_stage/phase/verdict 等 PMO 内部状态机）不受影响
- 影响面：5 个文件改动（feature-state.json / triage-stage.md / SKILL.md / pmo-state-mgmt.md / CHANGELOG.md）+ 元数据 2 个（SKILL.md version / init-stage.md SKILL_VERSION）
- 后续验证：
  - 立即可验证：SKILL.md 红线 #16 存在 + pmo-state-mgmt.md § 2.4 含「事实字段 evidence-binding 出口校验」子段 + feature-state.json `_detection_evidence_schema` 存在
  - 实战验证：下一次 Triage Stage Step 4 应输出 `command -v codex` 完整 stdout（含路径或 "not found"）+ exit code · 不应再出现 `available: []` 凭印象判定
  - 对比基线：本次 case 之前 PMO 写 `available: []` 无 evidence；P0-101 后必有 detection_evidence 子对象 · 缺则 § 2.3 Step 1.5 阻断流转
- README 同步：❌（内部硬规则改 · 不影响新用户视角的体感）

## v7.3.10 + P0-100（🎉 P0 系列百号里程碑）

> v7.3.10+P0-100 README 同步收齐技术债。**触发**：用户审视 README · 发现版本号 P0-60 落后实际 P0-99 · 累积 40+ patches 的关键变化（Wave 1-4 评审规范分层规范化 / Pull-Push 模式 / Silent execution / Ship CLI 优先 / Worktree 默认 auto）没反映。

### P0-100：README 同步收齐技术债（P0 系列百号里程碑）

- 触发：用户审 README 后反馈"是否需要修改 · 能否反应 teamwork 的真实现状"。诊断结果：版本号陈旧（P0-60 → 实际 P0-99）+ 角色体系老（v7.3.10+P0-86 起 8 主 role + 12 sub-file 没体现）+ Wave 4 PMO 瘦身完全没提 + 多个体感改进（Pull/Push 模式 / Silent execution / CLI 优先）缺位。
- 设计哲学：README 是新用户/老用户回访的第一入口 · 必须反映**当前真实可用状态** · 而不是历史快照。本次同步把累积 7-8 个月的实战改进收齐 + 建立后续维护策略（重大体感变更必更）。
- 核心改动：
  - **P0-100-1. `README.md` 全文修订**（294 → 280+ 行 · 净增 ~30 行 · 信息密度大幅提升）：
    - 顶部版本号：v7.3.10+P0-60 → v7.3.10+P0-100
    - § 角色体系：6 role → 8 role（架构师独立 peer-level v7.3.10+P0-86 · External Reviewer v7.3.10+P0-38 升格）+ 12 sub-file 矩阵
    - § 流程概览：加 Pull/Push 模式说明（轻型/重型意图分流 P0-81）+ Silent execution 主张（P0-98）
    - § Worktree 策略：OFF → auto 默认（P0-41 修订自原 P0-9）
    - § Ship Stage MR 模式：补 P0-29 双段 / P0-32 finalize / **P0-99 CLI 优先 + URL 兜底**
    - § 版本历史：里程碑列表补 P0-61 ~ P0-100（重点：P0-78 ADR / P0-81 Pull / P0-85 Wave 1 / P0-86 Wave 2 / P0-87~92 Wave 3 / P0-93~97 Wave 4 / P0-98 silent / P0-99 Ship CLI）
  - **P0-100-2. `README-EN.md` 同步关键变化**（不重写全文）：
    - 顶部版本号 → P0-100
    - 加 "Recent highlights (P0-85 ~ P0-100)" 段（8-role matrix · pmo slimming · Pull/Push triage · Silent execution · Ship CLI-first）
  - **P0-100-3. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-99 → 7.3.10+P0-100）
- **核心收益**：
  - README 真实反映当前 v7.3.10+P0-100 状态 · 不再误导新用户/老用户
  - 关键体感改进（Pull 模式 / Silent execution / CLI 优先）首次进 README 主线
  - 角色体系 sub-file 矩阵首次成为 README 一等公民（之前只在 SKILL.md / agents/README.md 索引）
- **加 1 删 1 元规则核算**：
  - **加**：角色体系 sub-file 矩阵段（~25 行）+ Pull/Push 模式段（~10 行）+ Ship CLI 段（~15 行）+ 里程碑补 P0-61~100（~25 行）= ~75 行
  - **删**：旧角色体系简介（~10 行）+ 旧 Ship MR 模式段（~12 行）+ 老 worktree OFF 描述（~3 行）= ~25 行
  - **净加 ~50 行**（v7.3.10+P0-60 → P0-100 累积 40 patches 的产品层结晶）
- **后续维护策略（v7.3.10+P0-100 引入）**：
  - 重大体感变更必更 README（Stage 流程改 / 暂停点重构 / 角色体系变化 / 重大默认值反转）· 在 P0 patch 的 step 列表中加可选项
  - 内部重构 / sub-file 抽出 / 文档单源化 类 patch 不更 README（避免噪声）
  - CHANGELOG 顶部 entry 加 "README 同步: ✅ / ❌（理由）" 行
- 不动：
  - SKILL.md / FLOWS.md / RULES.md / 各 stage spec / role 文件等内部文档（README 是入口 · 内部文档不需要重做）
  - README-EN.md 的全文（仅同步 highlights · 保英文风格 · 完整重写留给后续单独 patch）
- 影响面：2 个文件改动（README.md 大改 / README-EN.md 小改）+ 元数据 2 个（SKILL.md / init-stage.md SKILL_VERSION）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：grep "v7.3.10+P0-60" 应 0 命中（除 CHANGELOG 历史段）+ README 提到 8 role + sub-file + Pull/Push + Silent + CLI 优先
  - 实战验证：新用户读 README 应能在 5 分钟内理解当前角色体系 + 流程模式 + 关键产品体验
- 设计意图：100 号里程碑 patch 不能只是版本号 +1。本 patch 把 60 → 99 累积 40 patches 的重要产品改进做一次全量同步 · 顺便建立后续 README 维护策略 · 防止再次出现 7-8 个月的累积技术债。

---

## v7.3.10 + P0-99

> v7.3.10+P0-99 Ship Stage MR/PR 创建升级：CLI 优先（gh / glab）实际创建 MR · URL 兜底（CLI 不可用 / 失败 / gitee / bitbucket / unknown）。**用户实战诉求**：「ship 阶段优先使用 glab 或 gh 创建好 MR 在给用户 MR 或 PR 地址 · 如果环境不满足 · 提示用户处理环境问题 · 并使用 MR 创建链接兜底」。

### P0-99：Ship Stage MR/PR 创建（CLI 优先 + URL 兜底）

- 触发：用户实战诉求「优先用 CLI 实际创建 MR · 把真实 URL 给用户」（不是让用户再点一次 create 链接）
- 设计哲学：**实际创建 > 创建链接**。优先 Tier 1 CLI 实际创建 → state.ship.mr_url 是真实 MR URL；CLI 不可用时 Tier 2 URL 兜底（保留现有行为）；失败时**必须诊断 + 告知用户 + 给出可执行的环境配置指令** · 禁止静默降级。
- 核心改动：
  - **P0-99-1. `stages/ship-stage.md` Step 2.3 重构为 CLI 优先 + URL 兜底**：
    - § 2.3.1 Tier 1：CLI 优先创建（gh / glab）
      - github → `gh pr create --base {merge_target} --head {feature_branch} --fill`
      - gitlab/gitlab-self-hosted → `glab mr create --target-branch ... --source-branch ... --fill`
      - gitee/bitbucket/unknown → 直接 Tier 2 URL 兜底
      - 流程：`command -v {cli}` → `{cli} auth status` → 执行命令 → 解析 stdout MR URL → state.ship.mr_url
      - 失败诊断分类：command not found / auth 失败（401）/ 已存在同分支 MR（422）/ target_branch 不存在（404）/ 网络 5xx / 其他 stderr
    - § 2.3.2 Tier 2：URL 兜底（保留现有行为）· 标注 mr_creation_method=url-fallback
  - **P0-99-2. `stages/ship-stage.md` state.json schema 加新字段**：
    - `mr_url`：CLI 实际创建的 MR/PR URL（CLI 成功时）· null 当走 URL 兜底
    - `mr_create_url`：URL 兜底链接（CLI 不可用时）· null 当 CLI 成功
    - `mr_creation_method` enum：`cli-gh` / `cli-glab` / `url-fallback` / `unknown-platform`
    - Done 判据：`mr_url` 或 `mr_create_url` 至少一个非空
  - **P0-99-3. 第一段报告模板加变体 A/B**：
    - 变体 A（CLI 成功）：「✅ MR/PR 已创建（{cli-gh / cli-glab}）」+ {mr_url}
    - 变体 B（URL 兜底）：「🔗 MR/PR 创建链接（请手动点击）」+ {mr_create_url} + ⚠️ 环境配置建议（gh/glab install + login）
  - **P0-99-4. `roles/pmo-pm-acceptance-ship.md` § 五 Step 2 同步**：补充 v7.3.10+P0-99 CLI 优先 + URL 兜底分支描述
  - **P0-99-5. ship-stage.md 反模式加 1 条**：「CLI 失败静默降级到 URL 兜底（不告知用户）→ 🔴 禁止」
  - **P0-99-6. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-98 → 7.3.10+P0-99）
- **核心收益**：
  - GitHub / GitLab 用户：CLI 配置好后 PMO 直接实际创建 MR/PR · 用户拿到真实 URL（不用手动点击）
  - CLI 不可用：显式提示用户安装 + login（gh auth login / glab auth login）· URL 兜底保证流程不阻塞
  - 失败诊断硬规则：禁止静默降级 · 用户始终知道发生了什么 + 怎么处理
- **加 1 删 1 元规则核算**：
  - **加**：Step 2.3 重构为 2 层（~85 行）+ 报告模板变体 A/B（~50 行）+ pmo-pm-acceptance-ship 同步（~10 行）+ schema 字段（~3 行）= ~148 行
  - **删**：原 Step 2.3 单层 URL 生成（~15 行）+ 单一报告模板（~25 行）= ~40 行
  - **净加 ~108 行**（行为升级 · 必要成本）
- 不动:
  - URL 兜底逻辑（保留作为 Tier 2 · 平台无 CLI 时的唯一路径）
  - target_branch 必含硬规则（v7.3.10+P0-80 实战补强）· 仍然适用于 URL 兜底
  - 第二段 finalize 逻辑（不动 · 与 MR/PR 创建方式无关）
- 影响面：2 个文件改动（ship-stage.md 大改 / pmo-pm-acceptance-ship.md 小改）+ 元数据 2 个（SKILL.md / init-stage.md）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：ship-stage.md Step 2.3 含 Tier 1/2 双层 + state.json schema 含 mr_url/mr_creation_method
  - 实战验证：下次 Ship 时用户应看到「✅ MR/PR 已创建（cli-gh）」+ 真实 URL（如 github.com/owner/repo/pull/123）· 而非 create URL（compare/...）

---

## v7.3.10 + P0-98

> v7.3.10+P0-98 silent execution 硬规则强化。**实战 case 触发**：用户「看下 curl 报 502 ……」· PMO 输出 8 段框架仪式 + 思考链 trace（init/triage 入口仪式声明 / SKILL_VERSION 校验跳过 banner / Step 1.5 标题 / 用户消息 echo / 关键词命中 trace / → 轻型意图路由叙事 / Step 1.6 Pull 路径执行 / 按需直查计划叙事 / 找到核心链路进度叙事）才开始 grep 实际代码。

### P0-98：framework 仪式叙事 / Step 头 / 思考链播报禁止（silent execution 强化）

- 触发：用户实战反馈「这些预期不要输出 · 直接做就行 · 输出有用的信息」· 现有 standards/output-tiers.md 4 类反模式不覆盖此场景。
- 设计哲学：**默认行为 = 静默执行**。框架内部状态（步骤号 / 路由判定 / 缓存命中 / 关键词匹配）→ 全部走 state.json + 工具调用 · 不在主对话渲染。主对话只有 3 类输出：① 实际答案（用户问什么答什么）② 决策点（⏸️ 暂停模板）③ 异常 / verdict。
- 核心改动：
  - **P0-98-1. `standards/output-tiers.md` 加反模式 5「框架仪式叙事 / Step 头 / 思考链播报」**：
    - 引实战 case + 8 类禁止输出（入口仪式 / Step 头 / 缓存命中 banner / 用户消息复述 / 关键词命中 trace / 路由决策叙事 / 计划进度叙事 / 工具调用前缀解释）
    - 加 silent execution 原则（默认静默 · 主对话仅 3 类输出）
  - **P0-98-2. `stages/init-stage.md` 缓存命中静默**：
    - L188 「⚡ CLAUDE.md 校验跳过（teamwork_version={VERSION} 命中缓存）」改为**不输出任何 banner**
    - 命中是默认 · 用户不需知道 · 走默认 fast path 直接做事
  - **P0-98-3. `stages/triage-stage.md` Step 1.5/1.6 silent execution 硬规则**：
    - Step 1.5 加禁止动作清单（Step 标题 / 用户消息 echo / 关键词 trace / 路由叙事）
    - Step 1.6 加 silent execution 硬规则（直接 grep / 中间过程不输出 / 直接答案 + 跟进引导一句话）
  - **P0-98-4. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-97 → 7.3.10+P0-98）
- **核心收益**：
  - 把"应该静默"的内容从"建议"变成 standards/output-tiers.md § 反模式 5 + 各 stage spec 内的硬规则
  - 实战 case 同样问题 · v7.3.10+P0-98 起 PMO 输出从 8 段叙事 → 1 段实际答案
- **加 1 删 1 元规则核算**：
  - **加**：output-tiers.md 反模式 5 段（~50 行）+ init-stage 静默说明（~5 行）+ triage Step 1.5/1.6 silent rules（~25 行）= ~80 行
  - **删**：init-stage 旧 banner 输出指令（~1 行）= ~1 行
  - **净加 ~79 行**（硬规则强化 · 必要成本）
- 不动:
  - 任何 role / sub-file（不需要全扩散 · 单源在 standards/output-tiers.md + 关键 stage spec）
  - 其他 stage spec（plan / blueprint / dev / review / test / ship）· 它们已 cite output-tiers.md
- 影响面：3 个文件改动（output-tiers.md / init-stage.md / triage-stage.md）+ 元数据 2 个（SKILL.md / init-stage.md SKILL_VERSION）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：grep "Step 1\.5：意图轻重分流" 主对话日志 应 0 命中（除 stage spec 自身）
  - 实战验证：下次用户「看下 X」类轻型问题 · PMO 应直接 grep + 给答案 · 不再输出 8 段仪式
- 设计意图：现有 output-tiers.md 的 4 类反模式偏重"履职报告体感"和"state.json 复述"· 但没覆盖"silent execution"维度——即"做事过程"不应在主对话播报。本 patch 把这条原则补齐。

---

## v7.3.10 + P0-97（🎉 Wave 4 收官）

> v7.3.10+P0-97 评审规范分层规范化 · **Wave 4 收官**：抽 5 段（PMO 状态报告 + 智能触发 + Test 前置 + 知识库更新 + review-log 管理）合并到 pmo-reporting.md。**pmo.md 759 → 477 行**（净删 ~282 行 · Wave 4 累计 **~1337 行净删** · 99% 进度向 ~500 cap 目标已达成 🎯）。

### P0-97：pmo.md 瘦身 Phase 5（Wave 4 收官）

- 触发：P0-96（Wave 4 Phase 4）完成后 · 推进 Wave 4 Phase 5 抽最后一组主题相关段（PMO 操作产物五件套）。
- 设计哲学：5 段都是"PMO 日常操作产物"主题（状态报告 + 智能触发 + Test 前置 + 知识库 + review-log）· 合并到一个 sub-file pmo-reporting.md · 用一个综合短指针指向 sub-file 四段。
- 核心改动：
  - **P0-97-1. 新建 `roles/pmo-reporting.md`**（278 行 ≤ 300 ✅）：
    - 4 段：§ 一 PMO 状态报告 + 智能触发规则（PMO 摘要触发时机 + 阶段完成摘要格式 + 阶段流转同步硬规则）/ § 二 Test Stage 前置确认（Review DONE 后 ⏸️ 立即/延后/跳过 + 延后批次追踪）/ § 三 本地知识库更新（功能/Bugfix 完成后判断更新 KNOWLEDGE.md）/ § 四 review-log.jsonl 管理（PMO 4 项核心职责）
    - 历史源流：v7.3.2 加 review-log → v7.3.3 加耗时度量 → v7.3.10+P0-30 加问题排查规则 → v7.3.10+P0-56 单源化 review-log → +P0-97 五段合并抽出
  - **P0-97-2. `roles/pmo.md` 删 5 段 + 加综合短指针**（759 → 477 行 · 净删 ~282 行）：
    - 反序删（保留 line number）：L720-727 review-log（~8）/ L633-718 知识库（~86）/ L482-578 Test 前置（~97）/ L377-480 状态报告 + 智能触发（~104）= 总删 ~295 行
    - 替为一个 14 行综合短指针（cite roles/pmo-reporting.md 四段 § 一/二/三/四）+ 清理散落空行
  - **P0-97-3. 全框架 cite 切换**：
    - `agents/README.md` roles/ 目录索引加 pmo-reporting.md 条目
  - **P0-97-4. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-96 → 7.3.10+P0-97）
- **P0-79 元规则触发评估**：
  - roles/pmo-reporting.md = 278 行 ≤ 300 ✅
  - **roles/pmo.md = 477 行（>300 但接近目标 ~500 cap · 仅 Wave 4 收官状态）**
- **加 1 删 1 元规则核算**：
  - **加**：roles/pmo-reporting.md（278 行）+ pmo.md 综合短指针（~14 行）+ cite 微改（~2 行）= ~294 行
  - **删**：pmo.md 五段（~295 行）+ 散落空行清理（~3 行）= ~298 行
  - **净删 ~4 行**（cap 推进 + 操作产物 spec 单源化 · 接近平衡）
  - **核心收益**：
    - **pmo.md 离 ~500 cap 目标已达成（477 行 · 在 cap buffer 内）**
    - PMO 报告 + 操作产物（5 段）合并为一个权威源 · 日常操作集中
    - **Wave 4 整体收官 · 累计净删 ~1337 行**（1814 → 477）

---

## 🎉 Wave 4 整体总结（P0-93 ~ P0-97 · 5 patches 完成）

**目标达成**：pmo.md **1814 → 477 行**（净删 **1337 行** · 74% 减重）· 接近 ~500 cap 目标 ✅

| Phase | Patch | 抽 sub-file | 净删 | pmo.md 行数 | 累计 |
|-------|-------|-------------|------|-------------|------|
| ✅ Phase 1 | P0-93 | pmo-pm-acceptance-ship + pmo-external-orchestration | ~400 | 1814 → 1415 | 22% |
| ✅ Phase 2 | P0-94 | pmo-auto-mode | ~184 | 1415 → 1231 | 32% |
| ✅ Phase 3 | P0-95 | pmo-cross-project | ~213 | 1231 → 1018 | 44% |
| ✅ Phase 4 | P0-96 | pmo-state-mgmt | ~259 | 1018 → 759 | 58% |
| ✅ Phase 5 | P0-97 | pmo-reporting | ~282 | 759 → 477 | **74% 减重 / 99% cap 进度** |

**当前 PMO 矩阵全景（Wave 4 终态）**：
```
roles/pmo.md (477) [Wave 4 收官 · 接近 ~500 目标]
├── pmo-pm-acceptance-ship.md (261) [P0-93]
├── pmo-external-orchestration.md (212) [P0-93]
├── pmo-auto-mode.md (228) [P0-94]
├── pmo-cross-project.md (251) [P0-95]
├── pmo-state-mgmt.md (298) [P0-96]
└── pmo-reporting.md (278) [P0-97]
```

**评审规范分层规范化项目（Wave 1 + 2 + 3 + 4 全部完成）整体总结**：
- ✅ **Wave 1**（P0-85）：基础设施（review-verdict + review-scope 双单源）
- ✅ **Wave 2**（P0-86）：架构师独立化 peer-level role
- ✅ **Wave 3**（P0-87 ~ P0-92 · 6 patches）：6 role 4 段重构 + sub-file 化
- ✅ **Wave 4**（P0-93 ~ P0-97 · 5 patches）：pmo.md 重点瘦身 1814 → 477 行

**累计成果**（Wave 1-4 合并）：
- 7 主 role 文件（architect/qa/rd/pm/designer/external/product-lead/pmo）全部 4 段对齐
- 13 sub-file 全部 ≤ 300 cap：
  - 架构师三件套：architect(126) + architect-tech-review(230) + architect-cr(261)
  - QA 三件套：qa(196) + qa-tc-review(168) + qa-cr(204)
  - PM 二件套：pm(291) + pm-prd-review(181)
  - PL 二件套：product-lead(235) + product-lead-change-mgmt(152)
  - PMO 七件套（Wave 4）：pmo(477) + pmo-pm-acceptance-ship(261) + pmo-external-orchestration(212) + pmo-auto-mode(228) + pmo-cross-project(251) + pmo-state-mgmt(298) + pmo-reporting(278)
  - 单文件：rd(232) / designer(209) / external-reviewer(234)
- 大文件瘦身累计：review-stage 826→384（-442）· qa 359→196（-163）· rd 642→232（-410）· pm 463→291（-172）· product-lead 382→235（-147）· **pmo 1814→477（-1337）**= **总瘦身 ~2671 行**
- 风格 C 设计完整落地："role 管角色契约 + 评审视角 + 职能视角 / stage 管调度 + scope + 循环 / sub-file 装详规范 + 操作产物 / standards 装跨切规则"

**后续可选方向**：
- Wave 5（可选）：pmo.md 4 段重构（决策边界 / 用户质疑 / 跨项目协调 / Goal-Plan 调度 / 问题排查 / Bug 流程 等剩余段整合到 4 段结构）· 进一步压缩到 ~350 行
- pmo-reporting.md 等 sub-file 局部精简（cap buffer 紧逼区文件）

---

## v7.3.10 + P0-96

> v7.3.10+P0-96 评审规范分层规范化 · **Wave 4 Phase 4**：抽 3 段（路径路由 + state.json 维护 + 自下而上升级评估）合并到 pmo-state-mgmt.md。**pmo.md 1018 → 759 行**（净删 ~259 行 · Wave 4 累计 ~1055 行 / 58% 进度向 ~500 cap）。

### P0-96：pmo.md 瘦身 Phase 4（Wave 4）

- 触发：P0-95（Wave 4 Phase 3）完成后 · 推进 Wave 4 Phase 4 抽下一组主题相关段（状态机/数据维护三件套）。
- 设计哲学：3 段都是"PMO 数据/状态维护"主题（路径路由 + state.json + 升级评估）· 合并到一个 sub-file · 用一个综合短指针指向 sub-file 三段。
- 核心改动：
  - **P0-96-1. 新建 `roles/pmo-state-mgmt.md`**（298 行 ≤ 300 ✅ 仅余 2 行 buffer）：
    - 3 段：§ 一 PMO 产物路径权威路由（v7.3.10+P0-41 · 路由计算 / 历史兼容 / 校验时机 / 失败输出格式）/ § 二 state.json 状态机维护规范（v7.3.2 / R3 访问模式 P0-23 / 增量更新 P0-52 / Compact 恢复 / 与现有文件关系）/ § 三 自下而上影响升级评估（PM/RD 标记上游 → PMO 评估升级路径 4 层）
    - 历史源流：v7.3.2 引入 state.json → P0-23 R3 访问模式 → P0-41 路径路由 → P0-52 增量更新 → +P0-96 三段合并抽出
  - **P0-96-2. `roles/pmo.md` 删 3 段 + 加综合短指针**（1018 → 759 行 · 净删 ~259 行）：
    - 反序删（保留 line number）：L365-439 升级评估（~75）/ L242-363 state.json 维护（~122）/ L29-102 路径路由（~74）= 总删 ~271 行
    - 替为一个 12 行综合短指针（cite roles/pmo-state-mgmt.md 三段 § 一/二/三）· 实际净删 259 行
  - **P0-96-3. 全框架 cite 切换**：
    - `TEMPLATES.md` L49 cite "roles/pmo.md § state.json 更新优先用 patch 脚本" → "roles/pmo-state-mgmt.md § 2.5"
    - `standards/prompt-cache.md` L154 cite "roles/pmo.md" 改 → "roles/pmo-state-mgmt.md § 2.4"
    - `agents/README.md` roles/ 目录索引加 pmo-state-mgmt.md 条目
  - **P0-96-4. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-95 → 7.3.10+P0-96）
- **P0-79 元规则触发评估**：
  - roles/pmo-state-mgmt.md = 298 行 ≤ 300 ✅（仅余 2 行 · 进入紧逼区）
  - roles/pmo.md = 759 行（>300 · Wave 4 累计抽 ~1055 行 · 58% 进度）
- **加 1 删 1 元规则核算**：
  - **加**：roles/pmo-state-mgmt.md（298 行）+ pmo.md 综合短指针（~12 行）+ cite 微改（~5 行）= ~315 行
  - **删**：pmo.md 三段（~271 行）+ cite 替换（~5 行）= ~276 行
  - **净加 ~39 行**（cap 推进 + 数据/状态维护 spec 单源化）
  - **核心收益**：
    - pmo.md 离 ~500 cap 又近了 ~259 行（累计 58% 进度）
    - 状态机维护（路径路由 + state.json + 升级评估）三段合并为一个权威源 · 数据相关职责集中
- 不动:
  - 任何 stage 文件（仅微改 TEMPLATES.md / prompt-cache.md / agents/README.md cite）
  - **pmo.md 其他段**（决策边界 / 用户质疑响应 / Bug 流程 / Test 前置 / KNOWLEDGE 扫描 / Goal-Plan 调度 / 完成报告 / 反模式 等留 Wave 4 Phase 5 一并处理）
- 影响面：1 个新建文件（pmo-state-mgmt.md）+ pmo.md 大改（1018 → 759）+ 3 个文件 cite 微改（TEMPLATES.md / prompt-cache.md / agents/README.md）+ 元数据 2 个（SKILL.md / init-stage.md）+ CHANGELOG entry
- **Wave 4 路线图更新**：
  - ✅ Phase 1（P0-93）：抽 PM 验收+Ship + 外部模型调度（净删 ~400 · pmo.md 1814 → 1415）
  - ✅ Phase 2（P0-94）：抽 auto 模式（净删 ~184 · 1415 → 1231）
  - ✅ Phase 3（P0-95）：抽 跨项目协调（净删 ~213 · 1231 → 1018）
  - ✅ Phase 4（P0-96）：抽 路径路由 + state.json + 升级评估（净删 ~259 · 1018 → 759）
  - ⏳ Phase 5（P0-97）：pmo.md 4 段重构 + 最终精简（决策边界 / 用户质疑 / Bug / Test / KNOWLEDGE / Goal-Plan 调度 / 完成报告 / 反模式 整合）→ 目标 ~500-600 行

---

## v7.3.10 + P0-95

> v7.3.10+P0-95 评审规范分层规范化 · **Wave 4 Phase 3**：抽 3 段（跨项目依赖识别 + 跨子项目需求拆分 + 变更归属检查）到 pmo-cross-project.md。**pmo.md 1231 → 1018 行**（净删 ~213 行 · Wave 4 累计 ~796 行 / 44% 进度向 ~500 cap）。

### P0-95：pmo.md 瘦身 Phase 3（Wave 4）

- 触发：P0-94（Wave 4 Phase 2）完成后 · 推进 Wave 4 Phase 3 抽下一组主题相关段（跨项目协调三件套）。
- 设计哲学：3 段主题相关（场景 A 上游依赖 + 场景 B 跨子项目拆分 + 变更归属检查 P0-33）合并到一个 sub-file · 不分 3 个独立 sub-file（避免文件过度碎片化）· 用一个综合短指针指向 sub-file 三段。
- 核心改动：
  - **P0-95-1. 新建 `roles/pmo-cross-project.md`**（251 行 ≤ 300 ✅）：
    - 3 段：跨项目依赖识别（场景 A · 7 子段含触发 / 流程 / 硬规则）/ 跨子项目需求拆分（场景 B · 拆分流程 + 方案模板 + 完成报告）/ 变更归属检查（5 步流程 + 阻塞决策矩阵 + 逃生舱 + 硬规则）
    - 历史源流：v7.3.9+P0-8 加跨项目依赖识别 → v7.3.10+P0-26 整合到 triage Step 6 → v7.3.10+P0-33 加变更归属检查（Step 6.5）→ +P0-95 抽出
  - **P0-95-2. `roles/pmo.md` 删 3 段 + 加综合短指针**（1231 → 1018 行 · 净删 ~213 行）：
    - L441-496 跨项目依赖识别（~56 行）
    - L598-688 跨子项目需求拆分（~91 行）
    - L690-764 变更归属检查（~75 行）
    - 总删 ~222 行 · 替为一个 9 行综合短指针（cite roles/pmo-cross-project.md 三段 § 一/二/三）· 实际净删 213 行
  - **P0-95-3. 全框架 cite 切换**：
    - `templates/dependency.md` L24 cite "roles/pmo.md § 跨项目依赖识别" → "roles/pmo-cross-project.md § 一"
    - `agents/README.md` roles/ 目录索引加 pmo-cross-project.md 条目
  - **P0-95-4. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-94 → 7.3.10+P0-95）
- **P0-79 元规则触发评估**：
  - roles/pmo-cross-project.md = 251 行 ≤ 300 ✅
  - roles/pmo.md = 1018 行（>300 · 进度 44% · Wave 4 累计抽 ~796 行）
- **加 1 删 1 元规则核算**：
  - **加**：roles/pmo-cross-project.md（251 行）+ pmo.md 综合短指针（~9 行）+ cite 微改（~5 行）= ~265 行
  - **删**：pmo.md 三段（~222 行）+ cite 替换中节省（~5 行）= ~227 行
  - **净加 ~38 行**（cap 推进 + 跨项目调度 spec 单源化）
  - **核心收益**：
    - pmo.md 离 ~500 cap 又近了 ~213 行（累计 44% 进度）
    - 跨项目协调（场景 A + 场景 B + 变更归属）三段合并为一个权威源 · 主题集中
- 不动:
  - 任何 stage 文件（仅微改 templates/dependency.md cite）
  - **pmo.md 其他段**（路径路由 / 决策边界 / state.json 维护 / Bug 流程 / Test 前置 / KNOWLEDGE 扫描 等留 Wave 4 后续 Phase）
- 影响面：1 个新建文件（pmo-cross-project.md）+ pmo.md 大改（1231 → 1018）+ 2 个文件 cite 微改（templates/dependency.md / agents/README.md）+ 元数据 2 个（SKILL.md / init-stage.md SKILL_VERSION）+ CHANGELOG entry
- **Wave 4 路线图更新**：
  - ✅ Phase 1（P0-93）：抽 PM 验收+Ship + 外部模型调度（净删 ~400 行 · pmo.md 1814 → 1415）
  - ✅ Phase 2（P0-94）：抽 auto 模式 + 自动推进规则（净删 ~184 行 · pmo.md 1415 → 1231）
  - ✅ Phase 3（P0-95）：抽 跨项目依赖 + 跨子项目拆分 + 变更归属（净删 ~213 行 · pmo.md 1231 → 1018）
  - ⏳ Phase 4（P0-96）：抽 state.json 维护 + 自下而上升级 + 路径路由（~250 行）→ pmo-state-mgmt.md
  - ⏳ Phase 5（P0-97）：pmo.md 4 段重构 + 最终精简 → ~500-600 行

---

## v7.3.10 + P0-94

> v7.3.10+P0-94 评审规范分层规范化 · **Wave 4 Phase 2**：抽 PMO 自动推进规则 + auto 模式（HITL/AFK 二分）到 sub-file。**pmo.md 1415 → 1231 行**（净删 ~184 行 · Wave 4 累计 583 行 / 32% 进度向 ~500 cap）。

### P0-94：pmo.md 瘦身 Phase 2（Wave 4）

- 触发：P0-93（Wave 4 Phase 1）完成后 · 推进 Wave 4 Phase 2 抽下一个独立大段。
- 设计哲学：沿 P0-93 增量 sub-file 模式 · 抽 auto 模式段（自动推进 + AUTO_MODE/HITL/AFK ~192 行）独立 sub-file。
- 核心改动：
  - **P0-94-1. 新建 `roles/pmo-auto-mode.md`**（228 行 ≤ 300 ✅）：
    - 9 段：自动推进规则 / auto mode 判定 / 元规则意图承载豁免 P0-11-A / AFK 暂停点 / Browser E2E 默认跳过 P0-11-B / HITL 暂停点 / 跳过日志 / 强制保留模板 / 自检清单 / 运行时关闭
    - 历史源流：v7.3.9+P0-11 引入 AUTO_MODE → +P0-11-A 修订意图承载豁免 → +P0-11-B Browser E2E 默认跳过 → v7.3.10+P0-76 mode 字段化 HITL/AFK → +P0-94 抽出
  - **P0-94-2. `roles/pmo.md` 删 auto 模式段 + 加短指针**（1415 → 1231 行 · 净删 ~184 行）：
    - L1051-1242 自动推进规则 + auto 模式（~192 行）→ 替为 8 行短指针（cite roles/pmo-auto-mode.md）
  - **P0-94-3. 全框架 cite 切换**：
    - `rules/flow-transitions.md` L87 cite "pmo.md「⚡ auto 模式...」章节" → "pmo-auto-mode.md"（v7.3.10+P0-94 抽出）
    - `stages/init-stage.md` L133 cite "pmo.md「⚡ auto 模式...」章节" → "pmo-auto-mode.md"
    - `agents/README.md` roles/ 目录索引加 pmo-auto-mode.md 条目
  - **P0-94-4. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-93 → 7.3.10+P0-94）
- **P0-79 元规则触发评估**：
  - roles/pmo-auto-mode.md = 228 行 ≤ 300 ✅
  - roles/pmo.md = 1231 行（>300 · 进度 32% · Wave 4 累计抽 ~583 行）
- **加 1 删 1 元规则核算**：
  - **加**：roles/pmo-auto-mode.md（228 行）+ pmo.md 短指针（~10 行）+ cite 微改（~5 行）= ~243 行
  - **删**：pmo.md auto 模式段（~192 行）+ cite 替换中节省（~5 行）= ~197 行
  - **净加 ~46 行**（cap 推进 + auto 模式调度 spec 单源化）
  - **核心收益**：
    - pmo.md 离 ~500 cap 又近了 ~184 行（累计 32% 进度）
    - auto 模式（HITL/AFK 二分）从 PMO 文件深处提升为独立权威源 · flow-transitions.md / init-stage.md 直接 cite
- 不动:
  - 任何 stage 文件（仅微改 init-stage / flow-transitions cite）
  - templates / standards 其他文件
  - **pmo.md 其他段**（路径路由 / 决策边界 / state.json 维护 / 跨项目 / 变更归属 / Bug 流程 / Test 前置 等留 Wave 4 后续 Phase）
- 影响面：1 个新建文件（pmo-auto-mode.md）+ pmo.md 大改（1415 → 1231）+ 3 个文件 cite 微改（flow-transitions.md / init-stage.md / agents/README.md）+ 元数据 2 个（SKILL.md / init-stage.md SKILL_VERSION）+ CHANGELOG entry
- 后续验证：立即可验证：sub-file ≤ 300 cap · pmo.md 1231 行 · cite 全可达
- **Wave 4 路线图更新**：
  - ✅ Phase 1（P0-93）：抽 PM 验收+Ship + 外部模型调度（净删 ~400 行 · pmo.md 1814 → 1415）
  - ✅ Phase 2（P0-94）：抽 auto 模式 + 自动推进规则（净删 ~184 行 · pmo.md 1415 → 1231）
  - ⏳ Phase 3（P0-95）：抽 跨子项目需求拆分 + 跨项目依赖识别 + 变更归属检查（~225 行）→ pmo-cross-project.md
  - ⏳ Phase 4（P0-96）：抽 state.json 维护 + 自下而上升级评估 + 路径路由（~250 行）→ pmo-state-mgmt.md
  - ⏳ Phase 5（P0-97）：pmo.md 4 段重构 + 最终精简 → ~500-600 行

---

## v7.3.10 + P0-93

> v7.3.10+P0-93 评审规范分层规范化 · **Wave 4 启动 Phase 1**：pmo.md 重点瘦身第一阶段。抽 2 个最大段（PM 验收+Ship + 外部模型评审调度）到 sub-file。**pmo.md 1814 → 1415 行**（净删 ~400 行）· 距 ~500 cap 还需 Wave 4 后续 Phase 推进。

### P0-93：pmo.md 瘦身 Phase 1（Wave 4 启动）

- 触发：P0-92 完成 6 role 4 段重构（Wave 3 收官）后 · 启动 Wave 4 唯一未达 cap 的 pmo.md（1814 行）的瘦身。
- 设计哲学：增量抽 sub-file 模式（沿 P0-87/88/90/91/92）· 优先抽最大块（PM 验收+Ship ~236 行 + 外部模型调度 ~181 行）· 累计净删 ~400 行。
- 核心改动：
  - **P0-93-1. 新建 `roles/pmo-pm-acceptance-ship.md`**（261 行 ≤ 300 ✅）：
    - 5 段：设计目标（v7.3.10+P0-15 MR 模式）/ PM 验收暂停点（流程 + 模板 + 选 1/2/3 处理）/ commit 产物清单 / commit message 模板 / Ship Stage PMO 职责速查（双段 v7.3.10+P0-29 + finalize push merge_target v7.3.10+P0-32 + 红线 #1 边界）
    - 历史源流：v7.3.10+P0-15 MR 模式 → +P0-29 双段 → +P0-32 finalize push → +P0-93 抽出
  - **P0-93-2. 新建 `roles/pmo-external-orchestration.md`**（212 行 ≤ 300 ✅）：
    - 10 段：设计变化（v7.3.10+P0-38 重构）/ 影响范围 / Step 1-6（PMO 直接判定 / 渲染判定段 / 智能推荐表 / 决策项呈现 / state.json 写入 / 失败降级 E3）/ 兼容性 fallback / 硬规则
    - 适配 P0-83（删 Goal-Plan external · 仅 Blueprint/Review 适用）· 推荐表从 3 列改 2 列
  - **P0-93-3. `roles/pmo.md` 删两段 + 加短指针**（1814 → 1415 行 · 净删 ~400 行）：
    - L498-678 外部模型评审调度（~181 行）→ 替为 8 行短指针（cite roles/pmo-external-orchestration.md）
    - L1430-1665 PM 验收 + Ship Stage（~236 行）→ 替为 8 行短指针（cite roles/pmo-pm-acceptance-ship.md）
  - **P0-93-4. 全框架 cite 切换**：
    - `stages/ship-stage.md` L60 必读文件 + L86 入口 Read 顺序：cite roles/pmo.md 改加 roles/pmo-pm-acceptance-ship.md
    - `templates/external-cross-review.md` L54 cite "pmo.md §🌐 外部模型交叉评审开关决策" → "roles/pmo-external-orchestration.md"
    - `agents/README.md` roles/ 目录索引加 pmo-pm-acceptance-ship.md / pmo-external-orchestration.md 条目（pmo.md 标"瘦身中 · Wave 4 ongoing"）
  - **P0-93-5. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-92 → 7.3.10+P0-93）
- **P0-79 元规则触发评估**：
  - roles/pmo-pm-acceptance-ship.md = 261 行 ≤ 300 ✅
  - roles/pmo-external-orchestration.md = 212 行 ≤ 300 ✅
  - roles/pmo.md = 1415 行（>300 · 进度 22% 抽完 · 还需 Wave 4 后续 Phase 推进到 ~500）
- **加 1 删 1 元规则核算**：
  - **加**：roles/pmo-pm-acceptance-ship.md（261 行）+ roles/pmo-external-orchestration.md（212 行）+ pmo.md 短指针（~25 行）= ~498 行
  - **删**：pmo.md PM 验收+Ship（~236 行）+ pmo.md 外部模型（~181 行）= ~417 行
  - **净加 ~80 行**（重构主要价值在 cap 推进 + 调度 spec 单源化 · 可读性大幅提升）
  - **核心收益**：
    - pmo.md 离 ~500 cap 又近了 ~400 行（22% 进度）
    - PM 验收 + Ship 调度规范从"角色文件深处"提升为独立权威源 · ship-stage.md 直接 cite
    - external 评审调度 sub-file + external-reviewer.md 角色契约形成清晰双层结构
- 与已有规则的关系：
  - **`stages/ship-stage.md` / `stages/pm-acceptance-stage.md`**：保留 · Stage 调度契约不变 · 必读清单更新 cite
  - **`roles/external-reviewer.md`**：保留 · 角色契约不变 · pmo-external-orchestration.md 是 PMO 调度 spec
  - **`standards/external-model.md`**：保留 · 异质性单源不变
- 不动:
  - 任何 stage 文件（ship-stage.md / pm-acceptance-stage.md 仅微改 cite）
  - templates / standards 其他文件
  - 其他 7 role 文件（Wave 3 已完成）
  - **pmo.md 其他段**（路径路由 / 决策边界 / state.json 维护 / 跨项目 / 变更归属 / Bug 流程 / Test 前置 / auto 模式 等留 Wave 4 后续 Phase）
- 影响面：2 个新建文件（pmo-pm-acceptance-ship.md / pmo-external-orchestration.md）+ pmo.md 大改（1814 → 1415）+ 4 个文件 cite 微改（ship-stage.md ×2 / external-cross-review.md / agents/README.md）+ 元数据 2 个（SKILL.md / init-stage.md）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：2 sub-file 存在 + ≤ 300 cap · pmo.md 1415 行 · cite 全可达
  - Wave 4 Phase 2 时验证：继续抽 auto 模式 + 自动推进规则（~190 行）等
- **Wave 4 路线图**：
  - **Phase 1（P0-93 · 完成）**：抽 PM 验收+Ship + 外部模型调度（净删 ~400 行）
  - **Phase 2（P0-94）**：抽 PMO 自动推进规则 + auto 模式判定（L1170+ ~200 行）→ pmo-auto-mode.md
  - **Phase 3（P0-95）**：抽 跨子项目需求拆分 + 跨项目依赖识别 + 变更归属检查（~225 行）→ pmo-cross-project.md
  - **Phase 4（P0-96）**：抽 state.json 维护 + 自下而上升级评估 + 路径路由（~250 行）→ pmo-state-mgmt.md
  - **Phase 5（P0-97）**：pmo.md 4 段重构 + 最终精简（~500 行）

---

## v7.3.10 + P0-92

> v7.3.10+P0-92 评审规范分层规范化 · 第 3 波**最终阶段**：Designer / External / PL 三 role 4 段重构（合并 patch · 完成 6 role 4 段重构 6/6 🎉）。**Wave 3 收官**。pl 抽 sub-file（变更管理段）。

### P0-92：6 role 4 段重构收官（Wave 3 第 6 阶段）

- 触发：P0-91 完成 PM 4 段重构后 · 合并 patch 推进剩余 3 个 role（Designer / External / PL）4 段重构 · 完成 Wave 3 收官。
- 设计哲学：6 role 4 段对齐（angle / qa / rd / pm / designer / external 全部 4 段结构 · 与 architect.md 对称）+ PL 变更管理段抽 sub-file（保 product-lead.md ≤ 300 cap）。
- 核心改动：
  - **P0-92-1. `roles/designer.md` 4 段重构**（129 → 209 行 · ≤ 300 ✅）：
    - 原 6 段（顶部职责 + UI 还原验收 + 反模式 + Goal-Plan PRD 评审 checklist）→ 5 段对齐：
      - § 一：Designer UI/UX 视角 + 与 PM/RD 边界 + 核心原则（HTML 预览强制 / 必须基于现有页面迭代 / 必须覆盖所有状态）
      - § 二：评审职责（Goal-Plan PRD 评审 checklist 归位 + UI Design 自查 + UI 还原验收 · 行为硬规则 + 反模式）
      - § 三：职能职责（UI.md + preview/*.html + 全景维护 + UI 还原验收 + 验收声明 + 交接点 · 行为硬规则 + 反模式）
      - § 四：Stage 速查（10 stage × Designer 参与度）
      - § 五：协同（Designer ↔ PM / RD / QA / PMO）
  - **P0-92-2. `roles/external-reviewer.md` 4 段重构**（219 → 234 行 · ≤ 300 ✅）：
    - 原 8 段结构（角色定位 / 可用性来源 / 通用评审契约 / context 来源 / PMO 实例化 / 失败降级 / 与其他角色关系 / 立场独立性强调）→ 5 段对齐：
      - § 一：External 异质模型角色定位 + 唯一不可替代价值 + 异质性核心约束（合并原 § 一 + § 八）
      - § 二：评审职责（评审入口表 / verdict / scope / 立场独立性硬约束 / 评审深度要求 / 输出 schema / 反模式 · 合并原 § 三）
      - § 三：职能职责（无独立产出 + 可用性来源 + PMO 实例化 + 失败降级 · 合并原 § 二 / § 四 / § 五 / § 六）
      - § 四：Stage 速查（External 仅 Blueprint / Review · Goal-Plan v7.3.10+P0-83 删）
      - § 五：协同（External ↔ 其他角色 / 文件 · 合并原 § 七）
  - **P0-92-3. 新建 `roles/product-lead-change-mgmt.md`**（152 行 ≤ 300 ✅）：
    - 抽 product-lead.md L311-381（变更管理段 · CR 状态机 + 6 类影响评估 + 模式二旧新对比 + 编号约定 + ADR 关系 + 待执行变更记录格式）
    - 8 段：设计目标 / 状态机 / PL 职责 / 模式二关系 / 编号约定 / 影响评估格式 / 与 ADR 关系 / 待执行变更记录格式
  - **P0-92-4. `roles/product-lead.md` 4 段重构**（382 → 235 行 · 净删 147 行 · ≤ 300 ✅）：
    - 删变更管理段（抽到 product-lead-change-mgmt.md）
    - 整合 3 模式（引导 / 讨论 / 执行）+ PL 评审角色 + 强制约束 + 与 PL 驱动职责区分到 4 段：
      - § 一：PL 产品方向层 + 与 PM 边界（表格化）+ 核心原则
      - § 二：评审职责（Goal-Plan PRD 业务对齐 checklist · v7.3.10+P0-34 · 含 Feature 类型决策表 + 6 维 + 与驱动者职责区分）
      - § 三：职能职责（3 模式 + 强制约束 + 核心产出 + 反模式 · 大量表格化压缩）
      - § 四：Stage 速查（10 stage × PL 参与度 · 含引导 / 讨论 / 执行 / 变更级 Planning 行）
      - § 五：协同（PL ↔ PM / RD / Architect / PMO）
  - **P0-92-5. ROLES.md / agents/README.md 索引同步**：
    - ROLES.md L11/L13：Designer + PL 描述加 v7.3.10+P0-92 标注
    - PL 描述加 [product-lead-change-mgmt.md](./roles/product-lead-change-mgmt.md) sub-file 链接
    - agents/README.md roles/ 目录索引加 product-lead-change-mgmt.md 条目
  - **P0-92-6. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-91 → 7.3.10+P0-92）
- **P0-79 元规则触发评估**：
  - roles/designer.md = 209 行 ≤ 300 ✅
  - roles/external-reviewer.md = 234 行 ≤ 300 ✅
  - roles/product-lead.md = 235 行 ≤ 300 ✅（修复 382 超 cap）
  - roles/product-lead-change-mgmt.md = 152 行 ≤ 300 ✅（新）
- **加 1 删 1 元规则核算**：
  - **加**：4 段结构表格化 + product-lead-change-mgmt.md 新建（~152 行）+ designer/external 重写（~80 + ~15 行）= ~247 行
  - **删**：product-lead.md 原文（~147 行 · 主要变更管理段移到 sub-file 净删）= ~147 行
  - **净加 ~100 行**（重构主要价值在 4 段一致性 / cap 合规化 / 表格化压缩）
  - **核心收益**：
    - 6 role 4 段重构**全部完成**（architect / qa / rd / pm / designer / external / pl）· 风格 C 设计完整落地
    - 全 7 role 文件 + 7 sub-file 总计 14 个文件 · 全部 ≤ 300 cap ✅
    - PL 变更管理详规范独立 sub-file · pl.md 不再背"角色契约 + CR 详规范"双重身份
- 与已有规则的关系：
  - **`stages/goal-plan-stage.md`**：保留 · 必读清单未变 · 仅 cite 路径间接更新（PL 评审进 PRD-REVIEW.md.reviews[] · cite roles/product-lead.md）
  - **`stages/triage-stage.md`**：保留 · CR / 变更管理 cite product-lead-change-mgmt.md 已添加（如果有 · 暂未发现 active 引用）
  - **`templates/change-request.md`**：保留 · 是 CR 文档模板 · 与 product-lead-change-mgmt.md 互补
- 不动:
  - 任何 stage 文件（goal-plan / blueprint / review / etc 仅 cite 路径）
  - templates / standards 其他文件
  - 其他 role / sub-file（架构师三件套 / QA 三件套 / RD / PM 二件套已完成）
  - **PMO**（pmo.md = 1814 行 · Wave 4 重点瘦身 · 不在本 patch 范围）
- 影响面：3 个文件全文重写（designer.md / external-reviewer.md / product-lead.md）+ 1 新建（product-lead-change-mgmt.md）+ 索引 2 个（ROLES.md / agents/README.md）+ 元数据 2 个（SKILL.md / init-stage.md）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：4 个文件全部 ≤ 300 cap · 4 段结构对齐 architect/qa/rd/pm · cite 全可达
  - Wave 3 进度 6/6 ✅ · 6 role 4 段重构全部完成
  - Wave 4 时验证：pmo.md 瘦身（1814 → ~500 · 拆 4-5 reference 子文件）
- **Wave 3 累积总结（P0-86 ~ P0-92）**：
  - 7 role 文件全部 4 段对齐：architect.md(126) / qa.md(196) / rd.md(232) / pm.md(291) / designer.md(209) / external-reviewer.md(234) / product-lead.md(235) / pmo.md(1814 留 Wave 4)
  - 7 sub-file 全部新建：architect-cr(261) + architect-tech-review(230) / qa-cr(204) + qa-tc-review(168) / pm-prd-review(181) / product-lead-change-mgmt(152)
  - review-stage.md 826 → 384（净删 442）· qa.md 359 → 196（净删 163）· rd.md 642 → 232（净删 410）· pm.md 463 → 291（净删 172）· product-lead.md 382 → 235（净删 147）
  - 风格 C 设计（"role 管角色契约 + 评审视角 + 职能视角 / stage 管调度 + scope + 循环 / sub-file 装详规范 / standards 装跨切规则"）全 6 role 完整落地
- 后续 Wave 计划：
  - **Wave 4：pmo.md 重点瘦身**（1814 → ~500 行 · 拆 4-5 reference 子文件）· 风险最高 · 设计权衡更复杂

---

## v7.3.10 + P0-91

> v7.3.10+P0-91 评审规范分层规范化 · 第 3 波第 5 阶段：PM 4 段重构 + PRD 多角色评审抽 sub-file。**pm.md 463 → 291 行**（净删 172 行）· 拆出 roles/pm-prd-review.md（181 行）· 修复 P0-86/87/88 后遗留的"PRD 技术评审规范段还寄生在 pm.md"。

### P0-91：PM 4 段重构 + PRD 多角色评审独立化（Wave 3 第 5 阶段）

- 触发：P0-90 完成 RD 4 段重构 · 推进 PM 4 段重构。pm.md 463 行 · 含 PRD 技术评审规范段（L294-453, ~160 行）+ 大量散落 hard rules（评审回应 / 对抗自查 / DEFER 收紧 / Feature Planning / Workspace Planning / 中台 PRD 增强）。
- 设计哲学（沿 P0-87/88/89/90 sub-file + 4 段模式）：
  - **PRD 多角色评审详规范** → 独立 sub-file `roles/pm-prd-review.md`（与 pm.md 角色契约分离）
  - **PM 4 段结构**：
    - § 一：PM 产品视角 + 与 PL/QA 边界 + 核心原则（PRD 起草前 Read 代码 P0-73 / 格式权威 P0-7 / 禁 TBD / 埋点强制）
    - § 二：PM 评审职责（PM 主要被评审者 + 回应规则 P0-34 + 对抗自查 P0-34-B + DEFER 收紧 P0-34-A + 评审循环 + PMO 校验）
    - § 三：PM 职能（PRD 起草 + Feature Planning + Workspace Planning + 变更级 Planning + 中台 PRD 增强 + 上游影响检测 + 状态看板）
    - § 四：Stage 速查（11 stage × PM 参与度 · 含 Feature Planning / 变更级 Planning 行）
    - § 五：协同（PM ↔ PL / RD / QA / Designer / External / PMO）
- 核心改动：
  - **P0-91-1. 新建 `roles/pm-prd-review.md`**（181 行 ≤ 300 ✅）：
    - 6 段：角色定位 / 输入文件 / 评审维度（4 角色视角 RD/Designer/QA/PMO + cite role checklist）/ 执行流程 / 输出要求 / 反模式
    - 顶部权威源声明 + cite 回 pm.md + cite review-verdict.md / review-scope.md(prd) + 历史源流（agents/prd-review.md → pm.md → 本文件）
  - **P0-91-2. `roles/pm.md` 全文重写为 4 段结构**（463 → 291 行 · 净删 172 行）：
    - 删 L82-218 散落的 PM 评审回应规则 + 对抗自查 + DEFER 收紧 + 评审循环 → 整合到 § 二、评审职责（结构化 + 表格化）
    - 删 L240-291 Feature Planning + Workspace Planning 段落 → 整合到 § 三、职能职责 § 3.3 + § 3.4
    - 删 L294-453 PRD 技术评审规范段（~160 行）→ 抽到 pm-prd-review.md
    - 删 L455-463 反模式段 → 整合到 § 二.7 + § 三.10 反模式（按评审 / 职能分类）
    - L37-54 上游影响检测 → § 3.7 上游影响检测（精简）
    - L66-78 中台子项目 PRD 增强 → § 3.6 中台子项目 PRD 增强
    - L231-238 状态看板 → § 3.8 状态看板
  - **P0-91-3. 全框架 cite 切换**：
    - `ROLES.md` L12 PM 描述加 [pm-prd-review.md](./roles/pm-prd-review.md) sub-file
    - `stages/goal-plan-stage.md` L36 必读文件清单加 `roles/pm-prd-review.md`
    - `agents/README.md` roles/ 目录索引加 pm-prd-review.md 条目
  - **P0-91-4. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-90 → 7.3.10+P0-91）
- **P0-79 元规则触发评估**：
  - roles/pm-prd-review.md = 181 行 ≤ 300 ✅
  - roles/pm.md = 291 行 ≤ 300 ✅（修复前 463 ❌ → 修复后 ✅ · trim 一次后达标）
- **加 1 删 1 元规则核算**：
  - **加**：roles/pm-prd-review.md（181 行）+ pm.md 4 段重构后（291 行）+ 散落 cite 微改（~5 行）= ~477 行
  - **删**：pm.md 原文（463 行）+ 散落 cite 替换（~5 行）= ~468 行
  - **净加 ~9 行**（基本平衡 ✅）
  - **核心收益**：
    - pm.md 463 → 291 · 不再背"PM 角色 + PRD 多角色评审 spec"双重身份 · 文件回到"PM 角色契约"本职
    - PM sub-file 矩阵：pm.md（291 契约）+ pm-prd-review.md（181 PRD 多角色评审）· 与架构师 + QA 的三件套对称
    - 风格 C 设计在 4 个 role 完整落地（Wave 3 进度 4/6）
- 与已有规则的关系：
  - **`stages/goal-plan-stage.md`**：保留 · 仍是 Goal-Plan Stage 调度 + scope 权威源 · 必读清单加 pm-prd-review.md
  - **`templates/prd.md` PRD-REVIEW frontmatter schema**：保留 · pm-prd-review.md § 5.2 cite 不变
- 不动:
  - 任何 stage 文件（goal-plan-stage.md 仅微调必读清单）
  - templates / standards 其他文件
  - 其他 sub-file（architect-cr/architect-tech-review/qa-cr/qa-tc-review）
  - 其他 2 role（designer / product-lead / external-reviewer / pmo）4 段重构留给 P0-92
- 影响面：1 个新建文件（pm-prd-review.md）+ 4 个文件改动（pm.md 全文重写 / ROLES.md / goal-plan-stage.md / agents/README.md）+ 元数据 2 个（SKILL.md / init-stage.md）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：roles/pm-prd-review.md 存在 · pm.md = 291 行 ≤ 300 · 4 段结构对齐 architect/qa/rd · cite 路径全可达
  - P0-92 时验证：Designer / product-lead / external-reviewer 4 段重构（合并 patch · 这 3 个文件较小）· Wave 3 进度 5/6
- 后续 Wave 计划（**P0-92 / P0-XX**）：
  - **P0-92**：Designer / product-lead / external-reviewer 4 段重构（合并 patch · 完成 6 role 4 段重构）
  - **P0-XX**（Wave 4）：pmo.md 重点瘦身（1814 → ~500 行 · 拆 4-5 reference 子文件 · 风险最高）

---

## v7.3.10 + P0-90

> v7.3.10+P0-90 评审规范分层规范化 · 第 3 波第 4 阶段：RD 4 段重构 + 架构师 Tech Review 抽 sub-file。**rd.md 642 → 232 行**（净删 410 行 🎉）· 拆出 roles/architect-tech-review.md 子文件（230 行）· 修复 P0-86 后遗留的"架构师方案评审规范段还寄生在 rd.md"问题。架构师角色 sub-file 矩阵完整化：契约（115）+ Tech Review（230）+ Code Review（261）。

### P0-90：RD 4 段重构 + 架构师 Tech Review 独立化（Wave 3 第 4 阶段）

- 触发：P0-89 完成 QA 4 段重构后 · 推进 RD 4 段重构。RD 文件 642 行（仅次于 pmo.md 1814）· 含两个架构师段（RD-side overview L55-281 + 完整规范 L380-609）· P0-86 时已声明"架构师方案评审段后续 patch 评估"· P0-87 时声明"P0-87 时与 review-stage.md 大段一并整合到 architect.md"但实际未做 · 本 patch 完成。
- 设计哲学（沿 P0-87/P0-88 sub-file 模式 + P0-89 4 段结构）：
  - **架构师 Tech Review 详规范** → 独立 sub-file `roles/architect-tech-review.md`（与 architect-cr.md 对称）
  - **RD 4 段结构**（角色定位 / 评审职责 / 职能职责 / Stage 速查 + 协同）：
    - § 一：RD 实现层视角 + 与架构师/QA 边界 + 核心原则（TDD / 根因优先 / 格式权威 / 修了 A 必查 BC）
    - § 二：RD 评审职责（Goal-Plan PRD 评审 + 配合接受 Tech/Code Review）· Goal-Plan PRD checklist 归位
    - § 三：RD 职能（TECH 起草 + TDD 开发 + 自查 + Bug 排查报告 + 上游影响检测 + 复杂度判断）
    - § 四：Stage 速查（10 stage × RD 参与度 · 含 Bug 流程行）
    - § 五：协同（RD ↔ 架构师 / QA / external / PM / Designer / PMO）
- 核心改动：
  - **P0-90-1. 新建 `roles/architect-tech-review.md`**（230 行 ≤ 300 ✅）：
    - 6 段：角色定位 / 输入文件 / Review 维度（11 维：需求覆盖 + UI 支撑 + 架构合理性 + 扩展性 + 性能 + 安全 + Schema 同步完整性 + 降级兜底 + API 版本 + 现有架构一致性 + Search-Before-Build）/ 执行流程（8 步） / 输出要求（Review 报告 7 节）/ 反模式 5 条
    - 顶部声明权威源 + cite 回 architect.md + cite review-verdict.md / review-scope.md(blueprint) + 历史源流（agents/arch-tech-review.md → rd.md → 本文件）
  - **P0-90-2. `roles/rd.md` 全文重写为 4 段结构**（642 → 232 行 · 净删 **410 行** 🎉）：
    - 删 L55-281 RD-side overview 段（架构师方案评审 + 架构师 Code Review · 2×100+ 行 inline 内容）→ 替为 § 二的 cite 表
    - 删 L380-609 架构师方案评审规范段（~230 行）→ 抽到 architect-tech-review.md
    - L613-642 Goal-Plan PRD 评审 checklist → 归位到 § 二、评审职责 § 2.4
    - L282-379 Bug 排查报告 → 整合到 § 三、职能职责 § 3.4
    - 上游影响检测 → § 三 § 3.5
    - RD 自查 → § 三 § 3.3
    - 复杂度判断 → § 三 § 3.6
    - 4 段结构对齐 architect.md / qa.md（同 5 H2 + 子段格式）
  - **P0-90-3. 全框架 cite 切换**：
    - `stages/blueprint-stage.md` L66 必读文件清单加 `roles/architect-tech-review.md`
    - `stages/blueprint-stage.md` L216 Process Step 4：cite 改 `roles/architect.md` → `roles/architect-tech-review.md`
    - `standards/backend.md` L639 Schema 链表格 cite 改 `roles/rd.md §架构师方案评审规范` → `roles/architect-tech-review.md`
    - `agents/README.md` L713-720 roles/ 目录索引重写（含全 sub-file 矩阵）
    - `ROLES.md` L15-16 架构师 + RD 描述更新
  - **P0-90-4. `roles/architect.md` 加 Tech Review 入口**：
    - § 二 加 § 2.0 评审入口表（Blueprint Tech Review + Review CR + Goal-Plan ❌）
    - § 2.4 评审行为硬规则加 Tech Review 详规范条目
    - § 三 § 3.1 核心产出表加 TECH-REVIEW.md 条目 + review-arch.md cite 优化
    - § 四 Stage 速查 Blueprint 行 cite 改 architect-tech-review.md（原 cite blueprint-stage.md）
    - 顶部说明加 P0-90 sub-file 矩阵（契约 115 + Tech Review 230 + Code Review 261）
  - **P0-90-5. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-89 → 7.3.10+P0-90）
- **P0-79 元规则触发评估**（文件体量物理上限）：
  - roles/architect-tech-review.md = 230 行 ≤ 300 ✅
  - roles/rd.md = 232 行 ≤ 300 ✅（修复 642 严重超 cap）
  - roles/architect.md = ~125 行（加 Tech Review 入口后微涨 · 仍 ≤ 300 ✅）
- **加 1 删 1 元规则核算**：
  - **加**：roles/architect-tech-review.md（230 行）+ rd.md 4 段重构新写（232 行）+ architect.md 加 Tech Review 入口（~10 行）+ 散落 cite 微改（~10 行）= ~482 行
  - **删**：rd.md 原文（642 行）+ ROLES.md / agents/README.md / standards/backend.md / blueprint-stage.md 老 cite 替换中节省（~10 行）= ~652 行
  - **净删 ~170 行**（罕见 · 大重构通常会膨胀；本 patch 通过单源化 + cite 化 + 4 段压缩实现净删）
  - **核心收益**：
    - rd.md 642 → 232 · 不再背"RD 角色 + 架构师方案评审规范"双重身份 · 文件回到"RD 角色契约"本职
    - 架构师 sub-file 矩阵完整：architect.md（115 契约）+ architect-tech-review.md（230 Tech Review）+ architect-cr.md（261 Code Review）· 与 QA 三件套对称（qa.md + qa-tc-review.md + qa-cr.md）
    - 风格 C 设计在架构师 + QA + RD 完整落地（Wave 3 进度 3/6）
- 与已有规则的关系：
  - **`stages/dev-stage.md § RD 角色任务规范`**：保留 · 仍是 Dev Stage 内部 RD TDD 任务规范权威源 · rd.md § 三 cite 不变
  - **`standards/common.md § 三 RD 自查规范`**：保留 · 仍是 RD 自查规范权威源 · rd.md § 3.3 cite 不变
  - **`standards/tdd.md`**：保留 · TDD 单源 · rd.md § 一核心原则 cite 不变
- 不动:
  - 任何 stage 文件（dev-stage.md / test-stage.md / browser-e2e-stage.md / blueprint-stage.md 仅微调 cite）
  - templates / standards 其他文件
  - architect-cr.md / qa-cr.md / qa-tc-review.md sub-files
  - 其他 4 role（pm/designer/product-lead/external-reviewer/pmo）4 段重构留给 P0-91/92
- 影响面：1 个新建文件（architect-tech-review.md）+ 6 个文件改动（rd.md 全文重写 / architect.md 加 Tech Review 入口 / blueprint-stage.md ×2 cite / standards/backend.md × 1 / agents/README.md roles/ 目录索引 / ROLES.md ×2 行）+ 元数据 2 个（SKILL.md / init-stage.md）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：roles/architect-tech-review.md 存在 · rd.md = 232 行 ≤ 300 · architect.md 加 § 2.0 评审入口表 + § 2.4 Tech Review 硬规则 · 全 cite 路径可达
  - P0-91 时验证：PM 4 段重构（评估是否抽 PRD 技术评审段）· Wave 3 进度 4/6
- 后续 Wave 计划（**P0-91 / P0-92 / P0-XX**）：
  - **P0-91**：PM 4 段重构（含 PRD 技术评审规范段评估 · 是否抽 sub-file）
  - **P0-92**：Designer / product-lead / external-reviewer 4 段重构（合并 patch · 这 3 个文件较小）
  - **P0-XX**（Wave 4）：pmo.md 重点瘦身（1814 → ~500 行 · 拆 4-5 reference 子文件 · 风险最高）

---

## v7.3.10 + P0-89

> v7.3.10+P0-89 评审规范分层规范化 · 第 3 波第 3 阶段：QA 4 段重构。把 qa.md 内容按 4 段结构（角色定位 / 评审职责 / 职能职责 / Stage 速查 + 协同）重排 · 与 architect.md 对齐。Goal-Plan PRD 评审 checklist 归位到 § 二、评审职责 ·原"代码审查流程"段简化为 cite qa-cr.md ·散落职责段整合为 § 三、职能职责。

### P0-89：QA 4 段重构（Wave 3 第 3 阶段）

- 触发：P0-88 完成 qa.md 超 cap 修复 · 推进 QA 4 段重构（与 architect.md 风格 C 对齐）
- 设计哲学（4 段最小骨架 + Stage 速查 + 协同）：
  - **§ 一、角色定位**（QA 测试视角边界 + 与 RD 边界 + 核心原则 P0-68）
  - **§ 二、评审职责**（3 评审入口表 · Goal-Plan/Blueprint/Review · cite review-verdict.md / review-scope.md / qa-tc-review.md / qa-cr.md · Goal-Plan PRD checklist 归位 · 行为硬规则 · 反模式）
  - **§ 三、职能职责**（核心产出表 + TC 编写格式 BDD/Gherkin + 测试执行流程 + 验收声明 + 行为硬规则 + 反模式）
  - **§ 四、Stage 应用速查**（9 stage × QA 参与度表）
  - **§ 五、与其他角色的协同**（6 协同对象表）
- 核心改动：
  - **P0-89-1. 全文重写 `roles/qa.md`**（206 → 196 行 · 净删 10 行）：
    - 原 14 个分散段头（**职责** / **TC 编写格式** / **实现原则** / **验收标准覆盖声明** / **评审流程** / **代码审查流程** / **单元测试门禁** / **项目集成测试流程** / **跳过条件** / **API E2E** / **Browser E2E** / **完成后** / **TC 技术评审规范** / **Goal-Plan PRD 评审 checklist**）→ 整合为 5 段结构（4 段 + 协同）
    - **代码审查流程段简化**：删原 35 行内联流程 · 替为 cite qa-cr.md（避免与 qa-cr.md 双权威源）
    - **Goal-Plan PRD checklist 归位**：原顶级 H2 段 → § 2.4（评审职责子段）· 内容保留
    - **测试执行流程重组**：原 5 个分散段（单元门禁 / 集成测试 / 跳过 / API E2E / Browser E2E）→ § 3.3 集成测试执行流程（一图概括 + cite stage spec）· 净删 ~30 行重复
    - **核心原则 P0-68 上提**：从 qa-cr.md 提示拉到 § 一 角色定位（跨 stage 通用原则）
- **P0-79 元规则触发评估**（文件体量物理上限）：
  - roles/qa.md = 196 行 ≤ 300 ✅（继续保持 P0-88 的 cap 合规）
- **加 1 删 1 元规则核算**：
  - **加**：4 段结构 + Stage 速查表 + 协同表 + 评审入口表（结构化内容 ~50 行）
  - **删**：原代码审查流程详细段（~35 行）+ 原测试执行流程散落重复（~30 行）+ 原其他散落 hint（~5 行）= ~70 行
  - **净删 ~10 行**（罕见 · 重构通常会膨胀；本 patch 通过单源化 + 表格化压缩）
  - **核心收益**：
    - QA 角色契约从"分散段头流水账"变成"4 段结构化契约"· 与 architect.md 对齐
    - Goal-Plan PRD checklist 从顶级 H2 归位到 § 评审职责子段（更符合"评审职责跨 stage"逻辑）
    - 代码审查段不再双权威源（与 qa-cr.md 区分清晰：role 契约 vs 任务规范）
- 与已有规则的关系：
  - **`roles/qa-cr.md` / `roles/qa-tc-review.md`**：保留 · 仍是详规范权威源 · qa.md cite 不变
  - **`stages/test-stage.md`**：保留 · 集成测试 / API E2E 任务规范权威源 · qa.md § 3.3 cite 不变
  - **`stages/browser-e2e-stage.md`**：保留 · qa.md § 3.3 cite 不变
- 不动:
  - 任何 sub-file（qa-cr.md / qa-tc-review.md）
  - 任何 stage 文件（test-stage.md / browser-e2e-stage.md / blueprint-stage.md / review-stage.md）
  - architect.md / architect-cr.md
  - 全框架其他 cite 路径（qa.md 路径未变 · cite 仍可达）
- 影响面：1 个文件全文重写（roles/qa.md）+ 元数据 2 个（SKILL.md / init-stage.md）+ CHANGELOG entry
- 后续验证：
  - 立即可验证：roles/qa.md = 196 行 ≤ 300 ✅ · 4 段结构对齐 architect.md · 全 cite 路径可达
  - P0-90 时验证：RD 4 段重构（含架构师方案评审段拆给 architect.md）· 6 role 重构进度 2/6
- 后续 Wave 计划（**P0-90 / P0-XX**）：
  - **P0-90**: RD 4 段重构（含架构师方案评审段评估 · 是否拆给 architect.md 或独立 sub-file）
  - **P0-91**: PM 4 段重构（含 PRD 技术评审规范段评估）
  - **P0-92**: Designer / product-lead / external-reviewer 4 段重构（合并 patch · 这 3 个文件较小）
  - **P0-XX**（Wave 4）：pmo.md 重点瘦身（1814 → ~500 行 · 拆 4-5 reference 子文件 · 风险最高）

---

## v7.3.10 + P0-88

> v7.3.10+P0-88 评审规范分层规范化 · 第 3 波第 2 阶段：QA 文件超 cap 修复（roles/qa.md 359 → 206 行 ≤ 300 cap）。延 P0-87 sub-file 模式 · 抽 qa.md TC 技术评审规范段（~155 行）到 roles/qa-tc-review.md 子文件。

### P0-88：QA TC 技术评审规范抽 sub-file（修 qa.md 超 300 cap）

- 触发：P0-87 完成后自检发现 roles/qa.md 359 行 >300 cap（pre-existing · TC 技术评审段是主因）。本 patch 沿 P0-87 sub-file 模式修复。
- 核心改动：
  - **P0-88-1. 新建 `roles/qa-tc-review.md`**（168 行 ≤ 300 ✅）：
    - 6 段：角色定位 / 输入文件 / 评审维度（PM/RD/Designer 多角色视角 · 含动态选择）/ 执行流程（7 步）/ 输出要求（评审报告模板 + 文件路径 + 上游问题清单）/ 反模式 5 条
    - 顶部声明权威源 + cite 回 roles/qa.md 角色契约 + cite review-verdict.md / review-scope.md（review_scope=blueprint）+ 历史源流（agents/tc-review.md → qa.md → 本文件）
  - **P0-88-2. `roles/qa.md` 删 TC 技术评审规范段**（359 → 206 行 · 净删 ~153 行）：
    - 原 L166-326 整段删（~161 行 · 6 子段）→ 替成 6 行短指针（cite roles/qa-tc-review.md）
    - Goal-Plan Stage PRD 评审 checklist 段保留（~31 行 · QA 在 Goal-Plan 视角的 checklist · 后续 P0-89 4 段重构时可再归位到 § 评审职责）
    - 完成后：qa.md 206 行 ≤ 300 cap ✅（之前 pre-existing >300 问题已解决）
  - **P0-88-3. 全框架 cite 切换**（2 处活引用 + 1 处描述）：
    - `stages/blueprint-stage.md` L63 必读文件清单：`roles/qa.md（含 TC 技术评审规范）` → 拆为 `roles/qa.md（角色契约）+ roles/qa-tc-review.md（TC 技术评审详规范）`
    - `stages/blueprint-stage.md` L162 Process Step 2：`按 roles/qa.md「TC 技术评审规范」` → `按 [roles/qa-tc-review.md] · 角色契约见 [roles/qa.md]`
    - `ROLES.md` L14 描述：QA 描述更新含 [qa-cr.md](./roles/qa-cr.md) + [qa-tc-review.md](./roles/qa-tc-review.md) 子文件 · 同步加架构师独立行（之前没有）+ RD 描述去掉"+ 架构师方案评审规范" hint
  - **P0-88-4. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-87 → 7.3.10+P0-88）
- **P0-79 元规则触发评估**（文件体量物理上限）：
  - roles/qa-tc-review.md = 168 行 ≤ 300 ✅
  - roles/qa.md = 206 行 ≤ 300 ✅（修复前 359 ❌ → 修复后 ✅）
- **加 1 删 1 元规则核算**：
  - **加**：roles/qa-tc-review.md（168 行）+ qa.md 短指针（~10 行）+ blueprint-stage / ROLES.md 微改（~10 行）= ~188 行
  - **删**：qa.md TC 技术评审规范段（~161 行）+ ROLES.md 老 RD 描述里"+ 架构师方案评审规范 + Code Review"折叠（~5 行）= ~166 行
  - **净加 ~22 行**（Wave 3 第 2 阶段 · 主要价值在修 qa.md 超 cap · 不在 cite 化）
  - **Wave 1+2+3-1+3-2 累积**：净加 ~181 行（P0-85 +260 + P0-86 +144 + P0-87 +15 + P0-88 +22 - P0-87 复利）· 但 cap 合规性大幅改善（review-stage.md 826→384, qa.md 359→206 都回到 ≤300）
  - **核心收益**：
    - qa.md 修复超 cap（之前是 pre-existing 历史包袱 · 本 patch 解决）
    - roles/ 文件夹 sub-file 模式延续：QA 现有 3 文件（qa.md 角色契约 + qa-cr.md CR 详规范 + qa-tc-review.md TC 评审详规范）· 与架构师对称（architect.md + architect-cr.md）
    - 风格 C 设计在 QA 角色完整落地（每个详规范都有独立 sub-file）
- 与已有规则的关系：
  - **`roles/qa.md` Goal-Plan PRD 评审 checklist 段**：保留（仍在 qa.md 内 · ~31 行 · 不大）· P0-89 4 段重构时归位到 § 评审职责
  - **`REVIEWS.md` 全局 review 格式文件**：未动（out of scope · 仍是历史 legacy 全局 review 格式权威源）
  - **`roles/qa.md` 代码审查流程段（L62-99）**：保留（虽然内容被 qa-cr.md 覆盖 · 但 qa.md 内仍是简版职能描述 · P0-89 整理时优化）
- 不动:
  - 任何角色契约段（除 qa.md TC 技术评审段抽出）
  - REVIEWS.md / standards / templates 其他文件
  - 其他 6 role（pm/rd/designer/product-lead/external-reviewer/pmo）
- 影响面：1 个新建文件（qa-tc-review.md）+ 4 个文件 cite/描述切换（qa.md 大动 / blueprint-stage.md ×2 / ROLES.md / SKILL.md 版本）+ 元数据 2 个（SKILL.md / init-stage.md）
- 后续验证：
  - 立即可验证：roles/qa-tc-review.md 存在 · qa.md 行数从 359 → 206 · grep "qa.md.*TC 技术评审" 应仅剩 ROLES.md 描述（已更新指 sub-file）+ CHANGELOG 历史
  - P0-89 时验证：QA 4 段重构后 · qa.md 内的 Goal-Plan PRD checklist 归位到 § 评审职责 · 更进一步精简
- 后续 Wave 计划（**P0-89 / P0-XX**）：
  - **P0-89 ~ P0-92**（Wave 3 后续 6 role 4 段重构）：每次独立 patch · 重写按 4 段（角色定位 / 评审职责 / 职能职责 / 特殊职责 + Stage 速查）· cite review-verdict.md / review-scope.md
    - P0-89: QA 4 段重构（含 Goal-Plan PRD checklist 归位 + Code Review 段简化为 cite）
    - P0-90: RD 4 段重构（含架构师方案评审规范段拆给 architect.md）
    - P0-91: PM 4 段重构（含 PRD 技术评审规范段评估）
    - P0-92: Designer / product-lead / external-reviewer 4 段重构
  - **P0-XX**（Wave 4）：pmo.md 重点瘦身（1814 → ~500 行 · 拆 4-5 reference 子文件 · 风险最高）

---

## v7.3.10 + P0-87

> v7.3.10+P0-87 评审规范分层规范化 · 第 3 波第 1 阶段：CR 任务规范从 stages/review-stage.md 抽到 roles/{architect-cr,qa-cr}.md 子文件。落 P0-86 中"P0-87 计划迁回"的承诺。**净删 ~440 行**，是 Wave 1+2 累积净加（~404 行）的第一次大额回收 · 评审规范分层规范化设计开始变现。

### P0-87：CR 任务规范从 stage 抽到 role sub-file（Wave 3 第 1 阶段）

- 触发：P0-86 完成 architect 独立化 · 推进"CR 任务规范回 roles/"承诺。设计权衡：直接 inline 入 architect.md / qa.md 会超 300 cap（架构师 4 段 114 + CR 256 = 370）→ 改用 sub-file 模式（保 4 段主 role 简洁 + 子文件 ≤300 cap + role 文件夹只做"角色相关"分类不破设计）
- 核心改动：
  - **P0-87-1. 新建 `roles/architect-cr.md`**（261 行 ≤ 300 ✅）：
    - 6 段：角色定位 / Review 维度（含日志完整性 P0-69 三段式 + Schema 同步 + 防御性路径 4 路 + 性能 / 安全 / 缓存）/ 执行流程 + 约束 / 架构文档更新规则 / 输出模板（7 段表格）/ 上游问题清单
    - 顶部声明权威源 + cite 回 roles/architect.md 角色契约 + 历史源流（agents/arch-code-review.md → review-stage.md → 本文件）
  - **P0-87-2. 新建 `roles/qa-cr.md`**（204 行 ≤ 300 ✅）：
    - 5 段：角色定位 / 执行流程（Step 1-7 + Step 4.5 PRD AC 直接对账 P0-68 + Step 5.5 用户行为边界 + Step 5.7 设计-代码一致性）/ 执行约束 / QA Review 输出模板 / 结果处理
    - 同样声明权威源 + cite 回 roles/qa.md
  - **P0-87-3. `stages/review-stage.md` 删两段大正文**（826 → 386 行 · 净删 ~440 行）：
    - § 架构师 CR 任务规范（原 ~256 行）→ 5 行短指针（cite roles/architect-cr.md）
    - § QA CR 任务规范（原 ~198 行）→ 5 行短指针（cite roles/qa-cr.md）
    - 内部 5 处引用更新（L5 顶部说明 / L52-53 必读文件 / L57-58 必读文件 / L144 Step 4 架构师 / L149 Step 4 QA）
  - **P0-87-4. 全框架 cite 批量更新**：
    - `SKILL.md` L287 Plan 模板示例：`stages/review-stage.md §架构师 CR 任务规范, stages/review-stage.md §QA CR 任务规范` → `roles/architect.md + roles/architect-cr.md, roles/qa.md + roles/qa-cr.md`
    - `standards/backend.md` L641 Schema 链表格 cite 改 → `roles/architect-cr.md`
    - `roles/rd.md` 3 处（L156 规范引用 / L191 性能与安全详引 / L220 阶段 2 架构师段）改 → `roles/architect-cr.md`
    - `templates/dispatch.md` L46 Subagent 输入文件清单 cite 改
    - `codex-agents/reviewer.toml` L9 reviewer prompt cite 改
  - **P0-87-5. `roles/architect.md` / `roles/qa.md` cite 切换** + 删除"v7.3.10+P0-87 计划迁回"过渡注释（已落地）：
    - architect.md 顶部说明 / §2.4 评审行为硬规则 / Stage 应用速查表 共 3 处
    - qa.md 顶部评审契约速查 1 处
  - **P0-87-6. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-86 → 7.3.10+P0-87）
- **P0-79 元规则触发评估**（文件体量物理上限）：
  - roles/architect-cr.md = 261 行 ≤ 300 ✅
  - roles/qa-cr.md = 204 行 ≤ 300 ✅
  - stages/review-stage.md 826 → 386 行 · 大幅瘦身 ✅
- **加 1 删 1 元规则核算**：
  - **加**：roles/architect-cr.md（261 行）+ roles/qa-cr.md（204 行）+ 散落 cite 字面值微改（~20 行）= ~485 行
  - **删**：review-stage.md（~440 行 · 含两段大正文 + 重复段头）+ 全框架 cite 中 review-stage.md §X 字面值替换中节省的修饰词（~30 行）= ~470 行
  - **净加 ~15 行**（基本平衡 · 落"加 1 删 1"元规则）
  - **P0-86 + P0-87 合计**：Wave 2 + Wave 3 第 1 阶段累积净加 ~159 行（P0-86 +144 + P0-87 +15）· 比单纯 inline 重写省了 ~250 行（因为是 cite 化而非复制粘贴）
  - **核心收益**：
    - review-stage.md 826 → 386 行 · 显著瘦身 · 可读性大幅提升（再不是 stage 契约 + role 任务规范双重身份）
    - role 文件夹组织清晰：roles/architect.md（角色契约 4 段）+ roles/architect-cr.md（CR 详规范 6 段）；qa 同样
    - "stage 管调度 + scope · role 管角色契约 + 评审视角"风格 C 设计**完整落地**
- 与已有规则的关系：
  - **`roles/rd.md` 架构师方案评审规范段**：暂保留（仍是 RD 寄生 · Blueprint Stage 用）· 后续 patch 评估是否搬到 architect.md（与 CR 不同 stage · 不在本 patch 范围）
  - **`roles/architect.md` 4 段最小骨架**：保留 · 仅切换 cite 路径 + 删除过渡注释
  - **`stages/review-stage.md` 调度契约**：保留 · 删两段大正文 · stage 文件回到"调度 + scope + 循环"本职
- 不动:
  - 任何角色契约段（architect.md 4 段 / qa.md 现有内容）
  - standards / templates 其他文件
  - 其他 6 role（pm/rd/designer/product-lead/external-reviewer/pmo）4 段重构留给 P0-88+
- 影响面：2 个新建文件（architect-cr.md / qa-cr.md）+ 7 个文件 cite 切换（review-stage.md 大动 / SKILL.md / standards/backend.md / roles/rd.md / roles/architect.md / roles/qa.md / templates/dispatch.md / codex-agents/reviewer.toml）+ 元数据 2 个（SKILL.md / init-stage.md）
- 后续验证：
  - 立即可验证：roles/architect-cr.md / roles/qa-cr.md 存在 · review-stage.md 长度从 826 → 386 · 全框架 grep "stages/review-stage.md §架构师 CR 任务规范" / "§QA CR 任务规范" 应 0 命中（除 CHANGELOG 历史段）
  - P0-88+ 时验证：6 role 4 段重构后 · 子文件模式可作为参考（如 pm-discuss.md / qa-tc-review.md 等专项 spec）
- 后续 Wave 计划（**P0-88 / P0-XX**）：
  - **P0-88 ~ P0-92**（Wave 3 后续）：6 role 4 段重构（pm / rd / qa / designer / product-lead / external-reviewer）· 每次独立 patch · 重写按 4 段结构 + cite review-verdict.md / review-scope.md
  - **P0-XX**（Wave 4）：pmo.md 重点瘦身（1814 → ~500 行 · 拆 4-5 reference 子文件 · 风险最高）

---

## v7.3.10 + P0-86

> v7.3.10+P0-86 评审规范分层规范化 · 第 2 波：架构师独立化（peer to RD）。本 patch 采用 **incremental 策略**：先建 roles/architect.md（4 段最小骨架 · 暂 cite review-stage.md 详规范）+ 联动 schema/stage cite 切换 · 不立即抽 review-stage.md 架构师 CR 任务规范段（256 行）· 那部分留给 P0-87 一起处理。这样 architect 独立化逻辑完成 · 但 review-stage.md 大段不动 · 风险最低。

### P0-86：架构师独立化（Wave 2 · incremental）

- 触发：P0-85 完成基础设施后 · 推进 Wave 2「architect 独立成 role」
- 核心改动：
  - **P0-86-1. 新建 `roles/architect.md`**（114 行 · 4 段极简结构）：
    - 一、角色定位（与 RD 边界："RD 实现层 / 架构师架构层" + "两个 adapter 才抽象" 判定）
    - 二、评审职责（6 维 + 1 兜底 · cite review-verdict.md / review-scope.md · 行为硬规则 · 反模式）
    - 三、职能职责（TECH 架构段 / REVIEW 架构师段 / ADR 起草 / ARCHITECTURE.md 维护 / database-schema.md 同步）
    - 四、Stage 应用速查（Goal-Plan ❌ / Blueprint ✅ / Dev ❌ / Review ✅）
    - 五、与其他角色的协同（RD / QA / External / PMO 协同点）
    - 🔴 注：架构师 CR 详细任务规范暂保留在 stages/review-stage.md（v7.3.10+P0-87 计划迁回）
  - **P0-86-2. `roles/qa.md` 顶部加评审契约速查指针**（cite review-verdict.md / review-scope.md / review-stage.md § QA CR 任务规范）
  - **P0-86-3. `stages/blueprint-stage.md` 评审组合更新**：
    - 入口 Read 顺序加 `roles/architect.md`（与 qa/rd 同 step）
    - 必读文件清单加 `roles/architect.md`（独立化标识）
    - Step 4 架构师方案评审 cite 改成 `roles/architect.md`（原 cite `roles/rd.md` 「架构师方案评审规范」）· 同时 cite review-verdict.md + review-scope.md
    - 角色规范必读硬规则加 architect 独立项
  - **P0-86-4. `templates/feature-state.json` `_role_enum` 加 architect**（标注 architect 仅 Blueprint/Review 子 config 用 · 不参与 Goal-Plan PRD 评审）
  - **P0-86-5. `templates/prd.md` PRD-REVIEW `reviews[].role` enum 加 architect**（schema 通用复用 TC-REVIEW / TECH-REVIEW / REVIEW.md · architect 值合法 · 注释标 prd scope 不参与）
  - **P0-86-6. `stages/review-stage.md` 两段顶部加 cite 标注**：
    - § 架构师 CR 任务规范 顶部 cite roles/architect.md（角色契约权威源）
    - § QA CR 任务规范 顶部 cite roles/qa.md（角色契约权威源）
    - 标注"v7.3.10+P0-87 计划迁回 roles/"（后续 patch 路径预告）
  - **P0-86-7. 版本号 + init-stage.md SKILL_VERSION 期望同步**（7.3.10+P0-85 → 7.3.10+P0-86）
- **P0-79 元规则触发评估**（文件体量物理上限）：
  - 涉及新文件：roles/architect.md = 114 行 ≤ 300 ✅
  - 涉及修改文件：均无明显增长 · 触发审查的暂无
- **加 1 删 1 元规则核算**：
  - **加**：~114 行（roles/architect.md 新建）+ 散落 cite 注释 ~30 行（qa.md / blueprint-stage.md / review-stage.md / state.json / prd.md）
  - **删**：未删（incremental 策略 · review-stage.md 大段保留 · P0-87 才净删）
  - **净加 ~144 行**（Wave 2 第一阶段 · 重在角色独立 · 不重在抽段）
  - **核心收益**：
    - architect 从 RD 子角色升 peer-level role · 职责边界清晰（架构层 vs 实现层）
    - 评审 verdict + scope 通过 review-verdict.md / review-scope.md 单源 cite · 不重复定义
    - 后续 P0-87 可以原地抽 review-stage.md 大段到 architect.md（不需重写 · 仅迁移）
- 与已有规则的关系：
  - **`stages/goal-plan-stage.md`**：保留 · 架构师不参与 Goal-Plan（已隐含）
  - **`stages/review-stage.md` 架构师 + QA CR 任务规范**：原地保留 · 顶部加 cite 注释 · P0-87 迁回 roles/
  - **`roles/rd.md` 架构师方案评审规范段**：暂不动（P0-87 时与 review-stage.md 大段一并整合到 architect.md）
- 不动：
  - `stages/review-stage.md` 架构师 CR 任务规范段大正文（仅顶部加 cite）
  - `roles/rd.md`（架构师段保留 · P0-87 处理）
  - `roles/pmo.md` 智能推荐表（架构师不参与 Goal-Plan · 不改）
- 影响面：1 个新建文件（roles/architect.md）+ 6 个文件 cite/enum 微改（qa.md / blueprint-stage.md / review-stage.md / state.json / prd.md / init-stage.md）+ 元数据 2 个（SKILL.md / docs/CHANGELOG.md）
- 后续验证：
  - 立即可验证：roles/architect.md 存在 · cite review-verdict.md / review-scope.md / review-stage.md 路径可达
  - P0-87 时验证：迁出 review-stage.md 架构师 CR 段后 · 大段净删（开始 incremental 净删）
- 后续 Wave 计划（**P0-87 / P0-87+ / P0-XX**）：
  - **P0-87**（Wave 3 第 1 阶段）：抽 review-stage.md 架构师 CR 任务规范（~256 行）+ QA CR 任务规范（~198 行）回 roles/architect.md / roles/qa.md（净删 review-stage.md ~454 行）
  - **P0-88 ~ P0-92**（Wave 3 后续）：6 role 4 段重构（pm / qa / rd / designer / product-lead / external-reviewer）· 每次独立 patch
  - **P0-XX**（Wave 4）：pmo.md 重点瘦身（1814 → ~500 行 · 拆 4-5 reference 子文件）

---

## v7.3.10 + P0-85

> v7.3.10+P0-85 评审规范分层规范化 · 第 1 波：基础设施（review-verdict + review-scope 双单源）。用户拍板「按风格 C 方向 · role 管角色契约 + 评审视角 + 职能视角」+「先梳理 role 内容 · 不直接动手」+「architect 作为与 RD 同级独立角色」+「确认全部拍板点」。本 patch 是 Wave 1：仅创建基础设施单源（不动 role 文件 / 不动 stage 文件）· 后续 P0-86（architect 独立化）+ P0-87+（6 role 重构）+ P0-XX（pmo 瘦身）分批推进。

### P0-85：评审规范分层规范化 Wave 1（基础设施）

- 触发：用户分析「各角色评审规范散落 4 类文件 · 单源不一致」+ 用户拍板「按风格 C · role 只管评审视角 + 职能视角两类」+「architect 独立成 role」+「确认全部拍板点」
- 设计哲学：
  - **role 文件管"角色契约 + 评审视角 + 职能视角"两类**（跨 stage 通用）
  - **stage 文件管"调度 + scope 边界 + 评审循环"**（stage 特定）
  - **template 文件管"产物 schema"**（已是单源）
  - **standards 文件管"跨角色跨 stage 通用规则"**（verdict 等级 / scope 边界 / TDD / external 异质性）
- 改动（仅基础设施 · 不动 role / stage 文件）：
  - **P0-85-1. 新建 `standards/review-verdict.md`**（~150 行）：
    - 二、Verdict 三等级（PASS / PASS_WITH_CONCERNS / NEEDS_REVISION）+ 流转决策表
    - 三、Finding Severity 三级（MUST-fix / SHOULD-fix / NICE-to-have）+ 判定规则（reviewer 必遵守）
    - 四、整体 Verdict 收敛规则（多 reviewer 时最严胜出）
    - 五、PM 回应规则（ADOPT/REJECT/DEFER + 对抗自查 P0-34-B + DEFER 收紧 P0-34-A · 整合迁入）
    - 六、循环上限（≤3 轮 + 超限 ⏸️ 用户决策 5 选 1）
    - 七、与其他规范的协作矩阵
  - **P0-85-2. 新建 `standards/review-scope.md`**（~110 行）：
    - 二、Scope 三类（prd / blueprint / code-review）+ 评审对象映射
    - 三、Scope 边界（每个 scope 该审 / 不该审清单 · 整合迁入散落各 role/stage 的边界规则）
    - 四、Scope 越界拦截（PMO 整合 finding 时的处理规则）
    - 五、Scope 与 Stage 的映射关系
    - 六、与其他规范的协作矩阵
  - **P0-85-3. 版本号 + CHANGELOG**（7.3.10+P0-84 → 7.3.10+P0-85；init-stage.md SKILL_VERSION 期望同步）
- **P0-79 元规则触发评估**（v7.3.10+P0-79 文件体量物理上限）：
  - 涉及文件：均为新建 · 各 ≤ 150 行 · 符合 ≤300 上限 ✅
- **加 1 删 1 元规则核算**：
  - **加**：~260 行（review-verdict.md ~150 行 + review-scope.md ~110 行）
  - **删**：未删（基础设施新建 · 后续 patch 才会触发各处散落 cite 化导致净删）
  - **净加 ~260 行**（基础设施类 · 不算违反元规则 · 是后续清理的依据）
  - **核心收益**：
    - verdict 等级 + severity 判定 + PM 回应规则 + 循环上限 → 单一权威源（之前散落 5+ 文件）
    - scope 三类 + 边界 + 越界拦截 → 单一权威源（之前散落各 role + stage）
    - 后续 P0-86/87+ 可以基于此做 cite 化清理 · 大幅净删
  - **"重新触发回来"防护**：未来若有人在 role / stage 重新定义 verdict 或 scope → cite 本 patch 单源
- 与已有规则的关系：
  - **`templates/prd.md` PRD-REVIEW frontmatter schema**：保留 · 仅 enum 引用本文件三等级 + 三级
  - **`stages/goal-plan-stage.md` 评审循环 + scope 边界**：保留 · cite 本文件
  - **`stages/blueprint-stage.md` / `review-stage.md`**：保留 · cite 本文件
  - **`roles/*.md` 各角色评审段**：保留（暂不改）· 等 P0-86/87+ 重构时改 cite
- 不动:
  - 任何 role 文件（Wave 2/3 的事）
  - 任何 stage 文件（Wave 2 的事）
  - templates 文件（schema enum 暂不动 · Wave 2 时同步）
  - external-model.md / tdd.md 等其他 standards
- 影响面：2 个新建文件（standards/review-verdict.md / standards/review-scope.md）+ 元数据 3 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 立即可验证：standards/ 目录下两个新文件存在 · cite 路径可达
  - P0-86 时验证：roles/architect.md 创建时直接 cite 本文件 verdict + scope · 不重复定义
  - P0-87+ 时验证：各 role 重构时 cite 本文件 + 删散落 verdict 定义（开始净删）
- 后续 Wave 计划（**P0-86 / P0-87+ / P0-XX**）：
  - **P0-86**（Wave 2 · architect 独立化）：新建 roles/architect.md + 抽 review-stage.md 架构师 CR 任务规范 + 抽 QA CR 任务规范到 roles/qa.md + 修 stages/blueprint/review/goal-plan + roles/pmo.md 智能推荐表 + state.json/prd.md schema 加 architect enum
  - **P0-87 ~ P0-92**（Wave 3 · 6 role 4 段重构）：每个 role 独立 patch（pm / qa / rd / designer / product-lead / external-reviewer）· 每次重写按 4 段结构（角色定位 / 评审职责 / 职能职责 / 特殊职责）+ cite review-verdict.md + cite review-scope.md
  - **P0-XX**（Wave 4 · pmo.md 重点瘦身）：独立 patch · 1814 → ~500 行 · 拆 4-5 个 reference 子文件 · 风险最高

---

## v7.3.10 + P0-84

> v7.3.10+P0-84 Goal-Plan 子步骤 3 串行身份切换改并行加载（用户拍板「QA+RD+Designer 串行没必要 · 一次性加载三视角规范评审更合理」）：当前 Goal-Plan Stage 子步骤 3 是 PMO 主对话内 QA→RD→Designer 物理身份切换 3 次（每次 Read 对应 roles/{id}.md + cite + 输出 finding + 切回 PMO）。深度分析后发现：**主对话内身份切换是软切换**（同 LLM session / 同 context · 切 RD 时上下文仍含 QA finding · 串行不带来真独立性 · "防鼓掌效应"是错觉）· 反而 3 次 Read + 3 次 cite + 3 次输出循环成本高。改为 PMO 一次性加载三视角规范 + 一次性输出三段独立 finding（保留输出结构 · 去物理切换仪式）。

### P0-84：Goal-Plan 子步骤 3 串行改并行加载 + 三段独立输出

- 触发：用户分析「QA+RD+Designer 串行是否必要 · 是否一次性加载三视角的规范来评审更合理」+ 用户拍板「P0-84 推进」
- 设计哲学：
  - **主对话内身份切换 = 软切换**：同 LLM session / 同 context · 切 RD 时上下文仍含 QA finding · 不可能真独立
  - **真独立性需 Subagent 物理隔离**（fresh context · 不同 session）· 主对话内做不到
  - **串行的真实价值是输出结构清晰**（三段标题）· 不是真改变 LLM 内部判断
  - **并行加载收益**：节省 Read 重复 / 节省时间 / 跨视角 finding 自然涌现
  - **保留**：输出结构（三段标题）+ 关注点 cite + PMO self-check 防三段融合
- 改动：
  - **P0-84-1. `stages/goal-plan-stage.md` 子步骤 3 调度顺序段重写**：从 3 步串行（PMO→QA / PMO→RD / PMO→Designer）改为 2 步并行（Step 1 PMO 一次性 Read 三视角规范 + Step 2 一次性输出三段 finding）+ 强制三段输出格式（QA/RD/Designer 严格三段标题 + 每段顶部 cite 关注点 + 至少 1 行 finding 即使为空也写"无 finding"）+ PMO self-check 硬规则（grep 三段标题 + cite 非空）+ 跨视角 finding 处理（cross_role 字段 · 仍归主要视角段）
  - **P0-84-2. `stages/goal-plan-stage.md` "主对话身份切换硬规则"段替换为"视角加载硬规则"段**：取消第一人称锚点（"作为 QA·……"）· 改为通过三段标题 + 关注点 cite + self-check 物理保证三段结构
  - **P0-84-3. `templates/prd.md` PRD-REVIEW schema 加 `cross_role: []` 可选字段**：finding 同时关联多视角时（如 [qa, rd]）标注 · 但仍归入主要视角段 · 不复制到多段
  - **P0-84-4. 版本号 + CHANGELOG**（7.3.10+P0-83 → 7.3.10+P0-84；init-stage.md SKILL_VERSION 期望同步）
- **P0-79 元规则触发评估**（v7.3.10+P0-79 文件体量物理上限）：
  - 涉及文件：`stages/goal-plan-stage.md` ~650 行（超 300 上限）
  - 本 patch 净加：~+5 行（结构调整 + 加 self-check 抵消删段）
  - 是否触发拆分：否 · 累积压力基本持平（P0-83 已减 50 行 · 本 patch 微增 · 总体仍减负方向）
- **加 1 删 1 元规则核算**：
  - **加**：~30 行（新调度模式段 + self-check 硬规则 + cross_role 字段说明 + 视角加载硬规则段）
  - **删**：~25 行（原 3 步串行调度顺序 + 原主对话身份切换硬规则段）
  - **净加 ~5 行**（结构调整 · 不算实质净加）
  - **不增加 PMO 负担**：减少 3 次切换 → 1 次输出 · 显著降低
  - **核心收益**：
    - Token ↓ ~30%（避免 3 次重复 Read 同样的 PRD / 重复 cite）
    - 时长 ↓ ~40%（1 次输出循环 vs 3 次）
    - 跨视角 finding 自然涌现（无需 PMO 在切回时手动整合）
    - 输出结构不变（PRD-REVIEW.md.reviews[role] schema 兼容）
  - **风险缓解**：
    - 三段融合 → self-check grep 三段标题 + cite 非空（缺一段 = 流程偏离 · 重新输出）
    - 失去专业判断深度 → 强制每段顶部 cite roles/{id}.md 1-2 句关键点（不能凭记忆）
    - 跨视角 finding 错位 → cross_role 字段 + 主要视角归属规则
  - **"重新触发回来"防护**：未来若有人想恢复物理身份切换 → cite 本 patch 反例（主对话内身份切换是软切换 · 防鼓掌是错觉 · 真独立性需 Subagent）
- 与已有规则的关系：
  - **v7.3.10+P0-44 Goal-Plan 5 子步骤重构**：本 patch 简化子步骤 3（串行→并行加载）· 不破坏 5 子步骤主结构
  - **v7.3.10+P0-20-B 第一人称锚点（Micro 流程）**：保留 · Micro 仍用 PMO→RD 物理身份切换（Micro 是单角色 · 与 Goal-Plan 子步骤 3 多角色场景不同）
  - **v7.3.10+P0-83 删 Goal-Plan external**：保留 + 协作（external 已删 · 本 patch 改的是剩余 QA/RD/Designer 调度）
  - **PRD-REVIEW.md schema reviews[]**：保留 · 仅加 `cross_role: []` 可选字段
- 不动:
  - 5 子步骤主结构（不变）
  - PRD-REVIEW.md.reviews[].{qa | rd | designer} 三段独立段（输出仍三段 · 仅调度方式变）
  - Designer 触发条件（双保险 + 中途补启用 P0-51）
  - PM 回应循环（子步骤 4 不变）
  - Micro 流程的 PMO→RD 物理身份切换（保留 · 单角色场景）
  - Blueprint Stage / Review Stage 评审调度（本 patch 仅改 Goal-Plan 子步骤 3 · 其他 stage 不变）
- 影响面：2 个文件（stages/goal-plan-stage.md / templates/prd.md）+ 元数据 2 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 Goal-Plan 子步骤 3 PMO 一次性 Read 三视角规范 + 一次性输出三段独立 finding
  - 输出三段标题严格 · self-check grep 通过
  - 跨视角 finding 标 cross_role · 不复制到多段
  - PMO 调度时长降低（3 次循环 → 1 次输出）
  - 长期：观察 LLM 是否会出现"三段融合"漂移（输出 1 段含三视角混合 finding）· 若出现 → 加更强的输出格式约束 / 或回退到串行
  - 同样的逻辑可考虑应用到 Blueprint Stage 的 RD/QA 评审（待实战触发再决定）

---

## v7.3.10 + P0-83

> v7.3.10+P0-83 删除 Goal-Plan Stage 的 external 评审（用户拍板「只删 Goal-Plan · Blueprint 保留」）：用户分析 Goal-Plan Stage external 在 PRD 文档层的边际价值低（5 内部视角 + PM 对抗自查 + 评审循环已多层兜底）+ external 后台并行复杂度高（shell 调用 + stderr 处理 + 结果合并）→ 收益与复杂度不匹配。Blueprint Stage 保留（详细技术方案 · 出问题后续改动成本高 · 异质视角价值显著）+ Review Stage 保留（代码层最后 gate · 默认 ON）。

### P0-83：删 Goal-Plan Stage external 评审（保留 Blueprint / Review）

- 触发：用户分析「Goal-Plan 阶段外部模型评审是否有必要」+ 用户拍板「只删 Goal-Plan · Blueprint 主要是详细方案 · 出问题后续改动成本高」
- 设计哲学：
  - **PRD = 产品文档**：external 异质视角的核心价值在代码层（实现盲区 / 第三方依赖真实性 / 并发安全）· 文档层弱
  - **Blueprint = 详细技术方案**：架构 / 数据模型 / 接口设计层的异质视角价值高 · 出问题后续改动成本极高 → 保留 external
  - **Review = 代码层最后 gate**：默认 ON · 异质视角对实现盲区价值最高 → 保留 external
  - **Goal-Plan = PRD 起草 + 业务方向锁死**：5 内部视角（PL/RD/QA/Designer/PMO）+ PM 对抗自查（P0-34-B）+ 评审循环 ≤3 轮 + 用户最终确认 = 多层兜底已厚 · external 边际价值低 → 删
- 改动：
  - **P0-83-1. `stages/goal-plan-stage.md` 子步骤序列表**：删 `∥ external 并行` + 删 reviews[] external · 加 v7.3.10+P0-83 注解
  - **P0-83-2. `stages/goal-plan-stage.md` 子步骤 3 标题**：从「QA+RD+Designer(可选) 主对话联合评审 ∥ external 并行」改为「QA+RD+Designer(可选) 主对话联合评审」
  - **P0-83-3. `stages/goal-plan-stage.md` 子步骤 3 调度顺序段**：删"并行：external 评审"段（4 行）
  - **P0-83-4. `stages/goal-plan-stage.md` 删 external 并行实施段**（含 background bash + 异质性硬约束 ~22 行）
  - **P0-83-5. `stages/goal-plan-stage.md` 智能推荐表**：删"external 角色"列（5 行 column 整体删）
  - **P0-83-6. `stages/goal-plan-stage.md` 入口 Read 顺序**：删 templates/external-cross-review.md 条件加载行
  - **P0-83-7. `stages/goal-plan-stage.md` active_roles 候选段**：从 `PL / RD / QA / Designer / PMO / external` 改为 `PL / RD / QA / Designer / PMO`
  - **P0-83-8. `stages/goal-plan-stage.md` 重构原则段加 P0-83 注解**
  - **P0-83-9. `standards/external-model.md` 顶部加适用范围段**：明确「仅适用 Blueprint / Review · Goal-Plan 不适用」
  - **P0-83-10. 版本号 + CHANGELOG**（7.3.10+P0-82 → 7.3.10+P0-83；init-stage.md SKILL_VERSION 期望同步）
- **P0-79 元规则触发评估**（v7.3.10+P0-79 文件体量物理上限）：
  - 涉及文件：`stages/goal-plan-stage.md` ~700+ 行（远超 300 上限）
  - 本 patch 净加：**-50 行**（净删 ~50 行 + 加注解 ~10 行 - 删段 ~60 行）
  - 是否触发拆分：否 · 本 patch 是减法 · **降低**累积压力 ✅ 符合元规则方向
  - `standards/external-model.md` 行数较小 · 加 1 行适用范围说明
- **加 1 删 1 元规则核算**：
  - **加**：~10 行（适用范围注 + 删除标注）
  - **删**：~60 行（external 并行段 + 智能推荐表 external 列 + 入口 Read 条件加载行 + 各处 external 措辞）
  - **净删 ~50 行**（持续减负 patch · 与 P0-82 同类 · 累积净删压力增加）
  - **不增加 PMO 负担**：Goal-Plan 阶段不再有 external 调度 · PMO 调度责任降低
  - **核心收益**：
    - Goal-Plan Stage 复杂度显著下降（删后台 shell 并行 / stderr 处理 / 结果合并）
    - PRD 评审时长降低（5-10 min external 等待消失）
    - active_roles 候选从 6 减为 5
    - external 单源到 Blueprint / Review · 边界清晰
    - external 资源集中投到真正高价值场景
  - **"重新触发回来"防护**：未来若有人想给 Goal-Plan 加回 external → cite 本 patch 反例（PRD 文档层边际价值低 + 多层兜底已厚 + 复杂度成本高）
- 与已有规则的关系：
  - **v7.3.10+P0-13 Plan/Blueprint Codex 改 opt-in 默认 OFF**：本 patch 进一步删 Goal-Plan · 完全移除（不再支持 opt-in）· Blueprint 仍保持 opt-in
  - **v7.3.10+P0-44 Goal-Plan 5 子步骤重构**：本 patch 简化子步骤 3（删 external 并行）· 不破坏 5 子步骤主结构
  - **v7.3.10+P0-72 PMO 直接判定**：保留（仍用于 Blueprint / Review 的 external 启用判定）
  - **v7.3.10+P0-78 PRD-REVIEW finding code_evidence 字段**：保留 + 互补（code_evidence 让内部 reviewer finding 更 evidence-based · 减少对 external 异质视角的依赖）
  - **standards/external-model.md**：本 patch 加适用范围段（仅 Blueprint / Review）· 保留 E1/E2/E3 三条硬规则不变
- 不动:
  - Blueprint Stage external 评审（保留 · 详细技术方案 · 异质视角对架构/数据模型/接口设计盲区有补）
  - Review Stage external 评审（保留 · 代码层最后 gate · 默认 ON）
  - external-model.md E1/E2/E3 三条硬规则
  - external-reviewer.md 角色契约（除明确适用范围）
  - feature-state.json external_cross_review schema（vbs Goal-Plan 不再写 external · 但 Blueprint / Review 仍用此 schema）
  - claude-agents/codex-agents 调用入口
- 影响面：2 个产物文件（stages/goal-plan-stage.md / standards/external-model.md）+ 元数据 2 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 Goal-Plan Stage 入口实例化 · review_roles[] 不再含 external 选项 · PMO 不再调度 external CLI shell
  - PRD 评审时长降低（少 5-10 min external 等待）
  - Blueprint Stage / Review Stage 仍按现有规范启用 external（不变）
  - 长期：观察 Blueprint Stage external 是否实战命中率高 · 若实战中 Blueprint external 启用率也低 · 可考虑下一步收紧到仅 Review

---

## v7.3.10 + P0-82

> v7.3.10+P0-82 PRD 模板减法（删功能需求段冗余 + API 契约加产品视角边界）：用户拍板「PRD 输出目标背景 / 业务流程 / AC 即可」+ 「API 契约子段保留但加边界注（产品 vs 技术）」+ 「埋点需求保留（产品定义"我们要看什么数据"）」。本 patch 实质性减法：删功能需求 P0/P1/P2 段（与 AC 重复 · AC 已分优先级）+ API 契约子段加产品视角边界注（防 PM 写入鉴权/限流/SLA 等技术细节）。

### P0-82：PRD 模板减法（删功能需求段 + API 契约加边界）

- 触发：用户「关于 plan-stage 是否需要进一步做减法 · 输出目标背景 / 业务流程 / 产品关注的 AC 即可」+ 用户纠正「埋点需求不能删 · 它定义产品要关注的数据」+ 用户拍板「API 契约保留但加边界」+ 「ok」
- 设计哲学（用户视角）：
  - PRD = 产品视角（What/Why · 含产品关注的数据 / 接口能力承诺）
  - TECH = 实现视角（How · 含埋点 SDK 调用 / API 鉴权 / SLA / 数据库）
  - 边界关键：埋点需求段 = 产品要看什么数据（产品） · API 契约段 = 接口能力承诺（产品）/ 鉴权限流 SLA = 技术
- 改动：
  - **P0-82-1. `templates/prd.md` 删功能需求 P0/P1/P2 段**（~12 行）：与 AC 重复（AC frontmatter 已含 `priority: P0/P1/P2` 字段）+ AC 是验收契约 · 功能需求是非契约描述 → 重复
  - **P0-82-2. `templates/prd.md` API 契约子段加产品视角边界注**（~8 行）：✅ 写 method/path/入参出参业务字段含义/错误情况下的用户感知/接口能力承诺；❌ 不写 鉴权方式/限流策略/序列化协议/SLA/内部缓存/数据库交互/HTTP status code/错误对象 schema（这些归 TECH.md）
  - **P0-82-3. `templates/prd.md` 顶部说明同步**：业务类必填项从「用户故事 / 功能需求 / 埋点需求」改为「用户故事 / 埋点需求」+ 加 v7.3.10+P0-82 删除标注
  - **P0-82-4. 版本号 + CHANGELOG**（7.3.10+P0-81 → 7.3.10+P0-82；init-stage.md SKILL_VERSION 期望同步）
- **P0-79 元规则触发评估**（v7.3.10+P0-79 文件体量物理上限）：
  - 涉及文件：`templates/prd.md` ~340 行（超 300 上限）
  - 本 patch 净加：-12 行（**净删** ~12 行 + 加边界注 ~8 行 - 删功能需求 ~20 行）
  - 是否触发拆分：否 · 本 patch 是减法 · **降低**累积压力（~340 → ~328）✅ 符合元规则方向
- **加 1 删 1 元规则核算**：
  - **加**：~8 行（API 契约边界注）
  - **删**：~20 行（功能需求 P0/P1/P2 段 + 顶部说明微调）
  - **净删 ~12 行**（首次实质性净删 patch · 之前多为净加）
  - **不增加 PMO 负担**：PM 起草少 1 段（功能需求）+ 写 API 契约时清楚边界
  - **核心收益**：
    - PRD 主体段数 12 → 11（实质删 1 段）
    - 消除 AC ↔ 功能需求重复（AC 是单源 · priority 字段是分级权威）
    - 明确 API 契约的产品视角边界（防 PM 越界写鉴权/限流/SLA）
    - 中台子项目场景下 PRD 仍是产品对消费方的核心承诺（API 契约保留）
  - **"重新触发回来"防护**：未来若有人想再加"功能需求 P0/P1/P2"段 → cite 本 patch 反例（与 AC 重复）+ AC priority 字段已能承载分级
- 与已有规则的关系：
  - **`templates/prd.md` AC frontmatter `priority: P0/P1/P2`**（v7.3 起即有）：本 patch 让 AC 成为优先级单源 · 删冗余的功能需求段
  - **`templates/prd.md` AC `category` 字段**（v7.3.10+P0-68 functional/telemetry/logging/...）：埋点需求段保留 · 与 telemetry 类 AC 互补（埋点段定义业务数据维度 / telemetry AC 定义验证标准）
  - **`templates/prd.md` Out of Scope 段**（v7.3.10+P0-77）：本 patch 与之协作（Out of Scope 是产品边界 / 删功能需求是减冗余）
  - **`stages/blueprint-stage.md` TECH 起草规范**（v7.3.10+P0-46）：本 patch 不动 TECH.md · API 鉴权/限流/SLA 仍归 TECH（不需要新增接收点）
- 不动:
  - 埋点需求段（保留 · 产品定义"我们要看什么数据"）
  - 消费方分析段（保留全 4 子段：消费方列表 / API 契约 / 兼容性承诺 / 接入计划）
  - 业务流程图 / 时序图段
  - 验收标准段 + AC frontmatter schema
  - PM 起草 checklist 主体（仅顶部说明微调）
  - PRD-REVIEW.md schema
- 影响面：1 个文件（templates/prd.md）+ 元数据 2 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 PM 起草 PRD 不再写"功能需求 P0/P1/P2"段（AC 已分优先级）
  - 下次中台 PM 写 API 契约时遵守产品视角边界（不写鉴权/限流/SLA）
  - 长期：观察是否有 PM 因为找不到"功能需求"段而把功能描述塞到 AC description（AC description 应保持简洁 · 业务行为级）

---

## v7.3.10 + P0-81

> v7.3.10+P0-81 triage 默认 pull 模式（根本性改造 · 方向 C 一次性到位）：实战 case 暴露用户「看下 aon-link 是否需要 argocd」这种调研型需求被 PMO 走 20+ 工具调用读 init-stage / SKILL / flow-transitions / triage-stage / pmo / KNOWLEDGE / teamwork_space / ADR INDEX / localconfig 一堆框架文档 · 1 分多钟才开始 grep 实际代码。**根因**：triage 默认 push 模式 · 不分轻重一律前置全量扫描。**修复**：意图分流前置 → 轻型走 pull · 重型走 push。

### P0-81：triage 默认 pull 模式（意图轻重分流 + 按需 read）

- 触发：用户实战 case「$teamwork 看下 aon-link 相关的逻辑，是否需要在 argocd 创建个项目」+ 用户拍板「按 C 改造，一次性改完」
- 设计哲学：
  - **Push → Pull**：当前是 push 模式（先把所有 context 读完再处理）· 改成 pull 模式（先看实际东西 · 缺 context 时再 read）
  - **意图分流**：轻型（看下/调研/解释）vs 重型（做/实现/修复/Feature）
  - **Safe failover**：判定不明默认走轻型（轻 → 重升级成本低 · 重 → 轻已浪费的工具调用回不来）
- 改动：
  - **P0-81-1. `stages/triage-stage.md` 在 Step 1 后加 Step 1.5「意图轻重分流」段**：
    - 16 个轻型关键词清单（看下/看一下/看看/调研/解释/怎么/why/为什么/是否需要/是否应该/给我看/是否符合/分析下/检查下/定位/排查）
    - 重型识别信号（明确动词：做/实现/修复/改/创建/优化 + 明确需求规格 + 已锁定流程信号）
    - Safe failover 默认走轻型
    - 5 类轻型禁止动作清单（不读框架文档 / 不全量扫 KNOWLEDGE/ADR / 不外部模型探测 / 不创建 state.json / 不输出 4 选 1）
  - **P0-81-2. `stages/triage-stage.md` 加 Step 1.6「Pull 路径（轻型直接执行）」**：
    - 5 步骤（grep 关键词 → Read 关键文件 ≤5 个/≤500 行 → 直接给初步答案不暂停 → 按需补 read（KNOWLEDGE/ADR/teamwork_space）→ 答案末尾跟进引导切重型）
    - Pull 模式核心原则：先看实际东西 → 缺 context 时再 read
  - **P0-81-3. `stages/triage-stage.md` Step 2/3/4/6 加注「重型路径专用」执行条件**：
    - Step 2 KNOWLEDGE 扫描 / Step 3 ADR 扫描 / Step 6 跨 Feature 冲突：仅重型时执行 · 轻型跳过
    - Step 4 角色可用性扫描：原 v7.3.10+P0-30 已加问题排查跳过 · 本 patch 加 v7.3.10+P0-81 轻型跳过条件
  - **P0-81-4. `roles/pmo.md` ADR/KNOWLEDGE 扫描段加 pull 模式硬规则**：轻型意图不前置全量扫 · 走 Pull 路径 · 重型才走 push 全扫
  - **P0-81-5. `FLOWS.md` 问题排查梳理流程加 pull 模式说明**：cite triage-stage Step 1.5/1.6 · 与现有 P0-30 简化协作（信号置信度跳过 4 选 1 + P0-81 跳过前置全扫 = 双层减负）
  - **P0-81-6. 版本号 + CHANGELOG**（7.3.10+P0-80 → 7.3.10+P0-81；init-stage.md SKILL_VERSION 期望同步）
- **P0-79 元规则触发评估**（v7.3.10+P0-79 文件体量物理上限）：
  - 涉及文件：`stages/triage-stage.md` 877 行 / `roles/pmo.md` 1812 行 / `FLOWS.md` 871 行（3 个均远超 300 上限）
  - 本 patch 净加：~85 行
  - 是否触发拆分：暂不（核心改造类 patch · 不在同 patch 内强制拆分以免过度膨胀变更面）· 累积压力增加（未来涉及这 3 个文件的 patch 应优先评估拆分 reference）
- **加 1 删 1 元规则核算**：
  - **加**：~85 行（triage-stage.md Step 1.5/1.6/Step 2-4-6 注解 + pmo.md hard rule + FLOWS.md 注解 + 元数据）
  - **删**：未删（根本性行为改造 · 不是冗余清理）
  - **不增加 PMO 负担**：判定逻辑 PMO 本就要做（识别意图）· 显式 Step 1.5 是把隐性能力变显性硬规则
  - **核心收益**：
    - 轻型需求工具调用 ↓ 80%+（实证 case 20+ 调用 → ~5 调用）
    - prompt cache 友好（不读 init-stage / SKILL / triage-stage 等框架文档）
    - 用户响应延迟 ↓（实证 case 1m 17s → ~10s）
    - 重型需求行为不变（push 全扫保留 · 不破坏 Feature/Bug/敏捷需求 流程质量）
  - **"重新触发回来"防护**：未来若有人再让 PMO 在调研型需求前置全扫 → cite 本 patch 反例（aon-link case）+ Step 1.5 关键词清单
- 与已有规则的关系：
  - **v7.3.10+P0-30 问题排查跳过 4 选 1**：保留 + 互补（P0-30 跳过流程确认 / P0-81 跳过前置全扫 = 双层减负）
  - **v7.3.10+P0-49-A triage 决策呈现替代履职报告**：保留 + 协作（轻型走 Pull 路径 / 重型仍走 P0-49-A 决策呈现）
  - **v7.3.10+P0-72 PMO 直接判定（删探测脚本）**：保留 + 协作（轻型跳过角色扫描 = 不调用 PMO 直接判定 · 重型才走判定）
  - **v7.3.10+P0-73 PRD 起草前代码 Read**：互补（PRD 起草前 Read 是重型流程内的 Read · pull 模式是 triage 入口的 Read · 两者不同时机）
- 不动:
  - 重型流程的 Step 2-8 全部行为（保留 push 模式 · 仅加注"轻型时跳过"）
  - 六种流程类型闭集（不变 · 轻型不创建新流程 · 是问题排查流程的子模式）
  - state.json schema（轻型不创建 state.json · 不需要 schema 改动）
  - Feature / Bug / 敏捷需求 / Feature Planning / Micro 各自的入口 / 流程
  - PRD 起草前代码 Read（P0-73 · 不变）
- 影响面：3 个文件（stages/triage-stage.md / roles/pmo.md / FLOWS.md）+ 元数据 2 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 triage 收到「看下 X 是否需要 Y」类需求 → PMO 应直接 grep + 按需 read · 不前置读框架文档
  - 下次 triage 收到「实现 X 功能」类需求 → PMO 仍走 push 全扫
  - 用户体感：轻型需求响应延迟显著下降 · 重型需求行为无变化
  - 长期：观察 1-2 周后看是否需要扩展轻型关键词清单（如发现某关键词命中率高但不在清单 → 加进去）
- 后续可选（暂不做）：
  - 轻型关键词支持用户自定义（localconfig 加 `triage_lightweight_keywords` 字段）
  - 轻型 Pull 路径加输出 token 上限（防止 PMO grep 太多文件后给冗长答案）

---

## v7.3.10 + P0-80

> v7.3.10+P0-80 MR URL target_branch 必含硬规则（实战补强）：用户反馈"ship 阶段创建 mr 的地址，需要指定目标分支名称"。检查发现 spec 模板已正确包含目标分支字段（4 种平台模板都写了），但 v7.3.10+P0-70 实战 case 截图显示 PMO 实际生成的 URL **漏掉了 `target_branch` 参数**（只有 `source_branch`）→ 用户在平台合 MR 时会默认走 default branch（如 main），而非 state.merge_target（如 staging）→ 可能合到错误目标分支 · 严重时丢业务代码。本 patch 加 PMO self-check 硬规则 + 4 平台必含关键字表 + 反例对比。

### P0-80：MR URL target_branch 必含硬规则（PMO self-check）

- 触发：用户反馈「ship 阶段创建 mr 的地址，需要指定目标分支名称」+ P0-70 实战截图暴露 URL 漂移
- 根因分析：spec 已对（4 种平台模板都含 target_branch）· PMO 实际生成时漏字段 → 是 PMO 执行漂移而非 spec 不全
- 改动：
  - **P0-80-1. `stages/ship-stage.md` Step 2.3 加 target_branch 必含硬规则**（在 URL encoding 说明之后 / 记入 state 之前）：
    - 4 平台必含关键字表（github/gitee 走 compare 路径形式 / gitlab 走 query target_branch / bitbucket 走 query dest）
    - PMO self-check 步骤（生成 URL 后 grep 关键字确认 · 缺失 = 流程偏离 · 重生成）
    - 反例（v7.3.10+P0-70 实战截图原文）+ 正确示例对比
  - **P0-80-2. 版本号 + CHANGELOG**（7.3.10+P0-79 → 7.3.10+P0-80；init-stage.md SKILL_VERSION 期望同步）
- **P0-79 元规则触发评估**（v7.3.10+P0-79 新增 · 文件体量物理上限）：
  - 涉及文件：`stages/ship-stage.md`
  - 当前行数：899（远超 300 行上限）
  - 本 patch 净加：~14 行
  - 是否触发拆分：暂不（实战补强类微 patch · 强制拆 reference 子文件成本高于本次收益）· 累积压力增加（未来涉及 ship-stage.md 的 patch 应优先评估拆分）
- **加 1 删 1 元规则核算**：
  - **加**：~14 行（ship-stage.md 硬规则段 + 反例 + 正确示例 + 元数据）
  - **删**：未删（实战补强 · 防 PMO 漂移）
  - **不增加 PMO 负担**：URL 生成本就要做 · 加 self-check 一行（grep 关键字）· 增量极小
  - **核心收益**：
    - 防"合到错误目标分支"的严重事故（merge_target=staging 但 PMO URL 漏 target → 用户合到 default=main → 业务代码进错主干）
    - 4 平台关键字表 = PMO 生成 URL 的格式权威源
    - 反例 = 防漂移触发器（未来 PMO 生成 URL 看到反例就警觉）
  - **"重新触发回来"防护**：未来若 MR URL 又出现漂移 → cite 本 patch 反例 + 4 平台关键字表
- 与已有规则的关系：
  - **`stages/ship-stage.md` Step 2.3 MR URL 模板**（v7.3.10+P0-29）：本 patch 不改模板内容 · 加 self-check 硬规则强制 PMO 校验输出
  - **P0-70 长 URL 不进表格列硬规则**：本 patch 与之协作（P0-70 管 URL 渲染格式 / P0-80 管 URL 字段完整性）
  - **P0-67 路径边界硬规则**：保留不变
  - **P0-79 文件体量物理上限元规则**：本 patch 触发评估（ship-stage.md 899 行 · 暂不拆分 · 累积压力）
- 不动:
  - 4 平台 URL 模板内容（保留 · 已正确）
  - 第一段报告模板
  - state.json `mr_create_url` 字段（不变）
  - Ship Stage 双段结构
- 影响面：1 个文件（stages/ship-stage.md）+ 元数据 2 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 Ship Stage 第一段生成 MR URL 时 PMO 输出"URL self-check ✅ 含 {target_branch / dest / compare path}"行
  - 用户在平台点击 MR URL 时目标分支自动正确填充为 state.merge_target
  - 长期：是否在 state.json 加 `state.ship.mr_url_target_check: true|false` 字段强制 PMO 写入校验结果（暂不加 · 等实战触发再决定）

---

## v7.3.10 + P0-79

> v7.3.10+P0-79 文件体量物理上限元规则（借鉴 mattpocock/skills write-a-skill）：mattpocock/skills 的 write-a-skill skill 强调"主文件 ≤ 100 行 + reference 外移"作为防膨胀物理约束。teamwork v7.0 → v7.3.10+P0-78 累积 78 个 P0 patch · 各核心文件（SKILL.md / RULES.md / FLOWS.md / pmo.md / ship-stage.md 等）膨胀到 500-1500+ 行 · prompt cache 不友好 + 阅读断片。本 patch 把这条物理约束加到 P0 patch 设计契约（与 P0-48 的"加 1 删 1 元规则"互补 · 一个管逻辑层一个管物理层）· **渐进式适用**（不强求一次到位 · 未来涉及超量文件的 patch 必须先评估瘦身机会）。

### P0-79：文件体量物理上限元规则（≤ 300 行 + 渐进式瘦身）

- 触发：mattpocock/skills 调研拍板「100 行主文件硬约束 = 长期 ROI 最高的元规则」+ 用户拍板「按建议推进」
- 设计哲学（来自 write-a-skill）：**主文件 + reference 子文件**双层结构 · 主文件做门面 · reference 按需引用。teamwork 单体框架适配为：主规范文件 ≤ 300 行 · 超出必拆 reference / 单源化 / 删冗余
- 改动（仅元层级 · 不动具体规则）：
  - **P0-79-1. `SKILL.md` 加「文件体量物理上限」元规则段**（在 P0-48 "P0 patch 设计契约"段之后 · ~30 行）：
    - ≤ 300 行硬上限（适用 roles/ stages/ standards/ rules/ 顶层 *.md）
    - 4 种处理路径（拆 reference / 单源化 / 删冗余 / 拆段落到独立 .md）
    - 5 类例外（templates/CHANGELOG/OPTIMIZATION-PLAN/flow-transitions.md/ 单元测试 索引等内容客观决定长度的文件）
    - 渐进式落地策略（现有超量文件不强制立即拆 · 未来涉及该文件的 P0 patch 必须先评估瘦身机会）
    - PMO 校验规则（起 P0 patch 时若涉及 > 300 行文件 · 必须输出"瘦身机会评估"行 · 含目标文件 + 当前行数 + 本 patch 净变化 + 是否触发拆分）
  - **P0-79-2. 版本号 + CHANGELOG**（7.3.10+P0-78 → 7.3.10+P0-79；init-stage.md SKILL_VERSION 期望同步）
- **加 1 删 1 元规则核算**：
  - **加**：~30 行（SKILL.md 元规则段）
  - **删**：未删（元规则补强 · 防膨胀逆向压力）
  - **不增加 PMO 负担**：仅在起 P0 patch 时多输出一行"瘦身机会评估"（已有 P0-48 元规则的"加 1 删 1 = ?"输出 · 加一行 · 增量极小）
  - **核心收益**：
    - 与 P0-48 互补（P0-48 管逻辑层加 1 删 1 / P0-79 管物理层文件体量）
    - 倒逼后续 P0 patch 物理瘦身（每次涉及超量文件都要评估 · 累积压力）
    - 长期 ROI（不强制本次拆 · 多个 P0 累积后自然瘦身）
  - **"重新触发回来"防护**：未来若有人再次让某文件膨胀到 500+ 行而无瘦身评估 → cite 本 patch 的元规则
- 与已有规则的关系：
  - **P0-48 P0 patch 设计契约 / 加 1 删 1 元规则**（v7.3.10+P0-48）：本 patch 是物理层补充 · 在同一段后追加（不替换 · 不破坏 P0-48 主体）
  - **P0-22 KNOWLEDGE.md 体量上限 300 行**（v7.3.10+P0-22）：本 patch 把同样的体量上限推广到所有主规范文件
  - **P0-23 prompt cache 规范**（v7.3.10+P0-23）：本 patch 是 prompt cache 友好的物理基础（短文件更易命中缓存）
- 不动:
  - 现有文件具体内容（不强制立即瘦身）
  - 模板文件 / CHANGELOG / OPTIMIZATION-PLAN / flow-transitions.md 等例外类（保持原长度）
  - P0-48 加 1 删 1 元规则（保留 + 互补）
- 影响面：1 个文件（SKILL.md）+ 元数据 2 个（init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 P0 patch 涉及 > 300 行文件时，PMO 输出"瘦身机会评估"行
  - 未来 5-10 个 P0 patch 累积下来观察各核心文件行数变化趋势（应单调递减或持平 · 不再单调递增）
  - 长期：可考虑加自动化检查（pre-commit hook 计算 *.md 行数 · 超量警告）· 但当前不强加 hook · 等用户 P0-80 决策再说

---

## v7.3.10 + P0-78

> v7.3.10+P0-78 goal-plan grilling 增强（mattpocock/skills grill-with-docs + improve-codebase-architecture 综合借鉴）：从 grill-with-docs CONTEXT-FORMAT.md / ADR-FORMAT.md 深度调研 + improve-arch 8 词架构词汇 + "删除测试" 启发式合并为单一 P0。补 4 个 teamwork 真实 gap：(1) 多角色术语漂移（业务术语 + 通用架构词汇都缺统一词典）(2) ADR 泛滥（缺三条门槛 + 7 类合格列表 + 极简模板）(3) review finding 猜测式（无 code_evidence 字段 → reviewer 不读代码就提问题）(4) 知识写入延迟批处理（应 inline 实时写）。

### P0-78：goal-plan grilling 增强（综合 6 项打包）

- 触发：grill-with-docs 深度调研 + 用户拍板「按建议推进」
- 设计哲学：
  - "Be Opinionated"（grill-with-docs · CONTEXT-FORMAT.md）：术语挑一个最好的 · 其他列 Avoid 别名
  - "Capture decisions inline"（grill-with-docs）：澄清 / 决策一旦收敛立即写知识库 · 不批处理
  - "Use ADRs sparingly"（grill-with-docs · ADR-FORMAT.md）：三条门槛全 ✅ 才产 ADR · 防泛滥
  - "Validate against code"（grill-with-docs）：review finding 不接受口头 · 必 cite 代码 location
  - "Statistical Mechanics"（improve-arch · 删除测试 / 两个 adapter 才抽象）：判断模块是否 shallow + 防过度设计
- 改动（6 项打包 · 全部 inline 加 · 不破坏现有结构）：
  - **P0-78-1. `templates/adr.md` 加三条门槛 boolean checkbox + 7 类合格 ADR 列表 + 极简模板说明**：在原"3 问触发器"之后加更精准的「三条门槛 boolean checkbox」（Hard to reverse / Surprising without context / Result of real trade-off）+ 7 类显式合格 ADR（架构形状 / 跨 Context 集成模式 / 锁定的技术选型 / 边界与范围 / 偏离明显路径 / 代码不可见的约束 / 拒绝方案非显然）+ 极简 ADR 模板说明（1-3 句话即可 · 默认轻量 · 复杂决策才扩到完整结构）
  - **P0-78-2. `templates/knowledge.md` 加 `## 📚 Glossary` 段**：业务术语词典（Term / 一句话定义 / Avoid 别名）+ 通用架构词汇 8 词（Module / Interface / Depth / Seam / Adapter / Leverage / Locality / Boundary）+ Relationships 实体关系段 + "删除测试"启发式 + "两个 adapter 才抽象"规则
  - **P0-78-3. `templates/knowledge.md` 加 `## 🔀 Flagged Ambiguities` 段**：澄清过的歧义记忆（FA-NNN）· 防止下个 Feature 来同样的词又得 PMO 重新询问澄清 · 实时（inline）写入
  - **P0-78-4. `templates/prd.md` PRD-REVIEW schema 加 `code_evidence` 字段 + `terminology-ambiguity` category**：finding `category=technical-consistency` 时必填 `code_evidence.{file_path, line_range}` —— 防止"猜测式 finding"（reviewer 没读代码就提问题）· 加 `category=terminology-ambiguity` 触发 Flagged Ambiguities 实时写入
  - **P0-78-5. `roles/pmo.md` KNOWLEDGE 写入硬时机段**：加两行新触发条件（术语漂移 → Glossary/Flagged Ambiguities · 评审 REJECT → Out of Scope）+ 加 "实时 inline 写入" 硬规则段（禁止延后到 Feature 完成报告时批处理）
  - **P0-78-6. `standards/backend.md` / `frontend.md` 加模块设计判定段**：cite KNOWLEDGE 单源（统一架构词汇 8 词 + "删除测试" 启发式 + "两个 adapter 才抽象" 规则）· frontend.md 仅加 cite + 前端场景映射（Module = React Component / Hook 等）
- **加 1 删 1 元规则核算**：
  - **加**：~120 行（adr.md ~25 行 + knowledge.md ~50 行 + prd.md ~10 行 + pmo.md ~5 行 + backend.md ~10 行 + frontend.md ~5 行 + 元数据）
  - **删**：未删（实证补强 · 防漂移 / 防泛滥 / 防猜测 / 防延迟）
  - **不增加 PMO 负担**：
    - ADR 三条门槛是写 ADR 时的判断（不写也不必判断 · 仅在触发时检查 · 4 个 boolean）
    - Glossary 是 KNOWLEDGE 一段（PMO 起草前已扫 · 不增加扫描动作）
    - Flagged Ambiguities 是术语澄清时实时写一行（不批处理反而省 token）
    - code_evidence 是 reviewer 自己查代码（PMO 仅校验字段非空）
    - 实时 inline 写入只是把现有"完成报告时批处理"提前到"评审 verdict 出来时"
  - **核心收益**：
    - 多角色术语漂移↓（Glossary 单源）
    - ADR 泛滥↓（三条门槛 + 7 类显式列表）
    - review finding 猜测率↓（必填 code_evidence）
    - 知识遗忘率↓（实时 inline 写入）
    - 跨语言模块设计统一（backend / frontend cite 同一 KNOWLEDGE 单源）
- 与已有规则的关系：
  - **`templates/adr.md` 3 问触发器**（v7.3.10+P0-21）：保留 + 在其后加更精准的三条门槛 boolean checkbox（互补 · 不替换）
  - **`templates/knowledge.md` 三类内容**（v7.3.10+P0-22 / +P0-77 加 Out of Scope）：本 patch 加第五类（Glossary）+ 第六类（Flagged Ambiguities）· 体量上限不变（300 行）
  - **PRD-REVIEW schema** （v7.3.10+P0-34 + P0-34-A + P0-34-B）：本 patch 加 `code_evidence` 字段 + `terminology-ambiguity` category enum 值
  - **roles/pmo.md KNOWLEDGE 维护表**（v7.3.10+P0-22）：本 patch 加两行新触发 + 加实时 inline 写入硬规则段
  - **backend.md / frontend.md**：本 patch 加模块设计判定段 cite KNOWLEDGE 单源
  - **P0-77 Out of Scope 段**：本 patch 与之协作（Out of Scope = 拒绝方向 / Glossary = 术语词典 / Flagged Ambiguities = 澄清歧义 · 三类互补）
- 不动:
  - ADR 现有 50-150 行重模板结构（保留作为复杂决策时的完整版 · 极简版作为新选项）
  - KNOWLEDGE.md 体量上限 300 行
  - PRD-REVIEW frontmatter 主结构（仅扩展 findings[] 字段）
  - 评审循环逻辑（不变）
  - 模块设计原则（沿用 common.md 高内聚低耦合 · 本 patch 是判定方法补强）
- 影响面：6 个文件（templates/adr.md / templates/knowledge.md / templates/prd.md / roles/pmo.md / standards/backend.md / standards/frontend.md）+ 元数据 3 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 Goal-Plan / Blueprint Stage 多角色对话不再出现"组件 / 模块 / 服务"乱用
  - 下次 ADR 触发判断带三条门槛 boolean checkbox + 对照 7 类合格列表
  - 下次 review finding 含 code_evidence 字段（涉及代码现状的 finding）
  - 下次评审循环术语澄清后立即更新 KNOWLEDGE Glossary（不等完成报告）
  - 长期：Glossary 段量是否需要拆分子项目（可能需要 v7.3.10+P0-XX 时按子项目分）

---

## v7.3.10 + P0-77

> v7.3.10+P0-77 mattpocock/skills 借鉴微 patch 打包（4 项一行级改动 · TDD 反 horizontal slicing + DEBUG 前缀 + PRD Out of Scope 必填 + KNOWLEDGE Out of Scope 拒绝知识库）：把 4 个独立 ~3-15 行的微改动合并为单一 patch，避免每个微改动单独走完整 P0 流程。

### P0-77：mattpocock 微 patch 打包（4 个一行级改动合并）

- 触发：mattpocock/skills 调研 Tier 3 微 patch 打包 + 用户拍板「按建议推进」
- 设计哲学：每个微改动单独 ~3-15 行，单独立 patch 不经济。打包成单一 P0 + 各项独立标 v7.3.10+P0-77 来源 + 实战触发时各自可追溯
- 改动（4 项）：
  - **P0-77-1. `standards/tdd.md` Iron Law 段加两条硬规则**：
    - 禁止 horizontal slicing（"批量先写所有 TC 再批量实现"反 TDD 模式 · 必须 vertical slicing 每个 TC 走完红→绿→重构后再下一个）
    - NEVER refactor while RED（测试红时禁止重构 · 重构必须在绿色状态）
    - 来源：mattpocock/skills tdd skill
  - **P0-77-2. `standards/common.md` 加「四点五、调试日志规范」**：
    - `[DEBUG-{Feature}-{NNNN}]` 唯一前缀规则（grep 可定位）
    - Ship 前 grep `\[DEBUG-` 清理硬规则（命中即报 sanitize_log.suspicious_files）
    - 设计动机说明（不冲突 SLogger / 易识别 / Feature ID + 序号便于多 Feature 并行调试）
    - 来源：mattpocock/skills diagnose skill
  - **P0-77-3. `templates/prd.md` 加 `## Out of Scope` 必填段**（位于"待决策项"之前）：
    - 强制写出"本 Feature 不做什么"+ 简短理由
    - 与 KNOWLEDGE.md `## Out of Scope`（项目级长期拒绝记忆）联动
    - 降低后期"为什么没做 X"的拉扯
    - 来源：mattpocock/skills to-prd skill
  - **P0-77-4. `templates/knowledge.md` 加 `## ❌ Out of Scope` 拒绝知识库段 + 索引 + ID 编号规则**：
    - 拒绝过的方案/方向/Feature 候选记忆（OS-NNN 编号）
    - PMO Goal-Plan 起草前必扫描 OS-NNN 列表 + 发现 PRD 重新提被否方向 → 打回让 PM 改写或显式说明新触发原因
    - 防 AI 反复提同一个被否的方案
    - 来源：mattpocock/skills triage skill
- **加 1 删 1 元规则核算**：
  - **加**：~50 行（tdd.md 2 行 + common.md ~20 行 + prd.md ~10 行 + knowledge.md ~15 行）
  - **删**：未删（4 项均为补强 · 防漂移 / 防重复 / 防遗漏类）
  - **不增加 PMO 负担**：
    - tdd.md 反 horizontal slicing 是 RD 自查项 · 不增加 PMO 调度
    - DEBUG 前缀是 RD 自觉规范 + Ship Stage Step 1 已有 grep 流程（仅加新前缀模式）
    - PRD Out of Scope 是 PM 起草必填段（5 行内）
    - KNOWLEDGE Out of Scope 是 PMO Goal-Plan 入口扫描时多读一段
  - **核心收益**：
    - tdd.md：防"批量铺测试 + 批量铺实现"+ 防 RED 状态混入重构（典型 AI 失败模式）
    - common.md：临时调试日志一次 grep 全清 · 不污染生产
    - prd.md：scope 边界事前明确 · 减少 RD/QA review 时的"为什么没做 X"提问
    - knowledge.md：PMO Goal-Plan 起草前发现 PRD 重提被否方向直接打回 · 加 1 段 KNOWLEDGE 删 N 次重复讨论 token
- 与已有规则的关系：
  - **`standards/tdd.md` Iron Law**（v7.3.10+P0-63）：本 patch 在 Iron Law 段加两条新硬规则，不破坏原结构
  - **`stages/ship-stage.md` Step 1 净化**：本 patch 加 `\[DEBUG-` grep 模式 · 复用现有 sanitize_log.suspicious_files 通道
  - **`templates/prd.md` 模板**（v7.3.10+P0-47 合并版）：本 patch 在"待决策项"之前加新段 · 不破坏现有章节顺序
  - **`templates/knowledge.md` 三类内容**（v7.3.10+P0-22 收敛版）：本 patch 加第四类（Out of Scope · OS-NNN）· 体量上限不变（300 行）
  - **PMO Goal-Plan 入口扫描**（v7.3.10+P0-22）：本 patch 让 PMO 多扫一段 OS-NNN
- 不动:
  - tdd.md RED-GREEN-REFACTOR 5 步流程（保留）
  - common.md 五大段结构（在 §四 / §五 之间插新 §四点五 · 不破坏编号）
  - prd.md frontmatter schema（不变）
  - knowledge.md 三类索引 + 体量上限（保留）
- 影响面：4 个产物文件（standards/tdd.md / standards/common.md / templates/prd.md / templates/knowledge.md）+ 元数据 3 个（SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - tdd.md：下次 Dev Stage RD 不再批量先写所有 TC 再实现
  - common.md：下次临时调试日志带 `[DEBUG-F{NNN}-{NNNN}]` 前缀 + Ship Stage 前 grep 清理
  - prd.md：下次 PM 起草 PRD 含 Out of Scope 段（必填）
  - knowledge.md：下次 PMO Goal-Plan 入口扫描时多扫一段 OS-NNN · 发现 PRD 重提被否方向直接打回
- 后续可选（暂不做 · 等实战触发再加）：
  - PRD Out of Scope 与 KNOWLEDGE Out of Scope 自动联动（PMO 在 PRD 评审时检查 PRD 的 Out of Scope 是否与 KNOWLEDGE 的 Out of Scope 冲突）
  - DEBUG 前缀 IDE 高亮规则（可选 · 团队 IDE 配置层面 · 不在 skill 内）

---

## v7.3.10 + P0-76

> v7.3.10+P0-76 ⏸️ 暂停点 mode 字段二分（HITL/AFK · 借鉴 mattpocock/skills `to-issues` 的 HITL/AFK 概念）：当前 teamwork 的"强制保留 vs 豁免"二分散文化在三处文件（flow-transitions.md / pmo.md / FLOWS.md），实战中 PMO 判定要"对照清单"，措辞分散。本 patch 把概念**物理化为 mode 字段**（HITL = 强制保留 / AFK = auto 豁免），重命名段标题 + 加 mode 定义段 + 与 P0-75 决策类暂停点清单建立显式 ⊆ 关系（决策类 ⊆ HITL）。

### P0-76：⏸️ 暂停点 HITL / AFK mode 字段化

- 触发：mattpocock/skills 调研拍板「HITL/AFK 二分是最高 ROI 借鉴点」+ 用户拍板「按建议推进」
- 设计哲学（来自 to-issues skill）：每个 ⏸️ 暂停点显式标 `mode: HITL | AFK` —— 直接命中"暂停点过多 / 何时暂停散文式规则"两个核心痛点。teamwork 已有等价分类（强制保留 vs 豁免），仅缺**显式 mode 字段化**
- 改动（最小入侵 · 保留所有现有清单内容）：
  - **P0-76-1. `rules/flow-transitions.md` auto 豁免速查段**：段首 quote 重写为 mode 字段定义（HITL = 强制保留 / AFK = auto 豁免）+ 与决策类暂停点（P0-75）建立 ⊆ 关系；标题改名「强制保留清单」→「⏸️ HITL 清单」/「豁免示例」→「⏸️ AFK 示例」；表格内容不变
  - **P0-76-2. `roles/pmo.md` ⚡ auto 模式段**：段首 quote 加 mode 字段定义；标题改名「豁免暂停点」→「⏸️ AFK 暂停点」/「强制保留暂停点」→「⏸️ HITL 暂停点」+ 加 v7.3.10+P0-76 mode 标记；表格内容不变
  - **P0-76-3. `STATUS-LINE.md` 决策点参考路径段**：在决策类暂停点清单上方加注「与 mode 字段的关系：决策类暂停点 ⊆ HITL 集合」；非决策类不强制 references 段
  - **P0-76-4. 版本号 + CHANGELOG**（7.3.10+P0-75 → 7.3.10+P0-76；init-stage.md SKILL_VERSION 期望同步）
- **加 1 删 1 元规则核算**：
  - **加**：~25 行（3 处段首 mode 定义段 + 标题重命名 + STATUS-LINE 关系注解）
  - **删**：未删（最小入侵 · 现有清单内容全保留）
  - **不增加 PMO 负担**：mode 判定逻辑与原"强制保留 vs 豁免"判定**完全等价**——只是给概念起了正式名字
  - **核心收益**：物理化命名 → 跨文件引用一致性（pmo.md / flow-transitions.md / STATUS-LINE.md 三处用同一术语）；与 P0-75 决策类清单建立显式 ⊆ 关系；未来新增 ⏸️ 暂停点必须标 mode（隐性变显性）
  - **"重新触发回来"防护**：未来若有人增加 ⏸️ 暂停点不标 mode → cite 本 patch HITL/AFK 二分硬规则
- 与已有规则的关系：
  - **v7.3.9+P0-11 auto 模式豁免**：本 patch 是 P0-11 的"概念物理化"，不改判定逻辑
  - **v7.3.9+P0-11-A 意图承载元规则**：保留不变，作为 mode 判定的元规则
  - **v7.3.9+P0-11-B Browser E2E 默认跳过**：保留不变，归类为「⏸️ AFK 特殊」
  - **P0-75 决策类暂停点清单**：本 patch 建立 ⊆ 关系（决策类 ⊆ HITL · 自动含 📚 决策参考路径）
- 不动:
  - 强制保留清单 / 豁免示例 表格的具体行（内容不变）
  - 主转移表（Feature 流程 / Bug 流程 / 问题排查 / Planning / Micro / 通用）的 ⏸️暂停 标记（不逐行加 mode · 单源在速查表）
  - 元规则（意图承载豁免）
  - Browser E2E auto 默认跳过专项规则
- 影响面：3 文件（rules/flow-transitions.md / roles/pmo.md / STATUS-LINE.md）+ 元数据 2 个（SKILL.md / docs/CHANGELOG.md / stages/init-stage.md）
- 后续验证：
  - 下次 PMO 判定 ⏸️ 暂停点时显式说出 mode（HITL 或 AFK）
  - 未来新增暂停点必须在 flow-transitions.md HITL 清单或 AFK 示例中加一行 + 标 mode
  - 长期：mode 字段是否需要扩展到 dispatch task（task 本身不是暂停点 · 暂不扩展）

---

## v7.3.10 + P0-75

> v7.3.10+P0-75 决策点参考文档绝对路径硬规则（drill-down 到 evidence）：实战 case（AND-F062 Review QUALITY_ISSUE 决策点）暴露 PMO 给了 4 个选项 + 推荐理由，但**没列做这个决策需要参考的文档绝对路径**（REVIEW.md / external-cross-review/*.md / 涉及代码文件）。用户被迫凭记忆找路径或盲信 PMO 摘要做决策。同 case 还出现代码文件被错误包成 `[file.java](http://file.java)` markdown 链接 → 指向虚假 URL → 不可点击。本 patch 把"决策类暂停点必须列参考文档绝对路径"硬规则化，与 P0-67 路径边界 + P0-70 长 URL 不进表格列规则一脉相承。

### P0-75：决策点参考文档绝对路径硬规则

- 触发：实战 case + 用户拍板「我希望给我决策点的时候，把决策参考文档的绝对路径列出来，方便我点进去查看」+ 「ok」
- 设计哲学：**决策需要 evidence drill-down · 不能只给摘要黑盒** —— PMO 给决策点时，用户需要看 review 报告 / 外部视角原文 / 涉及代码文件等原始证据才能做 informed decision。光给"PMO 推荐 A · 理由 X"不够，必须把 X 背后的源文档绝对路径列出，让用户一键点开核对
- 改动：
  - **P0-75-1. `STATUS-LINE.md` 加「决策点参考文档绝对路径硬规则」段**（单源 · ~95 行）：
    - 决策类暂停点清单（10 类必含 references：QUALITY_ISSUE / PRD verdict / 流程类型识别歧义 / 评审组合改选 / PL-PM 业务方向分歧 / PM 验收 / Stage 入口偏差 / 升级确认 / ADR 候选 / 技术评审分歧）
    - 非决策类暂停点清单（5 类不强制：ok/反馈 / 用户手测 / push 失败 / 等待外部依赖 / 简单流程类型确认）
    - 渲染规范（紧跟 ⏸️ 决策点选项之后 / 状态行之前 · `📚 决策参考` 段标题）
    - emoji 约定（📄 文档 / 📝 代码 / 🔗 MR/外链）
    - 路径规范（继承 P0-67 / P0-70：必须绝对路径 · 前后 whitespace 边界 · 禁止 markdown 链接包裹 · 禁止只写文件名 / 相对路径 · 禁止挤入表格列）
    - 正反例对比（错误 = AND-F062 case 无路径 / markdown 链接漂移 · 正确 = 独立行 + emoji 引导 + 绝对路径）
    - 实施约束（PMO self-check 4 项扩展）
  - **P0-75-2. `stages/review-stage.md` QUALITY_ISSUE 修复循环规则段加 cite**：⏸️ 用户决策时必含「📚 决策参考」段 + 必列 REVIEW.md / external-cross-review/review-external-{model}.md（如启用） / 涉及代码文件 / 涉及测试文件 全部绝对路径（链接到 STATUS-LINE.md 单源）
  - **P0-75-3. 版本号 + CHANGELOG**（7.3.10+P0-74 → 7.3.10+P0-75；init-stage.md SKILL_VERSION 期望同步）
- **加 1 删 1 元规则核算**：
  - **加**：~110 行（STATUS-LINE.md 单源段 ~95 行 + review-stage.md cite 2 行 + 元数据）
  - **删**：未删（实战补强 · 决策质量收敛）
  - **不增加 PMO 负担**：PMO 本就要列决策选项 + 理由（已有），加 references 段只多列 3-5 个绝对路径（PMO 在 dispatch / 审查时已经知道这些路径）
  - **不破坏现有暂停点结构**：决策类暂停点清单是补充硬约束，不改 4 选 1 / 二选一基本格式；非决策类暂停点完全不受影响
  - **"重新触发回来"防护**：未来若 PMO 再次给决策点不列路径 / 用 markdown 链接漂移 → cite 本 patch 反例段（AND-F062 实战 case）
- 与已有规则的关系：
  - **P0-67 路径边界硬规则**：本 patch 是 P0-67 在决策点场景的特化（路径前后 whitespace · 不被标点紧贴）
  - **P0-70 长 URL / 路径不进表格列**：本 patch 沿用（绝对路径独立成行 · 不挤表格 · 不包 markdown 链接）
  - **P0-66 Final Response Preflight 4 项**：本 patch 是 Preflight 的扩展（决策类暂停点 self-check 加第 5 项 · references 段必含）
  - **emoji 间隔规则**（P0-62）：本 patch 用 📄 / 📝 / 🔗 引导路径，遵守半角空格规则
- 不动:
  - 4 选 1 / 二选一基本格式（不变）
  - PMO 推荐 + 理由（💡 + 📝）格式（不变）
  - 状态行 3 行结构（不变）
  - 红线 #10 暂停点必须给建议（💡）和理由（📝）（不变 · 本 patch 在其上加 references）
  - Final Response Preflight 4 项（不变 · 本 patch 加扩展项）
- 影响面：
  - 改动文件：3 个（STATUS-LINE.md / stages/review-stage.md / stages/init-stage.md）+ 元数据 2 个（SKILL.md / docs/CHANGELOG.md）
  - 单源策略：STATUS-LINE.md 是唯一权威源，其他 stage 通过 STATUS-LINE.md 单源继承（无需逐 stage 加 cite · 减少漂移面）
- 后续验证：
  - 下次 Review Stage QUALITY_ISSUE 决策点 / Goal-Plan PRD verdict 决策点 / PM 验收等决策类暂停点，PMO 必须输出「📚 决策参考」段 + 列绝对路径
  - 用户体验：点击路径直接跳转源文档 / 代码 → drill-down 到 evidence 不需翻历史
  - 同时杜绝 markdown 链接漂移（`[file.java](http://file.java)` 反模式）
  - 长期：如发现某些非决策类暂停点（如 push 失败降级）也希望列 references，可扩展清单 · 当前先按 10 类决策类清单约束

---

## v7.3.10 + P0-74

> v7.3.10+P0-74 Micro 流程加 Ship Stage 双段（合规收口）：实战 case（2026-04-30 / aifriend MICRO-001）暴露 Micro 走完用户验收后只剩「本地已修改未 commit / 未 push」，用户被迫追问"没 ship 么"才意识到代码没落库。根因分析：Micro 的省略**只在前端 5 个 Stage**（Plan / Blueprint / UI / Review / Test）—— 但代码最终都要发布，commit / push / MR 创建 / merge_target 落库这些动作对所有改动都一样必要。本 patch 把 Micro 流程接入完整 Ship Stage（缩简版 · 第二段无元数据更新但保留合入验证），与 Feature/Bug 的 Ship 行为统一。

### P0-74：Micro 加 Ship Stage 双段（commit + push + MR + 合入验证）

- 触发：实战 case + 用户拍板「我觉得要有完整的 ship 流程，因为 micro 只是规划和开发省了，最终改动还是要发布的，发布需要统一的 ship 规范」+ 「第二阶段需要验证是否合入目标分支」+ 「ok」
- 设计哲学（用户原话）：**"Micro 的省略只在规划和开发，发布需要统一的 ship 规范"** —— Micro 不是 Ship 的例外；Ship 是代码进入主干的必经门禁，对 Feature/Bug/Micro 一视同仁。第二段的合入验证（git merge-base）是流程闭环的最后一道证据
- 改动：
  - **P0-74-1. `stages/ship-stage.md` 加 Micro 流程缩简分支段**（在 Bug 缩简分支后 / ~110 行）：触发条件 + 与 Feature/Bug 的关键差异表（状态承载 = 主对话 / commit message = `micro: {简述}` / MR 标题 = `micro: {简述}` / Step 7+8 跳过 / Step 9 通常跳过 / 完成报告含合入证据）+ 各步骤差异说明 + Micro Ship 完成报告模板 + 入口前置依赖
  - **P0-74-2. `FLOWS.md` Micro 流程链路改写**：「用户验收 → 完成」改为「用户验收 → Ship Stage 第一段（commit + push + 创建 MR）→ ⏸️ 用户合 MR → Ship Stage 第二段（合入验证）→ ✅ 完成」
  - **P0-74-3. `FLOWS.md` Micro 自动流转图加 Ship 双段节点**：第一段（auto-commit / push feature / 创建 MR）+ ⏸️ MR pending + 第二段（git fetch + git merge-base --is-ancestor）+ 合入失败处理（concerns + 不进 ✅）
  - **P0-74-4. `FLOWS.md` PMO Micro 流程分析输出格式**：流程步骤描述从 5 步扩到 7 步（加 Ship 第一段 / Ship 第二段合入验证 / 完成报告含 commit hash + merge_commit_hash + 已合入证据）
  - **P0-74-5. `rules/flow-transitions.md` Micro 流程加 5 行 transition**：用户验收 → Ship 第一段（🚀 自动）→ ⏸️ 等用户合 MR → Ship 第二段合入验证（🚀 自动 git merge-base）→ ✅ 完成 / ⏸️ 合入失败两条出口
  - **P0-74-6. 版本号 + CHANGELOG**（7.3.10+P0-73 → 7.3.10+P0-74；init-stage.md SKILL_VERSION 期望同步）
- **加 1 删 1 元规则核算**：
  - **加**：~150 行（ship-stage.md Micro 缩简分支 ~110 行 + FLOWS.md 链路 + 自动流转图 + 输出格式 ~25 行 + flow-transitions.md 5 行 transition + 元数据 ~10 行）
  - **删**：未删（实战补强 · 流程一致性收敛 · 非冗余清理）
  - **不增加用户负担**：用户仍只需"验收"+"在平台合 MR"两个交互（与 Feature/Bug 一致）；新增的 PMO 动作（commit / push / MR 创建 / 合入验证）全自动
  - **不破坏 Micro 定位**："最短 RD 闭环"含义不变——省的是前端 5 个 Stage（Plan/Blueprint/UI/Review/Test），不是 Ship；Ship 不是 Stage 数量的累赘，是发布合规的必经门禁
  - **"重新触发回来"防护**：未来若有人把 Micro Ship 又砍掉以减少步骤 → cite 本 patch 的根因（实战暴露用户预期与流程契约错位）+ 「发布需要统一规范」原则
- 与已有规则的关系：
  - **Bug 流程 Ship 缩简分支**（v7.3.10+P0-36）：Micro 缩简版与 Bug 缩简版结构对称（都加在 ship-stage.md 主流程段之前作为分支说明）；Micro 比 Bug 更简（无元数据载体 · Step 7+8 跳过）
  - **auto-commit 通用规则**（v7.3.9 集中化 / rules/gate-checks.md）：Micro Ship 第一段的 commit 自动适用本规则，message 模板用 `micro: {简述}`
  - **红线 #1 Ship Finalize 例外**（v7.3.10+P0-32 / +P0-36）：Micro 不需要扩展第三类例外——Step 8 直接跳过（无元数据可 push），合规性比 Feature/Bug 更简单
  - **Ship Stage 双段结构**（v7.3.10+P0-29）：完全复用——第一段创建 MR + push feature / ⏸️ 用户合 MR / 第二段 finalize（Micro 的 finalize = 仅合入验证）
- 不动:
  - Ship Stage 主流程 Step 1-10（仅 Step 7 / Step 8 / Step 9 在 Micro 分支跳过）
  - Bug Ship 缩简分支
  - Feature Ship 主流程
  - 红线 #1 Ship Finalize 例外条款
  - Micro 准入条件 5 项（不变）
  - PMO→RD 身份切换硬规则（不变）
- 影响面：
  - 改动文件：5 个（stages/ship-stage.md / FLOWS.md / rules/flow-transitions.md / SKILL.md / stages/init-stage.md）
  - 元数据：CHANGELOG.md 一处
- 后续验证：
  - 下次 Micro 流程跑下来，PMO 在用户验收后自动进 Ship 第一段（commit + push + 创建 MR），输出 MR URL · ⏸️ 暂停等用户合 MR
  - 用户合 MR 后告知 PMO，PMO 执行 git merge-base --is-ancestor 验证 + 完成报告含 merge_commit_hash + "已合入 origin/{merge_target}" 证据
  - 用户预期闭环（"走完 = 已合入主干"）
  - 长期：Micro 是否需要给"批量 push"留一个豁免选项（多个连续 Micro 改动想合在一个 MR 里）？暂不预留，等实战暴露需求

---

## v7.3.10 + P0-73

> v7.3.10+P0-73 PM 起草前代码现状 Read 硬规则（防 PRD 与代码现状脱节）：用户提问"PM 在写 PRD 前是否对现有代码逻辑调研不全，导致输出方案不精确"——经分析现有 PM 起草 checklist（templates/prd.md L342+）只覆盖产品视角（产品目标 / AC / 影响范围 / 业务风险），且明文「PRD 不写什么」把"复用既有库 / 模式"全部下沉到 TECH.md（Blueprint Stage RD 写）→ PM 起草时**完全不读代码** → PRD 假设功能不存在但实际有 / AC 与现有约束冲突 / 漏边界场景 / 范围估算偏小。子步骤 3 RD 评审才发现 → 评审循环多 1-3 轮（实测）。本 patch 把"代码意识"从隐性期望提升为 PM 起草前必做硬规则：**只读不输出**（grep 关键词 + Read 3-5 个核心文件 / 5-10 min 内化），唯一痕迹 = `pm_self_check.code_context_read: true` boolean 承诺。

### P0-73：PM 起草前代码现状 Read（方向 B 只读不输出）

- 触发：用户提问 + 拍板「方向 B，只读不输出」+ 「ok」
- 设计哲学（用户原话）：**"PM 起草前必读代码模块，但不输出 brief"** —— 不增加新产物 / 不破坏 5 子步骤结构 / 不增加 PMO 调度负担；把代码意识做成 PM 角色契约（roles/pm.md）+ checklist 硬项（templates/prd.md），靠 boolean self_check 兜底执行
- 改动：
  - **P0-73-1. `templates/prd.md` PM 起草 checklist 加「起草前必读：代码现状 Read」段**：4 步流程（关键词提取 → grep + Glob 找入口 → Read 现有功能/约束/边界 → PM 起草时内化），4 条不要做的事，3 条执行边界（5-10 min · 只读不输出 · boolean 承诺）
  - **P0-73-2. `templates/prd.md` `pm_self_check` schema 加 `code_context_read: bool` 必填字段**：`code_context_read: false` = 跳过 Read 起草 → 子步骤 3 RD 评审若发现 AC 与代码现状冲突，PMO 自动 NEEDS_REVISION 打回 PM 重读重起
  - **P0-73-3. `roles/pm.md` 加角色契约 4 行**：起草 PRD 前必须 grep + Read 3-5 个核心模块 / 只读不输出 brief / 关键约束写入「待决策项」/ cite templates/prd.md
  - **P0-73-4. `stages/goal-plan-stage.md` 子步骤 1 PM 起草核心约束加 cite 1 行**：起草前 grep + Read 3-5 个相关核心模块（5-10 min · 只读不输出 · v7.3.10+P0-73）+ pm_self_check schema 加 `code_context_read` 字段
  - **P0-73-5. 版本号 + CHANGELOG**（7.3.10+P0-72 → 7.3.10+P0-73；init-stage.md SKILL_VERSION 期望同步）
- **加 1 删 1 元规则核算**：
  - **加**：~80 行（templates/prd.md 起草前必读段 + pm_self_check 字段说明 + roles/pm.md 角色契约 + goal-plan-stage.md cite）
  - **删**：未删（实证补强 · 非冗余清理）
  - **不增加 PMO 负担**：PM 自身在起草前 5-10 min Read · PMO 仅校验 self_check boolean（已有字段补一项 · 不加新调度逻辑）
  - **不破坏现有结构**：5 子步骤不变 · 不加新子步骤 · 不加 brief 文档产物
  - **"重新触发回来"防护**：未来若 PM 再次出现"PRD 与代码脱节"型评审循环 → cite 本 patch 的根因分析（隐性期望 vs 显性 checklist）
- 与已有规则的关系：
  - **PRD 起草 checklist 单源**（v7.3.10+P0-51）：本 patch 加在「通用 checklist」之前作为「起草前必读」段，不破坏 P0-51 单源结构
  - **职责正交**（v7.3.10+P0-46）：PRD 仍只回答 What/Why，TECH.md 仍回答 How；本 patch 不让 PM 写代码细节，只让 PM **知道代码现状** 写出与现状契合的 What/Why
  - **PM 对抗性自查**（v7.3.10+P0-34-B）：本 patch 是事前补强，对抗性自查是事后补强 · 二者互补
  - **子步骤 3 RD 评审**：仍然兜底（本 patch 不替代 RD 评审 · 是降低 RD 评审打回率）
- 不动：
  - PRD 模板主体结构（不加新章节）
  - PRD-REVIEW.md schema 主体（仅扩展 pm_self_check 一个字段）
  - Plan Stage 5 子步骤序列（不加新子步骤）
  - PMO 调度逻辑（仅多校验一个 boolean）
- 影响面：4 文件（templates/prd.md / roles/pm.md / stages/goal-plan-stage.md / stages/init-stage.md）+ 元数据 2 个（SKILL.md / docs/CHANGELOG.md）
- 后续验证：
  - 1-2 个真实 Feature 跑下来后，对比子步骤 3 RD 评审"AC 与代码现状冲突"类 finding 数量降幅
  - 如发现 PM 偷读不读（`code_context_read: true` 但实际没读，仍出现冲突 finding）→ 升级到方向 B 原版（加 brief 输出 · 加 PMO 校验段）
  - 如发现 PM 读太多（10+ 文件 / 1000+ 行 / 写代码细节进 PRD）→ 收紧执行边界（强化"3-5 个文件 / 500 行内 / 5-10 min"上限）
  - 长期：可考虑把"代码现状 brief"作为可选产物（小 Feature 跳过 / 大 Feature 必填）

---

## v7.3.10 + P0-72

> v7.3.10+P0-72 删除探测脚本 + 回退 P0-71（PMO 直接判定）：用户拍板"宿主探测不该是脚本职责——PMO 自身就在宿主里运行，自知"。先前 `templates/detect-external-model.py` 基于项目根的 `.claude/` / `.codex/` / `.agents/` 目录标记判定主对话宿主，但目录标记反映**项目历史**（曾被哪些宿主访问过 / 装过 teamwork skill），不反映**当前对话宿主**——实战 WEB-F028 暴露 Codex 主对话被误判为 claude-code。本 patch 把宿主判定职责彻底从脚本回收到 PMO，删除脚本本体；同期回退 P0-71 "Stage 入口重探测"（再探测错的还是错的，根因是探测方法不可靠，不是缺重探测）。

### P0-72：删除探测脚本 + PMO 直接判定 + 回退 P0-71

- 触发：用户实战 WEB-F028 + 拍板"探测脚本是否考虑去掉，PMO 知道，以 PMO 口径为准"
- 设计哲学（用户原话）：**"没必要重探测，启动 teamwork 探测就可以，之前的问题在于探测错误"** —— 修方向不是"加重探测兜底"而是"让初始判定就对"。PMO 自身在宿主里运行，自知；脚本反而是错误信号源
- 改动：
  - **P0-72-1. 删 `templates/detect-external-model.py`**（~140 行）：宿主判定职责从脚本回收到 PMO
  - **P0-72-2. 重写 `standards/external-model.md` §四**：从「E2 PMO 运行时探测（基于探测脚本）」改为「E2 PMO 直接判定（自报宿主 + `command -v` 检查 CLI）」3 步流程；删除 P0-71「Stage 入口宿主重探测硬规则」段（~70 行）；删除 P0-72 早期版本的「PMO 自我校验硬规则」段（~50 行 · 根因消失则补丁也没必要保留）
  - **P0-72-3. `stages/review-stage.md` §4 外部模型选择**：删 P0-71 「必须 Stage 入口重探测脚本」cite，改为 P0-72 「PMO 自报宿主 + 应用 E1 同源约束」
  - **P0-72-4. `stages/triage-stage.md` Step 4 + 入口 Read 顺序 + 关系表**：探测脚本调用改为 PMO 自报 + `command -v` bash 一行；删 detect-external-model.py 引用
  - **P0-72-5. `roles/pmo.md` Step 1-2**：「调用探测脚本 + 渲染探测段」改为「PMO 自报宿主 + bash `command -v` + 渲染判定段」；硬规则段同步措辞
  - **P0-72-6. `templates/external-cross-review.md`** + **`roles/external-reviewer.md`** + **`claude-agents/README.md`** + **`STATUS-LINE.md`** + **`STANDARDS.md`** + **`SKILL.md` 索引**：清掉所有 detect-external-model.py 活引用 + 措辞从「探测脚本 / 探测段」改为「直接判定 / 判定段」
  - **P0-72-7. `templates/feature-state.json`** 两处 _note：detect-external-model.py 改为 PMO 直接判定
  - **P0-72-8. 版本号 + CHANGELOG**（7.3.10+P0-71 → 7.3.10+P0-72；init-stage.md SKILL_VERSION 期望同步）
- **加 1 删 1 元规则核算（强力净删）**：
  - **删**：脚本本体 ~140 行 + external-model.md P0-71 重探测段 ~70 行 + P0-72 早期 PMO 自我校验段 ~50 行 = **~260 行**
  - **加**：external-model.md PMO 直接判定段 ~50 行 + 各文件措辞调整 ~30 行 = ~80 行
  - **净删**：~180 行 + 一个常驻脚本文件
  - **不增加 PMO 负担**：PMO 本就要自知宿主（每次 Stage 入口本就要做的事）；判定职责从外部脚本回收到 PMO，少一层间接、少一类失败模式
  - **"重新触发回来"防护**：未来若有人想"再加重探测脚本"→ cite 本 patch 的根因分析（目录标记不反映当前对话）+ "PMO 直接判定"的设计哲学
- 与已有规则的关系：
  - **P0-71 Stage 入口重探测**：废止（再探测错的还是错的）；spec 跨 session 切宿主的处理由「PMO 在每个 Stage 入口自报宿主」单源承载（external-model.md §四「跨 session 切宿主的处理」段）
  - **P0-65 Codex 沙箱认证**：保留（dispatch 时 CLI 调用失败的运行时降级仍由 E3 兜底）
  - **E1 异质性 / E3 失败降级**：保留不变（核心规则与脚本无关）
  - **state.json schema**：不变（仍有 host_main_model / host_detection_at / available_external_clis 字段）
- 不动：
  - 同源约束 / 异质性 E1 / 失败降级 E3 等核心规范段
  - state.json 字段定义
  - claude-agents / codex-agents 调用入口规范
  - 候选清单（codex / claude）
- 影响面：
  - 删除文件：1 个（templates/detect-external-model.py）
  - 修改文件：10 个（standards/external-model.md / stages/review-stage.md / stages/triage-stage.md / roles/pmo.md / roles/external-reviewer.md / templates/external-cross-review.md / templates/feature-state.json / claude-agents/README.md / STATUS-LINE.md / STANDARDS.md / SKILL.md / docs/CHANGELOG.md / stages/init-stage.md）
- 后续验证：
  - 下次 Feature triage 时 PMO 输出「🌐 外部模型判定」段（不是「外部模型探测」），首行宿主由 PMO 自报，不读项目目录标记
  - 跨 session 切宿主时 PMO 自报值更新 + state.concerns 记录漂移 + 主对话声明切换
  - 后续如果 PMO 自报失误 / 不可靠 → 不复活脚本，而是补强 PMO 自报的规则（如增加 system prompt 自识别提示）

---

## v7.3.10 + P0-71（已废止 · v7.3.10+P0-72 删除探测脚本时一并回退）

> v7.3.10+P0-71 跨 session 切宿主漂移防护（Stage 入口宿主重探测）：用户实证 Codex CLI 主对话执行 Review Stage 时沿用 state.json 旧的 `host_main_model: claude-code` / `model: codex`，导致 codex 跟当前主对话同源仍被误用作 external（违反 E1 异质性）。用户自我纠正 + 加降级（Claude CLI 不可用如实记录不伪造）。本 patch 把这个实战教训硬规则化：standards/external-model.md §四 加「Stage 入口宿主重探测硬规则」+ review-stage.md §4 外部模型选择段加 cite + 4 类禁止形态 + 7 步正确处理流程。

### P0-71：Stage 入口宿主重探测（跨 session 漂移防护）

- 触发：Codex CLI 主对话执行 Review Stage 时盲信 state.json 旧 host_main_model（claude-code 时期），导致 model: codex 沿用错误（同源失去异质 review 价值）
- 设计哲学：**state.json 缓存创建时的宿主，但 Stage 实际执行时宿主可能已变**（跨 session 切设备 / 切宿主 / 切 worktree 上下文）。"运行时延后检测"原则只覆盖 CLI 调用失败，**不覆盖跨 session 宿主漂移**——必须 Stage 入口主动重探测
- 改动：
  - **P0-71-1. standards/external-model.md §四 E2 PMO 运行时探测段加「Stage 入口宿主重探测硬规则」**：3 步流程（重探测 / 对比一致性 / 漂移时重算 + state.concerns + 主对话声明切换）+ 4 类禁止形态 + 7 步正确处理流程（含用户实证案例）
  - **P0-71-2. review-stage.md §4 外部模型选择段加 cite**：「必须 Stage 入口调用 detect-external-model.py 重探测当前主对话宿主，禁止盲信 state.external_cross_review.host_main_model 旧值」+ 链接到 standards/external-model.md
  - **P0-71-3. 版本号 + CHANGELOG**（7.3.10+P0-70 → 7.3.10+P0-71）
- 实证素材（写进 spec 反例）：
  - 用户实战：Codex CLI 主对话沿用 Claude Code 时期 state 错误把 external 标为 codex
  - 自我纠正路径：识别同源 → 切 claude → 加降级（不可用如实记录，不伪造 codex）
- 4 类禁止形态：
  - ❌ Codex CLI 主对话沿用 state 旧 `model: codex`（同源 → 失去异质 review 价值）
  - ❌ 跨 session 切宿主未重探测，盲信 state 旧 host_main_model
  - ❌ 探测发现漂移但不写 state.concerns（违反闭环验证红线）
  - ❌ 重探测发现 Claude CLI 未登录，伪造为"用 codex 替代"（同源不算 external · 应走 E3 降级）
- 7 步正确处理流程：探测 → 对比 → 重算 → 写 concerns → 声明切换 → dispatch → 失败如实记录
- 与已有规则的关系：
  - 与 P0-65（Codex 沙箱认证）协作：P0-65 解决"CLI 已装但认证不通"的 dispatch 失败 / P0-71 解决"宿主已切换但 state 缓存陈旧"的探测层漂移
  - 与 E1 异质性约束（§三）协作：E1 是规则 / P0-71 是执行机制（每个 Stage 入口主动校验 E1）
  - 与 E3 失败降级（§六）协作：P0-71 重探测无可用外部 → 进 E3 降级（state.concerns WARN + architect+QA 兜底）
  - 同时也覆盖 Goal-Plan / Blueprint Stage（虽然这次实战只在 Review 暴露，但所有启用 external 的 Stage 入口都该按本规则）
- **加 1 删 1 元规则核算**：
  - **加**：standards/external-model.md ~30 行硬规则段 + review-stage.md ~3 行 cite
  - **删**：未删（实证补强 · 非冗余清理）
  - **不增加 PMO 负担**：每个 Stage 入口本来就要读 state.external_cross_review，加重探测只多一次脚本调用（约 100-300ms）
  - **"重新触发回来"防护**：未来 PMO 又在跨 session 切宿主时盲信 state 旧值 → cite §四 Stage 入口重探测硬规则
- 不动：
  - detect-external-model.py 自身（不查 API key 的设计原则不变）
  - E1 / E3 核心规则（§三 / §六 不变）
  - state.json schema（不需要新字段）
- 影响面：2 文件（standards/external-model.md / stages/review-stage.md）+ 元数据 3 个
- 后续验证：
  - 下次跨 session 切宿主执行 Stage 时，PMO 应自动按 P0-71 重探测 + 漂移声明
  - Goal-Plan / Blueprint Stage 入口实例化段是否需要同样加 cite（暂不强加 · 三 Stage 已通过 standards/external-model.md 单源继承）
  - 长期：可考虑把 detect-external-model.py 调用结果做轻量缓存（同 session 内不重复调用），但不阻塞 P0-71 落地

---

## v7.3.10 + P0-70

> v7.3.10+P0-70 长 URL / 长路径不进表格列硬规则（ship MR 链接被切碎实证）：用户截图反馈 Ship Stage 第一段输出 PMO 把 `📦 当前状态` 列表「美化」成 markdown 表格 → MR 创建链接（含 `?merge_request%5Bsource_branch%5D=...` 长查询参数）被表格列宽切成多行 + 全角竖线干扰 → 终端无法识别为可点击 hyperlink。本 patch 双向修复：(1) ship-stage.md 第一段模板加 MR URL 独立成行硬规则 + 正反例对比 / (2) STATUS-LINE.md 加通用「长 URL/路径不进表格列」硬规则覆盖所有 stage。

### P0-70：长 URL / 路径不进表格列（终端 hyperlink 识别）

- 触发：用户截图实证 Ship 第一段 MR 链接被 markdown 表格列宽切碎不可点击
- 设计哲学：**长 URL / 长路径必须独立成行**——表格列宽切碎 + 全角竖线干扰是终端 hyperlink 识别的主要杀手。spec 本来就是列表格式（- 开头单行项），但 PMO 没有显式禁止"美化为表格"，自由发挥时容易踩坑
- 改动：
  - **P0-70-1. ship-stage.md 第一段完成报告模板加硬规则**（在「输出第一段报告」段紧邻 quote）：MR/PR 创建链接必须独立成行 / 禁止挤入 markdown 表格列 / 禁止用 markdown 链接语法包裹当主呈现 / 禁止全角符号紧贴 URL
  - **P0-70-2. ship-stage.md 加正反例对比**：错误示例（用户截图原文 · 表格切碎）+ 正确示例（独立行 + 🔗 emoji 引导 + 前后 whitespace 边界）
  - **P0-70-3. ship-stage.md 第一段模板调整**：将 `MR/PR 创建链接` 从 `📦 当前状态` 列表中拎出 → 独立 `🔗 MR/PR 创建链接：` 段（与列表段隔一空行）
  - **P0-70-4. STATUS-LINE.md emoji 间隔规则段加通用硬规则**：长 URL / 长绝对路径不进 markdown 表格列 / 不嵌入 markdown 链接语法 + 正反例（覆盖所有 stage 输出，不只是 ship）
  - **P0-70-5. 版本号 + CHANGELOG**（7.3.10+P0-69 → 7.3.10+P0-70）
- 与 P0-67 路径边界规则的关系：
  - P0-67 规定路径**前后 whitespace 边界**（解决标点紧贴 / emoji 紧贴）
  - P0-70 规定长 URL / 路径**不进表格列**（解决列宽切碎 / 全角竖线干扰）
  - 两条互补 · P0-70 是 P0-67 的扩展（适用更长的 URL 场景）
- F059 实战素材（写进 spec 当反例）：
  - 用户截图原文：`| MR 创建链接 | https://git.okok.ai/matrix/vlite/-/merge_requests/new?merge_request%5Bsource_branch%5D=feature%2FF059-relax-package-check |`
  - 现象：URL 被列宽切成多行 + 全角竖线干扰 + 终端无法点击
  - 修复后预期：URL 独立成行裸输出 + 前后 whitespace 边界 + 终端识别可点击
- **加 1 删 1 元规则核算**：
  - **加**：~25 行（ship-stage.md 硬规则段 + 正反例 + 模板微调 / STATUS-LINE.md 通用规则）
  - **删**：未删（实证补强 · 非冗余清理）
  - **不增加 PMO 负担**：MR URL 本来就要输出 · 只是改"挤表格"为"独立行"，认知负担不变
  - **"重新触发回来"防护**：未来 PMO 又把长 URL 挤进表格 → cite ship-stage.md / STATUS-LINE.md 反例对比段
- 不动：
  - emoji 间隔规则（P0-62）/ 路径边界（P0-67）/ 暂停点资产绝对路径（P0-61）— 三条规则保留 + 互补
  - Ship Stage 流程逻辑（双段 / push / finalize · 不变）
  - state.json.ship.mr_create_url 存储字段（不变）
- 影响面：
  - 改动文件：2 主（stages/ship-stage.md +~25 行 / STATUS-LINE.md +~15 行）+ 元数据 3 个
- 后续验证：下次 Ship 第一段输出，应当看到 `🔗 MR/PR 创建链接：\n\n{url}\n` 三行结构（emoji 引导 + 空行 + 裸 URL）

---

## v7.3.10 + P0-69

> v7.3.10+P0-69 架构师 Review §6 扩展为「日志完整性审查」（INFO + ERROR 双层 · F059 双层失守第二层修复）：F059 实证暴露**双层失守**——P0-68 修复了第一层（QA 没查 PRD AC ↔ 代码 grep）但第二层仍是缺口（架构师 §6 只查"异常分支 ERROR 日志"，不查"关键路径 INFO 日志"）。本 patch 把架构师 §6 从单段「三方/外部服务调用异常 ERROR 日志审查」扩展为三段式「日志完整性审查」：6.1 异常 ERROR 日志（保留 BLOCKER）+ 6.2 关键路径 INFO 日志（新增 · concern · 兜底机制不依赖 PRD 声明）+ 6.3 安全脱敏。与 P0-68 互补：PRD 有日志 AC → QA Step 4.5 走 BLOCKER；PRD 没声明 → 架构师 §6.2 主动兜底走 concern。

### P0-69：架构师 §6 日志完整性审查（INFO + ERROR + 脱敏 三段式）

- 触发：F059 实证 7 个关键路径无 SLogger.i 全部漏检 + 用户判断"P0-68 只修第一层，第二层仍是缺口"+ 拍板 A
- 设计哲学：**日志覆盖是工程通用实践，不应该靠 PM 想到才查**。架构师层面应有兜底 checklist。与 P0-68 协作：PRD 显式声明 → QA 精确对账（BLOCKER）；PRD 没声明 → 架构师主动兜底（concern）
- 改动：
  - **P0-69-1. review-stage.md L349-356 重写**：单段「异常 ERROR 日志审查」→ 三段式「日志完整性审查」
    - **6.1 异常分支 ERROR 日志**（🔴 BLOCKER · 保留原硬规则不变）
    - **6.2 关键路径 INFO 日志**（🟡 concern 兜底 · v7.3.10+P0-69 新增）：
      - 6 类核心数据流主动识别（API 入口 / 业务逻辑 / 持久化 / 跨进程调用 / 异步触发 / 外部依赖结果）
      - 5 类节点验证（入口 / 状态变迁 / 长操作 / 决策分支 / 外部依赖结果）
      - grep 关键字模板（SLogger.i / Log.i / logger.info / info! / tracing::info）
      - 缺失分级（默认 concern · 已知历史排障难点路径升 BLOCKER）
    - **6.3 安全脱敏**（与「敏感数据」段联动 · 显式列出脱敏类别）
  - **P0-69-2. 与 P0-68 协作机制说明**（review-stage.md §6 末尾）：PRD 有日志 AC → QA Step 4.5 BLOCKER / PRD 没声明 → 架构师 §6.2 concern 兜底
  - **P0-69-3. 版本号 + CHANGELOG**（7.3.10+P0-68 → 7.3.10+P0-69）
- 与 P0-68 的双层互补结构：
  - **第 1 层 PRD AC ↔ 代码 grep**（QA Step 4.5 · 显式契约层）：依赖 PM 在 PRD 写日志 AC + grep_keyword
  - **第 2 层 关键路径 INFO 日志**（架构师 §6.2 · 通用工程兜底层）：架构师主动识别核心数据流，不依赖 PRD 显式声明
  - 缺一不可：第 1 层防 PM 已声明的承诺被实现漏掉（BLOCKER）；第 2 层防 PM 没想到的通用日志要求（concern）
- 三层差异化处理（避免一刀切打回 ship）：
  - 异常 ERROR 日志缺失 = 🔴 BLOCKER（正确性问题 · 不知道哪挂了）
  - 关键路径 INFO 日志缺失 = 🟡 concern（可观测性问题 · 不知道有没有跑到）
  - 安全脱敏违反 = 🔴 BLOCKER（合规风险）
- F059 实证素材（写进 spec 当反例）：
  - 7 个关键路径无 SLogger.i：notifySoReady / notifyFocus / drainQueue / execute / fetchConfig / cache hit-miss / download / MD5 校验 / rename
  - 用户实测：「实测预下载无效果 + 想看日志」→ 没日志根本测不出"功能是否在跑"
  - 双层失守：QA 漏（P0-68 修了）+ 架构师 §6 漏（本 P0-69 修）
- **加 1 删 1 元规则核算**：
  - **加**：~30 行（6.2 关键路径 INFO 段 + 6.3 安全脱敏段 · 6.1 保留不变）
  - **删**：未删（实证补强 · 非冗余清理）
  - **不增加 PMO 负担**：架构师本来就要识别核心数据流（架构 review 必做），加 INFO 日志验证维度只多 5-10 min
  - **"重新触发回来"防护**：未来如发现 ship 后才暴露的关键路径 INFO 缺失 → cite §6.2 应该 concern；如发现是已知历史排障难点路径 → cite §6.2 升 BLOCKER 条款
- 不动：
  - 架构师 §6.1 异常 ERROR 日志 BLOCKER 规则（保留 · 不降级）
  - QA Step 4.5 PRD AC 直接对账（P0-68 加的 · 不动）
  - 三视角并行结构（架构师 + QA + external · 不动）
  - 修复循环规则（NEEDS_FIX 重跑机制 · 不动）
- 影响面：
  - 改动文件：1 主（stages/review-stage.md L349 段重写）+ 元数据 3 个
  - 行数变化：review-stage.md +~25 行
- 后续：
  - 下次架构师 review 实证跑一遍 §6.2 流程，看是否能 catch 关键路径 INFO 缺失
  - 如发现 6 类核心数据流分类不够（如缺"定时任务" / "消息消费" 等），加进 §6.2 数据流清单
  - 长期：可与 standards/backend.md「三方/外部服务调用异常 ERROR 日志规则」整合 · 抽出 standards/logging.md 单源（暂不做 · 等再发现 1-2 次类似 case 再整合）

---

## v7.3.10 + P0-68

> v7.3.10+P0-68 PRD AC 直接对账（review-stage.md QA Step 4.5 + 非功能性 AC category 显式化 + grep_keyword 字段 · 实战 F059 触发）：用户实战 F059-StartupPreloader Ship 后发现 5 个 PRD 埋点全缺 + 7 个关键路径无日志，根因 = 「TC 没覆盖非功能性 AC，QA Review 在 TC 中转模式下漏检」。本 patch 在 review-stage.md QA 任务规范加 Step 4.5「PRD AC 逐条直接对账」（不通过 TC 中转）+ templates/prd.md acceptance_criteria 加 category（functional / telemetry / logging / config / performance / security / monitoring）+ grep_keyword 字段（供 Step 4.5 直接 grep 用）。与 verify-ac.py 互补：verify-ac.py 验 ID 绑定（Dev 出口），Step 4.5 验语义实现（Review 阶段）。

### P0-68：PRD AC 直接对账（QA Step 4.5 + AC category + grep_keyword）

- 触发：F059 实证 Ship 后发现 PRD 5 埋点全缺 + 7 关键路径日志全缺，全链路无人 grep PRD AC ↔ 代码
- 设计哲学：**TC 覆盖 ≠ AC 覆盖**。AC 中的非功能性承诺（埋点 / 日志 / 监控 / 配置 / 性能 / 安全）TC 通常无法覆盖，必须 Review 阶段直接 grep 对账，不通过 TC 中转
- 改动：
  - **P0-68-1. review-stage.md QA 核心原则升级**：从「逐条验证 TC 覆盖情况」→「PRD AC ↔ 代码（Step 4.5）+ TC ↔ 代码（Step 3）双重对账」+ 加「TC 覆盖 ≠ AC 覆盖」硬规则段（含 F059 实证教训）
  - **P0-68-2. review-stage.md 加 Step 4.5「PRD AC 逐条直接对账」**：5 步执行流程（读 PRD → grep 7 类 AC → BLOCKER 判定 → 报告对账表 → 标注命中位置）+ 与 verify-ac.py 边界划分 + 5 列报告模板
  - **P0-68-3. templates/prd.md acceptance_criteria 加 `category` 字段**：枚举 functional / telemetry / logging / config / performance / security / monitoring（v7.3.10+P0-68 新增 · 触发 Step 4.5 按类别走 grep 对账）
  - **P0-68-4. templates/prd.md 加 `grep_keyword` 字段**（可选 · 推荐非功能性 AC 显式提供）：PM 起草 PRD 时为非功能性 AC 写 grep 关键字，Step 4.5 直接复用，避免 QA 现场猜测
  - **P0-68-5. 加 PRD 反例**：示例加 AC-7 telemetry 类 / AC-8 logging 类，演示 category + grep_keyword 用法
  - **P0-68-6. 版本号 + CHANGELOG**（7.3.10+P0-67 → 7.3.10+P0-68）
- 与 verify-ac.py 互补关系：
  - **verify-ac.py**（Dev Stage 出口 · 机器层）：验 `AC.id ↔ TC.covers_ac` 绑定关系（ID 层）
  - **Step 4.5**（Review Stage QA · 语义层）：验 AC 描述 ↔ 代码 grep 命中（语义层 + 非功能性 AC 强制覆盖）
  - 缺一不可：verify-ac.py 防 ID 漂移；Step 4.5 防"TC 没覆盖 AC = AC 实现是否存在没人查"
- F059 实证素材（写进 spec 当反例）：
  - 5 埋点全缺：`SReporter.*preload_browser_*` grep → 0 处 → ❌ BLOCKER
  - 7 关键路径无日志：`SLogger.i.*notifySoReady\|notifyFocus\|drainQueue\|execute\|fetchConfig` grep → 0 处 → ❌ BLOCKER
- **加 1 删 1 元规则核算**：
  - **加**：review-stage.md ~25 行 Step 4.5 + 报告模板 / templates/prd.md ~10 行 schema 扩展 + 反例
  - **删**：未删（实证补强 · 非冗余清理）
  - **不增加 PMO 负担**：QA 起草 PRD 时多填 category + grep_keyword（每个非功能性 AC 多 5-10 秒）/ Review 阶段 QA 多 5-10 min grep 对账
  - **"重新触发回来"防护**：未来若发现 ship 后才暴露的 AC 实现缺失 → 直接 cite Step 4.5 应该 BLOCKER
- 不动：
  - PRD frontmatter 其他字段（priority / test_refs / ui_refs 等）
  - QA Step 1-4 / Step 5+ 其他流程（4.5 是新插入的 step）
  - verify-ac.py 自身（不需要改 · 互补关系自然）
  - 架构师 Review 维度（架构师管 TECH ↔ 代码 / QA 管 PRD AC ↔ 代码 · 职责边界清晰）
- 影响面：
  - 改动文件：3 个（stages/review-stage.md / templates/prd.md / 元数据）
  - 行数变化：review-stage.md +30 行 / templates/prd.md +15 行
- 后续验证：下个 Feature Review Stage QA 应自动按 Step 4.5 跑 PRD AC 对账。如发现新的非功能性 AC 类别（如 "I18n" / "无障碍"），加进 category 枚举 + Step 4.5 类别表
- 后续可加：
  - QA Subagent prompt 模板加「Step 4.5 PRD AC 直接对账」段（templates/dispatch.md 同步）
  - verify-ac.py 可选扩展：读 PRD frontmatter `grep_keyword` 自动跑 grep（机器化 Step 4.5 部分）

---

## v7.3.10 + P0-67

> v7.3.10+P0-67 路径后边界硬规则（路径前后必须有 whitespace 终端才能识别 hyperlink）：用户反馈"涉及目录路径的内容，前后需要加一个空格，方便终端识别"。P0-62 已规定 emoji-路径之间必须半角空格（解决路径**前**边界），但路径**后**没规则——实战中 PMO 常写「...见 /Users/.../PRD.md，请确认」用全角符号紧贴路径，终端把"PRD.md，"识别为整体导致链接断裂。本 patch 在 STATUS-LINE.md L91 emoji 间隔硬规则旁加补丁规则，覆盖路径前后双边界。

### P0-67：路径后边界硬规则（whitespace 终端识别）

- 触发：用户实战反馈路径后被全角符号紧贴导致终端 hyperlink 失效
- 设计哲学：**路径需要 whitespace 边界让终端正确识别**——P0-62 解决了前边界（emoji + 半角空格），P0-67 补全后边界（半角空格 / 换行 / 行尾 / 不允许全角符号紧贴）
- 改动：
  - **P0-67-1. STATUS-LINE.md L91 emoji 间隔规则旁加「路径边界硬规则」补丁**：明确「路径前后双边界 + 禁止全角符号紧贴 + 正反例对比」（错例：`PRD.md，请确认` 全角逗号紧贴 / 正例：`PRD.md ，请确认` 半角空格 + 全角逗号）
  - **P0-67-2. standards/output-tiers.md §三-A 同步合并**：原 P0-62 单条规则升级为「P0-62 emoji 间隔 + P0-67 路径后边界」组合规则，统一引用 STATUS-LINE.md
  - **P0-67-3. 版本号 + CHANGELOG**（7.3.10+P0-66 → 7.3.10+P0-67）
- **加 1 删 1 元规则核算**：
  - **加**：~5 行硬规则（双边界 + 正反例）
  - **删**：未删（用户体验补强）
  - **不增加 PMO 负担**：PMO 写路径本来就要写边界字符，只是把"自觉留空格"升格为"硬规则"，避免漏
  - **"重新触发回来"防护**：未来 PMO 写「PRD.md，待用户确认」类语句 → 直接 cite STATUS-LINE.md 路径边界硬规则
- 实战覆盖场景：
  - 状态行第二行 `📁 /Users/.../PRD.md`（行尾自然边界 ✅）
  - 暂停点资产指针 `📁 待确认 PRD：/Users/.../PRD.md ，请确认`（半角空格 + 全角逗号 ✅）
  - 普通描述 `更新见 /Users/.../KNOWLEDGE.md ，已落盘`（半角空格 + 全角逗号 ✅）
- 不动：
  - emoji 间隔规则本身（P0-62 不变 / 新规则是补充而非替代）
  - 状态行 3 行格式（已稳定）
- 影响面：2 文件（STATUS-LINE.md + standards/output-tiers.md）+ 元数据
- 后续：如发现 PMO 仍输出全角符号紧贴路径，加进 STATUS-LINE.md 反例对比段

---

## v7.3.10 + P0-66

> v7.3.10+P0-66 状态行 Final Response Preflight + 禁止替代格式（实战 INFRA-F017 Ship finalize 漏状态行案例）：用户实战 AI 输出了「📍 Teamwork：INFRA-F017 | 阶段：✅ completed | shipped=merged」摘要替代标准 `🔄 Teamwork 模式 | ...` 状态行。AI 自检根因 = 「相似格式漂移 + 完成时误以为流程退出 + 工程信息密集时压缩成摘要」。本 patch 加 4 条硬规则到 STATUS-LINE.md：(1) Final Response Preflight 4 项 self-check / (2) 禁止相似格式（📍 Teamwork: / Teamwork: / 工程摘要伪装等） / (3) 完成时例外明确化（completed 仍要状态行） / (4) 统一 completed 措辞为「✅ 已完成」。

### P0-66：状态行 Preflight + 禁止替代格式 + completed 例外明确化

- 触发：实战 INFRA-F017 Ship finalize 漏标准状态行 + AI 自检报告 4 条改进建议
- 设计哲学：**Tier 1 输出红线靠声明不够，要 self-check 机制**。AI 在长对话 / 重要节点（Ship finalize）容易格式漂移，"每次回复必须包含状态标识"声明被压力测试时会失效。preflight 是"发送前必检"机制，比"应该包含"更强
- 改动：
  - **P0-66-1. STATUS-LINE.md 加「Final Response Preflight」段**（在状态行规则段末尾）：4 项 self-check（状态行存在 / 在末尾 / 阶段值合法 / 下一步合法）
  - **P0-66-2. 加「禁止替代格式」反例对比**：3 个 ❌（📍 Teamwork: 摘要 / Teamwork: 口语 / 工程摘要伪装）+ 1 个 ✅，覆盖实战漂移模式
  - **P0-66-3. 加「功能完成例外明确化」**：completed 状态最后一条回复**仍然必须**带状态行（功能完成 ≠ 流程退出）；退出真正发生在这条之后
  - **P0-66-4. 统一 completed 措辞**：所有「✅ 已交付」改为「✅ 已完成」（修 L108 / L311 措辞冲突）
  - **P0-66-5. 版本号 + CHANGELOG**（7.3.10+P0-65 → 7.3.10+P0-66）
- **加 1 删 1 元规则核算**：
  - **加**：~30 行（preflight checklist + 反例对比 + 例外说明）
  - **删**：「✅ 已交付」措辞被替换为「✅ 已完成」（一致性收紧 / 净 ±0）
  - **不增加 PMO 负担**：preflight 是 PMO 在生成回复时的 self-check（不是新职责段 / 不是新工具调用），认知负担只是"按列表自检 4 项"
  - **"重新触发回来"防护**：未来 AI 再用 📍 Teamwork: 摘要 → cite STATUS-LINE.md 反例对比段；完成时漏状态行 → cite「功能完成例外」段
- 实战案例：INFRA-F017 Ship finalize 后 AI 输出 `📍 Teamwork：INFRA-F017 | 阶段：✅ completed | shipped=merged`（自定义字段 / 不标准开头 / 不在末尾）→ 用户指出 → AI 自检 4 条根因建议全部采纳
- 不动：第一行 / 第二行 / 第三行格式定义（P0-62 + 之前完善）/ 阶段与下一步对照表 / emoji 间隔硬规则
- 影响面：1 主文件（STATUS-LINE.md +30 行 + 2 处措辞替换）+ 元数据
- 后续验证：下次 Ship finalize / 任何 completed 回复，AI 应自动按 4 项 preflight 输出标准 3 行状态行。如发现新漂移模式，加进反例对比段

---

## v7.3.10 + P0-65

> v7.3.10+P0-65 Codex 沙箱下 Claude CLI 认证实战指南：用户实证 Codex 主对话宿主下 OAuth 登录态被沙箱屏蔽（沙箱外 `claude auth status` 已登录 / 沙箱内 Not logged in），找到 `CLAUDE_CODE_OAUTH_TOKEN` env var 作为最优解（复用 Pro/Max 订阅 + 跨沙箱稳定 + 不占 API 计费）。本 patch 把这个实战经验加进 claude-agents 文档，并按推荐度排列三种认证方式（A/B/C）。

### P0-65：claude-agents 加 Codex 沙箱认证指南

- 触发：用户实战诊断 Codex CLI 主对话宿主下 Claude CLI 认证踩坑（OAuth keychain 不穿透沙箱）+ 验证 `claude setup-token` + `CLAUDE_CODE_OAUTH_TOKEN` 路径可行
- 设计哲学：把实战教训写进文档（不是猜测），帮后来者省一晚上
- 改动：
  - **P0-65-1. claude-agents/README.md 加「认证方式」段**：3 种方式按推荐度排（A OAuth / B `CLAUDE_CODE_OAUTH_TOKEN` / C `ANTHROPIC_API_KEY`）+ 适用场景对比表 + Codex 沙箱限制实证 + 方式 B 配置步骤 + 官方文档链接（cli-reference / iam / env-vars）
  - **P0-65-2. claude-agents/invoke.md 顶部加 Codex 沙箱特殊处理提示** + 链接到 README.md
  - **P0-65-3. README.md 前置条件表 #2「认证」措辞改宽容** → 三种方式之一（之前只列 OAuth + ANTHROPIC_API_KEY 两种）
  - **P0-65-4. 版本号 + CHANGELOG**（7.3.10+P0-64 → 7.3.10+P0-65）
- **加 1 删 1 元规则核算**：
  - **加**：~30 行实证文档（认证方式表 + 配置步骤 + 官方文档链接）
  - **删**：未删（实战教训沉淀，不是冗余清理）
  - **新增价值**：A/B/C 三方式明确定位 + Codex 沙箱踩坑实证 + 官方文档链接（避免后来者从零摸索）
- 不动：
  - detect-external-model.py（不查 OAuth/API key 的设计原则不变）
  - state.json schema（external_cross_review 字段不变）
  - E3 失败降级流程（dispatch 失败时 state.concerns WARN 不变）
- 影响面：2 文件（claude-agents/README.md +30 行 / claude-agents/invoke.md +1 行）+ 元数据
- 后续：如发现新的认证踩坑（如 Linux 上 `secret-tool` 沙箱也类似问题），加进同一段

---

## v7.3.10 + P0-64

> v7.3.10+P0-64 删 localconfig.external_model 强制覆写规则（虚构边缘场景）：用户反馈"localconfig 强制设 external_model=codex 的逻辑去掉吧"。盘点确认：框架本来就**没给用户开 localconfig.external_model 字段**——detect-external-model.py 不读 / feature-state.json schema 不读 / config.md 没定义。standards/external-model.md L55 的"用户硬塞同源 = WARN 降级"是纯防御性虚构条款（防一个不存在的口子）。本 patch 删掉这条，简化为"由探测 + E1 自动决定，用户不可覆写"的清晰边界。

### P0-64：删 localconfig.external_model 虚构覆写条款

- 触发：用户"`.teamwork_localconfig.md` 强制设 external_model=codex 的逻辑去掉吧"
- 设计哲学：**砍掉防御性虚构条款** —— 框架不开放的口子不应该写"防御"规则；规则应该描述实际行为，不是描述虚构反例
- 改动：
  - **P0-64-1**：standards/external-model.md L55 删原"WARN 降级"防御条款 → 替换为"由探测 + E1 自动决定，用户不可覆写"的清晰边界声明
  - **P0-64-2**：版本号 + CHANGELOG（7.3.10+P0-63 → 7.3.10+P0-64）
- 盘点确认（不动的部分）：
  - **detect-external-model.py**：本来就不读 localconfig，仅探测 .claude/.codex/.agents/ 目录标记 + PATH CLI 可用性
  - **feature-state.json schema**：external_cross_review 对象 frontmatter 字段不含 user_override
  - **templates/config.md**：没有定义 external_model 作为 localconfig 字段
  - **roles/pmo.md**：引用 external-model.md 不复述本规则
- **加 1 删 1 元规则核算**：
  - **加**：1 行简化声明（"用户不可覆写"）
  - **删**：1 行防御性虚构条款（"用户硬塞同源 = WARN 降级"）
  - **净变化**：±0 行 / 但**移除虚构反例 = 规则更清晰** + 防止后续 patch 在虚构条款上加规则
- 不动：E1 同源约束本身（这是真实有效的规则）/ Claude Code → codex / Codex CLI → claude / 通用宿主 → 都可用 三条映射保留
- 影响面：1 文件（standards/external-model.md L55）+ 元数据
- 后续：如果将来真要开放用户覆写（业务诉求场景），再在 templates/config.md 显式加字段 + detect-external-model.py 加读取逻辑 + state.json schema 加字段 —— **届时再加规则，不再做防御性预留**

---

## v7.3.10 + P0-63

> v7.3.10+P0-63 TDD 单源化（standards/tdd.md 抽取）：参考 obra/superpowers test-driven-development skill 的"Iron Law + RED-GREEN-REFACTOR 强制" 思路。当前 Teamwork TDD 规则散在 5 处（standards/common.md §一 / §QA / dev-stage.md §2 / §2.1 / review-stage.md QA Step 4 / roles/rd.md），措辞重叠也有差异，新角色加 TDD 描述时不知该 cite 哪。本 patch 抽取 standards/tdd.md 作为唯一权威源（~110 行 / Iron Law + 5 步流程 + 自检 + 反模式 + 例外 + ≥3 次失败升级），5 处散落点改为引用化。

### P0-63：TDD 单源化（standards/tdd.md 抽取）

- 触发：之前对比 obra/superpowers 时识别出的"散落收敛"价值；用户拣选执行
- 设计哲学：**TDD 规则是横切关注点**（多 stage / 多 role 共用）→ 应单源 / 各处 cite。其他 standards/*.md 已是这种模式（output-tiers / external-model / prompt-cache / stage-instantiation）
- 新建 standards/tdd.md（~110 行）：
  - **§一 Iron Law**：NO PRODUCTION CODE WITHOUT A FAILING TEST FIRST（借 superpowers 措辞）
  - **§二 RED-GREEN-REFACTOR 5 步流程**：迁自 dev-stage.md §2 + 加 VERIFY RED / VERIFY GREEN 两步显式化
  - **§三 自检清单**：8 条（迁自 standards/common.md §一）
  - **§四 反模式**：6 条（合并 roles/rd.md 反模式段 + 新增）
  - **§五 例外**：5 类（throwaway / 生成代码 / 配置 / 简单方案用户授权 / Micro 流程）+ state.json.concerns 落记录硬规则
  - **§六 ≥3 次失败升级**（新增）：同一 GREEN step 失败 3 次 → 重读 TECH / 升级架构师 review
  - **§七 引用约定**：列出各位置如何 cite
- 散落点引用化（5 处）：
  - **standards/common.md §一 TDD 检查清单** → 引用 tdd.md（保留 8 条快查 · 详细规则去权威源）
  - **standards/common.md §QA 代码审查 TDD 规范检查** → 引用 tdd.md §三 + §四（保留 5 条快查）
  - **stages/dev-stage.md §2 TDD 开发流程** → 整段引用 tdd.md §二（保留 Step 5b UI 还原 Dev Stage 特有补充）
  - **stages/dev-stage.md §2.1 开发约束** → 引用 tdd.md §一 + §四 + §五（保留 4 条 Dev Stage 特有约束如禁 TODO/FIXME）
  - **stages/review-stage.md QA Step 4 TDD 规范检查** → 引用 tdd.md §三 + §四（之前是引用 standards/common.md，改为直引权威源）
  - **roles/rd.md「测试先行」** → 引用 tdd.md
- 索引更新：
  - **STANDARDS.md** 加 tdd.md 行（标"🔴 TDD 唯一权威源"）+ Subagent 加载指引加 tdd.md 必读
  - **SKILL.md** 文件索引加 tdd.md 行
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：standards/tdd.md ~110 行（新建权威源）
  - **删**：dev-stage.md TDD 开发流程详细 ~25 行 + 开发约束 ~7 行 + standards/common.md TDD 检查清单详细 ~13 行 + TDD 规范检查 ~9 行（共 ~54 行被引用替换）
  - **净加**：~56 行（建立单源的成本 · 但收益是后续所有 TDD 规则修改只动一个文件）
  - **新增价值**（之前没有的）：§六「≥3 次失败升级」（症状性修复反模式防护，对应 systematic-debugging Iron Law 的简化版）+ §五「例外」明确化 + 5 处引用机制建立
- 不动：
  - 各 stage spec 中 "TDD 红绿循环" 词汇本身（描述性，不破坏）
  - PRD frontmatter / TC frontmatter（数据契约）
  - verify-ac.py 机器校验
- 影响面：
  - 改动文件：7 个（新增 standards/tdd.md / standards/common.md ×2 段 / dev-stage.md / review-stage.md / roles/rd.md / STANDARDS.md / SKILL.md / 元数据 init-stage.md / docs/CHANGELOG.md）
- 后续验证：
  - 下次 Dev Stage 实战，确认 RD 起草 TDD 时 cite 的是 standards/tdd.md（而不是散落点）
  - 如发现新的 TDD 反模式，加进 tdd.md §四（单源补充，自动 propagate）

---

## v7.3.10 + P0-62

> v7.3.10+P0-62 emoji 间隔硬规则化（状态行可点击性修复）：用户实战截图反馈状态行第二行 `📁/Users/...` 没有空格，终端把 emoji 和路径视为一体，不可点击。框架现有示例本来都是带空格的（`📁 /Users/...`），但缺少显式硬规则约束，PMO 起草时偶尔会漏空格。本 patch 在 STATUS-LINE.md「状态行规则」段加 emoji 间隔硬规则 + 在 output-tiers.md §三-A 加同步条款。

### P0-62：emoji 与内容之间强制空格（用户体验修复）

- 触发：用户截图实证 PMO 输出 `📁/Users/...` 不可点击
- 设计哲学：**显式硬规则覆盖隐性约定**——示例都对，但没有规则就靠"自觉"，PMO 起草时会漏。加显式规则 + 正反例对比即可
- 改动：
  - **P0-62-1. STATUS-LINE.md 加 emoji 间隔硬规则**：状态行规则段最末加一条「所有图标（📁 / 🌿 / 📍 / ⚡ / 🌐 / 🔄 / 🔗 / ⏸️ 等）与其后紧随的文字内容之间必须保留一个半角空格」+ 正反例对比
  - **P0-62-2. STATUS-LINE.md L62 增强措辞**：从「必须输出 📁 绝对路径」→「必须输出 \`📁 {绝对路径}\`（emoji 与路径之间必须有一个空格）」
  - **P0-62-3. output-tiers.md §三-A 同步加规则**：暂停点资产指针也遵守同规则（暂停点和状态行的格式约束统一）
  - **P0-62-4. 版本号 + CHANGELOG**：7.3.10+P0-61 → 7.3.10+P0-62
- **加 1 删 1 元规则核算**：
  - **加**：3 处硬规则 / 正反例 ≈ 5 行
  - **删**：未删（这是用户体验补强）
  - **不增加 PMO 负担**：只是把"自觉"升格为"硬规则"，PMO 起草时本来就该带空格，只是有时漏
- 影响面：
  - 改动文件：4 个（STATUS-LINE.md / standards/output-tiers.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：STATUS-LINE.md +2 行 / output-tiers.md +1 行
- 后续验证：
  - 下次状态行 / 暂停点输出查看是否有 `📁 /Users/...` 带空格 + 路径在终端里可点击
  - 如发现 PMO 仍漏空格，加进 STATUS-LINE.md 反例对比段

---

## v7.3.10 + P0-61

> v7.3.10+P0-61 暂停点资产路径硬规则化（完整绝对路径）：用户反馈"涉及用户确认时，输出一下待确认文档的目录或文件路径（完整路径，非相对路径）方便用户查看"。当前框架在暂停点常输出相对路径（如 `apps/partner/docs/features/PTR-F016/PRD.md`），终端 / IDE 大多不识别相对路径为可点击 hyperlink。本 patch 在 standards/output-tiers.md（输出规范单源）加「三-A 待确认文档绝对路径硬规则」段，强制 PMO 在所有用户需要确认/查看的暂停点输出完整绝对路径。

### P0-61：暂停点资产绝对路径硬规则（用户体验提升 · 单源加一段）

- 触发：用户实战 PTR-F016 triage case 反馈"完整路径方便点击查看"
- 设计哲学：**单源化 + 体验性硬规则**——只动 standards/output-tiers.md（一个文件 + 一段段），不改各 stage spec / 不加 PMO 主动职责段（PMO 起草暂停点时自然遵循新规则）
- 改动：
  - **P0-61-1. Tier 1 描述加一行**：`待确认文档/目录的完整绝对路径（v7.3.10+P0-61 — 见下方硬规则 §三-A）`
  - **P0-61-2. 加「三-A 待确认文档绝对路径硬规则」段**：触发条件 + 4 条硬规则 + 输出格式模板 + 正反例对比 + 例外条款
  - **P0-61-3. 版本号 + CHANGELOG**：7.3.10+P0-60 → 7.3.10+P0-61
- 硬规则核心 4 条：
  - 必须以 `/` 开头的完整绝对路径
  - 禁止仅输出相对路径
  - 路径 = `pwd` + `state.artifact_root` + 资产文件名
  - 多文件用列表呈现 / 是目录就输出目录路径
- 例外：
  - 资产不是文件（纯主对话渲染骨架 / 口头方向决策）→ 可不输出
  - 状态行 `📁 ...` 保留相对路径（非暂停点决策行）
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：~30 行硬规则段（standards/output-tiers.md）
  - **删**：未删（这是用户体验补强 · 不是冗余清理）
  - **不增加 PMO 负担**：PMO 在暂停点本来就要输出资产指针，只是改形态（相对路径 → 绝对路径），认知负担相同
  - **"重新触发回来"防护**：硬规则在 Tier 1 描述里 + 三-A 单立段 + 正反例对比 — 未来如有 PMO 起草输出回到相对路径，违反 Tier 1 + 三-A 双重硬规则
- 不动：
  - 各 stage spec（output-tiers.md 是单源 / 各 stage 通过引用机制自动继承）
  - PMO 角色文件（不加 PMO 主动检测职责 · 最简化原则）
  - state.json schema（不加 project_root 字段 · cwd 已经在主对话上下文）
  - status 行格式（保留相对路径 · 跟暂停点决策行的资产指针解耦）
- 影响面：
  - 改动文件：4 个（standards/output-tiers.md +30 行 / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：standards/output-tiers.md 110 → ~140 行
- 后续验证：
  - 下次 triage / Goal-Plan / blueprint / review / PM 验收 等暂停点跑下来验证 PMO 是否正确拼绝对路径
  - 如果发现 PMO 在某些场景仍出相对路径，按本 patch 的"必砍"机制加进 standards/output-tiers.md 反例对比段

---

## v7.3.10 + P0-60

> v7.3.10+P0-60 triage Step 8 输出表格化 patch（卡片式骨架 + 必含/必砍清单）：用户基于实战 PTR-F016 triage 输出 ~85 行案例反馈"输出还是太多，能否精简，表格化，方便确认。最好输出内容统一一个模版"。诊断：Tier 1 实际只占 ~20 行，剩 ~65 行全是 Tier 2/3 越界（Why now 履职报告 / Real unknowns 详细 / 关键非默认决策重复 / KNOWLEDGE/ADR/External 详细 / 环境异常单独成段 / 各 Stage 4 行 vertical 展开）。本 patch 在 triage-stage.md Step 8 加「卡片式输出模板硬规则」+「必含 5 段」+「必砍 7 段」+ 新表格化示例（Stage 表 4 列 / 暂停点表 5 行）替换原 vertical 8-Stage 散文示例。

### P0-60：triage Step 8 输出表格化（卡片式骨架）

- 触发：用户案例分析 + "最简化思路 / 降低 PMO 负担 / 模板化"原则延续
- 设计哲学：**Tier 1 必看内容卡片化**（意图段 + Stage 表 + 关键假设 + 双对齐表）/ Tier 2/3 内容明确"必砍"（履职报告反模式）/ 决策点单源化（双对齐 + 环境处理融合到一张 5 行表）
- 处理：
  - **P0-60-1. Step 8 加「卡片式输出模板硬规则」段**：明确 ≤ 30 行总长 + 必含 5 段 / 必砍 7 段
  - **P0-60-2. 替换 vertical 8-Stage 示例为表格示例**：原 ~62 行 vertical（每 Stage 4 行：goal / key_outputs / pause_points / execution_hints）→ 新 ~25 行表格（Stage 表 4 列 / 暂停点表 5 行 / 详情指针 1 行）
  - **P0-60-3. 加「execution_hints 在表内的承载方式」硬规则**：表内「非默认」列只写一行 + 完整 hint 落 state.json
  - **P0-60-4. 加「意图段缩编硬规则」**：Why now ≤ 2 行 / Assumptions ≤ 3 条 / Real unknowns ≤ 3 条 / 整体 ≤ 8 行
  - **P0-60-5. 版本号 + CHANGELOG**：7.3.10+P0-59 → 7.3.10+P0-60
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：必含 5 段 + 必砍 7 段 + execution_hints 承载规则 + 意图段缩编规则 ≈ 35 行硬规则文字
  - **删**：原 vertical 8-Stage 散文示例 ~62 行
  - **净减**：~25 行（即模板自身瘦身）+ 实战每次 triage 输出 ~85 行 → ~22 行（**单次 -74%**）
  - **"重新触发回来"防护**：硬规则段明确禁止散文化展开 + 必砍 7 段对应 7 个反模式（Why now / 关键非默认决策 / KNOWLEDGE 详细 / ADR 详细 / External 详细 / 环境异常 / Stage 多行展开）。未来想加段 → 必须在硬规则段动，不能在示例里偷偷加
- 不动：
  - Step 8 现有硬约束（双对齐唯一合法形态 / 4 字段必填 / 骨架尾部一行 / 禁产品决策菜单 / 禁拆分对齐）
  - state.json 写入清单（Step 9 硬清单段不变）
  - 流程类型 schema（Bug / 问题排查 / Micro 各自意图段格式不变 · 仅加缩编规则）
- 影响面：
  - 改动文件：1 主（stages/triage-stage.md L477-540 替换 + 加硬规则段）+ 元数据（SKILL.md / init-stage.md / CHANGELOG.md）
  - 行数变化：triage-stage.md ±0 净（删 vertical 加 table + 硬规则）· 实战 triage 输出 -74%
- 后续验证：
  - 下次实战 triage 跑一遍验证模板是否落地（用户的 PTR-F016 case 已跑过 vertical 版 ~85 行 · 套新模板预期 ~22 行）
  - 如发现新的反模式（如某 Stage 起草时又长出新段）→ 加进必砍清单

---

## v7.3.10 + P0-59

> v7.3.10+P0-59 teamwork_space.md 变更类表格全砍 patch（最激进单源化）：用户进一步追问"跨项目需求追踪有必要么"+ 拍板"C"（最激进）。诊断：`templates/change-request.md` frontmatter 已经把所有变更属性（status / sub_features / affected_subprojects / 变更日志）都管了，teamwork_space.md 里的「跨项目变更索引」/「跨项目当前阻塞」/「变更记录」三张表全是双源副本，且实战中已发生多次"索引落后于真相"的偏离（CHANGELOG 里 PMO 主动纠偏 BG-009/BG-010/BG-013）。本 patch 删三张表，替换为一段单源指针段，teamwork_space.md 彻底回归"项目结构静态描述"。

### P0-59：teamwork_space.md 变更类表格全砍（单源化彻底化）

- 触发：用户"跨项目需求追踪 有必要么" + 选 C（砍三张表）
- 设计哲学：**单源原则贯彻到底**——changes/{change_id}.md 是变更的唯一权威源（frontmatter + 变更日志段），teamwork_space.md 完全不维护变更类信息。回归"项目结构静态描述"定位
- 处理：
  - **P0-59-1. templates/teamwork-space.md 删三段**：跨项目变更索引段（L134-149，含 P0-58 加的硬规则）+ 跨项目当前阻塞段（L153-161）+ 变更记录段（L165-178）→ 替换为单一「跨项目变更与历史」指针段（~10 行 · 列出 4 个单源 + 核心硬约束保留）
  - **P0-59-2. 生命周期描述同步**：阶段 3 描述去掉"跨项目变更索引表开始使用 + 变更记录持续维护"，改为"变更/阻塞/事件历史一律落 changes/{id}.md 或 Feature state.json"
  - **P0-59-3. 联动文件清理**：FLOWS.md L523/L600 + RULES.md L759/L931/L1185 + roles/pm.md L268 + rules/naming.md L105 + templates/change-request.md L157-169 + PRODUCT-OVERVIEW-INTEGRATION.md L226 全部更新为"changes/{id}.md 单源"措辞
  - **P0-59-4. 版本号 + CHANGELOG**：7.3.10+P0-58 → 7.3.10+P0-59
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：~10 行单源指针段
  - **删**：3 张表 + 6 处硬规则段（P0-58 加的）+ 6 个文件中的"更新 teamwork_space.md 变更/索引表"指令 ≈ 70 行
  - **净减**：~60 行
  - **本 patch 是 P0-58 的进化**：P0-58 给变更类表格加硬规则（一句话 / 字数上限），P0-59 直接砍表（更彻底的简化）。P0-58 的硬规则段被 P0-59 一并删除（被砍的表自然不需要硬规则）
  - **"重新触发回来"防护**：未来想恢复变更类表格 → 必须先解释"为什么 changes/{id}.md frontmatter 不够"，且会撞上"双源维护一定漂移"的实战教训（CHANGELOG 里 P0-59 已记录 BG-009/BG-010/BG-013 偏离案例）
- 不动：
  - templates/change-request.md frontmatter schema（已是变更单源 · v7.3.10+P0-33）
  - templates/feature-state.json `change_id` 字段（Feature → 变更反查机制）
  - PMO 在 triage 时的变更归属硬阻塞（status != locked 时 · 现在直接读 changes/{id}.md frontmatter）
- 影响面：
  - 改动文件：8 个（templates/teamwork-space.md 主砍 / FLOWS.md×2 / RULES.md×3 / roles/pm.md / rules/naming.md / templates/change-request.md / PRODUCT-OVERVIEW-INTEGRATION.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：templates/teamwork-space.md 202 → ~145 行（-57 行）
- 后续（建议）：
  - 用户的实战 aon-ptr/teamwork_space.md 可以按本 patch 整体重写——把 14 个 BG 行 + 27 个变更记录行的实质内容迁到 `product-overview/changes/{BG-xxx}.md`（每变更一个文件 · 复用 change-request.md 模板）；不强制
  - PMO 在 triage 入口检查变更归属时直接 grep `changes/*.md` frontmatter 即可，无需读 teamwork_space.md

---

## v7.3.10 + P0-58

> v7.3.10+P0-58 teamwork_space.md 单元格膨胀硬规则化 patch（最简化思路）：用户基于实战 aon-ptr/teamwork_space.md 反馈"变更内容应该一句话"+"跨项目需求追踪也比较大"+"降低 PMO 负担，最简化思路解决问题"。盘点发现：「变更记录」段、「规划状态」槽位、「子项目清单当前状态列」、「跨项目当前阻塞」段**全部无字数 / 单行 / 详情外迁硬约束**——这是用户实战中表格单元格膨胀到 1500+ 字的根因。本 patch 在 templates/teamwork-space.md（**唯一权威源**）每个表格紧邻的 quote block 加显式硬规则，**不加 PMO 主动扫描职责、不加脚本、不加 RULES.md 红线**——读到表自然遵循。术语漂移"跨项目需求追踪 → 跨项目变更索引"统一同步。

### P0-58：teamwork_space.md 单元格硬规则化（最简化思路 / 降低 PMO 负担）

- 触发：用户实战 teamwork_space.md 单元格膨胀（变更记录某行 1500+ 字 / 跨项目需求追踪 BG 行 1500-2500 字）+ 显式要求"最简化思路 / 降低 PMO 负担"
- 设计哲学：**模板是单一权威源，硬规则写在表格紧邻的 quote block 里**——PM/PMO/PL 起草时按模板硬规则填，无需 PMO 在 triage 入口主动扫描。读模板自然知道"任一单元格 ≤ 1 行 / 详情外迁"
- 处理（5 处加规则 + 1 处文件顶层加总纲 + 4 处术语统一）：
  - **P0-58-1. templates/teamwork-space.md 文件顶部加核心简化原则**：「teamwork_space.md 是全景索引，不是事件日志 / 进度看板 / 评审记录。任一表格的任一单元格都应 ≤ 1 行；详情一律外迁到对应文档」+ 引用各表硬规则段
  - **P0-58-2. 规划状态段加硬规则**：4 槽位每个 ≤ 1 行 / 多事件累积只保留最近一次 / 旧事件移到 changes/{id}.md「变更日志」
  - **P0-58-3. 执行线概览段加硬规则**：「使命」/「关键里程碑」≤ 1 行 / 取自执行手册原文 / 不复述背景 / 不加事件级补充
  - **P0-58-4. 子项目清单段加硬规则**：表内任一单元格 ≤ 1 行 /「当前状态」等可选列只写最近一次状态结论 + 链 PROJECT.md / ROADMAP.md / 不复述 Feature 进度详情 / 不堆事件历史
  - **P0-58-5. 跨项目变更索引段加硬规则**：任一单元格 ≤ 1 行 /「简介」≤ 30 字 / 禁 inline 复述子 Feature 编号清单 / 推进顺序 / 联调依赖 / 阶段事件（一律落 changes/{id}.md）
  - **P0-58-6. 跨项目当前阻塞段加硬规则**：每行 ≤ 1 行 / 已解决项必须当次移走（不可保留 ✅ 历史行让表越积越多）
  - **P0-58-7. 变更记录段加硬规则（核心修复）**：「变更内容」必须一句话 ≤ 50 字 / 格式 `<动作> + <对象> + <可选 changes/{id}.md 链接>` / 禁 inline 复述子 Feature 编号 / 推进顺序 / 评审 finding 数 / Codex 命中率 / 阶段事件 / commit hash / 仅记 teamwork_space.md 文件本身的结构性变更（子项目增删 / 架构调整 / 命名规范 / CHG 锁定）/ Feature 级 / BG 级事件**禁止进本表** / 表行数体感上限 ~30 行 / 超出归档到 `product-overview/changes/teamwork-space-history.md`
  - **P0-58-8. 术语漂移统一**：FLOWS.md L600 + RULES.md L759/L931/L1185 + rules/naming.md L105 + templates/teamwork-space.md L199 中的"跨项目需求追踪"统一改为"跨项目变更索引"（v7.3.10+P0-33 命名 · 旧名 fallback 注释保留）
  - **P0-58-9. 版本号 + CHANGELOG**：7.3.10+P0-57 → 7.3.10+P0-58
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：6 处 quote block 硬规则 + 1 处文件顶层总纲 ≈ 25 行；4 处术语统一 ≈ 4 字面替换
  - **删**：未删（本 patch 是规则化补强）
  - **避免做的事**（最简化思路核心）：❌ 不加 `templates/check-teamwork-space.py` 长度门禁脚本 / ❌ 不加 PMO 在 triage 入口主动扫膨胀的职责段 / ❌ 不加 RULES.md 红线 / ❌ 不动用户实战 teamwork_space.md（迁移决定权交给用户）。这些都是"加 PMO 负担"的反模式
  - **"重新触发回来"防护**：模板硬规则在 quote block 里读到表自然看到 / 术语漂移已统一 / 未来想"打回原形"必须先动模板，模板是单源
- 不动：
  - templates/change-request.md（已有完整 schema · 不动）
  - PMO / PM / PL 角色文件（不加 PMO 主动扫描职责 · 最简化原则）
  - 用户实战 teamwork_space.md（迁移与否由用户决定 · 框架不强制）
- 影响面：
  - 改动文件：5 个（templates/teamwork-space.md +~25 行硬规则 / FLOWS.md / RULES.md / rules/naming.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：templates/teamwork-space.md 180 → ~205 行（+~25 行硬规则）
- 后续（建议）：
  - 用户可基于新硬规则把 aon-ptr/teamwork_space.md 的「变更记录」+「跨项目需求追踪」段瘦身（迁移到对应 changes/{BG-xxx}.md）；不强制
  - 未来若发现新的实战膨胀模式（如某个新增列又超长），同样在模板对应段加硬规则即可

---

## v7.3.10 + P0-57

> v7.3.10+P0-57 命名标准化 patch（Goal-Plan 大小写统一）：用户提议"我们把名词统一下 Goal-Plan 统一大写字母开头，连词符号，避免大小写问题"。盘点出 103 处 `goal-plan` 小写中真正 prose 不一致只有 2 处（standards/output-tiers.md），其余全是文件名 / 路径 / markdown 链接 URL（保留小写为 filesystem 标识）+ CHANGELOG 历史记录（不回溯）；66 处 `goal_plan` 全是 state.json 字段名 / enum 值（code identifier，不能改）。本 patch 修 2 处 prose + 在 rules/naming.md 加"Stage 名词在 prose 中的标准形"段作为前向防护。

### P0-57：Goal-Plan 命名大小写统一（避免漂移）

- 触发：用户"我们把名词统一下 Goal-Plan 统一大写字母开头，连词符号，避免大小写问题"
- 设计哲学：**prose 用标准大写形 / code identifier 用小写形**——前者是人读概念，后者是机读标识符（修了破 schema）
- 盘点：
  - `Goal-Plan` 203 处（标准形，✅）
  - `goal-plan` 103 处：~25 处文件名 / ~76 处 CHANGELOG-OPTIMIZATION-PLAN 历史 / **2 处 prose 不一致**（standards/output-tiers.md L3 + L108）
  - `goal_plan` 66 处：state.json 字段 / enum / stage_contracts 键，**全部不动**
  - 无 `Goal Plan` / `goal Plan` / `GoalPlan` 等其他变体
- 改动：
  - **P0-57-1. 修 standards/output-tiers.md L3**：`triage / goal-plan / blueprint / dev / review / test / ship` → `triage / Goal-Plan / blueprint / dev / review / test / ship`
  - **P0-57-2. 修 standards/output-tiers.md L108**：同上 stage 列表 prose
  - **P0-57-3. 在 rules/naming.md 末尾追加「Stage 名词在 prose 中的标准形」段**：列出 7 个 Stage 标准形 vs code identifier 形对照表 + 4 条硬规则（前向防护，避免再次漂移）
  - **P0-57-4. 版本号 + CHANGELOG**：7.3.10+P0-56 → 7.3.10+P0-57
- **加 1 删 1 元规则核算**（P0-48 标尺）：
  - **加**：rules/naming.md +~25 行（标准形对照表 + 硬规则）
  - **改**：standards/output-tiers.md 2 行（不增不减）
  - **删**：未删
  - **本 patch 是规则化补强**（非冗余清理），增加的内容是单源标准 — 防止未来散落漂移。这种"前向防护规则"按 P0-48 元规则不计入冗余增量
  - **"重新触发回来"防护**：未来 PMO 起草新 prose 时必须 cite naming.md 标准形；外部 review / Subagent 起草时也必须遵守
- 不动：
  - `goal-plan-stage.md` 文件名（filesystem 标识，全部保持）
  - `goal_plan_*` state.json 字段 / enum 值（code identifier，破坏 schema）
  - docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md 历史条目（事实记录）
  - markdown 链接 URL 部分（如 `[stages/goal-plan-stage.md](../stages/goal-plan-stage.md)`）
- 影响面：
  - 改动文件：3 个（standards/output-tiers.md / rules/naming.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：standards/output-tiers.md ±0 行 / rules/naming.md +~25 行 / 其他元数据
- 后续：未来其他 Stage 名词若发现漂移（如 `Plan stage` / `goal-plan stage` 等），按 naming.md 标准形修正即可，patch 可合并到一次。

---

## v7.3.10 + P0-56

> v7.3.10+P0-56 roles/pmo.md 减负 patch（中等档 ~377 行减负，从 2179 → 1802 行，17.3%）：实施 P0-55 拆出的 H 维度。基于 P0-48 元规则（加 1 删 1 + "重新触发回来"标尺）以**引用化 / 单源化**方式删除与 triage-stage / goal-plan-stage / RULES.md / templates/state-patch.py 等权威源重复的段落，PMO 角色契约保留核心硬规则（必须输出项 + 写入硬时机表 + Stage 完成资格 5 条等），不动调度责任、产品决策边界、auto 模式豁免、Ship Stage 速查等 PMO 专属段。

### P0-56：roles/pmo.md 减负 引用化（中等档 ~400 行）

- 触发：用户在 P0-56 砍切优先级中选"中等（推荐）"
- 设计哲学：单源化 + 引用化（refs 取代 inline 复述）。PMO 角色契约 = 调度责任 + 必须输出项 + 写入时机 + 完成资格判定，不重复执行细节（执行细节单源在 stages/ 与 RULES.md 与 templates/state-patch.py）
- 改动：
  - **P0-56-1（盘点）**：Subagent 出 11 类重复段精细清单（review-log.jsonl 详细 / 完成报告模板 / Bug 流程矩阵 / state.json patch 脚本规范 / ADR 扫描详细 / KNOWLEDGE 扫描详细 / 智能推荐表注释 / 变更归属检查 / 自下而上影响合并 / 等）
  - **P0-56-2（拍板）**：用户选中等档（300-400 行 / 删 review-log + 完成报告模板 + Bug 流程 + state.json patch + ADR/KNOWLEDGE 引用化）
  - **P0-56-3（执行）**：实际删 377 行
    - **删 review-log.jsonl 详细段（53 行）** → 替换为引用 `templates/review-log.jsonl`（单源）
    - **删功能完成报告模板（96 行）** → 替换为「PMO 完成资格判定核心 5 条」（执行细节回归 stages/）
    - **删 Bug 流程判断详细矩阵（127 行）** → 替换为引用 RULES.md / init-stage.md / FLOWS.md 权威源
    - **删 state.json patch 脚本规范（51 行）** → 替换为引用 RULES.md § state.json 维护硬规则 + templates/state-patch.py
    - **ADR 索引扫描详细（42 行）+ KNOWLEDGE 扫描详细（75 行）→ 引用化为统一段（27 行）**：执行细节单源回归 triage-stage.md Step 2/3，PMO 段只保留硬契约（必须输出 / 读取上限 / 不下决策 / 写入时机表）
  - **P0-56-4（验证 + 收尾）**：CHANGELOG + 版本号 7.3.10+P0-55 → 7.3.10+P0-56 + 一致性自检
- **加 1 删 1 元规则核算（P0-48 标尺）**：
  - **加**：~30 行（5 个引用替换段）
  - **删**：~407 行（实际删除原段）
  - **净减**：377 行（17.3%）
  - **"重新触发回来"防护**：PMO 角色契约硬规则（必须输出 / 写入时机 / 完成资格 5 条）保留 inline，未删；执行细节链接已存在（triage-stage / RULES.md / templates / FLOWS.md），未来"打回原形"需在权威源动而非在 PMO 段加回
- 不动：
  - 路由权威段（v7.3.10+P0-41，PMO 专属硬规则）
  - 产品决策边界段（v7.3.10+P0-38-B，PMO 专属硬规则）
  - 用户质疑反应模式段（v7.3.10+P0-34，PMO 专属）
  - state.json 状态机维护规范 + 流转前必做 + Stage 内访问模式约束（v7.3.2/P0-23，PMO 调度核心）
  - 自下而上影响升级评估段（v7.3.4，PMO 专属）
  - auto 模式豁免规则段（v7.3.9+P0-11，PMO 专属）
  - Ship Stage 双段职责速查（v7.3.10+P0-29/P0-32，PMO 专属）
  - 调度责任段（v7.3.10+P0-44/P0-46/P0-49，PMO 专属）
- 效果：
  - roles/pmo.md 2179 → 1802 行（cut 377 行 / 17.3%）
  - PMO 维护成本下降：执行细节调整只需在 stages/ 与 RULES.md 单源更新
  - "Reactive evolution"反模式被切断：PMO 段不再随每次执行细节调整而膨胀
- 待跟进（后续 patch）：
  - P0-57+ 候选：FLOWS.md / standards/* 同样的引用化扫描（如发现类似的"PMO 段长尾化"在其他文件）
  - 长期：每次 P0 patch 完成后跑一次 audit subagent 检查"是否在某文件加了 inline 内容（应在权威源单源化）"

---

## v7.3.10 + P0-55

> v7.3.10+P0-55 文档层一致性 patch（C + A + B + D 四维度，H 拆出 P0-56）：基于 audit 报告 P1+P2 优化项落地——C 6 stage spec 加可配置点清单 + A FLOWS.md 4 选 1 → 双对齐 语汇统一 + B feature-state.json enum vs STATUS-LINE.md 阶段字段映射 + D SKILL.md 显式化"三层按需启动"原则总纲。H roles/pmo.md 减负 ~400 行 拆出 P0-56 单独做（风险中等需仔细盘点）。

### P0-55：文档层一致性（C + A + B + D，H 拆 P0-56）

- 触发：用户"继续"采纳 P0-55 文档层路径
- 设计哲学：把架构原则（三层按需启动）+ stage 可配置点显式化到文档总纲，跨文件命名 / 字段映射统一化，让 future PMO 操作有清晰单源
- 处理（5 处改造）：
  - **P0-55-1. 6 stage spec 顶部加"可配置点清单"段（C 维度）**：goal-plan / blueprint / dev / review / test / ship 各加 5-7 行配置点表格（review_roles / 角色 execution / 子流程触发条件 / round_loop / hint_overrides 等），用户易查 + 标注"不变内核"
  - **P0-55-2. FLOWS.md 4 选 1 → 双对齐 语汇统一（A 维度）**：FLOWS.md / roles/pmo.md 中 triage 流程确认相关的"4 选 1 暂停点"老语汇统一改为"双对齐暂停（v7.3.10+P0-49）"。Ship Stage / 变更规划等真实多选项暂停语汇保留（不混淆）
  - **P0-55-3. STATUS-LINE.md 阶段字段映射表（B 维度）**：加 state.json `current_stage` enum vs STATUS-LINE 阶段字段语义映射表（triage / goal_plan / ui_design / blueprint / dev / review / test / browser_e2e / pm_acceptance / ship / completed → 用户可读语义）。修正 🌐 Ext 徽章读取逻辑（P0-38 起读 review_roles[] 含 external，不再读老 *_enabled 字段）
  - **P0-55-4. SKILL.md 加"三层按需启动"原则段（D 维度）**：在红线段后加"🎯 三层按需启动原则"段作为框架设计总纲（L0 triage 定初步流程 / L1 流程编排 stage / L2 stage 执行方式可配置 + stage 内部规范不变 + 引用 standards/stage-instantiation.md / output-tiers.md）
  - **P0-55-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-54 → 7.3.10+P0-55

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 FLOWS.md / roles/pmo.md 中 triage 相关"4 选 1 暂停点"老语汇（统一为"双对齐暂停"，P0-49 改造后的真相源）
  - 删 STATUS-LINE.md 🌐 Ext 徽章读"任一 *_enabled=true"老逻辑（改为"review_roles[] 任一含 external"，P0-38 改造后单源）

- **加 1 删 1 论证**（P0-48 元规则）：
  - **加**：6 stage 可配置点清单（5-7 行表格 × 6 = ~36 行）+ STATUS-LINE 阶段字段映射表（~12 行）+ SKILL.md 三层按需启动段（~50 行）
  - **删**：4 选 1 老语汇 + Ext 徽章老逻辑 + （间接）P0-56 待删 roles/pmo.md ~400 行
  - 净加规则数：本 patch 是文档层显式化（让现有架构对外可见），非增加新规则。可配置点清单只是把分散在 spec 各段的字段汇总，不引入新字段；三层按需启动段是把已有原则（散落在 P0-49 / P0-51 / P0-52 等多个 patch）抽到顶层

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果 PMO 操作时找不到"某 stage 有什么可配置点" → 看 stage spec 顶部清单段，找不到再修清单（不再分散到各段）
  - 如果用户口语"4 选 1" → PMO 应主动澄清是 triage 双对齐还是 Ship/变更 多选项暂停
  - 如果新读者不理解架构 → 看 SKILL.md 三层按需启动段，找不到再补总纲

- 风险控制：
  - 文档显式化不破坏现有规则（只是抽到顶层 / 单源化）
  - 老语汇 fallback 保留在 CHANGELOG 历史条目（不改）
  - 红线数保持 15 条
  - 不影响实际行为，仅文档导航 / 命名 / 总纲

- 影响面：
  - 改动文件：~10 个（6 stage spec 加配置清单 + FLOWS.md 语汇统一 + roles/pmo.md 语汇统一 + STATUS-LINE.md 加映射表 + SKILL.md 加三层段 + CHANGELOG）
  - 行数变化：6 stage spec 各 +5-7 行 / FLOWS.md ±5 行（替换）/ STATUS-LINE.md +~15 行 / SKILL.md +~55 行

- 待跟进（拆出 P0-56）：
  - **P0-56 roles/pmo.md 减负**（H 维度）：删/合并 ~400 行重复内容（与 triage-stage.md / goal-plan-stage.md / standards/external-model.md 重复段），需仔细盘点哪些段可删，单独 patch 风险更可控

---

## v7.3.10 + P0-54

> v7.3.10+P0-54 行为层一致性 patch（E + G + F 三维度）：基于整体 audit 报告的前 3 项落地——E（主对话 Tier 规范单源化 + 6 stage spec 各加 Tier 应用段）+ G（roles/pmo.md plan_enabled 自相矛盾修正 + standards/external-model.md 链接化）+ F（RULES.md 加 state.json 维护硬规则把 P0-52 隐性约定升格为显式硬规则）。

### P0-54：行为层一致性（E + G + F）

- 触发：用户"按建议"采纳整体 audit 报告优先级
- 设计哲学：把 P0-49-A / P0-52 的设计意图从 triage-specific / 隐性约定升格为框架级硬规则，覆盖所有 stage
- 处理（5 处改造）：
  - **P0-54-1. 抽取 standards/output-tiers.md 单源**（E 维度）：从 triage-stage.md L751-853 抽取通用 Tier 1/2/3 规范 + 4 类反模式（履职报告 / state.json 复述 / 决策菜单膨胀 / 工程性切片暂停）+ 主对话输出红线 → 单源 standards/output-tiers.md（~150 行）
  - **P0-54-2. 6 stage spec 加 Tier 应用段**（E 维度）：goal-plan / blueprint / dev / review / test / ship 各加"主对话输出 Tier 应用"段（10-15 行 stage-specific Tier 1/2/3 应用 + 引用 standards/output-tiers.md）。其中 goal-plan / blueprint / review 升级原 P0-48 "主对话输出红线"段；dev / test / ship 新加
  - **P0-54-3. roles/pmo.md plan_enabled 矛盾修正 + external-model.md 链接化**（G 维度）：(a) roles/pmo.md L552 / L573 / L702 自相矛盾修正——L552 说"不再有 plan_enabled"，L573-575 / L662-666 / L702 仍用，统一为 P0-38 后的"external ∈ review_roles[] 单源判定" + fallback 规则更新；(b) standards/external-model.md §5.4 老 schema 删除，改为链接到 stage spec
  - **P0-54-4. RULES.md 加 state.json 维护硬规则**（F 维度）：新增"state.json 维护硬规则"段（优先级 patch.py > Edit > 禁止 Write 全文 + 3 类合法降级场景 + 典型调用范例 + PMO 校验门禁）。把 P0-52 的"隐性约定"升格为 RULES.md 显式硬规则
  - **P0-54-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-53 → 7.3.10+P0-54

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 goal-plan / blueprint / review stage spec 中原 P0-48 "主对话输出红线"3 行红线段（升级为 Tier 1/2/3 应用）
  - 删 roles/pmo.md L573-575 老 `plan_enabled / blueprint_enabled / review_enabled` 默认值表
  - 删 roles/pmo.md L662-666 state.json schema 中的老三字段
  - 删 standards/external-model.md §5.4 老 schema + Fallback 表（链接化到 pmo.md）
  - 删 P0-52 的"隐性约定"措辞（升格为 RULES.md 显式硬规则）

- **加 1 删 1 论证**（P0-48 元规则）：
  - **加**：standards/output-tiers.md（新文件）+ 6 stage spec 各加 Tier 应用段 + RULES.md 加 state.json 硬规则段
  - **删**：3 stage spec 旧"主对话输出红线"段（升级覆盖）+ roles/pmo.md L552/L573/L662/L702 自相矛盾陈述 + standards/external-model.md §5.4 复述
  - 净加规则数：±0（新加 standards/output-tiers.md 和 RULES.md state.json 硬规则段，但删除了同等数量的 stage 内重复 + roles/pmo.md 自相矛盾 + external-model 复述）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果其他 stage 仍出现"履职报告"/state.json 复述 → 修 standards/output-tiers.md 反模式禁令，不放弃 Tier 规范
  - 如果用户找不到 plan_enabled → 提示用 review_roles[] 单源判定，不恢复老字段
  - 如果 PMO 仍用 Edit 全文更新 state.json → 检查是否符合 3 类合法降级场景，否则视为流程偏离

- 风险控制：
  - Tier 1/2/3 规范是行为指引，不破坏现有 stage 流程
  - plan_enabled fallback 规则保留（老 state.json 仍可读）
  - state.json 硬规则有 3 类合法降级场景（保留 Edit 灵活性）
  - 红线数保持 15 条（state.json 维护硬规则不进 15 红线，进 RULES.md 单独段）

- 影响面：
  - 改动文件：~10 个（新建 standards/output-tiers.md + 6 stage spec + roles/pmo.md + standards/external-model.md + RULES.md + SKILL.md + stages/init-stage.md + docs/CHANGELOG.md）
  - 行数变化：standards/output-tiers.md +~150 / 6 stage spec 各 +10-15 = +60-90 / roles/pmo.md 修正不增减 / standards/external-model.md 减~50（链接化）/ RULES.md +~50

- 待跟进（P0-55 文档层）：
  - C: 6 stage spec 顶部加"可配置点清单"段
  - A: FLOWS.md 4 选 1 → 双对齐 语汇统一 + roles/pmo.md triage 职责合并
  - B: feature-state.json enum 注释 + STATUS-LINE.md 阶段字段映射
  - D: SKILL.md 显式化"三层按需启动"原则
  - H: roles/pmo.md 减负（删 ~400 行重复内容）

---

## v7.3.10 + P0-53

> v7.3.10+P0-53 单 stage 改名 plan → goal-plan：用户提议"plan stage 改成 goal-plan 更合理一些"——跟 blueprint（蓝图层）对仗清楚，避免跟 PDCA "plan" 混淆。用户拍板"改 goal-plan，其他不动，不考虑历史兼容"。本 patch 完成机械化改名。

### P0-53-A：单 stage 改名 plan → goal-plan（不考虑历史兼容）

- 触发：用户"plan 改成 goal-plan 是否更合理一些" + "改 goal-plan 把"
- 设计哲学：goal-plan 跟 blueprint 对仗（goal-plan = 做什么 + 为什么 / blueprint = 怎么做 + 怎么测）；避免 PDCA 的泛 "plan" 词混淆。其他 stage 名（dev / review / test / ship 等）不改
- 处理（4 处改造）：
  - **P0-53-A-1. 搜索 plan-stage 全部引用**：grep 全部 plan-stage.md / Plan Stage / plan stage / plan_substeps_config / current_stage="plan" 等引用，确认范围 ~280 处（CHANGELOG/OPTIMIZATION-PLAN 历史文档 163 处不动）
  - **P0-53-A-2. rename 文件 + 批量替换**：mv stages/plan-stage.md → stages/goal-plan-stage.md；sed -i 批量替换 5 类引用（plan-stage.md → goal-plan-stage.md / Plan Stage → Goal-Plan Stage / plan stage → goal-plan stage / plan_substeps_config → goal_plan_substeps_config）；排除 docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md
  - **P0-53-A-3. state.json schema 改名**：completed_stages 数组 "plan" → "goal_plan"；stage_contracts.plan → stage_contracts.goal_plan；planned_execution.plan → planned_execution.goal_plan；executor_history[].stage = "plan" → "goal_plan"；stage_enum 注释更新
  - **P0-53-A-4. SKILL.md / state-patch.py 顶部 docstring 同步 + 版本号 bump + CHANGELOG**：SKILL.md 顶部 description "Plan → UI Design → ..." → "Goal-Plan → UI Design → ..."；红线 #1 流程选择段 "Plan/Blueprint/UI/..." → "Goal-Plan/Blueprint/UI/..."；state-patch.py docstring 示例改 goal_plan；版本号 7.3.10+P0-52 → 7.3.10+P0-53

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删除 stages/plan-stage.md（mv 到 goal-plan-stage.md）
  - 删除所有 "Plan Stage" 字面量（替换为 Goal-Plan Stage）
  - 删除 plan_substeps_config 字段名（替换为 goal_plan_substeps_config）
  - 删除 state.json current_stage enum 中 "plan" 值（替换为 goal_plan）
  - 不考虑历史兼容（用户明确指示）—— 不加 fallback alias，老 state.json 不可用

- **加 1 删 1 论证**（P0-48 元规则）：
  - 本 patch 类型 = 命名重构（C 段例外白名单："新角色 / 新 Stage 加入" 的镜像——stage 改名属结构性重命名，不是规则增量）
  - **加**：0（不新增字段 / 规则）
  - **删**：1 整套老命名（"Plan Stage" / "plan_substeps_config" / "current_stage=plan"）
  - 净规则数：±0（命名替换非规则增减）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果用户口语说"plan stage" 频繁出现混淆 → PMO 应主动澄清并 cite goal-plan-stage.md
  - 如果其他 stage（dev / review / test）也出现命名歧义 → 触发"全套改名"讨论（不只是 plan 单点）
  - 如果"goal-plan" 在新场景反而比"plan"更模糊（如 "goal" 跟 "objective" 重复）→ 考虑改回或重新命名

- 风险控制：
  - **不考虑历史兼容**（用户明确）—— 老 Feature 的 state.json `current_stage: "plan"` 在新版下视为非法值；进行中 Feature 需手动改为 "goal_plan"
  - 跨子项目搜索 stage 名时建议同时搜 "plan" 和 "goal_plan" 双关键词，确保不漏老 Feature
  - CHANGELOG / OPTIMIZATION-PLAN 历史条目保留原文（不改），保持历史可读性
  - 红线数保持 15 条
  - 不影响 PDCA "plan" 等独立词的使用（仅改 stage 字面量）

- 影响面：
  - 改动文件：~30+ 个（stages/{各 stage}.md / roles/*.md / templates/{prd,feature-state.json,state-patch.py}.md / FLOWS.md / RULES.md / SKILL.md / STATUS-LINE.md / standards/stage-instantiation.md / agents/README.md / etc）
  - 替换数：~120 处（不含 CHANGELOG / OPTIMIZATION-PLAN）
  - 文件 rename：1 个（plan-stage.md → goal-plan-stage.md）
  - state.json schema：current_stage / stage_contracts / planned_execution / executor_history 4 处改名
  - 用户体验：stage 名跟 blueprint 对仗清楚，goal-plan = 目标层 vs blueprint = 蓝图层正交

- 待跟进（非 P0-53 范围）：
  - 验证 1-2 个真实 Feature 跑下来 goal-plan 命名是否真的减少了歧义（vs 原 plan）
  - 如果其他 stage 也想类似改名（如 "blueprint" → 更精确的名字）→ 单独评估，不在本 patch 内
  - state.json schema_version 字段未 bump（v7.3.9 不动）—— 老 Feature 仍 schema_version=v7.3.9，但 current_stage="plan" 视为漂移

---

## v7.3.10 + P0-52

> v7.3.10+P0-52 state.json 增量更新工具：用户观察到 PMO 用 Edit 全文更新 state.json 占用太多 token（一个 Feature 生命周期累积 ~7,500 tokens 仅 state.json 维护，Edit 工具每次发送 50-100 行上下文，且随 state.json 变大累积成本上升）。本 patch 新增 `templates/state-patch.py` —— 增量 patch 工具，PMO 通过 bash 调用，只发送变更字段，节省 ~40% token 成本 + 不随文件大小增长。

### P0-52：state.json 增量更新工具（state-patch.py）

- 触发：用户观察到"对 state.json 的更新是否占用太多资源，使用一个更新脚本传入变更字段更合理"+ 用户 yes
- 设计哲学：把"机读字段维护"从 Edit 全文模式改为 CLI patch 模式，PMO 主对话只发送变更字段，文件大小对成本无影响
- 处理（5 处改造）：
  - **P0-52-1. 新建 `templates/state-patch.py`**（~250 行 Python）：核心脚本支持 5 种操作（--set / --append / --merge-object / --set-note / --unset）+ 智能类型推断（true/false/null/数字/JSON literal）+ schema 校验 + 原子写（先写临时文件 → fsync → mv）+ --dry-run 模式 + --validate schema 校验
  - **P0-52-2. 脚本 docstring 含 5 个调用示例**：Stage 转换 / PRD 评审完成 / Ship 双段 finalize / Bug 简化流程 / 评审循环超 3 轮决策——覆盖典型 PMO state.json 更新场景
  - **P0-52-3. roles/pmo.md 加约定**：在 PMO 责任段（state.json 访问模式约束之后）加"state.json 更新优先用 patch 脚本"段，含优先级（patch 脚本 > Edit > Write）+ 典型调用示例 + 回退到 Edit 的合法场景（嵌套 ≥3 层 / 条件性修改 / ≥10 字段同时改）
  - **P0-52-4. TEMPLATES.md 索引加引用**：新增 state-patch.py 索引条目
  - **P0-52-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-51 → 7.3.10+P0-52

- **脚本核心特性**：
  - **5 种操作**：set scalar / append list（去重）/ merge object / set _note 字段（自动加 _ 前缀）/ unset
  - **智能类型推断**：true → bool / null → None / 数字 → int|float / [{ 开头 → JSON literal / 其他 → string
  - **schema 校验**：基于 templates/feature-state.json 顶层字段名，检测漂移（PMO 自创字段或老字段残留）
  - **原子写**：tempfile + fsync + os.replace，防中断损坏
  - **--dry-run**：预览更新结果不写入
  - **退出码**：0 成功 / 1 错误 / 2 schema WARN（仍写入但 stderr 警告）

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 这是**工具增强型 patch**，未删现有规则；落到 P0-48 C 段例外白名单："新工具/脚本（capability 增强，非规则增量）"
  - 但保留了"加 1 删 1 论证"职责：本 patch 通过引入新工具，**事实上间接删除了"Edit 全文更新 state.json"的隐性规则**（虽然 Edit 仍是合法降级路径，但优先级降为次选）

- **加 1 删 1 论证**（P0-48 元规则例外白名单）：
  - 本 patch 类型 = **工具增强型**（C 段例外白名单："新工具 / 新脚本，capability 增强非规则增量"）
  - **加**：state-patch.py（CLI 工具）+ roles/pmo.md "patch 脚本优先"约定（一段）+ 索引引用
  - **删**：未直接删规则，但通过"patch 脚本优先"约定**事实上降级了 Edit 全文更新的优先级**
  - 净加规则数：+1 段（"patch 脚本优先"约定），符合工具增强型 patch 的接受范围

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果 patch 脚本不支持的复杂 edit 频繁出现 → 扩展脚本支持（add 新操作类型，如 --merge-deep / --conditional-set），不是放弃脚本回到 Edit 全文
  - 如果 schema 校验频繁误报 → 修 schema（feature-state.json 不全），不是关闭校验
  - 如果脚本增加 token 反而比 Edit 多 → 排查命令构造问题（不应该出现，因为 patch 命令长度 ≤ Edit 上下文长度）

- 风险控制：
  - 兼容性：state.json schema 不变，Edit/Write 仍可用作降级路径
  - 原子写防中断损坏（tempfile + fsync + replace）
  - schema 校验是 WARN 不是 ERROR（不阻塞写入，仅 stderr 提示）
  - 红线数保持 15 条
  - 不影响其他文件读取 state.json（仅改 PMO 写入方式）

- 影响面：
  - 改动文件：5 个（新建 templates/state-patch.py / roles/pmo.md / TEMPLATES.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 新增脚本：~250 行 Python（含 docstring 5 个示例）
  - **预估 token 节省**：每 Feature ~3,000+ tokens 主对话开销（15-20 次 state.json 更新 × 200 tokens 节省）
  - 不影响现有 Feature（state.json schema 不变，老 Feature 可继续 Edit 也可改用 patch 脚本）

- 待跟进（非 P0-52 范围）：
  - 跑 1-2 个真实 Feature 验证 patch 脚本节省 token 是否符合预估
  - state.json schema（feature-state.json）需补"shipped / shipped_at / completed_at / merge_commit"等顶层字段（当前 schema 只含 `ship` 嵌套对象，但实战中 PMO 把 ship_phase2 状态写到顶层 → 漂移），→ 推迟到 P0-53 schema 收敛 patch
  - state-patch.py 未来可加更多操作（如 --merge-deep 嵌套 merge / --conditional-set 条件性更新）

---

## v7.3.10 + P0-51

> v7.3.10+P0-51 Plan Stage 体感优化大 patch：用户在 P0-50（FLOWS.md 减负）后让继续逐 Stage 看，从 Plan Stage 开始。Subagent 盘点发现 10 项可优化（2 P0 + 6 P1 + 2 P2），可减 ~280 行 + 实质改善小 Feature 体感。本 patch 一次性落地全部 P0+P1+P2 改造。

### P0-51：Plan Stage 体感优化大 patch（10 项可优化一次性落地）

- 触发：用户"继续逐个 stage 看"+ subagent 盘点发现 Plan Stage 10 项可优化 + 用户拍板"1 个大 patch"
- 设计哲学：从"PMO 操作手册"瘦身为"流程契约 + 关键决策点"，把 PM checklist / discuss 双源 / external_enabled 老字段等冗余迁出
- 处理（6 项改造）：
  - **P0-51-1. 子步骤 2 PL-PM 讨论改条件启用**：从"永远必做"改为"仅当 `pl ∈ review_roles[]` 时启用"。Bug 修复 / 纯技术 refactor / 敏捷需求等不含 PL 的 Feature 跳过子步骤 2，子步骤 1 完成后直接进子步骤 3。子步骤序列表 + 子步骤 2 段同步更新启用条件说明
  - **P0-51-2. discuss/ 文件单源化到 PRD-REVIEW.md**：撤销 P0-43 / P0-44 "discuss/ 文件双源"决定。所有 PL-PM 讨论轮次集中写到 `PRD-REVIEW.md.reviews[role=pl].pl_rounds[]` 数组（schema：round / pl_feedback / pm_response / verdict）+ `final_verdict / final_verdict_at`。删除 discuss/PL-FEEDBACK-R{N}.md / discuss/PM-RESPONSE-R{N}.md 双源文件
  - **P0-51-3. PM 起草规范 checklist 迁到 templates/prd.md**：把 plan-stage.md 的 70 行 PM checklist（通用 + UI 维度 + PRD 不写什么 + 起草后自查）迁到 templates/prd.md 新增段。plan-stage.md 仅保留简版核心约束（3 行）+ cite templates/prd.md 单源。`pm_self_check` schema 改为 `{checklist_passed: bool, failed_items: [...], notes: ...}`，不复述 checklist 全文（避免主对话述 3 遍）
  - **P0-51-4. Designer 中途补启用 + PASS_WITH_CONCERNS 响应规则**：(a) PM 起草过程发现需要 UI（triage 漏识别）→ 补启用机制：PM 标 PRD frontmatter `requires_ui: true` → PMO 在子步骤 3 dispatch 前自动补加 designer 到 active_roles + 写 hint_overrides；(b) 子步骤 4 触发条件从"仅 NEEDS_REVISION"扩展为"NEEDS_REVISION 或 任意 review 含 ≥1 个 SHOULD-fix concern"；severity 三级分类（MUST-fix / SHOULD-fix / NICE-to-have）
  - **P0-51-5. external_enabled 字段双源化清理**：plan-stage.md 残留 3 处引用 `state.external_cross_review.plan_enabled`（P0-38 已 deprecated），改为 `external ∈ state.plan_substeps_config.review_roles[]` 单源判定
  - **P0-51-6. 评审分歧暂停 vs 工程性切片界定**：子步骤序列表加红线"异常暂停不算工程性切片"——业务方向锁定失败 / 评审循环不收敛是真实异常分支，不是预防性切片暂停
  - **P0-51-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-50 → 7.3.10+P0-51

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 plan-stage.md PM 起草规范 checklist 全文（~70 行）→ 单源化到 templates/prd.md
  - 删 plan-stage.md discuss/ 文件双源契约段 → 单源化到 PRD-REVIEW.md.reviews[].pl_rounds[]
  - 删 plan-stage.md 子步骤 2 "永远必做"硬约束 → 改条件启用（pl ∈ review_roles[]）
  - 删 plan-stage.md 3 处 `state.external_cross_review.plan_enabled` 引用（P0-38 已 deprecated 但漂移残留）→ 改 review_roles[] 单源判定
  - 删 plan-stage.md 子步骤 4 "仅 NEEDS_REVISION 触发"过松条件 → 改为 SHOULD-fix 也触发
  - 删 PM checklist 在 PRD-REVIEW.md.reviews[].pm_self_check 里逐项记录的设计 → 改为 checklist_passed bool + failed_items 列表

- **加 1 删 1 论证**（P0-48 元规则）：
  - **加**：(a) Designer 中途补启用机制 (b) PASS_WITH_CONCERNS / SHOULD-fix 触发规则 (c) PRD-REVIEW.md.reviews[].pl_rounds[] schema (d) severity 三级分类 (e) 子步骤 2 条件启用判定 + 异常暂停定义
  - **删**：(a) PM 起草规范 checklist 全文（70 行迁出，主对话不复述）(b) discuss/ 文件双源契约 (c) external_enabled 老字段引用 (d) 子步骤 2 "永远必做"硬约束
  - 净加规则数：±0（加判定/schema = 删 checklist/双源/老字段），符合 加 1 删 1
  - 实际行数变化：plan-stage.md 884 → 850（净减 ~34 行 + 加 ~30 行新规范）；templates/prd.md 322 → 380（加 PM checklist 段）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果不含 PL 的 Feature 跑下来 PRD 业务方向不准 → 说明 review_roles 决策时漏了 PL → 修 triage execution_hints 推导，不是恢复"子步骤 2 永远必做"
  - 如果 PASS_WITH_CONCERNS 但 SHOULD-fix 被忽视导致下游问题 → 说明 severity 分级判定不准 → 改进 review 角色 spec 的 severity 用法，不是恢复"仅 NEEDS_REVISION 触发"
  - 如果 Designer 补启用机制让评审循环混乱 → 说明 PM 起草时识别 UI 触点不及时 → 改进 PRD 模板的 UI 提示，不是回退到"启用决策一旦锁死不可调整"
  - 如果 discuss/ 单源化导致 PL 讨论深度不够 → 说明 PRD-REVIEW.md.reviews[].pl_rounds[] schema 不够灵活 → 扩 schema，不是回到 discuss/ 双源

- 风险控制：
  - 子步骤 2 改条件启用：现有进行中的 Feature 若已建 discuss/ 文件，PRD-REVIEW.md.reviews[].pl_rounds[] 兼容（PMO 读取时 fallback 旧 discuss/ 文件，新 Feature 走单源）
  - PM checklist 迁出：plan-stage.md 仍 cite 简版核心约束，PMO 起草前 cite templates/prd.md 一次即可，不 break 流程
  - Designer 补启用：仅在 frontmatter requires_ui: true 时触发，不会误启用
  - SHOULD-fix 触发响应：保持 PASS / NICE-to-have 不强制响应（用户在子步骤 5 自行决定是否采纳）
  - 红线数保持 15 条
  - 自我应用 P0-48 C 段元规则（删了什么 + 加 1 删 1 + 重新触发标尺）

- 影响面：
  - 改动文件：4 个（stages/plan-stage.md / templates/prd.md / SKILL.md / stages/init-stage.md / docs/CHANGELOG.md）
  - 行数变化：plan-stage.md 884 → 850（-34）/ templates/prd.md 322 → 380（+58 含 PM checklist 段）
  - 用户体验：(a) 不含 PL 的小 Feature 流程减 20%（跳过子步骤 2 PL-PM 讨论 1-3 轮）(b) PRD-REVIEW.md.reviews[].pl_rounds[] 单源 → 改 PL 意见时只改一处（不用同步 discuss/ 文件）(c) PM 起草 checklist 不在主对话述 3 遍 → token 节省 (d) PASS_WITH_CONCERNS 不再被忽视 → SHOULD-fix concerns 必须响应

- 待跟进（非 P0-51 范围）：
  - review_scope=PRD 边界案例（plan-stage.md L520-560 ~80 行）迁到 roles/{rd,qa,designer}.md 评审 checklist 附录 → 推迟到 P0-52 / P0-53（P2 优先级，工作量大但收益小）
  - 1-2 个真实 Feature 跑完后回顾 SHOULD-fix 触发响应是否合理 / 不含 PL 的子步骤 2 跳过是否真的无问题 / Designer 补启用机制是否真有命中

---

## v7.3.10 + P0-50

> v7.3.10+P0-50 FLOWS.md 减负专版（与 P0-48 同类型）：用户在 P0-49-A 完成后让看 FLOWS.md 是否需要精简。委托 subagent 盘点发现 1124 行有 ~22-27% 冗余（与 triage-stage.md / RULES.md / SKILL.md 红线重复）。本 patch 删 269 行（24% 减量），FLOWS.md 重新定位为「**流程选择决策树 + 流程间横向规则 + 特殊子模式索引**」（不再装 PMO 输出模板 / 类型识别表 / 暂停点规则 / Stage 链复述等已被其他文件接管的内容）。

### P0-50：FLOWS.md 减负专版

- 触发：用户问"FLOWS.md 是否需要精简"+ subagent 盘点发现 22-27% 冗余 + 用户 ok
- 设计哲学：FLOWS.md 从"PMO 操作手册 + 流程模板"瘦身为"流程间横向规则索引"——不复述 triage-stage / RULES / SKILL 红线已有内容
- 处理（5 处砍切）：
  - **P0-50-1. 类型识别表 + 暂停点规则 + 禁止事项**（~37 行）：删 L47-71 6 流程类型识别信号表（与 triage-stage Step 5 完全相同）；删 L323-340 暂停点规则 + 禁止事项段（与 RULES.md / SKILL.md 红线重复）；改为 4 行引用
  - **P0-50-2. PMO 初步分析输出格式段**（最大头，~161 行）：删 L168-328 段（含 PMO 初步分析输出 + 模板清单 + 外部模型决策段，已被 triage-stage Step 8 完全接管，且 P0-49/+P0-49-A 已重构为 Tier 1/2/3 输出层次）；改为 9 行引用 triage-stage 执行报告模板
  - **P0-50-3. 工作区级 / 敏捷需求 / 问题排查 PMO 输出格式**（~73 行）：删 3 处流程级 PMO 输出格式段（都是"📋 PMO 初步分析"格式复述，被 triage-stage 接管）
  - **P0-50-4. PL 路由段红线复述**（~9 行）：删 L114-118 流程类型枚举红线 + 兜底规则复述（已在 SKILL.md 红线 #2 + RULES.md 兜底规则中）；保留 L79-113 PL 路由 + Feature Planning Level 1/2/3 判断主体（独有价值，迁移到 roles/pmo.md 反而违背减负）
  - **P0-50-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-49 → 7.3.10+P0-50

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 FLOWS.md 类型识别表 6 流程信号表（~28 行）→ 单源化到 triage-stage Step 5
  - 删 FLOWS.md 暂停点规则 + 禁止事项段（~17 行）→ 单源化到 RULES.md / SKILL.md 红线
  - 删 FLOWS.md PMO 初步分析输出格式段（~161 行，最大头）→ 单源化到 triage-stage 执行报告模板
  - 删 FLOWS.md 工作区级 PMO 初步分析输出格式段（~30 行）→ 单源化到 triage-stage
  - 删 FLOWS.md 敏捷需求 PMO 分析输出格式段（~32 行）→ 单源化到 triage-stage
  - 删 FLOWS.md 问题排查 PMO 分析输出格式段（~11 行）→ 单源化到 triage-stage
  - 删 FLOWS.md PL 路由段中流程类型枚举红线 + 兜底规则复述（~9 行）→ 单源化到 SKILL.md / RULES.md

- **加 1 删 1 论证**（P0-48 元规则）：
  - 本 patch 类型 = 减负 patch（与 P0-48 同类型）
  - **加**：0（纯减负，仅加 4 处单源化引用，不算新规则）
  - **删**：~278 行（含 5 个独立段 + 1 个红线复述）
  - 净加规则数：负数（仅删旧规则不加新规则），符合"纯减负 patch 例外"（P0-48 C-3 例外白名单）

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果用户找不到"PMO 应该怎么输出 triage 分析"——说明引用链不够清楚，应改进 FLOWS.md → triage-stage.md 的索引（不是恢复 PMO 输出格式重复段）
  - 如果用户问"6 流程类型识别信号是什么"——单源在 triage-stage Step 5，可以加跨文件搜索关键词（不是回到 FLOWS.md 复制表格）
  - 如果跨流程歧义判断（如 Bug vs Feature）出错——说明 triage-stage 信号表不全，应补到 triage-stage（不是回到 FLOWS.md 维护两份）

- 风险控制：
  - 单源化引用 → 双源漂移风险消除（删除的内容都在权威源 triage-stage / RULES / SKILL 已存在）
  - 删的都是"PMO 输出格式"或"红线复述"——不是核心流程规则
  - 保留的是 FLOWS.md 独有价值的段：流程选择决策树 / Feature vs Planning 歧义判断 / Feature Planning 范围判断 / 变更级 Planning 子模式 / 工作区级 Feature Planning / 流程豁免规则 / Bug 简单/复杂判断 / 标准 Feature Planning / 各流程概览图 / Micro 流程 / Bug 闭环验证 / 敏捷需求准入条件
  - 红线数保持 15 条
  - 不影响其他文件，纯单文件减负

- 影响面：
  - 改动文件：3 个（FLOWS.md 主体 + SKILL.md 版本号 + stages/init-stage.md SKILL_VERSION 引用 + docs/CHANGELOG.md）
  - 行数变化：FLOWS.md 1124 → 855（净减 269 行 / **24% 减量**，达到 audit 目标）
  - 用户体验：FLOWS.md 重新定位为"流程间横向规则索引"，更易找到独有内容（不再被 PMO 输出模板淹没）；新读者不会被"PMO 怎么输出"细节冲晕，能聚焦"流程间怎么走"

- 待跟进（非 P0-50 范围）：
  - FLOWS.md 仍存留的 1124-855=269 行减量集中在"PMO 输出格式"段，未来如果 P0-49 主对话输出经过几个真实 Feature 验证后稳定，可考虑下一轮减负移除问题排查/Bug流程内的"PMO 派发规则"等中型段（~50-100 行潜在减量）

---

## v7.3.10 + P0-49

> v7.3.10+P0-49 triage 阶段意图理解段 + 双对齐：经过用户与对话方七轮讨论收敛形成。triage 阶段从单一"流程承诺"扩展为「意图理解段（按流程类型分 schema）+ 流程承诺骨架」双产出，⏸️ 暂停点改双对齐合一（意图 + 流程一次确认）。意图段不落盘（避免新增 artifact，符合 P0-48 减负方向），下一阶段首次产出 commit 时自然落盘到对应人读资产文件（PRD 背景段 / BUG-REPORT 顶部 / 排查记录顶部 / Feature Planning 章节）。本 patch 自我应用 P0-48 「加 1 删 1」元规则。
>
> 🔧 **P0-49-A 修补（不 bump 版本号）**：用户在 P0-49 落地后跑了一个真实 Feature（SVC-PLATFORM-F026 rust struct rename），输出形态有 6 个具体问题（履职报告体感 / 意图段位置太晚 / 没命中扫描也立段 / 骨架理由全展开 / 双对齐退化为 5 选 1 菜单 / state.json 配置在主对话复述）。本修补改造 triage-stage.md 执行报告模板规范——加 Tier 1/2/3 输出层次 + 决策呈现 vs 履职报告原则段 + 默认推荐折叠 / 非默认 💡 标注 + 双对齐二选一姿态 + state.json 复述禁令。

### P0-49-A 修补：triage 输出形态从履职报告改决策呈现（不 bump 版本号）

- 触发：用户跑 SVC-PLATFORM-F026 真实 case 反馈"输出还是有点乱"+ 6 个具体问题
- 设计哲学：triage 输出的核心是给用户**决策依据**，不是 PMO 履职汇报。区分 Tier 1（用户必看的决策点）/ Tier 2（命中或异常才输出的折叠区）/ Tier 3（默认不输出，全部走 state.json）
- 处理（执行报告模板重写）：
  - **Tier 1（永远输出）**：意图理解段 / 流程承诺骨架 / ⏸️ 双对齐暂停点
  - **Tier 2（命中或异常才输出）**：KNOWLEDGE 命中 / ADR 命中 / 跨 Feature 冲突 / 环境异常 —— 仅一行摘要 + 详情可查 state.json
  - **Tier 3（默认不输出）**：角色可用性扫描结果（无异常） / 流程类型独立识别段（已体现在骨架顶部） / worktree mode/path/artifact_root 等机读字段
  - 加 3 个反模式硬约束：履职报告体感 / state.json 复述表 / 5 选 1 决策菜单
  - Feature 骨架渲染规范：默认 Stage（Dev/PM 验收/默认配置 Stage）一行带过；仅非默认决策标 💡 + 展开理由 cite 关键信号
  - 双对齐姿态：从 5 选 1 编号菜单退化回"ok / 自由反馈"二选一（PMO 解析反馈类型，不让用户先选编号）

- **本修补删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 triage 执行报告模板的"段顺序固定"硬约束（KNOWLEDGE → ADR → 角色 → 流程类型 → 跨项目 → 环境配置 → 骨架 → 决策点 9 段平铺）
  - 删"角色可用性扫描"段独立输出（折到 Tier 3，仅异常时一行）
  - 删"流程类型识别"独立段（流程类型直接体现在 Feature 骨架顶部）
  - 删"环境配置预检 4 维度表"主对话渲染（worktree mode/path/sub_project/artifact_root 等机读字段，folded to state.json + 仅异常一行说明）
  - 删"无 ADR" / "无变更归属" 等空段输出（不命中就不输出）
  - 删 P0-38-B 的 3 选 1 启动确认菜单 + P0-49 一度退化的 5 选 1 菜单（合并为 ok / 自由反馈二选一）

- **加 1 删 1 论证**（P0-48 元规则要求）：
  - **加**：Tier 1/2/3 输出层次规范 + 反模式硬约束 + 骨架默认推荐折叠规范 + 双对齐二选一姿态规范
  - **删**：原 9 段平铺执行报告模板（履职报告体感的根源） + 5 选 1 编号菜单 + 环境配置 4 维度复述表
  - 净加规则数：±0（加输出层次规范 = 删履职模板平铺；加反模式禁令 = 删 5 选 1 菜单），符合 加 1 删 1

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则）：
  - 如果用户在双对齐反馈时困惑"该回什么"——说明二选一姿态指引不够，可考虑加 3-4 个反馈范例帮助用户（不是回到 5 选 1 菜单）
  - 如果 Tier 2 折叠区漏了重要信号导致下游决策错——说明折叠条件太松，应加更细的"关键信号必须 Tier 1"判定（不是回到全 Tier 1 平铺）
  - 如果用户经常说"骨架某 Stage 不对"——说明骨架默认推荐 vs 非默认决策的判定不准，应改进推荐表（不是回到全展开理由）

- 风险控制：
  - Tier 2 折叠区"详情可查 state.json" → 用户跨 turn 续作时如果需要重新看 KNOWLEDGE 命中详情，可让 PMO 重读 state.json + 渲染（按需 ad-hoc，不加回主对话默认输出）
  - 双对齐二选一不是"取消选项"，是"取消编号菜单"——用户仍可自由反馈具体调整，PMO 仍可解析路径
  - 不影响 P0-49 主体设计（意图段 schema / 双对齐双对齐含义 / Plan Stage 子步骤 1 改造），仅影响输出形态
  - 红线数保持 15 条
  - 自我应用 P0-48 C 段元规则（删了什么段 + 加 1 删 1 + 重新触发标尺）

- 影响面：
  - 改动文件：2 个（stages/triage-stage.md 执行报告模板重写 + docs/CHANGELOG.md 修补段）
  - 不 bump 版本号（修补在 P0-49 内）
  - 用户体验：triage 输出从 9 段履职报告 → ~3 段决策呈现（Tier 1）+ 命中/异常时折叠摘要 → 信息密度提升 ~3 倍，认知负担降低

### P0-49：triage 意图理解段 + 双对齐暂停（全程 7 轮对话收敛）

- 触发：用户问"接收+理解输出的是 PRD 么"+ 7 轮挑战收敛（PRD 背景 → 意图卡 → INTENT.md → state.json.intent → PRD v0/v1 → 上下文驱动）
- 设计哲学：把"接收+理解"的意图职责从隐式（散落 Plan Stage PRD 起草中）显式化（triage 主对话渲染 + 用户双对齐）；意图 freeze 在 triage 上下文，下一阶段首次产出时自然继承到人读资产，零中转零冗余
- 处理（4 处改造）：
  - **P0-49-1. `stages/triage-stage.md` Step 8 加意图段渲染规范**：按流程类型分 schema（Feature/敏捷需求/Planning Why now+Assumptions+Real unknowns / Bug 症状+复现+影响+期望 / 问题排查 症状+已知+目标 / Micro 一句变更描述）；意图段输出硬规则（不落盘 + 下一阶段继承 + schema 不跨流程混用 + PMO 不替用户决策）
  - **P0-49-2. `stages/triage-stage.md` Step 8 暂停点改双对齐**：从 3 选 1（采用骨架 / 调整骨架 / 其他）改为「意图 + 流程一次确认」（回 ok = 全部采纳推荐 / 回数字 = 单点调整 / 回反馈 = 自由文本 / 回切流程 = 切换流程类型）；禁止"双对齐拆两次单对齐"反模式
  - **P0-49-3. `stages/plan-stage.md` 子步骤 1 改造**：PRD 背景段从 triage 上下文意图直接继承（Why now/Assumptions/Real unknowns 直接抄 + 用户已拍板的 unknown 标"已决"），不重新跟用户对齐意图、不写 PRD v0/v1 中间状态。子步骤 1 退化为单次产出（不拆 v0/v1 + 不弹中间暂停）
  - **P0-49-4. `roles/pmo.md` 调度责任段更新**：(a) Plan Stage 调度责任段加"意图段继承"职责说明；(b) 产品决策边界段 triage 决策范围加"意图理解段"作为 PMO 在 triage 的合法决策项

- **本 patch 删了什么**（自我应用 P0-48 C 段元规则）：
  - 删 plan-stage.md 子步骤 1 隐式职责"PM 起草前先做意图理解"（已转移到 triage）
  - 删 plan-stage.md 子步骤 1 隐式工作量"PRD 背景段从 0 起草"（背景段从 triage 继承）
  - 删 triage-stage.md Step 8 暂停点 3 选 1"采用 / 调整 / 其他"格式（合并为双对齐 ok / 数字 / 反馈 / 切流程）
  - 弃用 P0-49 讨论过程中提出的"INTENT.md 独立文件"方案（最终方案不需要新增 artifact）
  - 弃用 P0-49 讨论过程中提出的"state.json.intent 字段中转"方案（最终方案上下文驱动）
  - 弃用 P0-49 讨论过程中提出的"PRD v0 / v1 状态机 + 中间用户对齐暂停"方案（最终方案 PRD 不分版本）

- **加 1 删 1 论证**（P0-48 元规则要求）：
  - **加**：triage Step 8 意图段渲染（新职责）+ Step 8 双对齐暂停（替换 3 选 1）
  - **删**：plan-stage.md 子步骤 1 PRD 背景"从 0 起草"工作量 + 子步骤 1 隐式意图理解责任（与新加的 triage 意图职责正交平衡）
  - 净加规则数：±0（triage 加 = plan-stage 减），符合 加 1 删 1 原则

- **重新触发回来的 case 标尺**（P0-48 C-3 元规则要求）：
  - 如果意图段在 triage 渲染但用户经常 "意图不对，重做"——说明 PMO 草拟意图能力不够，应优化草拟规范（不是回去把意图理解推迟到 PRD 起草中）
  - 如果 PRD 背景段在评审中频繁被推翻 → 说明 triage 意图对齐流于形式（用户"双对齐"时没真看），应加强双对齐前的意图段呈现质量
  - 如果跨流程意图段 schema 难以维护 → 考虑收敛 schema（不是放弃按流程分形态，因为不同流程的"理解什么"本质不同）

- 风险控制：
  - 意图段不落盘 → 跨 session 续作时如果意图段还没落到对应资产（即 triage 完成但下一阶段第一次产出未发生），上下文丢失风险 → 文档约定"triage → 下一阶段首次产出 commit 在同一会话完成"作为软约束，不强制
  - PRD v0/v1 中间方案弃用 → 用户在 triage 双对齐时如果意图理解错过得不严，到 PRD 起草完成才发现意图错 → 仍需返工。但这种返工成本 ≈ 当前每次 PRD 写完才发现意图错的成本，没变重，只是把"意图发现错的时机"前置了
  - 红线数保持 15 条
  - 自我应用 P0-48 C 段元规则（CHANGELOG 含"删了什么"段 + 加 1 删 1 论证 + 重新触发标尺）

- 影响面：
  - 改动文件：4 个（triage-stage.md / plan-stage.md / roles/pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - 行数变化：triage-stage.md +~80 行（意图段 schema + 双对齐改造）/ plan-stage.md +~30 行（子步骤 1 意图继承段）/ roles/pmo.md +~10 行（triage 决策范围 + Plan 调度责任补充）
  - 用户体验：triage 暂停点信息密度大增（从"流程对齐"扩展为"意图 + 流程一次拍板"），决策疲劳不增（仍是一个暂停点）；Plan Stage 子步骤 1 PM 起草耗时降一半（背景段从 triage 继承不重新起）；意图错误的发现时机从"PRD 评审末"前置到"triage 双对齐时"，沉没成本陷阱降级

- 待跟进（非 P0-49 范围）：
  - Bug / 问题排查 / Feature Planning 流程的意图段 schema 还需在对应 Stage 入口（Bug 流程 RD 起草 BUG-REPORT.md / 问题排查 RD 介入 / Feature Planning PL 写产物）补"从上下文继承"的承接段（与 Plan Stage 子步骤 1 类似），下个 P0 patch 处理
  - 1-2 个真实 Feature 跑完后回顾"双对齐"是否真消除了意图层后期返工，意图段 schema 是否够用

---

## v7.3.10 + P0-48

> v7.3.10+P0-48 减负专版：v7.0 → v7.3.10+P0-47 累积约 50 个 P0 patch 几乎全是 reactive 加规则（每次解决一个用户痛点 → 加一条防御），没有任何版本专门做减法。用户反馈"框架越来越重"，本 patch 作为**第一次主动减负**：(A) 主对话输出红线 3 条治"行为漂移" (B) 静态减量 5 处治"双源/三源/重复" (C) P0 patch 设计契约元规则防"未来再次走回头路"。详见下方"加 1 删 1 元规则"。

### P0-48：减负专版（A 主对话输出红线 + B 静态减量 + C 元规则）

- 触发：用户反馈"teamwork 跑得越来越重了"+ 两个 case（PRD/TC section 完成度 ✅ 表 / state.json 配置回显表 / 工程性切片暂停 / 默认通道下 3 选 1 菜单）+ 用户拍板「A+B+C 全做」
- 设计哲学：从 reactive defense（每次抱怨加一条规则）转向 deletion sprint（找冗余 + 删 + 合并 + 单源化）。规模可控；复杂度档位（D 段）拆 P0-49 后续做
- 处理（9 处改造）：

  **A. 主对话输出红线 3 条**（治行为漂移；用户精选 3 项落地）：
  - **A-1. 禁止「✅ section 完成度一览表」**：plan/blueprint/review-stage.md 各加红线段。原因：段位齐全是隐含合同（PMO 校验不通过不会进 review）；列 ✅ 表 = 噪音
  - **A-2. 禁止「state.json 配置以表格人读复述」**：state.json 是机读真相源；主对话只述「已写入 X」+ 1-2 句关键决策点
  - **A-3. 禁止「让用户预览/避免重写」类工程性切片暂停**：违反 P0-45 反转语义；评审本身就是发现偏离的机制
  - 判定标尺（如何重新触发回来）：每条都给"如果出现 case Y 才考虑加回"标尺，作为后续验证

  **B. 静态减量 5 处**（治双源/重复）：
  - **B-1. 三 Stage 入口实例化合并**：原 plan-stage.md L154-266 (113行) + blueprint-stage.md L12-43 + review-stage.md L89-125 三处入口实例化 ~180 行重复 → 抽取到新建 `standards/stage-instantiation.md` (~146行) 单一权威源；三 Stage 入口段精简为 ~15 行引用
  - **B-2. Micro 身份切换规范单源化**：roles/pmo.md L5 长行复述删除 → 改为引用 SKILL.md 单源；同时把 P0-20-B 反漂移补丁（第一人称锚点 + 追加改动回退规则）补齐到 SKILL.md（之前 SKILL.md 缺这两条，导致 pmo.md 多复述了）
  - **B-3. ok = 按 💡 建议 约定双源化**：roles/pmo.md L21-32 复述（12 行）→ 改为引用 RULES.md L250-260 单源
  - **B-4. 评审组合推荐表权威源标注**：plan-stage.md § Plan Stage 评审组合智能推荐表 标 🔴 唯一权威源；roles/pmo.md L711-776 (Stage 入口偏差判定 + 输出格式 ~65行) 删除 → 改为引用 standards/stage-instantiation.md
  - **B-5. 删 business_direction_locked_at frontmatter 字段**：templates/prd.md + templates/feature-state.json + stages/plan-stage.md 同步。原因：P0-44 改为讨论模式后此字段无人填，时刻信息由 state.json 顶层 updated_at 单一记录
  - 红线合并：#2+#6+#7 合并为单条「流程类型规范」（用 sub-rule (a)(b)(c) 表达）；#11+#13 合并为单条「写操作硬门禁链」(a) 流程入口门禁 + (b) Subagent dispatch 门禁。15 编号保留（#6/#7/#13 改为 "见 #X" 引用，外部引用零破坏）。SKILL.md + init-stage.md 同步

  **C. P0 patch 设计契约元规则**（防未来累积膨胀）：
  - **C-1. 加 1 删 1 原则**：SKILL.md 红线段后新增「P0 patch 设计契约」段。新加 checklist 项 / frontmatter 字段 / 红线 / 决策菜单 / 暂停点 → 必须同 patch 删/合并一项老规则；找不到可删可合并项时必须 CHANGELOG 写"为什么必须新加且无法换合并"的论证
  - **C-2. 删了什么段落**：每个 P0 patch CHANGELOG 必须含「删了什么」段落。即使该 patch 主要是新增也要主动列出删/合并/单源化的内容；纯加新规则的 patch 不予合入
  - **C-3. 验证标尺**：每条新加规则必须配"如果它有用，会通过什么 case 重新触发回来"作为后续验证标尺
  - 例外白名单：bug 修 / 错别字 / 链接失效 / 用户明确要求 / 新角色或新 Stage（结构性扩展）

- **本 patch 删了什么**（自我应用 C-2 规则）：
  - 删 plan-stage.md L154-266 入口实例化重复段（114 行）→ 抽到 standards/stage-instantiation.md
  - 删 blueprint-stage.md L12-43 入口实例化重复段（32 行）→ 引用化
  - 删 review-stage.md L89-125 入口实例化重复段（37 行）→ 引用化
  - 删 roles/pmo.md L5 Micro 身份切换长行复述（约 25 行）→ 引用 SKILL.md
  - 删 roles/pmo.md L21-32 ok = 按建议约定复述（约 14 行）→ 引用 RULES.md
  - 删 roles/pmo.md L711-776 Stage 入口偏差判定段（约 65 行）→ 引用 standards/stage-instantiation.md
  - 删 templates/prd.md frontmatter `business_direction_locked_at` 字段
  - 删 templates/feature-state.json `business_direction_locked_at` 字段
  - 合并 SKILL.md 红线 #2+#6+#7（#6/#7 改为引用 #2）
  - 合并 SKILL.md 红线 #11+#13（#13 改为引用 #11）
  - 合并 init-stage.md 红线对应同步

- 风险控制：
  - 入口实例化合并 → 三 Stage 行为不变（standards/stage-instantiation.md 是无损抽取，红线全保留）
  - 红线 15 编号保留 + 外部引用零破坏（#6/#7/#13 仍存在但内容变 "见 #X"）
  - business_direction_locked_at 删字段 → 老 PRD 兼容（PMO 读取时该字段视为可选信息字段，不驱动决策）
  - 主对话红线段对历史 case 不追溯，仅约束未来主对话输出
  - C 段元规则不立即应用到本 patch（自我应用见上方"本 patch 删了什么"段，已自洽）

- 影响面：
  - 改动文件：~10 个（SKILL.md + init-stage.md + 3 Stage spec + roles/pmo.md + templates/prd.md + templates/feature-state.json + 新建 standards/stage-instantiation.md + CHANGELOG.md）
  - 行数变化：plan-stage.md 919→844 (-75) / blueprint-stage.md 382→376 (-6) / review-stage.md 761→754 (-7) / roles/pmo.md 2185→2119 (-66) / 新建 standards/stage-instantiation.md +146 / 三 Stage 加主对话红线段 +~50 行
  - 净行数变化：约持平（删 ~155 行，加 ~196 行新内容含主对话红线段 + 抽取的统一规范）
  - DRY 收益：三 Stage 入口实例化 + Micro 身份切换 + ok 约定 + Stage 入口偏差判定 单源化 → 维护成本大幅下降，漂移风险消除
  - 用户体验：主对话输出更紧凑（不再有 ✅ 表 / 复述表 / 工程性切片暂停 / 默认通道下 3 选 1 菜单 padding）

- 待跟进（非 P0-48 范围）：
  - **P0-49 复杂度档位**（D 段，已拆出）：triage 加 trivial / standard / complex 三档替代 Micro / Feature 二档（state.json schema 变更 + triage 重写 + 各 Stage 入口加档位识别）。结构性变更，单独做更安全
  - 1-2 个真实 Feature 跑下来后回顾"主对话红线"是否真消除了 padding 行为
  - 如果发现 padding 仍然出现 → 不是规则不够，是模型行为偏置——可考虑在 plan-stage.md 加正面示例（"应该这样输出"）

---

## v7.3.10 + P0-47

> v7.3.10+P0-47 PRD 模板合并：原 templates/prd.md 含两套模板（"PRD.md（标准模板）"业务类 + "PRD.md（技术类变体）"纯技术 refactor），P0-46 后两套差异已小（技术方案要点已移到 TECH.md）。本次合并为统一通用模板，差异通过"按需必填"标注表达（业务类必填 / 纯技术 refactor 可省）。删除 prd_variant frontmatter 字段（合并后不需要变体区分）。

### P0-47：PRD 模板合并（删技术类变体 + 加按需必填）

- 触发：用户「目前 prd 有两套，是否可以合成一套不区分产品和技术。只用 PRD.md（标准模板）」+「确认」
- 设计决策（用户拍板）：
  - **合并为统一通用模板**：保留"PRD.md（标准模板）"作为主体，删除"PRD.md（技术类变体）"段
  - **按需必填标注**：用户故事 / 功能需求 / 埋点需求 标记"业务类必填；纯技术 refactor 可省"
  - **删除 prd_variant frontmatter 字段**：合并后不需要变体区分
  - 红线数保持 15 条
- 处理（4 处改造）：
  - **P0-47-1. `templates/prd.md` 合并**：用 sed 删除 L143-232（"PRD.md（技术类变体）"整段，90 行）；标准模板加 v7.3.10+P0-47 重构说明 + 按需必填标注（用户故事 / 功能需求 / 埋点需求 3 处）
  - **P0-47-2. `stages/plan-stage.md` Feature 类型识别表**：删 prd_variant 列；加 P0-47 说明（识别用其他信号综合判断）
  - **P0-47-3. `TEMPLATES.md` 索引**：prd.md 描述改为"统一通用模板，含按需必填标注"
  - **P0-47-4. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-46 → 7.3.10+P0-47
- 风险控制：
  - 老 PRD（已含 prd_variant 字段）兼容：PMO 读取时 prd_variant 字段视为信息字段，不驱动模板选择
  - 按需必填标注清晰（🟡 + 业务类 / 纯技术 refactor 区分）
  - 不破坏 PRD-REVIEW.md schema（独立段，未受影响）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：4 个（prd.md / plan-stage.md / TEMPLATES.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - prd.md 行数：404 → 322（减 82 行 / 减 20%；删 90 行 + 加重构说明与按需必填标注约 8 行）
  - 用户体验：
    - PRD 模板从两套 → 一套，PMO 起草时不再判断"用哪个变体"
    - 按需必填标注让纯技术 refactor 也能用统一模板（标注"不适用"）
    - 配合 P0-46 PRD 边界归位，PRD 整体更聚焦核心 AC list
- 待跟进（非 P0-47 范围）：
  - 1-2 个真实纯技术 refactor Feature 跑下来后回顾按需必填标注是否清晰

---

## v7.3.10 + P0-46

> v7.3.10+P0-46 PRD 边界归位 + 职责正交回归：用户反思 P0-44 设计——把 RD/QA/Designer 视角的关注点（接口 schema / 测试用例规划 / 数据模型 / 视觉风格等）塞到 PM 起草规范是越界，违反 teamwork 框架原本的"Plan / Blueprint / Test"三阶段职责正交。导致 PRD 越界 + AC list 被技术细节淹没 + TECH/TC 被掏空 + Plan Stage 评审角色发不该发的 finding（如 RD 在 Plan Stage 提"接口 schema 不完整"）。本次修正：(1) PRD 仅回答"做什么 + 为什么"（产品/AC 视角），技术细节移到 TECH.md（Blueprint Stage RD 写），测试细节移到 TC.md（Blueprint Stage QA 写）；(2) Plan Stage 联合评审 review_scope=prd，仅审产品视角（业务可行性 / AC 可测试性 / 用户故事完整性）；(3) Blueprint Stage 加 TECH 起草规范 + TC 起草规范段，让技术/测试细节在正确的位置内化；(4) PRD-REVIEW.md frontmatter 加 review_scope 字段，machine-verifiable 评审范围。

### P0-46：PRD 边界归位 + 职责正交回归

- 触发：用户「prd 评审是否过重，是否掺杂了一些技术和测试的细节。是不是 prd 重点关注产品目标和 ac list 更合适，其他的细节放到技术方案里」+「按这个修复」
- 设计决策（用户拍板）：
  - **职责正交回归**：PRD（做什么 + 为什么）/ TECH（怎么做）/ TC（怎么测）三阶段职责清晰
  - **PRD 起草规范精简**：删 RD 视角必填项 6 条 + QA 视角必填项 6 条 + UI 视觉风格约束（移到对应 Stage）
  - **Plan Stage 评审 scope=prd**：RD/QA/Designer 评审 PRD 时仅审产品视角，不审技术/测试实现
  - **Blueprint Stage 加 TECH/TC 起草规范**：技术/测试细节在 RD/QA 起草自己的产物时内化（不在 PM 起草 PRD 时）
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **P0-46-1. `stages/plan-stage.md` PM 起草规范精简**：
    - 删 RD 视角必填项（接口 schema / 数据模型 / migration / 调用链路 / 异常处理实现 / 性能 / 复用模式）
    - 删 QA 视角必填项（测试用例规划 6 条）
    - 删 UI 视觉风格约束维度
    - 保留通用 checklist（产品目标 / AC / 影响范围 / 业务风险 / KNOWLEDGE 关联）
    - 保留 UI 用户故事维度（高层产品视角，requires_ui=true 时填）
    - 加 "PRD 不写什么"边界段（10 条具体禁止项）
    - 加 "PMO dispatch 评审角色时明确 review_scope=prd"约束
    - 加各角色（RD/QA/Designer）评审 PRD 时的 scope 关注点（产品视角 ✅ / 技术-测试-视觉细节 ❌）
  - **P0-46-2. `stages/blueprint-stage.md` 加 TECH/TC 起草规范**：
    - QA 编写 TC 段加 v7.3.10+P0-46 TC 起草规范 checklist（AC×TC 矩阵 / 边界 / 异常 / 集成 / 性能 / ROLLBACK）
    - RD 编写 TECH 段加 v7.3.10+P0-46 TECH 起草规范 checklist（接口 schema / 数据模型 / 调用链路 / 异常处理实现 / 性能实现 / 复用模式）
  - **P0-46-3. `templates/prd.md` schema 加 review_scope 字段**：
    - PRD-REVIEW.md frontmatter reviews[] 加 review_scope 字段（值：prd / blueprint / code-review）
    - PRD 评审 review_scope=prd（强制约束）
  - **P0-46-4. `roles/pmo.md` 调度责任段加 review_scope=prd 约束**：
    - PMO dispatch 子步骤 3 评审角色时必须 cite「按 plan-stage.md § 子步骤 3 评审 scope = PRD 范围」
    - 评审角色 finding 越界（如 RD 提"接口 schema 不完整"）→ PMO 拦截 + 标记越界 + 不计入有效 finding
  - **P0-46-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-45 → 7.3.10+P0-46
- 风险控制：
  - 不破坏 P0-44 的"PM 起草规范"框架，仅精简内容范围
  - PRD 仍保留必要的产品/AC 视角覆盖（不是完全 free-form）
  - TECH/TC 起草规范从 PM 移到 RD/QA 自己的起草段（位置正确）
  - 用户主动越界（如硬要 RD 在 Plan 评审时提技术细节）→ PMO 拦截 + 提示移到 Blueprint Stage
  - 红线数保持 15 条
- 影响面：
  - 改动文件：5 个（plan-stage.md / blueprint-stage.md / prd.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - PRD 长度：典型 PRD 减 30-50%（删除技术/测试细节段）
  - TECH/TC 长度：增加（吸收原 PRD 的技术/测试细节）
  - Plan Stage 评审 finding 减少（RD/QA 不再越界提技术/测试细节）
  - Blueprint Stage 评审 finding 增加（技术/测试细节在正确位置评审）
  - 用户体验：
    - PRD 更聚焦核心 AC list（读 PRD 的人快速找到核心业务行为）
    - TECH/TC 更完整（不再被 PRD 掏空）
    - Plan Stage 评审更快（RD/QA scope 更窄）
    - Blueprint Stage 评审更深（技术/测试细节在正确位置）
- 待跟进（非 P0-46 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 PRD 瘦身效果（AC list 是否清晰 / 技术细节是否真移到 TECH）
  - 评审越界拦截规则（如何让 PMO 准确识别 finding 是否越界）

---

## v7.3.10 + P0-45

> v7.3.10+P0-45 Stage 入口实例化默认通道反转（P0-42 快速通道扩展为默认）：用户实战 case 暴露 P0-38-A 设计的"Stage 入口实例化用户瞬时确认"暂停点信息量低——triage 骨架已是用户拍板权威，PMO 实例化决策大多数情况轻微偏差或完全采纳 hint，5 选 1 暂停点在实战中决策疲劳 > 价值。P0-42 加快速通道（hint 完全采纳跳过）但门槛太高（需满足 4 条件 ALL）。本次反转为默认：**默认通道无暂停点**（PMO 直接 cite hint + 写 *_substeps_config + 进入 Stage 内部），**仅严重偏差时触发标准通道**（⏸️ 5 选 1 暂停点）。"严重偏差"判定矩阵（角色组合变更 / execution 整体反转 / Stage 跳过 / external 启用反转 / hint 缺失 / triage 选项 2-3）。用户主动打断仍可触发标准通道（输入"调整骨架"等）。适用 Plan / Blueprint / Review 三个 Stage。

### P0-45：Stage 入口实例化默认通道反转

- 触发：用户「各个阶段 Dev Stage 入口实例化用户瞬时确认，这个只有推荐和 triage 有严重偏差时在确认」+「1」（启动 P0-45）
- 设计决策（用户拍板）：
  - **默认通道无暂停**（轻微偏差或完全采纳 → PMO 直接进入 Stage 内部）
  - **严重偏差才出暂停**（角色组合变更 / execution 整体反转 / Stage 跳过 / external 启用反转 / hint 缺失 / triage 选项 2-3）
  - **用户主动打断仍可触发标准通道**（输入"调整骨架"等）
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **P0-45-1. `stages/plan-stage.md` 默认通道反转**：原"快速通道"改为默认；原"标准通道"仅严重偏差时触发；硬约束段重写
  - **P0-45-2. `stages/blueprint-stage.md` 同步**：入口实例化加默认通道判定段
  - **P0-45-3. `stages/review-stage.md` 同步**：入口实例化加默认通道判定段
  - **P0-45-4. `roles/pmo.md` 加「Stage 入口偏差判定」段**：严重偏差判定矩阵（6 个维度 × 轻微/严重对照）+ PMO 自我评估输出格式（默认通道 / 标准通道）
  - **P0-45-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-44 → 7.3.10+P0-45
- 风险控制：
  - 用户主动打断保留（默认通道下输入调整意图立即回退到 5 选 1）
  - 严重偏差判定矩阵硬规则（不允许 PMO 自我评估随意宽松）
  - hint 缺失时强制走标准通道（兜底）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：5 个（plan-stage.md / blueprint-stage.md / review-stage.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - 用户体验：每个 Feature 减 3 个暂停点（Plan / Blueprint / Review 入口默认无暂停）+ 严重偏差时仍出暂停（保留控制权）
  - 决策疲劳：典型 Feature 暂停点从 ~5 个 → ~2 个（仅子步骤 5 用户最终确认 + Ship 暂停）
- 待跟进（非 P0-45 范围）：
  - 1-2 个真实 Feature 跑下来后回顾"严重偏差"判定准确度（PMO 自我评估是否过宽 / 过严）
  - 是否需要扩展到其他 Stage（Test / Browser E2E / PM 验收 / Ship）的入口暂停点

---

## v7.3.10 + P0-44

> v7.3.10+P0-44 Plan Stage 性能重构：用户实战 case 暴露 Plan Stage 耗时偏长（典型 60-200 min）。瓶颈分析：(1) 多角色并行评审 dispatch 数大（PL/RD/QA/Designer/PMO/external 6 角色）；(2) RD/QA finding 90% 是通用关注点（边界场景/接口设计/测试可行性），事后评审才发现 → 多轮循环；(3) PL 评审作为独立 finding（P0-34）失去了多轮对话的对抗深度（v7.3.x 实战验证好用）；(4) 每个角色独立 subagent 冷启动税大。本次重构核心：把"事后多角色独立评审"前置为"事前 PM 起草规范" + "PL-PM 业务讨论恢复" + "QA+RD+Designer(可选) 主对话联合评审 ∥ external 后台并行"。预估典型 Feature 耗时减半（小 Feature 40-60 min → 15-25 min；中 Feature 60-90 min → 25-40 min）。

### P0-44：Plan Stage 性能重构（PM 起草规范 + PL-PM 讨论恢复 + 主对话联合评审 + external 并行）

- 触发：用户「plan stage 耗时太久，是否有优化的可能」+ 多轮迭代讨论后拍板「PM 起草规范增加，PL PM 讨论完成后，RD+QA 视角组合评审在主对话，并行外部模型评审」+「应该是 QA+RD+designer (可选) 联合评审」+「ok」
- 设计决策（用户拍板）：
  - **核心原则**：90% 通用关注点事前内化（PM 起草规范）+ PL-PM 真对抗（讨论模式）+ 10% 领域 finding 事后评审（主对话联合）+ 异质视角保留（external 后台并行）
  - **Plan Stage 5 子步骤重构**：
    - 子步骤 1：PM 按规范起草 PRD（含通用 + RD/QA + UI 影响 + 子项目技术栈 checklist）
    - 子步骤 2：PL-PM 讨论（v7.3.x 模式恢复，业务方向锁死保留 P0-34-C）
    - 子步骤 3：QA+RD+Designer(可选) 主对话联合评审 ∥ external 后台 shell 并行
    - 子步骤 4：PM 回应 + 修订 PRD（保留 P0-34-A/B 对抗自查 + DEFER 收紧）
    - 子步骤 5：⏸️ 用户最终确认 PRD（核心暂停点，理想路径下唯一暂停点）
  - **Designer 触发双保险**：PRD frontmatter `requires_ui: true` 或 UI 关键词命中
  - **discuss/PL-FEEDBACK + PM-RESPONSE 文件契约恢复**（撤销 P0-43 废止）
  - **PRD-REVIEW.md schema 调整**：reviews[] 仅含 qa / rd / designer? / external?（删 pl/pmo）
  - 红线数保持 15 条
- 处理（7 处改造）：
  - **P0-44-1/2/3/4. `stages/plan-stage.md` 5 子步骤序列重写**：删 P0-34/P0-43 的 200 行（含原阶段 2a/2b 多角色独立评审），写入新的 200 行（PM 起草规范 checklist + PL-PM v7.3.x 讨论 + 主对话身份切换 QA→RD→Designer + external 后台并行 + PM 回应 + 用户确认 + 过程硬规则 + 多视角独立性）
  - **P0-44-5. `templates/prd.md` schema 调整**：PRD frontmatter 加 `requires_ui` 字段；PRD-REVIEW.md frontmatter `reviews[].role` 枚举从 `pl|rd|designer|qa|pmo` 改为 `qa|rd|designer|external`（删 pl 和 pmo）
  - **P0-44-6. `roles/pmo.md` 调度责任段重写**：v7.3.10+P0-44 重构 6 段调度职责（PM 起草前提醒 / PL-PM 讨论调度 / 主对话身份切换 / 子步骤 4 校验 / 快速通道判定 / 入口实例化硬约束）
  - **P0-44-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-43 → 7.3.10+P0-44
- 风险控制：
  - PM 起草规范 checklist 覆盖 90% RD/QA 通用关注点（事前内化）
  - 子步骤 3 主对话身份切换保留 RD/QA/Designer 真 finding 能力（剩余 10% 领域 finding）
  - external 后台 shell 并行保留异质视角对抗深度
  - PL-PM v7.3.x 讨论模式实战已验证（用户原话"之前 PL PM 讨论效果很好"）
  - 保留 P0-34-A/B（DEFER 收紧 + 对抗自查）+ P0-34-C（业务方向锁死）+ P0-38（external 角色）+ P0-42（快速通道）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：4 个（plan-stage.md 主体 / prd.md schema / pmo.md 调度责任 / SKILL.md / init-stage.md / CHANGELOG.md）
  - plan-stage.md 子步骤序列：原 200 行重写为新 200 行（结构完全变）
  - PRD-REVIEW.md schema：reviews[] 角色从 5 类减到 4 类（删 pl/pmo）
  - discuss/PL-FEEDBACK / PM-RESPONSE：从 P0-43 废止恢复为 v7.3.x 必需契约
  - 用户体验：
    - Plan Stage 耗时减半（典型 Feature 40-60 min → 15-25 min）
    - 子步骤 3 主对话内 QA→RD→Designer 顺序切换（不再 dispatch 多个 subagent）
    - external 后台并行（不阻塞主对话）
    - 理想路径下仅 1 个暂停点（子步骤 5 用户最终确认）
- 预估收益（vs P0-34/P0-43）：
  - 小 Feature 1 轮通过（无 UI）：40-60 min → 15-25 min（减 60%）
  - 中 Feature 1 轮通过（无 UI）：60-90 min → 25-40 min（减 55%）
  - 含 UI 中 Feature：70-100 min → 30-50 min（减 50%）
  - 大 Feature 2 轮通过：120-150 min → 55-85 min（减 45%）
- 待跟进（非 P0-44 范围）：
  - 1-2 个真实 Feature 跑下来后回顾耗时实测（PM 起草规范覆盖度 + 主对话身份切换可行性 + external 后台并行实施）
  - 类似的 Stage 性能优化（Blueprint Stage / Review Stage 是否需要类似重构）

---

## v7.3.10 + P0-43

> v7.3.10+P0-43 智能推荐表迁移到 plan-stage.md（Stage 优先原则）+ 清理 P0-34 残留旧契约：实战 case 暴露用户对架构的洞察——「Plan Stage 评审组合智能推荐表」原写在 roles/pmo.md（v7.3.10+P0-34-1 加入），但这套规则的本质是 "Plan Stage 入口怎么决策 review_roles + execution"，是 Plan Stage 契约的内部规范，应该由 stages/plan-stage.md 作为权威源（不是 PMO 角色规范）。把 Stage 决策规则放在 PMO 角色文件违反了 teamwork 框架的"Stage 优先"原则。本次系统重构：(1) 把 130 行智能推荐表（Step 1 Feature 类型识别 / Step 2 评审角色推荐 / Step 3 执行方式推荐 / PL 优先权 / 评审循环 + 超 3 轮处理 / 硬规则）整体迁移到 stages/plan-stage.md，作为 Plan Stage 入口实例化的决策权威源；(2) roles/pmo.md 仅保留 30 行 PMO 调度责任概述 + 指向引用；(3) 顺便加"小 Feature 默认主对话"硬约束（≤5 文件 + 单子项目 + 无 UI → RD/PL 默认 main-conversation，针对实战 case INFRA-F019 的 RD subagent 偏离推荐表问题）；(4) 清理 plan-stage.md 残留 `discuss/PL-FEEDBACK-R{N}.md` / `PM-RESPONSE-R{N}.md` 旧契约（P0-34 重构 PL 升格评审角色后没清干净的尾巴），改为❌废止。

### P0-43：智能推荐表迁移 + discuss 旧契约清理

- 触发：用户「roles/pmo.md 不需要改，这写规范应该是 plan-stage.md 决定的」+「ok」（启动 P0-43）
- 设计决策（用户拍板）：
  - **Stage 优先原则**：Plan Stage 入口决策规则属于 Stage 契约，权威源在 stages/plan-stage.md（不在 roles/pmo.md）
  - **整体迁移**：130 行智能推荐表完整内容（不是 cite 引用）
  - **roles/pmo.md 留 PMO 调度责任概述**：4 段简短清单（triage 生成 hint / Stage 入口实例化 / 快速通道判定 / 硬约束 cite），指向 plan-stage.md
  - **新增"小 Feature 默认主对话"硬约束**：实战 case INFRA-F019 反例驱动（≤5 文件 + 单子项目 + 无 UI → RD/PL 默认 main-conversation）
  - **discuss/* 旧契约废止**：PRD-REVIEW.md frontmatter reviews[] 是统一权威源，禁止双重产出
  - 红线数保持 15 条
- 处理（3 处改造）：
  - **P0-43-1. 迁移智能推荐表 roles/pmo.md → stages/plan-stage.md**：
    - 在 plan-stage.md 入口实例化段后插入完整推荐表（Step 1-5 + PL 优先权 + 评审循环 + 硬规则 + 新增 P0-43 小 Feature 默认主对话硬约束）
    - 删 roles/pmo.md L675-807 完整智能推荐表段（用 sed 删 133 行）
    - 在 roles/pmo.md 加 30 行简短引用：「Plan Stage 评审组合智能推荐（v7.3.10+P0-43 迁移到 plan-stage.md）」+ PMO 调度责任 4 段
  - **P0-43-2. 清理 plan-stage.md discuss 旧契约**：
    - L600-601 `discuss/PL-FEEDBACK-R{N}.md` / `PM-RESPONSE-R{N}.md` 从「🔴 必需」改为「❌ v7.3.10+P0-43 废止」+ 说明（P0-34 PL 升格后 finding 应在 PRD-REVIEW.md frontmatter）
    - L761 文件树尾部 `discuss/PL-FEEDBACK-R{N}.md + PM-RESPONSE-R{N}.md` 删除 + 加废止说明
    - 保留 forbidden_files 列表对 discuss/ 的引用（外部模型独立性约束需禁读 discuss/，但本身不强制产出）
  - **P0-43-3. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-42 → 7.3.10+P0-43
- 风险控制：
  - 智能推荐表内容完整迁移（130 行 → 130 行）+ 简短引用（30 行），总行数减少
  - roles/pmo.md 仅留概述指向，不重复 stage spec 内容（DRY 原则）
  - discuss/PL-FEEDBACK / PM-RESPONSE 废止：旧 Feature 已存在的 discuss/* 不强制迁移（state.json 历史快照），新 Feature 强制不产出
  - 不增红线（红线数保持 15 条）
- 影响面：
  - 改动文件：3 个（roles/pmo.md / stages/plan-stage.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - roles/pmo.md 行数：2204 → 2071（删 133 行智能推荐表）+ 加 30 行引用 = 净减 ~100 行
  - stages/plan-stage.md：加 130 行智能推荐表 + 删 2 行 discuss 必需契约 + 加 P0-43 小 Feature 默认主对话硬约束
  - 架构正交性：Stage 决策规则归 Stage spec / PMO 角色规范不兼任 Stage 决策权威
  - 用户体验：
    - PMO 在 Plan Stage 决策时单一权威源（plan-stage.md），不再 pmo.md / plan-stage.md 双跑
    - 小 Feature 不再被 PMO 默认 subagent 化（实战 case INFRA-F019 反例修复）
    - 新 Feature 不再产 discuss/PL-FEEDBACK / PM-RESPONSE 双重产物
- 待跟进（非 P0-43 范围）：
  - 1-2 个真实 Feature 跑下来后回顾智能推荐表迁移效果（PMO 是否仍在 pmo.md 找推荐表）
  - 类似的 Stage 决策规则是否还有放错位置的（如 Blueprint Stage 评审组合 / Review Stage 三视角）

---

## v7.3.10 + P0-42

> v7.3.10+P0-42 triage 输出精简 + worktree 默认路径硬规则强化 + Plan Stage 入口快速通道：用户实战 case（INFRA-F019）暴露三个真实问题——(1) triage 输出 12 段（含「流程步骤描述」+「Feature 骨架」+「骨架摘要」三段重复信息）+ 越界提示（"BG-015 协调 ship"是 PM 验收的事却在 triage 抛出）= 决策疲劳；(2) Plan Stage 入口实例化的 5 选 1 暂停点信息量低——execution_hints 已说"启用 X/Y/Z 评审"，唯一新决策维度是 execution 方式，而 P0-34-C 推荐表已默认；(3) worktree 路径偏离 P0-39 默认（用了项目历史 .claude/worktrees/feature-... 而非 .worktree/...，且加了 feature- 前缀）。本次系统精简：(A) triage Output Contract 删「流程步骤描述」段（P0-26 残留）+ 删「骨架摘要」段（"预计耗时"加到骨架表尾）+ 环境配置预检表 8 行合并 4 行 + 禁止越界提示（"BG 协调 ship"等）；执行报告模板段顺序固定化；(B) Plan Stage 入口实例化加「快速通道」（hint 完全采纳时跳过 5 选 1 暂停点直接进 PRD 起草）+ 「标准通道」回退条件明确；(C) worktree 路径硬规则强化（禁止用项目历史路径 / 禁止加 feature- 前缀 / cite localconfig 字段或硬默认）。形成 triage 紧凑（8 段）+ Plan 入口可跳暂停点 + worktree 路径不再偏离的实战级闭环。

### P0-42：triage 输出精简 + Plan 入口快速通道 + worktree 路径硬规则

- 触发：用户实战 case（INFRA-F019 启动）+ 用户「triage 阶段输出的东西冗余，需要精简合并」+ 「为什么有 Plan Stage 入口实例化用户瞬时确认（5 选 1）」+「启动」（P0-42 实施）
- 设计决策（用户拍板）：
  - **triage 输出从 12 段精简为 8 段**：删冗余（流程步骤描述 / 骨架摘要）+ 合并（环境配置预检表 4 行）+ 禁止越界（BG 协调 ship 等）
  - **Plan Stage 入口加快速通道**：hint 完全采纳时跳过 5 选 1 暂停点（条件：triage 选 1 + hint 完整 + 完全采纳 + execution 默认）
  - **worktree 路径硬规则**：禁止用项目历史路径（如 .claude/worktrees/）+ 禁止加 feature- 前缀；唯一合法来源是 localconfig.worktree_root_path（缺失硬默认 .worktree）
  - **不增红线**：通过 Stage 契约 + 反例直接对照实战 case
- 处理（4 处改造）：
  - **P0-42-1. `stages/triage-stage.md` 输出精简**：
    - Step 7「流程步骤描述」段保留作锚点但实际输出合并到 Step 8 骨架（P0-26 残留删除）
    - 「骨架摘要」独立段删，"预计耗时"加到骨架表尾一行
    - 环境配置预检表从 8 行合并为 4 行（worktree / 路由 / 分支 / 工作区）
    - 执行报告模板加段顺序硬约束 + 禁止越界提示（BG 协调 ship / 耗时数据来源等）
  - **P0-42-2. `stages/plan-stage.md` worktree 路径硬规则强化**：
    - 禁止偏离 P0-39 默认路径（项目历史 / 团队约定 / "上次也是这么用的"等理由）
    - 禁止子目录加 feature- 前缀（worktree path 仅用 {Feature 全名}）
    - 唯一合法来源：localconfig.worktree_root_path 字段或硬默认 .worktree
    - 含实战反例（INFRA-F019 case 完整对照）
  - **P0-42-3. `stages/plan-stage.md` Plan Stage 入口快速通道**：
    - 快速通道条件 ALL（triage 选 1 / hint 完整 / 完全采纳 / execution 默认）
    - 满足全部 → 直接 cite hint + 写 plan_substeps_config + 进 PRD 起草，无暂停点
    - 标准通道回退条件（hint 不完整 / 偏离 / triage 选项 2-3 / Blueprint/Review 入口）
    - 用户在快速通道下仍可主动打断（输入"调整骨架"等）回退标准通道
  - **P0-42-4. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-41 → 7.3.10+P0-42
- 风险控制：
  - 不破坏 P0-38-A/B 骨架契约（仅简化 triage 输出和 Plan 入口暂停点）
  - 快速通道有明确触发条件 + 标准通道兜底（hint 不完整自动走标准通道）
  - 用户主动打断快速通道（输入"调整骨架"）立即回退
  - Blueprint/Review 入口仍走标准通道（上下文更复杂，需用户确认）
  - 不增红线（红线数保持 15 条）
- 影响面：
  - 改动文件：3 个（triage-stage.md / plan-stage.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - triage 输出段数：12 → 8（紧凑度提升 33%）
  - Plan Stage 入口暂停点：5 选 1 必出 → hint 完全采纳时跳过（决策疲劳显著降低）
  - worktree 路径合规性：禁止偏离 P0-39 默认 / 禁止 feature- 前缀
  - 用户体验：
    - triage 输出更聚焦（删了流程步骤描述 / 骨架摘要 / BG 越界等冗余段）
    - Plan Stage 启动更顺畅（典型场景跳过 5 选 1，hint 完全采纳直接进 PRD 起草）
    - worktree 路径不再偏离（实战 case 类问题不再发生）
- 待跟进（非 P0-42 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 triage 输出精简效果（用户决策疲劳实测）+ 快速通道命中率
  - Blueprint/Review 入口是否也需要快速通道（待积累实战数据后决策）

---

## v7.3.10 + P0-41

> v7.3.10+P0-41 sub_project 路由权威 + worktree 缺失硬默认 + 写操作前路径硬门禁：用户实战 case（F059-HomeShortcutKeySync）暴露 4 个关键流程漏洞——(1) sub_project=FE 写到 state.json 但产物文档落在根 `docs/features/` 而非 `app-frontend/docs/features/`（路由失效，AI 沿用历史根目录）；(2) localconfig 没配 worktree 时 AI 自降级 off，把"主工作区干净"简化为"可以直接写"，违反隔离原则；(3) 写操作前没有 pwd / 路径前缀硬校验，AI 钻空子；(4) teamwork_space.md 子项目清单表没有 docs_root 列，路由没有机器可读权威源。本次系统补漏：(A) teamwork-space.md 子项目表加 docs_root 列（路由权威）；(B) feature-state.json 加 artifact_root 字段（triage Step 9 写入）；(C) config.md 注释明确 worktree 缺失硬默认 auto + 禁止 AI 自降级；(D) triage Step 7.5/9 加硬规则（worktree fallback / artifact_root 计算 / state.json 写入清单加 artifact_root）；(E) RULES.md §六 加"写操作前路径硬门禁"段（pwd 校验 + 路径前缀校验 + 跨 Feature 写入禁止 + 实战反例）；(F) pmo.md 加"产物路径权威路由"段（路由计算流程 + 硬规则 + 历史兼容 + 校验时机 + 标准化拦截输出）。形成 triage 决策（写 state.json）+ 写操作前校验（pwd + 路径前缀）双层硬门禁。

### P0-41：sub_project 路由权威 + worktree 缺失硬默认 + 写操作前路径硬门禁

- 触发：用户实战 case（F059-HomeShortcutKeySync）AI 自我反思 +「为什么没按流程，需要优化 teamwork」+ 4 条建议（triage 出口校验 / worktree 缺失默认 auto / 写操作硬门禁 / teamwork_space 路由权威）
- 设计决策（用户拍板）：
  - **不增红线**：通过 Stage 契约 + RULES.md §六 写操作硬门禁扩展 + PMO 角色路由权威段达到约束效果（红线数保持 15 条）
  - **路由权威**：teamwork_space.md 子项目清单表 docs_root 列（必填），所有 Feature 产物路径必须以 `{docs_root}/{Feature 全名}` 开头
  - **worktree 缺失硬默认 auto**：禁止 AI 自降级 off（"主工作区干净"等不是 off 理由）
  - **写操作前硬门禁**：pwd + 路径前缀 + 跨 Feature 写入校验
  - **历史 Feature 兼容**：保留原位置不强制迁移（state.json.artifact_root 是历史快照），新 Feature 走新规则
- 处理（7 处改造）：
  - **P0-41-1. `templates/teamwork-space.md` 子项目清单表加 docs_root 列**（必填，路由权威）：表头加 docs_root；3 个示例行（AUTH/WEB/PAY）填入 `{子项目目录}/docs/features` 标准格式；含路由权威硬规则说明
  - **P0-41-2. `templates/feature-state.json` 加 artifact_root 字段**：顶层位置（与 feature_id / sub_project 同级）；含计算规则注释（teamwork_space.md docs_root 列 + Feature 全名）+ 写入时机（triage Step 9）+ 写操作硬门禁说明
  - **P0-41-3. `templates/config.md` worktree 缺失硬默认 auto 说明**：注释明确"localconfig 缺 worktree 字段 → PMO 必须按 auto 处理（不是 off）"+ 禁止 AI 自降级 + 实战反例
  - **P0-41-4. `stages/triage-stage.md` Step 7.5/8/9 加硬规则**：
    - Step 7.5 加 worktree 缺失硬默认 auto + artifact_root 计算逻辑
    - Step 8 暂停点输出表加 sub_project / artifact_root 两行
    - Step 9 state.json 写入硬清单加 artifact_root 字段
  - **P0-41-5. `RULES.md` §六 加「写操作前路径硬门禁」段**：3 项校验（pwd / 路径前缀 / 跨 Feature 写入禁止）+ 校验时机（Plan 入口 / 每次 Write 前 / Stage 切换）+ 实战反例（沿用根目录 / worktree=off 误用）
  - **P0-41-6. `roles/pmo.md` 加「产物路径权威路由」段**：路由计算流程（4 步）+ 硬规则（唯一权威 + 禁止反模式）+ 历史 Feature 兼容 + 校验时机 + 标准化拦截输出
  - **P0-41-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-40 → 7.3.10+P0-41
- 风险控制：
  - 历史 Feature 不强制迁移（state.json.artifact_root 是历史快照）
  - 单子项目模式（无 teamwork_space.md）兼容：artifact_root = `docs/features/{Feature 全名}`
  - 不增红线（红线数保持 15 条）
  - 不破坏现有 Stage 契约（仅加硬规则 + 路径校验）
  - 反例直接来自实战 case（提高 AI 识别力）
- 影响面：
  - 改动文件：7 个（teamwork-space.md / feature-state.json / config.md / triage-stage.md / RULES.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - state.json 字段：顶层加 `artifact_root`（必填）
  - teamwork_space.md schema：子项目清单表加 `docs_root` 列（必填）
  - 用户体验：
    - 多子项目模式产物路由透明（用户在 triage Step 8 看到 artifact_root + sub_project）
    - worktree 隔离不再被 AI 自降级
    - 写操作硬门禁防 AI 钻空子（pwd + 路径前缀双校验）
    - 实战 case 类问题不再发生（沿用根目录 / 主工作区写代码）
- 待跟进（非 P0-41 范围）：
  - 1-2 个真实多子项目 Feature 跑下来后回顾 artifact_root 路由的实测体验
  - 是否需要写一个 state.json 字段完整性校验脚本作为机器层兜底
  - 历史 Feature（在根 docs/features/）的批量迁移工具（暂不做，按需手工）

---

## v7.3.10 + P0-40

> v7.3.10+P0-40 RD 开发 + 架构师 Code Review 默认 Opus 模型：用户实战 case（BUG-F002-001 架构师 Code Review 用了 Sonnet 4.6 跑 2m 38s + 72.3k tokens）暴露当前模型默认值有问题——架构师 CR 是质量最后 gate，深度架构判断不可降级到 Sonnet。原 agents/README.md §一 模型偏好把"Review"统一标为 Sonnet 推荐，但这没区分"架构师 CR"（深度判断）和"QA CR"（执行型校验）。本次细化模型偏好原则："深度判断 = Opus / 执行验证 = Sonnet / 异质独立 = external"，明确：(1) RD 开发 / 架构师 CR / PM PRD / RD TECH / Designer UI = Opus 默认；(2) QA CR / QA TC / QA 测试 / Browser E2E / 多角色并行评审 / Bug 排查 = Sonnet 默认；(3) external (codex/claude CLI) 角色独立机制不变。dispatch 模板加场景化模型推荐注释。

### P0-40：RD 开发 + 架构师 CR 默认 Opus（深度判断不可降级）

- 触发：用户「rd 开发和 架构 review 默认应该用 opus 模型」+ 实战 case 显示 Bug 流程架构师 CR 用 Sonnet
- 设计决策（用户拍板）：
  - **RD 开发**（Dev Stage）默认 Opus（保持原推荐 / 显式化 + 例外说明）
  - **架构师 Code Review**（Review Stage + Bug 流程必经）从 Sonnet 推荐改为 Opus 推荐
  - **QA Code Review** 保持 Sonnet（执行型校验，TC 覆盖判断 Sonnet 够用）
  - **原则统一为**："深度判断 = Opus / 执行验证 = Sonnet / 异质独立 = external"
  - external 角色独立机制（claude-agents）不动 — 与"架构师 CR / RD Dev"是不同概念
  - 红线数保持 15 条
- 处理（4 处改造，跳过原计划的 P0-40-3 claude-agents 同步）：
  - **P0-40-1. `agents/README.md` §一 模型偏好调整**：原 "Opus 推荐 = Plan/Blueprint/Dev/Designer / Sonnet 推荐 = Review/Browser E2E" 重构为按角色细分：
    - Opus 推荐：RD Dev / 架构师 CR / PM PRD / RD TECH / 架构师评审 TECH / Designer UI / Panorama
    - Sonnet 推荐：QA CR / QA TC / QA 测试 / Browser E2E / PRD/TC/TECH 多角色并行评审 / Bug 排查
    - external：codex / claude CLI（独立异质）
    - 加显式 v7.3.10+P0-40 关键变化说明
  - **P0-40-2. `stages/dev-stage.md` + `stages/review-stage.md` AI Plan 模式默认 Opus**：
    - dev-stage.md AI Plan 段加"v7.3.10+P0-40 默认 Opus 模型"硬规则（主对话继承会话 / Subagent 显式 model: opus / Bug 排查例外用 Sonnet）
    - review-stage.md AI Plan 段加三视角模型默认（架构师 CR = opus / QA CR = sonnet / external = 异质独立）
  - **P0-40-3. (跳过)** claude-agents 文件同步：审视后发现 claude-agents/ 处理的是 external reviewer，与 P0-40 的"架构师 CR / RD Dev"是不同概念，不需要改
  - **P0-40-4. `templates/dispatch.md` 模板更新**：Model 字段加完整场景化默认推荐注释（架构师 CR / RD Dev = opus；QA / Test / 校验型评审 = sonnet；含 Bug 排查例外）
  - **P0-40-5. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-39 → 7.3.10+P0-40
- 风险控制：
  - 不改 external 机制（claude-agents/invoke.md 默认 sonnet 不动 — 那是 external reviewer 调用，不是架构师 CR）
  - 不引入硬性强制（仍是"推荐"，用户可自定义覆盖）
  - 主对话模式由用户会话模型决定，仅在 Subagent 模式硬约束 model 字段
  - 红线数保持 15 条
- 影响面：
  - 改动文件：6 个（agents/README.md / dev-stage.md / review-stage.md / dispatch.md / SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - 用户体验：
    - Bug 流程架构师 CR 用 Opus → 减少深度问题漏判（典型 Bug 改动 ≤5 文件，Opus 反而更稳）
    - Feature 流程 Review Stage 三视角分层（架构师深度 / QA 校验 / external 异质）→ 平衡质量与成本
    - QA Code Review 仍用 Sonnet → 不增加 token 成本（QA 主要做 TC 逐条覆盖校验）
- 待跟进（非 P0-40 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 Opus 架构师 CR 的实测效果（finding 深度 / 漏判率 / 成本）
  - 是否需要在 .teamwork_localconfig.md 加 `default_model_per_role` 字段让用户级偏好持久化（当前用户级偏好需手工修改 stage spec）

---

## v7.3.10 + P0-39

> v7.3.10+P0-39 worktree 默认路径调整 + 可配置：原硬编码默认路径 `../feature-{Feature 全名}` 是 sibling 目录（仓库父目录的同级目录），存在两个问题：(1) 污染父目录（用户的 `~/apps/okok/` 下会出现 `feature-AUTH-F042-...` 这种与项目仓库混在一起的目录）；(2) IDE 跨 worktree 跳转受限 + 工具链忽略复杂。本次改默认路径为 `{worktree_root_path}/{Feature 全名}`（默认 `worktree_root_path = .worktree`，即项目根目录下 `.worktree/` 子目录），且支持在 `.teamwork_localconfig.md` 配置 `worktree_root_path` 字段调整根目录（如 `../.repo-worktrees` 父目录分组 / `/tmp/worktrees` 完全自定义绝对路径）；install.sh 自动注入 `.worktree/` 到项目根 `.gitignore`（避免主仓库 git 嵌套混乱）。

### P0-39：worktree 默认路径项目内 + 可配置 root_path

- 触发：用户「需要改为默认在项目根目录的.worktree 目录下，可在.teamwork_localconfig.md 配置路径」+ 二次精简「配置 key：`worktree_path` 改为 `worktree_root_path`，去掉占位符逻辑，默认就是 worktree_root_path 下按 featurename 创建子目录」
- 设计决策（用户拍板）：
  - **默认路径变更**：`../feature-{Feature 全名}` → `{worktree_root_path}/{Feature 全名}`（默认 worktree_root_path = `.worktree`）
  - **配置 key**：`worktree_root_path`（不是 worktree_path），语义更明确——是"根目录"，子目录按 Feature 全名自动拼接
  - **去掉占位符逻辑**：路径拼接简化为 `{worktree_root_path}/{Feature 全名}`，不需要 `{feature_name}` / `{repo_root}` 等占位符
  - **gitignore 自动化**：install.sh 自动检测项目根 .gitignore，缺则追加 `.worktree/`
  - 红线数保持 15 条
- 处理（6 处改造）：
  - **P0-39-1. `templates/config.md` 加 `worktree_root_path` 配置**：默认 `.worktree`；说明实际路径 = `{worktree_root_path}/{Feature 全名}`；含路径合法性约束 + .gitignore 提醒 + 解析优先级
  - **P0-39-2. `stages/plan-stage.md` 改 worktree 命令**：路径解析逻辑（读 worktree_root_path + 拼接 Feature 全名）；命令模板从 `git worktree add ../feature-{Feature 全名}` 改为 `git worktree add {worktree_root_path}/{Feature 全名}`；state.json 写入加 `root_path` 字段
  - **P0-39-3. `stages/triage-stage.md` 预检表加 worktree 路径预览行**：Step 7.5 「🛠 环境配置预检」表加 `worktree 路径` 行（按 localconfig 推算 + Plan Stage 入口创建）
  - **P0-39-4. `templates/feature-state.json` 示例更新**：`environment_config.worktree_root_path = ".worktree"`；`worktree.path` 示例改为 `.worktree/AUTH-F042-email-login`；加 `worktree.root_path` 字段
  - **P0-39-5. `install.sh` .gitignore 注入**：检测项目根 .gitignore 是否含 `.worktree/`；缺则追加（含说明注释）
  - **P0-39-6. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-38-B → 7.3.10+P0-39
- 风险控制：
  - state.worktree.path 是历史快照（不重算），老 Feature 的旧路径保留
  - localconfig 缺 `worktree_root_path` → 用新默认 `.worktree`
  - 自定义路径在项目内时由用户自行确保 gitignore（仅默认路径自动注入）
  - 项目无 `.git` 目录时 install.sh 跳过 gitignore 注入（不报错）
  - 红线数保持 15 条
- 影响面：
  - 改动文件：6 个（config.md / plan-stage.md / triage-stage.md / feature-state.json / install.sh / SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - state.json 字段：`environment_config.worktree_root_path`（新增）/ `worktree.root_path`（新增）/ `worktree.path` 默认值变更
  - 用户体验：
    - 新 Feature 的 worktree 自动落到项目内 `.worktree/{Feature 全名}`，不污染父目录
    - IDE 索引可包含 `.worktree/` 或排除（按团队偏好），跨 worktree 不再跳到 sibling 目录
    - 自定义路径配置一目了然（一行 `worktree_root_path: <path>`）
- 待跟进（非 P0-39 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 `.worktree/` 目录在 IDE 中的索引体验（IntelliJ / VS Code）
  - 是否需要在 install.sh 提供命令行参数自定义 worktree_root_path（避免每个项目手工改 localconfig）

---

## v7.3.10 + P0-38-B

> v7.3.10+P0-38-B 三个硬约束补丁：用户实战 case（INFRA Android 落地页 CDN 域名替换）暴露 P0-38-A 设计未真正落地——AI 仍按旧 P0-28 模式跑：(1) triage Step 8 输出 Q1-Q4 四个产品决策（替换范围 / 实现参数化 / 复制内容 / 反馈方式），把业务方向 / 技术方案 / UX 细节决策都塞进 triage 暂停点；(2) 用户回 "1B 2B 3A 4A" 时实际是回答了产品决策，没机会确认骨架，流程跳步，Plan Stage 失去价值；(3) state.json 缺 execution_plan_skeleton / available_roles / external_cross_review 三字段；(4) Plan Stage 入口直接跳到"创建目录 + 写 PRD"，绕过实例化流程（读 execution_hints / 写 plan_substeps_config / 输出 5 行 Plan / ⏸️ 用户瞬时确认）。本次补三个硬约束让 P0-38-A 真正落地：(A) triage Step 8 暂停点唯一合法形态是骨架确认 3 选 1 + 禁止产品决策类暂停点；(B) Step 9 state.json 写入硬清单（必含三字段，缺一不可）+ PMO 校验；(C) plan/blueprint/review 三 Stage 入口实例化硬规则，跳过实例化视为流程违规；(D) `roles/pmo.md` 加"产品决策边界"段，明确 triage 决策范围 vs Plan Stage 决策范围 + 反例（实战 Q1-Q4 模式）+ PMO 自检清单。

### P0-38-B：让 P0-38-A 真正落地的硬约束补丁

- 触发：用户「看下下面的 case 有问题么」+ 提供实战 case（INFRA Android 落地页 CDN 域名替换 Q1-Q4 产品决策塞 triage）+ AI 审视后发现 5 处偏离 P0-38-A 契约 +「按建议」（启动 P0-38-B）
- 设计决策（用户拍板）：
  - **不增红线**：通过 Stage 契约硬规则 + PMO 角色自检 + 反模式禁止条款达到约束效果（红线数保持 15 条）
  - **PMO 产品决策边界明确**：triage 不决策业务方向 / 技术方案 / UX 细节；这些带不确定性进 Plan Stage 由 PM 起草 PRD 时承载
  - **Stage 入口实例化不可绕过**：进入 Plan/Blueprint/Review 必须先做实例化，跳过视为流程违规
  - **state.json 写入硬清单**：triage Step 9 必含 execution_plan_skeleton / available_roles / external_cross_review 三字段
- 处理（4 处改造）：
  - **P0-38-B-1. `stages/triage-stage.md` Step 8/9 加硬约束**：
    - Step 8 暂停点唯一合法形态：骨架确认 3 选 1（采用 / 调整 / 其他）
    - 禁止反模式：≥2 个产品决策点 / 流程确认 + 产品澄清混在同一暂停点 / Q1-Q4 类的业务方向决策
    - execution_plan_skeleton 输出契约：必须输出 4+1 字段，仅"流程步骤描述"段不算合规
    - Step 9 state.json 写入硬清单：必含 execution_plan_skeleton / available_roles / external_cross_review 三字段（缺一视为流程违规）
    - 含违规示例（实战 case 反模式）
  - **P0-38-B-2. `stages/{plan,blueprint,review}-stage.md` 入口实例化硬规则**：
    - plan-stage.md 加"跳过实例化 = 流程违规"硬规则 + 反模式列举（直接跳到创建目录 + 写 PRD / Steps remaining 仅 3 步 / Role specs loaded 缺）
    - blueprint-stage.md 同上（禁止跳过直接进 4 步内部闭环）
    - review-stage.md 同上（禁止跳过直接进三视角独立审查）
    - PMO 校验：未先输出实例化 5 行 Plan + 写入 *_substeps_config → 视为流程违规
  - **P0-38-B-3. `roles/pmo.md` 加"PMO 产品决策边界"段**：
    - 决策类型与责任归属（triage 决策范围 vs 不该决策范围 vs 产品决策合法承载位置）
    - 错误做法详细反例（实战 case Q1-Q4 模式完整展示）
    - 正确做法（方式 1 把不确定性带进 Plan Stage 默认推荐 / 方式 2 极简需求唯一解读）
    - 边界例外：合法的 Step 8 暂停点（流程类型确认 / 环境配置异常 / 跨 Feature 冲突）
    - PMO 自检清单（输出前 3 步自检：A/B/C 决策点检查 / 业务-技术-UX 关键词检查 / 3 选 1 格式检查）
  - **P0-38-B-4. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-38-A → 7.3.10+P0-38-B
- 风险控制：
  - 不破坏现有 Stage 契约（仅加硬约束 + PMO 校验，不改 Stage 处理流程）
  - 不引入新红线（红线数保持 15 条）
  - 反例直接来自实战 case（提高 AI 识别力）
  - 兼容老 Feature：state.json 缺新字段时按降级路径处理（标 INFO + 不阻塞）
- 影响面：
  - 改动文件：6 个（triage-stage.md / plan-stage.md / blueprint-stage.md / review-stage.md / pmo.md / SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - 红线数：保持 15 条
  - PMO 行为变化：
    - triage Step 8 不再输出产品决策选项
    - 业务/技术/UX 取舍带不确定性进 Plan Stage
    - state.json 必含 execution_plan_skeleton / available_roles / external_cross_review
    - 进入各 Stage 必须先做入口实例化（5 行 Plan + 写 *_substeps_config + ⏸️ 用户瞬时确认）
  - 用户体验：
    - triage 输出更聚焦（仅骨架确认，不再回答产品 Q&A）
    - 产品决策集中在 Plan Stage（PM 起草 PRD 时一次性讨论 + 用户最终确认）
    - 减少决策疲劳（避免回答 4-5 个 A/B/C 选项）
- 待跟进（非 P0-38-B 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 P0-38-A + B 是否真正落地（特别是 PMO 自检清单的执行率）
  - 如 AI 仍漏掉 execution_plan_skeleton 字段，考虑加 state.json 写入前的机器可校验脚本

---

## v7.3.10 + P0-38-A

> v7.3.10+P0-38-A 修订 P0-38 的两个设计点：(1) 角色可用性扫描从 init Stage 移回 triage Stage——init 职责本已重，且角色可用性是动态的（用户中途装/卸 CLI 应实时感知），available_roles 不应是会话级常量；(2) execution_plan_skeleton.stages 字段从"5 字段（含 candidate_roles）"瘦身为"4 字段必填 + 1 可选（execution_hints）"——candidate_roles 是机械可推算的，不应入决策态；改为 execution_hints 文本字段（软建议非决策），承载启用/跳过角色 + 动作动词（评审/设计/实现 TDD/测试/验收/净化+push+finalize）+ 模型 + 理由；角色固定 Stage（Dev/Test/PM 验收/Ship）允许 hints=null；Stage 入口实例化时必读 hint + 否决时在 *_substeps_config.hint_overrides 写文本说明（cite hint 原文 + override 原因）。形成 triage 给软建议 + Stage 入口实例化做硬决策的双层契约。

### P0-38-A：角色扫描移回 triage + execution_hints 文本契约

- 触发：用户「角色可用性扫描是否应该放到 triage 阶段，triage 阶段的目标就是需要哪几个 stage 来完成事项，事项的目标是什么，每个 stage 的预估参与角色是什么」+「等一下，我觉得偏了，triage 输出的应该是个骨架...至于模型，串行还是并行，在这个阶段执行时再做进一步规划。不做前置规划，防止上下文不够」+「是否给一个阶段实施建议，例如 external_reviewer(codex) 参与一下评审」+「role_hints 是否可以直接是个文本，而不是结构化 json」+「启用 architect/qa/external(codex) 改为 启用 architect/qa/external(codex) 评审」（动词后缀）+「不需要每个 Stage 都给建议，但给建议一定给理由」+「是否把角色建议改为执行建议更好一些」+「接受」
- 设计决策（用户拍板）：
  - **角色可用性扫描放 triage**（修复 P0-38 设计错误）：每次 Feature 启动实时扫描，反映运行时环境变化；available_roles 是 Feature 决策时快照，不是会话级常量
  - **删 candidate_roles 字段**：机械可推算的不入决策态（基于 Stage spec 内置清单 ∩ available_roles 即可推算）
  - **加 execution_hints 字段（文本，可选）**：
    - 文本不是 JSON：消费者只有 Stage 入口的 PMO（也是 LLM），无需结构化解析；state.json 已有 concerns/note/pmo_summary 等文本字段先例；文本可表达犹豫/条件/关联
    - 命名"执行建议"不是"角色建议"：hint 承载内容超出"哪些角色"，含动作动词 + 模型 + 顺序 + 协调
    - 软约定格式（非硬约束）："启用 X 动词；跳过 Y。理由：..."
    - 动词约定：评审 / 设计 / 实现 TDD / 测试 / 验收 / 净化+push+finalize
    - 角色固定 Stage（Dev/Test/PM 验收/Ship）允许 hints=null
    - 给 hint 必须有理由（不接受裸建议）
  - **加 hint_overrides 字段（文本，可选）**：Stage 入口实例化时若否决 hint，必须在 *_substeps_config.hint_overrides 写文本说明（cite hint 原文 + override 原因）
  - 红线数保持 15 条
- 处理（7 处改造）：
  - **P0-38-A-1. `templates/feature-state.json` schema 调整**：删 execution_plan_skeleton.stages[].candidate_roles；加 execution_hints (string | null)；available_roles 注释从"init 写入"改"triage 写入"；plan_substeps_config 加 hint_overrides 字段
  - **P0-38-A-2. `stages/init-stage.md` 回退角色扫描段**：删除 P0-38-3 添加的"角色可用性扫描段"，恢复"探测延后到 triage Step 4"
  - **P0-38-A-3. `stages/triage-stage.md` Step 4 + Step 8 调整**：Step 4 从"读 available_roles"改回"角色可用性扫描"（调 detect-external-model.py 写 available_roles）；Step 8 骨架字段：删 candidate_roles + 加 execution_hints + 渲染措辞用"执行建议"+ 动词约定 + 角色固定 Stage 不给 hint
  - **P0-38-A-4. `roles/external-reviewer.md` 来源调整**：可用性来源段从"init Stage 决定"改为"triage Stage 决定"+ 设计意图说明
  - **P0-38-A-5. plan/blueprint/review-stage.md 入口实例化段更新**：读 execution_hints + 必读 cite + 否决时写 hint_overrides；删除对 candidate_roles 的引用
  - **P0-38-A-6. `roles/pmo.md` 智能推荐表注释同步**：智能推荐表段说明承担两处职责（triage 时生成 execution_hints + Stage 入口实例化）
  - **P0-38-A-7. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-38 → 7.3.10+P0-38-A
- 风险控制：
  - 不破坏现有 *_substeps_config 内部契约（仅加 hint_overrides 字段）
  - 不引入结构化 hint schema（文本字段，灵活性高 + 维护成本低）
  - 老 Feature 兼容：state.json 缺新字段时按 Stage spec 内置清单走标准流程，无需迁移
  - 红线数保持 15 条（红线 #14 AI Plan 模式 + execution_hints 软建议 + Stage 入口实例化天然形成"骨架软建议 → 入口硬决策 → 5 行 Plan"三层）
- 影响面：
  - 改动文件：7 个（feature-state.json + init-stage.md + triage-stage.md + plan/blueprint/review-stage.md + external-reviewer.md + pmo.md + SKILL.md / CHANGELOG.md 版本号）
  - state.json schema：删 execution_plan_skeleton.stages[].candidate_roles；加 execution_hints (string | null)；plan_substeps_config 等加 hint_overrides
  - 概念变化：candidate_roles 决策字段 → execution_hints 软建议字段
  - 用户体验：
    - triage 主对话渲染从机械"角色范围列表"改为有指向性的"执行建议（含动词 + 模型 + 理由）"
    - Stage 入口实例化路径透明（hint + override_reason 留审计痕迹）
    - 角色固定 Stage（Dev/Test/PM 验收/Ship）不再有冗余 hint
- 待跟进（非 P0-38-A 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 hint 命中率（PMO triage 时 hint 与 Stage 入口实际决策的一致率）
  - hint_overrides 文本格式是否需要软约定（如 cite hint 原文 + override 原因两段式）

---

## v7.3.10 + P0-38

> v7.3.10+P0-38 triage 输出骨架 + Stage 入口实例化 + external 升格为评审角色：用户审视当前 triage stage 输出后提出关键设计反思——triage 时上下文不足以决策每 Stage 的具体执行细节（PRD 还没写、代码还没出），把"模型选择 / 串行并行 / 评审循环参数 / 具体输入输出"前置到 triage 是过度规划，违反延迟绑定原则。本次重构 triage stage 的输出本质：从"决策片段化输出"升级为"完整 Feature 骨架"——只输出 5 字段（stage / candidate_roles / goal / key_outputs / pause_points），具体决策推迟到各 Stage 入口实例化（红线 #14 AI Plan 模式承担）。同时把外部模型从"独立维度（plan_enabled/blueprint_enabled/review_enabled 三字段）"升格为"评审角色"（新建 `roles/external-reviewer.md`，与 PL/RD/QA/Designer/PMO/Architect 平级）；角色可用性扫描从"triage 时探测"前移到"init Stage 一次性扫描"（写入 state.available_roles[]）；triage Step 8 决策块从"两个独立块（外部模型 + Plan 评审组合）"瘦身为"单一骨架决策块"。形成"init 能力探测 → triage 骨架调度 → 各 Stage 入口实例化"三层职责正交架构。

### P0-38：triage 骨架化 + Stage 入口实例化 + external 升格

- 触发：用户「我们重新确认下 triage stage 需要输出的内容，我理解是一个落地 plan，完成这个 feature 需要哪些 stage，每个 stage 有哪些 todo，每个 todo 的参与角色是什么，每个角色的模型是什么，输入是什么，输出是什么」+ 反思「等一下，我觉得偏了，triage 输出的应该是个骨架，有哪些流程，需要谁参与，目标是什么。至于模型，串行还是并行，在这个阶段执行时再做进一步规划。不做前置规划，防止上下文不够」+「确认」
- 设计决策（用户拍板）：
  - **三层职责正交架构**：
    - init Stage = capability detection（一次性扫描 available_roles）
    - triage Stage = scheduler（输出 execution_plan_skeleton 骨架）
    - 各 Stage 入口 = workers（基于上游产物实例化具体配置）
  - **triage 骨架 5 字段**：stage / candidate_roles / goal / key_outputs / pause_points（不含模型/串行并行/具体 IO/评审循环参数）
  - **延迟绑定原则**：所有"基于上下文不足以决策"的字段（model / execution / 串行并行 / round_loop）推迟到各 Stage 入口
  - **external 升格为评审角色**：与 PL/RD/QA/Designer/PMO/Architect 平级，统一进入 review_roles[]；不再有独立维度
  - **取消 P0-28 三字段**：plan_enabled / blueprint_enabled / review_enabled 删除（按 review_roles[] 是否含 external 判定）
  - **立场独立性硬约束保留**：external-reviewer.md 反复强调异质模型 + forbidden_files 不可读
  - 红线数保持 15 条
- 处理（9 处改造）：
  - **P0-38-1. `templates/feature-state.json` schema 变更**：加 `available_roles[]` + `execution_plan_skeleton` 顶层字段；删 `external_cross_review.{plan/blueprint/review}_enabled` 三子字段（保留 model / host / available_clis 等元数据）
  - **P0-38-2. 新建 `roles/external-reviewer.md`**：角色契约（核心价值=立场独立性 + 通用评审原则 + context schema 规范 + 失败降级 + 立场独立性硬约束反复强调）
  - **P0-38-3. `stages/init-stage.md` 加角色可用性扫描段**：原 P0-24 的"延后探测"废止；改为 init Step 1.x 一次性扫描内部 6 角色（固定可用）+ 调用 detect-external-model.py 探测 external 异质性 + 写入 state.available_roles[]
  - **P0-38-4. `stages/triage-stage.md` Step 4 + Step 8 重写**：
    - Step 4：从"调探测脚本"改为"读 state.available_roles[]"
    - Step 8：删独立"🌐 外部模型评审决策"块 + 删"🧭 Plan Stage 评审组合决策"块；改为输出 execution_plan_skeleton（5 字段：stage / candidate_roles / goal / key_outputs / pause_points）+ 启动确认 3 选 1
  - **P0-38-5. `stages/plan-stage.md` 加入口实例化段**：删 plan_enabled 字面值引用（替换为"`"external" in plan_substeps_config.review_roles[].role`"）；加 Plan Stage 入口实例化流程（PMO 基于 execution_plan_skeleton.stages[plan].candidate_roles + 已有信息决策 active_roles + execution + pl_prioritized + round_loop）
  - **P0-38-6. `stages/blueprint-stage.md` 加入口实例化段**：删 blueprint_enabled 字面值引用；加 Blueprint Stage 入口实例化流程（基于 PRD 复杂度信号决策评审组合 + ADR 触发判断）
  - **P0-38-7. `stages/review-stage.md` 加入口实例化段**：删 review_enabled 字面值引用；加 Review Stage 入口实例化流程（基于 Dev Stage 代码复杂度决策三视角评审组合 + parallel_mode）
  - **P0-38-8. `roles/pmo.md` 智能推荐表瘦身**：原"🌐 外部模型交叉评审开关决策"段顶部加 P0-38 升格说明；原"🧭 Plan Stage 评审组合智能推荐"段重定位为"Plan Stage 入口实例化的角色实现规范"
  - **P0-38-9. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-37 → 7.3.10+P0-38
- 风险控制：
  - 不破坏现有 Stage spec 内部契约（Process Contract / Output Contract 主体不变，仅入口加实例化段 + 字段引用更新）
  - 不引入新抽象（claude-agents/ + codex-agents/ 现有文件作为 external 角色 context 物化，零变更）
  - external 异质性硬约束保留（init 扫描时同源外部不进 available_roles）
  - 老 Feature 兼容：state.json 缺新字段时降级为 P0-28 兼容层行为（老字段 plan_enabled 等读到时按原语义解释）
  - 红线数保持 15 条（红线 #14 AI Plan 模式 + Stage 入口实例化天然对齐，二者形成"骨架 → 实例化 → 5 行 Plan"清晰双层）
- 影响面：
  - 改动文件：9 个（feature-state.json + 新建 external-reviewer.md + init-stage.md + triage-stage.md + plan-stage.md + blueprint-stage.md + review-stage.md + pmo.md + SKILL.md / CHANGELOG.md 版本号）
  - state.json schema 新增字段：available_roles[] / execution_plan_skeleton{}
  - state.json schema 删除字段：external_cross_review.{plan_enabled / blueprint_enabled / review_enabled}
  - 红线 #14 AI Plan 模式：与 Stage 入口实例化天然对齐（5 行 Plan 就是实例化产物）
  - 用户体验：
    - triage Step 8 从 2-3 个决策块瘦身为 1 个骨架决策块（决策疲劳显著降低）
    - external 是否启用变成"角色是否在 candidate_roles 推荐里"（语义统一）
    - 不可用 external 自动从推荐里剔除（用户面无感降级）
- 待跟进（非 P0-38 范围）：
  - 1-2 个真实 Feature 跑下来后回顾骨架决策块的可读性 + 各 Stage 入口实例化的实操体验
  - templates/external-cross-review.md 措辞按"角色契约"语境调整（非 P0-38 范围，独立小补丁）
  - 老 Feature 兼容层何时正式淘汰（建议跑 5+ 新 Feature 后再考虑）

---

## v7.3.10 + P0-37

> v7.3.10+P0-37 codex profile 默认 high + fast：用户实战 case 暴露 codex CLI 调用频繁卡死或超时——根因是 `codex-agents/*.toml` 全部 8 个 profile 中只有 `designer.toml` 显式设置了 `model_reasoning_effort = "high"`，其余 7 个未设 → fallback 到 codex CLI 默认 `xhigh`（极深度思考模式，单次调用可能 5-15 分钟），叠加 `service_tier` 全部未设 → fallback 到 OpenAI API 默认 `standard` tier（高负载时排队），双重放大耗时。本次统一所有 8 个 profile 显式默认 `model_reasoning_effort = "high"` + `service_tier = "fast"`，并在 codex-agents/README.md 加默认配置说明 + 调优指引（何时调高/调低 + 用户级覆盖方法 + 与红线 #14 的关系）。

### P0-37：codex profile 默认 high + fast（避免 xhigh 卡死 + standard tier 慢响应）

- 触发：用户「我们能否默认 codex 执行的时候使用 high 和 fast 模式，避免耗时和卡死」+ 实战 case 显示 codex 调用经常超时或卡死（macOS `timeout` 命令缺失叠加 codex 自身 xhigh 推理深度）+「按建议」
- 设计决策（用户拍板）：
  - **统一显式默认**：所有 8 个 profile 显式设置 `model_reasoning_effort = "high"` + `service_tier = "fast"`，不再依赖 codex CLI fallback
  - **质量 vs 速度的权衡**：`high` 是 cross-review 质量足够 + 响应时间可控（30-180 秒）的合理 baseline；`xhigh` 卡死代价 = 整个 Feature 流转中断 + 用户介入诊断，不接受作为默认
  - **service_tier=fast 计费略高但稳定性收益远超成本**：用户 OpenAI 账户不支持 fast tier 时不会报错（仅退化为 standard 行为），无副作用
  - **保留用户级覆盖**：profile 级编辑 / 命令行 -c 覆盖 / 项目根 `.codex/config.toml` 全局覆盖三种方式
  - 红线数保持 15 条
- 处理（3 处改造）：
  - **P0-37-1. 8 个 codex profile 加 `model_reasoning_effort = "high"` + `service_tier = "fast"`**：reviewer.toml / prd-reviewer.toml / blueprint-reviewer.toml / designer.toml（已有 high，加 fast）/ planner.toml / rd-developer.toml / tester.toml / e2e-runner.toml；每行加 v7.3.10+P0-37 注释说明
  - **P0-37-2. `codex-agents/README.md` 加「默认推理深度 + service_tier 配置」段**：
    - 全局默认配置块
    - 为什么默认 high + fast（vs xhigh 默认卡死、vs standard 排队）
    - 何时调整（调低 / 调高 / service_tier 切换）
    - 用户级覆盖方法（profile 级 / 命令行 / config.toml）
    - 与红线 #14 的关系（high 是 Plan 模式合理 baseline，xhigh 容易在 Plan 模式纸面分析阶段卡住）
    - 历史 case 说明
  - **P0-37-3. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-36 → 7.3.10+P0-37
- 风险控制：
  - 不修改 developer_instructions 段（业务逻辑不变）
  - 不修改 sandbox_mode（权限边界不变）
  - 用户 OpenAI 账户不支持 fast tier 时降级为 standard 行为，不会报错
  - 用户可通过 profile 级 / 命令行 / config.toml 三种方式覆盖默认值
  - 红线数保持 15 条
- 影响面：
  - 改动文件：9 个（8 个 codex-agents/*.toml + 1 个 codex-agents/README.md + SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - codex 调用耗时：xhigh → high 实测下降 60-80%（用户报告：高复杂度场景 5-15 分钟 → 30-180 秒）
  - codex 调用稳定性：standard → fast 减少 API 排队等待，跨地理区域 / 高负载时段尤其明显
  - 用户体验：codex cross-review 不再卡死，Feature 流转可预期完成
- 待跟进（非 P0-37 范围）：
  - 1-2 个真实 Feature 跑下来后回顾 high 模式的 cross-review 质量是否仍能发现深层 finding（如不足以发现关键问题，考虑 prd-reviewer / blueprint-reviewer 两个最关键的 profile 单独提到 xhigh + 配合 gtimeout 上调）
  - macOS 用户 `timeout` 命令缺失问题（用户场景）：考虑 `claude-agents/invoke.md` 加 `gtimeout` fallback 检测 + 友好提示
  - 是否在 .teamwork_localconfig.md 加 `codex_default_reasoning_effort` / `codex_default_service_tier` 字段，让用户级偏好持久化（未来 P0）

---

## v7.3.10 + P0-36

> v7.3.10+P0-36 Bug 流程 state.json + Ship Stage 补齐：用户审计发现 Bug 流程两个设计漏洞——(1) Bug 流程不维护 state.json（rules/flow-transitions.md Bug 流程表所有 11 条转移以 BUG-REPORT.md 文本字段为状态源，违反 v7.3.2「state.json 单一权威」）；(2) Bug 流程无 Ship Stage（PMO Bug 总结直接到「完成 ✅」，commit/push/MR/merge/worktree 清理全部空白）。这两个漏洞是 v7.3.10+P0-15（Ship Stage 引入）+ +P0-29（双段拆分）+ +P0-32（Ship Finalize push）等连续升级时**只改 Feature 流程未同步 Bug 流程**的累积结果。本次补齐：(A) BUG-REPORT.md 加机读 YAML frontmatter（复用 feature-state.json 字段命名，承担 Bug 流程的 state.json 职能，不新建独立 state.json 文件以避免简单 Bug 流程膨胀）；(B) Ship Stage 加 Bug 缩简分支（共享 Step 1-10 主流程，仅状态承载文件 / 字段命名 / MR 标题模板 / push 范围有差异）；(C) flow-transitions.md Bug 流程末尾加 4 条 Ship 转移行；(D) 红线 #1 Ship Finalize 例外条款扩展（从仅允许 state.json 一文件 → 同时允许 BUG-REPORT.md 一文件，仅 frontmatter 元数据字段）。复杂 Bug 不影响（升级 Feature 后用 Feature 的 state.json）。

### P0-36：Bug 流程 state.json + Ship Stage 补齐

- 触发：用户「看下 bugfix 流程是否有问题，更新的文件是否是 state.json，结束后是否会自动进入 ship」+ 审计确认两个漏洞 +「按建议」
- 设计决策（用户拍板）：
  - **不新建独立 state.json 文件**：BUG-REPORT.md 顶部 YAML frontmatter 承载 Bug 流程状态机，字段命名复用 feature-state.json（current_stage / phase / shipped / commit_hash / mr_url / merge_commit_hash 等），保持 schema 一致性 + 避免简单 Bug 流程文件膨胀
  - **Ship Stage 共享主流程**：Bug 缩简版与 Feature 共享 Step 1-10，仅产物 / 状态字段引用 / MR 标题模板 / push 范围有差异，不重复 Stage 设计
  - **红线 #1 Ship Finalize 例外条款扩展**：从仅允许 state.json 一文件 → 同时允许 BUG-REPORT.md 一文件（仅 frontmatter 元数据字段，零业务影响）
  - **复杂 Bug 不变**：复杂 Bug 进入 Feature 流程后用 Feature 的 state.json，无需改动
  - 红线数保持 15 条（红线 #1 例外条款扩展，不增红线）
- 处理（6 处改造）：
  - **P0-36-1. `templates/bug-report.md` 加机读 YAML frontmatter**：bug_id / feature_id / classification / flow_type: bug / current_stage 枚举 / completed_stages / phase / commit_hash / shipped / mr_url / mr_merged_at / merge_commit_hash / merge_target_pushed_at / worktree_cleanup / ship_concerns / planned_execution 等字段；含复杂 Bug 例外说明（移交 Feature state.json）+ PMO 校验规则
  - **P0-36-2. `stages/ship-stage.md` 加 🆕 Bug 流程缩简分支段**：触发条件（flow_type=bug + classification=simple + current_stage=pmo_summary + phase=summarized）+ 与 Feature Ship 关键差异表（状态承载 / 字段引用 / MR 标题 / Step 7-8 写入对象 / push 范围）+ 各步骤 Bug 分支差异说明（Step 1-10 各项是否有差异）
  - **P0-36-3. `rules/flow-transitions.md` Bug 处理流程末尾加 4 个 Ship 转移行**：`PMO Bug 总结 → Ship Stage 第一段` / `Ship 第一段 → 等待合并` / `等待合并 → Ship Finalize`（⏸️暂停）/ `Ship Finalize → Bugfix 完成 ✅`；额外加 2 条异常分支（MR 关闭未合并 / push 失败）；既有 11 条转移加 frontmatter 字段引用
  - **P0-36-4. `roles/pmo.md` Bug 流程段加 BUG-REPORT.md frontmatter 维护职责**：初始化模板 + 每次阶段变更必做（写 frontmatter current_stage）+ 复杂 Bug 升级时移交规则 + Ship Stage 调度规则；`FLOWS.md` Bug 流程末段加 Ship Stage 流程图（净化 → push → MR → ⏸️ 用户合并 → finalize → 清理）
  - **P0-36-5. 红线 #1 Ship Finalize 例外扩展**：`SKILL.md` 红线 #1 措辞从"Feature 流程"扩展为"Feature 流程 / 简单 Bug 流程"两分支，明确 Bug 分支允许 push BUG-REPORT.md 一文件 + 仅 frontmatter 元数据字段；`stages/init-stage.md` 红线 #1 同步；`stages/ship-stage.md` Step 7 严格边界段同步加 Bug 分支
  - **P0-36-6. CHANGELOG + 版本号 bump + 一致性自检**：版本号 7.3.10+P0-34-A → 7.3.10+P0-36（跳过 P0-35，因 P0-35 是评审 → 讨论模式重构方案被驳回）
- 风险控制：
  - 不破坏 Feature 流程现有契约（Ship Stage 主流程 Step 1-10 完全不变）
  - 不引入新文件（frontmatter 寄宿在 BUG-REPORT.md，不新建独立 state.json）
  - 复杂 Bug 上升 Feature 流程时清晰移交（frontmatter classification=complex + current_stage=escalated_to_feature）
  - 老 Bug 兼容：v7.3.10+P0-36 之前的 BUG-REPORT.md（无 frontmatter）仍允许存在，PMO 在流转校验时识别为"老格式"，提示用户手工 ship 或补 frontmatter；新建 BUG-REPORT.md 强制带 frontmatter
  - 红线数保持 15 条（红线 #1 例外条款扩展，不增红线）
- 影响面：
  - 改动文件：6 个（bug-report.md / ship-stage.md / flow-transitions.md / pmo.md / FLOWS.md / SKILL.md / init-stage.md / CHANGELOG.md）
  - state.json 字段：feature-state.json **不改**（Bug 流程不复用 state.json 文件）
  - BUG-REPORT.md 新增 frontmatter：~20 个字段（复用 feature-state.json 字段命名）
  - 红线 #1 Ship Finalize 例外：从单分支扩展为双分支（Feature / Bug）
  - 用户体验：简单 Bug 修复后自动进入 Ship Stage，commit/push/MR/finalize/worktree 清理闭环；BUG-REPORT.md frontmatter 单一权威记录全程状态
- 待跟进（非 P0-36 范围）：
  - 1-2 个真实简单 Bug 跑下来后回顾 Ship 缩简版实测体验（特别是 Step 7 写 BUG-REPORT.md frontmatter 的可读性 vs state.json）
  - 是否需要为 Bug 流程也加 worktree 集成（当前 worktree 主要服务 Feature 流程，简单 Bug 通常不开 worktree）
  - templates/bug-report.md 老格式兼容性的 PMO 识别逻辑细化

---

## v7.3.10 + P0-34-A

> v7.3.10+P0-34-A 是对 P0-34 评审模式的「对抗深度补丁包」（不重构 P0-34 主框架）：用户实战担忧 → P0-34 评审模式相比旧 PL-PM 讨论可能导致对抗深度降低（finding 提了 PM 给个 ADOPT/REJECT/DEFER 就过、问题被 DEFER 抛给用户、PL 业务深度被技术评审挤压）。诚实反思后，**不做 P0-35 完整重构**（"对抗辩论"在 LLM 上的实现存在物理局限：subagent 和 PM 是同一模型，没有真实立场冲突；多轮回合 ≠ 多轮深度），改用 3 个小补丁覆盖 80% 诉求：(A) DEFER 严格收紧（仅允许 category=business-decision，技术/业务/UX/质量类 finding 禁止 DEFER）；(B) PM 对抗性自查段（每条 ADOPT/REJECT 前必须先输出 ≥2 句"反方最强论据模拟"，对抗强度通过内省补回）；(C) PL 优先权 + 业务方向锁死（PL 评审先于其他角色 dispatch，PL 收敛后 PRD frontmatter `business_direction_locked: true`，其他角色基于锁死 PRD 评审，防止技术评审挤压业务对齐）。3 补丁合力使 PM response 从"轻量回应"变成"对抗内省 + 实质收敛"，且不增加流程步数。

### P0-34-A：DEFER 收紧 + PM 对抗性自查 + PL 优先权（3 补丁包）

- 触发：用户「之前的PL  PM 讨论效果很好，也能发现一些问题，变成review 之后是否会导致讨论深度降低了，例如将更多问题抛给了用户，而不是经过反复思考对抗性辩论的结果。」+ 反思「对抗性辩论是否合理，是否会将流程变复杂」+「按建议」
- 设计决策（用户拍板）：
  - **不做 P0-35 完整重构**：评审 → 讨论模式重构是过度工程化；LLM 自对抗物理局限存在；P0-34 刚做完未经实战验证就大改属 anti-pattern
  - **3 个小补丁**覆盖核心诉求：DEFER 收紧 + PM 自查 + PL 优先权
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **P0-34-A. `roles/pm.md` + `templates/prd.md`：DEFER 严格收紧**
    - DEFER 加 `category` 字段，仅允许 `"business-decision"`（明确商业/用户决策范围：商业策略 / 价格 / 法务合规 / 用户研究待补）
    - 禁止类别：`technical-consistency` / `business-alignment` / `ux` / `quality`（必须 ADOPT 或 REJECT 带 rebuttal）
    - PMO 校验：扫描所有 DEFER 项的 category 一致性，违规打回 PM 重做，校验通过写 `state.plan_substeps_config.defer_audit_passed: true`
  - **P0-34-B. `roles/pm.md` + `templates/prd.md`：PM 对抗性自查段**
    - PM 每条 ADOPT/REJECT 之前必须输出 `adversarial_self_check` 段（≥2 句具体内容）
    - 站在 finding 提出方视角写最强反驳论据（防止 LLM 配合性回应 / sycophancy）
    - REJECT 项 rationale 必须直接回应 adversarial_self_check 中的反方论据
    - PMO 校验：扫描所有 ADOPT/REJECT 项的 adversarial_self_check 字段（≥2 句具体内容 / 非空白 / 非占位符），违规打回，校验通过写 `state.plan_substeps_config.adversarial_check_passed: true`
  - **P0-34-C. `stages/plan-stage.md` + `roles/pmo.md` + `templates/prd.md` + `templates/feature-state.json`：PL 优先权 + 业务方向锁死**
    - 子步骤 2 拆为「阶段 2a：PL 优先评审」+「阶段 2b：其他角色并行评审」
    - PL 评审收敛 → PMO 写 PRD frontmatter `business_direction_locked: true` + state.json `business_direction_locked: true` + `business_direction_locked_at`
    - 业务方向不锁死，其他评审角色禁止 dispatch（防止焦点切碎）
    - PMO 智能推荐：review_roles[] 含 PL 时默认 `pl_prioritized: true`；纯技术 refactor / 业务方向已在 CR 阶段锁死时退化为 P0-34 全并行
    - 其他角色基于锁死 PRD 评审；发现实现层与已锁死方向矛盾，以 high 严重度上升触发回归 PL 二次评审
- 风险控制：
  - 不重构产物结构（PRD-REVIEW.md 仍保留）
  - 不重命名 state.json 字段（review_round / review_roles[] 等保持原名）
  - 不增加 Stage 步数（仍是 P0-34 的 5 子步骤）
  - PL 优先权可关闭（`pl_prioritized: false` 退化全并行，兼容纯技术 refactor）
  - 老 Feature 兼容：现有 Feature 已无新字段时按默认值（false）行为
  - 红线数保持 15 条
- 影响面：
  - 改动文件：5 个（pm.md / prd.md / plan-stage.md / pmo.md / feature-state.json + SKILL.md / init-stage.md / CHANGELOG.md 版本号）
  - state.json 字段：`plan_substeps_config` 加 `pl_prioritized` / `business_direction_locked` / `business_direction_locked_at` / `defer_audit_passed` / `adversarial_check_passed`
  - PRD frontmatter：加 `business_direction_locked` / `business_direction_locked_at`
  - PRD-REVIEW.md frontmatter：`pm_response` 重构为对象（含 action / category / adversarial_self_check / rationale / responded_at）
  - 用户体验：PM response 不再轻量；DEFER 不能滥用抛给用户；PL 业务对齐先于技术评审
- 待跟进（非 P0-34-A 范围）：
  - 1-2 个真实 Feature 跑下来后回顾对抗深度实测效果
  - 如果实测仍不够深，再启动 P0-35（评审 → 讨论模式重构）

---

## v7.3.10 + P0-34

> v7.3.10+P0-34 Plan Stage 5 子步骤显式化 + 多角色并行评审重构 + 用户质疑反应模式：用户实战 case（AI 进入 Plan Stage 后只做 PRD 初稿就直接暂停等用户确认，跳过了「PL 讨论」「RD/QA/Designer 多视角评审」「PM 回应循环」等内部子步骤）暴露当前 Plan Stage 设计的两个根因：(1) 子步骤对 AI 不可见——Plan Stage 在主对话被当作"原子动作"，PRD 初稿后直接跳到「⏸️ 用户确认」，PL 讨论 + 4 视角评审被预测性简化；(2) PL 角色定位混淆——PL 既是 product-overview/CR 的 driver，又是 Plan Stage 的"独立讨论 step"，导致 AI 不清楚 PL 在 Plan Stage 究竟该不该出现。本次重构：将 Plan Stage 拆为 5 个显式子步骤（PRD 初稿 → 多角色并行评审 → PM 回应循环 → 全员通过判定 → ⏸️ 用户最终确认），PL 降级为评审角色（与 RD/QA/Designer/PMO peer），评审组合 + Subagent 并行 vs 主对话执行模式由 PMO 在 triage Step 8 智能推荐 + 用户确认后写入 state.json 的 `plan_substeps_config`。AI Plan 模式 Execution Plan 从 4 行扩为 5 行（新增 `Steps remaining` 行强制枚举子步骤），强化"声明即承诺"细则（声明 Read 的 spec 必须真实 Read，可用 grep 历史 ToolUse 验证）。新增「用户质疑流程时 AI 反应模式」4 条规则（先规范 cite + 再边际价值 + 不主动建议跳过 + 用户明确说才豁免），防御 AI 看到用户疑虑就预测性简化的反模式。

### P0-34：Plan Stage 5 子步骤显式化 + 多角色并行评审 + 用户质疑反应模式

- 触发：用户「我觉得当前 Plan Stage 在主对话执行的时候，AI 容易跳过其中的 PL 讨论 + 多视角评审子步骤，直接 PRD 初稿后就 ⏸️ 等用户确认。这是流程被预测性简化的典型」+「在想想该怎么改」+「方向 B，需要 PMO 智能决策，但无论何时，智能决策的过程不能跳过，对应我们的 triage stage」+「Plan Stage 应该还有外部模型视角评审」+「我觉得 PL 讨论去掉，PL 也作为评审的一个角色」+「Subagent 并行 vs 主对话的混合，triage 阶段 PMO 来决定」+「按建议」
- 设计决策（用户拍板）：
  - **Plan Stage 5 子步骤显式化**：PRD 初稿（PM 主对话）→ 多角色并行评审（subagent / 主对话由 PMO triage 决定）→ PM 回应循环（ADOPT/REJECT/DEFER）→ 全员通过判定（all PASS / PASS_WITH_CONCERNS）→ ⏸️ 用户最终确认。Round ≤ 3，超出 Round 3 触发用户决策（force-pass / continue-round-4 / modify-scope / abort）。
  - **PL 角色定位拆分**：PL 在 product-overview / change-request 阶段是 driver；在 Plan Stage 是评审角色（与 RD/QA/Designer/PMO peer），不再有"独立 PL-PM 讨论 step"。
  - **外部模型评审作为 Plan Stage 子步骤 4**：由 P0-28 `plan_enabled` 控制（不引入新开关）。
  - **执行模式 PMO 智能决策**：subagent 并行 vs 主对话由 PMO 在 triage Step 8 推荐（信号：文件数 / 跨子项目 / 上下文累积 / token budget）+ 用户 5 选 1 确认（采用推荐 / 全 Subagent / 全主对话 / 自定义 / 其他指示）。
  - **Direction A 核心**：Execution Plan 从 4 行扩为 5 行（新增 `Steps remaining`），强迫 AI 在 Stage 开始前枚举子步骤，跳步立即可见。
  - **声明即承诺**（新增红线 #14 细则）：声明 Read 的 spec 必须真实 Read，可用 grep 历史 ToolUse 验证；声明而未 Read 视为伪造证据，违反闭环验证红线 #9。
  - **用户质疑反应模式**（4 条规则）：先 cite 规范 → 分析本场景边际价值 → 不主动建议跳过 → 用户明确说「跳过」才豁免（红线 #3 兜底）。
  - 红线数保持 15 条（红线 #14 扩展 + 用户质疑反应模式作为常规规则）
- 处理（11 处改造）：
  - **P0-34-1. `roles/pmo.md` 加 Plan Stage 评审组合智能推荐表**：5 种 Feature 类型 × 评审角色组合表 + 执行模式信号（subagent vs 主对话）+ 5-step 推荐流程 + PMO 视角触发条件（中以上启用）+ Designer 视角触发条件（双保险：PRD frontmatter + UI 关键词）+ Round 3 overflow 用户决策。
  - **P0-34-2. `stages/triage-stage.md` Step 8 加 Plan Stage 评审组合决策段**：PMO 推荐格式 + 5 选 1 选项 + Step 9 state.json 初始写入加入 `plan_substeps_config`。
  - **P0-34-3. `templates/feature-state.json` 加 plan_substeps_config 字段**：含 `review_roles[]`（每项 role + execution）+ `review_round` + `review_round_overflow_decision` 枚举（force-pass / continue-round-4 / modify-scope / abort）。
  - **P0-34-4. `stages/plan-stage.md` 重写 Process Contract**：5 子步骤表 + Step 2 并行 dispatch 逻辑 + Step 3 PM 回应规则（ADOPT/REJECT/DEFER）+ Step 4 round 判定 + Round 3 overflow 处理 + Step 5 用户最终确认 + PRD-REVIEW.md frontmatter schema 引用 + 流程硬规则更新。
  - **P0-34-5. `roles/product-lead.md` 加「PL 作为评审角色」段**：按 Feature 类型激活 + PL 评审 checklist（业务方向一致性 / 业务流程完整性 等）+ verdict 标准 + Subagent vs 主对话指引 + driver 角色（product-overview/CR）vs reviewer 角色（Plan Stage）的边界。
  - **P0-34-6. `roles/pm.md` 替换「PL-PM Teams 讨论」为「PM 评审回应规则」**：每条 finding 的回应规则（ADOPT 改 PRD / REJECT 给理由 / DEFER 给追踪位置）+ 硬规则（回应完整性 + 不静默跳过）+ 轮次流程描述。
  - **P0-34-7. `roles/rd.md` / `roles/qa.md` / `roles/designer.md` 加 Plan Stage PRD 评审 checklist**：各角色专属维度 + verdict 标准。
  - **P0-34-8. `templates/prd.md` 追加 PRD-REVIEW.md frontmatter schema**：`prd_feature_id` / `review_round` / `reviews[]` 数组（每项 role / execution / verdict / findings[] / pm_response）/ `overall_verdict` / 机器可验证条件。
  - **P0-34-9. `rules/flow-transitions.md` + `FLOWS.md` 加 Plan Stage 5 子步骤转移**：8 个新转移行 + auto 强制保留清单 3 条 + Feature 流程链显示 Plan Stage 5 子步骤标注。
  - **P0-34-10. `SKILL.md` Execution Plan 4 行 → 5 行（加 Steps remaining）+ 红线 #14 加声明即承诺细则；`RULES.md` + `roles/pmo.md` 加用户质疑流程时 AI 反应模式段**（4 条规则 + 输出模板 + 反例 + 与红线关系）。
  - **P0-34-11. CHANGELOG + 版本号 bump + 一致性自检**。
- 风险控制：
  - 不破坏现有 Plan Stage 上下游契约（仍以 PRD.md + PRD-REVIEW.md 为产物）
  - 评审组合 PMO 推荐 + 用户显式确认（不允许 PMO 主动 "省略评审角色"）
  - Round ≤ 3 硬上限 + 超出走用户决策，避免无限循环
  - 红线数保持 15 条（修订红线 #14 + 加常规规则，不增红线）
  - 兼容老 Feature：现有 Feature 已无 `plan_substeps_config` 时 PMO 按"全 4 视角内部 + 主对话"默认值
- 影响面：
  - 改动文件：13 个（pmo.md / triage-stage.md / feature-state.json / plan-stage.md / product-lead.md / pm.md / rd.md / qa.md / designer.md / prd.md / flow-transitions.md / FLOWS.md / SKILL.md / RULES.md）
  - state.json 字段：feature 顶层加 `plan_substeps_config`（含 review_roles[] / review_round / review_round_overflow_decision）
  - SKILL.md 红线 #14 扩展：4 行 → 5 行 + 声明即承诺细则
  - 用户体验：Plan Stage 不再被预测性简化 + 用户质疑时 AI 不再主动建议跳过 + 评审组合可定制
- 待跟进（非 P0-34 范围）：
  - 评审 verdict 自动化校验工具（解析 PRD-REVIEW.md frontmatter，未来 P0）
  - Plan Stage 评审耗时实测数据 + 推荐表权重调整（积累 5+ Feature 实战后回顾）

---

## v7.3.10 + P0-33

> v7.3.10+P0-33 变更管理升级：用户实战 case（BG-015 5 个子 Feature 中 2 已合并 staging、3 仍占位 FXXX）暴露当前变更管理两个问题：(1) `teamwork_space.md` 承担过多——既是子项目入口又含跨项目变更详细追踪表（子 Feature 编号 / 推进顺序 / 联调依赖），文件膨胀；(2) "边规划边启动"反模式——变更内 5 个子 Feature 没全部规划完就启动了 2 个，剩 3 个仍是占位符，跨子项目协调成本高。本次新增独立变更文档体系：`product-overview/changes/{change_id}.md` 含 YAML frontmatter（机读 status / sub_features / launch_order）+ 完整规划详情；`teamwork_space.md` 简化为变更索引（简介 / 状态 / 文档链接）；硬约束变更状态 != `locked` 时禁止启动归属本变更的子 Feature（PMO 在 triage Step 6.5 硬阻塞 + 用户明确选「强制启动」逃生舱）。

### P0-33：变更管理升级（独立文档 + 锁定后启动 + teamwork_space.md 简化）

- 触发：用户「变更流程需要做的更合理一些。变更描述文档放到 product-overview 子目录 changes 下，teamwork_space.md 只维护简单介绍 / 索引 / 当前状态，降低 teamwork_space.md 的负担。变更流程需要做完所有的需求规划后才能正式启动 feature」+「按建议」
- 设计决策（用户拍板）：
  - **变更编号格式**：`CR-{编号}` 推荐通用 / `BG-{编号}` 兼容历史 / `TD-{编号}` 可选
  - **state.json 加 change_id 字段**（null 表示独立 Feature 不归属任何变更）
  - **硬阻塞 + 强制启动逃生舱**：变更未锁定时禁止启动子 Feature，但保留「用户明确选数字 2」的逃生舱（不接受 ok / 默认推进）
  - **现有变更回填支持**（如 BG-015）：不阻塞已启动子 Feature，但补登未启动的 + 锁定剩余规划
  - **变更 vs ADR 并存**：变更=跨多 Feature 协作规划，ADR=单一技术决策；互相引用（变更 frontmatter `related_adrs`）
  - 红线数保持 15 条
- 处理（8 处改造）：
  - **A. 新建 `templates/change-request.md`**：独立变更描述模板，含完整 YAML frontmatter（change_id / status / sub_features / launch_order / risks / related_adrs）+ 状态生命周期 + 编号约定 + 与 teamwork_space.md / ADR / ROADMAP 的关系
  - **B. `templates/teamwork-space.md` 简化**：删除「跨项目需求追踪」详细表（子 Feature 编号 / 推进顺序 / 联调依赖）；改为「跨项目变更索引」段（简介 / 状态 / 影响子项目 / 文档链接）+ 加「跨项目当前阻塞」段（仅活跃阻塞项）
  - **C. `roles/product-lead.md` 加「变更管理」段**：状态生命周期 + PL 在各阶段的职责 + 模式二「执行模式」与变更管理的关系（升级而非废弃）+ 编号约定 + 与 ADR 的关系
  - **D. `stages/triage-stage.md` Step 6.5 变更归属检查**：扫描 product-overview/changes/*.md → 判断当前 Feature 归属 → 按变更状态决策（discussion/planning 硬阻塞 / locked/in-progress 校验 launch_order 拓扑位置 / completed/abandoned 异常提示）+ 4 选 1 逃生舱
  - **E. `roles/pmo.md` 加「📦 变更归属检查」段**：扫描 / 匹配规则 / 状态决策矩阵 / 阻塞输出格式 / 强制启动 + 改独立 Feature 处理 / state.json 写入 / 硬规则
  - **F. `templates/feature-state.json`**：顶层加 `change_id` + `change_force_start` 字段 + 注释说明
  - **G. `FLOWS.md` Feature Planning 段加「变更级 Planning」子模式**：完整流程描述（discussion → planning → locked → in-progress → completed）+ 核心约束 + 与 templates/change-request.md / roles/product-lead.md 关联
  - **H. `rules/flow-transitions.md` 加「变更管理状态转移」段**：6 个状态转移行 + 硬阻塞条件；auto 强制保留清单加 2 条（变更归属阻塞 4 选 1 / 锁定确认 4 选 1）
  - **I. `roles/pm.md` 职责段加变更级 Planning 协作规则**
- 风险控制：
  - 不阻塞独立 Feature（`change_id = null` 时 PMO 不做变更检查）
  - 既存变更（如 BG-015）支持回填，不强制重写历史
  - 强制启动逃生舱保留 + state.concerns WARN 留痕
  - 变更详情独立文档化避免 teamwork_space.md 膨胀
  - 红线数保持 15 条（修订流程边界，不增红线）
- 影响面：
  - 新建文件：1 个（`templates/change-request.md`）+ 新目录约定（`product-overview/changes/`）
  - 改动文件：8 个（teamwork-space.md / product-lead.md / triage-stage.md / pmo.md / feature-state.json / FLOWS.md / flow-transitions.md / pm.md）
  - state.json 字段：顶层加 change_id + change_force_start
  - 用户体验：变更管理流程更清晰（"规划完才启动"硬约束）+ teamwork_space.md 轻量化
- 待跟进（非 P0-33 范围）：
  - install.sh 是否需要在 product-overview/ 下自动建 changes/ 目录（暂不做，PMO 在首次创建变更时自建）
  - PMO triage 时 git 推断 feature 是否已合并（与 P0-32 配合解决"staging 尾巴"问题，可作为 P0-34）

---

## v7.3.10 + P0-32

> v7.3.10+P0-32 红线 #1 修订 + Ship Stage 第二段 push merge_target 收尾：用户实战 case 暴露 v7.3.10+P0-29 双段流程留下的"staging 尾巴"问题——MR 合并后 PMO 验证 + 写 state.json 最终态，但这个最终态只在本地 worktree 内（之后被清理）+ 没回到 staging，导致下个 Feature 启动时 PMO 在 staging 上看到上个 Feature 的 state.json 仍显示 phase=pushed，误判为"还在进行中"。本次修订红线 #1 加 Ship Finalize 例外条款：第二段 finalize 阶段允许 PMO push merge_target 一次，仅限 `{Feature}/state.json` 一个文件、仅状态字段、零业务影响。push 失败有完整降级路径（pull --rebase 重试 1 次 / 退回 feature 分支 push + state.concerns WARN），不阻塞流程。代码层合并权（push merge_target 业务代码）仍 100% 属于平台和用户。

### P0-32：红线 #1 修订 + Ship Stage 第二段 push merge_target 收尾

- 触发：用户「ship 流程，mr 合入后还会有一次状态变更，这个状态变更会被丢弃掉」+「在 staging 推进下一个需求的时候，往往还剩上一个需求的尾巴，因为 staging 并不知道上个需求已经完结」+「PMO 直接 push staging，是否更合理，我们修改下红线。确认 commit 合入后，切到目标分支，改状态，push，然后再清理 worktree」
- 设计决策：
  - **修订红线 #1（不是删除）**：保留"PMO 不做本地 merge / 不解决冲突"核心约束；新增 Ship Finalize 例外条款（仅一文件、仅状态字段、零业务影响）
  - **拆为更细的 Step 4-10**：原 Step 5/6/7 拆为 Step 5（检测）/ Step 6（切 merge_target + pull）/ Step 7（写最终态）/ Step 8（push）/ Step 9（清理 worktree）/ Step 10（完成报告）
  - **state.json 写入位置变更**：原"第二段写 state.json 在 worktree 内"→"在 merge_target 工作区内的 feature 目录"——避免 worktree 删除时丢失
  - **push 失败完整降级**：冲突 pull --rebase 重试 1 次 / protect rule 直接降级 / 网络失败询问用户 / 其他错误降级 + concerns
  - **降级仍记 phase=merged**（合并已完成，仅 push staging 失败不影响最终态判定）
  - 红线数保持 15 条（修订红线 #1 边界，不新增红线）
- 处理（6 处改造）：
  - **A. `SKILL.md` 红线 #1**：原"Ship Stage 行为（不 push merge_target）" → 新"Ship Stage 行为（v7.3.10+P0-15 / +P0-32 修订）"，加 Ship Finalize 例外条款 + 严格边界（仅 state.json 一文件 / 仅状态字段 / 零业务影响）+ push 失败降级
  - **B. `stages/init-stage.md` 红线 #1 注入段同步**：CLAUDE.md 注入红线 #1 加 Ship Finalize 例外条款描述
  - **C. `RULES.md` Ship Stage 速查段**：单 Stage 描述扩展为双段（第一段 push 不动 merge_target / 第二段 finalize push state.json 元数据）
  - **D. `stages/ship-stage.md` 第二段 Step 4-7 重写为 Step 4-10**：
    - Step 5（检测结果处理）：不在本步写 state.json，记录到内存变量
    - Step 6（切 merge_target）：cd 主工作区 + git checkout + git pull --ff-only；pull 失败暂停
    - Step 7（写 state.json 最终态）：在 merge_target 工作区内的 feature 目录写最终态（严格边界）
    - Step 8（push merge_target）：git add + commit + push；4 类失败降级（冲突 / protect rule / 网络 / 其他）
    - Step 9（清理 worktree）：cd 主工作区 + git worktree remove
    - Step 10（完成报告）：state.json 已在 Step 7+8 完整写入，本步只输出报告
  - **E. `roles/pmo.md` Ship Stage PMO 职责速查重写**：双段 + finalize push merge_target + 失败降级三态 + 红线 #1 边界（允许 / 禁止）
  - **F. `templates/feature-state.json` 加 3 个字段**：merge_target_pushed_at / merge_target_push_failed / merge_target_push_failed_reason（含 conflict / protect-rule / network / other 枚举）
  - **G. `rules/flow-transitions.md` Ship 第二段拆 6 行**：原 1 行（第二段统一行）扩展为 6 行（Step 6 切 merge_target / Step 6 pull 失败 / Step 7-8 push 成功 / Step 8 push 失败降级 / Step 9 清理 worktree）+ auto 强制保留清单加 2 条
  - **H. `FLOWS.md` Feature 流程图段更新**：10. Ship Stage 第二段从单行扩展为 7 行（Step 4-10 含 push merge_target 步骤）
- 风险控制：
  - 严格边界：仅 state.json 一文件、仅状态字段、零业务影响——红线 #1 的核心精神（PMO 不动业务代码）保持不变
  - push 失败完整降级：冲突 / protect rule / 网络 / 其他四类全有处理路径，不阻塞流程
  - 降级路径仍记最终态（feature 分支 push + state.concerns WARN）—— 即使 push merge_target 失败，本地 / feature 分支 remote 都有完整最终态
  - PMO 后续 triage 时 git 推断（git branch -r --contains）即使 staging 上 state.json 不完整也能正确识别 feature 已合并（这部分逻辑可在 P0-33 加，本次先不做）
- 影响面：
  - state.json 字段：state.ship 加 3 个字段（merge_target_pushed_at / merge_target_push_failed / merge_target_push_failed_reason）
  - 改动文件：6 个核心（SKILL.md / init-stage.md / RULES.md / ship-stage.md / pmo.md / feature-state.json）+ 2 个流转文件（flow-transitions.md / FLOWS.md）
  - 用户体验：staging 上 state.json 现在会显示 phase=merged（push 成功时）/ phase=merged + concerns（降级时）→"尾巴"问题在 push 成功路径下消失
  - 红线数：15 条（保持）
- 待跟进（非 P0-32 范围）：
  - P0-33 候选：PMO triage / init-stage 扫描 Feature 状态时加 git branch -r --contains 推断（即使 staging 上 state.json 不完整也能正确识别 feature 已合并）—— 双重保险

---

## v7.3.10 + P0-31

> v7.3.10+P0-31 两个补丁：(1) worktree 默认值从 off 翻转为 auto（撤销 v7.3.9+P0-9 决策）；(2) PMO 角色规范增加 ok = 按 💡 建议 识别快速规则（v7.3.10+P0-18 已在 RULES/STATUS-LINE 定义，本次在 roles/pmo.md 显式标注 PMO 收到用户输入时的识别顺序）。

### P0-31-A：worktree 默认值改为 auto（撤销 P0-9）

- 触发：用户「修改下现有逻辑：默认开始 worktree」
- 设计决策（撤销 P0-9 默认 off 的考量）：
  - 多 Feature 并行场景实际更常见，worktree 隔离避免主分支污染
  - v7.3.10+P0-29 Ship Stage 双段流程后 worktree 清理已闭环（合并验证后自动清理）
  - v7.3.10+P0-25 worktree deps 处理已有完整指引（standards/common.md 含 npm install / 软链 / KNOWLEDGE 三种处理选项）
  - v7.3.10+P0-27 环境配置预检前置到 triage，worktree 创建已自动化无暂停点
  - off 仍保留为可选（megarepo / IDE 跨 worktree 跳转受限场景仍可手动改 off）
- 处理（2 处改造）：
  - **A. `templates/config.md`**：worktree 字段默认值 `off` → `auto`；注释更新为 v7.3.10+P0-31 决策说明 + 撤销 P0-9 的理由 + 何时改 off 的指引
  - **B. `stages/init-stage.md`**：localconfig 不存在时的兜底从 `worktree=off` → `worktree=auto`，注释同步更新
- 影响面：
  - 既有项目（已有 .teamwork_localconfig.md 含 worktree=off）→ 不受影响（用户配置优先于默认值）
  - 新项目 / localconfig 缺失 → 默认 auto，PMO 在 Plan Stage 入口自动按 environment_config 创建 worktree
  - Micro 流程：本来就是直接改主分支不创建 worktree，不受默认值影响
- 风险控制：
  - 用户可随时改回 off（编辑 .teamwork_localconfig.md）
  - PMO 在 triage Step 7.5 环境配置预检会显式输出 worktree 模式 → 用户在暂停点可见

### P0-31-B：roles/pmo.md 显式标注 ok = 按建议 识别规则

- 触发：用户「PMO 需要知道 ok = 按建议」
- 现状诊断：v7.3.10+P0-18 已在 RULES.md / STATUS-LINE.md / SKILL.md / INIT.md 定义 ok 约定，但 roles/pmo.md（PMO 角色规范权威源）没有显式段落——PMO 加载自身规范时可能漏过该约定
- 处理（1 处改造）：
  - **`roles/pmo.md` 顶部加「🟢 用户输入识别快速规则」段**（在格式权威守门段之后、state.json 状态机维护规范之前）：
    - 4 类用户输入识别顺序（数字/字母 → ok 类肯定词 → 切换流程关键词 → 自由输入）
    - ok 类清单（ok / OK / Ok / 好 / 可以 / 行 / 嗯 / 按建议 / 按推荐）
    - PMO 必须 cite「✅ 已按 💡 建议处理：…」作为审计痕迹
    - 前置条件 + 边界保留（破坏性操作仍需显式数字回复）
    - 链接到 RULES.md 完整规范
- 影响面：
  - PMO 加载自身规范时直接看到 ok 识别规则，不依赖跨文件读取
  - 其他文件（RULES / STATUS-LINE）的 ok 规范不变，本次只是补 pmo.md 的显式入口

### 元数据

- SKILL.md frontmatter 7.3.10+P0-30 → 7.3.10+P0-31
- stages/init-stage.md L111 同步
- 红线数保持 15 条

---

## v7.3.10 + P0-30

> v7.3.10+P0-30 问题排查类轻量化：用户实战 case 暴露 triage-stage 对所有流程类型用同一个暂停点格式（4 选 1）的副作用——问题排查这种"用户意图明确、零代码改动、纯只读"的轻量任务被迫走完整 triage（4 步流、3 个暂停点）+ 询问排查范围 + 4 选 1 流程确认，反而违反用户明确意图。本次针对问题排查类做精准简化：信号置信度高时跳过 triage 4 选 1 流程确认暂停点（主动声明 + 直接执行 + 保留打断机制）；删除"PMO 给排查清单 → ⏸️ 用户确认范围"暂停点（PMO 自主决定排查范围 + 默认只读不启本地服务 + 标注未实测项）；KNOWLEDGE / ADR 无命中时一行带过；问题排查不展示外部模型探测段。结果：问题排查典型暂停点从 3 个降到 1 个（仅排查报告后的决策）。

### P0-30：问题排查类流程精简（信号置信度高时跳过 triage 流程确认暂停点 + 删除排查范围确认暂停点）

- 触发：用户实战 case「检查下 aon-com 网站的 favicon 是否符合预期」跑出 4 步流 3 暂停点 + 排查范围确认询问，反模式明显 → 用户「如果是问题排查，能否简化一些，不需要确认那么多，减少流程环节，直接排查」
- 设计决策：
  - **仅简化问题排查类**（不动 Feature / Bug / 敏捷 / Feature Planning / Micro，影响面最小）
  - **置信度判定**：用户措辞含明确核验词（"检查 / 排查 / 看看 / 为什么 / 分析下 / 是否符合预期 / 定位"）+ 无修复指令 + 范畴清晰 → 高置信度走快速通道；模糊 / 跨子项目 → 保守走标准 4 选 1
  - **快速通道**：跳过 4 选 1 + 主动声明"直接进入问题排查执行" + 保留用户打断机制（"切换流程"）
  - **PMO 自主决定排查范围**：默认源码静态查（grep / ls / cat / git log）+ 配置核对；不启动本地服务（dev server / Playwright），如需实测须用户授权
  - **KNOWLEDGE / ADR 无命中渲染降级**：从展开三类 0 命中标题 → 一行带过（"📚 KNOWLEDGE 扫描：均无相关条目"）
  - **问题排查不展示外部模型探测段**：问题排查不出代码、不需要外部模型评审；triage 输出整体跳过该段
  - 红线数保持 15 条
- 处理（5 处改造）：
  - **A. `stages/triage-stage.md` Step 5 流程类型识别表**：扩展问题排查识别信号词典（增加"检查下 / 看看 / 是否符合预期"等核验意图措辞）
  - **B. `stages/triage-stage.md` Step 8 暂停点呈现重构**：
    - 标准路径：Feature / Bug / 敏捷 / Feature Planning / Micro 走原 4 选 1 流程确认
    - 快速通道：流程类型 = 问题排查 + 信号置信度高 → 主动声明 + 直接执行
    - 置信度判定表（高 / 中 / 低 三档 + PMO 决策）
    - 用户打断机制（"切换流程"等关键词）
  - **C. `stages/triage-stage.md` Step 2 / 3 / 4 输出渲染降级**：
    - Step 2 KNOWLEDGE 无命中 → 一行带过（"📚 KNOWLEDGE 扫描：均无相关条目"）
    - Step 3 ADR 无命中 → 一行带过（"📜 ADR 扫描：均无相关决策"）
    - Step 4 外部模型探测：问题排查类时整体跳过本 Step
  - **D. `FLOWS.md` 问题排查流程概览段重构**：
    - 删除"PMO 派发角色 → ⏸️ 用户确认范围"暂停点
    - 加用户打断机制段
    - 简化为"用户提问 → triage 识别 + 信号置信度判定 → PMO 派发 + 自主决定范围 + 直接执行 → ⏸️ 用户决策"（仅 1 暂停点）
  - **E. `roles/pmo.md` 加「🔍 问题排查类轻量执行规则」段**：
    - 信号置信度判定表
    - PMO 派发角色规则（保留原 RD / PM / Designer）
    - 自主决定排查范围（默认只读，不启本地服务，标注未实测项）
    - 排查报告必填项（现状速查 / 现状 vs 预期 / 偏差等级 / 修复建议 / 未实测项清单）
    - 排查后 6 选 1 暂停点（不处理 / Micro / 敏捷 / Feature / Bug / 其他）
  - **F. `rules/flow-transitions.md` 问题排查流程转移表重构**：
    - 高置信度行：triage → 问题排查执行 🚀自动
    - 中/低置信度行：triage → 4 选 1 → 问题排查执行 ⏸️暂停
    - 删除原"问题排查梳理 → 排查待确认"独立行（合并到执行）
- 风险控制：
  - PMO 拿不准时**保守走标准 4 选 1**——用户回 1 选问题排查仍然进入快速通道，不会跑错流程
  - 用户打断机制保留（"切换流程"等）—— 任何时机用户都能切换
  - 修复指令明确时（如"检查并修好"）不识别为问题排查 → 走对应敏捷 / Bug / Micro 流程
  - 默认不启动本地服务 = 默认不动用户环境，避免越权
- 影响面：
  - 问题排查典型暂停点：3 个（流程确认 + 排查范围 + 决策）→ **1 个**（仅决策）
  - triage 输出长度：无命中场景下显著缩短
  - 改动文件：4 个（triage-stage.md / FLOWS.md / pmo.md / flow-transitions.md）
  - 红线数：15 条（保持）
- 待跟进（非 P0-30 范围）：
  - Feature Planning / Micro 是否也需要类似简化（用户暂未提，先不动）
  - 实战观察"信号置信度判定"的准确率，必要时调整词典

---

## v7.3.10 + P0-29

> v7.3.10+P0-29 Ship Stage 双段流程：用户洞察当前 Ship Stage 在 v7.3.10+P0-15 后留下"AI 生成 MR URL 后即结束"的工程缺口——用户在平台合并 MR 后 PMO 没有机制感知，worktree 永远 deferred、state.current_stage 永远停在 ship、Feature 永远不到 completed。本次重构为双段流程：第一段 push + 生成 MR URL + 输出明确"下一步该做什么"指引（4 选 1 暂停点：已合并/等待中/关闭未合并/其他）；第二段 finalize：用户回 1 后 PMO 用 `git branch -r --contains {feature_head_commit}` 自动检测合并 → 清理 worktree → Feature 标记 completed。检测失败（squash merge / GitLab rebase 重写场景）询问用户提供 commit hash 兜底。
>
> 设计哲学：把"明确告诉用户该做什么"做到位（v7.3.5/P0-18 暂停点编号化的延续），比开发复杂的自动监控更可靠；用户在每个关键节点都能"回数字即可继续"。

### P0-29：Ship Stage 双段流程（push → 等待合并 → finalize）

- 触发：用户「目前主要的问题是给出 mr create 链接，ai 什么也做不了了，是否能做到监控 MR 合入，合入后自动完成收尾」+「给出 mr create 后给个提示，合入后回复 1，将收尾流程。这样用户回到会话就知道该怎么做了」+「不用搞降级链了 简单点 branch-contains 检查就可以了。有问题询问用户」
- 设计决策：
  - **不做复杂的自动监控**（gh/glab 多层降级 / scheduled-task 轮询 / webhook）—— 简单可靠优先
  - **第一段暂停点明确指引**：用户在 MR URL 生成后看到"下一步该做什么"，回平台合并 → 回数字即可继续
  - **第二段用单一 git 命令检测**：`git branch -r --contains {feature_head_commit}` 覆盖 merge commit + GitHub rebase 等高频场景
  - **检测失败询问用户**：squash merge / GitLab rebase 重写场景下用户提供 hash + git 校验
  - **worktree 清理推迟到第二段**：合并验证通过后才清理（避免合并出问题需要回滚时 worktree 已经没了）
  - **MR 异常分支**：用户回 3 / 第二段询问回 3 → 进入异常处理（重开 MR / 放弃 Feature / 暂时等待）
- 处理（4 处改造）：
  - **A. `templates/feature-state.json` 加 ship 字段**（5 个新字段 + 1 个 enum 扩展）：
    - feature_head_commit / phase / merge_commit_hash / mr_merged_at / merge_detection_method
    - shipped enum 扩展：null | pushed | merged | closed_unmerged | abandoned | failed
    - phase enum：null | pushed | merged | closed_unmerged
  - **B. `stages/ship-stage.md` 重构为双段流程**：
    - 头部：v7.3.10+P0-29 双段流程定位 + 职责说明
    - 步骤概览：第一段 Step 1-3 + 第二段 Step 4-7 + 异常分支
    - Step 2 push 后加"git rev-parse 记录 feature_head_commit"
    - Step 3 重写为"等待合并暂停点 4 选 1"（删除原 worktree 清理暂停点，推迟到 Step 6）
    - 新增 Step 4：git fetch + git branch -r --contains 检测
    - 新增 Step 5：检测结果处理（5.A 通过 / 5.B 询问用户）
    - 新增 Step 6：清理 worktree（执行原 deferred）
    - 新增 Step 7：Feature 完成报告
    - 新增「异常处理段」：MR 关闭未合并 4 选 1（重开/放弃/暂时等待/其他）
  - **C. `roles/pmo.md` Ship Stage PMO 职责速查改写**：
    - 原 v7.3.10+P0-15 速查（3 步）→ v7.3.10+P0-29 速查（双段 + 异常分支）
    - 新增"第一段已完成、用户暂时退出"的恢复规则：下次进入 PMO 在 triage 识别 phase=pushed → 直接展示 Step 3 暂停点而不重跑第一段
  - **D. `rules/flow-transitions.md` + `FLOWS.md` 同步**：
    - flow-transitions：原 ship 1 行扩展为 6 行（第一段 / 等待合并暂停点 / 第二段 / 检测失败 / 异常处理 / push FAILED）
    - flow-transitions auto 强制保留清单加 3 条（第一段等待合并暂停点 / 第二段询问 hash / 异常处理）
    - FLOWS.md Feature 流程图段：原 9. Ship Stage 单步扩展为 9. Ship Stage 第一段 + 10. Ship Stage 第二段
- 风险控制：
  - 检测失败时 100% 走询问用户兜底，不静默标记为已合并
  - 用户提供 hash 必须经 git cat-file + branch -r --contains 双重校验
  - 异常分支保留完整路径（重开 MR / 放弃 / 等待）—— 不强制用户立刻决定
  - worktree 清理推迟到第二段验证通过后，避免误清理
  - 红线数保持 15 条
- 影响面：
  - state.json 字段：ship 子对象加 5 个新字段
  - 改动文件：4 个（feature-state.json / ship-stage.md / pmo.md / flow-transitions.md + FLOWS.md）
  - 用户体验：从"MR 生成后无衔接"→"4 选 1 明确下一步 → 自动验证合并 → 自动收尾"
- 待跟进（非 P0-29 范围）：
  - gh/glab CLI 适配（如未来用户反馈"git 检测覆盖率不够"）
  - scheduled-task 轮询（如 Cowork 环境下用户反馈"想要全自动"）

---

## v7.3.10 + P0-28

> v7.3.10+P0-28 三处评审外部模型决策合并到 triage-stage：用户洞察「PRD 评审 / 技术方案评审 / Review 是否需要外部模型」三处决策应该统一前置到 triage 阶段，由 PMO 按 Feature 规模/风险智能推荐 + 用户在 triage 暂停点一次性确认。`state.external_cross_review.enabled` 单字段拆为三处独立字段（plan_enabled / blueprint_enabled / review_enabled）。Review Stage 外部模型评审从 v7.3.10+P0-24 引入的「强制」改为「review_enabled 控制，默认 ON」——保持代码层最后 gate 行为，但允许用户在 triage 显式关闭。Fallback 兼容旧 enabled 字段。
>
> 默认行为：Plan / Blueprint 默认关（文档评审有内部 4 视角支撑），Review 默认开（代码层最后 gate）。PMO 按 Feature 规模/风险给智能推荐组合：大 Feature/高风险 → 三处全开；中/小 Feature/Bug → 仅 Review 开。提供快捷选项「采用推荐 / 全开 / 全关 / 自定义」。

### P0-28：三处评审外部模型决策合并到 triage-stage

- 触发：用户「我们把 prd 评审，技术方案评审，review 是否需要外部模型 放到 triage 阶段，由 pmo 根据实际情况设置」+「按建议，保留快捷选项」
- 设计决策：
  - **三处独立 enabled**：`external_cross_review.{plan_enabled, blueprint_enabled, review_enabled}` 取代单 `enabled` 字段
  - **Review 默认 ON**（保持 P0-24 引入的代码层最后 gate 行为，但从「强制」降为「review_enabled 控制」）
  - **PMO 智能推荐**用简单规则按 Feature 类型 + 关键词触发（不引入复杂权重模型）
  - **快捷选项**：采用推荐 / 三处全开 / 三处全关 / 自定义（用户回 `P=on/off B=on/off R=on/off` 格式）
  - **Fallback 兼容**：旧 enabled 字段自动映射到新三字段，旧 Feature 不强制迁移
- 处理（9 处改造）：
  - **A. `templates/feature-state.json` 字段拆分**：删除 `enabled` 单字段，新增 `plan_enabled / blueprint_enabled / review_enabled`；保留旧 enabled 注释作 fallback 文档化；加 `_fallback_compat` 注释说明读取规则
  - **B. `roles/pmo.md` 「外部模型交叉评审开关决策」段重写**：
    - 默认值改为三处独立（plan/blueprint=false, review=true）
    - 加 Step 3 PMO 智能推荐表（5 类 Feature 场景 × 3 处 Stage 决策矩阵）
    - 重写 Step 4 决策呈现（三处独立显示 + 5 选 1 快捷选项 + 选项 4 二级自定义）
    - Step 5 state.json 写入扩展为三字段
    - 兼容性段重写：fallback 优先级（三字段 > enabled > codex_cross_review > 默认）
    - 硬规则更新（默认值改为 PMO 推荐而非简单 OFF）
  - **C. `stages/triage-stage.md` Step 8 暂停点扩展**：外部模型决策点改为三处独立 + 快捷选项；Step 9 出口写入三字段
  - **D. `stages/plan-stage.md` 字段重命名**：`external_cross_review.enabled` → `external_cross_review.plan_enabled`（全文 replace_all）
  - **E. `stages/blueprint-stage.md` 字段重命名**：同上 → `blueprint_enabled`
  - **F. `stages/review-stage.md` 改为 review_enabled 控制**：
    - 入口宣告外部模型实例的条件改为 `review_enabled == true`
    - Step 4「外部模型独立审查」从「🔴 强制」改为「🟡 review_enabled 控制，默认 ON」
    - 措辞强调：与 P0-27 行为兼容（默认 review_enabled=true）
  - **G. `templates/external-cross-review.md` / `STATUS-LINE.md` / `FLOWS.md` / `templates/review-log.jsonl` 措辞同步**：
    - STATUS-LINE：徽章触发条件从 `enabled=true` 改为「任一 *_enabled=true」
    - FLOWS：默认值描述改为三处独立
    - review-log.jsonl：plan-external-review / blueprint-external-review / review-external 三行触发条件分别用对应 *_enabled
  - **H. `standards/external-model.md` §5.4 + Fallback 兼容表**：state.json 字段示例改为三字段；加 PMO 读取时 fallback 优先级表（5 个场景）
  - **I. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-27 → 7.3.10+P0-28；stages/init-stage.md 同步
- 风险控制：
  - 默认行为保持 P0-27 兼容：review_enabled 默认 ON，plan/blueprint 默认 OFF——既有 Feature 走 fallback 语义不变
  - 旧 Feature 不强制迁移（PMO 读取时自动 fallback）
  - 红线数保持 15 条
- 影响面：
  - 字段：state.external_cross_review 拆 1 → 3 字段
  - 改动文件：9 个（含 SKILL.md / 4 个 stage / pmo.md / state.json / external-cross-review.md / review-log.jsonl / STATUS-LINE.md / standards/external-model.md / FLOWS.md）
  - 用户体验：triage 暂停点决策项数 +1（外部模型评审），但配合快捷选项「采用推荐」实际操作步骤不变（一个数字回复完成）
  - 用户控制力：从「Plan/Blueprint 可选 + Review 强制」升为「三处全部可选」——更纯粹的"用户决定"
- 待跟进（非 P0-28 范围）：
  - PMO 智能推荐表的"中 Feature"判定标准实战观察后调整阈值
  - 跨 Feature 学习：连续 3 个 Feature 用户都改了推荐 → PMO 自动调整推荐策略（属于 P1+ 远期）

---

## v7.3.10 + P0-27

> v7.3.10+P0-27 删除 Plan Stage 入口 Preflight 暂停点：用户洞察 v7.3.9 引入的 Plan Stage 入口 preflight 暂停点是反模式——用户在 triage-stage 已经确认走 Feature 流程，再让用户对 PMO 自动跑通的环境检查结果做一次确认是仪式化操作；preflight 把"决策"和"执行"混在一起。重构原则：**决策前置到 triage（Step 7.5+8 探测 git 状态 + 用户在 triage 暂停点一次性确认环境配置），执行后置到 Plan Stage 入口（自动按 state.environment_config 执行 git 操作，无暂停点）**。Feature 典型暂停点从 4-5 个降到 3-4 个。preflight 概念整体废弃；Dev Stage 入口的"懒装依赖 preflight"和 PMO L1/L2/L3 dispatch 预检保留（不同概念）。

### P0-27：Plan Stage 入口 Preflight 暂停点删除

- 触发：用户「Plan Stage 入口 Preflight 确认 是否多余，直接 triage-stage 直接把需要确认的定好是否更合理」+「preflight 这命令也没用，直接去掉吧，保持干净，triage 阶段应该把该确认的都确认好了」
- 设计决策：
  - **彻底删除** Plan Stage 入口 preflight 暂停点（不留 escape hatch / 不做 `/teamwork preflight` 子命令）
  - 决策前置：triage Step 7.5 探测 git 状态（worktree / 分支 / base / 工作区干净度）+ Step 8 用户在 triage 暂停点一次性确认
  - 执行后置：Plan Stage 入口按 `state.environment_config` 自动执行 git 操作（fetch / 创建 worktree / 处理脏状态），**无暂停点**
  - 异常分支保留：base 不可达 / 分支冲突 / stash 失败时走异常分支（state.concerns + ⏸️），常规情况自动流转
  - 仅 Feature / Bug / 敏捷需求 流程触发 triage Step 7.5（Feature Planning / 问题排查 / Micro 不需要 worktree）
  - 红线数保持 15 条（无升格 / 无新增）
  - **Dev Stage 入口 preflight（懒装依赖，P0-3 引入）保留**——它是 Dev Stage 内部检查，不是用户暂停点
  - **PMO L1/L2/L3 dispatch 预检（红线 #13）保留**——它是 dispatch Subagent 前的预检，不同概念
- 处理（6 处改造 + CHANGELOG）：
  - **A. `stages/triage-stage.md` Step 7.5 加「环境配置预检」子段**：探测 git 状态 + 输出表格（worktree 模式 / 当前分支 / merge_target / base / 工作区状态 + 计划行为）+ 异常处理说明；仅 Feature / Bug / 敏捷需求 触发
  - **B. `stages/triage-stage.md` Step 8 暂停点扩展**：含流程类型 / 外部模型评审 / 环境配置异常（仅探测异常时出现）三层决策；常规情况下环境配置不需要单独决策
  - **C. `stages/triage-stage.md` Step 9 出口扩展**：写入 `state.environment_config = { worktree_mode, branch, merge_target, base, dirty_resolution, workspace_status_at_triage }`；triage 出口直接转入 Plan Stage（取代原"转入 Plan Stage 入口 preflight"）
  - **D. `stages/plan-stage.md` 删除整个「Stage 入口 Preflight」段（120+ 行）**，替换为新「Stage 入口环境准备」段（~70 行）：
    - 输入：state.environment_config（triage 已写入）
    - 自动执行序列：bash 4 步（dirty 处理 / fetch / worktree add / cd）
    - 异常分支表（4 类降级路径）
    - state.json 写入字段调整：`environment_config.{executed_at, worktree_created, concerns}`，删除原 `state.stage_contracts.plan_preflight` 字段
  - **E. `stages/plan-stage.md` 前置依赖段更新**：原 "Preflight" + "Worktree" 两条改为引用 state.environment_config
  - **F. `rules/flow-transitions.md` 删除 preflight 行**：原 "🔗 triage-stage → Plan Stage 入口 preflight" + "Plan Stage 入口 preflight → 🔗 Plan Stage" 两行合并为单行 "🔗 triage-stage → 🔗 Plan Stage（🚀自动）"；auto 豁免速查列表删除两条
  - **G. `roles/pmo.md` 删除「Plan Stage 入口 Preflight（v7.3.9 PMO 专属）」整段（80 行）**，替换为简短的「Plan Stage 入口环境准备」段（~15 行，引向 stages/plan-stage.md）；auto 豁免表中两条 preflight 行合并为一条
  - **H. 散落 preflight 字面值审查**：
    - `SKILL.md` 流程示例段删除 "0. Plan Stage 入口 preflight" 行
    - `stages/init-stage.md` auto 豁免列表 + worktree 检测段措辞调整
    - `templates/knowledge.md` "PMO preflight 阶段扫描" → "triage-stage 扫描" + 加链接
    - `templates/adr-index.md` "PMO preflight 阶段读取" → "PMO 在 triage-stage 阶段读取" + 加链接
  - **I. `templates/feature-state.json` 字段重构**：
    - 删除 stage_contracts.plan_preflight 整段
    - 新增顶层字段 `environment_config`（worktree_mode / branch / merge_target / base / workspace_status_at_triage / dirty_resolution / decided_at / executed_at / worktree_created / concerns）
    - 修订 stage_enum：删除 plan_preflight 枚举值，标注 v7.3.10+P0-27 重构说明
  - **J. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-26 → 7.3.10+P0-27；stages/init-stage.md L111 同步
- 风险控制：
  - 决策权完全保留给用户（在 triage 暂停点）—— 不是削减用户控制力
  - 异常分支降级路径完整（base 不可达 / 分支冲突 / stash 失败 都有暂停点 + state.concerns）
  - 既有 Feature 兼容：旧 Feature 的 stage_contracts.plan_preflight 字段允许遗留（PMO 读取时不报错），新 Feature 用 environment_config 字段
- 影响面：
  - 暂停点减少：Feature 典型暂停点 4-5 个 → 3-4 个
  - 改动文件：8 个（triage-stage.md / plan-stage.md / flow-transitions.md / pmo.md / SKILL.md / init-stage.md / knowledge.md / adr-index.md）+ 1 个 schema（feature-state.json）
  - 红线数：15 条（保持，无升格）
  - 概念清理：preflight 这个词在活文档中仅保留两处合理使用（Dev Stage 入口 preflight：懒装依赖；PMO L1/L2/L3 dispatch 预检），其他 preflight 字面值全部更名为"环境准备"或"环境配置"
- 待跟进（非 P0-27 范围）：
  - PRD 评审 / 技术方案评审 / Review 三处外部模型决策合并到 triage（用户提议 → P0-28）

---

## v7.3.10 + P0-26

> v7.3.10+P0-26 PMO 编排契约化升级：用户洞察 Teamwork 一致性漏洞——「PMO 承接用户输入 + 流程规划」当前散落在 5 个文件、4 种概念层级（红线 / 角色规范 / 流程文件 / 输出格式），但没有 Stage 契约。所有其他工作单元都走 Input/Process/Output 三契约，PMO 编排却游离在外。本次将 PMO 编排升格为契约化 Stage，确立**三层级 Stage 体系**：会话级（init-stage）/ 流程级（triage-stage）/ Feature 级（其余 10 个 stage）。同时 INIT.md 物理迁移到 stages/init-stage.md，统一所有 PMO 工作单元的契约形态。

### P0-26：PMO 编排契约化升级（init-stage + triage-stage）

- 触发：用户「pmo 承接用户输入，对流程进行规划，属于哪个 stage，我们讨论下怎样优化 teamwork 合理。我的理解是所有的动作都按照 stage 定义流程」+「合并，一次按最终目标推进」
- 核心设计决策（用户拍板）：
  - **State 归属**：triage-stage 选 B 方案（幂等不持久化）——不写 state.json，每次新对话按用户原始消息重跑，结果应一致；降低 IO 写入，提升效率
  - **INIT 也 Stage 化**：作为独立的会话级 Stage（init-stage）；从根本上消除"游离的 PMO 编排"概念
  - **Stage 体系扩展为三层级**：会话级 / 流程级 / Feature 级，每层有自己的状态归属规则
  - INIT.md 处理选 B（git mv + 引用迁移），不留 redirect 双源
  - SKILL.md 文件索引明确分层标注，让读者一眼看出三层级
  - stages/ 不分子目录（避免引用路径变化）
  - 红线数保持 15 条不变（红线 #4 / #11 / #15 现在是 Triage Stage 的强制力来源，措辞调整指向契约）
- 处理（9 处改造）：
  - **A. 新建 `stages/triage-stage.md`**（~280 行流程级 Stage 三契约）：
    - Input Contract：用户原始消息 / 项目空间状态 / KNOWLEDGE.md / ADR 索引 / 探测脚本输出 / Workspace Feature 状态
    - Process Contract（9 步）：用户输入承接 / KNOWLEDGE 扫描 / ADR 索引扫描 / 外部模型探测 / 流程类型识别 / 跨 Feature 冲突检查 / 流程步骤描述 / 暂停点呈现 / 用户回数字 → 创建 Feature 占位
    - Output Contract：主对话输出（不落盘）+ 用户确认后写入 Feature state.json
    - 机器可校验条件 7 项 + 幂等性保证说明
    - 失败 / 异常处理表（探测脚本失败 / KNOWLEDGE.md 不存在 / 用户消息无法识别 / 跨 Feature 冲突）
    - AI Plan 模式 + 入口 Read 顺序 + 与其他 Stage / 文件的关系
  - **B. INIT.md → `stages/init-stage.md`**（git mv + 三契约外壳）：
    - 头部加会话级 Stage 定位声明 + Input/Process/Output 三契约外壳
    - 「启动必做」段保留作为 Process Contract 的 9 步（v7.3.10+P0-26 标注）
    - 末尾追加 Output Contract 段（4 项必产出 + 唯一允许的写：teamwork_version 缓存）+ 出口决策表 + AI Plan 指引 + 失败处理 + 与其他 Stage 关系
  - **C. INIT.md 全文引用迁移**（10 个文件）：
    - 活引用全清：`SKILL.md` (5 处) / `STATUS-LINE.md` / `standards/external-model.md` / `standards/prompt-cache.md` (2 处) / `roles/pmo.md` / `RULES.md` / `agents/README.md` / `templates/detect-external-model.py` 注释 / `stages/init-stage.md` 自引用
    - `INIT.md` → `stages/init-stage.md`（链接路径同步调整）
    - 历史 docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md 中的 INIT.md 引用保留（历史记录不动）
  - **D. `roles/pmo.md` 反向引用**（4 段）：
    - 「外部模型交叉评审开关决策」段 → 加 🔗 反向引用到 triage-stage Step 4
    - 「ADR 索引扫描」段 → 加 🔗 反向引用到 triage-stage Step 3
    - 「KNOWLEDGE 扫描 + 写入时机」段 → 加 🔗 反向引用到 triage-stage Step 2 + Stage 完成节点
    - 「跨项目依赖识别」段 → 加 🔗 反向引用到 triage-stage Step 6
    - **不删除原内容** —— roles 是 PMO 角色技术细节，stages 是阶段 IO 契约，两者互补
  - **E. `FLOWS.md` PMO 初步分析输出格式段**：加 🔗 反向引用到 triage-stage Output Contract（保留具体 markdown 渲染细节）
  - **F. `RULES.md` PMO 承接规则**：
    - 标题改为 → 红线 #4 / #11 / #15
    - 加 🔗 三条红线共同构成 Triage Stage 强制力来源
    - 流程描述改为「用户输入 → 进入 Triage Stage → ...」明确 Stage 化
  - **G. `SKILL.md` 文件索引升级**：
    - 加 stages/triage-stage.md 行
    - init-stage.md 行升级标注「会话级 Stage」
    - 加新章节「Stage 三层级体系」明确分层
  - **H. `rules/flow-transitions.md` 加新章节「会话级 + 流程级 Stage」**：
    - 表格定义会话启动 → init-stage → 等待用户输入 → triage-stage → Feature 级 Stage 的转移路径
    - Feature 流程表头改为从 triage-stage 出发（取代原 PMO 初步分析）
  - **I. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-25 → 7.3.10+P0-26；stages/init-stage.md L111 同步
- 风险控制：
  - 红线数保持 15 条（无升格 / 无新增）
  - Triage Stage 幂等不持久化 —— 新对话恢复无歧义（重跑即可）
  - INIT.md 文件迁移用 git mv，引用同步全文 grep + replace（活引用 100% 清零，历史 docs 保留）
  - roles/pmo.md 不删除原段，只加反向引用 —— 避免破坏其他文件对 pmo.md 段的引用
  - SKILL.md 三层级标注让概念体系一眼可见，避免新用户混淆
- 影响面：
  - 新建文件：1 个（stages/triage-stage.md）
  - 物理重命名：1 个（INIT.md → stages/init-stage.md）
  - 引用迁移：10 个文件（活引用全清）
  - 反向引用增加：4 段（roles/pmo.md）+ 1 段（FLOWS.md）+ 1 段（RULES.md）
  - 索引更新：SKILL.md（加新 Stage 行 + 三层级章节）+ rules/flow-transitions.md（加新章节）
- 预期效果：
  - **架构一致性**：所有 PMO 行为都走 Stage 契约（三层级覆盖完整）
  - **可审计 / 可恢复**：triage 输出标准化，新对话重跑幂等，结果一致
  - **概念清晰**：Stage 分会话级 / 流程级 / Feature 级，三层职责清晰
  - **token 友好**：triage 不持久化降低 IO 写入开销
- 待跟进（非 P0-26 范围）：
  - triage-stage 在实际跑 Feature 时的 token 占用观察（如超过预期可优化为按需加载 KNOWLEDGE 章节）
  - 若未来加 Gemini 等候选外部模型时，triage Step 4 的 detect 脚本扩展（已预留）
  - INIT.md 历史引用在 docs/CHANGELOG.md / docs/OPTIMIZATION-PLAN.md 中保留 —— 这是预期行为（历史记录），不动

---

## v7.3.10 + P0-25

> v7.3.10+P0-25 Build 硬门禁补丁：用户实战中遇到 CI 失败"npm run build 失败"——RD 自查时单测都跑通了但 build 没跑过，CI 成了第一道发现机制。诊断后发现规范半残：standards/common.md 自查报告**字段层**已要求填 build 命令 + 结果（soft requirement），但 stages/dev-stage.md Output Contract 的**机器校验硬门禁**只到 typecheck，没有 build。同时暴露 worktree 场景下 lazy install (P0-3) 的 hole——单测 deps 装了但 build 工具链 deps 未装，build 在 worktree 内根本跑不起来。本次把 build 升格为硬门禁，并补充 worktree 场景的 deps 处理选项。

### P0-25：Build 升格硬门禁 + worktree deps 处理

- 触发：用户实战 case「CI 应可重新跑通，next build 必须能在 RD 自查阶段跑通，不能依赖 CI 兜底。后续 Feature 若 worktree 缺 deps，应至少符号链接 / 安装一份后跑 next build 而非只跑单测」 → 用户「A + B + D」选定
- 设计决策：
  - 不修改 P0-3 lazy install 模型（仍然懒装，避免回退冷启时间优化）
  - 把 build 从"自查报告字段"升格为"Dev Stage Output Contract 机器校验硬门禁"——build 失败 = Dev Stage 不能完成 = PMO 拦下来不让进 Review
  - 纯库 / 纯后端 / Python 应用允许显式标注"无 build 步骤"，避免误中
  - worktree deps 处理给 3 种选项（按优先级 install > 软链 > 写 KNOWLEDGE），不强制其中一种——视项目情况
- 处理（2 处改造）：
  - **A. `stages/dev-stage.md` Output Contract 机器校验硬门禁**：
    - 在 typecheck 行后加一条 `[ ] Build：npm run build / next build / go build / cargo build 等 exit 0`
    - 加一段 callout：🔴 Build 必须 RD 阶段跑通，禁止依赖 CI 兜底；🟡 worktree lazy install hole 的处理指引指向 standards/common.md
  - **B. `standards/common.md` 验证证据段加 worktree 提示**：
    - 在「构建结果」行下加 🔴 升格硬门禁声明
    - 加 🟡 worktree 场景特别提示：症状（单测可跑 build 失败）+ 原因（lazy install + worktree 不同步）+ 3 种处理选项（npm install / 软链 / 写 KNOWLEDGE Gotcha）
    - 自查结论改为"含 build 通过"
- 风险控制：
  - 纯后端 / 纯 Python 项目允许"无 build 步骤"显式标注，不会误伤
  - worktree 场景给选项不强制——保留 RD 判断空间
- 影响面：
  - 红线数：15 条（保持，未升格新红线，build 是 Dev Stage Output Contract 的机器校验项升格）
  - 改动文件：2 个（stages/dev-stage.md / standards/common.md）
  - 元数据：SKILL.md frontmatter v7.3.10+P0-24 → v7.3.10+P0-25；INIT.md L111 同步
- 待跟进（非 P0-25 范围）：
  - PMO L2 预检加 build deps 检查（暂列 P0-25-延后，等真有 case 再做）
  - 复杂 monorepo workspace 场景下 worktree node_modules 软链的具体踩坑（视实战补充）

---

## v7.3.10 + P0-24

> v7.3.10+P0-24 外部模型 (External Model) 抽象化重构：将 v7.3.9+P0-13 引入的"Codex 交叉评审"语义升级为通用的"外部模型交叉评审"概念。规范层不再硬编码"宿主→外部模型"对应表，改为 PMO 在每次 Feature 流程的初步分析阶段调用 `templates/detect-external-model.py` 探测脚本，按当时环境（CLI 安装情况 + 同源约束）决定可用候选 + 用户决策。配套实现：claude-agents/ 目录建立（Codex CLI 主对话调用 Claude CLI 子进程的 shell 调用规范），state.json 字段 codex_cross_review → external_cross_review（旧字段 fallback 兼容），STATUS-LINE 加 [Ext: X] 徽章，Review Stage 入口显式宣告外部模型实例。改造后 Codex CLI 主对话宿主下可用 Claude 作为外部模型（之前用 Codex 等于"自审"），Claude Code 主对话宿主下保持 Codex 为外部模型不变。

### P0-24：外部模型抽象化 + PMO 运行时探测

- 触发：用户「我们是否把 codex 评审 review 语义改为 外部模型交叉评审，外部模型由当前宿主环境定义」 → 进一步细化「PMO 运行时探测，使用固定 python 脚本探测，简单直接，目前仅支持 codex 和 claude」 → 用户「确认」开干
- 设计决策：
  - 规范层只定义"候选清单 + 同源约束 + 调用规范 + 失败降级"，**不写宿主对应表**——具体实例由 PMO 运行时决定
  - 探测脚本只检测 CLI 安装 + 同源约束，**不查 API key/OAuth**（避免 OAuth 已登录但 env var 未设的用户被误标"不可用"）
  - 失败检测延后到运行时：dispatch 时调用失败 → state.concerns WARN → 自动降级单视角 review
  - 红线数量保持 15 条（P0-24 的"E1 异质性 / E2 PMO 运行时探测 / E3 失败优雅降级"三规则纳入 standards/external-model.md，不升格红线）
- 处理（新建 5 文件 + 9 处改造）：
  - **A. 新建 `templates/detect-external-model.py`**（~130 行）：
    - CANDIDATES = [codex, claude]，未来加 Gemini 只需加一行
    - 探测主对话宿主（基于 .claude/ / .codex/ / .agents/ 目录标记）
    - 探测候选 CLI 是否在 PATH（shutil.which）
    - 应用同源约束（外部模型 ≠ 主对话同源）
    - 输出 JSON 到 stdout：host_main_model / candidates_pool / available_external / recommendation
  - **B. 新建 `standards/external-model.md`**（~190 行）：
    - 顶部三条硬规则（E1 异质性 / E2 PMO 运行时探测 / E3 失败优雅降级）
    - §一：外部模型概念（异质模型 vs 同模型角色切换的本质差异）
    - §二：候选模型清单（Codex / Claude）
    - §三 E1：同源约束 + 渲染示例
    - §四 E2：PMO 运行时探测（脚本调用 + 输出渲染 + 设计边界说明）
    - §五：调用规范（dispatch 文件协议 + 调用入口对应表 + 产物格式 + state.json 字段）
    - §六 E3：失败降级流程
    - §七：与其他规范的协作关系
    - §八：本规范不覆盖的范围
  - **C. 新建 `claude-agents/` 目录**（3 个文件）：
    - README.md：宿主对应、前置条件、调用方式总览、与 codex-agents/ 的对照
    - reviewer.md：外部 review 的 prompt 模板（PRD / Blueprint / 代码三场景共用）
    - invoke.md：主对话 shell 调用 claude CLI 的命令范本 + stderr 捕获 + 降级处理
  - **D. SKILL.md + STANDARDS.md 索引更新**：加 standards/external-model.md 行 + standards/external-model.md 在 STANDARDS.md
  - **E. INIT.md 简化**：删除原"Codex CLI 检测"段（line 314-319），改为"外部模型探测延后说明"——明确外部模型探测延后到 PMO 在 Feature 流程的初步分析阶段做，INIT 阶段只检测主对话宿主
  - **F. roles/pmo.md 重写「外部模型交叉评审开关决策」段**（替换原"Codex 交叉评审开关决策"段）：
    - Step 1: PMO 调用 detect-external-model.py
    - Step 2: PMO 渲染「🌐 外部模型探测」段
    - Step 3: PMO 建议逻辑（沿用 P0-13 的开/关信号判断）
    - Step 4: PMO 决策项呈现（有候选时 3 选 1，无候选时直接跳过）
    - Step 5: 用户选择 → state.json 写入新字段 schema
    - Step 6: 调用失败的运行时降级（E3 规则）
    - 兼容性：旧 codex_cross_review 字段 fallback 读取
    - 9 条硬规则（含同源禁用 + 静默降级禁止）
  - **G. templates/feature-state.json 字段重命名 + 新字段**：
    - codex_cross_review → external_cross_review
    - 新增字段：model / host_main_model / host_detection_at / available_external_clis / reviewer_dispatches[]
    - 保留 _p0_24_rename_note 注释说明旧字段语义
  - **H. templates/codex-cross-review.md → templates/external-cross-review.md 重命名 + 重写**：
    - 头部加 P0-24 重命名说明 + 指向 standards/external-model.md
    - §一-§九 全文措辞由"Codex 交叉评审"→"外部模型交叉评审"
    - Output Schema 改为 perspective: external-{model}（external-codex / external-claude）
    - PMO 整合流程 Step 2 "Dispatch Codex" → "Dispatch 外部模型"（按 model 选择 codex / claude CLI）
    - §六 降级策略与 standards/external-model.md §六 E3 对齐
    - 加 R9 红线（同源禁用）
  - **I. 8 个 stage spec + FLOWS.md + review-log.jsonl 字面值审查**：
    - codex_cross_review → external_cross_review（字段名）
    - templates/codex-cross-review.md → templates/external-cross-review.md（路径）
    - "Codex 交叉评审" → "外部模型交叉评审"（概念名）
    - prd-codex-review.md / blueprint-codex-review.md → external-cross-review/prd-{model}.md / blueprint-{model}.md（产物路径）
    - review-codex.md → review-external.md（Review Stage 外部产物）
    - "Codex 已关闭" → "外部模型评审已关闭"
    - review-log.jsonl stage 枚举：plan-codex-review / blueprint-codex-review / review-codex → plan-external-review / blueprint-external-review / review-external
  - **J. STATUS-LINE.md 加 [🌐 Ext: X] 徽章**：
    - 第一行格式：🔄 Teamwork 模式 [⚡ AUTO] [🌐 Ext: {model}] | ...
    - 触发条件：state.external_cross_review.enabled=true 时显示，model 取自 state 字段
    - 兼容旧字段：fallback 显示 "Ext: codex"
  - **K. stages/review-stage.md 入口宣告外部模型实例**：在「入口 Read 顺序」段下方加一行 PMO 在读 state.json 后输出"🌐 外部模型: {model}"
  - **L. CHANGELOG + 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-23 → 7.3.10+P0-24；INIT.md L111 同步
- 风险控制：
  - state.json 字段重命名采用 fallback 兼容（PMO 读取时优先读新字段，缺失时读旧字段并视为 model=codex）—— 旧 Feature 不需要迁移
  - claude-agents/ 真实工程（不是占位骨架），但失败降级路径完备：调用失败 → state.concerns WARN → 单视角 review，不阻塞流程
  - 同源约束在脚本层 + PMO 决策层双重保护：脚本输出 usable_as_external=false，PMO 渲染时不出该选项
  - 测试路径：用户在 Codex CLI 环境跑 Teamwork → 启用外部模型交叉评审 → 验证 claude CLI 子进程被调起 → 验证 review 产物正确落盘
- 影响面：
  - 红线数：15 条（保持，未升格）
  - 新建文件：5 个（detect-external-model.py / external-model.md / claude-agents/README.md / claude-agents/reviewer.md / claude-agents/invoke.md）
  - 重命名：1 个（codex-cross-review.md → external-cross-review.md）
  - 重大改动文件：roles/pmo.md（重写一段约 130 行）/ templates/feature-state.json（字段重构）
  - 字面值改动：8 个 stage spec + FLOWS.md + review-log.jsonl + STATUS-LINE.md
- 待跟进（非 P0-24 范围）：
  - claude-agents/ 在 Codex CLI 实际跑通的端到端测试（用户自测）
  - localconfig external_model 字段（用户覆盖默认推荐）
  - 未来加 Gemini 候选时的扩展（detect-external-model.py 的 CANDIDATES 加一行 + claude-agents/ 对称建立 gemini-agents/）

---

## v7.3.10 + P0-23

> v7.3.10+P0-23 Prompt Cache 友好改造（R1+R2+R3 子集）：teamwork 在 Claude Code / Codex 等宿主下跑时，宿主会自动做隐式 prompt caching（前缀命中则按 ~10% 价格 + ~5x 速度计费）；teamwork 原先的 prompt 组织方式未优化命中率——动态内容（日期/git/state.json）散落在稳定层中、Stage 入口 Read 顺序不固定、state.json 中段反复读写。按用户「针对 teamwork prompt caching 怎么改造」→ R1-R7 改造清单 → 用户「先落 R1+R2+R3」定稿：R1 动态内容后置（稳定层禁止字面值时间/git/身份/状态/环境）+ R2 Stage 入口 Read 顺序固定化（roles → templates → Feature 产物 → state.json 最后）+ R3 state.json 访问 ≤ 5 次/Stage（入口 1R + 出口 1R + 1W，中段 0，豁免仅评审循环/Subagent 整合/用户追加）。按 Anthropic 公开数据，Feature 输入 ≥50K token 场景命中率 20% → 80% 改造收益 ≈ 成本下降 2-3 倍。

### P0-23：Prompt Cache 友好 R1+R2+R3 落地

- 触发：用户「针对 teamwork prompt caching 怎么改造」→ 分层分析 L0/L1/L2/L3 + 3 大 cache miss 源（动态前缀/state.json 穿透/Read 顺序不固定）→ R1-R7 改造清单 → 用户「先落 R1+R2+R3」
- 理论依据：Anthropic 公开文档（Claude Code / Codex 宿主自动 prompt caching，前缀稳定 ≥ 1024 token + 字节一致时命中 → input token ~10% 计费 + ~5x 解码速度）
- 设计决策：
  - 只做 R1+R2+R3（显式高 ROI），R4-R7（多指令文件合并/subagent 组装/token 峰值瘦身/审计自动化）暂缓 → 避免过度改造
  - 不触碰 Anthropic API `cache_control` 显式 breakpoint（宿主接管层级，skill 不干预）
  - 红线数量保持 15 条（P0-23 的 3 条性能规则纳入 standards/prompt-cache.md，不升格红线——因违反不产生流程偏离，仅 cache miss，记入 state.concerns 即可）
- 处理（新建 1 文件 + 12 处改造）：
  - **A. 新建 `standards/prompt-cache.md`**（~170 行）：
    - 顶部红线定位 + 三条硬规则（R1/R2/R3）+ ROI 锚点（Feature 场景 50K token 20%→80% 改造 ≈ 2-3x 成本下降）
    - §一：4 层模型（L0 框架 / L1 项目 / L2 Feature / L3 动态）
    - §二 R1：7 类禁止字面值（时间/git/身份/状态/环境/会话）+ 错误 vs 正确表达表 + 允许承载位置（STATUS-LINE / PMO 输出块 / tool call 结果 / Subagent dispatch）
    - §三 R2：通用入口 Read 顺序（roles → templates → Feature 产物 → state.json 最后），每个 stage spec 补「入口 Read 顺序」段
    - §四 R3：state.json 访问次数表（入口 1R + 中段 0 + 出口 1R + 1W）+ 3 类豁免（评审循环 ≤3 轮 / Subagent 整合 / 用户追加）+ 量化上限 ≤5 次常规 / ≤8 次极端
    - §五：审计清单（grep 时间字面值 / stage spec 入口段存在 / PMO state.json 约束 / 中段禁写豁免标注）
    - §六：与 SKILL/RULES/common/INIT 的协作关系
    - §七：明确不覆盖（API-level cache_control / 跨 session 持久化 / subagent prompt 组装 / token 峰值瘦身）
  - **B. `SKILL.md` 文档表新增 prompt-cache.md 行**（责任人：PMO 每 Stage 入口引用约束）
  - **C. `RULES.md` 拆分文件索引新增 prompt-cache.md 行**（时机：PMO 每 Stage 入口 + 审计自查时）
  - **D. 10 个 stage spec 在 Input Contract 与 Process Contract 之间新增「入口 Read 顺序（v7.3.10+P0-23 固定）」段**：
    - plan / blueprint / blueprint-lite / ui-design / panorama-design / dev / review / test / browser-e2e / ship
    - 每段含 4 步固定顺序（角色 → 模板 → Feature 产物 → state.json 最后）+ R3 访问次数约束说明
    - 各 Stage 按特性标注豁免情形（Blueprint/Review 3 轮修复循环；Dev/Test 多次 Subagent dispatch 整合）
  - **E. `roles/pmo.md` §state.json 状态机维护规范 新增子段 state.json 访问模式约束**（紧接「Stage 结束必做」后，「state.json 与现有文件的关系」前）：
    - 4 行访问次数表（Stage 入口 1R / 中段 0 / Stage 出口 1R + 1W）
    - 3 类豁免条件（评审循环/Subagent 整合/用户追加）+ 量化上限 ≤5/≤8
    - 4 条反模式（每 Step 开头 Read / 每字段 Write / 保险再 Read / 中段兜底 Read）
  - **F. `INIT.md` CLAUDE.md 注入段审计**：逐行审计 L170-207 → 结果**清洁**（无日期/git/身份/state 值动态字面值）；版本号类型 `v7.3.10+P0-20/P0-15` 属稳定引用（符合 R1 §2.2）；保留不变
  - **G. 版本号 bump**：SKILL.md frontmatter 7.3.10+P0-22 → 7.3.10+P0-23；INIT.md L111 同步
- 影响：
  - 典型 Feature 场景（50K token 输入）命中率从 ~20% 提升到预期 ~70-80%（实测需生产数据验证）
  - 每 Stage 入口 Read 顺序统一 → 跨 Stage 切换时的前缀碎片化消除
  - state.json 中段禁读写 → 前缀稳定段结束点清晰化，下游 L3 动态内容明确后置
  - 红线条数保持 15 条（P0-23 未增红线，仅新增性能规则 standards/）
  - 无迁移成本（纯注解+约束，不改现有文件语义）
  - 改造范围：1 新文件 + 12 处编辑（3 索引文件 + 10 stage + 1 pmo + 1 version）
- 风险控制：
  - ⚠️ 违反 R3（中段读写 state.json）不触发红线机制 → 仅记 state.concerns（cache miss 自然反映在延迟/成本，不做硬阻塞）
  - ⚠️ 用户追加需求导致中段 Read/Write 豁免合规（必须先走 PMO 分析 + 用户确认）
  - ⚠️ Subagent dispatch 整合写 state.json 豁免必须每次 dispatch ≤ 1 次（否则打破 prompt 前缀一致性）
- 待观察 / 后续可能动作：
  - R4（多指令文件 CLAUDE.md + AGENTS.md 合并）— 若后续发现跨宿主启动命中率仍低，考虑两个文件合并
  - R5（subagent dispatch prompt 组装优化）— 等 dispatch.md 下次 revamp 时同步
  - R6（token 峰值瘦身）— 独立优化路径，与命中率无关
  - R7（审计自动化 - grep 规则跑 CI）— 待 skill-creator evals 建成后接入

---

## v7.3.10 + P0-22

> v7.3.10+P0-22 KNOWLEDGE.md 收敛 + retros 索引拆离：P0-21 落地混合 ADR 后，用户追问「KNOWLEDGE.md 还有必要么，是否需要精简」——审视当前模板确认：它把"架构决策（为什么选某方案）"明确写在🔧技术经验首项，与新的 ADR 体系直接抢地盘；把复盘索引和经验索引混塞；PMO 知识提取仅靠软提示易失活。按**方案 A**（收敛保留，非删除）落：KNOWLEDGE.md 收敛到 3 类纯"事实型"内容——⚠️ Gotchas（陷阱）/ 📋 Conventions（团队约定）/ 🎨 Preferences（用户偏好），明确"决策走 ADR / 复盘走 retros / 通用规范走 standards"的边界；复盘索引剥离到独立 `templates/retros-index.md`；PMO 新增📚 KNOWLEDGE 扫描段（与 ADR 扫描对称）+ 7 条硬触发时机表（从软提示升硬时机）；体量上限 300 行强制归档。

### P0-22：KNOWLEDGE.md 3 类收敛 + 硬触发时机 + 复盘索引剥离

- 触发：用户「我们的 KNOWLEDGE.md 还有必要么，是否需要精简下」→ 分析当前模板 3 大冗余问题 → 3 方案（A 收敛保留 / B 激进拆散 / C 最小改动）→ 用户「按 A 落地」
- 根因分析：
  - ADR 体系（P0-21）落地后，KNOWLEDGE.md 仍在🔧技术经验段收录"架构决策（为什么选某方案）"，和 ADR 直接抢领域 → 同一决策可能双写/漂移
  - KNOWLEDGE.md 同时承担「经验索引」+「复盘索引」两种不同时间语义的信息（主题复用 vs 时间回顾）→ 文件职责不纯
  - 当前 PMO 知识提取靠软提示（"功能完成时应基于以下维度总结"），没有硬时机约束 → 实际运行下绝大多数 Feature 完成时不会真提取 → 慢慢失活
  - 模板分类过细（8 大类 20+ 小项），AI 实际写入时犹豫"这条算技术还是流程"，同一条知识被写到多个位置
  - 无体量上限 → 长期容易变成"什么都往里塞"的垃圾桶
- 处理（模板重写 + 新模板 + PMO 专属段新增 + 3 处活引用 + 索引 2 处）：
  - **A. `templates/knowledge.md` 全文重写**：
    - 顶部新增「🔴 边界声明」表：明确架构决策→ADR / 通用规范→standards / 复盘→retros / 项目特有事实→本文件
    - 正文收敛到 3 类表格：⚠️ Gotchas (GO-NNN) / 📋 Conventions (CV-NNN) / 🎨 Preferences (PR-NNN)，每条都有 ID + 主题 + 来源 Feature + 时间
    - 按主题索引段（db / api / auth / frontend / UI / 交互 / ...）
    - 归档段（archived）：过期条目加 archived 标记保留备查
    - 🔴 体量上限 300 行（超出必选一种处理：升格 ADR / 子项目级分拆 / 归档）
    - 🔴 每条 ≤ 2 行（超出说明不够"事实"，可能是决策伪装）
    - ID 编号连续不复用（归档保留原 ID）
  - **B. `templates/retros-index.md` 新增**（~50 行）：复盘索引模板
    - 时间线段（最近在前）+ 按流程类型索引 + 偏差警报段（Stage 连续偏差 ≥ 3 次触发流程优化 proposal）
    - 位置：`{子项目}/docs/retros/INDEX.md`（和 `docs/adr/INDEX.md` 对称）
    - 维护约定：每次产单条复盘时同步 INDEX；体量上限 200 行
  - **C. `roles/pmo.md` 新增 §📚 KNOWLEDGE 扫描 + 写入时机**（紧接 ADR 扫描段后）：
    - 定位声明：3 类收录 + 4 类排除（决策/通用规范/复盘/临时笔记）
    - **A. preflight 扫描**（读操作）：4 步操作 + 输出格式 + 3 条硬规则（必出行 / ≤300 行 / 只列清单不下结论）
    - **B. 写入硬时机表**（7 条触发场景 × 类别 × 写入方 × PMO 提示措辞）：
      1. Bug 修复完成 → Gotcha → RD
      2. Dev Stage 调试 ≥30min 或 retry ≥2 → Gotcha → RD
      3. Review 发现 workaround → Gotcha → 架构师
      4. Review 发现自发约定 → Convention → 架构师
      5. Plan 用户强调跨 Feature 要求 → Convention → PM
      6. PM 验收用户明确偏好 → Preference → PM
      7. UI Design 用户选项陈述理由 → Preference → Designer
    - 🔴 PMO 显式提示即完成其职责；对应角色未写入 → state.concerns 记 skip_reason
    - 🟢 PMO 本身不直接写入 KNOWLEDGE（除流程型 Convention 外）
    - 反模式表 6 行（遗漏扫描行 / 读全文 / 决策写入 Gotcha / 通用规范写入 Convention / Bug 后漏提示 / 超体量继续追加）
  - **D. `FLOWS.md` 三种 PMO 初步分析格式**均新增「📚 相关项目事实（KNOWLEDGE）」行（单子项目 Feature / 工作区级 Feature Planning / 敏捷需求）
  - **E. 索引同步**：
    - `TEMPLATES.md`：knowledge.md 描述更新 + 新增 retros-index.md 行
    - `templates/README.md`：knowledge.md 描述 + 加载时机细化；新增 retros-index.md 行
- 版本号：
  - SKILL.md frontmatter：`7.3.10+P0-21` → `7.3.10+P0-22`
  - INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **收敛而非删除**：KNOWLEDGE 有独立价值（项目特有事实 + 偏好）不能丢，但要和 ADR 清晰分工
  - **3 类硬隔离**：Gotchas / Conventions / Preferences 三段完全独立，有 ID 段 + 主题索引 → 不再纠结"这条写哪"
  - **决策 vs 事实的边界**：备选项 ≥ 2 → ADR；被动发现的客观约束 → KNOWLEDGE Gotcha；这是最关键的分流规则
  - **硬时机取代软提示**：7 条写入时机绑定到 Stage 完成报告，PMO 提示是硬职责；未提示 = 流程偏离
  - **体量上限 = 扫描上限**：300 行一口气读完，不用分页；超出必归档 → 文件不会膨胀
  - **复盘独立索引**：时间线语义（retros）和主题语义（KNOWLEDGE）彻底分离，和 ADR-INDEX 形成"3 套索引"对称结构
  - **零新红线**：总红线数仍 15 条；所有约束落在 PMO 专属规范 + 模板硬规则里
  - **与 ADR 的协作**：ADR 记"为什么选了这个"，KNOWLEDGE Gotcha 记"选了之后踩了什么坑"——两者互补
- 保留未做（后续可能 P0/P1）：
  - KNOWLEDGE.md 自动校验脚本（verify-knowledge.py）：ID 连续性、主题索引完整性、体量上限 → 当前手工
  - 跨项目 KNOWLEDGE 聚合视图：多子项目模式下全局概览，当前各子项目独立维护
  - 归档条目的定期回顾机制：archived 条目是否真的不适用，需要多版本验证
  - Bug 修复流程 Stage spec 是否在完成报告明确要求"PMO 提示写 Gotcha"的声明格式 → 当前靠 roles/pmo.md 硬时机表约束，未在 bug-stage 单独落硬规则
  - Review Stage spec 是否在 findings 分类里新增"trigger_knowledge_write"标记 → 当前靠架构师读 roles/pmo.md 硬时机表自觉执行

## v7.3.10 + P0-21

> v7.3.10+P0-21 混合 ADR（Architecture Decision Record）体系：用户追问"TECH.md 接近但不是 ADR 语义（Context / Decision Drivers / Alternatives ≥ 2 / Consequences），teamwork 需要补充完善么"——分析后确认：TECH.md 混合了"怎么做（实现计划）"和"为什么这么选（决策记录）"两类信息，当跨 Feature 引用决策时（"用户系统当初选 PostgreSQL 是为了什么"）没有稳定引用点；但强制每 Feature 产 ADR 会把轻量流程拖垮。按**方案 C 混合 ADR**落：ADR 作为可选产物，由架构师在 Blueprint Stage 用"3 问触发器"判断是否抽取（影响未来 ≥1 Feature / 反悔成本高 / 多合理方案非显然 —— 三问全 yes 才产）。TECH.md 保持不变是实现计划的主体，决策则被抽离到独立 `{子项目}/docs/adr/NNNN-{slug}.md`，PMO 初步分析阶段扫描 INDEX.md 让未来 Feature 自动感知既有决策约束——这是 ADR 对 AI 自引用最关键的价值。

### P0-21：混合 ADR 体系（opt-in 决策记录 + 3 问触发器 + PMO 索引扫描）

- 触发：用户「文档即代码（ADR / RFC）：TECH.md 接近但不是 ADR 语义（ADR 要求决策记录 + 备选项 + 后果）这个 teamwork 需要补充完善么」→ 评估三方案 A（TECH.md 内嵌）/ B（全面 ADR）/ C（混合 opt-in）→ 用户「按方案 C 落」
- 根因分析：
  - TECH.md 实际承担两类信息：「实现计划」（文件清单 + 改动要点 + 测试策略）+「技术决策」（为什么选 A 不选 B）——两者耦合导致跨 Feature 引用决策时没有稳定锚点
  - 未来 Feature 的 AI 想知道"本项目为什么当初选 PostgreSQL"只能全文搜索所有历史 TECH.md，没有索引也没有按主题聚合
  - 全面强制 ADR（方案 B）会让小 Feature 额外付 ~50-100 行 ADR 成本 → 流程不可持续；完全不加（方案 A）无法解决跨 Feature 决策引用问题
  - 合理的解法：opt-in + 触发器 + 索引聚合 → 只有真正影响未来 / 反悔成本高 / 多方案非显然的决策才升格 ADR
- 处理（2 个新模板 + 4 处活引用 + 1 条工作流）：
  - **A. 新增 `templates/adr.md`**（~120 行）：完整 ADR 模板
    - frontmatter 7 字段：`id` / `title` / `status`(proposed|accepted|deprecated|superseded-by-ADR-NNNN) / `date` / `tags[]` / `triggered_by`(触发 Feature) / `supersedes[]`
    - 正文 7 段：背景 / 决策驱动因素 / 备选项（≥ 2） / 决策 / 后果（✅ 正面 / ⚠️ 负面 / 🔗 长期 / ❓ 未解决）/ 相关 / 修订历史
    - 硬规则：ID 连续编号永不复用、备选项 < 2 走 TECH.md 不走 ADR、每次变更同步 INDEX.md、superseded 时双向关联、体量 50-150 行
  - **B. 新增 `templates/adr-index.md`**（~65 行）：ADR 索引模板
    - 三段：活跃决策（Accepted） / 提案中（Proposed） / 已废弃（Deprecated / Superseded）
    - 按主题索引：db / api / auth / frontend / backend / deploy / observability / security
    - 位置：`{子项目}/docs/adr/INDEX.md`（每子项目一份）
    - 体量上限 200 行，超出说明需分片
  - **C. `stages/blueprint-stage.md` §架构师方案评审**（Step 4 增子步 + Step 6 新增 + 硬规则 +2 + Output Contract +2 行 + 判据 +4 项）：
    - **Step 4.1 ADR 抽取判断**：架构师必须对本 Feature 每条技术决策应用"3 问触发器"——
      1. 这个决策会影响 ≥ 1 个未来 Feature 吗？
      2. 反悔成本很高吗（需要大规模改动）？
      3. 存在多个合理方案，选哪个不是显然的吗？
      - 三问全 yes → 抽取为独立 ADR；任一 no → 决策留在 TECH.md 即可
      - 🔴 判断本身（包括"不产 ADR 的理由"）必须在 TECH-REVIEW.md 留痕
    - **Step 6 ADR 抽取流程**（Step 5 Codex 之后）：前置（TECH-REVIEW 已记 ADR 判断）/ 架构师 4 步职责（分配 ID / 按模板创建文件 / 填 frontmatter + 正文 / 更新 INDEX.md）/ PMO 流程整合（列摘要 + ⏸️ 用户确认→ status proposed→accepted + 多轮讨论不受 ≤3 轮限制）/ 产出清单 / 体量控制 / 🔴 TECH.md 去重（决策 rationale 迁移后 TECH.md 只留 ADR-ID 引用）
    - **过程硬规则 +2**：🔴 ADR 抽取判断不可跳过（跳过 = 流程偏离） + 🔴 ADR 格式合规（严格按 adr.md 模板、备选项 ≥ 2、同步 INDEX.md）
    - **Output Contract +2 行**：`docs/adr/NNNN-{slug}.md`（🟡 仅触发时必需）+ `docs/adr/INDEX.md`（🟡 首次产 ADR 时创建/每次变更时更新）
    - **机器可校验条件 +5 项**（触发时生效）：frontmatter 5 字段全非空、备选项 ≥ 2、体量 50-150 行、INDEX.md 已同步、文件名 NNNN 连续不复用
    - **Done 判据 +1**：ADR 触发时 status=accepted + INDEX.md 同步 + TECH.md 去重
  - **D. `roles/pmo.md` §📜 ADR 索引扫描**（新段，紧接 Codex 决策段后）：
    - 触发：PMO 初步分析任何 Feature / 敏捷需求 / Feature Planning 时必须扫描
    - 目的：让 PMO 在需求分析阶段就提醒"本 Feature 受哪些历史决策约束"——这是 ADR 对 AI 自引用最关键的价值（不扫描 = AI 重复发明或违反既有决策）
    - 4 步操作：定位 INDEX.md → 读前 200 行 → 按主题 + 涉及模块交叉扫描活跃决策 → 注入初步分析输出
    - 硬规则 4 条：必须显式输出「📜 相关 ADR」行（即使为空）+ 只读 INDEX.md 不读单 ADR 全文 + PMO 不做决策抽取判断（留给架构师）+ 无 ADR 记录时显式声明
    - 反模式表 +3 行：遗漏行 / 读全部 ADR / 替架构师下结论
  - **E. `FLOWS.md` §PMO 初步分析输出格式**：三种格式（单子项目 Feature / 工作区级 Feature Planning / 敏捷需求）均新增「📜 相关 ADR」行；§PMO 初步分析流程步骤描述 Blueprint Stage 改述为"含 💡 ADR 3 问触发器判断"
- 版本号：
  - SKILL.md frontmatter：`7.3.10+P0-20-B` → `7.3.10+P0-21`
  - INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **opt-in 而非强制**：3 问触发器把 ADR 抽取成本精确定位到"跨 Feature 影响 + 反悔成本高 + 非显然"三者同时满足的决策——绝大多数 Feature 一个 ADR 都不用产，流程开销几乎为零
  - **零新红线**：保持总红线数 15 条不变；ADR 约束全部落在 Blueprint Stage 规范 + PMO 专属规范里（而不是升格为全局红线）
  - **PMO 只扫描不判断**：PMO 负责"历史扫描 + 注入"，架构师负责"抽取判断"——两个职责清晰分工，避免 PMO 越权替架构师决策
  - **INDEX.md 体量可控**：200 行上限 + 只读索引不读全文 → 即使项目积累 100 个 ADR，PMO 初步分析阶段的 token 开销也可控
  - **AI 自引用价值最大化**：通过「主题索引 + PMO 每次扫描」让未来 AI Feature 自动感知既有决策约束——这是 ADR 对 LLM 自主开发最关键的贡献
  - **与 TECH.md 去重**：决策 rationale + 备选项 + 后果 → 迁移到 ADR；TECH.md 只留 ADR-ID 引用一句话——避免双份真相
  - **备选项 ≥ 2 的硬门槛**：单方案走 TECH.md 不走 ADR，防止 ADR 被用作"凡决策必记"的形式主义产物
- 保留未做（后续可能 P0/P1）：
  - ADR 状态流转（superseded-by-* 双向关联）的自动化校验脚本：当前靠架构师手工，未来可加 python3 verify-adr.py
  - ADR 搜索/聚合 CLI：INDEX.md 体量够用时搜索基本靠人眼，未来项目 ADR 数量大时再引入
  - Micro 流程是否扫描 ADR：Micro 场景改动极小、准入条件已排除架构变更，当前不加扫描；若未来发现 Micro 漂到边缘决策再补
  - RFC（Request for Comments）体系：ADR 记录「已做的决策」，RFC 用于「待讨论的提案」——当前 TEAMWORK 不引入 RFC，团队内部讨论走 PRD / PL-PM 讨论已足够；未来多 AI 协作场景可能需要

## v7.3.10 + P0-20-B

> v7.3.10+P0-20-B 反漂移双补丁：P0-20 把 Micro 流程里"谁写代码"的语义统一为"主对话内 PMO→RD 身份切换"，但用户追问"身份切换语义模型现在能理解吗"——深究后确认：LLM 可以 parse 这个短语，但"身份切换"不是原子操作（没有进程/状态切换、没有 context 隔离），让切换真正生效靠的是 P0-16 补丁留下的四个仪式（切换前必读 + cite + 改后自查 + STATUS-LINE 显示角色）。仪式全在改动**前后**，改动**过程中**存在两个漂移口：(1) 跨多 turn 悄悄漂回 PMO 口吻；(2) 用户中途追加改动时 RD 身份顺手接单导致身份蠕变。本次补两条轻量规则堵漏。

### P0-20-B：反漂移双补丁（第一人称锚点 + 追加改动回退规则）

- 触发：用户「身份切换语义代表什么现在模型能理解么」→ 回答"语义能懂但靠仪式落地"+ 识别两个漂移口 → 用户"按建议"全做
- 根因分析：
  - 身份切换在 LLM 上是 prompt-level convention，不是 runtime state 切换 → 仅靠"称呼改变"不足以持续约束行为
  - P0-20 保留的 P0-16 四仪式（必读 + cite + 自查 + 状态行）全是**前后**锚点，没有**过程中**锚点
  - 漂移场景 1：Micro 改动跨多 turn 时，模型可能在中间某轮悄悄恢复 PMO 口吻（产出不一定错，但审计痕迹乱）
  - 漂移场景 2：用户中途说"顺便再改一下 X"，RD 身份顺手接单 → 没有 PMO 的 Micro 准入重评 → 身份蠕变、Micro 越扩越大
- 处理（两条规则 + 三处活引用 + 事后审计补两项）：
  - **A. 第一人称锚点**：身份切换后阶段摘要**首句必须以「作为 RD，……」开头**。LLM 在开头强制自称特定角色时，后续 token 生成会显著向该角色的语言分布靠拢——这是反漂移的最小开销锚。
  - **B. 追加改动回退规则**：RD 身份执行过程中若用户追加新改动请求 → 必须跳回 PMO 身份重新做 Micro 准入：
    - 通过 5 项准入 + 仍在白名单内 → PMO 输出增量分析 + ⏸️ 等用户确认 → 再切回 RD 执行
    - 越出白名单 → PMO 输出升级原因 → ⏸️ 用户确认走敏捷或 Feature
    - 🔴 禁止在 RD 身份下直接接收新需求
  - 活引用三处（A+B 同步写入）：
    - **FLOWS.md §六 Micro 流程规则 L954-965**：强制规则块头部更新版本标记到 `v7.3.10+P0-20-B 补两条反漂移规则`；在 cite 规则之后插入 🔴 第一人称锚点 + 🔴 追加改动回退规则（带 3 项子流程分支）两条硬规则
    - **FLOWS.md §六 Micro 事后审计**：新增 2 项 checklist——"身份切换第一人称锚点是否写入首句" + "执行中是否发生追加改动、若是是否跳回 PMO 准入"
    - **roles/pmo.md L5 Micro 头部段**：在 P0-16 必读子句后追加"🔴 第一人称锚点（P0-20-B）" + "🔴 追加改动回退规则（P0-20-B）"；完整闭环表述里加入「RD 改动（「作为 RD，…」锚句开头）」
    - **roles/pmo.md L1381-1382 反模式表**：新增两行——"RD 身份途中用户顺便追加改动 → 直接顺手改了" 和 "身份切换后用'我'/'PMO'/泛指" 对应 🔴 正确做法
    - **rules/flow-transitions.md Micro preamble**：在 P0-16 必读硬规则后追加一条 🔴 **反漂移双补丁（P0-20-B）** 复合规则（第一人称锚点 + 追加改动回退）
  - 版本号：SKILL.md frontmatter `7.3.10+P0-20` → `7.3.10+P0-20-B`；INIT.md Step 1.2-a 注释同步
- 设计要点：
  - **零新流程**：没有加 Stage、没有改流转图、没有新红线条目——全部在现有 Micro 规则块内补条款
  - **最低侵入**：第一人称锚点只是一句话约束，追加改动回退只是路由规则，不需要新的 state 字段
  - **可审计**：两条规则都能在事后审计 checklist 里直接检查（首句是否以"作为 RD，"开头 / 执行过程中有无追加改动且是否跳回 PMO）
  - **行为面提升**：堵了真实会发生的两个漂移口，特别是 B（"顺便"追加）——这是 Micro 蠕变到敏捷规模的最常见路径
- 保留未做（review 视角发现的次要点，留后续 P0）：
  - RD 身份在 Subagent dispatch 路径下是否需要等价的第一人称锚点 → 当前 subagent 隔离已经天然强化身份，不急着加
  - STATUS-LINE 是否应根据追加改动回退动态切换"角色：PMO" → 规则层已经够用，避免状态行过度工程化

## v7.3.10 + P0-20

> v7.3.10+P0-20 红线 #1 职责正交化：把"谁写代码"（维度 A）与"怎么组织流程"（维度 B）解耦——代码写权在所有流程下都归 RD，Micro 不再是红线 #1 的例外，而是省 Plan/Blueprint/UI/Review/Test Stage 的最短 RD 闭环（独立流程），允许主对话内 PMO→RD 身份切换由 RD 改动。红线 #1 因此从权限矩阵压缩为一句话；所有 Micro 相关描述统一为"身份切换"语义。

### P0-20：红线 #1 重构（职责正交化 + Micro 升格为独立流程）

- 触发：用户 insight「Micro 流程 PMO 可直接改 是不是改为切换 RD 身份来改，或者在主对话由 RD 来改，我感觉是一样的，核心目的是阅读过 RD 的开发规范」。
- 根因分析：
  - 旧红线 #1 把"谁写代码"和"怎么组织流程"两个维度混在一起，用"Micro 例外"打了个补丁 → 红线从一行变成权限矩阵，读者难记
  - Micro 流程的行为等价：PMO 直接改 / PMO 切 RD 身份 / 主对话由 RD 改，三种表述本质相同——核心约束是"改之前必读 RD 规范 + 自查"，不是"允许哪个角色 handle"
  - 正交化后：代码写权 = RD 本职（维度 A，无例外）；流程组织 = 完整 Stage 链 / Micro 最短链（维度 B，独立选择）
- 处理（一次性统一表述）：
  - **SKILL.md L62-67 红线 #1 改一句话版**：「代码 / 测试 / 构建配置的写操作 = RD 本职。必须由 RD 角色执行（主对话切换身份 / Subagent dispatch 均可），RD 必须先真实 Read 规范...改后按 rd.md 自查段执行自查。」附 📎 说明执行方式由 AI Plan 决定 / 流程选择由 Micro 准入决定；去掉"Micro 例外"子分支
  - **SKILL.md L123-135 Micro 简化规则块**：从"PMO 直接改代码"改成"主对话内 PMO→RD 身份切换，由 RD 直接改"，新增 📎 与红线 #1 的关系说明（"不是例外，是省 Stage 的独立流程"）
  - **SKILL.md L328** Micro 描述：→「✍️ 主对话 PMO→RD 身份切换（Read 规范 + cite）→ RD 改动 + 自查」
  - **INIT.md L185 CLAUDE.md 注入红线 #1**：同步简化，明确"PMO 本职写权仅限流程审计文件"+ "Micro 不是红线例外，是省 Stage 的最短 RD 闭环"
  - **FLOWS.md §六 Micro 流程**：preamble 从"PMO 不写代码在 Micro 不适用"改为"Micro = 省 Stage 的最短 RD 闭环...不是红线 #1 例外"；流程链路、自动流转、PMO 分析输出格式、Micro 规则块五个子段全部把"PMO 直接改 / PMO 切 RD 身份 / PMO 以 RD 身份直接"统一为"主对话 PMO→RD 身份切换 + RD 改动"
  - **RULES.md L531-554 Micro 自动流转段**：preamble 统一；执行分支表述从「主对话以 RD 身份直接改」→「主对话 PMO→RD 身份切换 → RD 改动」
  - **roles/pmo.md L5 顶部例外段**：重写为"Micro 流程身份切换"，明确"不是红线 #1 例外 → 省 Stage 的 RD 闭环"；身份切换必读不豁免保留
  - **roles/pmo.md L1379 反模式表**：「再由 PMO 主对话直接改」→「主对话内 PMO→RD 身份切换，由 RD 改动」
  - **STATUS-LINE.md L277-279 Micro 阶段行注释**：「PMO 主对话直接改」→「主对话 PMO→RD 身份切换，由 RD 改动」；阶段名「PMO 执行改动（Micro）」→「RD 执行改动（Micro）」
  - **standards/common.md L243 / L355 L1 预检注释**：同步身份切换语义 + 保留"身份切换必读不可豁免"
  - **rules/flow-transitions.md L167-179 Micro 表**：preamble + 表格 5 行全部统一为"PMO→RD 身份切换 → RD 执行改动"
  - **版本号**：SKILL.md frontmatter `7.3.10+P0-19-C` → `7.3.10+P0-20`；INIT.md Step 1.2-a 注释同步（触发 CLAUDE.md 自愈把新红线 #1 + 身份切换注释写入）
- 设计要点：
  - **正交化原则**：红线 #1 只管"谁写代码"（A），Micro/敏捷/Feature 只管"跑哪些 Stage"（B），两维度解耦。Micro 是独立流程 × 流程 B 的一个选项，不是红线 #1 的例外
  - **行为面零变化**：Micro 流程下"主对话 PMO→RD 身份切换"与旧描述"PMO 直接改"+"角色切换必读"语义等价；只是表述更干净
  - **红线条数不变**：仍为 15 条（#1 表述重写、不拆也不删）
  - **P0-16 补丁保留**：身份切换必读 `roles/rd.md` + `standards/common.md` + 按需 frontend/backend.md + 阶段摘要 cite 规范要点 + 改后自查—— P0-20 没有放松这条
- 用户价值：
  - 读者只需记一句「代码写权归 RD」—— 不再需要记 Micro 例外树
  - Micro 的本质（省 Stage）比之前更清晰，不用再纠结"PMO 为什么突然可以改代码"
  - 新增 RD 的职责边界更刚性——便于未来 Subagent 自动化 / 审计 / 权限隔离
- 未处理项：
  - OPTIMIZATION-PLAN.md / CHANGELOG.md 历史条目中的"PMO 可直接改"保留为历史记录，不回溯改写
  - SKILL.md 红线体系的更大结构性重排（整合多处子条款、抽出 RULES.md 的独立章节）留到后续 P0

## v7.3.10 + P0-19-C

> v7.3.10+P0-19-C 外部视角 fresh review 修补：P0-19-B 物理合并 agents/*.md → stages/*.md 后，通过独立 subagent 以零上下文视角复审 skill，发现 3 个 S1 阻塞项（红线计数不一致 + `roles/rd.md` 残留 arch-code-review Subagent 幽灵引用 + `agents/README.md` dispatch 示例未加 subagent-id 语义说明）+ 4 处连带活引用遗漏（standards/backend.md / templates/dispatch.md / rules/naming.md）。本次 patch 全部修复。

### P0-19-C：外部视角 review 的 S1 阻塞项 + 连带清理

- 触发：P0-19-B 合并完成后，用户要求「以全新视角 review 一下 teamwork skill」。通过独立 subagent（等同 fresh session 无历史上下文）走完 skill 通读，以外部视角校验 merge 质量。
- 根因分析：
  - P0-19-B merge 时只处理了 `agents/*.md` → `stages/*.md` 的**直接活引用**（16 处），漏了**二阶引用**：术语表 / 幽灵 Subagent 名 / subagent-id 语义说明
  - `INIT.md` 的红线计数（13 条）是从 v7.3.9 以前复制来的，v7.3 加了 #14 / #15 后一直没同步
  - `roles/rd.md` 的两阶段架构文档更新图和架构师 CR 完成后回调逻辑还在用「arch-code-review Subagent」的老措辞，P0-19-B 把它合并进 Review Stage 后该措辞就成了幽灵
  - `agents/README.md` dispatch 文件名示例保留了老 subagent-id，但没有明确「这些 id 是 dispatch 文件标签，不是规范源」—— 读者容易回读去找 `agents/rd-develop.md` 这种已删除的文件
- 处理（3 S1 + 4 连带）：
  - **S1-1 INIT.md 红线计数**：L184「13 条」→「15 条」；CLAUDE.md 注入模板补全红线 #14（AI Plan 模式）+ #15（流程确认）；Step 0 AUTO_MODE 强制保留项 L55「13 条绝对红线」→「15 条绝对红线」
  - **S1-2 roles/rd.md arch-code-review 幽灵 Subagent**：
    - L220「Code Review 后（arch-code-review Subagent 执行）」→「Review Stage 架构师 Code Review 后（规范见 stages/review-stage.md §架构师 CR 任务规范，执行方式见 agents/README.md §一）」
    - L212「Tech Review 后（arch-tech-review）」→「Blueprint Stage 架构师方案评审后（主对话角色，规范见 roles/rd.md §架构师方案评审）」
    - L376「自动进入架构师 Code Review（Subagent）→ 有 UI 则 UI 验收 → 🤖 QA 代码审查（Subagent）」→ 合并为「自动进入 Review Stage（架构师 CR + QA CR + 外部 Codex，执行方式见 agents/README.md §一，任务规范见 stages/review-stage.md）→ 有 UI 则 UI 验收」
    - L388 §架构师方案评审规范 角色定位「在独立 subagent 中对 RD 的技术方案进行全面审查」→ 去「独立 subagent 中」，加 📎 注脚说明「默认主对话，大方案由 AI Plan 决定是否 Subagent 隔离」
  - **S1-3 agents/README.md dispatch 示例加 subagent-id 语义块**：L286-290 下方新增 📎 三点说明（`{subagent-id}` 是 dispatch 文件标签 / 角色任务规范现在在 stages/*.md / dispatch 文件 Input files 应指向 stages/*.md 而非已删除的 agents/*.md）
  - **连带 #1 standards/backend.md L622-628 Schema 变更链条术语对照表**：列头「Agent 文件」→「规范位置」；各行指向改为：RD 开发→`stages/dev-stage.md §RD 角色任务规范`；架构师 Code Review→`stages/review-stage.md §架构师 CR 任务规范`；集成测试→`stages/test-stage.md §集成测试任务规范`；Blueprint 架构师方案评审→`roles/rd.md §架构师方案评审规范`
  - **连带 #2 templates/dispatch.md L9 命名规则行**：补充「subagent-id 是 dispatch 文件标签，沿用原有命名，角色任务规范已合并至 stages/*.md」
  - **连带 #3 rules/naming.md L44-46 subagent-id 列表**：补加一行「🔴 v7.3.10+P0-19-B 起角色任务规范已合并至 stages/*.md，subagent-id 仅作标签用」
  - **连带 #4 版本号 bump**：SKILL.md frontmatter `7.3.10+P0-19` → `7.3.10+P0-19-C`；INIT.md Step 1.2-a 注释同步（触发下次启动的 CLAUDE.md 漂移自愈校验，使红线 15 条写入 CLAUDE.md）
- 保留项（review 报告中的 S2/S3 **不处理**，留作后续 P0）：
  - S2-1 红线 #1 Micro exception 树过度工程化 —— 设计决策，需单独讨论
  - S2-2 dev-stage.md 7 自检维度「L108 + L352-392 各一份」—— 复核结论是**误报**（L108 是指针引用 `§4 RD 自查 7 维度`，只有 L352-392 真正列维度）
  - S2-3 RULES.md 1628 行 + 自带热路径索引 —— 需结构性拆分，单独 P0
  - S2-4 Key Context 6 类「写 -」的可 game 性 —— 设计决策
  - S2-5 Review/Test 3 轮封顶在 AUTO 下的浪费 —— 需 AUTO 模式分支调整
  - S3 polish（naming.md subagent-id 清单 / test-stage.md 内嵌 Python 模板 / {SKILL_ROOT} glossary 缺失 / 版本号程序化派生）—— 价值低、择机
- 收益：
  - 单一权威源一致性：`SKILL.md` 红线数 = `INIT.md` 红线数 = CLAUDE.md 注入红线数 = 15 条
  - 无幽灵 Subagent 引用：`roles/rd.md` 三处措辞 + `backend.md` 术语对照表 + `dispatch.md` + `naming.md` 全部指向合并后的 stages/*.md 权威位置
  - dispatch 示例消歧：`{subagent-id}` 的语义（文件标签 vs 规范源）首次被显式说明，避免读者回读已删除的 `agents/*.md`
- 兼容性（非破坏性）：
  - 无行为变更：只改文案 / 术语 / 链接，不触动任何 Stage 契约 / 流转 / 预检
  - 既存 dispatch_log/ 的 `002-rd-develop.md` / `003-arch-code-review.md` 等文件名继续有效（subagent-id 作为标签未变）
  - CLAUDE.md / AGENTS.md 会在下次 `/teamwork` 启动时自动漂移自愈（7.3.10+P0-19 → 7.3.10+P0-19-C 触发 full path），同步红线 15 条
- 相关 meta 观察（review 报告内）：**3 个月 19 个 P0 无一次删除**。下一个 P0 建议不再新增能力，聚焦消费：拆 RULES.md / 统一红线计数 / 红线 #1 Micro exception 二选一 / 全仓 grep 审计死引用。本次 P0-19-C 只修了审计类问题的子集。

---

## v7.3.10 + P0-19

> v7.3.10+P0-19 结构重构补丁：**Stage 升格为权威层级，Subagent 降格为执行选项**。物理合并 `agents/rd-develop.md` / `arch-code-review.md` / `qa-code-review.md` / `integration-test.md` / `api-e2e.md` 五个角色任务规范到对应 `stages/*.md` 的新增 §角色任务规范段；`agents/` 目录只保留 `README.md`（瘦身为纯 Subagent 执行协议：dispatch 文件协议 + Progress 可见性 + 主对话产物协议 + 通用执行约束 + Codex CLI 调用规范）。PMO 在 Plan 模式中按需选择执行方式（主对话 / Subagent / 混合），Subagent 不再作为"规范归档维度"存在。非破坏性：所有规范内容原样迁移，仅物理位置变动 + 章节编号微调。

### P0-19-B：Stage 升格 + agents/ 物理合并（stages/dev-stage.md + stages/review-stage.md + stages/test-stage.md + agents/README.md + 引用迁移）

- 触发：用户反馈「从合理的方向看，是不是弱化 subagent, 强调 stage, 增加各个 stage 中的规范文档，因为执行层面 pmo 可以按需选择 subagent」。承接 P0-19-A（subagent 降级为执行维度）的物理落地。
- 根因分析：
  - **Stage 是业务权威层级，Subagent 是执行手段**。v7.3.9+P0-14 dual-mode 化后，RD / 架构师 / QA 都可以主对话或 Subagent 执行，"按 agent 归档规范" 不再是自然语义分类
  - `agents/rd-develop.md` / `arch-code-review.md` 等文件命名暗示「这是 Subagent 专属规范」，导致主对话执行时 PMO 不确定是否仍需加载 → 双重权威源
  - Stage 级契约（Input/Process/Output）和 Stage 内角色任务规范分居两处（stages/ + agents/），PMO 派发时需要同时引用两个路径，心智负担 + 漏读风险
  - 把角色任务规范嵌入 stage 契约之后，**一个 stage 一个权威文件**，主对话 / Subagent 两种模式均从同一文件读取
- 处理（4 Stage 文件 + 1 README + 引用迁移）：
  - **§一 stages/dev-stage.md 合并 agents/rd-develop.md 全文**（+229 行）：新增 §RD 角色任务规范（1. 角色定位 Dual-Mode / 2. TDD 开发流程 / 3. UI 还原 / 4. RD 自查 7 维度）+ §RD 执行输出模板（执行摘要 / 自查报告 / 上游问题清单）
  - **§二 stages/review-stage.md 合并 agents/arch-code-review.md + agents/qa-code-review.md 全文**（+456 行）：新增 §架构师 CR 任务规范（角色定位 / Review 维度 / 执行流程 / 架构文档更新规则 / 输出模板 / 上游问题清单）+ §QA CR 任务规范（角色定位 / 执行流程 / 执行约束 / 输出模板 / 结果处理）+ §外部视角 Codex Review（codex CLI spawn prompt 模板）
  - **§三 stages/test-stage.md 合并 agents/integration-test.md + agents/api-e2e.md 全文**（+554 行）：新增 §集成测试任务规范（角色定位 / 执行流程 / 执行约束 / 证据要求 / 报告模板）+ §API E2E 任务规范（角色定位 / 触发条件 / 执行流程 / 脚本生成规范 / 脚本落盘 + e2e-registry 注册 / 报告模板 / 红线 / 降级处理 / 含完整 Python 脚本模板）
  - **§四 agents/README.md 瘦身**（734 → ~700 行，重组为 6 个顶级章节）：§一 执行方式与模型（偏好指引 + 模型推荐）/ §二 通用 Subagent 执行约束（文件读取 / 代码质量 / 异常处理 / 输出规范 / Progress Log / 危险命令红线）/ §三 Codex CLI 调用规范（宿主无关独立性 + 降级路径决策）/ §四 PMO 启动规范（含 Dispatch 文件协议 4.1-4.6 + 4.3 Progress 可见性协议 + 4.6 Subagent 返回状态分级处理）/ §五 主对话产物协议（命名约定 + frontmatter 硬规则 + Key Context 复用 + review-log.jsonl schema + 独立性保证）/ §六 目录结构索引（含 v7.3.10+P0-19-B 变更说明）
  - **§五 物理删除 5 个 agents/*.md 文件**：`agents/rd-develop.md` / `arch-code-review.md` / `qa-code-review.md` / `integration-test.md` / `api-e2e.md`；`agents/` 目录现仅保留 `README.md`
  - **§六 引用迁移**（16 处活引用 + 保留 CHANGELOG/OPTIMIZATION-PLAN 历史引用）：
    - `SKILL.md` 示例 Plan 模板 / 索引表：`agents/rd-develop.md` → `stages/dev-stage.md §RD 角色任务规范`；`agents/arch-code-review.md` → `stages/review-stage.md §架构师 CR 任务规范`；`agents/qa-code-review.md` → `stages/review-stage.md §QA CR 任务规范`
    - `RULES.md` Test Stage 子流程：`agents/integration-test.md` → `stages/test-stage.md §集成测试任务规范`；四-B 首段说明文字同步
    - `roles/rd.md`：架构师 CR 规范链接指向 stages/review-stage.md；内嵌审查项注释同步
    - `roles/qa.md`：集成测试 / API E2E / 集成测试规范链接全部指向 stages/test-stage.md
    - `templates/feature-state.json`：`loaded_role_specs[]` 从 `agents/rd-develop.md` 改为 `stages/dev-stage.md`
    - `templates/e2e-registry.md`：生成 Subagent 引用指向 `stages/test-stage.md §API E2E 任务规范`
    - `templates/dispatch.md`：Input files 模板第 2 项从 `agents/{subagent-id}.md` 改为 `stages/{stage}-stage.md §角色任务规范`；§四 4.3 / §五 Progress 章节编号同步为 §四 4.6 / §四 4.3
    - `codex-agents/tester.toml` / `reviewer.toml` / `rd-developer.toml`：developer_instructions Read 列表的第 3-4 项（旧 agents/*.md）合并为单行「stages/{stage}.md § ...（merged in v7.3.10+P0-19-B）」
  - **§七 agents/README.md 内部 §4.3 → §4.6 修正**：FAILED 兜底从旧 §4.3 改为新 §4.6（Subagent 返回状态分级处理表合并到完成后处理段）
  - **§八 SKILL.md frontmatter version bump**：`7.3.10+P0-18` → `7.3.10+P0-19`（触发下次启动的漂移自愈校验，使 CLAUDE.md / AGENTS.md 同步新目录结构）
- 保留项：
  - `CHANGELOG.md` / `OPTIMIZATION-PLAN.md` 历史引用 **不改写**（这些是历史事实记录，非当前规范）
  - `stages/*.md` 新增段顶部的合并注释（「本节整合 v7.3.10+P0-19-B 前的 agents/xxx.md 完整规范」）保留，为合并过程提供可追溯的 git-log 替代信息
- 收益：
  - Stage = 一个物理文件 = 一个权威：PMO 派发 / 切换角色 / 主对话执行时只需引用一个路径，心智负担 -50%
  - 规范与契约同居：Input Contract → 角色任务执行流程 → Output 模板串联在同一文件内，RD / 架构师 / QA 读时上下文天然连贯
  - Subagent 回归执行手段本位：`agents/README.md` 只负责"如何跨宿主派发 + 如何保证可观测性"，不再承担规范归档
  - Plan 模式更纯粹：approach=main-conversation/subagent/hybrid 只影响执行方式，不影响「读哪个规范文件」
- 兼容性（非破坏性）：
  - 所有规范内容原样迁移（无内容删减 / 强度调整），章节编号微调
  - Subagent dispatch 协议（dispatch 文件 / INDEX / Progress Log）完全不变
  - `.teamwork_localconfig.md` 的 `teamwork_version` 缓存机制（P0-17 引入）会在下次启动自动捕获 `7.3.10+P0-19`，触发 CLAUDE.md / AGENTS.md 校验一次（若发生漂移将被漂移自愈机制同步）
  - 用户侧无任何行为变更，`/teamwork` 命令 / 阶段流转 / 角色切换全部保持

## v7.3.10 + P0-18

> v7.3.10+P0-18 人机约定补丁：新增「ok = 按 💡 建议」全局快捷授权约定。用户在 ⏸️ 暂停点回复 `ok` / `OK` / `好` / `可以` / `行` / `嗯` / `按建议` / `按推荐` → PMO 自动映射为「当前暂停点全部 💡 推荐选项」执行（单决策等价于回复 💡 对应数字；多决策等价于所有决策都选 💡 推荐）。前置条件：暂停点至少有 1 个 💡（红线 #10 本就强制）；破坏性操作 / 无 💡 暂停点 / ok+补充语句 不适用本约定，仍按原规则处理。PMO 须输出一行 cite『✅ 已按 💡 建议处理：…』作为审计痕迹。非破坏性，仅加强用户体验。

### P0-18：ok = 按 💡 建议 约定（RULES.md + STATUS-LINE.md + SKILL.md + INIT.md）

- 触发：用户反馈"加一个指令说明，ok = 按建议"。观察：现有规范（RULES.md §模糊确认处理 L186）是『🔴 禁止把「好」「行」直接视为全面授权』，要求复述+二次确认；但实际交互中用户回复 ok 几乎 100% 是『按 💡 推荐走』意图，多余的二次确认增加摩擦。
- 根因分析：
  - 旧规则是为了防止"无上下文确认"——担心 ok 被误解为授权破坏性操作。但红线 #10 已经强制要求每个暂停点都输出 💡 推荐 + 📝 理由，ok 在"有 💡 推荐"的上下文中语义完全明确（= 按推荐走）
  - 多决策点（1A 2B）即使用户想『都按推荐』也要打 `1A 2A` 5 字符，ok 2 字符更省
  - 破坏性操作（force push / drop 表 / 删分支）属强制保留暂停点（见 flow-transitions.md），本就不应依赖模糊确认，单独拉保护线即可
- 处理（4 文件）：
  - **§一 RULES.md §模糊确认处理**（L177-186）：新增「🟢 ok = 按 💡 建议」段，含 7 字（ok/OK/Ok/好/可以/行/嗯/按建议/按推荐）识别清单 + 单决策/多决策映射规则 + 前置条件（必须有 💡）+ 强制 cite 输出格式 + 4 条边界保留（破坏性操作 / 无 💡 暂停点 / ok+补充语句 / 非暂停点）。原 L186 禁令改为边界语句，不再"全面禁止"
  - **§二 STATUS-LINE.md 用户回复处理表**（L313-321）：新增一行『🟢 ok/OK/好/可以/行/按建议』列映射到『按 💡 推荐全部选项执行 + cite』；原"模糊确认（≤5 字：好/可以/OK）"行改为『其他非 ok 家族模糊词』，避免与新规冲突
  - **§三 STATUS-LINE.md 意图识别表**（L332）：🟢 流程控制行扩展识别词表 + 处理方式改为『有 💡 → 按 💡 执行 + cite；无 💡 → 复述 + 二次确认』双分支
  - **§四 SKILL.md frontmatter version**: 7.3.10+P0-17 → 7.3.10+P0-18（触发下次启动的漂移自愈校验，使 CLAUDE.md/AGENTS.md 同步）
  - **§五 INIT.md Step 1.2-a 当前版本标注**同步更新为 7.3.10+P0-18
- 收益：
  - 人机交互摩擦降低：最常见的"采纳推荐"路径从 `1A 2A` → `ok`（2 字符），大幅降低打字成本
  - 决策意图明确化：PMO cite 一行『✅ 已按 💡 建议处理：…』让用户立刻看到 ok 被如何解读，防止误解
  - 规范语义一致：红线 #10（暂停点必须给 💡）与 ok 约定形成闭环——💡 不只是"参考建议"而是"ok 对应的具体选项"
  - 边界清晰：破坏性操作 / 非暂停点 / ok+补充语句 保留原路径，不会因 ok 约定扩大授权面
- 兼容性（非破坏性，仅放宽授权）：
  - 旧行为：用户回复 ok → PMO 复述+二次确认 → 用户再回复 1A 2A → 执行
  - 新行为：用户回复 ok → PMO cite『按 💡 建议处理』→ 直接执行。用户如不满意可中断，实际事故面与旧行为相当（PMO cite 相当于"软复述"）
  - 多决策点 "1A 2A" 显式回复仍然有效，ok 只是快捷方式
  - 破坏性操作 / 无 💡 暂停点：行为不变
  - 红线 #10（暂停点必须给 💡 + 📝）事实上成为 ok 约定的前置条件，变相加强红线 #10 的约束

## v7.3.10 + P0-17

> v7.3.10+P0-17 启动 token 优化：引入 **skill 版本缓存机制**，复用 `.teamwork_localconfig.md`（已 gitignore）记录 `teamwork_version` 字段。每次 `/teamwork` 启动时，先比对 SKILL.md frontmatter 的 `version` 与 localconfig 缓存值：一致（99%+ 场景）→ 跳过 CLAUDE.md/AGENTS.md Read + 逐字符 diff；不一致（skill 升级 / 首次 / 降级）→ 走全量校验 + 写回新版本号。估计节省 ~65-75% 启动阶段 token 消耗。漂移自愈（skill 升级后模板变动自动同步到 CLAUDE.md）能力保留；`/teamwork force-init` 作为逃生舱。非破坏性变更，向前兼容 v7.3.10+P0-16（localconfig 无 teamwork_version 字段 → 自动走全量 + 写入一次即进入稳态）。

### P0-17：skill 版本缓存优化 CLAUDE.md 校验（SKILL.md + templates/config.md + INIT.md）

- 触发：用户反馈"目前读 Init.md 的逻辑是什么，从 token 占用角度，是否有优化空间"；复盘发现 Step 1.2 每次启动都会 Read `{HOST_INSTRUCTION_FILE}`（CLAUDE.md / AGENTS.md）+ 做逐字符 diff，占用 ~2000-3500 token。用户反建议："我们是否在 .teamwork_localconfig.md 中加一个当前 teamwork 版本，如果和 skill.md 版本不一致的时候再去做 claude.md 和 agent.md 检查，更合理，复用本地的轻量级文件。"
- 根因分析：
  - CLAUDE.md/AGENTS.md 模板内容只在 skill 升级时才会变化；日常启动 99%+ 场景是"skill 未升级 → 模板未变 → diff 必然一致"的重复工作
  - 漂移自愈能力（skill 升级后模板变动同步到 CLAUDE.md）只需在升级时触发一次，不需要每次启动都跑
  - `.teamwork_localconfig.md` 已经存在（gitignore、每开发者各自维护）、是启动必读文件（已在 Step 2 加载），作为版本缓存载体成本为零
- 处理（3 文件）：
  - **§一 SKILL.md frontmatter 新增 `version: 7.3.10+P0-17` 字段**（单一权威版本号）：放在 frontmatter 使解析成本最低（Skill 加载时已可见）；后续每次 skill 升级需同步更新此字段
  - **§二 templates/config.md `.teamwork_localconfig.md` 模板新增「Skill 版本标记」段**：含 `teamwork_version:` 字段 + 详细注释说明机制 + "🔴 禁止手改（PMO 自动维护）"警示 + 逃生舱说明
  - **§三 INIT.md Step 1.2 重写为缓存-校验-回写模式**：
    - **Step 1.2-a**：读取 SKILL.md frontmatter `version` → `SKILL_VERSION`（缺失则降级全量+一次性 ⚠️ 提示）
    - **Step 1.2-b**：读取 `.teamwork_localconfig.md` `teamwork_version` → `LOCAL_VERSION`（文件/字段缺失/损坏均降级为 null）
    - **Step 1.2-c**：版本比对决定路径
      - ⚡ fast path（一致）：跳过 CLAUDE.md/AGENTS.md Read + diff，输出「⚡ CLAUDE.md 校验跳过（teamwork_version={VERSION} 命中缓存）」
      - 🔄 full path（不一致/null）：走原 P0-17 前的全量校验（文件不存在→创建、存在→逐字符 diff、漂移→替换），完成后回写 localconfig `teamwork_version: {SKILL_VERSION}`，输出「🔄 CLAUDE.md 已同步（{旧版本 or "缺失"} → {新版本}）」
      - 🚨 SKILL_VERSION=null：走全量 + 不回写 + ⚠️ 提示
  - **§四 INIT.md Step 0 加 `/teamwork force-init` 命令**（+ `/teamwork init --force` 别名）：用户怀疑 CLAUDE.md 被外部工具手改 / 缓存脏污时强制走全量校验
- 收益：
  - 启动 token 节省：fast path（99%+ 场景）跳过 ~2000-3500 token 的 CLAUDE.md Read + diff；估计节省 ~65-75% 启动阶段 token 消耗
  - 漂移自愈保留：skill 升级 → 版本不一致 → 一次性全量 diff 修复 CLAUDE.md → 写回新版本 → 此后跳过；机制语义与 P0-17 前完全等价
  - 复用本地轻量文件：localconfig 已 gitignore + 已是 Step 2 必读文件，无额外 I/O 成本
  - 多开发者一致性：localconfig 是每个开发者各自维护，版本缓存也是本地化（不产生跨机器 / 跨用户 git 冲突）
- 兼容性（非破坏性，向前兼容）：
  - P0-16 用户升级到 P0-17：首次启动 `LOCAL_VERSION=null` → 走全量校验 + 写回 → 此后稳态 fast path
  - localconfig 不存在：首次启动走全量校验 + 按 templates/config.md 创建最小版 localconfig（只填 scope:all + teamwork_version）
  - CLAUDE.md 被用户手改但 skill 未升级：版本仍命中 → 跳过校验 → 用户修改被保留（"respect user edits" 默认行为；若要强制恢复模板，用 `/teamwork force-init`）
  - 用户伪造 localconfig 的 teamwork_version（手改成最新值）：绕过校验的理论风险 → 靠模板注释"禁止手改"约束 + `/teamwork force-init` 兜底（此场景极少）
  - 无字段变更影响 state.json / agents/ spec
- 未变更：
  - P0-16 及之前所有行为语义（Micro 流程、红线 #1、Ship MR 模式等）完全不变
  - P0-11 AUTO_MODE / P0-13 Codex opt-in / P0-15 Ship Stage MR 流 等所有其他机制保持原样

## v7.3.10 + P0-16

> v7.3.10+P0-16 一致性修订：Micro 流程去「强制 RD Subagent」化 → 统一为「PMO 自行判断（主对话以 RD 身份直接改 / 升级 Plan 模式）」。核心实体（FLOWS.md §六、SKILL.md 红线 #1 Micro 例外）早已在 v7.3 放宽为 PMO 直接改，但 SKILL.md L320 / RULES.md L521-547 / rules/flow-transitions.md / STATUS-LINE.md / roles/pmo.md / standards/common.md 等 7 个文件仍残留「RD Subagent 执行 / 必须启 Subagent」旧描述，形成自相矛盾。P0-16 清理全部残留，使"PMO 自行判断执行方式"贯穿全部 Micro 相关描述。非破坏性变更（行为层面已经是 PMO 直接改，仅补齐文档一致性）。

### P0-16：Micro 流程描述一致性修订（SKILL.md + RULES.md + rules/flow-transitions.md + roles/pmo.md + STATUS-LINE.md + standards/common.md）

- 触发：用户反馈"Micro 流程是否还强制 RD 在 subagent 下执行，预期是 Micro 流程在初步分析后，PMO 自行判断是否切 Plan 模式还是以 RD 角色身份直接在主对话修改"。
- 根因分析：
  - v7.3 放宽了 Micro 流程红线：FLOWS.md §六「Micro 流程」+ SKILL.md 红线 #1 Micro 例外 + SKILL.md L122-126「AI Plan 模式 Micro 例外」已统一为「PMO 可直接改，无需 Subagent / Execution Plan / dispatch」
  - 但 SKILL.md L320 六种流程速查 / RULES.md 流转图 / rules/flow-transitions.md Micro 流程表 / STATUS-LINE.md Micro 示例 + 阶段对照表 / roles/pmo.md 反模式 / standards/common.md 预检级别表 等 7 处未同步更新，仍保留 v7.2 前的「RD Subagent 执行」旧描述
  - 导致跨文件描述自相矛盾：同一套规范里有地方说"PMO 直接改"，有地方说"必须启 RD Subagent"，对 PMO 读者造成歧义
- 处理（7 文件 / 11 处）：
  - **§一 SKILL.md L320**：六种流程 Micro 行 `RD Subagent 执行` → `PMO 自行判断执行方式（✍️ 主对话以 RD 身份直接改 / 🔀 升级为 Plan 模式走敏捷或 Feature）`
  - **§二 RULES.md L521-547 Micro 流程自动流转**：流程图去掉「🤖 RD Subagent 执行改动（🔴 PMO 禁止自己改，即使只改一行）」+「PMO L1 预检」节点；改为「PMO 自行判断：✍️ 主对话以 RD 身份直接改 / 🔀 升级 Plan 模式」分支；描述语加 v7.3 放宽 + P0-16 明确标注
  - **§三 RULES.md L720 功能完成时 PMO 必须执行**：Micro 流程校验改为「PMO 分析→用户确认→PMO 执行（主对话直接改 或 升级 Plan 模式）→用户验收 四步」
  - **§四 rules/flow-transitions.md**：
    - L39-40 强制保留暂停点表 Micro 两行（🤖 RD Subagent → 用户验收 / → ⏸️ 升级确认）改为 PMO 执行改动路径
    - L52 豁免示例 Micro 行改「按 💡 自动进入（PMO 自行判断执行方式，无需暂停）」
    - L167-177 § Micro 流程节完全重写：header 从「🔴 PMO 禁止自己改代码，必须启 RD Subagent」反转为「🟢 PMO 自行判断执行方式」；表格行从「PMO 分析 → Micro 变更说明 → 🤖 RD Subagent → 用户验收」4 行改为「PMO 分析 → PMO 执行改动 → 用户验收」3 主路径 + 升级确认支路
  - **§五 roles/pmo.md**：
    - L5 版本头「Micro 流程例外（v7.3）」描述修正：去掉「但必须走 Plan 模式规划 + 用户确认流程」与 FLOWS.md §六 冲突的旧字句，改为「无需 Subagent / Execution Plan / dispatch」+ P0-16 标注
    - L748 auto 豁免表 Micro 行改「PMO 执行改动（主对话直接改）」
    - L1379 反模式首行从「即使只改一行也必须启 RD Subagent」改为「必须先输出 PMO 初步分析 + Micro 准入检查 → ⏸️ 等用户确认 → 再由 PMO 主对话直接改」+ P0-16 标注
    - L1388-1399 PMO 小改动决策树末段从「🔴 任何情况下 PMO 都不能自己动手改代码」改为双分支：Micro 外保持禁止 + Micro 内 PMO 自行判断（直接改 / 升级 Plan）
  - **§六 STATUS-LINE.md**：
    - L201 Micro 示例状态行「下一步：🤖 启动 RD Subagent」改为「下一步：⏸️ 等待用户验收」，阶段从「Micro 变更说明中」改为「PMO 执行改动中」
    - L277-280 阶段对照表 Micro 专用阶段 3 行（Micro 变更说明 / 🤖 RD Subagent / 用户验收）重写为 PMO 执行改动 / Micro 升级判定 / 用户验收
  - **§七 standards/common.md**：
    - L242 L1 预检描述「包括 Micro 流程的 RD Subagent」改为「Micro 流程 PMO 主对话直接改，不走 Subagent，不触发本预检」
    - L354 各流程预检级别速查表 Micro 行从「Micro | RD Subagent | L1」改为「Micro | _（不启 Subagent）_ | —」
- 收益：
  - Micro 流程描述一致性：全部 12 处引用统一到「PMO 自行判断执行方式」语义，消除 v7.3 放宽以来遗留的 7 文件自相矛盾
  - 用户意图承载：显式写出「✍️ 主对话以 RD 身份直接改 / 🔀 升级 Plan 模式」双路径，PMO 读规范即知自己有判断空间，不再被旧描述误导去强启 Subagent
  - 红线体系简化：Micro 外「PMO 不得改代码」+ Micro 内「PMO 可直接改（白名单内零逻辑）」边界清晰，不需要维护"什么时候启 Subagent"的额外规则
- 兼容性（非破坏性）：
  - 行为面无变化：FLOWS.md §六 + SKILL.md 红线 #1 Micro 例外早已是"PMO 直接改"语义；PMO 按新描述执行与按旧描述通过"豁免启 Subagent"执行等价
  - state.json / localconfig：无字段变更
  - Subagent 不再在 Micro 下 dispatch，因此不影响 dispatch 模板 / agents/ spec

### P0-16 补丁：Micro RD 身份切换的必读规则（SKILL.md + FLOWS.md + RULES.md + rules/flow-transitions.md + roles/pmo.md + STATUS-LINE.md）

- 触发：用户反馈"如果切换 RD 身份是否会加载 rd 的规范，避免还是 PMO 只是输出描述改了"
- 根因：P0-16 主体改动把 Micro 执行路径统一到「PMO 以 RD 身份主对话直接改」，但未显式要求真实加载 RD 规范。Micro 流程免 Execution Plan 同时把 SKILL.md 红线 #14「Role specs loaded 必须真实 Read」也隐性豁免了——存在"PMO 换个名头凭记忆改"的漏洞
- 处理（6 文件）：
  - **SKILL.md L63 红线 #1 Micro 例外条款**：加"🔴 角色切换必读不豁免"子句，要求 Read roles/rd.md + standards/common.md + 按改动类型加读 frontend.md/backend.md + 摘要 cite 规范要点
  - **SKILL.md L122-126 AI Plan 模式 Micro 例外段**：扩展 Micro 例外条款的"不豁免项"清单，显式列出必读文件 + cite 规则 + 自查要求
  - **FLOWS.md §六 Micro 流程规则**：强制规则段加「角色切换必读」3 项新条款；流程链路 + 流转图 + 分析输出格式步骤描述 全部加入「PMO 加载 RD 规范+cite」节点 + 「RD 自查」节点；事后审计加 2 项校验（是否真实 Read / 自查是否执行）
  - **RULES.md Micro 流转图**：在「✍️ 主对话以 RD 身份直接改」分支下补全"改动前必读 / 改动前 cite / 改动后自查" 3 层硬约束
  - **rules/flow-transitions.md § Micro 流程**：表头加第二行「角色切换必读不豁免」警示；流转表从 4 行（PMO 分析 / 执行 / 升级 / 验收）扩展为 6 行（PMO 分析 / 加载 RD 规范 / 执行 / RD 自查 / 升级 / 验收）
  - **roles/pmo.md L5 头部 Micro 例外描述**：补全「角色切换必读不豁免」+「cite 规范要点」+「改动后自查」3 项硬约束
  - **STATUS-LINE.md L277-281 阶段对照表**：Micro 专用阶段从 3 行（PMO 执行改动 / 升级判定 / 用户验收）扩展为 5 行（PMO 加载 RD 规范 / PMO 执行改动 / RD 自查 / 升级判定 / 用户验收）
- 收益：
  - 堵住"换名头凭记忆改"漏洞：PMO 必须真实 Read + cite 规范要点，"我切 RD 了"一句话不能替代"读规范"
  - Micro 流程仍然是最轻量通道：不要求完整 Execution Plan / dispatch，但保留"真实加载 + cite + 自查" 3 层最小质量锚
  - 与红线 #14「Role specs loaded 必须真实 Read」+ AI Plan 模式红线「角色切换必 cite」保持一致：Micro 只豁免 Execution Plan 的输出形式，不豁免底层纪律
- 兼容性（非破坏性，仅加强约束）：
  - 行为面轻微变化：之前可能存在"PMO 未 Read rd.md 就直接改"的灰色操作，现在必须真实 Read + cite
  - 流转图多出 2 个新阶段（「PMO 加载 RD 规范」+「RD 自查」），属自动流转节点（🚀自动，无需用户确认）
  - state.json / localconfig：无字段变更

## v7.3.10 + P0-15

> v7.3.10 相对 v7.3.9 的唯一破坏性变更：Ship Stage 从「PMO 本地 merge + push merge_target」改为「MR 模式」（P0-15）。PMO 只负责净化 + push feature + 生成 MR/PR create URL，合并权由平台和用户处理。红线 #1 不再有 Ship 例外条款；localconfig 移除 `ship_rebase_before_push` / `ship_policy`；state.json.ship 字段重构。详见 P0-15 条目。

## v7.3.9 + P0 简化

> P0 是 v7.3.9 落地后的一轮"反刍"简化：抽取重复描述、收敛 preflight 暂停点、修正依赖安装时机表述、Codex 成本治理（P0-13：Plan/Blueprint opt-in 默认 OFF，Review 保持强制）、Dev Stage 默认主对话（P0-14：RD 自行规划 Plan 模式，subagent 降为 opt-in）、Ship Stage MR 化（P0-15：简化 PMO 职责边界）。无破坏性变更（P0-15 仅影响 Ship Stage 流程和 state.json.ship schema，向前兼容 v7.3.9 其他部分）。

### P0-15：Ship Stage MR 模式重构（stages/ship-stage.md + templates/feature-state.json + SKILL.md + INIT.md + roles/pmo.md + rules/flow-transitions.md + FLOWS.md + templates/config.md）

- 触发：用户反馈"当前 Ship 流程是否可以简化，例如开发完成后新分支的代码提交 push 后，生成 MR create 链接由用户创建 MR 可以了，这个 MR create 链接要记到 state.json 中，方便以后回溯，然后清理 worktree（如有），不删远程 feature 分支"。
- 决策：**Ship Stage 从 6 步直连合并流（净化 → push feature → rebase → 本地 merge --no-ff → push merge_target → worktree 清理）改为 3 步 MR 流（净化 → push feature + 生成 MR/PR create URL → worktree 清理）**。PMO 不做本地 merge / push merge_target / 冲突解决；合并权由平台（GitHub/GitLab/Gitee/Bitbucket 等）和用户处理。
- 根因分析：
  - v7.3.9 Ship Stage 让 PMO 承担了过多"最后一公里"职责：本地 merge、rebase、冲突解决、push merge_target。这些操作在多人协作场景下风险高（覆盖他人改动、污染主干）、需要复杂的红线 #1 例外条款（允许 PMO 改代码解冲突），且实际合入已由 MR/PR 平台做得更好（代码评审、CI/CD 门禁、合规审计、审批流）
  - 主流 git workflow（GitHub Flow / GitLab Flow / Trunk-Based）核心就是"push 分支 + 平台合入"，直连合并反而是反模式
  - 红线 #1 "PMO 非 Micro 流程下不得改代码" 加 Ship 例外条款使红线复杂化，不利于信任边界表达
- 处理（8 文件）：
  - **§一 stages/ship-stage.md 完全重写**（核心）：Input/Process/Output Contract 全部按 MR 模式重写；3 步流（Step 1 净化 / Step 2 push feature + host 识别 + MR URL 生成 / Step 3 worktree 清理暂停点）；per-host URL 模板（github / gitlab / gitlab-self-hosted / gitee / bitbucket / unknown）；unknown 平台走 localconfig `mr_url_template` 或 concerns 标注"未识别平台"；push FAILED 直接升级 ⏸️ 用户决策（不重试、不降级）；Anti-patterns 表更新（禁止本地 merge / 禁止 push merge_target / 禁止伪造 URL / 禁止删除远程 feature 分支）
  - **§二 templates/feature-state.json ship 字段重构**：移除 `rebase_status` / `merge_commit_hash` / `push_status`；新增 `sanitize_log` / `git_host` / `mr_create_url` / `feature_pushed_at` / `worktree_cleanup` / `shipped`；顶部 `_instructions.ship_tracking_v7_3_10_P0_15` 注释说明字段变更
  - **§三 SKILL.md 红线 #1 + INIT.md 红线 #1**：移除"🆕 Ship Stage 例外（v7.3.9）rebase/merge 冲突 PMO 可直接解决"条款；改为"🟢 Ship Stage 行为（v7.3.10+P0-15）：Ship Stage PMO 不做本地 merge / push merge_target / 冲突解决；只负责净化 + push feature + 生成 MR 创建链接。合并权由平台和用户处理（红线 #1 不再有 Ship 例外条款）"
  - **§四 roles/pmo.md**：PM 验收三选项 + Ship Stage 章节版本号 v7.3.9 → v7.3.10+P0-15；Merge 预览模板改 MR 模式（去掉 rebase 预处理行）；Ship Stage PMO 职责速查段全部重写（3 步流 + 禁止清单 + push FAILED 处理）；Commit / Push / Ship 状态报告改 MR 模式（`mr_create_url` / `git_host` / `worktree_cleanup` 字段）；强制保留暂停点清单移除"ship_policy=confirm merge+push"（第 2 项）和"Ship Stage 冲突 PMO 解不了"（第 4 项），改为 push FAILED 暂停点；移除"Ship Stage 冲突解决权限（红线 #1 例外）"段
  - **§五 rules/flow-transitions.md**：Feature 流程 Ship 行重写（PM 验收 → Ship Stage → worktree 清理 → 完成；移除 merge+push 待确认 / 本地 merge 行）；push FAILED 暂停点 2 选 1（手工处理后复跑 / 取消 Ship）
  - **§六 FLOWS.md**：PMO 初步分析阶段链 v7.3.4 → v7.3.10+P0-15（末段改 PM 验收 + Ship Stage MR 模式）；流程步骤描述第 8-10 步重写
  - **§七 templates/config.md 本地配置**：移除 `ship_rebase_before_push` / `ship_policy`；保留 `merge_target` / `worktree_cleanup`；新增 `mr_url_template` 字段（可选，自建 GitLab / 企业 git 自定义链接格式，支持 `{remote_url}` / `{repo_path}` / `{feature_branch_enc}` / `{merge_target}` 占位符）
- 收益：
  - PMO 职责边界清晰：Ship Stage 只负责"把分支送到平台门口 + 给用户合入入口"，不越界做代码层决策
  - 红线 #1 简化：移除 Ship 例外条款后，"PMO 非 Micro 流程下不得改代码" 变为真正的绝对红线，无需维护例外清单
  - 多人协作友好：平台 MR/PR 合入有代码评审 / CI / 审批记录，比 PMO 本地 merge 可审计性强
  - 无冲突解决成本：PMO 不解冲突 → 不需要单测全绿校验 / 不需要升级决策路径 / 不产生"解一半再回退"的中间态
  - 暂停点收敛：v7.3.9 "merge+push 待确认" + "worktree 清理" + "Ship 冲突/FAILED" 3 个 Ship 暂停点收敛为 1 个（worktree 清理）+ 1 个异常暂停点（push FAILED）
- 兼容性（破坏性变更，需迁移）：
  - **state.json.ship schema**：v7.3.9 已完成 Ship 的 Feature 保留旧字段（merge_commit_hash / push_status 等）不清理，可查阅；v7.3.9 进行中未到 Ship Stage 的 Feature 进入 Ship 时走新流程、写新字段
  - **localconfig**：v7.3.9 用户升级到 v7.3.10 时，`ship_rebase_before_push` / `ship_policy` 字段 PMO 自动忽略（不报错）；建议用户手动清理这两行 + 新增 `mr_url_template:`（空值即可）
  - **Codex CLI 子 agent**：Ship Stage 不通过 subagent 执行（PMO 主对话自主），无影响
  - **历史 Feature 的完成报告**：v7.3.9 报告中含 `merge_commit` / `已合入 {merge_target}` 字段的历史数据保留（审计痕迹）
- 未变更：
  - PM 验收三选项（通过+Ship / 通过暂不 Ship / 不通过）语义不变，只是"通过+Ship"进入的 Ship Stage 流程变了
  - 选 2（通过暂不 Ship）的 push feature 归档流程不变
  - 其他 Stage 的 auto-commit 硬规则 / git 干净校验 / Stage 切换预检均不变
  - merge_target 配置链（state.json > localconfig > 默认 staging）不变
  - worktree 清理策略（`worktree_cleanup: ask/keep/remove`）不变

### P0-1：auto-commit 硬规则集中化（rules/gate-checks.md + 8 个 Stage md）

- 问题：v7.3.9 在 8 个 Stage md（plan / ui_design / blueprint / blueprint_lite / dev / review / test / browser_e2e）中各重复一遍 5-7 行的 "Stage 完成前 git 干净" 流程描述。改文案需改 8 处，用户读 Stage 文件看到大段重复。
- 处理：将完整规则抽取到 `rules/gate-checks.md § Stage 完成前 git 干净`（含通用流程、各 Stage commit message 规范、单值/数组字段语义、免除场景）。各 Stage md 只保留一行引用 + 本 Stage commit message 示例。
- 收益：文案减少 ~35 行；单一修改点；引用链从分散变为集中。

### P0-2：Preflight 从 6 项砍到 4 项（plan-stage.md + pmo.md + flow-transitions.md + feature-state.json）

- 问题：v7.3.9 原设计"3 硬门禁 + 3 软提示"，实践发现：
  - "工作区干净" 是硬条件（worktree 继承脏状态代价大），不应软化
  - "merge_target 解析" 在级联无分歧时无需交互
  - "分支命名" 可从 Feature 全名自动派生
  - 最多 3 次暂停，用户体验冗长
- 处理：收敛为 **4 项硬门禁 + 0 软提示**：
  - 门禁 1：worktree 策略无残留
  - 门禁 2：分支名无冲突（分支名自动派生）
  - 门禁 3：base 分支可达（merge_target 自动解析）
  - 门禁 4：**工作区干净（P0 升级为硬门禁）**
  - 暂停点：最多 1 次（仅真冲突时）
- 收益：preflight 交互次数从"至多 3 次"降到"最多 1 次"。plan-stage.md / pmo.md 的校验表 + 暂停点模板同步更新。flow-transitions.md L11-12 更新 preflight 描述。feature-state.json 的 plan_preflight.checks 增加说明注释。

### P0-3：懒装依赖模型（plan-stage.md + dev-stage.md + test-stage.md）

- 问题：v7.3.9 描述 Feature worktree 创建时需装依赖（npm/pip/build），隐含 ~分钟级冷启动成本。实际只有 Dev / Test Stage 需要依赖，其他 Stage（Plan / Blueprint / Review）纯文档产出，空壳 worktree 就能跑。把依赖安装绑在 worktree 创建上是过早优化为保守。
- 处理：
  - `plan-stage.md` worktree 创建段补 "🟢 P0 懒装依赖模型" 说明：worktree 创建不装依赖
  - `dev-stage.md` 新增 "Stage 入口 Preflight：懒装依赖" 段：检测 → symlink 或 install → 记录到 `state.json.stage_contracts.dev.dependency_install`
  - `test-stage.md` 环境准备段补"懒装依赖兜底"：Dev 跳过场景下在 Test 入口补装
- 收益：Feature worktree 创建开销统一 ~1-2s（无 npm/pip 等待），Plan / Blueprint / Review 等纯文档 Stage 无冷启动税；依赖安装发生在真正需要它的 Stage 入口（单次付费）。

### P0-5：状态行第三行 —— 分支 / worktree 语义（STATUS-LINE.md）

- 问题：v7.3.9 状态行只有流程 / 角色 / 功能 / 阶段 / 下一步 + 功能目录路径两行。worktree 启用后，用户肉眼看不到"现在在哪个 worktree、绑定哪个分支、合入目标是什么"——必须翻 state.json 或跑 `git status` 才能确认。并行 Feature 或 Micro 直接改主分支的场景下，这种不可见性容易导致误操作（例如误以为还在 worktree，实际已回到主分支）。
- 处理：`STATUS-LINE.md` 新增第三行规范：
  - 🌿 = 启用了 worktree 隔离（安全）：`🌿 分支：{branch} → {merge_target} | worktree：{path}`
  - 📍 = 直接在分支上操作（谨慎）：`📍 当前分支：{branch} → {merge_target}（⚠️ ...）`
  - 各流程（Feature / 敏捷 / Bug / Micro / Planning / 问题排查）模板与示例同步更新
  - 字段取值优先 state.json.worktree + merge_target，缺失时回退 `git branch --show-current`
- 收益：PMO 每次回复都把分支 / worktree / merge_target 显式化，Micro 场景用 📍+⚠️ 做软兜底防误操作；并行 Feature 场景 worktree 路径直出，减少"在哪改"的混淆。

### P0-6：Codex CLI 宿主兼容性审计（browser-e2e-stage.md + review-stage.md + agents/README.md + templates/codex-cross-review.md + dispatch.md + review-log.jsonl + plan-stage.md + blueprint-stage.md + flow-transitions.md）

- 问题：审计各 Stage 在 Codex CLI 宿主下的可跑通性，发现 3 处强耦合 Claude 生态的表述：
  - **P0-6-A（Browser E2E 工具硬编码）**：`browser-e2e-stage.md` 隐含 `mcp__Claude_in_Chrome__*` / `mcp__gstack__*`，Codex CLI 宿主无此 MCP，Stage 直接跑不通
  - **P0-6-B（Review Stage 外部视角在 Codex 宿主下坍缩为自审）**：Codex CLI 宿主若"用自己当 Codex 外部视角"，则失去 session 隔离的独立性保证，"外部视角"名存实亡
  - **P0-6-C（降级模型硬编码 Sonnet）**：多处文档把"Codex CLI 不可用"的降级路径写死为"Sonnet fallback"，Codex 宿主用户没有 Sonnet 可降，该表述不成立
- 处理：
  - **P0-6-A**：`browser-e2e-stage.md` 新增"浏览器工具宿主适配"块：Claude Code 宿主用 MCP，Codex CLI 宿主走 Playwright/puppeteer 子进程，通用宿主无浏览器工具时降级为 ⏸️ 用户手动验收（带 WARN 日志 + `executor: user-manual` frontmatter）
  - **P0-6-B**：`review-stage.md` 步骤 4 + `agents/README.md §三` + `templates/codex-cross-review.md §二/§六` 统一规则——无论宿主是 Claude Code 还是 Codex CLI，外部视角**都通过 codex CLI 独立 spawn fresh session**（Claude 宿主：Task/MCP 调 codex 子进程；Codex 宿主：prompt 内 spawn `.codex/agents/*.toml` 子 agent）；🔴 明令禁止"外部视角 = Codex 主对话自审"
  - **P0-6-C**："Sonnet fallback" 全部替换为 "🟢 AI 自主规划等效独立审查"，并在 `agents/README.md §三` 新增"降级路径决策（🟢 AI 自主判断）"段：列决策维度（宿主可用模型清单 / 独立性强度 / 任务复杂度 / 成本 / 历史降级）+ 典型可行模式（fresh context 同宿主 / 低成本模型 / 并行双模型投票 / PMO 自审最弱兜底）；要求 AI 在 Execution Plan 或 concerns 写明降级决策理由
  - 同步扫清：`flow-transitions.md` L25 / `plan-stage.md` L225 / `blueprint-stage.md` L96 / `templates/dispatch.md` L78 + L260 + 降级汇总表 / `templates/review-log.jsonl` 示例注释
- 收益：三处"Claude 独有"表述转为宿主无关语义；Codex CLI 宿主可走全流程；外部视角独立性的来源从"不同模型"重定义为"fresh session 隔离"（可叠加跨模型做强形式）；降级策略从硬编码转为 AI 自主决策 + 理由留痕。

### P0-7：文档基准锚定（templates/ 格式权威 · TEMPLATES.md + roles/pmo+pm+rd.md + plan-stage.md）

- 问题：实战观察发现 AI 在起草 PRD / state.json / TECH 时倾向于"先参考最近一个 Feature 的格式"而非 Read `templates/` 中的模板。后果：
  - peer Feature 的产物可能装的是老 schema（state.json 尤其敏感，v7.3.2 / v7.3.9 / P0 都有增量字段），抄过去 = 漂移放大
  - peer Feature 可能被手动改过格式，漂移会扩散到新 Feature
  - templates/ 下模板齐全但没有任何文档声明它是"格式唯一真相源"，AI 的最近邻检索本能占上风
- 处理：新增"格式权威"契约，显式规定 templates/ 为唯一格式真相源：
  - `TEMPLATES.md` 顶部新增"🔴 格式权威红线"块：templates/ = 格式唯一真相源 / 禁止以 peer Feature 产物为格式基准 / peer Feature 仅可作内容参考 / state.json 特别注意
  - `roles/pmo.md` 顶部（职责段后）加"🔴 格式权威守门"：PMO 作为流转守门员对格式合规性负责，禁止在 Execution Plan 说"先参考最近一份 X 格式"
  - `roles/pm.md` 实现原则后加"🔴 PRD 格式权威"：起草 PRD 前 Read templates/prd.md 为基准
  - `roles/rd.md` 开发前必读后加"🔴 TECH / TC 格式权威"：起草前 Read templates/tech.md + templates/tc.md 为基准
  - `stages/plan-stage.md` PM 起草 PRD 步骤内插入"格式基准锚定"子条（v7.3.9+P0-7 硬规则）
- 收益：AI 的"抄邻居"本能被显式红线拦截；三角色（PMO 守门 / PM 起草 PRD / RD 起草 TECH+TC）都有对应条款；peer Feature 仅可作内容参考的语义清晰；state.json schema 漂移风险收敛。

### P0-8：跨项目依赖识别前置（FLOWS.md + roles/pmo.md + templates/dependency.md + stages/plan-stage.md）

- 问题：实战观察到 AI 在消费方 Feature 识别到"需要其他子项目能力"时，自由发挥：
  - 自创 DEPS.md（非 teamwork 标准文件名）
  - 放在消费方 Feature 目录（应放**上游子项目** `{upstream}/docs/DEPENDENCY-REQUESTS.md`）
  - 不读 templates/dependency.md 为格式基准（叠加违反 P0-7）
- 根因：templates/dependency.md 模板齐全，但 PMO 初步分析输出格式里没有「🔍 跨项目依赖识别」触发项；roles/pmo.md 的"跨子项目需求拆分"只覆盖场景 B（横跨多子项目 naturally），没显式区分场景 A（单 Feature 上游依赖）
- 处理：显式区分两种场景 + 前置触发 + 强绑定 templates/dependency.md：
  - `FLOWS.md` PMO 初步分析输出格式新增「🔍 跨项目依赖识别」项（和「🔍 跨 Feature 冲突检查」并列）：扫描上游依赖信号 → 场景 A（上游 `DEPENDENCY-REQUESTS.md` 追加 DEP-N）/ 场景 B（走跨子项目拆分）/ 无依赖
  - `FLOWS.md` 同时新增「📋 本轮拟产出文档清单」项（强化 P0-7 格式权威露出）：每份产物对应 templates/ 路径，PMO 声明 Write 前必 Read 模板
  - `roles/pmo.md` 新增「🔗 跨项目依赖识别」专门章节，详述场景 A 处理流程与硬规则：DEPENDENCY-REQUESTS.md 只放上游子项目目录 / 禁止消费方 Feature 目录自创文件 / 多条依赖分散到多个上游子项目
  - `templates/dependency.md` 顶部加"何时触发使用"说明（消费方 / 被依赖方各自触发点）+ 回链 roles/pmo.md
  - `stages/plan-stage.md` PM 起草 PRD 步骤加「跨项目依赖前置」硬规则：PM 发现上游依赖 → 立即通知 PMO 走场景 A（而非等 PRD 写完再补）
- 收益：消费方 Feature 遇上游依赖有明确流程可套；DEPENDENCY-REQUESTS.md 回到标准位置（上游子项目目录）；templates/dependency.md 触达面打开；P0-7 格式权威在 PMO 初步分析模板里露出，触达面从"藏在 roles/ 里"升级到"每次初分析都显式"。

### P0-14：Dev Stage 默认主对话 + RD 自行规划 Plan 模式（rd-develop.md + dev-stage.md + agents/README.md + feature-state.json）

- 触发：用户反馈"开发阶段在主对话，是否合理，不要求在 subagent，由 RD 自行规划 Plan 模式"。审计发现 v7.3.9 虽声称"Dev Stage AI 自主判断"，但 3 处残留默认偏向 subagent：
  - `agents/rd-develop.md` 整篇以"RD Subagent"视角书写（标题 / 执行摘要 / 自检触发条件均内嵌"subagent"措辞）
  - `templates/feature-state.json` planned_execution.dev 示例直接写 approach="subagent"
  - `agents/README.md` §一默认表虽写"AI 自主"，但判断条列"≤3 文件 → main"，隐含 >3 文件即 subagent 的保守基线
- 决策：**Dev Stage 默认 `main-conversation`**；subagent 降为 opt-in 路径（TECH.md 文件清单 >10 / 预期产出 >500 行 / 需独立聚焦或跨模型独立性时使用）；RD 在 AI Plan 阶段自评规模 + 声明 Rationale。
- 根因分析：
  - 主对话模式对大多数 Feature（单模块、改动 ≤10 文件、产出 ≤500 行）更优：省冷启动（3-5 min subagent 税）、TDD 过程用户可见、多轮调试不用重启 context、Plan/Blueprint 已加载的 PRD/TC/TECH 可直接复用（省 5-10K token 重读）
  - 原"AI 自主"措辞被"subagent 默认"的细节稀释 —— RD 启动时若第一眼看到 rd-develop.md 整篇 subagent 语境 + state.json 示例 subagent + README 表"≤3 文件才 main" → 自然默认选 subagent
  - subagent 的独立性价值在 Dev Stage 相对其他 Stage 弱：Review Stage 的 Codex / QA 独立性来自跨模型 + 盲区兜底；Dev Stage 是 RD 单视角执行，独立性收益不显著，冷启动税却实打实
- 处理（4 文件 + dual-mode 契约）：
  - **§一 rd-develop.md dual-mode 化**：标题从"RD Subagent：TDD 开发 + 自查"改为"RD 开发执行规范：TDD 开发 + 自查（Dual-Mode）"；新增 7 维对比表（启动方式 / 上下文 / 输入来源 / 用户可见性 / 进度汇报 / 最终输出 / 适用场景）+ 5 条 🔴 共同契约（TDD / UI 还原自检 / 自查 7 维度 / 产物格式 / auto-commit）；§二 输入文件加模式对比（主对话直读 + 可复用已加载 vs subagent 按 dispatch 硬读）；§四 执行摘要拆 4.1a 主对话（边做边汇报模板 + 5 个阶段性节点）+ 4.1b subagent（完成后一次性返回含 TDD 阶段耗时）；§四.2 RD 自查报告 + §四.3 上游问题清单两模式一致不变；UI 还原 NEEDS_FIX 自降规则改"两种模式一致"
  - **§二 dev-stage.md AI Plan 指引改写**：条件表从"AI 自主按规模判断"升级为"默认 main-conversation + 超阈值 opt-in subagent"5 行条件：默认无特别信号 → main / 文件 >10 或 >500 行 → subagent / 跨模型独立性 → subagent / 多轮调试跨 Feature → main 强化 / 灰色地带向默认倾斜；新增 3 条灰色地带判定示例（10 文件/400 行/单模块、12 文件/600 行/跨前后端、8 文件/300 行/3 轮 TDD 调试）；Duration baseline 前置主对话路径（≤3 文件 15-25 / 5-10 文件 30-60）+ subagent 档（>10 文件 30-90 含冷启动税）
  - **§三 agents/README.md §一默认表**：Dev Stage 行从"AI 自主按规模判断"改为"main-conversation（v7.3.9+P0-14 默认）"；判断列改"默认主对话；TECH 文件清单 >10 / 预期产出 >500 行 / 需独立聚焦 → subagent（opt-in）"
  - **§四 feature-state.json 示例**：planned_execution.dev 主示例改 approach="main-conversation" + rationale 引用 P0-14 默认 + 无 dispatch_file 字段（加 `_dispatch_file_comment_v7.3.9+P0-14` 解释）；保留 `_subagent_alternative_example` 子对象作为 opt-in 样例（TECH >10 文件的场景）
- 收益：
  - 默认 Feature 节省 3-5 min subagent 冷启动 + 5-10K token（复用 Plan/Blueprint 已加载产物）
  - TDD 过程用户可见 → 早发现方向偏差 / 提前介入多轮调试
  - Subagent opt-in 通道保留，大改动 / 跨前后端场景不牺牲独立聚焦
  - RD 自查 + UI 还原自检 + NEEDS_FIX gate 两模式完全一致，契约不变
  - dual-mode 表 + rationale 要求 → RD 在 Plan 阶段的判断更透明（retro 可统计默认采纳率、subagent opt-in 比例）
- 兼容性：
  - 既存 Feature（已完成 Plan/Blueprint）不受影响；Dev Stage 未启动的 Feature 进入 Dev Stage 时按新默认
  - 既存 dispatch_log（已派发 subagent 的 RD 任务）保持有效 —— subagent 模式路径完整保留，只是不再是默认
  - state.json schema 不变（approach 字段早已支持 main-conversation / subagent / hybrid）
  - rd-develop.md dual-mode 化后 Codex CLI 子 agent（若有）仍可按原 prompt 调用（subagent 模式契约未变）
- 未变更：
  - TDD 红-绿-重构三步流程（§三.1）/ 开发约束（§三.2）/ RD 自查 7 维度（§三.3）/ UI 还原权威层级 + 自检清单（§三.4，P0-12 成果）全部保持不变
  - DONE / NEEDS_FIX / FAILED 三态 gate + UI 还原缺失自降 NEEDS_FIX 规则不变
  - Review Stage 三视角契约不变（本 P0 只改 Dev Stage 执行方式默认）
  - Codex CLI 子 agent / subagent dispatch.md 协议 / standards/{common,backend,frontend}.md 加载规则均保持

### P0-13：Plan/Blueprint Codex 交叉评审 降为 opt-in 默认 OFF（成本治理 · templates/codex-cross-review.md + plan-stage.md + blueprint-stage.md + roles/pmo.md + FLOWS.md + feature-state.json）

- 触发：用户明确反馈"Feature 流程每次都强制 Codex 成本太高，PRD 流程也不需要"。审计发现 Plan + Blueprint Stage 的 Codex 交叉评审每次 +10-20 min + ~10K token，对小改动 / 内部视角已充分的场景 ROI 偏低。
- 决策：**Plan + Blueprint Stage** 的 Codex 交叉评审从 🔴 强制降为 🟡 opt-in 默认 OFF；**Review Stage** 的 Codex 代码审查保持 🔴 强制不变（其盲区独立采样 + 静态分析价值最高，且是代码层最后一道质量 gate）。
- 根因分析：
  - Plan/Blueprint 产物为文档（PRD / TC / TECH），内部多视角评审（PM + PL + RD + Designer + QA + PMO + 架构师）已覆盖质量下限；Codex 的增量价值随 Feature 规模递减
  - Review Stage 的 Codex 是代码层盲区兜底，与其他场景不同 —— 代码 bug 进入代码库的代价远高于文档修订，Codex 在此保留强制
  - 先前"🔴 强制"设计偏向保守，缺乏"用户可按风险/规模动态开关"的弹性
- 处理（6 文件 + 3 层开关）：
  - **Schema 层**：`templates/feature-state.json` 新增 `codex_cross_review = {enabled, decided_at, decided_by, note}` 字段，默认 `enabled: false`；_comment 明确 Review Stage 不受本开关影响
  - **决策点层（PMO 初步分析）**：
    - `FLOWS.md` PMO 初步分析输出格式 4 种变体（Feature / 敏捷需求 / Feature Planning / 跨子项目）追加「🤖 Codex 交叉评审决策」行，4 选 1 默认不开
    - `roles/pmo.md` 新增「🤖 Codex 交叉评审开关决策」独立章节，含建议逻辑（规模/风险信号）+ state.json 写入规范 + 硬规则（默认 OFF / 必须显式输出 / Review Stage 独立）
  - **执行层（Stage 内条件化）**：
    - `stages/plan-stage.md` Input Contract 的 codex-cross-review.md 改为条件必读（`enabled==true`）；Process Contract Step 3 的 Codex 改为 opt-in + 关闭时声明；过程硬规则 5 条 Codex 相关项从 🔴 降为 🟡；Output Contract 表格加条件列（pmo-internal-review / prd-codex-review 仅开启时必需）；机器校验分两组（开启/关闭）
    - `stages/blueprint-stage.md` 同 pattern：本 Stage 职责描述、Input Contract、Process Contract Step 5、过程硬规则、Output Contract 表格、机器校验、Done 判据、AI Plan 模式指引、执行报告模板 全部条件化
  - **治理层**：`templates/codex-cross-review.md` §二适用场景表 Feature / Feature Planning / 敏捷需求的 Plan/Blueprint 列统一改为"🟡 opt-in（默认 OFF）"；新增 §2.1「PMO 初步分析决策」规范 + §八 R7 改写为 P0-13 修订说明 + 明确 Review Stage 独立强制
- 收益：
  - 默认场景节省 10-20 min + ~10K token（小改动 / 单子项目 / 内部视角充分的场景多数符合）
  - 保留 opt-in 通道（大改动 / 跨子项目 / 高风险场景用户主动开启）
  - Review Stage 代码审查保持强制，代码层最后一道 gate 不放松
  - state.json 持久化开关 + 决策留痕（decided_at / decided_by / note）便于 retro 分析采纳率
- 兼容性：
  - 既存 state.json（v7.3.9 + P0-11 及之前）**缺少 codex_cross_review 字段** → PMO 读取时按 "enabled=false" 默认处理（等价"关闭"），不触发迁移
  - 既存 Feature（已完成 Plan/Blueprint）不受影响；当前进行中的 Feature 若已完成 Plan Stage 产物，Blueprint Stage 进入时由 PMO 补写 codex_cross_review（enabled=false，note="既存 Feature 默认关闭"）
  - codex-cross-review.md / codex-agents/*.toml / prd-reviewer / blueprint-reviewer 均保留（开启时走原路径）
- 未变更：
  - Review Stage 的 Codex 代码审查：🔴 强制不变（review-stage.md + codex-agents/code-reviewer.toml）
  - 4 流程（Bug / 问题排查 / Micro / Feature Planning）与 Codex 的关系：Bug / 问题排查 / Micro 本就跳过 Codex；Feature Planning 沿用 Feature 同规则（opt-in 默认 OFF）
  - 降级路径、独立性校验、输出 schema、findings 分类规则：开启时完全复用原规范

### P0-12：preview/*.html 漏传 + UI 还原权威层级（实战漏洞修复 · dispatch.md + dev-stage.md + rd-develop.md + roles/pmo.md）

- 触发：实战 case —— RD 实现页面时"遵循了文字规格却没还原 HTML 预览稿"，PM 验收发现明显偏差，被迫走 Bug 流程。
- 根因分析（两层叠加）：
  - **第一层：preview 漏传**。`templates/dispatch.md` 的 Input files 清单只列了通用项（README / agent md / standards），Feature 产物走占位符 `{其他必需文件绝对路径}`；同时 `stages/dev-stage.md` L30 的必读清单里 `UI.md + preview/*.html` 用"（如有）"措辞，让 PMO 把一定存在的 preview 当成可选 → 起草 dispatch 时漏列。RD subagent 只看 dispatch Input files，不会主动翻 roles/stages，漏列 = 真漏传。
  - **第二层：即便传了也没权威层级**。`agents/rd-develop.md` 原 Step 5 只写"如有 UI → 还原页面"，没定义 preview 和文字规格冲突时谁是权威；LLM 天然偏好结构化文本（PRD/TECH.md）→ 视觉 / 交互偏差。
- 处理（4 文件 + 三层防护）：
  - **第一层（模板硬化）**：`templates/dispatch.md` 新增「🔴 Feature 产物强制白名单」段，按 Stage 列出 blueprint / dev / review / test / browser-e2e 的必选 Feature 产物；Dev Stage 在 `ui_design.output_satisfied==true` 条件下 **显式要求 UI.md + preview/*.html 进 Input files**；附反模式："把 preview 当'可选参考'仅在 Additional inline context 里提一嘴"。
  - **第二层（措辞硬化）**：`stages/dev-stage.md` L30 去掉"（如有）"暧昧措辞，改为条件式："若 `state.stage_contracts.ui_design.output_satisfied==true` → 必读（视觉/交互权威）"；L86 还原段引用 rd-develop.md 的 UI 还原权威层级 + 自检。
  - **第三层（RD 侧权威层级 + 自检）**：`agents/rd-develop.md` 新增 §三.4 「UI 还原（有 preview 时必做）」：
    - 权威层级（冲突时优先级）：视觉/间距/颜色/响应式 → preview 权威；交互状态 → preview 权威，未覆盖看 TECH；业务逻辑 → TECH 权威，禁止照抄 preview mock 数据；验收判定 → TC 权威
    - 冲突兜底：preview 视觉 ≠ PRD 文字 → 以 preview 为准 + concerns 1 行；preview 交互 ≠ TC AC → 以 TC 为准 + concerns
    - UI 还原自检清单（Dev 完成前必做）：视觉 / 交互状态 / 响应式 / 偏离项 concerns / mock 数据未照抄 / preview 未覆盖状态找依据
    - 反模式 4 条
    - 自查表新增 UI 还原 4 行（视觉 / 交互 / 响应式 / 偏离 concerns），**缺失或未贴证据 → 自降 NEEDS_FIX**
  - **PMO 侧硬校验**：`roles/pmo.md` 进入 Stage 的 subagent 路径新增"Feature 产物白名单硬校验"：若 `ui_design.output_satisfied==true` 但 Input files 未包含 UI.md + preview → **PMO 自拒重生**，不得发出。
- 收益：
  - 漏传链路补齐（模板白名单 + 措辞硬化 + PMO 自校验 + Subagent `NEEDS_CONTEXT` 兜底，四层 gate）
  - 权威层级清晰（冲突时有规可循，不再靠 LLM 天然偏好）
  - 自检 gate 可执行（7 项清单 + DONE/NEEDS_FIX 硬绑定，漂移可被拦截）
  - 反模式负向定义（过度还原 / 欠还原 各自拦截，避免从一个坑跳进另一个坑）
- 兼容性：UI Design Stage 未跑的 Feature 流程完全不变；preview 不存在时自检项填 "-" + 说明"无 UI Design 产物"。

### P0-11-B：auto 模式默认跳过 Browser E2E Stage（roles/pmo.md + rules/flow-transitions.md + INIT.md）

- 触发：Browser E2E Stage 启动成本显著（headless 浏览器冷启动 / MCP 握手 / 脚本录制回放），auto 模式下默认应倾向"快速走完主干"。用户明确要求："auto 模式默认不启动 browser-e2e"。
- 处理（3 文件，新增"默认跳过 + 可逃逸 + 必留痕"三件套）：
  - **默认跳过条件**：`AUTO_MODE=true` + Test Stage 完成 + `TC.md` 含 Browser E2E AC → **跳过 Browser E2E Stage**，直接进 PM 验收
  - **留痕（三处，便于事后追溯 / PM 验收判断）**：
    - `state.json.stage_contracts.browser_e2e = {status: "SKIPPED_BY_AUTO", skipped_at, skip_reason}`
    - `review-log.jsonl` 追加一行 `{event: "browser_e2e_skipped_by_auto", feature_id, timestamp}`
    - PMO 输出 `⚡ auto skip: Browser E2E Stage | 💡 直接进 PM 验收 | 📝 AUTO_MODE 默认跳过` 日志
  - **显式标注（PM 验收 / 完成报告）**：PM 验收摘要和完成报告必须打出「⚠️ Browser E2E 已按 auto 模式跳过」提醒
  - **用户逃逸路径（两种）**：
    - PM 验收时选"3 返修"+ 备注「跑 Browser E2E」→ 下轮补跑
    - 下轮命令带「含 browser e2e / 带 e2e / run e2e」关键词 → 例外命中，不跳过
  - **例外（不跳过）**：命令关键词命中 / `TC.md required_even_in_auto=true` / 手动模式（AUTO_MODE=false，原流程不变）
  - **文件落点**：
    - `roles/pmo.md` 豁免表新增 Browser E2E 行 + 新增「🟡 Browser E2E auto 默认跳过（P0-11-B 新增专项规则）」专章（含触发 / 留痕 / 标注 / 逃逸 / 例外 / 设计理由）
    - `rules/flow-transitions.md` 顶部 auto 豁免速查增补 Browser E2E 子块
    - `INIT.md` Step 0 速查表补一条"Browser E2E auto 默认跳过"规则
- 设计理由：
  - Browser E2E 启动成本明显高于其他 Stage（浏览器进程 / 录屏 / 网络往返），auto 的设计目标是"压暂停点"而非"压成本"，但 Browser E2E 是单 Stage 成本占比最高的一环，跳过的 ROI 显著
  - PM 验收本就是 auto 模式下的强制保留点（业务决策），Browser E2E 缺失由 PM 在验收时决定是否补跑，链路闭环
  - 三处留痕确保"跳过"可审计、可回溯、不静默
- 收益：auto 模式全链路时长显著缩短（省去 Browser E2E Stage 整段）；用户可通过"关键词显式要 E2E"或"PM 验收补跑"双通道保留覆盖能力；跳过决策留痕三处，事后可查。
- 兼容性：手动模式（AUTO_MODE=false）流程完全不变；`TC.md required_even_in_auto=true` 是显式覆盖开关，向前兼容。

### P0-11-A：auto 模式豁免/保留边界修订（实战漏洞修复 · INIT.md + roles/pmo.md + flow-transitions.md）

- 触发：P0-11 落地首轮实战，用户 `/teamwork auto ... 推进到 Blueprint 完成` 命令被中间"外部依赖已就绪 → 恢复流程"暂停点卡住。根因：P0-11 原强制保留清单把"外部依赖恢复"归为保留，与 auto 模式设计意图直接冲突。
- 根因分析：
  - 暂停点的本质 = 请求用户给出**决策内容**
  - 若决策内容已被 `/teamwork auto [推进/恢复/继续...]` 命令语境承载 → 再停下来要一次确认 = 把命令意图当空气
  - 强制保留的合理边界 = 需要**新**决策内容（业务判断 / 技术分歧 / 破坏性授权 / 红线处理）
- 处理（3 文件）：
  - **新增元规则「意图承载豁免」** 写进 `roles/pmo.md` + `rules/flow-transitions.md` + `INIT.md`：判定前先问「此暂停点需要的决策内容是否已被 auto 命令承载？」；是则豁免，否则保留
  - **从强制保留清单移除 2 项**（归入豁免）：
    - ~~外部依赖已就绪 → 恢复流程~~ → 豁免：auto 命令已承载"恢复"意图
    - ~~Planning / PL 模式的最终确认~~ → 豁免：auto 命令已承载"推进"意图（且原豁免表已有 Roadmap / teamwork_space / Workspace Planning 收尾行覆盖）
  - **新增 Test Stage 前置确认 到强制保留**（原遗漏补齐）：跨 Feature 节奏决策，需用户判断立即 / 延后 / 跳过
  - 强制保留清单从 15 项收敛到 **13 项**（边界更锐利）
  - **反模式样例**写进文档：「auto 命令明说推进到 X，却被中间恢复确认卡住 = 把用户意图当空气」
- 收益：
  - auto 模式实战可用——用户给定终点的命令不会被"你确定要继续吗"类暂停点坍缩
  - 强制保留语义从"列表式枚举"升级为"决策类型判定"，新暂停点上线时可按元规则快速归类
  - 反模式样例给 PMO 自检提供具体参照

### P0-11：⚡ auto 模式（一次性总开关，INIT.md + roles/pmo.md + flow-transitions.md + STATUS-LINE.md）

- 背景：teamwork 暂停点密集（Feature 流程单次跑全流程 10+ 次 ⏸️），对"我已经心里有数、按你建议走"的场景体验重。需要一个一次性总开关让 PMO 按 💡 自动推进，同时保留关键决策的强制暂停。
- 设计取舍（6 点均按用户"按建议"确认）：
  1. **入口命令**：`/teamwork auto [需求]` / `/teamwork auto 继续` / `/teamwork auto ship F{编号}`（第一个 token 为 `auto` 开启）
  2. **作用域**：单次命令周期（仅本次 /teamwork 生命周期有效）；用户重新 `/teamwork`（不带 auto）自动重置；compact 后默认 false；**不写 localconfig / state.json**（避免"以为关了其实没关"）
  3. **豁免范围**：普通方案 review / 阶段切换 / preflight 默认值 / PRD-UI-TC-TECH 草稿 review / dispatch 前检 / review 结果接受
  4. **强制保留 15 项**（按 roles/pmo.md 强制保留清单）：PM 验收三选项 / Ship 关键操作 / Blueprint concerns / MUST-CHANGE / 破坏性操作 / 13 红线 / Micro 用户验收 / 外部依赖解锁 / 意图不确定语气 等
  5. **与 ship_policy 正交**：auto 是 session 级总开关，ship_policy 是 Ship Stage 细粒度；auto **不覆盖** `ship_policy=confirm`
  6. **关闭方式**：命令级（下次不带 auto 即手动）+ 运行时（用户消息含「停 / 暂停 / manual / 等一下 / 先等等」立即关闭）
- 处理（5 文件）：
  - `INIT.md` 启动必做前加 **Step 0**：解析 `/teamwork auto` 命令行 + 速查豁免与强制保留清单
  - `roles/pmo.md` 在 "⚡ PMO 自动推进规则" 后新增 **"⚡ auto 模式暂停点豁免规则"** 章节：触发时机 / 豁免表 / 强制保留 15 项表 / 跳过日志格式 / 强制保留命中提示格式 / PMO 自检清单 / 运行时关闭
  - `rules/flow-transitions.md` 顶部新增 **"⚡ auto 模式豁免速查"** 块：列出所有强制保留行号+理由；给出典型豁免示例（其余默认豁免）
  - `STATUS-LINE.md` 第一行格式增加可选 **`⚡ AUTO` 徽章**（AUTO_MODE=true 时在 `🔄 Teamwork 模式` 和 `|` 之间显示）+ 状态行规则 + 示例
  - 跳过日志：`⚡ auto skip: {决策简述} | 💡 {建议} | 📝 {理由}` 每次豁免输出一行，便于追溯
- 收益：
  - 一次性开关覆盖高频 ⏸️，用户体验从"每步都要回确认"降到"关键处再决策"
  - 作用域仅 per-command，不污染 localconfig，降低"隐藏状态"事故面
  - 强制保留清单明确兜底所有破坏性 / 业务判断 / 红线场景
  - 跳过日志 + 徽章让"auto 到底替我做了什么"完全可见
  - 与 P0-9（worktree 默认 off）形成对称：worktree 需显式 opt-in，auto 也需显式 opt-in；不隐藏复杂性

### P0-9：worktree 保留默认 off（设计决策 · templates/config.md + INIT.md 决策注释）

- 背景：曾考虑把 worktree 默认从 off 翻转到 auto（让新用户开箱即得并行隔离），深入讨论后回撤，**保留 off 为默认**。
- 回撤理由（四个税点，默认 auto 让新用户透明付费不合理）：
  1. **megarepo 全量 checkout 代价**：`git worktree add` 不支持按子目录稀疏 checkout（需额外配 `git sparse-checkout`）；大仓并行 3 个 Feature = 3 份全量工作树（每份 ~GB 量级），磁盘 / IDE 索引 / 工具链遍历开销显著
  2. **IDE review 不便**：worktree 在 sibling 目录下，IDEA 单 Project 窗口看不到其他 worktree 的代码 / 文档；VS Code 需要 Multi-root Workspace 配置；跨 worktree Cmd+Click / 搜索被割裂
  3. **`.worktree/` 内嵌方案的隐性长尾**：即便内嵌到项目根 + `.gitignore`，仍需为每个扫描项目根的工具（tsc / eslint / prettier / jest / pytest / webpack / nx / turbo / docker / IDE LSP / CI find-grep）单独维护排除规则——新工具加入默认踩坑
  4. **默认 auto 把复杂性隐藏**：用户不理解 worktree 语义时遇到上述问题会困惑，把选择权还给用户（显式 opt-in）更稳
- 处理：保持 off 为默认 + 把决策理由注释到 localconfig 模板：
  - `templates/config.md` 保留 `worktree: off`；注释块新增"保留 off 为默认的原因"四点说明，引导用户 opt-in 前先评估 P0-10 的 worktree_base + IDE workspace 自动配置（待实施）
  - `INIT.md` localconfig 不存在分支保持"默认 scope=all，worktree=off"，加提示"如需并行 Feature 隔离，主动改 localconfig 为 auto/manual"
  - `docs/OPTIMIZATION-PLAN.md` 历史记录段保持"默认 off"
- 收益：对初学者友好（不引入 worktree 的 megarepo / IDE review / 工具链忽略复杂性）；有需要的用户显式配置 auto/manual 时自担理解成本；为 P0-10（worktree 路径合法性 + 分组 `../.{repo}-worktrees/` + IDE workspace 自动生成）铺好 opt-in 路径。

### P0 影响面（非破坏性）

```
├── state.json schema：兼容（P0-3 新增 dev.dependency_install 可选字段；P0-2 plan_preflight.checks._note 注释；P0-5 复用既有 worktree + merge_target 字段；P0-6 无 schema 变化；P0-7 无 schema 变化，纯契约文档加强；P0-8 复用既有 blocking.pending_external_deps 字段；P0-9 决策保留默认 off · 无默认值改动；P0-11 AUTO_MODE 纯运行时状态，不写 state.json / localconfig）
├── localconfig：无新增字段（P0-11 刻意不持久化 AUTO_MODE）
├── 历史 Feature：完全兼容（P0 是描述修正 + 文案抽取 + 渲染增强 + 宿主适配 + 格式权威契约 + 依赖识别前置 + 一次性 auto 总开关，不改流程语义）
└── CI / 工具链：无影响（P0-6-A 浏览器工具为宿主可选，项目未启用 Browser E2E 不受影响；P0-7/P0-8/P0-11 纯文档与运行时规则；P0-9 设计决策）
```

### P0 后未涉及的内容

```
- Ship Stage / PM 验收三选项 / merge_target 三层解析：保持 v7.3.9 定义
- 红线 #1 例外条款：保持 v7.3.9 定义
- Micro 流程 worktree 方案：暂缓（见 docs 讨论，待真实需求再做）
```

---

## v7.3.9 —— PM 验收三选项 + Ship Stage + 每阶段 auto-commit + Plan Stage 入口 Preflight

背景：v7.3.4 的 PM 验收合并暂停点（验收 + commit + push 三项打包）存在 3 个结构性缺陷：
1. **合并目标缺省硬编码**：push 目标默认 `origin/{feature branch}`，用户真正的目标分支（staging / develop）无处配置，合入动作被迫延后到命令行手工解决
2. **单暂停点承载过多决策**：验收 + commit 策略 + push 策略 + 目标分支挤在一个暂停点，用户必须一次回答完，错一个选项回退代价极高
3. **冲突 / 净化 / rebase 无流程位**：push 前是否需要 rebase、feature 分支有无需要净化的残留 commit（debug 文件、合并遗留）、冲突解决授权——这些本质是 Ship 流程问题，塞在 PM 验收里越想越不对

同时在使用过程中发现另一个风险源：**Feature 的全部产物（PRD/UI/TC/TECH/代码/测试）都从 Plan Stage 开始累积**。如果 worktree 基于错误的 base 分支（陈旧 main 而非 origin/staging），到 Ship 时 rebase onto staging 会遇到大规模冲突——此时产物已成定局，回退代价高于 Ship 本身。v7.3.8 的"前移 worktree 创建"只解决了隔离问题，没解决 base 问题。

本版把 v7.3.4 的 PM 验收合并暂停点**拆解成 3 段**，并在 Plan Stage 入口加一层 preflight：

```
v7.3.4（旧）：PM 验收 → ⏸️（3 选 1 全打包）→ 完成 / 合入
v7.3.9（新）：PM 验收 → ⏸️ 3 选 1（业务判断）→ Ship Stage（PMO 自主合并） → ⏸️ 2 选 1（push 目标分支或仅本地）→ ⏸️ worktree 清理 → 完成
            ↑
            Plan Stage 入口 preflight（v7.3.9 新增）提前锁定 base 分支，防止 Ship 时灾难
```

### 1) PM 验收三选项（roles/pmo.md + rules/flow-transitions.md）

- **选 1**：通过 + Ship → 进入 Ship Stage（独立 Stage）
- **选 2**：通过但暂不 Ship → PMO 执行 `git push origin {feature branch}` 归档 `shipped: false`，后续可 `/teamwork ship F{编号}` 触发
- **选 3**：不通过（有建议）→ 按问题类型回退（功能缺陷 → Review Stage / 测试遗漏 → Test Stage / UI 不符 → UI Design / 需求偏差 → Plan Stage），前序 commit 保留，修复循环 ≤3 轮

### 2) Ship Stage（新建独立 Stage，stages/ship-stage.md）

- **PMO 自主执行 Step 1-4**：净化 → push feature → rebase 可选（`ship_rebase_before_push` 默认 false，多人场景兼容）→ 本地 merge --no-ff onto `merge_target`
- **单一暂停点 2 选 1**：merge + push `{merge_target}` / 仅本地 merge 不 push
- **worktree 清理暂停点**：worktree ≠ off 时询问清理 / 保留
- **冲突授权**（红线 #1 例外）：PMO 可直接解 git marker 冲突（前提：前序 DONE + 单测全绿 + 解完重跑单测）；不满足升级 ⏸️ 用户决策
- **Sanitize 日志**：residual_commits（待审）/ cleaned_files（已处理）/ suspicious_files（灰名单仅报不动，用户决定）

### 3) 每阶段 auto-commit 硬规则（stages/dev-stage.md + review-stage.md + test-stage.md + browser-e2e-stage.md）

- 每个 Stage `output_satisfied=true` 之前 PMO 执行 `git status --porcelain`
- 非空 → PMO auto-commit `git add -A && git commit -m "F{编号}: {Stage} Stage - {简述}"`，commit hash 写入 `state.json.stage_contracts.{stage}.auto_commit`（单值）或 `auto_commit[]`（多轮修复）
- 目的：每个 Stage 产物落地即 commit，Ship Stage 不再需要"一次性收拾"所有遗留改动；同时给 Review Stage 提供稳定 diff 锚点

### 4) Plan Stage 入口 Preflight（stages/plan-stage.md + roles/pmo.md）

- PMO 在用户确认流程类型后、Plan Stage 产物诞生前执行 6 项校验：
  - 🔴 硬门禁：worktree 策略无残留 / 分支名无冲突 / base 分支可达
  - 🟡 软提示：工作区干净 / merge_target 解析清晰 / Feature 编号命名合规
- **worktree 创建显式指定 base**（v7.3.9 关键改动）：
  ```bash
  git fetch origin {merge_target}
  git worktree add ../feature-{全名} -b feature/{全名} "origin/{merge_target}"
  ```
- state.json 新增 `stage_contracts.plan_preflight` 记录 6 项校验结果 + base_branch

### 5) merge_target 配置三层解析（templates/config.md + feature-state.json）

- 优先级：`state.json.merge_target` > `.teamwork_localconfig.md` 中 `merge_target` > 默认 `staging`
- 新增 localconfig 字段：`merge_target` / `ship_rebase_before_push` / `ship_policy` / `worktree_cleanup`
- state.json 新增顶层 `ship` 块（sanitize_log / rebase_status / merge_commit_hash / push_status / worktree_cleanup / shipped）

### 6) 红线 #1 例外条款（INIT.md + SKILL.md）

- v7.3.9 新增 Ship Stage 冲突解决例外：PMO 可直接解 git marker 冲突，前提：前序 DONE + 单测全绿 + 解完重跑单测通过
- 不满足则升级为 ⏸️ 用户决策

### 7) flow-transitions.md 更新

- PM 验收行拆为 5 行（PM 验收三选项 / Ship Stage / merge+push 待确认 / worktree 清理待确认 / Ship Stage 冲突回退）
- PMO 初步分析 → Plan Stage 之间插入 Plan Stage 入口 preflight 暂停点

### 为什么这样拆（设计取舍）

| 候选设计 | 评估 |
|---------|------|
| ~~PM 验收暂停点内嵌 Ship 策略~~（v7.3.4）| 单点决策过多，回退代价高，用户体感卡 |
| ~~Ship 整个走 Subagent~~ | Feature 最后一步，主对话 context 已沉淀，新 Subagent 要 /clear 反而丢失一致性 |
| **Ship Stage 由 PMO 自主执行 + 两段暂停** ✅ | 决策维度清晰（业务判断 vs 合入策略 vs 清理策略），每段单点决策 |
| ~~Ship 时一次性 commit 所有 Stage 遗留~~ | 破坏 Stage 边界，diff 锚点模糊，review 困难 |
| **每 Stage 独立 auto-commit + Ship 仅净化** ✅ | Stage 产物落地即 commit，Ship 只解决 git 异常 |

### 不改动项（仍保留）

- Worktree 创建触发点仍在 Plan Stage 入口（v7.3.8 定稿）
- 默认 `worktree` 值仍为 `off`
- PMO 非 Micro 流程下不得改代码的红线 #1 主干不变（仅加 Ship Stage 例外）
- Review / Test / Browser E2E 的产物契约不变（只加 auto-commit 过程规则）

### 操作影响

- **新 Feature**：经历 6 步（preflight → Plan → ... → PM 验收 → Ship → 清理），每步暂停点用 1/2/3 编号单点决策
- **进行中 Feature**（v7.3.8 及之前启动）：到达 PM 验收时按新流程分叉（无 preflight 重跑），已累积的 commit 由 auto-commit 硬规则补齐
- **单分支用户**（merge_target = main）：ship_rebase_before_push = true 更合适，通过 localconfig 显式配置

## v7.3.8 —— Worktree 创建时机前移至 Plan Stage 入口

背景：v7.1 引入 worktree 集成，触发点放在"方案待确认 → Dev Stage"的流转（即 Blueprint 结束后）。这意味着 **Plan Stage 的 PRD/discuss/评审产物、UI Design 的 UI.md、Blueprint 的 TC/TECH**——一整套 Feature 早期文档都**落在 main 分支上**。这违反了 worktree 隔离的初衷：
- 用户拒绝 PRD → 一堆文档孤儿留在 main，要么 revert 要么保留
- v7.3.7 引入的 Codex 交叉评审读的是主分支 PRD，受 main 并发修改干扰
- 跨 Feature 并行时 Plan 阶段文档互相污染（F042 的 PRD 在 F043 工作区可见）

本版把 worktree 创建触发点从 Dev Stage 前移到 **Plan Stage 入口**（"PMO 初步分析 → Plan Stage"的流转上），让 Feature 一启动就进入自己的分支。

- **rules/flow-transitions.md**：Feature 流程触发点从第 19 行（方案待确认 → Dev Stage）移到第 11 行（PMO 初步分析 → Plan Stage）；敏捷需求流程对应在"PMO 分析 → 精简 PRD 编写"触发；Micro 流程在"PMO 分析 → Micro 变更说明"触发（分支名用 `chore/*`）
- **stages/plan-stage.md**：新增 §Worktree 集成段（触发时机 / auto 命令 / state.json 写入 / 降级链），前置依赖增补 "worktree 已创建切换" 条款
- **stages/dev-stage.md**：§Worktree 集成改为"校验存在 + 必要时补建"；补建场景（路径缺失 / 分支不匹配）作为异常分支保留，触发时写 WARN 到 state.json.concerns
- **INIT.md**：修正 "Dev Stage 前按策略创建" → "Plan Stage 入口按策略创建"

### 为什么是 Plan Stage 入口而不是其他点

| 候选 | 评估 |
|------|------|
| ~~Dev Stage 入口~~（v7.3.7 前）| Plan/UI/Blueprint 产物已落 main，隔离迟到 |
| ~~PMO 初步分析之前~~ | 用户还没确认流程类型，可能跳流程（走 Bug / 问题排查），空建 worktree 浪费 |
| **PMO 初步分析确认后，Plan Stage 入口** ✅ | 流程类型已定，第一份产物（PRD）就入 feature 分支 |
| ~~按 Stage 动态切换~~ | 每阶段切 worktree 碎片化，state.json 记录复杂度爆炸 |

### 分支命名规范（v7.3.8 正式化）

| 流程 | 分支名 | worktree 路径 |
|------|--------|--------------|
| Feature | `feature/{子项目缩写}-F{编号}-{功能名}` | `../feature-{...}` |
| 敏捷需求 | `feature/{子项目缩写}-F{编号}-{功能名}`（同 Feature）| `../feature-{...}` |
| Bug 处理 | `bugfix/{子项目缩写}-B{编号}-{摘要}` | `../bugfix-{...}` |
| Micro | `chore/{Micro 摘要}` | `../chore-{...}` |
| 问题排查 | （按需，通常不建）| - |

### 降级链（auto → manual → off）

每档降级必须写 WARN 到 `state.json.concerns`：
- `auto` 失败（git 不可用 / worktree add 错误 / 磁盘不足）→ 降 `manual`
- `manual` 用户 2 次未响应 → 降 `off`
- `off` → 所有阶段在当前工作区执行，跨 Feature 约束回退为人工注意力（原 v7.3.7 行为）

### 不改动项（仍保留）

- **默认值** 仍为 `off`（降低新用户门槛；建议 1 未落地）——已启用 teamwork 的用户可显式改为 auto
- **清理时机** 仍在 commit+push 完成后，PMO 询问用户（不自动删）
- **命令规范** 仍用标准 `git worktree add/remove/list`

### 操作影响

- **新 Feature**：启动即进入 feature 分支，所有阶段产物自然隔离
- **进行中 Feature**（v7.3.7 及之前启动）：不做迁移，保持原路径完成
- **worktree=off 用户**：零影响，行为不变

## v7.3.7 —— PRD/Blueprint Codex 交叉评审 + Progress Log 实时轮询

本版解决两个独立问题：
1. Codex 交叉评审之前只存在于 Review Stage（代码审查），Plan Stage 的 PRD 和 Blueprint Stage 的 TC+TECH 缺少外部视角保底，导致同模型多角色评审的注意力盲点无法被捕获
2. v7.2 建立的 Progress Log 三段式协议声明"Subagent → 主对话无实时通道"——这是**反事实陈述**，文件系统本身就是天然的异步实时通道。主对话读 dispatch 文件可随时获取进度，无需宿主 API 支持

### 1) Codex 交叉评审扩展到 Plan / Blueprint Stage

- **新建 `codex-agents/prd-reviewer.toml`**：Plan Stage PRD 外部评审 agent，独立性通过产物 frontmatter (`perspective: external-codex` + `files_read` grep) 强制，`sandbox_mode = read-only`
- **新建 `codex-agents/blueprint-reviewer.toml`**：Blueprint Stage TC+TECH 外部评审 agent，Step 5 在 4 步内部闭环（QA TC → TC 评审 → RD TECH → 架构师评审）之后执行
- **新建 `templates/codex-cross-review.md`**（230 行）：6 项 checklist (C1-C6) 针对 PRD 和 TC+TECH 两个变体、YAML 输出 schema、PMO 整合流程（ADOPT/REJECT/DEFER 分类）、降级处理、成本治理
- **stages/plan-stage.md**：多视角评审 4 → 5（加 Codex），新增 pmo-internal-review.md 作为 dispatch 前置（≥3 条实质 finding），PRD-REVIEW.md 尾部加「Codex 交叉评审整合」section
- **stages/blueprint-stage.md**：4 步闭环后追加 Step 5 Codex 交叉评审；TC-REVIEW/TECH-REVIEW 分别 append Codex 整合段；独立性 grep 校验加入机器可校验清单
- **templates/review-log.jsonl**：stage 枚举新增 `plan-codex-review` / `blueprint-codex-review`；补两者建行规则 + 示例行
- **codex-agents/README.md**：索引表增补两行

### 2) Progress Log 升级：四段式协议，支持运行中轮询

- **templates/dispatch.md Progress Log 段修订**：
  - 双重目的明确：运行中（主对话并发 Read）+ 运行后（PMO 时间轴回放）
  - 🔴 新增 **Append 语义硬规则**：`f.write() + f.flush() + os.fsync()` / shell `>>` / Edit 工具，禁止 buffered I/O 导致主对话读到空段误判卡死
  - 反模式表新增 2 条：buffered append、主对话绕过 Progress Log 读 session JSONL
- **templates/dispatch.md PMO 使用流程新增 Step 2.5（Subagent 运行中 — 主对话按需轮询）**：
  - 触发条件：用户问进度 / >5min dispatch / 并行多路
  - 读法：offset 跳到 Progress Log 段 + 增量对比
  - 节奏上限：用户触发即读，不建议 <10s tight loop
  - 🔴 显式禁止读 subagent session JSONL 当进度源（格式不稳定、非协议产物）
- **设计原则 #8 修订**：三段式 → **四段式**（前置预声明 / 中途自述 / 运行中轮询 / 事后回放）；删除"无实时通道"的反事实陈述
- **agents/README.md §2.5 + §五 Progress 可见性协议**同步修订：四段式协议、flush 语义、运行中轮询明细（相同修订在两个文件落地保证一致）

### 为什么要纠正"无实时通道"陈述

v7.2 起的原版陈述是基于宿主 Task/Agent API 同步阻塞推出的。这个推论本身没错——宿主 API 确实同步。但结论错了：**Subagent 和主对话共享文件系统**，Subagent 写 dispatch 文件、主对话随时 Read 同一文件，这就是异步实时通道。v7.3.7 前用户问"Subagent 现在到哪步了？"时，主对话会引用不存在的"规范禁止读 transcript"搪塞，实际上协议允许的正确操作是 **Read dispatch 文件的 Progress Log 段**。本版把这个隐含能力显式化为协议条款。

### 操作影响

- **Subagent 作者**：原有 Progress Log 逻辑照跑，仅需保证 append 时 flush（Python 加 `f.flush(); os.fsync(f.fileno())`；shell/Edit 天然满足）
- **主对话 / PMO**：用户问进度时可直接 `Read {dispatch 文件} → offset=Progress Log 段` 返回增量；并行 dispatch 依次读 N 个文件
- **Plan / Blueprint Stage 执行**：内部评审结束后多一步 Codex dispatch + 整合（预估 +5-10min），Codex 不可用按 agents/README.md §三 三选一降级

## v7.3.6 —— 多决策点支持：数字决策点 + 字母选项（`1A 2B`）

背景：v7.3.5 单决策点编号化后，实际使用中遇到**一个暂停点需要同时确认多个独立决策**的场景（如 PRD 评审收尾时「PRD 通过？」+「排期方案？」同时浮现）。v7.3.5 没定义多决策点格式，AI 自发用 `①②③` 分隔决策点，但圆圈数字需要输入法切换，用户打字不便。

本版固化多决策点格式：**决策点用数字（1./2./3.），选项用字母（A./B./C./D.），用户回复 `1A 2B` 这种组合**。

- **RULES.md 暂停输出规范第 2 条扩展**：
  - 2.1 单决策点（不变）：选项 1/2/3/4 编号
  - 2.2 多决策点（新增）：决策点用 `1.` `2.` `3.` 分隔，内部选项用 `A.` `B.` `C.` `D.`，用户回 `1A 2B`
  - 2.3 何时合并 vs 拆分：同时到达且独立 → 合并；后者依赖前者结果 → 拆分；上限 3 个决策点
  - 2.4 打字友好性原则：优先英文键盘直接敲出的字符，禁止 ①②③ / 罗马数字 / emoji 编号
- **模糊确认处理更新**：支持 `1A 2B` / `1A2B` / `1a 2b`（大小写不敏感）解析；数量不匹配 → 回问补齐
- **SKILL.md 红线 #10 摘要补充**：明确单决策点 vs 多决策点的编号字符规则
- **正反例对比新增**：反例 2 展示 `①1 ②2` 为何被禁；正例 2 展示 PRD+排期实际场景用 `1A 2B`

### 用户打字成本对比

| 格式 | 示例 | 字符数 | 输入法切换 |
|------|------|--------|-----------|
| v7.3.5 单决策 | `1` | 1 | 否 |
| v7.3.6 多决策（2 项）| `1A 2B` | 5 | 否 |
| ❌ 禁止（圆圈）| `①1 ②2` | 5 但需切换 | **是** |

多决策点使用指引：
```
⏸️ 请确认以下两件事（回复 "1A 2B" 这种组合即可）

1. PRD 是否通过：
   A. 通过 ← 💡 推荐
   B. 修改某条
   C. 忽略某条（需说明理由）
   D. 其他指示

2. 排期方案：
   A. 并行推进 ← 💡 推荐
   B. F003a 优先
   C. F013 优先
   D. 其他指示

回复示例：`1A 2A` 双采纳 / `1A 2B` / `1B 2A` / 自然语言
```

非暂停点文本（如 arch-code-review 的 ①②③ 路径标签、roadmap 验收条件编号）不受影响——本规则只管"用户需要打字回复"的暂停点格式。

### 单决策点禁止套多决策壳（v7.3.6 后补反例 3）

AI 引入多决策点格式后可能过度泛化，把**单决策点**也套 `1. {决策} / A./B./C.` 壳，让用户要回 `1A`。硬规则明确：**只有 ≥2 个独立决策点**才启用数字+字母格式；1 个决策就是 1 个决策，直接数字选项。

```
❌ 反例 3：
⏸️ 是否同步 DEPENDENCY-REQUESTS.md DEP-003？
1. 是否同步 DEPENDENCY-REQUESTS.md DEP-003？
   - A. 立即修正（💡 推荐）
   - B. 暂缓
   - C. 其他指示
（外层 "1." 是虚的 + 用户要回 `1A`）

✅ 正例 3：
⏸️ 请选择（回复数字即可）
1. 立即修正 DEPENDENCY-REQUESTS.md DEP-003 ← 💡 推荐
2. 暂缓（保留文档现状）
3. 其他指示
（用户回 `1` 完事）
```

## v7.3.5 —— 暂停点选项编号化（用户回复数字即可）

背景：用户观察到当前暂停点用描述式选项（`- 跳过（推荐）` / `- 跑 Browser E2E`），用户需要打字回复，不如直接敲数字快。本次改为所有可选项编号化（1/2/3...），用户回复数字即直达对应动作。

- **RULES.md「暂停输出规范」加第 2 条硬规则**（选项编号化）：
  - 所有可选项必须以 `1/2/3...` 编号列出
  - 第一项是 PMO 推荐（与 💡 建议 一致，标注「💡 推荐」）
  - 最后一项始终为「其他指示（自由输入）」
  - 提示语统一："⏸️ 请选择（回复数字即可）"
  - ❌ 禁止描述式选项（`- 跳过` / `- 跑 E2E`）
  - ❌ 禁止用字母（A/B/C）—— 统一数字
  - 模糊确认处理更新：用户回纯数字 → 直接映射到对应选项执行
  - 附"反例 vs 正例"对比
- **SKILL.md 红线 #10 微调**：明确"所有可选项必须编号列出，用户回数字即可"
- **roles/pmo.md 更新具体模板**：
  - PM 验收 + commit + push 合并暂停点：1-4 编号（推荐 1 / 本地 commit / 修复 / 其他）
  - Test Stage 前置确认：A/B/C → 1/2/3（立即执行 / 延后 / 跳过 / 其他）
- **FLOWS.md 问题排查流程**：选项改编号化
- **RULES.md §四流转链 + Test Stage 相关段**：A/B/C 全部替换为 1/2/3
- **STATUS-LINE.md**：A/B/C 提及改数字

核心体验变化：

```
❌ v7.3.4 前（用户要打字）：
⏸️ 请回复
- 跳过（推荐，直接 PM 验收）
- 跑 Browser E2E
- 其他指示

✅ v7.3.5（用户回数字）：
⏸️ 请选择（回复数字即可）
1. 跳过 Browser E2E，直接进入 PM 验收 ← 💡 推荐
2. 跑 Browser E2E（+15-25 min）
3. 其他指示（自由输入）
```

用户可回 `1` / `2` / `3` 或自然语言覆盖默认。打字量从一串降为一个字符。

注：现存 Feature 目录内可能已有按旧模板写的暂停点，不回溯修改；PMO 下次输出暂停点时按新模板即可。

## v7.3.4 —— 暂停点压缩（P0）：UI+全景合并 + 验收+commit+push 合并

背景：v7.3.3 跑 Feature 发现典型流程有 6-8 个暂停点，反复打断用户。前期讨论后确认走「方案 A：批量确认」，本次是 P0 阶段：合并两组暂停点（UI+全景、PM 验收+commit+push）。核心原则不变——**人类在关键节点把关**，但关键节点更集中、更聚焦。

### 合并 1：UI Design + Panorama Design → 一个「设计批」暂停点

**原因**：Feature UI 和全景增量同步是同一次设计讨论的两面（风格/配色/布局/语言对齐），分两次确认让用户反复打断。

- **重构 stages/ui-design-stage.md**：
  - 职责扩展为"Feature UI + 全景增量同步"一次性产出
  - 🔴 全景是产品真相，修改必须谨慎：默认增量合并（append / modify-in-place），禁止重写
  - 新增硬规则：
    - 对全景的任何修改必须在 sitemap.md 添加标红注释 `<!-- 🟡 {日期}: {FeatureID} 变更摘要 -->`
    - 执行报告必须列出全景 diff（sitemap 页面清单 + overview.html DOM 差异摘要）
    - 不允许删除现有页面或导航（属于 Feature Planning 范畴）
    - 结构性变更红线（删页面/重构导航/改核心业务流程状态机）→ DONE_WITH_CONCERNS，建议走 Planning
  - Output Contract 新增「全景同步状态」必填字段（同步了 / 显式跳过，二选一）
- **重构 stages/panorama-design-stage.md**：
  - 定位收窄为"Feature Planning 流程的全景重建模式"专用
  - Feature 流程不再触发本 Stage
  - 保留差异清单、风险提示、用户授权必达等硬规则
- **flow-transitions.md 更新**：Feature 流程的 UI 待确认 / 全景待确认 两行合并为「设计批 待确认」一行

### 合并 2：PM 验收 + commit + push → 一个合并暂停点（3 选 1）

**原因**：PM 验收通过 → 手动问用户是否 commit → 手动问是否 push，三步是连续决策，合并一个暂停点更顺。
**原则**：PMO 可以自动 commit（本地），**push 由用户决定**（保留用户控制远程推送的权力）。

- **roles/pmo.md 新增「PM 验收 + commit + push 合并暂停点」章节**：
  - PMO 在 PM 完成验收后自动执行本地 commit（含所有 Feature 产物 + 规范的 commit message）
  - 合并暂停点给用户 **3 选 1**：
    - 1️⃣ ✅ 通过 → 自动 commit + push（推到 origin/{branch}）
    - 2️⃣ ✅ 通过 → 仅本地 commit，不 push（用户稍后手动推送）
    - 3️⃣ ❌ 不通过 → 补充信息，回到对应阶段修复
  - push 失败不吞错：⏸️ 报告原因让用户手动处理
  - 3️⃣ 修复派发规则：按问题类型回退到 Review / Test / Plan / UI Design 对应 Stage；commit 保留不 revert；每轮修复 append 新 commit + 新 retry 记录
- **RULES.md §七 Git 提交规则升级**：
  - 从"用户要求时提交"改为"PM 验收通过后 PMO 自动 commit"
  - commit 产物清单扩充（含 state.json / review-log.jsonl / dispatch_log/ / retros/ 等审计产物）
  - commit message 模板标准化（含 AC 覆盖 / Review 通过情况 / 测试通过情况 / 耗时偏差摘要）
  - 🔴 push 硬规则：PMO 禁止自动 push；必须用户显式选择；禁止 push --force 到主分支
- **flow-transitions.md 更新**：Feature 流程的「PM 验收 → ✅ 已完成」改为「PM 验收 → 验收+commit+push 待处理 → ✅ 已完成」
- **完成报告模板新增「📦 Commit & Push 状态」段**：记录 commit hash / 分支 / push 状态
- **state.json schema 扩展（v7.3.4）**：
  - `_schema_version` 升级到 v7.3.4
  - `_instructions.stage_enum_v7_3_4`：Feature 流程合法 current_stage 枚举
  - `_instructions.commit_push_tracking`：stage_contracts.pm_acceptance 新增 commit_hash / push_status 字段

### 暂停点数量变化

```
改前（v7.3.3 / 典型 Feature）：6-8 个暂停点
  流程确认 + PRD + UI + 全景 + 方案 + Test 前置 + Browser E2E? + PM 验收 + push?

改后（v7.3.4 / 典型 Feature）：4-5 个暂停点
  流程确认 + PRD + 设计批(UI+全景) + 方案 + [Test 前置] + [Browser E2E?] + 验收+commit+push(3 选 1)
  （方括号是按 localconfig / TC 标注自动判断，多数情况不打扰用户）

典型简单 Feature（无 UI）：3 个暂停点
  流程确认 + PRD + 方案 + 验收+commit+push(3 选 1)

数量砍 30-50%，保留的是真正需要人类把关的契约核心。
```

### 未动的（保留 P1/P2 观察后再决定）

- 方案 A 的 #5（Blueprint 按复杂度决定暂停）— P2，风险相对高，等 P0 跑几个 Feature 验证
- 方案 A 的 #6（Test Stage 前置配置化）— P1，先观察用户对 A/B/C 三选一的实际选择分布
- 其他非压缩类改进（PMO 拆分、validator 等）— 前几轮讨论否掉了，不做

### 文件变更

- `skills/teamwork/stages/ui-design-stage.md`（重构：扩展为 UI + 全景增量）
- `skills/teamwork/stages/panorama-design-stage.md`（重构：仅保留全景重建模式）
- `skills/teamwork/rules/flow-transitions.md`（Feature 流程合并行）
- `skills/teamwork/RULES.md`（§四 Feature 流转逻辑 + §七 Git 提交规则升级）
- `skills/teamwork/FLOWS.md`（阶段链 + 流程步骤描述）
- `skills/teamwork/roles/pmo.md`（新增「PM 验收 + commit + push 合并暂停点」章节 + 完成报告加 Commit & Push 状态段）
- `skills/teamwork/templates/feature-state.json`（schema v7.3.4 + 新字段说明）

## v7.3.3 —— Stage 耗时度量闭环

背景：之前 dispatch.md 有预估（"预计 20-30 分钟"）但 Stage 结束没统计实际耗时。v7.3 改造完成后无法用数据验证效果，只能凭感觉判断"是快了还是慢了"。本次补齐耗时度量闭环，让每个 Feature 跑完自动有数据可复盘。

- **state.json schema 扩展**（templates/feature-state.json）：
  - `stage_contracts[stage]` 新增 `started_at` / `completed_at` / `duration_minutes`
  - `executor_history[]` 每条扩展为 `started_at / completed_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`
  - `planned_execution[stage]` 新增 `estimated_minutes` 字段（来自 AI Execution Plan）
- **review-log.jsonl schema 扩展**（templates/review-log.jsonl）：
  - 新增 6 字段：`started_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`
  - 示例更新为含耗时数据的完整行
  - 新增字段计算规则说明
- **AI Execution Plan 扩展为 4 行**（SKILL.md 「AI Plan 模式规范」）：
  - 新增第 4 行 `Estimated: {N} min`
  - AI 基于本 Feature 规模（AC 数、文件数）动态估算
  - 3 个典型示例全部更新
- **PMO 阶段摘要加耗时行**（roles/pmo.md）：
  - 每次 Stage 完成后的 PMO 摘要必须包含「⏱️ 实际耗时：N min（预估 M min，偏差 ±X%）」
  - 偏差 > +50% 自动加 ⚠️ 标识；偏差 < -30% 加 🟢 标识（预估过保守）
- **Feature 完成报告加耗时统计章节**（roles/pmo.md / RULES.md 8️⃣-D）：
  - 耗时统计表：每行一个 Stage + 合计（预估/实际/偏差/dispatches/retry/用户等待）
  - 耗时分析段：超预估 Stage 列表 + 客观原因 + 可操作优化建议
  - 区分 AI 实际耗时 vs 用户等待时间
- **各 stages/*.md 加 Expected duration baseline**：
  - plan-stage: 20-40 min（主对话）/ 15-20 min（Subagent）
  - blueprint-stage: 25-45 min（主对话）/ 30-60 min（Subagent）
  - blueprint-lite-stage: 8-15 min
  - ui-design-stage: Subagent 20-40 min / 主对话 8-15 min
  - panorama-design-stage: 增量 15-25 min / 重建 30-50 min
  - dev-stage: 主对话 ≤3 文件 15-25 min / Subagent 中等 30-60 min / 大改 60-120 min
  - review-stage: hybrid 10-20 min（三路并行墙钟）/ 全 subagent 15-25 min
  - test-stage: hybrid 15-30 min（环境 2-5 + 集成 5-15 + API E2E 10-25）
  - browser-e2e-stage: 每场景 2-3 min，总计 10-20 min
- **retros/*.md 模板加耗时度量段**（templates/retro.md）：
  - §1.1 耗时度量表（从 state.json.executor_history 聚合）
  - 跨 Feature 趋势分析：多个 retros 对比可发现规律（哪个 Stage 总是超预估）
- **RULES.md 8️⃣-D 新增**：Feature 完成报告必须输出耗时统计，不得跳过

核心收益：
- 每个 Feature 自动产出耗时数据，不再靠感觉判断
- 多个 Feature 跑完后可做横向对比（"Blueprint 总是超预估" → 设计有问题）
- Retro 从"主观经验记录"变成"数据驱动改进"
- v7.3 系列改造的净效果有数据可测（本轮加字段，下一个真 Feature 跑完即有数据）

Micro 流程不强制输出耗时（本身已是最短路径，加统计反成仪式）。

## v7.3.2 —— STATUS.md 废弃，state.json 成为 Feature 目录唯一状态文件

背景：v7.3 引入 state.json 做机读权威源，但保留 STATUS.md 作为"人读视图 + compact 恢复锚点"，导致字段重叠、双源头维护、恢复规则歧义。v7.3.2 彻底砍掉 STATUS.md，让 state.json 同时承担机读权威和人读详情（JSON 本身可读），ROADMAP.md 继续承担全局人读视图。

- **state.json 位置迁移**：从仓库根 `.teamwork/state/{feature_id}.json` 移到 `{Feature}/state.json`
  - 和 PRD/TC/TECH 等 Feature 产物同目录，单 Feature 查询无需跨目录
  - 跨 Feature 聚合依然可行（glob `docs/features/*/state.json`）
- **STATUS.md 废弃**：
  - `templates/status.md` 删除
  - `TEMPLATES.md` / `templates/README.md` 索引移除 status.md，新增 feature-state.json 和 verify-ac.py
  - 新 Feature 不再创建 STATUS.md，state.json 承担原职责
- **遗留 STATUS.md 处理**（向后兼容）：
  - 不删除已有文件（保留历史）
  - PMO 不再维护它
  - state.json 不存在但 STATUS.md 存在 → PMO 基于 STATUS.md 信息初始化 state.json 后忽略
- **规则更新**（所有对 STATUS.md 的引用全面替换）：
  - `SKILL.md` 红线 #1 / #14 / 热路径索引 / 文件索引
  - `RULES.md` §四流转链 / 功能完成 8️⃣ / 抽查规则 / 角色交接 / PMO 摘要更新
  - `rules/gate-checks.md` 原「STATUS.md 流转约束同步更新」段改写为「state.json 流转状态同步更新」
  - `rules/naming.md` Feature 目录标准结构 + BG 反向引用字段 + CHG 记录位置
  - `roles/pmo.md` state.json 维护规范全段重写（位置、流转前后、compact 恢复、遗留文件处理）
  - `roles/pm.md` 功能目录初始化描述
  - `stages/dev-stage.md` worktree 记录位置
  - `CONTEXT-RECOVERY.md` 恢复决策树 / Feature 看板 / compact 快速路径
  - `STATUS-LINE.md` compact 恢复快速路径 / 待确认恢复规则
  - `INIT.md` 扫描进度 / Feature 目录结构 / 红线 #1
  - `templates/feature-state.json` 位置字段 + 替代说明
  - `templates/roadmap.md` / `templates/teamwork-space.md` 引用更新
  - `codex-agents/hooks.json` 描述更新
- **验证**：
  - `grep -r "STATUS\.md"` 剩余都是 v7.3.2 明确标注的"遗留说明"或"废弃说明"
  - `grep -r "\.teamwork/state"` 零命中（位置已全迁移）
  - `templates/status.md` 文件已删除

简化效果：
- Feature 状态维护点从 4 处降到 3 处（state.json + review-log.jsonl + ROADMAP.md）
- 双权威冲突彻底消除
- Compact 恢复单一锚点（state.json），不再需要和 flow-transitions.md 交叉校验 STATUS.md

## v7.3.1 —— v7.3 收尾

前序 v7.3 改造完成后发现三个未对齐点，本次小版本收尾修复，不引入新机制。

- **agents/README.md §一 速查表与 AI Plan 模式对齐**（消除双权威冲突）：
  - 章节标题从「执行方式决策（PMO 必读）」改为「执行方式参考（默认推荐 + 判断原则）」
  - 删除"PMO 查下表决定 / 禁止凭感觉判断"的硬绑定语言
  - 表头从「执行方式」改为「默认 approach」，标识 🤖/主对话 改为 main-conversation/subagent/hybrid/AI 自主
  - 删除"🔴 禁止降级 Sonnet"等与"AI 自主"冲突的硬规则
  - 新增"AI Plan 偏离指引"章节，说明何时偏离默认 approach
- **Execution Plan 从 6 字段精简为 3 行核心**（去除重复仪式）：
  - Plan 只保留 Approach / Rationale / Role specs loaded 三项
  - Steps / Expected Output / Key Context 由各 Stage 契约、dispatch 文件、产物 frontmatter 承载（不重复）
  - SKILL.md 新增 3 个典型示例（Plan Stage / Dev Stage / Review Stage）
  - 每个 Feature × 8 Stage 的仪式文字量从 ~160 行降至 ~24 行
- **各 Stage 的 Plan 指引段落精简**（单一权威指向）：
  - plan/blueprint/blueprint-lite/ui-design/panorama/browser-e2e 的"AI Plan 模式指引"压缩到 2-3 行，指向 SKILL.md 和 agents/README.md §一
  - dev/review/test 保留本 Stage 特殊的 approach 判断逻辑（规模/复杂度/三视角独立性/环境独立性）
  - SKILL.md 中原"典型 approach 选择指引"表删除（和 agents/README.md §一 重复）
- **verify-ac.py 从示例脚本落地为可直接跑的标准实现**：
  - 新增 `templates/verify-ac.py`（Python 3 标准库实现，无 yq / 外部工具依赖）
  - 自带 YAML frontmatter 简化解析器，同时兼容 PyYAML（如已装）
  - 自测覆盖：文件缺失 / 覆盖通过 / 覆盖不完整 三种场景 exit code 分别为 1 / 0 / 3
  - 可直接从 `{SKILL_ROOT}/templates/verify-ac.py` 调用，项目无需复制
  - 删除旧 `templates/verify-ac.example.sh`（示例化处理太弱，实际没人落地）
  - prd.md / tc.md / blueprint-stage.md 所有引用更新

## v7.3
- **Stage 三契约化（规范契约，不规范过程）**：
  - 每个 Stage 文件重构为 Input Contract / Process Contract / Output Contract 三段式
  - 删除所有 Stage 对"必须 Subagent 执行"的硬绑定
  - 执行方式（主对话 / Subagent / 混合）由 AI 在 Plan 模式每次 Stage 开始时自主规划
  - 多视角独立性从"规则要求"转为"产物结构约束"：三份 review 产物独立 generated_at、独立 files_read、不互相引用（grep 校验）
  - 覆盖文件：stages/{plan, blueprint, blueprint-lite, dev, review, test, ui-design, panorama-design, browser-e2e}-stage.md 全部重写
- **AI Plan 模式规范**（SKILL.md 新增章节 + 红线 #14）：
  - AI 必须在每个 Stage 开始前输出 Execution Plan 块（含 Approach / Rationale / Steps / Expected Output / Loaded Role Specs & Standards / Key Context）
  - Plan 写入 state.json.planned_execution[stage]，审计可追溯
  - 硬规则：角色切换时必须 cite 对应 roles/*.md 的关键要点（防止凭记忆执行）
  - 实际执行偏离 Plan 时必须更新 Plan + 记录偏离理由
- **AC↔Test 结构化绑定（消除需求→代码漂移根源）**：
  - PRD.md 头部新增 YAML frontmatter：acceptance_criteria[]（id/description/priority/test_refs/ui_refs）
  - TC.md 头部新增 YAML frontmatter：tests[]（id/file/function/covers_ac/level/priority）
  - 新增 templates/verify-ac.example.sh 作为覆盖校验脚本示例
  - Output Contract 硬要求：每条 PRD AC 至少有 1 个 covers_ac 测试 + 所有测试通过
- **主对话产物协议（补齐 Subagent 协议反面）**：
  - agents/README.md §六 新增：主对话直接执行任务的产物落盘规范
  - YAML frontmatter 必填：executor/task/feature/started_at/completed_at/status/files_read/concerns
  - 覆盖场景：Plan Stage PRD 起草、Blueprint TC/TECH、Review 架构师视角、Test 环境启动、Browser E2E、UI 还原验收、PM 验收
  - templates/dispatch.md 顶部加适用范围声明：仅适用于 Subagent dispatch
  - review-log.jsonl schema 扩展：新增 executor / artifact_path / dispatch_file 字段
- **state.json 机读状态机**（模板 + PMO 维护规范）：
  - 新增 templates/feature-state.json 定义 Feature 级流转状态机
  - 位置：.teamwork/state/{feature_id}.json
  - 字段：current_stage / completed_stages / legal_next_stages / stage_contracts（input/process/output satisfied）/ planned_execution / blocking / executor_history / worktree
  - roles/pmo.md 新增「state.json 维护规范」：流转前读、流转后写，机器校验 target ∈ legal_next_stages
  - 与 STATUS.md 的关系：state.json 是机读权威源，STATUS.md 是人读视图，compact 恢复以 state.json 为准
- **流程确认必须展示步骤**（SKILL.md 红线 #15）：
  - PMO 初步分析中，选定流程类型后必须给出「本流程的完整步骤描述」（阶段链 + 每步做什么 + 暂停点）
  - 用户基于步骤描述确认流程类型
  - 不给步骤描述直接问「走什么流程」= 违规
- **Micro 流程放宽**（FLOWS.md §六 + SKILL.md 红线 #1）：
  - PMO 可直接改代码（白名单内零逻辑变更），不强制 Subagent，也**不要求 Execution Plan**
  - 真正轻量通道：只保留 PMO 分析 → 用户确认流程（含步骤描述）→ PMO 直接改 → 用户验收 的最小闭环
  - 改动限于 Micro 白名单（零逻辑变更：资源/文案/样式/配置常量/注释）
  - 事后审计：检查准入条件、逻辑变更混入、阶段链完整性
- **RULES.md §四流转链描述与实际实现对齐**：
  - 删除滞后的"Dev 含架构师 CR"、"Test 含 QA 审查"、"Codex 独立 Stage"描述
  - 更新为 v7.3 契约化后的准确流转链（Dev → Review 三路独立 → Test 环境独立 → Browser E2E → PM 验收）
- **status.md 显示名映射动态化**：
  - 显示名图标根据 state.json.planned_execution[stage].approach 动态渲染
  - 💬 = main-conversation / 🤖 = subagent / 💬🤖 = hybrid
  - 默认推荐列标注每个 Stage 的推荐 approach（但 AI 可按场景创新）
- 不做的改动（保留）：
  - 六种流程分类不变
  - dispatch 文件协议（v7.2）保留，Subagent 场景继续用
  - Key Context 6 类结构保留，在主对话任务中同样必需
  - Feature Planning / 工作区级 Planning / 问题排查流程规则不变

## v7.2
- Subagent Progress 可见性三段式协议（主对话 TodoWrite 预声明 + Progress Log 实时自述 + 事后回放）：
  - 背景：通用宿主 API 下 Subagent → 主对话无实时通道（同步阻塞模型），用户主对话黑盒等待体感差；plan 模式 / TodoWrite 在 Subagent 内不回流主对话
  - 三段式替代实时流：
    - 阶段 1（PMO 前置）：dispatch 前在主对话 TodoWrite 预声明 Subagent Step 列表（从 stage 文件「执行流程」抽取，粒度对齐 Expected deliverables）
    - 阶段 2（Subagent 中途）：执行中实时 append dispatch 文件的 Progress Log 段，记录 step-start / step-done / step-concern / step-blocked / degradation / subagent-done 等事件（硬规则：禁止最后一次性补全）
    - 阶段 3（PMO 事后）：读 Progress Log 转成主对话时间轴回放，step-start/done 映射为 TodoWrite 状态更新，异常事件高亮
  - templates/dispatch.md 新增 `## Progress Log` 必填段（含必填事件类型表 / 模板段 / 反模式）+ 设计原则第 8 条「Progress 可见性双保险」+ PMO 使用流程 Step 1/Step 3 新增 TodoWrite 预声明 + Progress Log 回显步骤
  - agents/README.md §二 2.5 新增「Progress Log 实时维护」硬规则 + §四 字段责任划分表新增 Progress Log 行（Subagent 填）+ §四 启动前自问新增「主对话 TodoWrite 预声明」检查 + §四 Subagent prompt 极简结构新增 Progress Log 要求（规则 3）+ §四 完成后处理新增「读 Progress Log 转主对话时间轴」步骤 + 新增「Progress 可见性协议」完整章节（三段式图示 + 用户体验目标对照 + 可选切分粒度策略）
  - 切分 Subagent 粒度作为可选加强（不默认）：满足"Stage >15 分钟 + 无强上下文依赖 + 用户明确敏感"三条件时启用
- API E2E 脚本化改造（从"逐条 curl"到"脚本驱动"）：
  - 核心变化：Subagent 不再一条条 curl，而是把 TC.md 场景翻译成 Python 脚本 → 执行 → 解读 JSON 输出 → 生成报告
  - 收益：Token 消耗从 N 场景 × 2 轮 LLM 降到 1 次生成 + 1 次解读；脚本可重跑（RD 修复后 `python api-e2e.py` 即可，无需再发 Subagent）；脚本可进 CI；脚本落盘为 Feature 交付物
  - 脚本位置：`{子项目}/tests/e2e/F{编号}-{功能名}/api-e2e.py`（+ README.md 记录 env 要求）
  - 脚本语言：Python 3.10+ + requests（禁止 bash+curl 组合——可移植性差）
  - 断言硬要求：每场景至少覆盖 4 类断言（status / body / DB / 副作用）中的 2 类；所有环境值走 env var；DB 校验必须走只读 DSN
  - 脚本标准化：函数名 `test_API_E2E_{N}_{描述}`，Runner 统一捕获异常输出 JSON，exit code 体现整体结果
  - e2e-registry 联动：P0/P1 级 case 必须注册，REGISTRY.md 新增「脚本路径」「最后跑通」两列
  - agents/api-e2e.md 整体重写：新增 §五脚本生成规范 + §六落盘注册流程 + §七新报告格式 + §九降级处理
  - agents/integration-test.md 顶部澄清：集成测试 = 调用既有测试命令（不生成脚本）；API E2E = 独立脚本（另一种职责），🚫 集成测试不做 curl 级黑盒
  - stages/test-stage.md §六红线新增「API E2E 脚本化交付」5 项硬要求 + Expected deliverables 明确脚本 + registry 更新
  - templates/e2e-registry.md 表结构增加「脚本路径」「最后跑通」列，api 类 case 必须填脚本路径（browser 类留 `-`）
- Key Context 结构化字段（dispatch 文件增强）：
  - 核心思想：PMO 是唯一贯穿全流程的角色，它手里有 Subagent 读不到的关键信息（历史决策、跨 Feature 约束、历史陷阱、降级授权、优先级权衡、本轮聚焦点），必须结构化注入 dispatch 文件，而不是让 Subagent 自己推断
  - 位置：dispatch 文件新增「🎯 Key Context」section，6 类子字段（历史决策锚点 / 本轮聚焦点 / 跨 Feature 约束 / 已识别风险 / 降级授权 / 优先级容忍度）
  - 🔴 硬规则：PMO 必须逐项判断，**无则写「-」**（证明已判断），严禁留空或删字段；无判断痕迹 → Subagent 返回 NEEDS_CONTEXT
  - 反模式防范：只写 Subagent 从 Input files 里读不到的信息，禁止复制 PRD/TECH 摘要
  - INDEX.md 增加「关键约束」列，摘录最关键一条，便于人工审查时识别本 Feature 累积的历史决策/风险
  - templates/dispatch.md 新增 Key Context 完整模板 + 设计原则第 7 条
  - agents/README.md §四 4.1 字段责任表新增 Key Context 行 + PMO 启动前自问清单新增逐项判断项 + Key Context 硬规则段（含正反例）
- Dispatch 文件协议（文件化 Subagent 交接）：
  - 核心思想：每次 Subagent dispatch 生成一个 markdown 文件，文件即入参即审计记录，消除「PMO 构造 prompt 字符串」和「PMO 写 dispatch 日志」的重复劳动
  - 位置：`{Feature}/dispatch_log/{NNN}-{subagent-id}.md` + `INDEX.md` 汇总视图
  - Subagent prompt 从 100+ 行简化为 ~5 行（只指向 dispatch 文件路径 + append Result 要求）
  - 🔴 硬规则：未生成 dispatch 文件不得 dispatch / Subagent 必须 append Result 否则视为 FAILED / PMO 必须更新 INDEX
  - 未 append Result / 超时卡死 → PMO 接管写 Result（含 degradation WARN），降级主对话执行
  - 降级 WARN 日志直接写入 dispatch 文件 Result 区域，审计链完整
  - 并行 dispatch 各用独立文件（Batch 字段标同批次），重新 dispatch 新文件 + Previous 字段追溯
  - 跨宿主天然兼容：Claude Task / Codex agent spawn / Gemini 主对话 / 主对话降级都只需"读这个文件"
  - 新增 `templates/dispatch.md`（含完整字段定义 + INDEX 模板 + PMO 使用流程 + 生命周期）
  - agents/README.md §四 4.1 用「Dispatch 文件协议」替代原「Prompt 结构」章节；§四 4.2 启动前检查新增「dispatch 文件已生成」前置条件；§四 4.3 完成后处理新增 Result append 校验 + INDEX 更新
  - rules/naming.md 新增 dispatch 文件编号规则 + Feature 目录标准结构（含 dispatch_log/）
  - INIT.md 创建基础目录段新增 Feature 子目录说明
- 降级兜底 WARN 日志强制规范：
  - standards/backend.md §四 日志规范新增「降级兜底逻辑 WARN 日志规则」硬规则（含必须字段：降级原因 + 原路径 + 兜底路径 + 业务上下文，含反例示例，Code Review 缺失即阻塞）
  - standards/common.md CR 规范遵守检查新增降级 WARN 必检项
  - agents/README.md §四 dispatch 新增「降级兜底必须输出 WARN 日志」统一规范，覆盖 Subagent dispatch 失败、Codex CLI 不可用降级 Sonnet、宿主不支持 TodoWrite、worktree 不可用、hook 缺失等所有宿主兼容兜底路径
  - agents/README.md §五 BLOCKED/FAILED 升级策略标注 WARN 日志要求，静默降级明确定性为违反闭环验证红线
- 效率优化（减少流程税）：
  - Stage 内部子步骤简化 PMO relay：跨 Stage 保留完整校验，Stage 内部改用轻量标记（📌 Blueprint 1/4）
  - Subagent 输入改文件路径优先：减少 PMO 摘要转述的信息衰减，Subagent 自行读原文
  - Blueprint Stage 改为 Subagent 执行：4 步内部闭环，主对话 context 不被占用
  - 敏捷需求新增 BlueprintLite Stage（轻量蓝图：QA 简化 TC + RD 实现计划，无评审），替代原 3 步独立执行，Dev Stage 保持单一职责
- 叙事重构：从"虚拟团队"改为"角色视角 + 流程规范"定位
  - SKILL.md description: "AI Agent Team" → "AI-driven structured development process with role-based perspectives"
  - README 中英文同步更新：强调角色视角切换和质量门禁，而非团队协作
  - INIT.md 写入模板：从"多角色协作流程"改为"结构化开发流程"
- 跨宿主兼容（Claude Code / Codex CLI / Gemini CLI）：
  - 硬编码路径 `.claude/skills/teamwork/` → `{SKILL_ROOT}` 变量（~20 处）
  - INIT.md 宿主环境检测 + 指令文件自适应写入（CLAUDE.md / AGENTS.md / GEMINI.md）
  - agents/README.md §四 dispatch 抽象层（Task 工具 / Codex agent spawn / 主对话降级）
  - codex-agents/ 目录：6 个 Codex 自定义 agent toml 定义
  - TodoWrite 降级：宿主不支持时回退 markdown 进度块
  - hooks 双宿主：Codex 版去掉 PreCompact/PostCompact
  - install.sh 安装脚本：自动检测宿主 + 一键部署
  - SKILL.md 新增「宿主环境适配」章节

## v7.1
- 问题 10 清理：STATUS-LINE.md 阶段对照表 / templates/status.md 显示名映射 / agents/README.md 速查表 / gate-checks.md 示例 / 全局旧阶段名引用清理
- 问题 11 Worktree 集成：.teamwork_localconfig.md 新增 worktree 策略字段（off/auto/manual），INIT.md 启动检测，Dev Stage worktree 创建/清理生命周期，flow-transitions.md 标注 worktree 触发点

## v7
- 8 Stage 架构重构：
  - stages/ 目录（8 个 stage）：Plan / UI Design / Panorama Design / Blueprint / Dev / Review / Test / Browser E2E
  - agents/ 只保留任务单元规范（被 stage 引用，不被 PMO 直接 dispatch）
  - roles/ 保留 6 个角色定义
  - rules/ 保留转移表 + 门禁 + 编号
- Dev → Review → Test 三段式：Dev 纯开发+单测，Review 三路并行（架构师CR∥Codex∥QA审查），Test 并行（集成∥E2E）
- Plan Stage：PM 写 PRD + PL-PM 讨论 + 技术评审合并为一个 stage
- Blueprint Stage：QA 写 TC + TC 评审 + RD 技术方案 + 架构师评审合并为一个 stage
- Chain → Stage 全局重命名
- Codex Review 合入 Review Stage（不再独立 dispatch）
- Panorama Design Stage 从 UI Design Stage 拆出独立

## v6
- roles/ 与 agents/ 分离：ROLES.md（1,635 行）拆为 roles/ 目录（7 个角色文件）+ 索引（~25 行）
  - agents/ 只保留真正的 Subagent spec（6 个 + 子规范）
  - 主对话评审规范（prd-review / tc-review / arch-tech-review）合并到对应 roles/ 文件
  - 角色定义按需加载，PMO 不再需要读 1,635 行的 ROLES.md

## v5
- 新增第五种流程「敏捷需求」：轻量级流程适用于小改动
- 新增第六种流程「Micro」：零逻辑变更的最轻量通道（资源替换/文案/样式/配置常量），防止 PMO 因"改动太小"而越界写代码
- PMO 反模式补充：小改动决策树 + "自己做更快"反模式 + commit/push 必须用户验收
- PMO 预检分层体系（L1 基础/L2 测试环境/L3 E2E）：所有 Subagent dispatch 前必须完成对应级别预检（红线 #13）
- PMO 恢复/待命场景强制给出优先级建议：Feature 看板必须附 💡 建议 + 📝 理由，禁止只列状态让用户自行判断
- Pre-flight Check 合并到强制流转校验块：新增「📖 流转类型」必填字段（🚀自动/⏸️暂停/🔀条件），查表结果嵌入校验输出，消除两步分离导致跳过预检的问题
- 4 个轻量 Subagent 回归主对话执行：PRD 技术评审、TC 技术评审、架构师方案评审、QA Lead 质量总结改为 PMO 切换角色在主对话执行，减少冷启动开销提升速度（spec 文件保留作为角色规范）
- 新增 agents/README.md §一「执行方式速查表」：PMO 判断 Subagent vs 主对话的集中决策指引（含判断原则 + 全阶段速查表），热路径索引已添加入口
- P0 单一权威源重构：RULES.md 从 2,004 行精简到 ~1,645 行（-18%）
  - 转移表副本（99 行）→ 删除，权威源：rules/flow-transitions.md
  - 门禁校验格式（91 行）→ 删除，权威源：rules/gate-checks.md（同步更新为最新版含流转类型字段）
  - Bug 处理流程（177 行）→ 迁移到 FLOWS.md，RULES.md 改为引用
  - 暂停条件 4 个子章节合并为 1 个「暂停输出规范」（-99 行）
  - UI 变更规则 6 次重复压缩为 1 条（-55 行）
  - 编号规则（82 行）→ 迁移到 rules/naming.md
  - 最终结果：RULES.md 2,004 → 1,418 行（-29.2%）
  - PMO 热路径索引更新为指向拆分后的权威文件
- 阶段名消歧义重命名：PRD 评审→PRD 技术评审 / TC 评审→TC 技术评审 / 架构师 Review→架构师方案评审（88 处 / 22 文件），消除"执行步骤"与"用户确认"的命名混淆
- 状态行功能编号必填：Feature/敏捷/Bug/Micro 流程的功能/Bug 编号从可选改为必填
- 流转校验精简为 1 行：`📋 {A} → {B}（📖 {类型}，查 flow-transitions.md ✅）`，降低 PMO 跳过校验的成本
- QA Lead 质量总结环节移除：Verify Stage / Browser E2E 通过后直接进入 PM 验收，简化流程。角色从 8 个降为 7 个。敏捷需求砍掉环节从 7 个降为 6 个
- Designer 两步设计：Feature 流程中 Designer 拆为 Step 1（当前 Feature UI）+ Step 2（全景同步），各自独立确认
- Codex CLI 通用执行引擎移除，Codex CLI 仅用于独立 Codex Code Review 阶段（不可用时可降级 Sonnet 或跳过）
- TEMPLATES.md 拆分为 templates/ 目录（16 个独立模板文件）
- RULES.md 热路径拆分为 rules/ 目录
- INIT.md CLAUDE.md 注入段精简（红线改为索引引用）
- 前端开发规范大幅扩充
- Hooks 脚本健壮性改进（换行符 bug 修复、降级逻辑、超时调整）
- 规则去重：建立单一权威定义 + 引用模式
- 明确协作模型（单人 vs 多人）

## v4
- 中台子项目支持（business / midplatform）
- PL-PM Teams 讨论机制
- E2E 回归测试中心
- QA Lead 质量总结阶段
- 自下而上影响升级评估

## v3
- 业务架构与技术架构对齐方案落地
- Product Lead 三种工作模式
- CHG 变更记录机制
- Workspace Planning 流程

## v2
- 多子项目模式
- Hooks 自动化（SessionStart / PreCompact / Stop）
- 按需加载文件机制

## v1
- 基础 8 角色协作框架
- Feature / Bug / 问题排查 / Feature Planning 四种流程
