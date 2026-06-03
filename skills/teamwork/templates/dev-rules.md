# DEV-RULES 模板

> 位置:`project-specs/DEV-RULES.md`(workspace 级 · 与 product-overview/ 同级)+ `{子项目}/docs/DEV-RULES.md`(子项目级)· 详 [docs/conventions.md §13](../docs/conventions.md)
>
> **本文件 = 本项目「怎么写代码」的强制开发规范**(分层 / 命名 / 错误处理 / 依赖方向 / 测试策略 / 风格)· blueprint(TECH 设计)+ dev(实现)**必读遵守**。
>
> 🔴 **人/团队维护 · teamwork 永不自动改**:这是团队事前定的规矩(不是 AI 事后沉淀)。bootstrap 只在文件**不存在**时从模板创建空壳;**已存在则绝不改动**。AI 在 review/dev 发现值得固化的新约定 → **提示用户**加,不代写。
>
> 🔴 **边界**(别混):
>
> | 信息类型 | 去处 |
> |---------|------|
> | **本项目强制开发规矩**(分层/命名/错误处理/测试/风格)| **本文件 DEV-RULES.md** |
> | 项目踩坑 / 历史坑 / 客观约束 / 用户偏好(AI 沉淀)| `KNOWLEDGE.md` |
> | 业务术语 / 实体关系 / 命名词典 | `GLOSSARY.md` |
> | 架构决策(有备选 + 后果)| `ADR` |
> | 跨项目通用规范 | teamwork `standards/` |
>
> 🔴 **保持精简**:只写「**必须遵守的规矩**」+ 一句理由 · 不写教程 / 不抄通用最佳实践(那些走 standards)。建议 ≤ 200 行。不适用的段直接删。

```markdown
# {项目名} 开发规范(DEV-RULES)

> 本项目团队约定的开发规矩 · blueprint/dev 必须遵守 · 与之冲突要么改方案、要么在 TECH 显式记原因。
> 维护:人工 · 新规矩讨论后由人加入。

## 架构 / 分层

> 模块边界、分层规则、依赖方向(谁能依赖谁、禁止反向依赖)。

- 示例:所有 DB 访问只经 `repository/` 层 · service 层禁止直接拼 SQL。
- 示例:依赖方向 `handler → service → repository` 单向 · 禁止 service 依赖 handler。

## 命名

> 文件 / 类型 / 函数 / 变量 / 数据库对象的命名约定(只列与语言默认不同的)。

- 示例:DB 表前缀 `app_` · 禁用 `tbl_`。
- 示例:前端表单字段一律 camelCase(不跟后端 snake_case)。

## 错误处理

> 错误返回结构 / 异常 vs 错误码 / 日志级别约定。

- 示例:所有 API error 返回 `{code, message, details}` 结构。
- 示例:用 `Result<T, E>` 显式传错 · 禁止吞异常。

## 测试策略

> 测试分层 / 覆盖要求 / 测试框架与约定 / 什么必须测。

- 示例:集成测试用 testcontainers · 不 mock DB。
- 示例:每个 public 接口至少 1 个 happy-path + 1 个 边界 test。

## 代码风格

> formatter / linter / import 顺序等(只列工具命令 + 与默认不同的约定)。

- 示例:`cargo fmt` + `clippy -D warnings` 必过 · 无格式 PR。

## 其他约定

- 示例:配置走环境变量 · 禁止硬编码;敏感配置走 `.teamwork-local-env/`。
```

## 与其他文档的协作

- 🔗 `KNOWLEDGE.md` — 项目踩坑 / 偏好(AI 沉淀 · 按需);本文件 = 人定强制规矩(必读)
- 🔗 `GLOSSARY.md` — 业务术语 / 命名词典
- 🔗 [standards/](../standards/) — 跨项目通用规范(本文件只写**本项目特有**的强制约定 · 不抄通用)
