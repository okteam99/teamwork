# PM Acceptance Stage

> 🧭 四段结构

---

## ① 目标(telos)

**产品视角验收**:PM 站在用户视角逐条核对 PRD 的 AC 是否真的达成(以 TEST-REPORT.md 实际数据为准,不凭印象),并把"要不要发布"这个产品决策显式交还用户拍板——AI 只验证事实、不替用户做发布决定。拦的风险:AC 没真过就放行、验收结论靠"看起来 OK"口述、发布与否被 AI 越俎代庖决定。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **AC 核对必须以实证为准**:PM 逐条对照 `TEST-REPORT.md` 的实际数据(通过 / 失败 / 截图)判断,不得凭"看起来 OK"口述(why:验收是发布前最后一道质量闸,凭印象过 = 闸形同虚设)。
2. **验收决策(`approved_and_ship` / `approved_no_ship` / `rejected_with_feedback`)只能用户拍板,AI 不可自决**:emit 三选项 R5 暂停点后必须停等用户回 1/2/3——哪怕选看起来"保守"的 `approved_no_ship` 也是越权(它让 Feature 跳过 ship 直接 completed,和继续推进一样是重大决策);"避免未授权 push"不构成自选 `approved_no_ship` 的理由,`approved_and_ship` 进 ship 后 Phase 1 仍有"等用户在平台合并"暂停点,push/merge 不会自动发生;`approved_no_ship` 仅用于真"完成但等时机"(协同其他 Feature),不得用作躲避决策的挡箭牌。🔴 **`auto_mode=true` 也必停此暂停点**——auto 只跳过技术 / 设计 / 评审类暂停点,产品决策权是用户专属(why:AI 自决 decision = 同时违 R5〔用户决策点〕与 R3〔用户决策被 AI 代替〕)。🔴 **唯一例外 = `yolo`**(用户启动时的 blanket 委托):自动 `approved_and_ship` + `add-concern WARN` 留痕 · **AC 对照照做不跳**(单源 SKILL § yolo 表 · stage-start brief 已按 `state.yolo` 物化);但**外部世界动作**(公网发布 / 建公开仓 / 生产部署)不在自动范围——合入清场后**单独停给用户**(详 [SKILL § yolo 外部世界动作边界](../SKILL.md))。
3. **`rejected_with_feedback` 必传 `--note`**(state.py 强校验,缺失报错):note 须含具体改什么(finding 明确)(why:拒绝没有具体意见 = 下一轮不知道改哪,反馈类暂停点存在的意义就是留下可执行的意见)。
4. **`decision=approved_and_ship` 是 ship-start 前置门禁**(ship-start 校验 `pm_acceptance.evidence.decision` 必为此值,否则 FAIL)(why:防止绕过 PM 验收直接 ship——验收决策是进 ship 的唯一合法入场券)。

---

## ③ 建议手段菜单(AI 按本 feature 自选 · 不强制)

| 手段 | 何时值得 |
|---|---|
| **主对话本地试跑关键路径** | 可本地起服务 / 跑通关键路径时 → 加强验收真实感;截图 / TEST-REPORT 证据已充分时可省 |

---

## ④ Output Contract(产物契约 · 机读)

### 上下文入口(读什么)
`PRD.md`(§验收标准 AC)· `TEST-REPORT.md` · `screenshots/*.png`(若 browser_e2e 启用)。主对话身份切换至 PM · 站在用户视角核对。

### 决策与 complete
```
state.py pm_acceptance-complete --feature <path> \
  --decision <approved_and_ship|approved_no_ship|rejected_with_feedback> \
  [--note "<具体改什么>"]
```
- `rejected_with_feedback` 时 `--note` 必填(state.py 强校验)
- `approved_and_ship` → 自动转 `ship`(ship-start 前置校验 `pm_acceptance.evidence.decision=approved_and_ship`,非此值 FAIL)
- `approved_no_ship` → 自动转 `completed`(不 ship)
- `rejected_with_feedback` → 留 `pm_acceptance` · state.py emit `pause_options_markdown` 4 选项(见下)

### ⏸️ R5 暂停点(验收决策 · 三选项 · 必用户拍板)
```markdown
⏸️ PM 验收完成 · AC <N/N> 通过 · 请你拍板:

1. **approved_and_ship** 💡 推荐(若 AC 全过且可发布)
   理由:<1 句> · 动作:进 ship stage(push 分支 + 建 MR · Phase 1 仍有"等你平台合并"暂停点)
2. **approved_no_ship**
   理由:完成但暂不发(等协同 / 等时机)· 动作:Feature 直接 completed · 不 ship
3. **rejected_with_feedback**
   理由:你发现需返工的问题 · 动作:带 feedback 回退(见 §回退选项)
```

### 回退选项(rejected_with_feedback · 用户选 1-4)
不强制 stage 内 fix-retry(PM 反馈类型多样:代码 / 需求 / 设计 / 放弃,非单一"改代码"性质)· state.py emit 4 选项:
```
1. 代码 bug → state.py reset-prev → dev-fix → review → test → pm_acceptance 完整重走
2. AC / 需求改 → state.py jump-to-stage --to goal --reason "..." → 改 PRD + 重 review
3. UI 设计改 → state.py jump-to-stage --to ui_design --reason "..." → 改 UI
4. 放弃 Feature → state.py ship-phase --action close-unmerged --abandon=true
```
选 2 / 3 的 `jump-to-stage` 自动写 concerns WARN 留痕(audit 可查 · 不算 R5 红线违规)。

### (可选)`PM-NOTE.md`
`{SKILL_ROOT}/templates/pm-note.md` · 含 AC 逐条对照 + 三选项决策 + rejected finding 列表。决策落库 `state.json` 的 `stage_contracts.pm_acceptance.evidence.decision`,无强制文件模板。

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `PM_ACCEPTANCE_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
