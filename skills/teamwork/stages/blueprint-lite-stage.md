# Blueprint Lite Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md · KNOWLEDGE.md(轻量参考)

### 2. QA 起草 TC.md(精简版)
每 AC 至少 1 test · BDD 风格 · 砍 TECH/TECH-REVIEW/External(敏捷流程精简)

### 3. (可选)Architect 快速看一眼
不强制 TECH-REVIEW.md · 主对话内提醒即可

### 4. complete
`state.py blueprint_lite-complete ...`

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | — | — | (读 PRD) |
| 2. QA 起草 TC.md(精简版) | `roles/qa.md` | § TC 起草 | 精简版 · 每 AC 至少 1 test |
| 3. (可选)Architect 快速看 | `roles/architect.md` | § Quick Review | 不强制 TECH-REVIEW.md |
| 4. complete | — | — | (无) |


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:`allowed_flow_types=["敏捷需求"]`(flow_type 错 → start FAIL)

**准入硬约束**(违反 → 不应用敏捷 · `reset-prev` 回退改 flow_type=Feature 重做):
- ≤5 文件改动 · 无 UI 变更 · 无架构变更 · 方案明确

**SOP**:
- TC.md 精简但完整(每 AC ≥1 test) · 砍 blueprint 不砍质量(review/test 严格度不降)
- 重要决策边界 case · 主对话内 PMO 判定是否补 external 一次

---

## Output Contract(产物形态参考)

### `TC.md(精简版)`
frontmatter `tests: [{id, covers_ac}]` · 每 AC 至少 1 test · 不要求 TECH.md

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BLUEPRINT_LITE_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
