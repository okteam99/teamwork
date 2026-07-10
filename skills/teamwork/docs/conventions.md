# 项目级约定

> 编号 ID + worktree 路径 的规范单源。
> 各 stage spec / state.py / templates / SKILL.md § Triage 入口规范 一律 cite 本文件。

> **目录**:§1-8 命名(ID 体系)· §9-12 路径(worktree)· §13 文档布局

---

# 命名(ID 体系)

---

## 1. 流程 artifact ID(Feature / Bug / Micro / 敏捷需求)

进状态机的顶层 artifact —— 每个有独立目录 + `state.json`。**按 flow_type 分字母**:

```
格式: {项目缩写}-{字母}{号段}-{Kebab-Case-名称}
号段两种策略(per-project · .teamwork_localconfig.json → id_strategy):
  ① utc-yymmddhhmmss(默认)= UTC0 秒级时间戳 YYMMDDHHMMSS(12 位定宽 · 跨机防撞号)
  ② sequential(opt-out)         = 顺序号 NNN(3 位 · 单 clone 项目 · 好念短序号)
示例: SVC-PLATFORM-F260601143012-Offer-Ranking   (Feature · utc 默认)
      PTR-F033-Credit-Note-Adjustment            (Feature · sequential opt-out)
      PTR-B019-UserMenu-Logout-Dropdown          (Bug · sequential)
      PTR-M003-Footer-Copyright-Year             (Micro · sequential)
```

| flow_type | 字母 | namespace | 说明 |
|---|---|---|---|
| Feature | `F` | 项目独立 | 完整 Feature |
| 敏捷需求 | `F` | 项目独立 | Feature 变体 · **与 Feature 共用同一条 F 序列** |
| Bug | `B` | 项目独立 | 标准 Bug 流程(独立修复请求 · ≠ Feature 内 bug · 见 §2) |
| Micro | `M` | 项目独立 | 微改(改文案 / 改配置) |

- **项目缩写**:来自 `teamwork-space.md` § 子项目清单「缩写」列(任何 teamwork 项目都有 teamwork-space.md · N≥1 统一模型 · 单项目 = 清单里 1 行 · 详 §7)
- **{号段}**:默认 **UTC 秒级时间戳**(`YYMMDDHHMMSS` · 12 位定宽 · 字典序=时间序 · 跨机/多 agent 并行各自生成、免中心协调 → 根治分布式 `max+1` 撞号);项目可 `id_strategy: sequential` opt-out 回 **3 位顺序号**(`各项目 × 各字母独立递增` · `PTR-F` 与 `PTR-B` 各一条序列)。两策略均**不跨项目共享**(`PTR-F033` 与 `SVC-PLATFORM-F033` 可并存)· **存量 ID 不重编号**(新旧天然可区分:3-4 位 vs 12 位)。
- **撞号硬校验**(R0):`init-feature` 若目标 `{PREFIX}-{字母}{号段}` 已被**另一**目录占用 → FAIL(同 clone race 兜底 · 任一策略生效);跨 clone 不可见的撞号靠 utc 时间戳策略根治。
- **名称**:多词用 `-` 拼接 · 不超过 6 词
- **目录**:`{docs_root}/features/{artifact ID}/`(完整 ID · 不省略名称 · 4 类 flow 同放 `features/` 下)
- **下一编号**:`state.py prepare-check --feature-id-prefix <PREFIX> --flow-type <type>` 按 `id_strategy` 推荐 `next_available_id_stem` —— **不手填**(utc 策略:已生成秒级号勿手算 · 重跑得新号 · 漏传 `--flow-type` 会退回字母 F)

state.py 校验:basename(--feature) 必须包含 --feature-id(防 slug 错位)。

## 2. bug 报告文件 ID(Feature/Bug 流程内的 bugfix/ 文件)

⚠️ **与 §1 区分**:这是开发过程中**落的 bug 报告文档名** · 不是进状态机的顶层 artifact。
独立的修复请求 = §1 标准 Bug 流程 `{PREFIX}-B{NNN}`;本节是某 artifact 的 `bugfix/` 子目录下的报告文件。

```
格式: BUG-{项目缩写}-{F|B}{NNN}-{seq}
示例: BUG-PTR-F033-001     (Feature PTR-F033 开发中发现的 bug)
      BUG-PTR-B019-001     (标准 Bug 流程 PTR-B019 的排查报告)
```

- **{F|B}{NNN}**:宿主 artifact 的编号(Feature 内 bug 用其 F 号 · 标准 Bug 流程用其 B 号)
- **seq**:三位数字 · **单宿主 artifact 内独立递增**
- **位置**:`{artifact 目录}/bugfix/BUG-....md`

## 3. ADR ID

```
格式: ADR-{NNNN}
示例: ADR-0001
```

- **NNNN**:四位数字 · **全局递增 · 不区分项目**(架构决策跨项目可见 / 单源)
- **位置(唯一落点)**:`{子项目}/docs/adr/ADR-NNNN-{topic}.md`(单项目仓库 = 仓库根 `docs/adr/`)· 🔴 ADR **只落子项目 `docs/adr/`** · 不落 Feature 目录(无 `{Feature}/adrs/`)
- **superseded 时双向链接**:原 ADR.status=superseded-by-NNNN + 新 ADR.supersedes=NNNN
- 详见 [templates/adr-index.md](../templates/adr-index.md)

## 4. 执行线 → WS → BL → F 映射(规划 → 执行)

```
执行线:   业务架构里的 taxonomy(不编号 · WS 向上 tag「承接 1+ 执行线」)
规划单元: WS-{NN}(product-overview/workstream/ · 一块规划 → 拆一组 feature)
规划期:   BL-{NNN}(Roadmap Backlog · planning 时分配 · 关联回 WS-NN)
执行期:   F-{NNN}(进入 Feature 流程后由 PMO 在 init-feature 时分配)
映射:     各自独立递增 · ROADMAP「关联 WS」列 + 「对应 F编号」列建链接
```

- **WS-NN**:两位数字 · 各项目独立递增 · 一个 WS 拆出一组 BL(写进各子项目 ROADMAP)· 完成 = 这组 feature 全写入 roadmap
- **BL-NNN**:三位数字 · **各项目独立递增**(同 F-NNN)· ROADMAP「关联 WS」列回指 WS-NN(反查"某 WS / 执行线下有哪些 feature")
- **BL → F 升级时机**:用户拍板某 Backlog 启动 Feature 流程时,PMO 分配下一个 F-NNN(各项目当时 sequence 的下一个)+ 同步回填 ROADMAP「对应 F编号」列
- **不强制同号**:BL-007 启动 Feature 时分配的 F 编号是 F 序列当时的下一位 · 与 BL 数字无关

## 5. Dispatch 文件 ID

```
格式: {NNN}-{subagent-id}.md
示例: 001-rd-developer.md
      002-arch-cr.md
      003-qa-cr.md
```

- **NNN**:三位数字 · **单 Feature 的 dispatch_log/ 目录内独立递增**
- **subagent-id**:来自 stages/*.md § 角色任务规范 中的标签
- 由 state.py 各 stage-start 自动生成 · PMO 不手填

## 6. KNOWLEDGE 子 ID

| 类 | 格式 | 范围 |
|---|---|---|
| Gotcha | `GO-NNN` | 项目内独立递增 |
| Convention | `CV-NNN` | 项目内独立递增 |
| Preference | `PR-NNN` | 项目内独立递增 |
| Out of Scope | `OS-NNN` | 项目内独立递增 |
| Flagged Ambiguity | `FA-NNN` | 项目内独立递增 |
| Glossary 术语 | 术语本身作 anchor · 不编号 | — |

详见 [templates/knowledge.md](../templates/knowledge.md)。

## 7. 项目缩写注册

新项目缩写必须在 `teamwork-space.md` § 子项目清单注册一次(注册单源 · 单项目也是 N=1 的一行 · teamwork-space.md 由 bootstrap 自动建骨架 · 详 [teamwork-space-guide.md](./teamwork-space-guide.md))。规则:
- **2-12 字符 · 全大写 · ASCII**(易读 · 文件名安全)
- **简单项目**:单字 e.g. `WEB` / `API` / `PAY` / `PTR`(Partner)
- **复合项目**:`-` 分组 e.g. `SVC-PLATFORM` / `OFFER-HOST`
- **避免与已注册项目缩写冲突**(workspace 内全局 unique)

实际已用缩写参考(从 git 历史抽样):`PTR`(Partner)/ `INFRA` / `SVC-PLATFORM` / `WEB` / `ADMIN` / `API` / `PAY`。

---

## 8. namespace 总结

| ID | namespace | 说明 |
|---|---|---|
| F-NNN | **项目独立** | Feature + 敏捷需求 共用 · PTR-F033 与 SVC-PLATFORM-F033 可并存 |
| B-NNN | **项目独立** | 标准 Bug 流程 · 与 F 序列独立(PTR-B 自成一列) |
| M-NNN | **项目独立** | Micro 流程 · 与 F / B 序列独立 |
| BL-NNN | **项目独立** | 同 F-NNN · feature 原子(规划期)· 关联回 WS-NN |
| WS-NN | **项目独立** | Workstream(规划单元 · `product-overview/workstream/`)· 拆一组 feature · 承接 1+ 执行线 |
| BUG-...-NNN | **宿主 artifact 内独立** | seq 在单 artifact(Feature / Bug)范围递增 |
| ADR-NNNN | **全局** | 架构决策跨项目可见 |
| Dispatch NNN | **Feature 内独立** | dispatch_log/ 内递增 |
| GO/CV/PR/OS/FA-NNN | **项目独立** | KNOWLEDGE.md 内递增 |

---

# 路径(worktree)

## 9. worktree 路径模板

```
完整路径 = {worktree_root_path}/{Feature-ID}
示例: .worktree/PTR-F033-Credit-Note-Adjustment
```

- **worktree_root_path**:可配置 · 默认 `.worktree`(项目根目录下)
- **Feature-ID**:见 §1(完整 ID · 不省略名称)
- **配置位置**:项目级 `.teamwork_localconfig.json` 中的 `worktree_root_path` 字段

## 10. worktree_root_path 配置

```yaml
# .teamwork_localconfig.json
worktree: auto                      # off / auto / manual · 默认 auto
worktree_root_path: .worktree       # 默认 · 项目根下子目录
```

**解析优先级**(从高到低):
1. `state.json.environment_config.worktree_root_path`(Feature 创建时锁定)
2. 项目根 `.teamwork_localconfig.json` 的 `worktree_root_path` 字段
3. 默认值 `.worktree`

**常见配置**:

| 配置 | 实际路径 | 适用场景 |
|---|---|---|
| `.worktree`(默认) | `<repo-root>/.worktree/PTR-F033` | 项目内 · bootstrap.py session 启动时自动加 .gitignore |
| `../.{repo_name}-worktrees` | `<repo-root>/../.aon-ptr-worktrees/PTR-F033` | 父目录分组 · 隔离主仓库 .git 索引 |
| `/tmp/worktrees`(绝对) | `/tmp/worktrees/PTR-F033` | 完全外置(CI / 临时) |

**约束**:
- 根目录不能是已 commit 的 git 工作目录(除 .gitignore 包含的目录如 .worktree)
- 父目录必须存在或可创建
- 项目内自定义路径需用户自加 .gitignore(避免 git 嵌套混乱)
- 项目外路径无需 gitignore

## 11. state.py 校验(物化拦截)

- `worktree_mode != off` 且 cwd 不在 `--worktree-path` 内 → FAIL
- `worktree_mode != off` 且 worktree 物理不存在 → FAIL

## 12. 与状态机的接口

triage 入口完成 → state.py init-feature 接管:

```bash
# triage 阶段(PMO 主对话 · SKILL.md § Triage 入口规范 §4.4):
git worktree add -b feature/PTR-F033 <worktree-path> origin/staging
cd <worktree-path>

# 状态机(在 worktree cwd 内):
state.py init-feature \
  --worktree-mode auto \
  --worktree-path <worktree-path> \
  ...
# 物化校验:cwd 必须在 worktree-path 内
```

完成 Feature 后清理(在主工作区跑 · 不在 worktree 跑):
```bash
cd <主工作区>  # ⚠️ 必须先 cd 出 worktree(物化拦截 · 详 ship-stage.md §坑 1)
git worktree remove <worktree-path>
git branch -d <branch>
```

## 12.5 浏览器验证截图(transient)

🔴 **「看一眼」的浏览器截图 → 系统临时目录 · 绝不落 worktree / 主工作区根**。

各 stage 常需 browse 预览/页面**截图自检渲染**(ui_design 预览验证 · dev/review/pm 顺手核对 UI)。这类截图是**一次性验证产物**(AI 自己看 · 非交付 · 不 commit)· **必须写到系统临时目录** · 否则会散落污染主工作区根目录。

- **统一位置**:`${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/`(按 feature 命名 · session 内可复寻 · 系统自动回收)。
  ```bash
  SHOT_DIR="${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots"; mkdir -p "$SHOT_DIR"
  # 浏览器截图存 "$SHOT_DIR/<name>.png" · 再按绝对路径 Read 查看
  ```
- **零工作区脚印**:在系统 temp · 不需 gitignore · 不进任何 commit · 不污染并行 Feature 基线(worktree 红线)。
- **🔴 playwright MCP 兼容**:playwright MCP 的 allowed-root 只能写 `<主仓根>/.playwright-mcp/`,**写不了上面的 temp 目录**。用 MCP 截图时 → **`.playwright-mcp/` 即可接受的自检截图目录**(同属一次性非交付)· 🔴 项目根 `.gitignore` 加 `.playwright-mcp/`(ship2 不必手动清)· 别跟 MCP 沙箱较劲。非 MCP 的 browse 仍优先上面的 temp 目录。
- **⚠️ 与 browser_e2e 证据区分**:`browser_e2e` stage 的**证据截图**是交付物 · 仍落 **`<feature_dir>/screenshots/*.png`**(committed · pm_acceptance 复核 · 详 browser-e2e-stage.md SOP)· **不**走临时目录。临时目录只放「自检看一眼」的非证据截图。

---

# 文档布局

## 13. 项目文档目录

teamwork 文档分 **workspace 级**(仓库根)和 **子项目级**两层。

### Workspace 级(仓库根)

| 目录 / 文件 | 内容 | 维护方 |
|---|---|---|
| `product-overview/` | 产品愿景 / 业务架构 / 执行线列表 + `workstream/`(WS)+ `PENDING.md`(待规划需求池 · 从 teamwork-space 外置 · 详 [PRODUCT-OVERVIEW-INTEGRATION.md](../PRODUCT-OVERVIEW-INTEGRATION.md)) | Product Lead |
| `project-specs/` | 工程层项目文档:`DEV-RULES.md`(人维护开发规范 · blueprint/dev 必读)· `UI-RULES.md`(人维护设计规范:控件/色板策略/交互约定 · 装策略不装视觉值)· `KNOWLEDGE.md`(AI 沉淀踩坑/事实)· `GLOSSARY.md` · `TROUBLESHOOTING.md` · `ARCHITECTURE.md`(workspace 级系统架构:子项目拓扑+依赖+目录 · 从 teamwork-space.md 外迁 · 区别 `{子项目}/docs/architecture/` 单子项目内部)· `PROCESS-LEDGER.md`(流程价值台账 · ship2 planning-backref 随收尾 MR append · 年检数据源 · 详 ship-stage §16) | bootstrap 建空骨架 · 项目维护 |
| `teamwork-space.md` | 知识地图根 / 路由(N≥1 统一模型 · **单项目也有** · bootstrap 自动建骨架 · 详 [teamwork-space-guide.md](./teamwork-space-guide.md)) | PM |
| `CLAUDE.md` / `AGENTS.md` | host 指令入口 · 固定位置 · 不可移 | teamwork 注入 |
| `.teamwork-local-env/` | 🔐 本机敏感配置:`config.properties`(KEY=value:DB 密码 / API key)+ 整文件(kubeconfig / 证书)· **双重 gitignore · 绝不进仓库**。bootstrap 缺失时自动建(`local_env_auto_create` 默认 true)· 已存在不覆盖。读取约定见 `TROUBLESHOOTING.md §五`。 | 用户(secret 真值)/ bootstrap(骨架) |

🔴 **`project-specs/` 与 `product-overview/` 同级** —— 产品视角 ↔ 工程视角成对。workspace 级工程文档**一律进 `project-specs/`** · 不散在仓库根。
🔴 **`.teamwork-local-env/` ≠ `.teamwork_localconfig.json`**:前者是**你的** secret(kubeconfig/密码/key · gitignored)· 后者是 **teamwork 自己**的配置(worktree/scope/id_strategy 等 · 可提交)。

### 子项目级(`{子项目}/docs/`)

`PROJECT.md`(业务总览)· `ROADMAP.md`(Feature 清单 + 优先级)· `DEV-RULES.md`(子项目级开发规范 · 人维护)· `UI-RULES.md`(子项目级设计规范 · 人维护)· `KNOWLEDGE.md`(子项目级 Gotcha)· `design/sitemap.md`(IA 地图:页面层级/导航/路由 · 🔴 只写地图不写视觉 · 🔴 **在 `design/` 下与全景同目录 · 非 `docs/` 根**)· `architecture/` · `adr/` · `features/{artifact ID}/`(详 §1)· `design/`(same-stack panorama:`preview-project/` 同栈设计预览项目 · 源即全景权威 + `preview.sh` 起 dev server 实时预览〔动态端口〕· `node_modules` gitignore · 不出静态 build 产物 · 🔴 **首次 seed 在规划层「UI 全景初步规划」**〔feature-planning Step 5 · 拆 WS 前〕· ui_design 阶段增量扩本 Feature 页)。

🔴 **顶级仓库不设 teamwork `docs/`** —— `docs/` 只在子项目层。单项目仓库 = 仓库根即项目根 · `project-specs/` 与 `docs/` 都在仓库根。

### KNOWLEDGE.md / DEV-RULES.md 两层

> 🔴 **分家**:KNOWLEDGE = AI 沉淀(踩坑/事实/偏好);DEV-RULES = 人维护(开发规范);**UI-RULES = 人维护(设计规范:控件/色板策略/交互约定 · 装策略不装视觉值)**。各自 workspace + 子项目两层。

| 层 | 路径 | 内容 |
|---|---|---|
| workspace | `project-specs/KNOWLEDGE.md` · `project-specs/DEV-RULES.md` | 跨子项目/仓库级:踩坑/事实(KNOWLEDGE)+ 开发规范(DEV-RULES · 构建/共享库/CI 约定)|
| 子项目 | `{子项目}/docs/KNOWLEDGE.md` · `{子项目}/docs/DEV-RULES.md` | 该子项目特有的踩坑(KNOWLEDGE)+ 开发规范(DEV-RULES)|

`GLOSSARY.md` / `TROUBLESHOOTING.md` 默认只在 workspace 级(`project-specs/`)。

---

# spec 文档写作约定(维护 teamwork skill 时)

> 🔴 **spec = 现行真相手册**:`SKILL.md` / `stages/*.md` / `standards/*.md` / `roles/*.md` 等给 AI 运行时读的文档,只写**当前该怎么做**,**当它一直如此**地写。

- 🔴 **不写版本标**:`(v8.xx)` / `[v8.xx]` / `v8.xx:` / `v8.xx 变更/增量/已物化` 一律不进 spec —— AI 运行时不需要知道某规则哪版加的。(例外:`v8.0` 范式切换在 SKILL.md 顶部留一处即可。)
- 🔴 **不写 case-id / 实证叙事**:`治本 SVC-CORE-Bxxx case` / `实证 PTR-Fxxx` / `旧实现…改成…` / `曾把 X 写坏` 等都是调试考古 —— 留**规则 + 不做的后果 + 反模式**就够,具体哪个 feature 触发的不写。
- ✅ **保留**:怎么做(步骤/命令/决策树)· 不做的后果(驱动遵守)· 反模式(防具体失败)· 设计 rationale(帮 AI 判断,但不带版本/case)。
- 📦 **历史只进 CHANGELOG**:版本演进、治本的 case、"为什么从 X 改成 Y" 全写 `docs/CHANGELOG.md`(发布时记录)· 不复制进 spec。
- 🔴 **发版纪律**:改 spec 加新规则时,**别在 spec 里写 `(v8.xx 新增)`** —— 直接当现行规则写;版本信息落 CHANGELOG。

---

## 引用本文件

- [docs/prepare.md](./prepare.md) — worktree 决策 + 暂停点收集 Feature ID(prepare 子流程引用本文件 §9-12 worktree 规范)
- [SKILL.md § 状态行](../SKILL.md) — 状态行例子(实际路径)
- [docs/feature-planning.md § Step 5](./feature-planning.md) — ROADMAP 起草时 BL-NNN 分配
- [stages/goal-stage.md](../stages/goal-stage.md) — Feature ID 已在 init-feature 时确定
- [stages/ship-stage.md § 8](../stages/ship-stage.md) — Ship 清理 worktree
- [templates/bug-report.md](../templates/bug-report.md) — Bug ID 格式
- [templates/roadmap.md](../templates/roadmap.md) — BL ↔ F 映射列说明
- [templates/adr-index.md](../templates/adr-index.md) — ADR-NNNN 维护
- [templates/config.md](../templates/config.md) — `.teamwork_localconfig.json` 模板(worktree 字段)
- [tools/bootstrap.py](../tools/bootstrap.py) — §13 `project-specs/` 骨架维护 + 旧散放文件迁移
