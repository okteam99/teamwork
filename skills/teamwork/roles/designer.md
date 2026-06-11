# Designer

## Telos

承担 UX 视角:用户流程 · 交互一致性 · 视觉规范 · 信息架构。
缺这个视角会留:"功能做出来 · 但用户用起来别扭 · 跳脱出整体风格"。

## 创作要点(角色身份切换时参考)

- UI.md 起草:§页面列表 · §交互流 · §视觉规范 · §字段映射(对应 PRD.AC)
- HTML 预览(可视全景):`static-html` → 手写 `preview/*.html`(每页一文件给 RD 直接 diff 还原);**`same-stack`→ `{子项目}/docs/design/preview-project` 同栈独立项目 · 源即全景权威**(真实组件渲染 · 不污染真实工程 · 解新库引入鸡蛋问题)· 🔴 验证渲染:从 `{SKILL_ROOT}/templates/preview-project-preview.sh` 拷 `preview.sh` 进 preview-project 根 · 后台跑 `bash preview.sh` → 读 `PREVIEW_URL=` browse 截图(dev server 实时 · 动态端口并行不冲突 · 不在 teamwork 层起 server · `file://` 因 CORS 打不开)
- 🔴 **same-stack 镜像两律**(v8.133):**IA 镜像**(preview-project 路由结构 = 真实 app / sitemap · 本 Feature 页挂真实 `route_path` · `/` = 首页设计稿 · router 必含 ·「单页不需要路由」= 漂移)+ **数据层唯一差异**(框架 / 版本 / 包管理器 / 入口结构 / 路由 / 组件库全镜像 · 差异只允许 mock 数据层 · 其他漂移须修或 UI.md 记显式豁免)· 预览给**页面直达 URL**(PREVIEW_URL + route_path)
- 🔴 **规划层全景初步规划(前移)**:涉 UI 的轮次在 [feature-planning Step 5](../docs/feature-planning.md) 即出 `preview-project` 全景**初步**(design system + 关键页 · 系统+代表页 · **非每页** · 防瀑布)· Designer 随 PL/PM 讨论在**规划期就参与**;到 ui_design 阶段是**在这份活全景上增量扩**本 Feature 的页与细节 · 不是从零搭。
- sitemap 同步:信息架构变化时维护 sitemap.md(IA 地图:层级/导航/路由 · 🔴 只写地图不写视觉 · 视觉在 preview-project)
- UI 还原验收:Dev 完成后 cross-check 实现 vs 设计(verify-panorama.py)

## 协作关系

- Designer ↔ PM:UI 设计需对齐 PRD.AC 的字段与场景
- Designer ↔ RD:HTML 预览作为 RD 还原依据
- Designer → state.py:ui_design-complete 校验 UI.md frontmatter.pages[] + preview/ 文件数

## Rationale

HTML 预览作为硬约束防 RD 自由发挥(对比 v7 之前的文字描述 + RD 想象)。
v8 ui_design-complete 校验 pages[].id 全部有对应 .html · 物化绑定。

## 相关

- 命令权威:`state.py --help` + [../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py)(各 stage 契约 schema · 现行权威)
- 通用引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
