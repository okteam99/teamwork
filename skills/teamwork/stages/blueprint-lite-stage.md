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

## 注意事项

### 坑 1 · 敏捷需求准入不符
改动 > 5 文件 / 有 UI 变更 / 方案不明 → 不应是敏捷需求。
 **对策**:发现复杂度超预期 → `state.py reset-prev` 回退 · 改 flow_type 到 Feature · 重做

### 坑 2 · 砍 blueprint 不等于砍质量
TC.md 仍要 AC↔Test 绑定 · review/test stage 严格度不降。
 **对策**:TC 精简但完整 · 每 AC 至少 1 test

### 坑 3 · 误用 flow_type
flow_type=Feature 错跑 blueprint_lite-start → 物化 FAIL(allowed_flow_types=["敏捷需求"])。
 **对策**:init-feature 时正确选 flow_type · 不混用

### 坑 4 · Feature 流程降级敏捷
为省事跳过完整 blueprint · 实际是 Feature 复杂度。
 **对策**:准入硬约束(≤5 文件 / 无 UI/架构变更 / 方案明确)· 不满足绝不用敏捷

### 坑 5 · External 完全跳过
即使敏捷 · 重要决策仍建议 external 一次。
 **对策**:复杂度边界 case · 主对话内 PMO 判定是否补 external

---

## Output Contract(产物形态参考)

### `TC.md(精简版)`
frontmatter `tests: [{id, covers_ac}]` · 每 AC 至少 1 test · 不要求 TECH.md

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BLUEPRINT_LITE_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
