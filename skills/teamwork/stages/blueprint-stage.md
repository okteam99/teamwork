# Blueprint Stage

> **auto-verified by**: `state.py blueprint-start` / `state.py blueprint-complete`
> 本文件按 **怎么做 + 注意事项** 结构(v8.0+P0-7)。
> 详细 schema 见 [../docs/v8-redesign/01-COMMAND-SCHEMA.md](../docs/v8-redesign/01-COMMAND-SCHEMA.md)。

---

## 怎么做

### 1. 加载上下文
读 PRD.md(权威需求)· ARCHITECTURE.md(系统架构)· KNOWLEDGE.md · standards/tdd.md

### 2. QA 起草 TC.md
BDD Given/When/Then · frontmatter `tests: [{id, covers_ac, description}]` · 每 AC 至少 1 test

### 3. RD 起草 TECH.md
§模块划分 · §数据模型 · §接口定义 · §依赖与影响 · §风险

### 4. Architect Tech Review → TECH-REVIEW.md
frontmatter `reviewer: architect` + `verdict` · 主对话默认(保留架构上下文)

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

### 坑 1 · AC↔Test 漏绑定
verify-ac.py 校验 FAIL(物化拦截)· blueprint-complete 失败。
  **对策**:每 AC 在 TC.md frontmatter.tests[].covers_ac 显式 cite · 不漏

### 坑 2 · External cross-review 漏
`external-cross-review/*.md` 为空 → P0-154 物化 FAIL。
  **对策**:必跑异质模型一次 · 落 markdown · 即使内容简短也算

### 坑 3 · TECH.md 写代码细节
代码细节属 dev stage · TECH.md 应写"方案"。
  **对策**:TECH 描述选型 / 接口 / 数据结构 · 不写函数实现

### 坑 4 · Architect 走 Subagent 失去架构上下文
架构师视角依赖累积上下文 · Subagent 是"白板"。
  **对策**:Architect 默认主对话 review · 保留之前 ADR / KNOWLEDGE 等上下文

### 坑 5 · NEEDS_REVISION 抛用户拍板
违 R5 暂停点协议 · 用户被反复打扰。
  **对策**:NEEDS_REVISION 在主对话内 PM 回应 + 修订 · 直到全 APPROVE · 才到 Substep 8 complete

---

## Output Contract(产物形态参考)

### `TC.md`
frontmatter `tests: [...]` · AC↔Test 一一绑定 · BDD Given/When/Then

### `TECH.md`
§模块 / §数据 / §接口 / §依赖 / §风险

### `TECH-REVIEW.md`
frontmatter `reviewer + verdict` · 架构师 finding

### `external-cross-review/*.md`
异质模型 review · 至少 1 份

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BLUEPRINT_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
