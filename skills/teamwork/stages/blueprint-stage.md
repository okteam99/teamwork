# Blueprint Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md(权威需求)· ARCHITECTURE.md(系统架构)· KNOWLEDGE.md(项目踩坑/事实)· standards/tdd.md。
🔴 **`project-specs/DEV-RULES.md` 存在 → 必读**(本项目**强制开发规范** · 人维护:分层 / 命名 / 错误处理 / 依赖方向 / 测试策略 / 风格)· TECH 方案**须遵守**;冲突要么改方案、要么在 TECH 显式记原因。不存在 → skip(人维护 doc · 可能未建 · 不硬 FAIL)。

### 2. QA 起草 TC.md
BDD Given/When/Then · frontmatter `tests: [{id, covers_ac, description}]` · 每 AC 至少 1 test

### 3. RD 起草 TECH.md
§模块划分 · §数据模型 · §接口定义 · §依赖与影响 · §风险
🔴 §数据模型 必明确标注:本方案**是否涉及数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration)· 涉及 → 触发 §7.5 用户确认暂停点。

### 4. Architect Tech Review → TECH-REVIEW.md
frontmatter `reviewers: [qa, architect, external]` + `verdict` · 主对话默认(保留架构上下文)
🔴 frontmatter 字段名是 `reviewers`(复数列表)· 必含 `state.stage_review_roles[blueprint]` 全部角色(reviewers_match evidence 校验)
🔴 **Tech Review 是拦过度设计的最佳时机(改 TECH 比改代码便宜)**:Architect 必过**简洁性 counter-lens** —— 「方案是否过度设计(YAGNI)· 能否更简单达成业务目标 · 每个组件职责是否最小且归对层(该透明的别解析 / 该下沉的别上提)」。external finding 别盲采:天然偏「加校验」· 每条对照业务目标 + 简洁性取舍(详 `roles/architect.md` Telos)。

### 5. (可选)QA TC Review
复杂 Feature 启用 · 简单跳过

### 6. External cross-review
**跑** `state.py external-review --feature <path> --stage blueprint`(host/model/profile 全自动 · 异质性硬约束物理墙)· 落 `external-cross-review/blueprint-<model>.md`。详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。

### 7. PM 回应 + 修订循环
NEEDS_REVISION 时主对话内闭环 · 不打扰用户

### 7.5 ⏸️ 数据库数据结构变更确认(条件暂停点 · R5)
🔴 **若 TECH 方案涉及数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration)·
blueprint-complete 前 **必 emit R5 标准 1/2/3 暂停点 · 等用户拍板**(DB schema 变更高风险 · 难回滚 · 写代码前必经用户确认):

🔴 **`auto_mode=true` 时跳过此暂停点** —— auto 用户已显式委托 AI 完成技术决策 · 但 PMO 必 `state.py add-concern --severity WARN --message "auto skip: DB schema change · tables/fields/migrations: ..."` 留 audit(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

```markdown
⏸️ TECH 方案涉及数据库数据结构变更 · 请确认:

1. **确认 DB schema 变更方案 · 进入 dev** 💡 推荐
   理由:表结构改动经三角色评审 · 你认可即进开发
   动作:blueprint-complete → 自动转 dev
2. **调整 DB 方案** — 你对表结构/字段/迁移设计有异议 · RD 修订 TECH §数据模型
3. **其他指示**

📚 决策参考:TECH.md §数据模型
```

不涉及 DB 数据结构变更 → 跳过此步 · 直接 §8。

### 8. complete
`state.py blueprint-complete ...` · verify-ac.py 自动跑 · external-review artifact 校验

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | `project-specs/DEV-RULES.md`(若存在) | 全文 | 项目强制开发规范 · TECH 须遵守(+ 读 PRD/ARCHITECTURE/KNOWLEDGE) |
| 2. QA 起草 TC.md | `roles/qa.md + standards/tdd.md` | § TC 起草 + § BDD | Given/When/Then 风格 / AC↔Test 绑定 |
| 3. RD 起草 TECH.md | `roles/rd.md + standards/common.md` | § TECH 起草 | 模块/数据/接口/依赖/风险 5 段 |
| 4. Architect Tech Review → TECH-REVIEW.md | `roles/architect.md` | § Tech Review | 技术合理性 + 架构一致性 + **简洁性(防过度设计 · 拦在 TECH 比拦在代码便宜)** |
| 5. (可选)QA TC Review | `roles/qa.md` | § TC Review | TC 设计能否真验证 AC |
| 6. External cross-review | `roles/external-reviewer.md` | § 调用规范 | 异质模型只读评审 · OpenAI ToS |
| 7. PM 回应 + 修订循环 | `roles/pm.md` | § Review 反馈处理 | NEEDS_REVISION 主对话内闭环 |
| 8. complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:`verify-ac.py`(每 AC ↔ TC.md `tests[].covers_ac`) · P0-154(`external-cross-review/*.md` 非空)

**SOP**(违反 → review NEEDS_REVISION):
- TECH.md 写"方案"(选型 / 接口 / 数据结构)· 不写函数实现 · 代码细节归 dev stage
- Architect 默认主对话 review(保留 ADR / KNOWLEDGE 上下文)· 不走 Subagent(白板效应)
- NEEDS_REVISION 主对话内 PM 闭环修订 · 不打扰用户(R5 + fix-retry 规范)

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - TC.md → `{SKILL_ROOT}/templates/tc.md`(含 frontmatter + tests[].covers_ac BDD 示例)
> - TECH.md → `{SKILL_ROOT}/templates/tech.md`(含 5 段:模块/数据/接口/依赖/风险)
> - TECH-REVIEW.md → 无独立模板 · 见下方 schema · 按评审角色 finding 分段
> - external-cross-review/*.md → 跑 `state.py external-review --feature ... --stage blueprint`(自动落产物 · 不要手写)
>
> 🤖 **校验脚本**:`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}` ·
> blueprint-complete 自动跑 · 校验 PRD 每条 AC 在 TC.md `tests[].covers_ac` 至少 1 个引用 · 漏覆盖 FAIL。

### `TC.md`
frontmatter `tests: [...]` · AC↔Test 一一绑定 · BDD Given/When/Then

### `TECH.md`
§模块 / §数据 / §接口 / §依赖 / §风险

### `TECH-REVIEW.md`
frontmatter `reviewers`(复数列表 · 含 blueprint 全部评审角色)+ `verdict` · 三视角 finding 汇总

### `external-cross-review/*.md`
异质模型 review · 至少 1 份

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BLUEPRINT_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
