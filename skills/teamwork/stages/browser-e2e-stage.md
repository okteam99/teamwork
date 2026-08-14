# Browser E2E Stage

> 🧭 **四段结构**(标准 · 详 [STAGES.md §3](../STAGES.md)):目标 + 硬规则白名单 + 手段菜单 + 产物契约 · 手段 AI 自选。

---

## ① 目标(telos)

**用真实浏览器证明「用户真能走通」**:关键路径在真实渲染环境下跑通,并留下**用户自己能看懂的视觉证据**(截图)。拦的风险:单测/接口测全绿但真实页面点不动、跨浏览器渲染塌、flaky 被静默成功糊弄过去。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **截图含浏览器 chrome + URL bar · 不裁剪**(why:裁掉就看不出 viewport / 真实 URL —— 证据可被「本地随便截一张」冒充)。
2. **每 AC 一组截图 · 含 happy path + ≥1 边界**(why:只截成功路径 = 没验边界 · 用户验收时看不到失败态长什么样)。
3. **模式与 PRD 场景一致**(桌面用户 → 有头 desktop viewport)(why:用移动 viewport 截桌面功能 = 证据与需求错位)。
4. **flaky 必留证据**:retry 必含 log + 失败截图 · **不静默成功**(why:静默重试把不稳定当通过 = 把线上问题藏进绿灯)。
5. ⏸️ **用户看截图确认(R5 暂停点)** · `auto_mode=true` 时跳过(截图已入 evidence · auto 用户已接受)(why:视觉验收是用户主权 · AI 判断不了「看着对不对」)。
6. 🔴 **关键路径必留可重放脚本**(用户拍板 · 工具**优先 Playwright** · 项目已有其他 e2e 基建则复用〔一致性优先〕):判据 —— **这条 browser 验证在交付后还需要重跑吗(回归 / CI)?** 需要 → 必须是可重放脚本(进 repo + TC 注册 · 按测试生命周期属 **L2 回归层**,`ci_reason` 立得住才进 L1);只是本次验收看一眼 → 截图即可(脚手架性探索落 scratch)(why:**AI 手点一次的验证不可重放** —— 代码一改,那组截图证明不了新代码,与「测试证据必须对应当前代码状态」同一机理;只点名工具不约束产物,AI 用 playwright MCP 手点也算「用了 Playwright」,可重放性才是本条的实质)。
7. 🎚️ **默认派验证档 subagent 执行**(本 stage 属验证类白名单 · 档位单源 [agents/README §一](../agents/README.md)):执行测试 / 截图 / 报告 = 校验型;主对话模型是用户主权不可切,**降档只有派 subagent 显式传 model 一条路**(prompt 首行 `Meta: tier=验证 · model=… · 理由=…`);**例外 🔴 不许 AI 自决 · 开 R5 请用户授权**(典型:首份可重放脚本要逆向真进程启动配方 = 探索+调试占主体);宿主不支持 subagent → 主对话串行 + `⚠️ WARN [degradation-fallback]`(why:白名单立在派发方规则里,执行入口不复述档位 = 对没带全局 context 的执行路径不存在 —— 默认继承会话主模型手点,常费而不自知)。

---

## ③ 建议手段菜单(AI 自选 · 不强制)

| 手段 | 何时值得 |
|---|---|
| **Playwright(默认首选 · 用户拍板)** | 无既有 e2e 基建时一律用它;已有 Puppeteer / Selenium / Cypress 基建则**复用**(同仓两套 e2e 栈 = 维护双份 · 一致性优先) |
| 全景预览对照(panorama_medium / panorama_path) | ui_design 出过设计稿 → 截图与设计并排比意图四要素 |
| 实际部署 URL vs 本地 dev server | 有可访问部署环境时优先真实环境(更接近用户) |

---

## ④ Output Contract

- **`screenshots/*.png`**:关键路径截图 · 至少 1 张 · 每 AC 一组
- **`BROWSER-TEST-REPORT.md`**:§测试场景 + §截图引用 + §异常发现 · 模板 `{SKILL_ROOT}/templates/browser-test-report.md`(含 AC↔截图矩阵 / flaky retry 处理 / `replay_entry` 重放入口)
- **可重放脚本**(硬规则 6 命中「交付后还需重跑」时):落项目 e2e 目录(如 `tests/e2e/browser/`)· TC `tests[]` 注册(level: fe-e2e)· 报告 frontmatter `replay_entry` 记一条可直接跑的重放命令(探索性/一次性验收填 `n/a`)。**不设机器门** —— 「关键与否」是判断题(载体承载:`replay_entry` 空着即可见)。

📎 **物化拦截**:`execution_hints.browser_e2e_needed`(state.py `auto_transition_fn` 按字段判定 · 本 stage 不强制必跑)。

⏸️ 暂停点选项(R5 标准 1/2/3 格式见 [SKILL.md § R5(b)](../SKILL.md)):
1. **确认 · 进入 pm_acceptance** 💡 推荐 — `browser_e2e-complete` → 自动转 pm_acceptance
2. **截图有问题 · 重测** — 按用户指出的异常重跑
3. **其他指示**

```
state.py browser_e2e-complete --auto-commit ... --artifacts screenshots/,BROWSER-TEST-REPORT.md
```

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BROWSER_E2E_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
