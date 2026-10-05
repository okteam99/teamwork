# PM Acceptance Stage

> 🧭 四段结构

---

## ① 目标(telos)

**产品视角验收**:PM 站在用户视角逐条核对 PRD 的 AC 是否真的达成(以 TEST-REPORT.md 实际数据为准,不凭印象),并把"要不要发布"这个产品决策显式交还用户拍板——AI 只验证事实、不替用户做发布决定。拦的风险:AC 没真过就放行、验收结论靠"看起来 OK"口述、发布与否被 AI 越俎代庖决定。

---

## ② 硬规则(白名单 · 每条一行 why)

1. **AC 核对必须以实证为准**:PM 逐条对照 `TEST-REPORT.md` 的实际数据(通过 / 失败 / 截图)判断,不得凭"看起来 OK"口述(why:验收是发布前最后一道质量闸,凭印象过 = 闸形同虚设)。
2. **AC 全过 → 不在此停 · 验收拍板并入 ship1 MR**(年检):AI 以 `--decision approved_and_ship --note "AC N/N 通过 · 用户拍板并入 ship1 MR"` complete,验收结论写进 ship1 MR 卡片的「✅ 验收」段;用户**点合并 = 验收通过并发布**,要改回「要改 <问题>」、不发回「撤回」(详 [ship-stage §5](./ship-stage.md))(why:台账 325 行 `rejected_with_feedback` 0 次,而每个 Feature 都在这里停一次、累计等待 ~10k 分钟 —— 用户在 ship1 本来就要看 MR 再合并,两次停是同一个发布决定拍两遍;**拍板权没变,只是合成一次**)。
   **AC 没过 / 有阻塞问题 / 有需要用户拍板的产品取舍** → **照旧停三选项**,只能用户拍板,AI 不可自决:不许自选 `approved_*` 硬过,也不许自选 `approved_no_ship` 躲决策(它让 Feature 跳过 ship 直接 completed);`approved_no_ship` 仅用于真「完成但等时机」。🔴 **`auto_mode=true` 也照停**(产品决策权是用户专属 · 违 R5/R3)。🔴 **唯一例外 = `yolo`**:AC 全过自动 `approved_and_ship` + `add-concern WARN` · AC 没过自动 `rejected_with_feedback` 回修(单源 SKILL § yolo 表);**外部世界动作**(公网发布 / 建公开仓 / 生产部署)合入清场后**单独停给用户**(详 [SKILL § yolo 外部世界动作边界](../SKILL.md))。
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

### ⏸️ R5 暂停点(条件 · 仅 AC 没过 / 有阻塞 / 有产品取舍时 · 三选项 · 必用户拍板)
AC 全过 → 不 emit 本暂停点 · 直接 `--decision approved_and_ship` complete · 验收结论随 ship1 MR 卡片给用户(见规则 2)。
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
