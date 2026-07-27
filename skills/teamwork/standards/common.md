# 通用开发规范

> 前后端共用的规范，所有 RD 必须遵守。
> 📎 后端专项规范见 [backend.md](./backend.md)，前端专项规范见 [frontend.md](./frontend.md)

---

## 一、测试核心原则

> v8.287:TDD 手段规定已撤除(怎么测 AI 自觉)· 测试的**结果规则 + 机器门**见 [HARD-RULES.md](./HARD-RULES.md) · 本节不复述通用原则。

## 二、代码架构规范(v8.284 压缩 · 分层/SOLID/Review 友好度等教科书内容已删)

> 通用架构原则(分层、单一职责、模块边界、Review 友好度)模型已内建 —— 本节只留**本框架的偏离与约定**:

- **架构文档维护**:架构决策(有备选 + 后果)→ `docs/adr/`;子项目拓扑/依赖方向 → `ARCHITECTURE.md`。**代码是唯一真相**,文档是它的索引,不是它的替身。
- **项目特例走 `DEV-RULES.md`**(人维护)· 本文件只装跨项目缺省。

## 三、测试脚本约定

> RD 在开发阶段负责创建/维护测试脚本。规范只约定脚本接口（名称 + 行为），不约定实现细节（Docker/K8s/本地均可）。
> PMO 和 Test Stage 通过脚本与测试环境交互，不直接执行 docker-compose 等底层命令。

### 两层脚本结构（Monorepo）

```
monorepo/ # 仓库根目录
├── scripts/ # 根级：全局环境（跨子项目共享）
│ ├── test-env-setup.sh # 启动全部依赖服务（DB/Redis/MQ + 各子项目服务）
│ ├── test-env-check.sh # 全局连通性检查
│ └── test-env-teardown.sh # 全局清理（可选）
│
├── packages/
│ ├── api/
│ │ └── scripts/ # 子项目级：只管自己的测试执行
│ │ ├── test-unit.sh # 子项目单元测试
│ │ ├── test-integration.sh # 子项目集成测试（假定全局环境已就绪）
│ │ └── test-api-e2e.sh # 子项目 API E2E
│ ├── web/
│ │ └── scripts/
│ │ ├── test-unit.sh
│ │ └── test-browser-e2e.sh # Browser E2E（可选）
│ └── shared/
│ └── scripts/
│ └── test-unit.sh

分层原则：
├── 根级脚本（scripts/）→ 环境启停，跨子项目共享
│ ├── 启动全部基础设施（DB/Redis/MQ/对象存储 等）
│ ├── 启动各子项目服务（按依赖顺序）
│ └── 加载全局前置数据
├── 子项目脚本（packages/{name}/scripts/）→ 测试执行，只管自己
│ ├── 假定全局环境已就绪，不负责启动环境
│ └── 只运行本子项目的测试
└── PMO 调用顺序：根级 setup → 子项目 test-*
```

### 脚本接口规范

```
🔴 所有脚本必须满足：
├── 退出码：0 = 成功，非 0 = 失败
├── 幂等：重复执行不出错
├── 无交互：不能 read stdin / 弹确认框（自动化脚本场景无 TTY）
└── stdout/stderr：失败时输出足够的诊断信息

【根级脚本】

scripts/test-env-setup.sh（全局环境准备）：
├── 职责：启动全部依赖服务 + 各子项目服务、加载前置数据、等待健康检查
├── 成功时 stdout 最后一行输出 JSON：
│ {"db_url": "...", "redis_url": "...", "services": {"api": "http://localhost:8080", "web": "http://localhost:3000"}}
├── 可选参数：--skip-if-running（已在运行则跳过，加速重复调用）
└── 实现自由：Docker Compose、本地进程、远程环境均可

scripts/test-env-check.sh（全局连通性检查）：
├── 职责：验证全局环境仍然可用（DB/Redis/各服务端口 可达）
├── 轻量快速：只做 ping/连接测试，不启动服务
├── 成功时 stdout 输出检查结果
└── 用途：Test Stage 内部复核（环境检查与实际跑测试之间留容错窗口）

scripts/test-env-teardown.sh（全局清理，可选）：
├── 职责：停止所有服务、清理测试数据
└── 默认保留环境供后续测试复用

【子项目脚本】

{subproject}/scripts/test-unit.sh（子项目单元测试）：
├── 职责：运行本子项目全量单元测试
├── 底层命令由项目决定（cargo test --lib / npm test / pytest 等）
└── 🔴 不依赖全局环境——纯代码级测试

{subproject}/scripts/test-integration.sh（子项目集成测试）：
├── 职责：运行本子项目集成测试（假定全局环境已就绪）
├── 🔴 不负责启动环境——必须先由根级 test-env-setup.sh 完成
└── 输出测试结果 + 覆盖报告到 stdout

{subproject}/scripts/test-api-e2e.sh（子项目 API E2E）：
├── 职责：逐场景验证本子项目 API 链路（假定全局环境已就绪）
├── 参数：可选传入 TC.md 路径以读取 API E2E Scenarios
└── 输出完整 request/response 到 stdout

{subproject}/scripts/test-browser-e2e.sh（Browser E2E，可选）：
├── 职责：浏览器自动化测试
├── 内部处理 playwright/puppeteer 安装检测
└── 输出截图/录屏路径 + 测试结果
```

### RD 创建时机

```
RD 在 TDD 开发阶段创建测试脚本：

根级脚本（首次创建后持续维护，新增子项目依赖时更新）：
├── scripts/test-env-setup.sh ← 首次有集成测试需求时创建
├── scripts/test-env-check.sh ← 与 test-env-setup.sh 同步创建
└── scripts/test-env-teardown.sh ← 可选

子项目脚本（每个子项目按需创建）：
├── test-unit.sh ← 编写单元测试时同步创建
├── test-integration.sh ← 编写集成测试时创建
├── test-api-e2e.sh ← QA 在 TC.md 定义 API E2E 场景后创建
└── test-browser-e2e.sh ← QA 在 TC.md 定义 Browser E2E 场景后创建（如需）

🔴 Dev Stage 自查检查项：测试脚本是否存在且可执行
 RD 自查 → 确认根级 + 子项目脚本存在 + 至少本地跑通一次
 架构师 CR → 确认脚本接口符合约定（退出码/幂等/无交互）
```

### PMO 预检(v8 物化路径)

📎 v7 三级 Subagent dispatch 预检流程(L1/L2/L3)在 v8 已废 · 由以下物化路径替代:
- **Feature ID 冲突** → `state.py prepare-check --feature-id-prefix <PROJ>`(自动返回 next_available_id)
- **测试环境检查** → 各项目自维护 `scripts/test-env-{setup,check}.sh`(本节 §三 接口规范);PMO/RD 按 stage brief 触发
- **stage 入口校验** → `state.py xxx-start` 物化拦截(missing prerequisites + hint)
- **保护标记 / 仓库约束** → 项目根 CLAUDE.md/AGENTS.md(host injection 自动注入)

v8 角色协作走主对话身份切换(不 dispatch Subagent)· 预检由 state.py 命令物化 · 不再依赖 PMO 凭记忆按 L1/L2/L3 顺序跑。

---

## 四、实现完成的硬门(v8.284 · 原「RD 自查规范 + 报告模板」216 行已删)

> 删除理由:那是**环节化自检 + 报告仪式**,零机器消费者(全库无工具校验 RD 自查报告)、零文档引用,且与 `templates/tech.md §完工自查`(review 真读它)职能重复。**证据要求本身由机器门承担**:`dev-complete --test-exit-code 0` + `--test-stdout` 非空 + artifacts 在 changeset。以下两条是从中抢救的真规则:

- 🔴 **Build 必须跑通才能进 Code Review**(硬门禁)。CI 是最后一道安全网,不是第一道发现机制。无 build 步骤的项目(纯库 / 纯脚本 / Python 应用)必须**显式标注「无 build 步骤」**,不能省略。
- 🟡 **worktree lazy-install 踩坑**:单测能跑但 `npm run build` / `next build` 失败(找不到 webpack / postcss / next 本身)= worktree 只装了单测所需 deps,build 工具链未装。处理:① worktree 内补装(`npm install --include=dev`,最稳,30s-2min)② 软链主 worktree 的 `node_modules`(秒级,但 monorepo workspace / 不同 lockfile 易出怪问题)③ 记进项目 `KNOWLEDGE.md` Gotcha。

## 四B、Designer 自查规范

> Designer 完成 UI 设计后、用户确认设计稿前，必须完成自查并输出自查报告写入 UI.md。
>
> 物化拦截：[tools/verify-panorama.py](../tools/verify-panorama.py) 校验自查报告完整性 + sitemap.md mtime + preview/ 数量 · UI Design Stage 出口前置。

### 自查触发时机

```
Designer 完成设计（UI.md + preview/*.html 草稿）
 ↓
执行自查清单（5 维度 · 见下）
 ↓
输出 Designer 自查报告（写入 UI.md 末尾）
 ↓
verify-panorama.py 物化校验 → 全 ✅ 才进 ⏸️ 用户确认设计稿
```

### 自查清单详解（5 维度）

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

### Designer 自查报告模板

UI.md 末尾必含本段（verify-panorama.py grep 校验）：

```markdown
## Designer 自查报告（🔴 出口必填 · verify-panorama.py 校验）

### 检查结果汇总
| 维度 | 检查项 | 通过 | 备注 |
|------|------|----|----|
| 1. 全景对齐 | 4 | ?/4 | panorama_path = ... · 宿主 = {当前/跨子项目→XX} |
| 2. 状态覆盖 | 4×N页 | ?/? | N 个页面 · 每页 4 态 |
| 3. PRD AC 覆盖 | M | ?/M | M 条 AC · 详 UI-AC-COVERAGE 表 |
| 4. 全景增量同步 | 4 | ?/4 | 类型：⏭️ 无变更 / 🟡 增量 / 🔴 结构性 |
| 5. 结构性变更红线 | 3 | ?/3 | 任一命中即停 Stage |

### 全景对齐证据
- panorama_path: {绝对路径}
- 全景宿主：{当前子项目 / 跨子项目→{hosting_subproject}}
- 风格对照：{摘录 panorama/sitemap.md 已有规范 + 本 Feature 遵守说明 ≥3 条}
- 导航位置：{本 Feature 页面在 sitemap 中的层级路径}
- 全景变更类型：⏭️ 无 / 🟡 增量（diff 见下）/ 🔴 结构性（不应继续）

### 全景增量 diff（仅 🟡 增量类型必填）
```diff
sitemap.md 变更：
+ 新增页面 X（位置：根 → A → X）
~ 修改页面 Y（导航文案变更：旧→新）
- （禁止删除条目）

overview.html DOM 变更：
+ 新增 <section data-page="X"> 节点（位置：第 N 个 section 之后）
~ 修改 <nav> 中页面 Y 的链接文案
```

### 自查结论
✅ 自查通过 · 可进入 ⏸️ 用户确认设计稿
⚠️ N 项未通过 · 已修复 · 重跑自查
🔴 结构性变更触发停 Stage · 建议走 Feature Planning
```

### 自查结果处理

```
自查结果：
├── 全 ✅ → ⏸️ 用户确认设计稿
├── 有 ⚠️ 低风险（如 1 个 AC 未覆盖且已补）→ 修复后重新自查
├── 🔴 结构性变更红线命中 → 停 Stage → DONE_WITH_CONCERNS
└── verify-panorama.py 校验 FAIL → 按 stderr hint 补完自查报告 → 重跑
```

---

## 四C、权威源单源规则（跨角色汇总指针）

> **本节定位**：跨角色 meta-rule · 不复述各 role L2 sub-spec 原文 · 只列表汇总 + 后续注册模板.

**核心原则**：每个产物维度有唯一**权威源**（spec / template / panorama / KNOWLEDGE 等）· peer Feature 仅可作**内容参考**（写法、套路、决策历史）· ❌ 禁止当**格式 / 框架 / schema** 基线.

**优先级**：teamwork 规范权威源 > peer Feature 历史. 触发"参考最近相似 Feature"心智路径时 · 默认走错 · 必须改走权威源.

**已注册维度**（各 L2 sub-spec 仍是原文 · 本表只指针）：

| 角色 | 维度 | 权威源 | L2 sub-spec | 实证 case |
|-----|------|-------|------------|----------|
| PMO | 格式 / frontmatter / schema | `templates/` | [pmo.md § 格式权威守门](../roles/pmo.md) | |
| Designer | 框架 / 配色 / layout / region | panorama `preview/overview.html` | [designer.md § 6 维自查](../roles/designer.md) · [ui-design-stage.md § 框架基线唯一性](../stages/ui-design-stage.md) | (PTR-F032) |

**新维度注册要求**（Architect / RD / QA 实战触发时按此模板加行 · 不再重复论证 meta）：
1. cite 实证 case · 写明 AI 走的捷径心智路径
2. 反模式黑名单 ≥3 条（具体措辞 / 心智路径 / 顺序倒置）
3. 下游校验工具或 grep 锚点（出口拦截 · R-SP-8 reader 兜底）
4. 在本表加一行 · 各 role L2 sub-spec 落详规则

---

## 四D、QA 代码审查视角(v8.284 压缩 · 原 70 行报告模板已删)

> 🔴 QA 代码审查的核心是**读代码验证 TC**(TDD 规范检查是辅助)。AC↔TC 的机械绑定由 `verify-ac.py` 物化校验;**逐条覆盖判断**归 review stage 的外审必覆盖方向「测试真实性与覆盖」(测试真跑 = 读实跑证据 · 覆盖真行为 · 边界回归)—— 不在本文件再列一份报告模板。

## 四点五、调试日志规范（借鉴 mattpocock/skills diagnose）

🔴 **`[DEBUG-{Feature}-{NNNN}]` 唯一前缀规则**：临时调试日志（println / console.log / log.debug 等）必须用统一前缀 `[DEBUG-{Feature}-{NNNN}]`，方便 ship 前一次性 grep 清理。

```
✅ 正确：
console.log("[DEBUG-F062-0001] payload before validation:", payload);
log.debug("[DEBUG-F062-0002] cache hit ratio:", ratio);

❌ 错误：
console.log("xxx", payload); // 无前缀 · ship 前难定位
console.log("debug:", payload); // 通用 debug 字面值 · 与既有日志冲突
```

🔴 **Ship 前清理硬规则**：Ship Stage Step 1 净化阶段必须 grep `\[DEBUG-` 确认零匹配；命中即报 ship.sanitize_log.suspicious_files 让用户决定（保留生产 / 删除 / 改正式 SLogger）。

🟢 **设计动机**：`[DEBUG-` 前缀比裸 `console.log` 易识别 + 不与正式 logger（SLogger / Log / logger）冲突 + 一次 grep 全清。Feature ID + 序号便于多 Feature 并行调试时区分来源。

---

## 五、文档流程图规范(v8.284 压缩)

🔴 所有文档中的流程图 / 时序图 / 架构图**统一用 Mermaid**(` ```mermaid ` 代码块)· **禁** ASCII 流程图 / 图片截图 / 第三方绘图工具链接 —— 必须能在 GitHub 与 Markdown 预览器直接渲染。图类型按需选(flowchart / sequenceDiagram / stateDiagram-v2),语法不在此复述。

## 六、临时产物目录(scratch · v8.247)

Stage 执行期间的一切临时产物 —— 测试日志、构建输出(cargo target / 前端构建缓存等)—— **必须**落在统一 scratch 根下:

    ${TMPDIR:-/tmp}/teamwork/<feature_id>/<用途>

- `<feature_id>` 必须是 state.json 中的**完整 feature_id**(如 `SVC-CORE-F029`)· 🔴 **禁止**简称/别名/分支缩写(如 `bl031` —— 实证:即兴命名使 ship2 按 feature_id 回收全部落空 · 42GB 孤儿)。
- `<用途>` 自由命名(如 `review-r2-test.log` / `screenshots/`)。⚠️ 但**构建产物 target 是特例**:见下方「构建 target 按 feature 共享」。
- 🔴 **禁止**在 scratch 根之外创建 teamwork 相关临时目录(如 `/tmp/<项目名>-*`)—— 根之外不在回收范围 · 会永久泄漏(实证 6GB)。
- 与 [conventions.md §12.5](../docs/conventions.md) 浏览器截图约定**同根**(`${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/` 是本约定的一个 `<用途>` 实例)。

🔴 **构建 target 按 feature 共享 · 不按 stage 切**(v8.249 纠 v8.247):**一个 feature 一个 target 目录**(`<feature_id>/target`)· 该 feature 的**串行** stage(goal→…→dev→review→test→ship 一次一个)全部复用同一份 —— dev 编好 test 直接热增量,不重编依赖树(实证:按 stage 切 = 每 stage 冷编整棵 deps · Rust 冷编 5-20min vs 热增量 <1min · 是 test 阶段耗时的主浪费)。

> ⚠️ v8.247 曾写「按 stage 隔离 target 是正确设计 · 防多 worktree 并行争抢文件锁」—— **推理错**:并行争抢发生在**不同 feature 的不同 worktree** 之间,而路径里的 `<feature_id>` 已隔开;同一 feature 内 stage 严格串行、从不并发构建,再按 stage 切只会打掉增量缓存。锁隔离只需到 `<feature_id>` 粒度。(极少数「单 stage 内派多个并行 cargo 构建」才需在该 stage 内临时 sub-split · 属例外不是默认。)

Rust 项目示例(target 按 feature 共享):

    CARGO_TARGET_DIR=${TMPDIR:-/tmp}/teamwork/SVC-CORE-F029/target cargo test --test '*'
    # 同 feature 的 dev / review / test 全用这一份 target · 增量复用

**回收双通道**:ship2 `tmp-cleanup` 即时清理(verify-delivered 通过后整树删 · 内容已上岸零风险)+ bootstrap TTL 兜底(默认 7 天 · 按**目录**整体删 —— cargo target 靠 fingerprint 判增量 · 按文件删会打碎一致性 · 捞回放弃的 feature 与历史孤儿)。

> 背景:CI 机磁盘 100% 打满实证 —— `/tmp/teamwork` 48GB 全是可无损重建的 cargo target(单 feature 26GB · 躺了数月)· 「有人写没人收」的无主命名空间。同类先例 = external-review-logs 无保留策略膨胀 300MB(v8.x 已治)· 本节是同一模式在 160 倍量级上的复用。
