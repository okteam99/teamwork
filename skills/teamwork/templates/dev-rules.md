# DEV-RULES 模板

> 位置:`project-specs/DEV-RULES.md`(workspace 级 · 与 product-overview/ 同级)+ `{子项目}/docs/DEV-RULES.md`(子项目级)· 详 [docs/conventions.md §13](../docs/conventions.md)
>
> **本文件 = 本项目「怎么写代码」的强制开发规范**(API 契约 / 错误处理 / 其他约定 · v8.257 三项制)· blueprint(TECH 设计)+ dev(实现)**必读遵守**。
> 架构/分层/依赖方向**不在本文件**(归 `ARCHITECTURE.md` + ADR);命名/风格/测试策略走 [standards/](../standards/) 缺省 · 本项目真有强制特例才塞「其他约定」。
>
> 🔴 **人/团队维护 · teamwork 永不自动改**:这是团队事前定的规矩(不是 AI 事后沉淀)。bootstrap 只在文件**不存在**时从模板创建空壳;**已存在则绝不改动**。AI 在 review/dev 发现值得固化的新约定 → **提示用户**加,不代写。
>
> 🔴 **边界**(别混):
>
> | 信息类型 | 去处 |
> |---------|------|
> | **本项目强制开发规矩**(API 契约 / 错误处理 / 其他约定)| **本文件 DEV-RULES.md** |
> | 架构 / 分层 / 依赖方向 | `project-specs/ARCHITECTURE.md`(workspace)/ `{子项目}/docs/architecture/`(子项目)+ ADR |
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

## API 契约

> 对外接口的强制约定:响应包络 / 错误码结构 / 分页 / 字段 casing / 版本与兼容规则(只列本项目强制的;存量服务已有风格 = 对外契约 · 沿用并在此注册 —— standards 覆盖声明唯一注册处)。

## 错误处理

> 错误返回结构 / 异常 vs 错误码 / 日志级别约定。

## 其他约定

> 配置 / secret / 提交 等其他必守约定;命名 / 风格 / 测试策略若有**强制特例**(偏离 standards 缺省)也注册在此。
```

## 与其他文档的协作

- 🔗 `RELEASE-GUIDE.md` — **版本发布规范**(集成分支 → 生产 · 用户说「发布/上线」PMO 必读照办);本文件管怎么写码 · 它管怎么发版
- 🔗 `KNOWLEDGE.md` — 项目踩坑 / 偏好(AI 沉淀 · 按需);本文件 = 人定强制规矩(必读)
- 🔗 `GLOSSARY.md` — 业务术语 / 命名词典
- 🔗 [standards/](../standards/) — 跨项目通用规范(本文件只写**本项目特有**的强制约定 · 不抄通用)
