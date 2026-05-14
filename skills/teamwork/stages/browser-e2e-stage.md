# Browser E2E Stage

> **auto-verified by**: `state.py browser_e2e-start` / `state.py browser_e2e-complete`
> 本文件按 **怎么做 + 注意事项** 结构(v8.0+P0-7)。
> 详细 schema 见 [../docs/v8-redesign/01-COMMAND-SCHEMA.md](../docs/v8-redesign/01-COMMAND-SCHEMA.md)。

---

## 怎么做

### 1. 加载上下文
读 UI.md / preview/*.html / 实际部署 URL

### 2. 选浏览器自动化
Playwright / Puppeteer / Selenium(项目栈决定)

### 3. 编写脚本 + 截图
每 AC 关键路径截图(login → 主流程 → 边界) · 落 `screenshots/*.png`

### 4. 起草 BROWSER-TEST-REPORT.md
§测试场景 + §截图引用 + §异常发现

### 5. ⏸️ 用户看截图确认
给用户截图 URL · 等确认

### 6. complete
`state.py browser_e2e-complete --auto-commit ... --artifacts screenshots/,BROWSER-TEST-REPORT.md`

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | — | — | (读 UI.md / preview / 部署 URL) |
| 2. 选浏览器自动化 | `roles/qa.md` | § E2E 选型 | Playwright / Puppeteer / Selenium |
| 3. 编写脚本 + 截图 | `roles/qa.md + roles/designer.md` | § 截图规范 | 每 AC 一组截图 · 含 viewport + URL |
| 4. 起草 BROWSER-TEST-REPORT.md | — | — | (无) |
| 5. ⏸️ 用户看截图确认 | — | — | (无) |
| 6. complete | — | — | (无) |


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

### 坑 1 · 截图覆盖不全
只截首页 · 关键交互漏。
  **对策**:每 AC 一组截图 · 含 happy path + 至少 1 边界

### 坑 2 · 截图无浏览器信息
看不出 viewport / URL · audit 失败。
  **对策**:截图含浏览器 chrome 边框 + URL bar(不裁剪)

### 坑 3 · 失败静默忽略
flaky test 重跑通过 · 不记录。
  **对策**:retry 必含 retry log + 失败截图 · 不静默成功

### 坑 4 · headless vs 有头模式差异
headless 截图与用户实际看到不一致。
  **对策**:与 PRD 描述场景一致(若 PRD 描述桌面用户 → 有头 desktop viewport)

### 坑 5 · 误把 browser_e2e 当必跑
本是可选 stage · execution_hints.browser_e2e_needed 决定。
  **对策**:state.py auto_transition_fn 按字段判定 · 不强制启用

---

## Output Contract(产物形态参考)

### `screenshots/*.png`
关键路径截图 · 至少 1 张 · 每 AC 一组

### `BROWSER-TEST-REPORT.md`
§测试场景 + §截图引用 + §异常发现

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BROWSER_E2E_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
