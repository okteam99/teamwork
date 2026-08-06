# Blueprint Stage

> 🧭 **四段结构**(标准 · 详 [STAGES.md §3](../STAGES.md)):目标 + 硬规则白名单 + 手段菜单 + 产物契约 · 手段 AI 自选。

---

## ① 目标(telos)

**在写代码之前把方案与测试收敛掉**:PRD 的「做什么」变成经评审的「怎么做」(TECH)+「怎么验」(TC),且**方案里的高影响要素(DB 结构变更 / 安全兜底)由用户拍板**。拦的风险:对着假设设计(不读真实代码)、过度设计被带进实现、schema/兜底被悄悄决定、AC 无测试覆盖。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **工程规范 = `standards/HARD-RULES.md`(必读白名单)+ 项目 `project-specs/DEV-RULES.md` 的并集 · 🔴 冲突以项目为准**(DEV-RULES 不存在则只读前者;方案与规范冲突 → 要么改方案、要么在 TECH 显式记原因)(why:项目主权高于框架缺省;白名单只收「逆模型默认」与「模型不可知」两类 —— 分册按需查不必通读)。
2. **§现状基线 grounded 真实代码**(不靠假设)· **§依赖与影响改契约必 grep 消费方**(不凭记忆)· **§查询性能涉 SQL 必给理由**(够快也要说为什么)(why:三者都是「写得出但没核实」的高发区 —— 对着假设设计是扩已有页 / 改已有契约类事故的上游)。
3. 🧾 **退役/替换类改造:按口径分张台账 · 总数不作验收门**—— 调用面 / 构造面 / 约束面各一张(口径定义 + 逐文件清单 + 每文件处置)· 🔴 **不同口径的总数不可互相印证**(why:实证中 TECH 与 TC 各算出「35 处/7 文件」并都自称与 PRD 吻合,实为两个互斥 population;真实是 25/6、71/6、18/5,且第三张是评审才发现的 —— **数字碰巧接近比对不上更危险,它让人以为核过了**)。
4. **每 AC 至少 1 test**(TC frontmatter `tests: [{id, covers_ac, description}]`)(why:`verify-ac.py` 物化校验 · 漏覆盖 = 需求→代码断链)。
5. **评审走隔离 subagent 冷审 · 不喂主对话起草心路**(需要 ADR / KNOWLEDGE 背景 → 派发 prompt 附路径让其自读)(why:同一 AI 起草完审自己会脑补填缝,白板效应恰是要的独立性)。
6. **两路并行同发 · 互不喂对方产出 · 🎭 模型错开**(外审路 ≠ 主审路)(why:同模型双路 = 盲区相关 · 错开是零成本的近异质)。
7. **`reviewers` 字段(复数)必含 `state.stage_review_roles[blueprint]` 全部角色**(why:`reviewers_match` evidence 校验 · 少列 = 评审配置形同虚设)。
8. **外审必覆盖方向 + `coverage: [...]` 申报**:可测试(TC 质量 / 测试策略 · QA 视角并入)· 方案盲区(依赖 / 影响面 / 迁移风险)+ **AI 自主方向 ≥1**(按 feature 自定)· 每方向给 finding 或「查过无发现」(why:物化门 `cross_review_coverage` —— 申报是外审没退化成泛谈的最低物证)。
9. ⏸️ **方案要素确认(条件暂停点 · 见 ④)**:TECH 涉 **DB 数据结构变更** 或 **🛡️ 兜底清单非空** → blueprint-complete 前必 emit R5 暂停点等用户拍板(why:schema 与兜底是「高影响且不可轻易回退」的方案要素 · ROI 账与拍板权都归用户 · 不许默默做)。
10. 🎚️ **TECH 起草与评审必用主模型 / 高级模型**(错开时也只在高档之间错 · **不许降到验证档**)(why:TECH 是全局质量上限 —— 方案错了下游全错 · 改 TECH 比改代码便宜但前提是方案本身出自够强的判断;其余环节〔TC 对照 / 测试执行 / 机械外化〕该降档就降,主对话编排并行)。
11. **TECH 写「方案」不写函数实现**(选型 / 接口 / 数据结构;代码细节归 dev)· **NEEDS_REVISION 主对话内闭环修订**(不打扰用户)(why:阶段职责边界 + R5/fix-retry 规范)。

> 🔴 **拦过度设计的最佳时机在这里**(改 TECH 比改代码便宜):Architect 必过**简洁性 counter-lens** · external finding 别盲采(天然偏「加校验/加安全/加兜底」)· 🛡️ **安全加固/兜底降级 finding 必过 ROI**(最难驳故最该审)—— **判据全文单源 [roles/architect.md](../roles/architect.md) Telos**(含实证 SDK-F038)· 🆕 **rival 设计强制**:评审新增结构必须自己先生成 ≥1 个替代形态再裁决 —— 「赢了作者列举的被否方案」不算通过。
> 🔴 **变更最小化**(四问清单见 `templates/tech.md §变更表清单`):每项 DB 变更必带「**解决什么问题 + 为何非更简方案不可**」—— 写不出 = 该变更大概率不需要。

---

## ③ 建议手段菜单(AI 自选 · 不强制)

| 手段 | 何时值得 |
|---|---|
| ⚡ **起草期并行 · 收敛期归一**| **推荐默认** —— **起草**:TC ∥ TECH 各派一 subagent(两者相互独立:TC 锚 PRD.AC · TECH 锚设计方案;goal 投机窗已产 TECH 草稿则接续)· 🔴 **收敛**:复核后的修订由**同一个 agent 顺序改两档**,不再跨 agent 往返;纯机械同步项(错误码回填 / 过期注删除)**主编排直接 Edit 落盘 · 不派 agent** |
| 第三视角冷审(roster 含 external 时)| 跑 `state.py external-review --stage blueprint` 拿 subagent 配方 → 起**错开模型** subagent(≠会话主模型)· 产物落 `external-cross-review/*.md`(`review_via: subagent` + 照实申报 `review_model` + coverage)· roster 无 external → 整段 skip |
| QA 独立 TC Review | 默认并入外审「可测试」方向;测试面大的复杂 Feature `change-review-roles` 加回独立跑 |
| 读 ARCHITECTURE / KNOWLEDGE / standards 分册 | 涉架构影响、已知踩坑、测试分层决策时 |

---

## ④ Output Contract

**产物 schema 以模板为单源**(原压缩重述已删 —— 它曾与 §②给出**互相矛盾**的两份 TECH 段落清单,是「指针 + 复制被指向内容」的漂移实例):

- `TC.md` → `{SKILL_ROOT}/templates/tc.md`(🔴 含 **§TC 的职责边界** —— 判据「**换实现就要改的内容不属于 TC**」· 表数/表清单/存储形态归 TECH · TC 只验可观测行为)
- `TECH.md` → `{SKILL_ROOT}/templates/tech.md`
- `TECH-REVIEW.md` → 无独立模板 · frontmatter `reviewers`(复数 · 含 roster 全角色)+ `verdict` · 按角色 finding 分段
- `external-cross-review/*.md` → 跑 `state.py external-review --feature ... --stage blueprint` 自动落(**不要手写** · 含 `coverage: [...]`)

📎 **物化拦截**:`verify-ac.py`(每 AC ↔ TC.md `tests[].covers_ac` · blueprint-complete 自动跑 · 漏覆盖 FAIL)· P0-154(`external-cross-review/*.md` 非空 · roster-gated)· `reviewers_match` · `cross_review_coverage`。

### ⏸️ 方案要素确认暂停点(条件 · R5)

🔴 **`auto_mode=true` 时跳过** —— 但 PMO 必 `state.py add-concern --severity WARN --message "auto skip: 方案要素确认 · DB: .../兜底: ..."` 留 audit(详 [SKILL.md § auto_mode](../SKILL.md))。

```markdown
⏸️ TECH 方案要素确认(DB 变更 / 兜底策略 · 命中项如下)· 请确认:

**变更点明细**(🔴 必给 · **照抄 TECH §变更表清单**原样贴出 · 对象级每条一行 —— 分类概括 / 文件指针不算变更点):对象 | 变更 | 解决什么问题 | 为何非更简方案不可 | 破坏性。

**关键迁移策略**(有则必列 · ≤6 行):有损与否 / 唯一约束前历史数据冲突预检 / 历史回填口径 / down migration / 清理周期 / 特殊设计一句话。

**🛡️ 兜底清单**(TECH 含安全/降级兜底时必给 · 无则省略 · **照抄 TECH §兜底清单**原样贴出 · 含 💬 大白话列)。

12. **确认方案 · 进入 dev** 💡 推荐   2. **调整方案**(对表结构/字段/迁移/兜底有异议 → RD 修订 TECH)   3. **其他指示**
(R5 标准三选项格式见 [SKILL.md § R5(b)](../SKILL.md))

📚 决策参考:TECH.md §数据模型(完整字段与迁移顺序 · 指针只作深读补充 · 🔴 不替代上面的明细)
```

🔴 **变更点明细是本暂停点的正文 · 不是可选附件**(实证:只给「增加诊断投影与快照序号」类分类概括 + 指针 → 用户被迫追问「DB 变更方案是什么」= 暂停点白 emit 一轮)。两类都未命中 → 跳过。

```
state.py blueprint-complete ...     # verify-ac.py 自动跑 · external-review artifact 校验
```

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BLUEPRINT_SPEC`
- external 协议:[../standards/external-model-usage.md §二](../standards/external-model-usage.md) · 入口规范:[../SKILL.md](../SKILL.md)
