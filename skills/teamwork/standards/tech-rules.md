# 技术规则(tech-rules)—— 方案起草 · dev 开发 · review 三时点唯一必读(行数不写死 —— 数字宣称必漂)

> 🔴 **必须同时读并满足项目规范**(标准路径):`project-specs/DEV-RULES.md`(项目开发规范 · 人维护)+ `project-specs/ARCHITECTURE.md`(项目架构规范)—— **本规范与项目规范需同时满足;冲突部分以项目规范为准**。覆盖声明唯一注册处 = DEV-RULES.md(未声明 → 按本文件缺省;`KNOWLEDGE.md` 只归事实/踩坑 · 不作规范覆盖注册处);DEV-RULES 不存在 → 只读本文件,并提示用户可把项目约定固化进去(AI 不代写)。
>
> 🔴 **收录判据 = 与模型默认行为的距离**(只收两类):
> - **逆默认**:模型默认会做**反**的 —— 它越强越笃定,越需要这条明确逆着写;
> - **不可知**:模型不可能猜到的框架/项目约定(这是**信息**不是规范)。
> **模型默认就会的一律不收**(REST 命名 / SOLID / TDD 红绿步骤 / mermaid 语法 / WCAG 细则…)—— 收了就是注意力税。
>
> 三时点用法:**起草 TECH** 重点 §三(方案要素带着门想)· **dev** 重点 §一/二/五 · **review** 全文对照(§三 的门逐条验)。存量服务的**对外契约**(如 API 响应结构)一致性优先:沿用存量 + 提示用户固化进 DEV-RULES。

---

## 一、逆模型默认(🔴 模型会做反 · 必须明确逆着写)

1. **默认避免 DB-level `FOREIGN KEY`**(含 `ON DELETE/UPDATE CASCADE`)· 引用完整性由应用层 / ORM / 服务边界保证。
   *模型默认:「加 FK 保证引用完整性」(教科书)。* 项目可在 `DEV-RULES.md` 声明覆盖 → 以其为准 + TECH 引用行号。决策门详 §三。
2. **降级 / 兜底 / fallback 路径触发 → 必打 WARN 日志**(无例外)· **缺失即阻塞 Code Review**。
   *模型默认:静默 fallback(「优雅降级」不留痕)= 生产盲区。* 必须字段详 §三。
3. **三方 / 外部服务调用异常 → 必打 ERROR 日志**(HTTP 非 2xx / 业务错误码 / 超时 / 连接失败 / 反序列化失败,任何非预期响应)。必须字段详 §三。
4. **不静默吞异常**:每条 catch / error 路径必有 WARN(可恢复)或 ERROR(需排查)+ 足够上下文(feature id / 关键业务 id / 原因)。
5. **「两个 adapter 才抽象」**:第一次出现适配需求 = 写 inline 一次性代码;**第二次重复才抽象**。
   *模型默认:提前抽象(过度设计的最常见入口)。*
6. **安全加固 / 兜底降级必过 ROI**(概率×后果 vs 实现维护成本)· 立不住就砍。
   *模型默认:「加安全总没错」—— 这两类最难驳、最易盲采。详 [external-model-usage.md §二](./external-model-usage.md)。*
7. **测试必须真断言** · **禁止 mock 被测组件自身的内部方法** · 🔴 **测试输入必须来自真实链路**
   (自造 fixture 要显式标注,并说清它与真实输入的差异)。
   *模型默认:① 为了让测试过,把正要验的那段 mock 掉;② 造"干净"的 fixture —— **而干净恰恰绕开了真实链路的形状**。
   两条都产出恒绿空壳,比没测试更危险(门禁/评审/验收同时失效)。*
   实证(SVC-CORE-F260728):测试用 SQL 直插绕开真实摄入路径 → **11 测试 + 4 变异验证全绿,功能却全坏** ——
   冷审 / 变异验证 / CI **全在自己画的那个圈里**,最后靠生产数据才发现。
   🔴 判据一句话:**验的是「我伪造的输入能被正确处理」,还是「真实链路会产生这样的输入」?**
8. **每个 TC 用例必须有对应实现**(TC↔实现这一跳没有机器门 · AC↔TC 由 `verify-ac.py` 管)。
 🟢 **怎么测由 AI 自觉**:TDD 红绿 / 先骨架后补边界 / test-after 自选 —— 框架**只管结果不规定手段**。
   结果由机器门保证(不靠自觉):AC 覆盖 → `verify-ac.py` · 真跑真绿 → `dev-complete --test-exit-code 0` + `--test-stdout` 非空(红 base 走 `test-baseline` 差分「0 新增」)· 没作弊 → test-stage ②「不为凑 exit-code=0 走捷径」+ review 外审必覆盖「测试真实性与覆盖」。
9. **≥3 次失败修复 → 停止并升级**,不允许无意识第 4/5/6 次尝试(症状性修复反模式)。

---

## 二、框架/项目约定(🔴 模型不可能知道 · 这是信息不是规范)

10. **临时产物只落 scratch 根**:worktree 模式(缺省)= `<worktree>/.teamwork-scratch/<用途>` · off/legacy = `${TMPDIR:-/tmp}/teamwork/<feature_id>/`(完整 feature_id · 禁简称)· 🔴 禁两根之外另建 · build target 按 feature 共享 —— 全文单源 [conventions.md §12.48](../docs/conventions.md)。
11. **临时调试日志唯一前缀** `[DEBUG-{Feature}-{NNNN}]`(如 `console.log("[DEBUG-F062-0001] payload:", payload)`)· **ship 净化阶段必 grep `\[DEBUG-` 确认清空**(命中报 suspicious_files 让用户决定)。前缀比裸 log 易识别、不与正式 logger 冲突、一次 grep 全清。
12. **测试脚本两层结构**:脚本**不负责启动环境** —— 环境由根级 `test-env-setup.sh` 完成;脚本本身纯代码级。接口契约(退出码 / 幂等 / 无交互 / stdout JSON)单源 [scripts-policy.md §7](./scripts-policy.md)。
13. **结构化日志必填字段**:`timestamp` · `level` · `service` · `trace_id` · `message` · 业务上下文键 · 异常附 `stack`。格式 JSON,字段名以此为准(级别按标准语义 · 不复述)。
14. **统一响应格式与业务状态码**:以 §三 的格式与码表为准(不自造)· 优先级链(项目 DEV-RULES → 存量沿用 → 本文件缺省)同在 §三。
15. **迁移文件命名不靠读邻居推断**(邻居可能不一致/有坏样板)· 命名与多 worktree 并行**起号纪律**单源 [conventions.md §12.49](../docs/conventions.md)。
16. **Build 必须跑通才能进 Code Review**(硬门禁)· 无 build 步骤的项目须**显式标注「无 build 步骤」**,不能省略。CI 是最后一道安全网,不是第一道发现机制。
17. **测试按生命周期三层分层** · 判据一句话:**「交付后还有谁需要它失败的信号?」**
    - **L1 CI 契约层:🔴 默认不进 · 进必须带 `ci_reason`**(这条失败拦住什么级别的事故:对外契约破坏 / 数据损坏 / 资损 / 核心链路不可用;「顺手写的 / 覆盖率好看」不算充足理由);
    - **L2 回归层** = TC 其余(AC 绑定 · test stage 全量跑 · CI 不跑);
    - **L3 脚手架**(TDD 中间步 / 探索 probe / 一次性验证)= 🔴 **只落 scratch `.teamwork-scratch/scaffold-tests/`(ignored)· 不入仓库内容**(交付即弃 · 随 worktree 消亡)。
    *模型默认:写过的测试全部入库全部进 CI —— 执行便宜 ≠ 维护便宜。* 详 [templates/tc.md § 生命周期](../templates/tc.md)。
18. **权威源单源**:格式 / frontmatter / schema 基线一律走权威源(`templates/` · Designer 框架基线 = panorama `preview/overview.html`)· **peer Feature 产物只可作内容参考 · 禁当格式/框架基线**(触发「参考最近相似 Feature」心智路径时默认走错 · 实证 PTR-F032)。
19. **架构文档落点**:架构决策(有备选 + 后果)→ `docs/adr/`;子项目拓扑/依赖方向 → `ARCHITECTURE.md`。**代码是唯一真相**,文档是它的索引不是替身。项目特例走 `DEV-RULES.md`(人维护)。
20. **文档图统一 Mermaid**(` ```mermaid ` 代码块)· 禁 ASCII 图 / 图片截图 / 第三方绘图链接 —— 必须能在 GitHub 与 Markdown 预览器直接渲染。
21. **集成测试数据走 `docs/TEST-DATA.md`**:测试前先查它复用 · 新建的登记进去 · 测后清临时保基础(不登记 = 下个 Feature 重复造数据)。集成测试报告字段(环境信息 / API 结果 / 落库真值 / 数据来源 / 结论 / 失败项)齐即可 · 格式不规定。

---

## 三、方案与架构门(起草 TECH 时带着想 · review 时逐条验)

### API 契约(优先级链 · 本节全部小节适用:响应结构 / JSON 命名 / 状态码 / 分页)

> ① 优先按项目 `DEV-RULES.md` 的 API 约定 —— 有则严格照办 · 本节默认不适用。
> ② DEV-RULES 未规定 · 但**存量服务已有明确一致的接口风格** → **沿用存量**(对外契约 · 同服务内一致性 = 正确性 · 新接口不得自创风格)· 🔴 并**提示用户**固化进 DEV-RULES.md(AI 不代写)。
> ③ 全新服务 / 无任何既有约定 → 用下方 teamwork 缺省。
> 📎 与迁移命名「不读邻居」的区别:迁移文件名是**内部惯例**(坏样板不该传染);API 响应结构是**对外契约**(消费方依赖)→ 存量风格在 ② 合法沿用。

**缺省响应格式**:`{"code": "SUCCESS", "msg": "...", "data": {}, "extra": {}}`(code 业务状态码 · msg 人读 · data 空时 `{}` · extra 分页/调试可选)。
**JSON 命名缺省 snake_case** —— 禁驼峰/帕斯卡/中划线混入(同服务不一致即破坏)。
**缺省码表**:`SUCCESS`/200 · `INVALID_PARAM`/400 · `UNAUTHORIZED`/401 · `FORBIDDEN`/403 · `NOT_FOUND`/404 · `CONFLICT`/409 · `RATE_LIMITED`/429 · `INTERNAL_ERROR`/500;自定义码 `{模块}_{错误类型}`(如 `ORDER_ALREADY_PAID`)。

### 日志 CR 门(§一 规则 2/3 的详版 · 缺失即阻塞)

**降级/兜底必打 WARN(不得降为 INFO/DEBUG · 不得静默)**:触发 = 任何「A 失败 → B 兜底继续」分支(else/default 兜底 · 参数无效用默认值 · 重试 · 缓存未命中走库 · 一切「理论上不应该走到」的路径);必须字段 = 降级原因(原始异常)· 降级前方案 · 降级后方案 · 业务上下文(trace_id / 业务 id)。静默降级 = 掩盖问题 —— 兜得住可用性,不能兜可观测性。

**三方/外部调用异常必打 ERROR(不得降为 WARN/INFO · 不得静默)**:范围 = 任何跨进程边界网络调用(三方 API / RPC·MQ / 云 SDK / 中间件);触发含**限流/熔断/降级信号与「200 但业务语义失败」**;必须字段(缺一不可)= 调用目标 · traceId / spanId · 请求摘要(脱敏)· 响应摘要 · duration_ms · 重试信息 · 业务上下文。🔴 **APM / sidecar 自动上报 ≠ 免除打日志义务**(业务上下文 APM 采不到);外部调用被降级兜底时**先 ERROR(异常本身)再 WARN(降级动作)· 两条缺一不可**。

跨服务边界是故障定位的关键切面 —— 静默失败的外部调用 = 排查毫无头绪 = MTTR 飙升。

**评审门禁**:CR 时所有跨进程调用点必须验证有 ERROR(catch 包住外部调用但没打 → 阻塞);所有 fallback/catch-and-continue 路径必须验证有 WARN,缺失即阻塞。

### Schema 变更门(涉 DB 必过)

- **TECH.md 必声明是否涉 schema 变更**(涉及 → 列变更内容;破坏性变更〔删列/改类型/删表〕必标风险)· 迁移完成后同步 ARCHITECTURE.md → database-schema.md(设计层 Tech Review 后写 · 实现层 Code Review 后补)。
- 🔴 **加 migration 前先查 DEV-RULES 的 migration 约定/守卫**(version-ceiling / sequence guard 等)· 同 PR 满足守卫要求;撞到未声明的项目守卫 → 修复后记进 DEV-RULES/KNOWLEDGE。
- 🔴 **跨子项目 Schema 同步(增/改/删列必查 · 缺列 → ORM 反序列化报错 → 500)**:TECH.md 必含「数据库变更 → Schema 影响分析」章节(来源 = database-schema.md「Model/Struct 映射」表 + grep 全项目代码)· 核对 Struct 字段与列完全一致(名/类型/可空)+ 所有引用该 Struct 的 SQL 查询列匹配 · 架构师 Tech Review **独立验证**影响分析完整性(不依赖 RD 自查)· Code Review 对照影响分析表逐项验证。
- **验证链**:TECH 声明(影响分析)→ blueprint 架构师评审(完整性 · 独立 grep 对照 · 更新 schema 设计层)→ dev(按表同步)→ 架构师 CR(代码↔表一致 · 补实现层)→ 集成测试(迁移可执行 + ORM 映射)—— 各阶段术语不同 · 校验基准统一为 TECH「Schema 影响分析」表。

### FK 决策门(本段是 FK 策略唯一权威 · templates/tech.md 仅 cite)

默认避免的理由(逆教科书 · 故必须给 why):分库分表后 FK 失效(规则终须落应用层 · 双层维护反而不一致)· 大批量写入/迁移/灰度回放时 FK check 成本不可控 · 跨服务边界的引用关系不该由 DB 隐式承载 · 级联删除生产事故回滚成本极高 · ORM 通常已能维护引用语义。

🔴 若 TECH.md 仍要引入 `FOREIGN KEY` / `CASCADE`,**必须**在「Schema 影响分析」表加一行 **「FK 决策 + 理由」**,理由须满足任一:
✅ 强一致小规模 OLTP(单库 · 不分片 · <10M 行 · 低写入)· ✅ 法务/合规/财务强约束(DB 是最后真值防线)· ✅ 内部管理后台/配置表(写入极低频)· ✅ DEV-RULES.md 已明文「本项目默认启用 FK」(cite 行号)。

❌ **反模式黑名单**(命中即架构师 Tech Review BLOCKER · 不可降级):「ORM 自动生成的我没动」(须显式 DROP 或给理由)·「开发期数据完整性方便」·「防止脏数据」(应用层 transaction + 单测才是真防线)·「通用最佳实践 / 教科书推荐」(无项目语境 = 没给理由)· 没写 FK 决策行(= 引入未声明)。

出口校验(触发词 `FOREIGN KEY`/`REFERENCES`/`CASCADE` 命中必查):①「FK 决策 + 理由」行存在 ②理由满足 ✅ 任一 ③黑名单未命中 ④启用 CASCADE → 额外列「删除主行连带删哪些子行」清单 + CR 必查。

### API 版本约定

- 版本策略缺省 URL Path(`/api/v{N}/...`)· 项目可在 DEV-RULES 声明其他(声明后以其为准)。
- **Breaking Change 必升版本号**;版本状态(⚠️ 废弃中 / ❌ 已下线)与**废弃截止日期登记 api-design.md 版本清单**(不登记 = 没人知道何时能下线)。
- 涉 API 变更的 TECH.md 必声明:是否 Breaking → 新版本号 · 影响接口清单 · 旧版本迁移方案 · 完成后同步 api-design.md。

---

## 四、前端专项(阈值与禁令 · 仅前端子项目适用 · DEV-RULES 可覆盖)

> 组件测试写法 / 状态管理选型 / 性能手法 / 无障碍细则 = 模型自带知识 · 不入库;项目特异约定归 `DEV-RULES.md` / `UI-RULES.md`。

- **覆盖率 > 70%**(CI 门禁值)· P0 流程必须覆盖;分层归属:单元(纯函数/hook)· 组件(渲染+交互+状态)· 集成(跨组件/路由/数据流)· e2e(归 browser_e2e stage)。
- 🔴 **项目内统一 CSS 方案 · 禁混用**(CSS Modules / Tailwind / CSS-in-JS / Sass+BEM 选其一)—— 单 Feature 各选各的 = 样式体系碎裂。
- 🔴 **组件引用 design token · 禁硬编码颜色值/魔法数字**;暗色模式在 token 层切换 · token 定期与设计稿对账。
- 🔴 **全局样式仅限 reset / base / typography** · 禁在全局样式定义业务组件样式。

---

## 五、收口自查表(dev 完成前过一遍 · 判断题不设机器门 · 每项可打 ✅ / N-A+原因)

> 🔴 这是**兜底自查**,不是方法论 —— 怎么开发(TDD / 骨架先行 / 重构节奏 / 先集成后单测)**全由 AI 自定,框架不设限**;框架只收这张表 + 上面的白名单 + 结果证据门。

- [ ] **异常/降级分支都有日志**:每条 catch / fallback / 外部调用失败路径有 WARN 或 ERROR + 足够上下文(规则 2-4 · 详版 §三)
- [ ] **DB 字段/表结构改动已充分论证**:TECH 有方案论证 · 已过 blueprint 方案要素确认(R5 用户拍板)· 迁移与 schema 文档同步(ship 门会校)
- [ ] **测试真断言 · 输入来自真实链路**(规则 7)· 每个 TC 有对应实现(规则 8)
- [ ] **新测试已定生命周期层**:一次性的在 scratch · 入库的绑 AC/回归 · 进 CI 的带 `ci_reason`(规则 17)
- [ ] **临时产物只在 scratch** · 临时调试日志 `[DEBUG-*]` 已清或可 grep(规则 10/11)
- [ ] **交付卫生**:build 跑通(规则 16 · 无 build 步骤显式标注)· 无 TODO / FIXME / 占位符 / 不完整片段入库
- [ ] **契约面改动已核消费方**:改了 API / 共享包 / 事件结构 → grep 消费方并适配(改 API 者负责迁移所有消费者)

---

## 相关

- 分册(按需查 · 不必通读):[external-model-usage.md](./external-model-usage.md)(冷审形态与裁决纪律)· [scripts-policy.md](./scripts-policy.md)(脚本纪律 + 测试脚本契约)· [conventions.md](../docs/conventions.md)(执行环境约定:scratch / 迁移起号 / worktree 构建世界)
- 项目侧规范(优先级更高):`project-specs/DEV-RULES.md` + `project-specs/ARCHITECTURE.md`(人维护)
