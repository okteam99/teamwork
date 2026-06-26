# UI Design Stage

---

## 🟢 全景为唯一权威(推荐新模式)

> 老模式(Feature 内存 `preview/*.html` 副本)与全景权威版本**必然脱节**(static-html 介质 dirty state · 4 轮调像素仍有差异)。
> 新模式:**全景 `panorama_path/preview/<page>.html` 是唯一权威 · Feature 不存副本** · UI.md 改为「全景改动声明 + 局部决策记录」。

### frontmatter 新字段(替代 Feature 内 preview/ 副本)

```yaml
---
pages:
  - {id: offers, title: "Offers"}
panorama_medium: static-html               # 介质类型(不变)
panorama_path: apps/partner/docs/design    # 全景权威根
pages_changed:                              # 有此字段 → 进入新模式
  - page_id: offers                         # 必 · 对应 pages[].id
    route_path: /offers                     # same-stack 必 · 真实 app 目标路由(预览直达 URL 用 · 与 sitemap 一致)
    panorama_file: apps/partner/docs/design/preview/offers.html  # static-html 必 / same-stack 可选(渲染该页的源/路由)
    change_range: "Tabs 与 Table 之间新增 filter 区"               # 可选 · 本 Feature 改动描述
    acceptance_criteria_refs: [AC-1, AC-3] # 可选 · 关联 PRD AC
---
```

### Feature 执行流程

1. ui_design 阶段:Designer 直接编辑 `panorama_path/preview/<page>.html`(全景权威 · worktree 内改 · merge 后同步全景)
2. UI.md 写 `pages_changed[]` 声明本 Feature 改了哪几个 page + 改动范围
3. ui_design-complete:`_evidence_panorama_artifact` 校验每个 `panorama_file` 真实存在
4. panorama_sync stage(条件触发):architect 评审跨 Feature 影响 + 起草 panorama-change-summary.md + 更新 sitemap.md

### 与老模式的对比

| 维度 | 老模式 | 新模式 |
|---|---|---|
| Feature 内 preview/*.html | 必(static-html 介质) | **不存** |
| 全景 preview/*.html | 副本(panorama_sync 同步) | 唯一权威(ui_design 直接改) |
| 双副本不一致风险 | ⚠️ 必然 | ✅ 不存在 |
| Feature 局部决策痕迹 | UI.md + preview/ | UI.md(pages_changed[] 声明) |
| 评审视角分层 | ui_design 局部 + panorama_sync 全局(各评 1 次) | 不变(双 stage 保留) |
| 工作量(改一个 page) | 改 Feature 副本 + panorama_sync 时同步全景(2 处) | 直接改全景(1 处) |
| 跨 Feature 并行 | Feature 间无 merge 冲突(各自副本) | 多 Feature 改同一 panorama 文件可能 merge(项目 SOP 错峰) |

### 向后兼容(老 Feature)

- UI.md 无 `pages_changed[]` 字段 → fallback 老模式(`panorama_medium=static-html` 要求 Feature 内 `preview/*.html` ≥ 1)
- 老 Feature 不强迁 · 新 Feature 推荐新模式

---

## Panorama 介质类型(🔴 ui_design 启动前必决)

teamwork 支持两种 panorama 介质 · 项目应在 ui_design 启动前明确,写入 `UI.md` frontmatter `panorama_medium`:

| medium | 适用 | 实现 | 优点 / 缺点 |
|---|---|---|---|
| `same-stack`(**推荐**) | 项目前端栈已定 | **独立 preview-project**:`{子项目}/docs/design/preview-project/`(同技术栈的独立前端项目 · 自带目标库 · 含 mock data)· **源即全景权威** · 预览靠跑 `preview.sh` 起 dev server(动态端口 · 不在 teamwork 层起 server) | ✅ 真实组件渲染保真 · **不污染真实工程** · **解「本 Feature 引入新库(如 antd 未装)」鸡蛋问题**(preview-project 独立装)· 实时热更 ❌ 需搭独立项目 |
| `static-html`(兜底) | 前端栈未定 / Designer-only / Greenfield POC | 手写 `{panorama_path}/preview/*.html`(CDN) | ✅ 零 build chain · designer 独立产出 ❌ 介质差异 → **不可能像素级仿 live**(系统字体 vs webfont · CDN 编译时机 · 语义 token 缺失 等)· **仅作 IA / 视觉层级 / Token 一致性参考** |

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
> 🔴 **IA 镜像律**(v8.133):preview-project 的**路由结构 = 真实 app**(与 `sitemap.md` 一致)—— 本次设计页挂**真实目标 path**(`pages_changed[].route_path` · 如 `/settings/ingest`)· **`/` = 真实首页设计稿**(已有则复用 · 全景首版即建)· **router 必含**(「单页预览不需要路由 · 有意省略」= 漂移反模式 —— 全景的价值就在用户能沿真实导航走到新页)。
> 🔴 **分层同构律**(v8.134 · 替代 v8.133「数据层唯一差异律」· 同构承诺按「能否由结构保证」分层):
> - **Layer 1 基建层(业务无关 · 完全一致)**:页面框架(shell/layout)· 前端架构(构建链/路由机制/栈版本)· UI 组件库 · 主题 tokens。实现优先级:① **共享包**(monorepo workspace 包 · preview-project 与真实 app **依赖同一份代码** · 一致性由单源结构保证 · 零镜像维护)② 暂不可抽包 → 版本锁定镜像(退路 · UI.md 记豁免 + 回收计划)。
> - **Layer 2 业务页面层**:全景页承载**意图四要素** —— 布局结构 / 交互流 / 状态(normal·empty·loading·error)/ 字段映射(UI.md 既有段落即契约载体)。🔴 **一致性按介质定**:
>   - **same-stack → 完全一致**:页面内容从**同一份共享组件 / 真实页面源**渲染 · **零预览痕迹** · 设计=代码是「**构造保证**」非人肉对齐 · **不留「像素自由」口子**。🔴 机制 = **真实交互页面内做**(按钮→Drawer/编辑/详情 · 同真实 app · 交互保真)· **dev 顶栏只放页面到不了的态**(Loading/Error/Empty/边缘态 · 真实交互无法自然触发的)· 页面禁的是**预览专属控件**(state-switcher 下拉等真实 app 没有的 · 非真实交互按钮)· 详 § preview dev 顶栏。
>   - **static-html → 仅参考**:介质差异客观不可像素仿 · 四要素对齐即可(dev 还原与 pm_acceptance 的对照物)。
> - **权威时效(防权威倒置)**:页面层全景的设计权威**至该页 ship 为止** —— ship 后代码即唯一真相 · 全景页转历史参考 + 下一轮设计底版。🔴 反模式:拿停更的全景页「纠正」已演化的真实页面。
> - **下游编译契约**:共享基建有两个消费者(真实 app + 全景)· 任何 feature 改共享基建 → **dev 结束须保证全景编译通过**(详 [dev-stage.md §3.5](./dev-stage.md))。
> 🟢 **same-stack 去静态 build 产物**(用户拍板):**去掉静态 build 产物**(`docs/design/preview/*.html` 不再必产)· 全景权威 = preview-project **源**(committed · 要看跑 preview.sh)· 预览 = dev server 实时(动态端口 · 不在 teamwork 层起 server)。`pages_changed[].panorama_file` 对 same-stack 可选(指向 preview-project 内渲染该页的源/路由 · 非文件存在性校验)。
> 老 Feature(in-app /design 路由 / 静态 preview)向后兼容不强迁 · 新 Feature 用本模型。

🔴 **硬规则**:
- 项目 `PROJECT.md` 声明了前端栈(`frontend_stack` 非空)→ panorama **必须 `same-stack`** · 用 `static-html` 即规范违规
- 「前端栈已定 + panorama 仍 `static-html`」= **dirty state** · 必须开 Feature 把 panorama 迁到 `same-stack` · 不可永久 hack(4 轮调像素仍有差异 = 介质差异不可调和)
- 🔴 **same-stack 物化**:`{子项目}/docs/design/preview-project/` + `preview.sh` + `package.json` 必存在 · ui_design-complete **校验**(`_check_same_stack_preview_project`)· **不可只写 UI.md markdown 跳过可跑预览**(防 AI 拿"验证器只校验 UI.md""same-stack 不要求产物"当借口零可视产出 —— 最低物化闸 ≠ 免做交付物许可)
- `UI.md` frontmatter 缺 `panorama_medium` → verify-panorama / UI_DESIGN_SPEC 视作 `static-html`(向后兼容 · 但新建 Feature 必显式声明)

---

## 预览(same-stack · preview.sh 即唯一预览)

> 🔴 same-stack 预览是 ES-module bundle · `file://` 因 CORS 打不开 → **必须 dev server**。**不在 teamwork 层起 server**(用户拍板)· 改用 preview-project 自己的 dev server · **每次选一个动态空闲端口** → 并行 worktree / 多终端 **天然不冲突**。

```bash
# preview-project 内含 preview.sh(从 templates/preview-project-preview.sh 拷入 · chmod +x)
# PMO 后台跑 · 抓早期 stdout 的 PREVIEW_URL= 行给用户 browse:
bash {子项目}/docs/design/preview-project/preview.sh    # → PREVIEW_URL=http://localhost:<动态端口>/
```

`preview.sh` 做:① 按 lockfile 选包管理器 ② 缺 node_modules 则装 ③ `node net` 选动态空闲端口(`PORT` env 可覆盖)④ 打印 `PREVIEW_URL=` ⑤ 起 dev server(vite/next/CRA · 脚本内一行按框架改)。

🔴 **预览地址约定(IA 镜像 · v8.133)**:preview.sh 打印的是**根 URL**;PMO 给用户 / browse 的预览地址 = `PREVIEW_URL` + **本次设计页 `route_path`**(直达 · 取自 UI.md `pages_changed[].route_path`)· 并注明 `/` = 真实首页设计稿;多页改动 → 每页一条直达 URL 清单。🔴 把新设计页渲染在 `/`(顶掉首页)= IA 镜像违规。

🔴 **注意**:① dev server 前台阻塞 → PMO 用 `run_in_background` 跑 · 读 `PREVIEW_URL=` 行 · 等就绪(~2s)再 browse · 用完 kill 进程 ② 仅 `localhost`(本机)③ 首跑装依赖较慢。

---

## preview dev 顶栏(只放页面到不了的 · 真实交互优先 · 页面=真代码)

> 🔴 **真实可达的交互 → 页面内做成真实交互(默认)**(治本:别把按钮→Drawer 这种真实交互也赶到顶栏 · 那样预览不反映真实交互路径):真实 app 里**点页面按钮能到的** —— 新建/编辑 **Drawer · Modal · 行→详情 · 页内导航/Tab · 配置弹窗** —— 在 preview 里就做成**真实可点**(点页面的「新建模型」就开对应 Drawer · 同真实 app)。这正是「设计=代码」要的**交互保真**。
>
> 🔴 **dev 顶栏只放「页面入口覆盖不到的」**(preview-project 的 dev 布局外壳 · 真实 app 不存在):
> - **页面区**:每个全景页一个入口 → `route_path`(直达 · 与 sitemap 一致)· 🔴 页间跳转若真实 app 有**页内入口**(导航/链接/按钮)则**页内优先** · 顶栏只兜底无页内入口的页。
> - **状态区**:**真实交互无法自然触发的态** —— `Loading / Error / Empty / 边缘态`(没有「让我看 loading 态」的真实按钮)+ 难自然触发的展示态 / preset 直开某特殊态(评审便利)。🔴 **能在页面内点出来的态不放这里**。
>
> 🔴 **「禁内嵌 switcher」澄清**(修订 v8.169 过度收口):禁的是**预览专属控件**(真实 app 没有的 state-switcher 下拉 / 场景 toggle 嵌进页面)· **不是禁真实交互按钮**(新建/编辑/详情那些真实 app 有的 · 该真实工作)。状态**注入**仍走顶栏(mock-data provider 按状态注入 · 页面组件不知自己在被预览 = Storybook args),但**交互可达性走页面**。
> 🔴 **不违 IA 镜像**:`/` 仍是真实首页 · 顶栏是 `/` 之上的**工具层**(不占真实路由)。

---

## 怎么做

### 1. 加载上下文
读 PRD.md(用户场景)· sitemap.md(信息架构)· 🔴 **UI-RULES.md(设计规范:控件偏好/色板策略/交互约定/a11y · workspace `project-specs/` + 子项目 `{子项目}/docs/` 两层)**· KNOWLEDGE.md(项目级 UI 踩坑)· `PROJECT.md § 技术栈`(决定 panorama_medium)

🔴 **判定:扩已有真实页 vs 全新页**(决定设计稿的单位)。本 Feature 若是给**已存在的真实页**加东西(真实代码已渲染该页 · 如给 `/analytics/offers` 加 tab)→ **必读该页真实组件/路由源的当前实际形态**(整体布局 / 筛选区 / KPI·funnel·trend / 卡片位置 / 表格列…)作 grounding(同 prepare/goal「decisive 前提核验真实文件」· 不靠 Explore 摘要猜)· 设计单位是**整张页**(见 §3 复现门)。全新页 → 从 design system + UI-RULES 起草。

### 2. Designer 起草 UI.md
frontmatter `pages: [{id, title}]` + `panorama_medium: same-stack|static-html` 必 · body §页面列表 / §交互流 / §视觉规范 / §字段映射(对应 PRD.AC)· 🔴 §交互流/§视觉规范 **逐条对照下文 § 交互 & 视觉质量 rubric**(治「对交互没判断力」· 不等用户逐条纠)

### 3. 产出 panorama(按 `panorama_medium` 分支)

🔴 **全景在规划期已出生 · ui_design 是增量扩**:涉 UI 的 WS 在 [feature-planning Step 5「UI 可视全景初步规划」](../docs/feature-planning.md) 时已 seed `preview-project`(design system + 关键页)。ui_design 默认在**已有全景上增量补**本 Feature 的页与细节(同一份活物 · 源即权威)· **不是从零搭**。仅当规划期没出全景(老项目 / 跳过规划路径)→ 此处**首次 seed**(回退 · 扩已有页则按下方「复现门」按真实代码补全这张页 · **不是画概念**)。

🔴 **扩已有页 → 设计稿 = 真实页全貌复现 + 新部分集成(治「概念页 / 局部设计」)**:本 Feature 给已存在的真实页加东西时,设计稿的单位是**整张页**,不是孤立新控件:
- ① **读真实代码定形态**(不是猜):打开该页真实组件/路由源,抓当前实际布局 —— 筛选区 / KPI·funnel·trend / 卡片位置 / 表格列 / Top card…(grounding 同 prepare/goal「核验真实文件」· 不轻信 Explore 摘要)。
- ② **preview-project 按真实形态复现整页 → 再集成本 Feature 新部分**。🔴 **复现 ≠ 重写**(已有页本身就是真实代码 · 优先级同 Layer 1):**㉑ 导入真实页/组件源**(同 monorepo workspace 包 → preview 与真实 app **同一份代码** · 一致性单源结构保证 · 改真实页 preview 自动跟 = 最大限度一致)→ **㉒ 暂不可导入**(app-local 未抽包)→ **按真实源 1:1 镜像** + UI.md 记豁免 + 抽包回收计划(退路 · 非默认)→ 🔴 **绝不凭印象重画**(= 概念页变体 · drift 源头)。新部分(本 Feature)是唯一净新增,在真实上下文里定位新 tab / 区块怎么落。
- 🔴 **禁出「概念页」**:只画新控件、不复现它所在真实页的结构 = 局部设计 = 评审/用户看不出真实落地效果。**实证 AON Offer-Analysis case**:预览只做概念页 · 真实 `/analytics/offers` 的筛选区 / KPI / Top card 位置没对齐 → 用户判「设计稿不完整、和实际不一致」要求重做。
- 全景里**已有该页保真复现** → 直接走下方「增量补」;**没有**(brownfield / 规划期没 seed 这张)→ 先按 ①② 复现这张页(**不是从零画概念** · 是按真实代码补全 + 集成)。

🟢 **推荐:全景为唯一权威**(详上 § 全景为唯一权威 · UI.md frontmatter 加 `pages_changed[]`):

- **`same-stack`**:在 `{子项目}/docs/design/preview-project/` **扩/搭**同栈独立项目(规划期已 seed → 增量补本 Feature 页;不存在 → 首次搭)(基建层共享包/同版 · mock data · **路由结构镜像真实 app** · 本 Feature 页挂真实 `route_path` · `/` = 首页设计稿 · 页面层 = 意图权威〔四要素〕)· **源即全景权威**(committed · 不出静态 build)· 从 `{SKILL_ROOT}/templates/preview-project-preview.sh` 拷一份 `preview.sh` 进 preview-project 根(`chmod +x` · 按框架改 dev server 那一行)· 本 Feature **引入新库**时 preview-project 独立装该库(解鸡蛋问题)· 🔴 **验证渲染:后台跑 `bash {子项目}/docs/design/preview-project/preview.sh` → 读 `PREVIEW_URL=` → 等就绪 browse 截图**(详上 § 预览 · `file://` 因 CORS 打不开 · **不在 teamwork 层起 server** · 动态端口并行不冲突)· 🔴 **截图存系统临时目录 `${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/`(自检一次性产物 · 非交付)· 绝不落 worktree / 主工作区根**(详 [docs/conventions.md §12.5](../docs/conventions.md))
- **`static-html`**:**直接编辑** `panorama_path/preview/<page.id>.html`(全景权威 · 唯一 source · worktree 内改 · merge 后同步全景)· UI.md `pages_changed[].panorama_file` 链到权威路径 · **Feature 内不存 preview/ 副本**

老模式(向后兼容 · 无 `pages_changed[]`):每 page.id 对应 Feature 内 `preview/<page.id>.html`(副本)· 静态 HTML + Tailwind CDN · 含可点击交互 —— 不推荐(双副本不一致风险)

### 4. 判定 panorama 是否被本 Feature 改动(workspace 级 IA 影响?)
本 Feature UI 若动了 workspace 级 panorama(sitemap 节点 / overview / 设计 token)→ 在 §6 `ui_design-complete --panorama-changed=true` 显式标记 → 自动转 **panorama_sync** stage(workspace 级单独 stage · 收敛 sitemap 更新 + 跨 Feature reviewer 协调评审 · 详 [panorama-sync-stage.md](./panorama-sync-stage.md))。
不动 panorama → `--panorama-changed=false` · 直进 blueprint。

🟢 判据是「panorama 文件要不要动」(含 sitemap 描述列更新)· 不必预判影响大小 —— panorama_sync 内部再判级:节点内增量(L1)不暂停自动过 · 结构变更(L2)才停。`true` ≠ 必暂停。

🔴 **本 stage 不直接改 sitemap.md** —— 改 sitemap / overview 是 panorama_sync stage 的产物(隔离审计 / 暂停点 / 跨 Feature 评审)。

### 5. ⏸️ 用户预览确认(R5 暂停点)
🔴 **`auto_mode=true` 时跳过此暂停点** —— 设计意图已落 UI.md / preview · auto 用户接受(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

🔴 emit R5 标准 1/2/3(模板见 [SKILL.md § R5(b)](../SKILL.md)):
1. **确认 UI · 进入 blueprint** 💡 推荐 — `ui_design-complete` → 自动转 blueprint
2. **要改设计** — Designer 按你的反馈改 UI.md + preview
3. **其他指示**

📚 决策参考:
- **`static-html`**:直接 browse `preview/<page>.html`(纯 HTML · `file://` 可开)
- **`same-stack`**:后台跑 `bash {子项目}/docs/design/preview-project/preview.sh` → 把 `PREVIEW_URL` + 本次设计页 `route_path` 的**直达 URL** 给用户 browse(根 `/` = 首页设计稿 · 多页给直达清单 · dev server 实时 · 动态端口 · 详 § 预览)

### 6. complete
```
state.py ui_design-complete --feature X --auto-commit Y \
  --artifacts <UI.md[,preview/]> \
  --panorama-changed {true|false}
```
- `--artifacts`:UI.md 必 · `static-html` 介质加 `preview/` · `same-stack` 介质仅 UI.md
- `--panorama-changed`:**必传** · true → 自动转 `panorama_sync` stage(workspace IA 同步 + 跨 Feature 评审)· false → 直进 blueprint

---

## 交互 & 视觉质量 rubric(设计时逐条对照 · dev 还原 + 评审同一基准 · 单源)

> 🔴 **为什么有这份 rubric**:模型对交互体验缺天生判断力(实战反馈:涉交互改动「降智」· 要人逐条纠正)· 把**可枚举**的设计判断前置成清单 → 模型主动答、不靠人喂(真正的 taste 那层仍归 §5 用户预览)。蒸馏自 `design-review`(交互状态/排版/颜色/间距)+ `frontend-design`(copy)· 🔴 按「**扩展既有 app**」裁剪 —— 品牌独特性那套**只在全景首版/greenfield 用**,per-feature 要的是**和既有系统一致**。

### A. 交互状态(每个交互元素逐条 · 治「对交互没判断力」)
- **反馈**:hover · 按下 active · `focus-visible` 环(禁 `outline:none` 不补替代)· loading **骨架匹配真实布局**(非裸转圈)· success 确认 + 自动消失
- **完备态**:normal / **empty**(消息 + 主操作 + 视觉 · 非「无数据」)/ loading / **error**(具体原因 + 下一步怎么做 · 非「出错了」)/ disabled(opacity + `cursor:not-allowed`)· 首次 vs 回访(如适用)
- **可恢复**:破坏性操作有确认 · 误操作能撤销/退回(接 PL 质疑六问⑥ 既有行为变更)
- **边界退化**:超长文本/溢出 · 慢网/超时 · 快速重复点击 · 并发 · 超大列表 —— 交互怎么不崩
- **触控/指针**:可点元素 `cursor:pointer` · 触控目标 ≥ 44px

### B. 视觉质量地板(🔴 对照既有设计系统 · 不自造)
- **排版**:复用既有字阶/字重 · body ≥ 16px · 不跳标题级 · 数字列 `tabular-nums`
- **颜色**:复用既有语义色(success/error/warning)· WCAG AA(正文 4.5:1)· 不靠颜色单独编码(配图标/文字)
- **间距**:既有 4/8px scale · 不臆造值 · 对齐既有栅格 · radius 跟既有层级
- **一致 > 独特**:页面**匹配现有组件/模式 · 不重新发明**(🔴 策略对照 **UI-RULES**〔控件偏好/色板策略〕· 视觉值对照 preview-project tokens · 独特品牌设计仅全景首版/greenfield 相关)

### C. 文案(copy = 设计材料 · 非装饰)
- 从**用户视角**命名(「通知」非「webhook 配置」)· active voice(「保存更改」非「提交」)
- 同一动作**全流程同名**(按钮「发布」→ toast「已发布」)· error/empty 当**指引**不当情绪:说清出了什么 + 下一步

🔴 **rubric 是设计/还原/评审同一基准**:Designer 起草(§2)逐条过 · dev 还原(dev-stage §3)按它核 · §5 用户预览前 Designer 自查报告对 **A 段逐项过**(无则显式「N-A + 理由」)· reviewer 审对着这份(防凭空 generic 评)。

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | `roles/designer.md` | § Telos + 创作要点 | UX 视角 |
| 2. Designer 起草 UI.md | `roles/designer.md` + 本文件 § 交互 & 视觉质量 rubric | § 创作要点 + rubric A/B/C | frontmatter pages[] + body 4 段 · 🔴 §交互流/§视觉规范 逐条对照 rubric |
| 3. 产出 panorama | `roles/designer.md` | § 创作要点 | 按 `panorama_medium` 走 · same-stack 搭 preview-project + preview.sh(源即权威)· static-html 产 preview/*.html · 含可交互 |
| 4. panorama 判定 | — | — | (无 cite 要求 · 涉变更交 panorama_sync stage) |
| 5. ⏸️ 用户预览确认 | — | — | (无) |
| 6. complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**(均按 `panorama_medium` 适配):
- **`static-html`**:preview HTML 文件名 = `<page.id>.html`(物化校验 `pages[].id` 对应 .html 存在 · 错位 → ui_design-complete FAIL);`verify-panorama.py` 走完整校验(self-check + host marker + preview count + panorama_path)
- **`same-stack`**(物化):**要求** `{panorama_path}/preview-project/` + `preview.sh` + `package.json` 存在 —— ui_design-complete 校验(`_check_same_stack_preview_project`)· 全景权威 = preview-project **源**(不再要静态 build 产物)· 🔴 **不再「不要求产物 · return True」**(防 cut-corner)· 预览靠跑 preview.sh(动态端口)· UI.md 自查 + frontmatter 仍校验
- `stage_contracts.ui_design.output_satisfied=true` → dev-start 自动触发 UI 还原校验段(dev-stage §3 按 medium 分支)

**preview SOP**(违反 → dev 还原 / pm_acceptance 打回):
- 抽公共组件 / CSS class · preview 引用统一样式表 · 不每页 inline(维护噩梦)
- preview HTML 含点击 / 表单 / 跳转(真实交互)· 不只是静态图 · 让 dev 可 verify 交互
- 🔴 **分层同构反模式**(same-stack):新设计页渲染在 `/` 顶掉首页 / 省略 router / 路由与 sitemap 不一致(IA 层);基建层不走共享包而自造组件·自配主题·版本漂移(Layer 1);全景页缺意图四要素(Layer 2);**扩已有页凭印象重画 existing page(不导入/不镜像真实页源)= 概念页变体**(复现门 §3 · drift 源头);**dev 跳过设计↔实际一致性核对**(dev-stage §3 · 落地闸);拿停更全景页纠正已 ship 页面(权威倒置);改共享基建不验全景编译(下游契约 · dev-stage §3.5)
- ⏳ 物化 TODO:same-stack 时 `pages_changed[].route_path` 必填的工具校验(parse_frontmatter 不支持嵌套 list-of-dict · 需 raw 文本扫描 · 渐进物化)

**sitemap 改动**:必显式列影响范围 · 主对话与相关 Feature owner 协调(防破坏现有路由)

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - UI.md → `{SKILL_ROOT}/templates/ui.md`(含 panorama_medium frontmatter 示例)
> - preview/*.html(static-html 时)→ 无统一模板 · 按项目设计语言写
> - preview.sh(same-stack 时)→ `{SKILL_ROOT}/templates/preview-project-preview.sh`(拷入 preview-project 根 · 按框架改 dev server 一行)

### `UI.md`
frontmatter `pages: [{id, title}]` · body 4 段(页面列表 / 交互流 / 视觉规范 / 字段映射)

### panorama 产物(按 `panorama_medium`)
- **`static-html`**:`preview/*.html` 至少 1 文件 · `pages[].id` 全有对应 · 可交互
- **`same-stack`**:`{子项目}/docs/design/preview-project/`(同栈可跑独立项目 · 源即全景权威 · node_modules gitignore)+ `preview.sh`(预览入口 · 动态端口起 dev server)+ `package.json` —— **物化校验三者存在** · **不出静态 build 产物**

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `UI_DESIGN_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
