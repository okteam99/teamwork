# Test Stage

> **auto-verified by**: `state.py test-start` / `state.py test-complete`
> 本文件按 **怎么做 + 注意事项** 结构(v8.0+P0-7)。
> 详细 schema 见 [../docs/v8-redesign/01-COMMAND-SCHEMA.md](../docs/v8-redesign/01-COMMAND-SCHEMA.md)。

---

## 怎么做

### 1. 加载上下文
读 PRD.AC · TC.md · 实际代码 · dev 阶段 commit

### 2. QA 起草集成测试
基于 TC.md 测试用例 · 跨模块集成场景

### 3. QA 起草 API E2E
端到端 API 调用脚本 · 落 `{Feature}/e2e/*.py`(或语言对应)

### 4. 跑测试
集成测试 + API E2E 双 exit-code=0

### 5. 跑 verify-ac.py
AC↔Test 全覆盖物化校验 · 漏覆盖 FAIL

### 6. 起草 TEST-REPORT.md
§集成测试结果 / §API E2E 结果 / §AC 覆盖度 / §回归测试

### 7. complete
`state.py test-complete --integration-test-exit-code 0 --e2e-test-exit-code 0 ...`

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | — | — | (读 PRD.AC + TC.md + 代码) |
| 2. QA 起草集成测试 | `roles/qa.md + standards/backend.md` | § 集成测试 | 跨模块场景 / 不是单测复刻 |
| 3. QA API E2E | `roles/qa.md + standards/frontend.md` | § E2E 测试 | 落 e2e/* · 语言无关 · 可重跑 |
| 4. 跑测试 | — | — | (无) |
| 5. 跑 verify-ac.py | — | — | (物化校验 · 无 spec cite) |
| 6. 起草 TEST-REPORT.md | — | — | (无) |
| 7. complete | — | — | (无) |


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

### 坑 1 · 测试失败标 xfail/skip 走捷径
为 exit-code=0 跳过失败 test · 实际功能未实现。
  **对策**:失败必修 · skip 必含 reason + tracking issue · 不绕过

### 坑 2 · AC 全覆盖漏
verify-ac.py FAIL(物化拦截)。
  **对策**:每 AC 至少 1 集成测试或 E2E · TC.md frontmatter.tests[].covers_ac 显式 cite

### 坑 3 · E2E 脚本不可重跑
一次性 hack · CI 不能复用。
  **对策**:e2e/*.py 独立可执行 · 不依赖 dev 主对话上下文

### 坑 4 · TEST-REPORT 口述"通过"
不引用实际 exit-code / stdout · 失去 audit。
  **对策**:TEST-REPORT 含具体测试 stdout 摘录 + exit-code 数值

### 坑 5 · 集成测试 = 单元测试
集成测试应跨模块 · 跨服务 · 不是单测复刻。
  **对策**:集成测试聚焦"模块间接口契约" · 与 dev 的单测分工

---

## Output Contract(产物形态参考)

### `TEST-REPORT.md`
§集成 / §E2E / §AC 覆盖 / §回归

### `e2e/*`
至少 1 文件 · 语言无关 · 可重跑

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `TEST_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
