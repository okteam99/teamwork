# Browser E2E Stage

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


📎 **cite 纪律**(输出格式 / 强约束 / 为什么 cite)· 单源详 [../STAGES.md § 2 P0-11 cite 纪律](../STAGES.md)

## 质量基线

📎 **物化拦截**:`execution_hints.browser_e2e_needed`(state.py auto_transition_fn 按字段判定 · 不强制必跑)

**截图 SOP**(违反 → audit FAIL):
- 每 AC 一组截图 · 含 happy path + ≥1 边界
- 截图含浏览器 chrome + URL bar(不裁剪)· 看得出 viewport / URL
- 模式与 PRD 场景一致(桌面用户 → 有头 desktop viewport)

**flaky 处理**:retry 必含 log + 失败截图 · 不静默成功

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
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
