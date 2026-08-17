# UI Design Stage

> 🧭 **四段结构**(详 [STAGES.md §3](../STAGES.md)):目标 + 硬规则白名单 + 手段菜单 + 产物契约 · 手段 AI 自选。

---

## 🟢 全景为唯一权威(推荐新模式)

> 老模式(Feature 内存 `preview/*.html` 副本)与全景权威版本**必然脱节**(static-html 介质 dirty state · 4 轮调像素仍有差异)。
> 新模式:**全景 `panorama_path/preview/<page>.html` 是唯一权威 · Feature 不存副本** · UI.md 改为「全景改动声明 + 局部决策记录」。

### frontmatter(schema 单源 = `{SKILL_ROOT}/templates/ui.md`)

🔴 有 `pages_changed[]` → 进入新模式(全景是唯一权威 · Feature 不存 preview/ 副本)。字段清单与语义照模板,不在此复述。


### 向后兼容(老 Feature)

- UI.md 无 `pages_changed[]` 字段 → fallback 老模式(`panorama_medium=static-html` 要求 Feature 内 `preview/*.html` ≥ 1)
- 老 Feature 不强迁 · 新 Feature 推荐新模式

---

## ① 目标(telos)

**让用户在写代码之前就看见并拍板「它长什么样、怎么用」**:产出**可跑可点的全景增量**(不是概念图),意图四要素(布局结构 / 交互流 / 状态 / 字段映射)落进 UI.md 作为 dev 还原与 pm_acceptance 的对照物。拦的风险:概念页与真实页对不上(用户验收才发现)、设计=代码承诺退化成人肉对齐、跨 Feature IA 被单个 Feature 悄悄改。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **介质二选一且必显式声明**(`UI.md` frontmatter `panorama_medium`):项目 `PROJECT.md` 声明了前端栈 → **必须 `same-stack`**,用 `static-html` 即违规;「前端栈已定 + 仍 static-html」= dirty state,必开 Feature 迁移(why:介质差异不可调和 —— 实测 4 轮调像素仍有差,拿静态稿当 live 参考会一路错到验收)。
2. 🔴 **same-stack 物化闸**:`{panorama_path}/preview-project/` + `preview.sh` + `package.json` **必存在**(`_check_same_stack_preview_project` 校验)· **不可只写 UI.md markdown 跳过可跑预览**(why:防拿「验证器只校验 UI.md」当借口零可视产出 —— 最低物化闸 ≠ 免做交付物许可)。
3. 🔴 **IA 镜像律**:preview-project 路由结构 = 真实 app(与 `sitemap.md` 一致)· 本次设计页挂**真实 `route_path`** · `/` = 真实首页设计稿 · **router 必含**(why:全景的价值就在用户能沿真实导航走到新页;把新页渲染在 `/` 顶掉首页 = IA 违规)。
4. 🔴 **复现门(扩已有真实页时)**:设计单位是**整张页** —— 读真实代码定形态 → 按真实形态复现整页 → 再集成新部分 · **绝不凭印象重画**(why:实证 AON Offer-Analysis —— 只画概念页、真实页的筛选区/KPI/Top card 没对齐 → 用户判「设计稿不完整」要求重做)。
5. **sitemap / overview 随设计一并改**(设计 = 基于现有全景的改造 —— 新页节点 / 描述列在本 stage modify-in-place · 与附录维度 4 同轴):跨 Feature IA 影响由规则 8 的**出口判级**承接审计与暂停(why:改动与登记分两个 stage = 二次 touch 纯重复 · 实证 mtime 门逼人补碰文件)。
6. 🔴 **截图只落 scratch 目录**(worktree 模式 `<worktree>/.teamwork-scratch/screenshots/`〔ignored · 不进 diff〕· off 模式旧根)· **绝不散落 worktree 其他位置 / 主工作区根**(why:自检一次性产物非交付物 · 详 [conventions §12.5](../docs/conventions.md))。
7. ⏸️ **用户预览确认(R5 暂停点)** · `auto_mode=true` 时跳过(设计意图已落 UI.md/preview · auto 用户接受)(why:「看着对不对」是 taste 层 · 用户主权 · AI 判不了)。
8. 🔗 **全景变更判级(出口 · 原 panorama_sync stage 并入 · 用户拍板退役)**:改动涉全景 → 判级 —— **L1**(节点内增量 · 三判据**全**满足:① sitemap 无节点增删移 / 无路由变化 ② 无设计 token / 共享视觉基线变更 ③ 受影响 Features 扫描零命中)→ `add-concern --severity WARN` 记三判据依据 · 直进 blueprint;**L2**(任一不满足或拿不准)→ 判级结论 + 受影响 Features **并入本 stage 既有的用户确认设计稿暂停点**一并拍板(零新增停等 · auto_mode 跳过时 WARN 留痕);判级依据写 **UI.md §全景变更判级**(替代原 panorama-change-summary.md)(why:设计本就是改全景 —— 同步不需要第二个 stage,需要的只是结构性变更的判级与协调,条件暂停搭既有停等即可)。

---

## ③ 建议手段菜单(AI 自选 · 不强制)

| 手段 | 何时值得 |
|---|---|
| **same-stack:扩/搭 preview-project** | 规划期已 seed → 增量补本 Feature 页;不存在 → 首次搭。基建层走共享包/同版 · mock data · 页面层承载意图四要素 · 源即全景权威(committed · 不出静态 build)· 本 Feature 引入新库时 preview-project 独立装(解鸡蛋问题) |
| **static-html:直接编辑全景 HTML** | 前端栈未定 / Designer-only —— 改 `panorama_path/preview/<page.id>.html`(唯一 source · Feature 内不存副本)· `pages_changed[].panorama_file` 链到权威路径 |
| **复现手段排序**(扩已有页)| 优先导入真实页/组件源(同一份代码 · 一致性由结构保证);不可导入 → 按真实源 1:1 镜像 + UI.md 记豁免 |
| **全景变更判级**(规则 8) | 改动涉全景时出口必判 —— L1 三判据留痕直进 · L2 随用户确认一并拍板(不必预判影响大小 · 判级三判据是机械问句) |

## 📐 全景模型(介质 / IA 镜像律 / 分层同构律 —— ②③④ 共同引用的领域定义)

teamwork 支持两种 panorama 介质 · 项目应在 ui_design 启动前明确,写入 `UI.md` frontmatter `panorama_medium`:

| medium | 适用 | 实现 |
|---|---|---|
| `same-stack`(**推荐**) | 项目前端栈已定 | **独立 preview-project**:`{子项目}/docs/design/preview-project/`(同技术栈的独立前端项目 · 自带目标库 · 含 mock data)· **源即全景权威** · 预览靠跑 `preview.sh` 起 dev server(动态端口 · 不在 teamwork 层起 server) |
| `static-html`(兜底 · 仅作 IA/视觉层级/Token 参考 · 介质差异不可能像素级仿 live) | 前端栈未定 / Designer-only / Greenfield POC | 手写 `{panorama_path}/preview/*.html`(CDN) |

> 🔴 **same-stack 模型**:旧 same-stack = 在**真实前端 app** 加 `/design/*` 路由 —— 污染真实工程 + 引入新库时鸡蛋问题。新 same-stack = **`{子项目}/docs/design/` 独立 preview-project · 源即全景权威 · 跑 preview.sh 实时预览**:
> ```
> {子项目}/docs/design/
>   ├─ UI.md              设计规范(token + 组件映射 + 页面 + AC 覆盖)· 也可在 feature_dir
>   └─ preview-project/   🔴 独立前端项目(同技术栈 · 自带目标库 · src 渲染各页 + mock)= 全景权威(committed)
>        ├─ preview.sh    🔴 预览入口(装依赖 + 动态空闲端口 + 起 dev server + 打印 PREVIEW_URL)· 见 templates/preview-project-preview.sh
>        ├─ package.json  可跑项目证据
>        └─ node_modules/ gitignore
> ```
> `panorama_path = {子项目}/docs/design`。
> 🔴 **IA 镜像律**:preview-project 的**路由结构 = 真实 app**(与 `sitemap.md` 一致)—— 本次设计页挂**真实目标 path**(`pages_changed[].route_path` · 如 `/settings/ingest`)· **`/` = 真实首页设计稿**(已有则复用 · 全景首版即建)· **router 必含**(「单页预览不需要路由 · 有意省略」= 漂移反模式 —— 全景的价值就在用户能沿真实导航走到新页)。
> 🔴 **分层同构律**(替代 「数据层唯一差异律」· 同构承诺按「能否由结构保证」分层):
> - **Layer 1 基建层(业务无关 · 完全一致)**:页面框架(shell/layout)· 前端架构(构建链/路由机制/栈版本)· UI 组件库 · 主题 tokens。优先共享包(preview-project 与真实 app 依赖同一份代码 · 一致性由结构保证);不可抽包 → 版本锁定镜像 + UI.md 记豁免与回收计划。
> - **Layer 2 业务页面层**:全景页承载**意图四要素** —— 布局结构 / 交互流 / 状态(normal·empty·loading·error)/ 字段映射(UI.md 既有段落即契约载体)。🔴 **一致性按介质定**:
>   - **same-stack → 完全一致**:页面内容从**同一份共享组件 / 真实页面源**渲染 · **零预览痕迹** · 设计=代码是「**构造保证**」非人肉对齐 · **不留「像素自由」口子**。🔴 机制详 § preview dev 工具面板(真实交互页面内做 · 面板只放页面到不了的态)。
>   - **static-html → 仅参考**:介质差异客观不可像素仿 · 四要素对齐即可(dev 还原与 pm_acceptance 的对照物)。
> - **权威时效(防权威倒置)**:页面层全景的设计权威**至该页 ship 为止** —— ship 后代码即唯一真相 · 全景页转历史参考 + 下一轮设计底版。🔴 反模式:拿停更的全景页「纠正」已演化的真实页面。
> - **下游编译契约**:共享基建有两个消费者(真实 app + 全景)· 任何 feature 改共享基建 → **dev 结束须保证全景编译通过**(详 [dev-stage.md ②硬规则 5(共享基建→全景编译契约)](./dev-stage.md))。
> 🟢 **same-stack 去静态 build 产物**(用户拍板):**去掉静态 build 产物**(`docs/design/preview/*.html` 不再必产)· 全景权威 = preview-project **源**(committed · 要看跑 preview.sh)· 预览 = dev server 实时(动态端口 · 不在 teamwork 层起 server)。`pages_changed[].panorama_file` 对 same-stack 可选(指向 preview-project 内渲染该页的源/路由 · 非文件存在性校验)。
> 老 Feature(in-app /design 路由 / 静态 preview)向后兼容不强迁 · 新 Feature 用本模型。

🔴 介质声明 / same-stack 物化闸 / dirty state 三条硬规则见 **② 硬规则 1-2**(单源 · 此处不复写);补充一条向后兼容:`UI.md` frontmatter 缺 `panorama_medium` → verify-panorama / UI_DESIGN_SPEC 视作 `static-html`(老 Feature 兼容 · 新建必显式声明)。

---


## 预览(same-stack · preview.sh 即唯一预览)

> 🔴 same-stack 预览是 ES-module bundle · `file://` 因 CORS 打不开 → **必须 dev server**。**不在 teamwork 层起 server**(用户拍板)· 改用 preview-project 自己的 dev server · **每次选一个动态空闲端口** → 并行 worktree / 多终端 **天然不冲突**。

```bash
# preview-project 内含 preview.sh(从 templates/preview-project-preview.sh 拷入 · chmod +x)
# PMO 后台跑 · 抓早期 stdout 的 PREVIEW_URL= 行给用户 browse:
bash {子项目}/docs/design/preview-project/preview.sh    # → PREVIEW_URL=http://localhost:<动态端口>/
```

🔴 **预览地址约定(IA 镜像)**:preview.sh 打印的是**根 URL**;PMO 给用户 / browse 的预览地址 = `PREVIEW_URL` + **本次设计页 `route_path`**(直达 · 取自 UI.md `pages_changed[].route_path`)· 并注明 `/` = 真实首页设计稿;多页改动 → 每页一条直达 URL 清单。🔴 把新设计页渲染在 `/`(顶掉首页)= IA 镜像违规。

🔴 **注意**:dev server 前台阻塞 → PMO 用 `run_in_background` 跑 · 读 `PREVIEW_URL=` 行 · 等就绪(~2s)再 browse · 用完 kill 进程。

---

## preview dev 工具面板(🔴 右下角悬浮 · 只放页面到不了的态)

> 约束只有两条:
> - 🔴 **真实 app 里点得到的交互 → 页面内做成真实可点**(新建/编辑 Drawer · Modal · 行→详情 · 页内导航/Tab)—— 这是 same-stack「交互保真」的核心;
> - 🔴 **工具面板只放页面入口覆盖不到的**:状态区(Loading / Error / Empty / 边缘态 · 真实交互无法自然触发的)+ 页面区(Prototype Nav 兜底无页内入口的页)。禁的是**预览专属控件**(真实 app 没有的 state-switcher 下拉/场景 toggle 嵌进页面)· **不禁真实交互按钮**。
> 悬浮 overlay 不占布局流 → 不违 IA 镜像(`/` 仍是真实首页)· 可折叠。

---

## 交互 & 视觉质量判据(设计/还原/评审同一基准)

> 细则(hover 环 / 骨架屏 / 对比度数值 / 触控尺寸…)不入库 —— 模型内建常识,「模型对交互体验缺天生判断力」的旧前提已随模型能力失效。留**判据**不留细则:

- **完备四态必设计**:normal / empty(消息 + 主操作)/ loading / error(具体原因 + 下一步)· 首次 vs 回访(如适用)
- **可恢复**:破坏性操作有确认 · 误操作能撤销退回(接 PL 质疑六问⑥ 既有行为变更)
- **边界退化想过**:超长文本 / 慢网超时 / 快速重复点击 / 并发 / 超大列表 —— 交互怎么不崩
- 🔴 **一致 > 独特**:匹配现有组件与模式、**不重新发明** —— 策略对照 **UI-RULES**(控件偏好/色板策略)· 视觉值对照 preview-project tokens(独特品牌设计仅全景首版/greenfield)
- **文案从用户视角**:「通知」非「webhook 配置」· 同一动作全流程同名 · error/empty 当指引不当情绪

> 🧠 **写法非环节**:**画预览稿时就按这些判据画**,不是写完再逐项过。dev 还原(dev-stage ②硬规则 4)与 reviewer 审同用这份基准(防凭空 generic 评)。

---

## ④ Output Contract

- **`UI.md`**:**schema 与章节以模板为单源** `{SKILL_ROOT}/templates/ui.md`(实证:原契约曾点名模板里不存在的四个段,且模板明令「视觉描述一律归 HTML 预览产物 · 不在本文复述」—— Designer 照哪边写都违反另一边;**指针 + 复制被指向内容 = 副本必漂**)。UI.md 只承载**意图 / 追溯 / 审计**:§全景权威索引 · §UI-AC-COVERAGE · §Designer 自查报告 · §变更记录。
- **panorama 产物**:`same-stack` → preview-project 源(+ `preview.sh` 从 `{SKILL_ROOT}/templates/preview-project-preview.sh` 拷入 · `chmod +x` · 按框架改 dev server 一行)· `static-html` → `preview/*.html`

📎 **物化拦截**(按 `panorama_medium` 适配):
- **`static-html`**:preview HTML 文件名 = `<page.id>.html`(`pages[].id` 对应 .html 存在 · 错位 → complete FAIL);`verify-panorama.py` 走完整校验(self-check + host marker + preview count + panorama_path)
- **`same-stack`**:preview-project + preview.sh + package.json 三者存在(`_check_same_stack_preview_project`)· 全景权威 = **源**(不再要静态 build 产物)· 🔴 不再「不要求产物 · return True」(防 cut-corner)
- `stage_contracts.ui_design.output_satisfied=true` → dev-start 自动触发 UI 还原校验(dev-stage ②硬规则 4)

⏸️ **暂停点选项**(R5 标准格式见 [SKILL.md § R5(b)](../SKILL.md)):
1. **确认 UI · 进入 blueprint** 💡 推荐 — `ui_design-complete` → 自动转 blueprint
2. **要改设计** — 按用户反馈改 UI.md + preview
3. **其他指示**

📚 决策参考:`static-html` → 直接 browse `preview/<page>.html`;`same-stack` → 后台跑 preview.sh,把 `PREVIEW_URL` + 本次设计页 `route_path` 的**直达 URL** 给用户(根 `/` = 首页设计稿 · 多页给直达清单)。

```
state.py ui_design-complete --feature X --auto-commit Y \
  --artifacts <UI.md[,preview/]>
# --artifacts:UI.md 必 · static-html 加 preview/ · same-stack 仅 UI.md
```

**sitemap 改动**:必显式列影响范围 · 与相关 Feature owner 协调(防破坏现有路由)。

---

## 附录 · Designer 自查规范(6 维 · 迁自 standards · verify-panorama.py 校验对照)

> Designer 完成 UI 设计后、用户确认设计稿前，必须完成自查并输出自查报告写入 UI.md。
>
> 物化拦截：[tools/verify-panorama.py](../tools/verify-panorama.py) 校验自查报告完整性 + sitemap.md mtime + preview/ 数量 · UI Design Stage 出口前置。

**时机**:Designer 完成设计 → 按下方 6 维度自查 → 报告写入 UI.md 末尾 → `verify-panorama.py` 物化校验全 ✅ 才进 ⏸️ 用户确认设计稿。

### 自查清单详解（6 维度）

#### 1. 全景对齐

```
📋 全景对齐检查项：
├── panorama_path 已 read（cite Stage 入口实例化 Step 0 探测结果）
├── Feature UI 风格 / 配色 / 布局 / 语言与全景一致（read panorama_path/sitemap.md + overview.html 对照）
├── Feature 页面在全景中的位置已确认（新增节点 / 修改既有节点 / 影响哪条导航）
└── 跨子项目场景（panorama_path 不在当前 Feature 子项目）
 ├── UI.md 顶部已标注「全景宿主：{hosting_subproject}」
 └── 已显式说明「为什么走跨子项目全景」（防 Designer 凭印象）
```

🔴 项目无全景路径（Step 0 决策为 panorama_path=null）→ 标注「⚠️ 项目无全景基准 · 本 Feature UI 设计为独立基准」+ Concerns 记录。

#### 2. 状态覆盖

```
📋 状态覆盖检查项：
├── 每页面有正常态 HTML preview
├── 每页面有空态 HTML preview
├── 每页面有加载态 HTML preview
└── 每页面有错误态 HTML preview
```

🔴 缺态即阻塞 · ❌ 反模式：用文字描述代替 HTML preview。

#### 3. PRD AC 覆盖

```
📋 AC 覆盖检查项：
├── 每条 PRD AC 在 UI.md 找到对应页面 / 组件支撑
├── 输出 UI-AC-COVERAGE 表（AC.id → 页面/组件 → 覆盖状态）
└── 非 UI 类 AC（纯后端 / 纯逻辑）显式标注「⚠️ 需 RD 实现 · 非 UI」
```

#### 4. 全景增量同步（涉及变更时）

```
📋 全景增量同步检查项：
├── 判断本 Feature 是否引入新页面 / 修改现有页面结构 / 变更导航关系？
│ ├── 是 → 执行增量合并（下方 4 项）
│ └── 否 → 显式输出「⏭️ 本 Feature 无页面结构变更 · 全景无需同步」 + 跳过下方
├── design/sitemap.md 已 modify-in-place（不重写 / 不删除 / append 新页面）
├── design/preview/overview.html 已 modify-in-place
├── sitemap.md 对应段加标红注释 `<!-- 🟡 {日期}: {FeatureID} 本次变更：{变更摘要} -->`
└── 自查报告含全景结构 diff（前后页面清单 / overview.html DOM 差异摘要）
```

#### 5. 结构性变更红线（兜底拦截）

```
📋 结构性变更检查项：
├── 本 Feature 不涉及「删除现有页面」
├── 本 Feature 不涉及「重构导航结构」
└── 本 Feature 不涉及「修改核心业务流程状态机」
```

🔴 任一命中 → **停止本 Stage** → 返回 DONE_WITH_CONCERNS · 建议用户走 Feature Planning 而非 Feature 流程。

#### 6. 框架基线唯一性

- `framework_source` = panorama `preview/overview.html`(cite 路径)—— 框架 / 配色 / layout / region 的**唯一格式基线**。
- ❌ 反模式:拿**历史 Feature 的 `preview/*.html`** 当框架基线(peer Feature 只可作内容参考 · 详 [tech-rules 规则 18(权威源单源)](../standards/tech-rules.md) · 实证 PTR-F032)。

### Designer 自查报告模板

🔴 **模板单源 = [templates/ui.md § Designer 自查报告](../templates/ui.md)**(UI.md 全部章节的 schema 单源 · 含 6 维汇总表 + 全景对齐证据 + 增量 diff + 结论)· 本文件不再复制一份 —— 此前两处各存一份,维度数已漂移(这边 5 维 · 那边 6 维),**双副本必漂**。verify-panorama.py 校验的是 UI.md 实例(段存在 + 占位符已填 + 结论为通过)。

### 自查结果处理

全 ✅ → ⏸️ 用户确认设计稿;有 ⚠️ 低风险(如 1 个 AC 未覆盖且已补)→ 修复后重新自查;🔴 结构性红线命中 → 停 Stage → DONE_WITH_CONCERNS;verify-panorama.py FAIL → 按 stderr hint 补完报告重跑。

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `UI_DESIGN_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
