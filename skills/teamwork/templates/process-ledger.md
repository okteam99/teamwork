# PROCESS-LEDGER 模板(流程价值台账)

> 位置:`project-specs/PROCESS-LEDGER.md`(workspace 级 · 与 DEV-RULES / KNOWLEDGE 同级)。
> **telos**:一行一 feature 的流程仪式价值数据 · 给「该不该砍某环节」提供查表依据。消费方:流程审视场景 + 年检 kill criteria(详 [stages/ship-stage.md §16](../stages/ship-stage.md))。
> 🔴 区别 `docs/retros/`(业务/工程复盘 · 子项目级 · 知识层):本表只度量 **teamwork 流程本身**的环节价值 · 别混写。
> 写入时机:ship2(`ship-finalize`)完成后 PMO append。🔴 单元格 ≤1 行 · 机器字段照实抄 state.json / REVIEW.md · **不美化**(过场就写过场)。

---

# 流程价值台账

> 查询示例(年检 / 流程审视时算):external confirmed 率 = Σ采 / Σ总;某角色真 finding 率 = 该角色 finding 数 / feature 数;暂停点 all-default 率 = Σ默 / Σ(改+默)。

| Feature | flow | 实走 stages | 时长 | review/test 轮 | external 总/采/驳 | 角色真 finding | 暂停点 改:默 | bypass/WARN | 反思摘要(≤1 行) |
|---|---|---|---|---|---|---|---|---|---|
| <ID> | <Feature/Bug/敏捷/Micro> | <goal→blueprint→dev→…→ship> | <X.Xh> | <1/1> | <3/1/2> | <arch:1 qa:0 ext:1> | <1:2> | <0/0> | <external 拦 1 真问题 · ui_design 零 finding 过场> |
