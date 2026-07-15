# {项目名} 术语表（GLOSSARY）

> 🟢 **本文是 teamwork bootstrap 自动创建的空骨架**。
> ⏳ **请按业务填术语** · 填完后 PMO/PM/RD/架构师在起草 PRD / TECH 前会自动 read。
>
> teamwork 在以下场景按需 read：
> - PMO triage 期承接需求时（防业务词漂移）
> - PM 起草 PRD 前 / RD 起草 TECH 前 / 架构师 Tech Review 前
> - PM 评审 finding 类别 `terminology-ambiguity` 触发时（必须 ADOPT 写入本文档）
>
> **路径硬规则**：`project-specs/GLOSSARY.md`（teamwork 固定路径 · 与 product-overview/ 同级 · 详 docs/conventions.md §13）。
> **内容由项目维护**：teamwork 不假设业务术语 · 只提供骨架。
> **空骨架检测**：未填内容时所有表格仍为模板占位符（如 `{填入术语}`）· PMO 检测后用通用方法 + 提示用户填。

---

## 一、业务术语

跨子项目共享的业务核心概念 + 中英文对照。

| 术语（英文）| 中文 | 含义 | 出现位置 / 别名禁用 |
|------------|------|------|------------------|
| {填入术语} | {中文} | {一句话定义} | {子项目 / 模块 · 禁写 "xxx"} |

---

## 二、实体关系（Relationships）

业务实体之间的核心关系（用 mermaid 或文字描述）。

```
{填入实体关系图 / 文字描述}

例：
Partner --请求--> Offer（出价撮合）
AON --分发--> Partner（流量分发）
User --下单--> Offer
```

---

## 三、命名约定（跨服务一致性）

数据库 / API / 代码层的命名约定 · 防止跨服务漂移。

- **DB 表名**：{例：复数（partner_request_journals）/ snake_case}
- **DB 字段**：{例：snake_case · 主键 id 用 UUID / BIGSERIAL · 时间字段 *_at}
- **API 路径**：{例：/v1/{resource}/{action} 风格}
- **枚举字段**：{例：字符串而非 int（biz_type='offer_query'）}
- **错误码**：{例：HTTP 状态码 + 业务子码 · ERR_PARTNER_TIMEOUT}

---

## 四、别名 / 已澄清歧义

记录评审 / 实战 case 中澄清过的术语歧义 · 防止再次漂移。

| 错误用法 | 正确用法 | 澄清 case / 来源 |
|---------|---------|-----------------|
| {填入错误用法} | {填入正确用法} | {Feature 编号 / 评审 finding} |

---

## 五、缩写词典

项目特定的缩写 · 含通用业务缩写。

| 缩写 | 全称 | 说明 |
|------|------|------|
| {填入缩写} | {填入全称} | {上下文说明} |

例：
- MR = Merge Request（GitLab 合并请求）
- PR = Pull Request（GitHub 合并请求）
- AC = Acceptance Criteria（PRD 验收标准）

---

## 维护约定

- **写入硬时机**（teamwork 强约束）：
 - PM 评审 finding 类别 = `terminology-ambiguity` 时必须 ADOPT 并写入本文档（roles/pm.md）
 - 评审过程中发现新术语 / 跨服务命名不一致 → 立即登记
 - 业务方向变更后新术语出现 → PL 在 product-overview/ 更新前同步更新本文档
- **写入硬规则**：每条术语必须含中英文 + 一句话定义 + 出现位置（防止抽象孤立）
- **PMO preflight 扫描**：triage 期 PMO 自动 read 业务术语段 · 命中关键词时引用到主对话
- **多子项目场景**：跨子项目共享术语 → `project-specs/GLOSSARY.md`；子项目内部实现层术语 → 各子项目 KNOWLEDGE.md § Glossary 子段（仅项目内部命名 · 大多数项目不需要）
