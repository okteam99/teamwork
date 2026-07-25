# 工程硬规则白名单(🔴 必读 · v8.285)

> **这是 standards/ 的唯一必读文件**(~50 行)。分册(`common` / `backend` / `frontend` / `tdd`)是**按需查的参考**,不要求通读。
>
> 🔴 **工程规范 = 本文件 + 项目 `project-specs/DEV-RULES.md` 的并集 · 冲突以项目为准**(项目主权高于框架缺省;项目要覆盖某条,在 DEV-RULES 显式声明即可)。
>
> 🔴 **收录判据 = 与模型默认行为的距离**(v8.285 · 只收两类):
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
   *模型默认:「加安全总没错」—— 这两类最难驳、最易盲采。详 [external-model-usage.md §12](./external-model-usage.md)。*
7. **NEVER refactor while RED** · **不允许 horizontal slicing**(批量先写全部测试再批量实现)· **禁止 mock 被测组件自身的内部方法**。
8. **无失败测试不写生产代码**(TDD Iron Law)· 例外仅限 [tdd.md §五](./tdd.md) 列举场景且**须用户同意**。
9. **≥3 次失败修复 → 停止并升级**,不允许无意识第 4/5/6 次尝试(症状性修复反模式)。

---

## 二、框架/项目约定(🔴 模型不可能知道 · 这是信息不是规范)

10. **临时产物只落 scratch 根** `${TMPDIR:-/tmp}/teamwork/<feature_id>/...` —— 🔴 **禁**根之外另建 teamwork 临时目录 · 🔴 **禁**简称/别名(`bl031` 类 —— 实证:即兴命名让 ship2 按 feature_id 回收失败)· **build target 按 feature 共享** `<feature_id>/target`(串行 stage 复用增量编译)。
11. **临时调试日志唯一前缀** `[DEBUG-{Feature}-{NNNN}]` · **ship 净化阶段必 grep 确认清空**。
12. **测试脚本两层结构**:脚本**不负责启动环境** —— 环境由根级 `test-env-setup.sh` 完成;脚本本身纯代码级、不依赖全局环境。
13. **结构化日志必填字段**:`timestamp` · `level` · `service` · `trace_id` · `message` · 业务上下文键 · 异常附 `stack`。
14. **统一响应格式与业务状态码**:以 [backend.md §三](./backend.md) 的格式与码表为准(不自造)。
15. **迁移文件命名不靠读邻居推断**(邻居可能不一致/有坏样板)· 按 [backend.md §五](./backend.md) 优先级链取。
16. **Build 必须跑通才能进 Code Review**(硬门禁)· 无 build 步骤的项目须**显式标注「无 build 步骤」**,不能省略。

---

## 相关

- 分册(按需查 · 不必通读):[common.md](./common.md) · [backend.md](./backend.md) · [frontend.md](./frontend.md) · [tdd.md](./tdd.md) · [external-model-usage.md](./external-model-usage.md) · [scripts-policy.md](./scripts-policy.md)
- 项目侧规范(优先级更高):`project-specs/DEV-RULES.md`(人维护 · API 契约 / 错误处理 / 其他约定)
