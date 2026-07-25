# Blueprint Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md(权威需求)· ARCHITECTURE.md(系统架构)· KNOWLEDGE.md(项目踩坑/事实)· standards/tdd.md。
🔴 **`project-specs/DEV-RULES.md` 存在 → 必读**(本项目**强制开发规范** · 人维护:API 契约 / 错误处理 / 其他约定 · v8.257 三项制)· TECH 方案**须遵守**;冲突要么改方案、要么在 TECH 显式记原因。不存在 → skip(人维护 doc · 可能未建 · 不硬 FAIL)。

⚡ **§2 与 §3 起草相互独立 → 并行同发**(v8.256 · TC 锚 PRD.AC · TECH 锚设计方案 · subagent 各一)· 完成后互查一致(`tests[].covers_ac` ↔ TECH §测试策略)。

### 2. QA 起草 TC.md
BDD Given/When/Then · frontmatter `tests: [{id, covers_ac, description}]` · 每 AC 至少 1 test

### 3. RD 起草 TECH.md
🔴 **照 `templates/tech.md` 起草**(段落结构以模板为准 · v8.284 不在此复述 —— 原三处同源已产生分歧)。本 stage 只强调三条**证据要求**:**§现状基线 grounded 真实代码**(不靠假设)· **§依赖与影响改契约必 grep 消费方**(不凭记忆)· **§查询性能涉 SQL 必给理由**(够快也要说为什么)。
🔴 §数据模型 必明确标注:本方案**是否涉及数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration)· 涉及 → 触发 §7.5 用户确认暂停点(🛡️ TECH 兜底清单非空同触发 · v8.265)。🔴 **变更最小化**(v8.255 · 四问清单见 templates/tech.md §变更表清单):每项变更必带「**解决什么问题 + 为何非更简方案不可**」—— 写不出 = 该变更大概率不需要。DB 变更数是简洁性 counter-lens 的重点审查对象。

### 4. Architect Tech Review → TECH-REVIEW.md
frontmatter `reviewers: <state.stage_review_roles.blueprint 全体角色>` + `verdict` · 隔离 subagent 冷审(与 goal 冷审教义一致 · 不喂主对话起草心路;需要 ADR / KNOWLEDGE 背景 → 派发 prompt 附文件路径让其自读)
🔴 frontmatter 字段名是 `reviewers`(复数列表)· 必含 `state.stage_review_roles[blueprint]` 全部角色(reviewers_match evidence 校验)
🔴 **Tech Review 是拦过度设计的最佳时机(改 TECH 比改代码便宜)**:Architect 必过**简洁性 counter-lens** + external finding 别盲采(天然偏「加校验/加安全/加兜底」)· 🛡️ **安全加固/兜底降级 finding 必过 ROI**(v8.279 · 最难驳故最该审)—— **判据全文单源 [roles/architect.md](../roles/architect.md) Telos**(含实证 SDK-F038)。

### 5. (可选)QA 独立 TC Review
v8.244 默认 QA 并入 §6 外审覆盖方向「可测试」· 复杂 Feature(测试面大)`change-review-roles` 加回时独立启用

### 6. 第三视角冷审(external cross-review · roster 条件式 · v8.244 默认 roster = `[architect, external]`)
按 `state.stage_review_roles.blueprint` roster + localconfig 三层分支(与 §4 Architect 主审 ⚡ 并行同发 · 互不喂对方产出 · 🎭 两路模型错开〔v8.268〕):
- ① **roster 含 external 且 `.teamwork_localconfig.json` 的 `disable_external_review` 显式 `false`(opt-in 异质)** → 跑 `state.py external-review --feature <path> --stage blueprint`(host/model/profile 全自动)· 落 `external-cross-review/blueprint-<model>.md`
- ② **默认(缺省 / `true`)** → **错开模型** subagent 隔离冷审降级承担第三视角(≠主会话模型(如 fable5 会话 → 外审 opus) · v8.268)(产物仍落 `external-cross-review/*.md` · frontmatter 带 `review_via: subagent`)
- ③ **roster 无 external** → 整段 skip(机器校验自动过)

🔴 **外审内容契约(覆盖方向制 · v8.244)**:必覆盖 **可测试**(TC 质量 / 测试策略 —— QA 视角并入 · AC↔TC 机械绑定归 verify-ac)· **方案盲区**(依赖 / 影响面 / 迁移风险)+ 🔴 **AI 自主方向 ≥1**(按 feature 自定)· 每方向给 finding 或「查过无发现」· 产物 frontmatter 记 `coverage: [...]`(物化门 `cross_review_coverage`)。

详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。

### 7.5 ⏸️ 方案要素确认(条件暂停点 · R5 · DB 变更 / 兜底策略 · v8.265 双触发)
🔴 **触发条件(任一命中即停)**:① TECH 方案涉及**数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration);② TECH **🛡️ 兜底清单非空**(含任何安全兜底/降级兜底 —— ROI 账 + 拍板权都给用户 · 不许默默做)。
blueprint-complete 前 **必 emit R5 标准 1/2/3 暂停点 · 等用户拍板**(两类都命中则一次给全 · 都未命中跳过直接 §8):

🔴 **`auto_mode=true` 时跳过此暂停点** —— auto 用户已显式委托 AI 完成技术决策 · 但 PMO 必 `state.py add-concern --severity WARN --message "auto skip: 方案要素确认 · DB: .../兜底: ..."` 留 audit(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

```markdown
⏸️ TECH 方案要素确认(DB 变更 / 兜底策略 · 命中项如下)· 请确认:

**变更点明细**(🔴 必给 · **照抄 TECH §变更表清单**原样贴出 · 对象级每条一行 —— 分类概括 / 文件指针不算变更点):对象 | 变更 | 解决什么问题 | 为何非更简方案不可 | 破坏性。

**关键迁移策略**(有则必列 · ≤6 行):有损与否 / 唯一约束前历史数据冲突预检 / 历史回填口径 / down migration / 清理周期 / 特殊设计一句话。

**🛡️ 兜底清单**(TECH 含安全/降级兜底时必给 · 无则省略 · **照抄 TECH §兜底清单**原样贴出 · 含 💬 大白话列 v8.277)。

1. **确认方案 · 进入 dev** 💡 推荐   2. **调整方案**(对表结构/字段/迁移/兜底有异议 → RD 修订 TECH)   3. **其他指示**
(R5 标准三选项格式见 [SKILL.md § R5(b)](../SKILL.md))

📚 决策参考:TECH.md §数据模型(完整字段与迁移顺序 · 指针只作深读补充 · 🔴 不替代上面的明细)
```

🔴 **变更点明细是本暂停点的正文 · 不是可选附件**(v8.242 实证 case:只给「增加诊断投影与快照序号」类分类概括 + 指针 → 用户被迫追问「DB 变更方案是什么」—— 追问一次 = 暂停点白 emit 一轮)。

DB 变更与兜底清单**都未命中** → 跳过此步 · 直接 §8。

### 8. complete
`state.py blueprint-complete ...` · verify-ac.py 自动跑 · external-review artifact 校验

---

## 质量基线

📎 **物化拦截**:`verify-ac.py`(每 AC ↔ TC.md `tests[].covers_ac`) · P0-154(`external-cross-review/*.md` 非空 · roster-gated · v8.204 后默认降级 subagent 冷审)

**SOP**(违反 → review NEEDS_REVISION):
- TECH.md 写"方案"(选型 / 接口 / 数据结构)· 不写函数实现 · 代码细节归 dev stage
- NEEDS_REVISION 主对话内 PM 闭环修订 · 不打扰用户(R5 + fix-retry 规范)

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - TC.md → `{SKILL_ROOT}/templates/tc.md`(含 frontmatter + tests[].covers_ac BDD 示例)
> - TECH.md → `{SKILL_ROOT}/templates/tech.md`(结构以模板为准)
> - TECH-REVIEW.md → 无独立模板 · 见下方 schema · 按评审角色 finding 分段
> - external-cross-review/*.md → 跑 `state.py external-review --feature ... --stage blueprint`(自动落产物 · 不要手写)
>
> 🤖 **校验脚本**:`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}` ·
> blueprint-complete 自动跑 · 校验 PRD 每条 AC 在 TC.md `tests[].covers_ac` 至少 1 个引用 · 漏覆盖 FAIL。

> 🔴 **产物 schema 以模板为单源**(v8.284 删本节四个压缩重述 —— 原 `TECH.md` 条给的 5 段清单与 §3 的 9 段清单**互相矛盾**,正是「指针 + 复制被指向内容」的漂移实例):
> TC.md → `templates/tc.md` · TECH.md → `templates/tech.md` · TECH-REVIEW.md → 见上方 §4(frontmatter `reviewers` 复数含 roster 全角色 + `verdict`)· external-cross-review/*.md → `state.py external-review` 自动落(含 `coverage: [...]` 申报)。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BLUEPRINT_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
