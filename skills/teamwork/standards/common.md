# 通用开发规范

> 前后端共用的规范，所有 RD 必须遵守。
> 📎 后端专项规范见 [backend.md](./backend.md) · 前端专项见本文件 §七

---

## 一、测试核心原则

> TDD 手段规定已撤除(怎么测 AI 自觉)· 测试的**结果规则 + 机器门**见 [HARD-RULES.md](./HARD-RULES.md) · 本节不复述通用原则。

## 二、代码架构规范

> 通用架构原则(分层、单一职责、模块边界、Review 友好度)模型已内建 —— 本节只留**本框架的偏离与约定**:

- **架构文档维护**:架构决策(有备选 + 后果)→ `docs/adr/`;子项目拓扑/依赖方向 → `ARCHITECTURE.md`。**代码是唯一真相**,文档是它的索引,不是它的替身。
- **项目特例走 `DEV-RULES.md`**(人维护)· 本文件只装跨项目缺省。

## 三、测试脚本约定

> RD 在开发阶段负责创建/维护测试脚本。规范只约定脚本接口（名称 + 行为），不约定实现细节（Docker/K8s/本地均可）。
> PMO 和 Test Stage 通过脚本与测试环境交互，不直接执行 docker-compose 等底层命令。

### 两层脚本结构(Monorepo · 名称 + 职责即契约 · 逐脚本的实现叙述不复述)

- **根级 `scripts/`(全局环境 · 跨子项目共享 · 首次有集成测试需求时创建 · 新增子项目依赖时更新)**:
  - `test-env-setup.sh` —— 启动全部依赖服务 + 各子项目服务(按依赖顺序)+ 加载全局前置数据 + 等健康检查;🔴 成功时 stdout **最后一行输出环境信息 JSON**(如 `{"db_url": "...", "services": {"api": "http://localhost:8080"}}`)· 可选 `--skip-if-running`(已在运行则跳过)· 实现自由(Docker / 本地进程 / 远程均可);
  - `test-env-check.sh` —— 轻量连通性检查(只 ping 不启动 · Test Stage 内部复核用 · 与 setup 同步创建);
  - `test-env-teardown.sh` —— 可选 · 默认保留环境供复用。
- **子项目级 `{subproject}/scripts/`(测试执行 · 只管自己 · 🔴 假定全局环境已就绪 · 不负责启动)**:`test-unit.sh`(🔴 不依赖全局环境 · 纯代码级)· `test-integration.sh` · `test-api-e2e.sh`(可选传 TC.md 路径 · 输出完整 request/response)· `test-browser-e2e.sh`(可选)—— 底层命令由项目定(cargo / npm / pytest)· 编写对应测试时同步创建。
- **PMO 调用顺序**:根级 setup → 子项目 test-*。

### 脚本接口规范(🔴 所有脚本必须满足)

**退出码 0=成功 / 非0=失败 · 幂等(重复执行不出错)· 无交互(不 read stdin / 不弹确认 —— 自动化场景无 TTY)· 失败时 stdout/stderr 给足诊断信息。**

🔴 Dev Stage 自查:根级 + 子项目脚本存在且至少本地跑通一次;架构师 CR 确认接口符合约定(退出码/幂等/无交互)。

### PMO 预检(v8 物化路径)

v7 三级 dispatch 预检已废 · 由物化路径替代,不依赖记忆顺序:**Feature ID 冲突** → `state.py prepare-check`(返回 next_available_id)· **测试环境检查** → 本节脚本(PMO/RD 按 stage brief 触发)· **stage 入口校验** → `state.py xxx-start` 物化拦截 · **保护标记/仓库约束** → 项目根 CLAUDE.md/AGENTS.md。

---

## 四、实现完成的硬门

> 不设 RD 自查/报告仪式(环节化自检 · 零机器消费者 · 与 `templates/tech.md §完工自查` 职能重复)—— **证据要求由机器门承担**:`dev-complete --test-exit-code 0` + `--test-stdout` 非空 + artifacts 在 changeset。仅两条真规则:

- 🔴 **Build 必须跑通才能进 Code Review**(硬门禁)。CI 是最后一道安全网,不是第一道发现机制。无 build 步骤的项目(纯库 / 纯脚本 / Python 应用)必须**显式标注「无 build 步骤」**,不能省略。
- 🟡 **worktree lazy-install 踩坑**:单测能跑但 `npm run build` / `next build` 失败(找不到 webpack / postcss / next 本身)= worktree 只装了单测所需 deps,build 工具链未装。处理:① worktree 内补装(`npm install --include=dev`,最稳,30s-2min)② 软链主 worktree 的 `node_modules`(秒级,但 monorepo workspace / 不同 lockfile 易出怪问题)③ 记进项目 `KNOWLEDGE.md` Gotcha。

## 四B、Designer 自查规范

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
- ❌ 反模式:拿**历史 Feature 的 `preview/*.html`** 当框架基线(peer Feature 只可作内容参考 · 详 §四C 权威源单源规则 · 实证 PTR-F032)。

### Designer 自查报告模板

🔴 **模板单源 = [templates/ui.md § Designer 自查报告](../templates/ui.md)**(UI.md 全部章节的 schema 单源 · 含 6 维汇总表 + 全景对齐证据 + 增量 diff + 结论)· 本文件不再复制一份 —— 此前两处各存一份,维度数已漂移(这边 5 维 · 那边 6 维),**双副本必漂**。verify-panorama.py 校验的是 UI.md 实例(段存在 + 占位符已填 + 结论为通过)。

### 自查结果处理

全 ✅ → ⏸️ 用户确认设计稿;有 ⚠️ 低风险(如 1 个 AC 未覆盖且已补)→ 修复后重新自查;🔴 结构性红线命中 → 停 Stage → DONE_WITH_CONCERNS;verify-panorama.py FAIL → 按 stderr hint 补完报告重跑。

---

## 四C、权威源单源规则（跨角色汇总指针）

> **本节定位**：跨角色 meta-rule · 不复述各 role L2 sub-spec 原文 · 只列表汇总 + 后续注册模板.

**核心原则**：每个产物维度有唯一**权威源**（spec / template / panorama / KNOWLEDGE 等）· peer Feature 仅可作**内容参考**（写法、套路、决策历史）· ❌ 禁止当**格式 / 框架 / schema** 基线.

**优先级**：teamwork 规范权威源 > peer Feature 历史. 触发"参考最近相似 Feature"心智路径时 · 默认走错 · 必须改走权威源.

**已注册维度**（各 L2 sub-spec 仍是原文 · 本表只指针）：

| 角色 | 维度 | 权威源 | L2 sub-spec | 实证 case |
|-----|------|-------|------------|----------|
| PMO | 格式 / frontmatter / schema | `templates/` | [pmo.md](../roles/pmo.md) | |
| Designer | 框架 / 配色 / layout / region | panorama `preview/overview.html` | 本文件 §四B 维度 6(框架基线唯一性)· 报告模板 [templates/ui.md](../templates/ui.md) | (PTR-F032) |

**新维度注册要求**（Architect / RD / QA 实战触发时按此模板加行 · 不再重复论证 meta）：
1. cite 实证 case · 写明 AI 走的捷径心智路径
2. 反模式黑名单 ≥3 条（具体措辞 / 心智路径 / 顺序倒置）
3. 下游校验工具或 grep 锚点（出口拦截 · R-SP-8 reader 兜底）
4. 在本表加一行 · 各 role L2 sub-spec 落详规则

---

## 四D、QA 代码审查视角

> 🔴 QA 代码审查的核心是**读代码验证 TC**(TDD 规范检查是辅助)。AC↔TC 的机械绑定由 `verify-ac.py` 物化校验;**逐条覆盖判断**归 review stage 的外审必覆盖方向「测试真实性与覆盖」(测试真跑 = 读实跑证据 · 覆盖真行为 · 边界回归)—— 不在本文件再列一份报告模板。

## 四点五、调试日志规范

🔴 **`[DEBUG-{Feature}-{NNNN}]` 唯一前缀规则**：临时调试日志（println / console.log / log.debug 等）必须用统一前缀，如 `console.log("[DEBUG-F062-0001] payload:", payload)` —— 格式即规则 · 不另给 ✅/❌ 对照。

🔴 **Ship 前清理硬规则**：Ship Stage Step 1 净化阶段必须 grep `\[DEBUG-` 确认零匹配；命中即报 ship.sanitize_log.suspicious_files 让用户决定（保留生产 / 删除 / 改正式 SLogger）。

🟢 **设计动机**：`[DEBUG-` 前缀比裸 `console.log` 易识别 + 不与正式 logger（SLogger / Log / logger）冲突 + 一次 grep 全清；Feature ID + 序号便于多 Feature 并行调试时区分来源。

---

## 五、文档流程图规范

🔴 所有文档中的流程图 / 时序图 / 架构图**统一用 Mermaid**(` ```mermaid ` 代码块)· **禁** ASCII 流程图 / 图片截图 / 第三方绘图工具链接 —— 必须能在 GitHub 与 Markdown 预览器直接渲染。图类型按需选(flowchart / sequenceDiagram / stateDiagram-v2),语法不在此复述。

## 六、临时产物目录(scratch)

Stage 执行期间的一切临时产物 —— 测试日志、构建输出(cargo target / 前端构建缓存等)—— **必须**落在统一 scratch 根下:

    ${TMPDIR:-/tmp}/teamwork/<feature_id>/<用途>

- `<feature_id>` 必须是 state.json 中的**完整 feature_id**(如 `SVC-CORE-F029`)· 🔴 **禁止**简称/别名/分支缩写(如 `bl031` —— 实证:即兴命名使 ship2 按 feature_id 回收全部落空 · 42GB 孤儿)。
- `<用途>` 自由命名(如 `review-r2-test.log` / `screenshots/` / `scaffold-tests/`〔脚手架测试 · 一次性验证脚本 · 交付即弃 —— 详 [HARD-RULES 规则 17](./HARD-RULES.md)〕)。⚠️ 但**构建产物 target 是特例**:见下方「构建 target 按 feature 共享」。
- 🔴 **禁止**在 scratch 根之外创建 teamwork 相关临时目录(如 `/tmp/<项目名>-*`)—— 根之外不在回收范围 · 会永久泄漏(实证 6GB)。
- 与 [conventions.md §12.5](../docs/conventions.md) 浏览器截图约定**同根**(`${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/` 是本约定的一个 `<用途>` 实例)。

🔴 **构建 target 按 feature 共享 · 不按 stage 切**(纠早期误判):**一个 feature 一个 target 目录**(`<feature_id>/target`)· 该 feature 的**串行** stage(goal→…→dev→review→test→ship 一次一个)全部复用同一份 —— dev 编好 test 直接热增量,不重编依赖树(实证:按 stage 切 = 每 stage 冷编整棵 deps · Rust 冷编 5-20min vs 热增量 <1min · 是 test 阶段耗时的主浪费)。

> ⚠️ 曾写「按 stage 隔离 target 是正确设计 · 防多 worktree 并行争抢文件锁」—— **推理错**:并行争抢发生在**不同 feature 的不同 worktree** 之间,而路径里的 `<feature_id>` 已隔开;同一 feature 内 stage 严格串行、从不并发构建,再按 stage 切只会打掉增量缓存。锁隔离只需到 `<feature_id>` 粒度。(极少数「单 stage 内派多个并行 cargo 构建」才需在该 stage 内临时 sub-split · 属例外不是默认。)

Rust 项目示例(target 按 feature 共享):

    CARGO_TARGET_DIR=${TMPDIR:-/tmp}/teamwork/SVC-CORE-F029/target cargo test --test '*'
    # 同 feature 的 dev / review / test 全用这一份 target · 增量复用

**回收三通道**(用户拍板:磁盘占用 > MR 窗口期增量缓存):① **ship1 push 成功即清**(主时点 · emit `scratch_cleanup` —— 测试/构建证据已入 state.json,scratch 无对账价值;窗口期撞 MR 冲突回炉需冷编 = 接受的代价)② `close-unmerged --abandon` 放弃即清;ship2 `tmp-cleanup` 转**幂等兜底**(ship1 漏清 / legacy in-flight)③ bootstrap TTL 兜底(默认 7 天 · 按**目录**整体删 —— cargo target 靠 fingerprint 判增量 · 按文件删会打碎一致性 · 捞历史孤儿)。why(实证):清理原只挂 ship2 —— worknode 上 session 常在 ship1 后结束/换机,ship2 不在本机跑,TTL 窗内 `/tmp/teamwork` 打到 141GB(单 feature 78GB)。

> 背景:CI 机磁盘 100% 打满实证 —— `/tmp/teamwork` 48GB 全是可无损重建的 cargo target(单 feature 26GB · 躺了数月)· 「有人写没人收」的无主命名空间。同类先例 = external-review-logs 无保留策略膨胀 300MB(v8.x 已治)· 本节是同一模式在 160 倍量级上的复用。

---

## 七、前端专项(阈值与禁令 · 仅前端子项目适用)

> 组件测试写法 / 状态管理选型 / 性能手法 / 无障碍细则 / 构建实践 = 模型自带知识 · 不入库(防教程腐烂反向误导);项目特异约定归 `DEV-RULES.md` / `UI-RULES.md`(用户主权)。本节只留**模型猜不到的项目缺省**。

### 测试阈值(项目缺省 · DEV-RULES 可覆盖)

- **覆盖率 > 70%**(CI 门禁值)· P0 流程必须覆盖。
- **测试分层归属**(框架约定 · 怎么写 AI 自觉):单元(纯函数/hook)· 组件(渲染+交互+状态)· 集成(跨组件/路由/数据流)· e2e(真实浏览器 · 归 browser_e2e stage)。

### 样式禁令(跨 Feature 一致性 · 单人判断守不住的)

- 🔴 **项目内统一 CSS 方案 · 禁混用**(CSS Modules / Tailwind / CSS-in-JS / Sass+BEM 选其一)—— 单 Feature 各选各的 = 样式体系碎裂,没有哪个 Feature 单独负责。
- 🔴 **组件引用 design token · 禁硬编码颜色值 / 魔法数字**;暗色模式在 token 层切换(组件层不感知主题)· token 定期与设计稿对账。
- 🔴 **全局样式仅限 reset / base / typography** · 禁在全局样式中定义业务组件样式。
