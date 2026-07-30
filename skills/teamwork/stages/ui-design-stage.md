# UI Design Stage

> 🧭 **四段结构**(v8.285 · 详 [STAGES.md §3](../STAGES.md)):目标 + 硬规则白名单 + 手段菜单 + 产物契约 · 手段 AI 自选。

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
5. 🔴 **本 stage 不直接改 `sitemap.md`** —— 改 sitemap / overview 归 panorama_sync(why:跨 Feature IA 影响必须被单独一层看见〔隔离审计 + 暂停点 + 跨 Feature 评审〕)。
6. 🔴 **截图落系统临时目录** `${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/` · **绝不落 worktree / 主工作区根**(why:自检一次性产物非交付物 · 落仓库就污染 diff · 详 [conventions §12.5](../docs/conventions.md))。
7. ⏸️ **用户预览确认(R5 暂停点)** · `auto_mode=true` 时跳过(设计意图已落 UI.md/preview · auto 用户接受)(why:「看着对不对」是 taste 层 · 用户主权 · AI 判不了)。
8. **`--panorama-changed` 必传**(true → 自动转 panorama_sync · false → 直进 blueprint)(why:workspace 级 IA 影响的路由开关 —— 漏传 = 跨 Feature 影响无人评审)。

---

## ③ 建议手段菜单(AI 自选 · 不强制)

| 手段 | 何时值得 |
|---|---|
| **same-stack:扩/搭 preview-project** | 规划期已 seed → 增量补本 Feature 页;不存在 → 首次搭。基建层走共享包/同版 · mock data · 页面层承载意图四要素 · 源即全景权威(committed · 不出静态 build)· 本 Feature 引入新库时 preview-project 独立装(解鸡蛋问题) |
| **static-html:直接编辑全景 HTML** | 前端栈未定 / Designer-only —— 改 `panorama_path/preview/<page.id>.html`(唯一 source · Feature 内不存副本)· `pages_changed[].panorama_file` 链到权威路径 |
| **复现手段排序**(扩已有页)| 优先导入真实页/组件源(同一份代码 · 一致性由结构保证);不可导入 → 按真实源 1:1 镜像 + UI.md 记豁免 |
| **判定 panorama 是否被改动** | 判据是「panorama 文件要不要动」(含 sitemap 描述列)· 不必预判影响大小 —— panorama_sync 内部再判级(L1 不停 / L2 才停)· `true` ≠ 必暂停 |

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
> 🔴 **IA 镜像律**(v8.133):preview-project 的**路由结构 = 真实 app**(与 `sitemap.md` 一致)—— 本次设计页挂**真实目标 path**(`pages_changed[].route_path` · 如 `/settings/ingest`)· **`/` = 真实首页设计稿**(已有则复用 · 全景首版即建)· **router 必含**(「单页预览不需要路由 · 有意省略」= 漂移反模式 —— 全景的价值就在用户能沿真实导航走到新页)。
> 🔴 **分层同构律**(v8.134 · 替代 v8.133「数据层唯一差异律」· 同构承诺按「能否由结构保证」分层):
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

🔴 **预览地址约定(IA 镜像 · v8.133)**:preview.sh 打印的是**根 URL**;PMO 给用户 / browse 的预览地址 = `PREVIEW_URL` + **本次设计页 `route_path`**(直达 · 取自 UI.md `pages_changed[].route_path`)· 并注明 `/` = 真实首页设计稿;多页改动 → 每页一条直达 URL 清单。🔴 把新设计页渲染在 `/`(顶掉首页)= IA 镜像违规。

🔴 **注意**:dev server 前台阻塞 → PMO 用 `run_in_background` 跑 · 读 `PREVIEW_URL=` 行 · 等就绪(~2s)再 browse · 用完 kill 进程。

---

## preview dev 工具面板(🔴 右下角悬浮 · 只放页面到不了的态)

> 约束只有两条(v8.284 · 原 12 行「为什么右下角不是顶栏」的设计品味论证与 v8.169 版本纠错史已删):
> - 🔴 **真实 app 里点得到的交互 → 页面内做成真实可点**(新建/编辑 Drawer · Modal · 行→详情 · 页内导航/Tab)—— 这是 same-stack「交互保真」的核心;
> - 🔴 **工具面板只放页面入口覆盖不到的**:状态区(Loading / Error / Empty / 边缘态 · 真实交互无法自然触发的)+ 页面区(Prototype Nav 兜底无页内入口的页)。禁的是**预览专属控件**(真实 app 没有的 state-switcher 下拉/场景 toggle 嵌进页面)· **不禁真实交互按钮**。
> 悬浮 overlay 不占布局流 → 不违 IA 镜像(`/` 仍是真实首页)· 可折叠。

---

## 交互 & 视觉质量判据(设计/还原/评审同一基准 · v8.284 由 21 行细则压成 5 条判据)

> v8.284:原细则(hover/focus-visible 环/骨架屏/WCAG AA 4.5:1/触控 ≥44px/tabular-nums/4-8px scale…)已删 —— 那是模型内建的前端常识;原文写明理由是「模型对交互体验缺天生判断力」,该前提已随模型能力失效。留**判据**不留细则:

- **完备四态必设计**:normal / empty(消息 + 主操作)/ loading / error(具体原因 + 下一步)· 首次 vs 回访(如适用)
- **可恢复**:破坏性操作有确认 · 误操作能撤销退回(接 PL 质疑六问⑥ 既有行为变更)
- **边界退化想过**:超长文本 / 慢网超时 / 快速重复点击 / 并发 / 超大列表 —— 交互怎么不崩
- 🔴 **一致 > 独特**:匹配现有组件与模式、**不重新发明** —— 策略对照 **UI-RULES**(控件偏好/色板策略)· 视觉值对照 preview-project tokens(独特品牌设计仅全景首版/greenfield)
- **文案从用户视角**:「通知」非「webhook 配置」· 同一动作全流程同名 · error/empty 当指引不当情绪

> 🧠 **写法非环节**(v8.263/v8.284):**画预览稿时就按这些判据画**,不是写完再逐项过。dev 还原(dev-stage ②硬规则 4)与 reviewer 审同用这份基准(防凭空 generic 评)。

---

## ④ Output Contract

- **`UI.md`**:**schema 与章节以模板为单源** `{SKILL_ROOT}/templates/ui.md`(v8.293:原契约点名 §页面列表/§交互流/§视觉规范/§字段映射 —— 模板里**没有这四段**,且模板明令「视觉描述一律归 HTML 预览产物 · 不在本文复述」· Designer 照哪边写都违反另一边)。UI.md 只承载**意图 / 追溯 / 审计**:§全景权威索引 · §UI-AC-COVERAGE · §Designer 自查报告 · §变更记录。
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
  --artifacts <UI.md[,preview/]> --panorama-changed {true|false}
# --artifacts:UI.md 必 · static-html 加 preview/ · same-stack 仅 UI.md
```

**sitemap 改动**:必显式列影响范围 · 与相关 Feature owner 协调(防破坏现有路由)。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `UI_DESIGN_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
