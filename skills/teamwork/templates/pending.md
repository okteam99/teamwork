# PENDING 待规划需求池模板(实例化骨架)

> 位置:`product-overview/PENDING.md`(workspace 级 · 规划层 inbox)· 无 `product-overview/` 时首个 PENDING 项即创建该目录 + 本文件(轻量 · 不强制其他规划文档)。
> 🔴 **定位**:跨 Feature/session 发现的"本次范围外但要做"事项的**收集池** · 等用户拍板何时启动 —— 从 `teamwork-space.md` 外置(它 append-heavy · 不该占全景索引的"≤1 行/一眼看懂")。
> 🔴 **维护者**:PMO(AI)· append/删随主对话落盘(用户可见 · 非 R5 暂停点级)。
>
> 🔴 **规则**:
> - **追加**:任何 PMO/RD/PM 在 stage 内识别"本 Feature 不做但需后续做" → 必追加(防遗忘 / 防散落 OQ)。
> - **ID** `PENDING-NNN`(工作区独立递增)· **状态** 📝 待规划 / 🔄 规划中 · **背景** 1-3 句(来源 session + 为什么本次不做 + 影响)。
> - 🔴 **只保留 active(📝/🔄)**:转 ✅ 已转(进 Feature/Bug)→ 从表删 + 记 Feature `state.json.related_pending`;转 ❌ 不做 → 从表删(原因入 `workstream/WS-NN.md` 或 git log)· **防表膨胀**。
> - **mode A query** 命中"待做 / 待规划 / pending / backlog / 还要做什么" → PMO 读本表给用户(详 [SKILL.md § Triage](../SKILL.md))。
> - 🔴 每格 ≤ 1 行 · 转化后详情外迁(进 WS / Feature)· 本池不留历史。

```markdown
# 待规划需求池(PENDING)

> 跨 Feature/session 的"范围外但要做"项 · 等用户拍板启动 · 🔴 只留 active(📝/🔄)· 转化即从表删。

| ID | 标题 | 来源 | 目标项目 | 背景(1-3 句) | 状态 | 加入日期 |
|---|---|---|---|---|---|---|
| PENDING-001 | <例·country 字段填充责任方> | <例·SVC-CORE-F024 goal OQ-4> | <gateway / SDK 待拆> | <协议新增 country·谁填未定·影响 geo 过滤> | 📝 | 2026-05-18 |
```

## 与其他文档的关系

- 🔗 `teamwork-space.md` § 待规划需求池 — 只留 1 行指针指向本文件(不放表)。
- 🔗 转化出口:`product-overview/workstream/WS-NN.md`(进规划)/ Feature `state.json.related_pending`(进执行)。
- 🔗 维护规范:[docs/teamwork-space-guide.md §6](../docs/teamwork-space-guide.md)。
