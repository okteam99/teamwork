# PROCESS-LEDGER 模板(流程价值台账)

> 位置:`project-specs/PROCESS-LEDGER.md`(workspace 级 · 与 DEV-RULES / KNOWLEDGE 同级)。
> **telos**:一行一 feature 的流程仪式价值数据 · 给「该不该砍某环节」提供查表依据。消费方:流程审视场景 + 年检 kill criteria(详 [stages/ship-stage.md §16](../stages/ship-stage.md))。
> 🔴 区别 `docs/retros/`(业务/工程复盘 · 子项目级 · 知识层):本表只度量 **teamwork 流程本身**的环节价值 · 别混写。
> 写入时机:🔴 **ship1 archive 的规划 gate**(worktree 内 append · state.json / REVIEW.md 就在工作树 · 路径加进 `--planning-artifacts` 随 feature MR 原子合入;digest 在 ship2(ship-finalize)完成后 emit)。漏写兜底:`unzip -p features/_archive/<id>.zip <id>/state.json` 取数补行。🔴 单元格 ≤1 行 · 机器字段照实抄 · **不美化**(过场就写过场)。

---

# 流程价值台账

> 查询示例(年检 / 流程审视时算):external confirmed 率 = Σ采 / Σ总;某角色真 finding 率 = 该角色 finding 数 / feature 数;暂停点 all-default 率 = Σ默 / Σ(改+默)。

| Feature | flow | 实走 stages | 时长(总·AI自主·待用户) | review/test 轮 | external 总/采/驳 | 角色真 finding | 暂停点 改:默 | bypass/WARN | 反思摘要(≤1 行) | 各阶段耗时 | 用户邮箱 | 宿主 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| <ID> | <Feature/Bug/敏捷/Micro> | <goal→blueprint→dev→…→ship> | <2.4h·AI 88m·待 32m> | <1/1> | <3/1/2> | <arch:1 qa:0 ext:1> | <1:2> | <0/0> | <external 拦 1 真问题 · ui_design 零 finding 过场> | <goal 20m(+等5m)·dev 40m·review 8m·pm_acceptance 30m> | <git user.email> | <claude-code/codex-cli/gemini-cli> |

> 🔴 **schema 演进纪律(v8.210)= 只在末尾加列** —— 新列一律追加到表**最右**(旧 feature 行天然是**有效前缀** · 新列它们为空 = 该 feature 早于该指标 · 诚实)· **永不在中间插列**(否则旧行错位、年检读错列)。**旧项目台账迁移 = 仅换表头一行**(旧数据行不动):append 前跑 `state.py ledger-migrate --feature <path>`(幂等 · header 已最新则 no-op)。
> 🔴 **时长三分(v8.208)**:`总` = 墙钟(init→archive · 不含 MR 等待)· `AI自主` = 扣掉所有人工等待后 AI 真跑的时长(Σ 工作 stage〔duration − stage 内 pause-mark 暂停〕)· `待用户` = 全部人工等待(stage 内暂停 + pm_acceptance 等纯等待 stage 墙钟)。**数据源 = ship1 archive emit 的 `ledger_timing`**(确定性 · 照抄不肉眼算)· `各阶段耗时`同源(`per_stage`)。
> 🔴 **用户邮箱** = `git config user.email`(archive emit `ledger_timing.user_email`)· 供年检按人/团队分析流程健康度。
> 🔴 **宿主(v8.209)** = AI 宿主类型 `claude-code` / `codex-cli` / `gemini-cli`(archive emit `ledger_timing.host` = `state.host`)· 供年检**按宿主对比流程质量**(如 external 采纳率 / 过场率 / AI 自主时长在 claude vs codex 上的差异)。
