# 工程硬规则白名单(🔴 必读)

> **这是 standards/ 的唯一必读文件**(短白名单 · 行数不写死 —— 数字宣称必漂)。分册(`common` / `backend`)是**按需查的参考**,不要求通读。
>
> 🔴 **工程规范 = 本文件 + 项目 `project-specs/DEV-RULES.md` 的并集 · 冲突以项目为准**(项目主权高于框架缺省)。**覆盖声明唯一注册处 = DEV-RULES.md**(未声明 → 按 standards 缺省;`KNOWLEDGE.md` 只归事实/踩坑 · 不作规范覆盖注册处);存量服务的**对外契约**(如 API 响应结构)一致性优先:沿用存量 + 提示用户固化进 DEV-RULES(AI 不代写)。
>
> 🔴 **收录判据 = 与模型默认行为的距离**(只收两类):
> - **逆默认**:模型默认会做**反**的 —— 它越强越笃定,越需要这条明确逆着写;
> - **不可知**:模型不可能猜到的框架/项目约定(这是**信息**不是规范)。
> **模型默认就会的一律不收**(REST 命名 / SOLID / TDD 红绿步骤 / mermaid 语法 / WCAG 细则…)—— 收了就是注意力税。

---

## 一、逆模型默认(🔴 模型会做反 · 必须明确逆着写)

1. **默认避免 DB-level `FOREIGN KEY`**(含 `ON DELETE/UPDATE CASCADE`)· 引用完整性由应用层 / ORM / 服务边界保证。
   *模型默认:「加 FK 保证引用完整性」(教科书)。* 项目可在 `DEV-RULES.md` 声明覆盖 → 以其为准 + TECH 引用行号。详 [backend.md § FK 策略](./backend.md)。
2. **降级 / 兜底 / fallback 路径触发 → 必打 WARN 日志**(无例外)· **缺失即阻塞 Code Review**。
   *模型默认:静默 fallback(「优雅降级」不留痕)= 生产盲区。*
3. **三方 / 外部服务调用异常 → 必打 ERROR 日志**(HTTP 非 2xx / 业务错误码 / 超时 / 连接失败 / 反序列化失败,任何非预期响应)。
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

10. **临时产物只落 scratch 根**:worktree 模式(缺省)= `<worktree>/.teamwork-scratch/<用途>`(bootstrap 自动 gitignore · 随 worktree 消亡);worktree=off / legacy = `${TMPDIR:-/tmp}/teamwork/<feature_id>/`(🔴 完整 feature_id · 禁简称/别名 —— 实证:即兴命名让按 id 回收失败)。🔴 **禁**两根之外另建 teamwork 临时目录 · **build target 按 feature 共享** `.teamwork-scratch/target`(串行 stage 复用增量编译)。
11. **临时调试日志唯一前缀** `[DEBUG-{Feature}-{NNNN}]` · **ship 净化阶段必 grep 确认清空**。
12. **测试脚本两层结构**:脚本**不负责启动环境** —— 环境由根级 `test-env-setup.sh` 完成;脚本本身纯代码级、不依赖全局环境。
13. **结构化日志必填字段**:`timestamp` · `level` · `service` · `trace_id` · `message` · 业务上下文键 · 异常附 `stack`。
14. **统一响应格式与业务状态码**:以 [backend.md §三](./backend.md) 的格式与码表为准(不自造)。
15. **迁移文件命名不靠读邻居推断**(邻居可能不一致/有坏样板)· 按 [backend.md §五](./backend.md) 优先级链取。
16. **Build 必须跑通才能进 Code Review**(硬门禁)· 无 build 步骤的项目须**显式标注「无 build 步骤」**,不能省略。
17. **测试按生命周期三层分层** · 判据一句话:**「交付后还有谁需要它失败的信号?」**
    - **L1 CI 契约层:🔴 默认不进 · 进必须带 `ci_reason`**(这条失败拦住什么级别的事故:对外契约破坏 / 数据损坏 / 资损 / 核心链路不可用;「顺手写的 / 覆盖率好看」不算充足理由);
    - **L2 回归层** = TC 其余(AC 绑定 · test stage 全量跑 · CI 不跑);
    - **L3 脚手架**(TDD 中间步 / 探索 probe / 一次性验证)= 🔴 **只落 scratch `.teamwork-scratch/scaffold-tests/`(ignored)· 不入仓库内容**(交付即弃 · 随 worktree 消亡)。
    *模型默认:写过的测试全部入库全部进 CI —— 执行便宜 ≠ 维护便宜:AI 维护成本按语料线性 · CI 墙钟逐 feature 累加,临时 case 入库 = 永久税。* 详 [templates/tc.md § 生命周期](../templates/tc.md)。

---

## 三、收口自查表(dev 完成前过一遍 · 判断题不设机器门 · 每项可打 ✅ / N-A+原因)

> 🔴 这是**兜底自查**,不是方法论 —— 怎么开发(TDD / 骨架先行 / 重构节奏 / 先集成后单测)**全由 AI 自定,框架不设限**;框架只收这张表 + 上面的白名单 + 结果证据门。

- [ ] **异常/降级分支都有日志**:每条 catch / fallback / 外部调用失败路径有 WARN 或 ERROR + 足够上下文(规则 2-4)
- [ ] **DB 字段/表结构改动已充分论证**:TECH 有方案论证 · 已过 blueprint 方案要素确认(R5 用户拍板)· 迁移与 schema 文档同步(ship 门会校)
- [ ] **测试真断言 · 输入来自真实链路**(规则 7)· 每个 TC 有对应实现(规则 8)
- [ ] **新测试已定生命周期层**:一次性的在 scratch · 入库的绑 AC/回归 · 进 CI 的带 `ci_reason`(规则 17)
- [ ] **临时产物只在 scratch** · 临时调试日志 `[DEBUG-*]` 已清或可 grep(规则 10/11)
- [ ] **交付卫生**:build 跑通(规则 16 · 无 build 步骤显式标注)· 无 TODO / FIXME / 占位符 / 不完整片段入库
- [ ] **契约面改动已核消费方**:改了 API / 共享包 / 事件结构 → grep 消费方并适配(改 API 者负责迁移所有消费者)

## 相关

- 分册(按需查 · 不必通读):[common.md](./common.md)(通用 + §七前端专项)· [backend.md](./backend.md) · [external-model-usage.md](./external-model-usage.md) · [scripts-policy.md](./scripts-policy.md)
- 项目侧规范(优先级更高):`project-specs/DEV-RULES.md`(人维护 · API 契约 / 错误处理 / 其他约定)
