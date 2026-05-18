# Blueprint Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md(权威需求)· ARCHITECTURE.md(系统架构)· KNOWLEDGE.md · standards/tdd.md

### 2. QA 起草 TC.md
BDD Given/When/Then · frontmatter `tests: [{id, covers_ac, description}]` · 每 AC 至少 1 test

### 3. RD 起草 TECH.md
§模块划分 · §数据模型 · §接口定义 · §依赖与影响 · §风险

### 4. Architect Tech Review → TECH-REVIEW.md
frontmatter `reviewers: [qa, architect, external]` + `verdict` · 主对话默认(保留架构上下文)
🔴 frontmatter 字段名是 `reviewers`(复数列表)· 必含 `state.stage_review_roles[blueprint]` 全部角色(reviewers_match evidence 校验)

### 5. (可选)QA TC Review
复杂 Feature 启用 · 简单跳过

### 6. External cross-review
异质模型(codex / claude / gemini)独立 review → `{artifact_root}/external-cross-review/*.md`(至少 1 份)

### 7. PM 回应 + 修订循环
NEEDS_REVISION 时主对话内闭环 · 不打扰用户

### 8. complete
`state.py blueprint-complete ...` · verify-ac.py 自动跑 · external-review artifact 校验

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | — | — | (读 PRD/ARCHITECTURE · 无 spec cite) |
| 2. QA 起草 TC.md | `roles/qa.md + standards/tdd.md` | § TC 起草 + § BDD | Given/When/Then 风格 / AC↔Test 绑定 |
| 3. RD 起草 TECH.md | `roles/rd.md + standards/common.md` | § TECH 起草 | 模块/数据/接口/依赖/风险 5 段 |
| 4. Architect Tech Review → TECH-REVIEW.md | `roles/architect.md` | § Tech Review | 技术合理性 + 架构一致性 |
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
