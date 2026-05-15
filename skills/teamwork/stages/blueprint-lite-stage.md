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


**输出格式**(每个 substep 动手前必在主对话输出):
```
📖 cite:
- <spec> § <段>:"<引该段 1 句关键原文 · 证明真读>"
```

**强约束**(R5+P0-11 软约束 · 用户监督):
- 标 "—" 的 substep 无 cite 要求(状态机操作 / 用户暂停 / 已物化)
- 其余 substep **动手前必输出 cite 块** · 缺 cite 视为 process 违规(用户可叫停)
- cite 必含 § 段标题 + 至少 1 句原文(原文必真实存在于该 spec · 不可瞎编)
- AI 在 stage 内多次切角色 · 每次切换前重新 cite 该角色规范

**为什么 cite**:
- brief 列路径(P0-4)只解决"AI 找不到路径"· 不保证 AI 真读
- complete 时校验太晚(AI 已做完)
- substep 动手前 cite = 事前提醒 · 强制 AI 翻一眼 spec
- 物化死角(state.py 看不到 markdown Read 动作)· 软约束 + 用户监督兜底

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
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
