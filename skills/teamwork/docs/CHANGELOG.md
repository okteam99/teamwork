# Changelog

> 📦 本文件**保留最近 5 版**(发布时最旧一版迁入 [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md))。归档**定期清空**(v8.127 立制 · 完整历史 = git 提交历史 · 不在工作区热存)。
> 🔴 **发版三件套**(同 commit):本文件 entry(细节 · 易逝)+ [RETRO-LEDGER.md](./RETRO-LEDGER.md) 1 行(框架自省蒸馏 · 永久)+ 版本 bump。
> 🔴 **交付止于 push dev**(v8.143 用户拍板):发版**不** rsync 本机安装副本(`~/.agents/skills/teamwork`)—— 本机消费项目与其他机器同路:bootstrap 升级提示(channel 按各项目 `.teamwork_localconfig.json.update_channel` · 本机项目配 `dev`)→ 用户确认 → `update.py` tarball 覆盖。框架仓工作区 ≠ 交付渠道。

## v8.202 · 模板地址全 stage 到位:diagnose 补映射 + scaffold_hints 加「别抄旧」+ 4 brief 指针

> 用户:是否所有 start brief 都给模板地址?查实:`scaffold_hints`(v8.14)**早已**在 stage-start emit 绝对路径(10 stage 映射+validator)· 但 PRD 到达率 2/11 证明被忽略。真缺口三处。

### 改动
- **diagnose 补进 STAGE_TEMPLATES**(原漏:产 BUG-XXX.md 的 stage 反而 start 时不给 bug-report 模板)。
- **scaffold_hints 加 `usage` 警示**(单点 · 全 stage 生效):照绝对路径起草 · **别抄项目里同名旧产物**(旧文件 = 旧版模板快照 · 附到达率实测)。
- **4 个 brief 加统一指针**(blueprint_lite/test/browser_e2e/pm_acceptance):「📋 产物模板见 scaffold_hints.templates」—— 不在 brief 重复路径(防双源)· 只指向。

### 验证
- code(engine 映射+usage · specs 4 指针)· diagnose hints 冒烟 ✓ · pytest 809 passed。

## v8.201 · PRD canonical 到达率:goal brief 约束模板 + goal-complete 三命门校验

> 实测(v8.200 扩展区验证):post-v8.164 的 10 份 live PRD **仅 1 份**用 canonical 模板,其余自由结构/抄项目旧 PRD(同 WS-012 病根)—— 机读块/扩展区等新机制**到达不了**,加什么槽位都白加。

### 改动
- **goal brief 约束**(消费时点推):🔴 照 `templates/prd.md` 起草 · **别抄项目里旧 PRD**(附实测数据)。
- **goal-complete 校验**(`prd_template_conformance` evidence):只查**三个机读命门段**(不管字数/风格)—— `TEAMWORK-MACHINE` 机读块(或 legacy frontmatter)· 验收标准/AC(verify-ac 依赖)· 『开工前必须想清的』扩展区(可写「无」但段要在)· 缺 → FAIL + hint 指 canonical 模板。
- 测试 +3(自由结构拦三段 / canonical 放行 / legacy 缺扩展区仍拦)。

### 验证
- code(`_v8_stage_specs` check+接线+brief)· pytest 809 passed。

## v8.200 · 全模板加「🧩 补充洞察」自由区 · 模板是地板不是天花板

> 用户:模板是否可能限制模型能力?是否加一个 AI 自由发挥的补充板块(限制少 · 可留空)。判断:槽位不限能力 · 但「填完表=完成」的心智会 —— 模板外的重要发现(非常规风险/更好方案线索/跨 feature 影响)没处落就不会写。PRD 已有先例(v8.164 扩展区)· 推广到其余产物模板。

### 改动
- **tc / tech / ui / bug-report 四模板**统一加末段 `## 🧩 补充洞察(AI 自由发挥 · 可留空)`:模板槽位之外重要但没处落的 · 🔴 **地板不是天花板 · 填完槽位 ≠ 想完了** · 没有写「无」或删本节 · **不为凑内容而写**(防它自己变成新仪式)。
- PRD 不动(v8.164 `## 开工前必须想清的` 已是同物)。

### 验证
- doc-only(4 模板各 +5 行)· `test_v8_stage_specs` 90 passed。

## v8.199 · 删 P0-11 cite 纪律(A 全删)+ brief 全面性核查

> 精简讨论首刀(用户拍板 A):cite 纪律 = 每 substep 动手前引 spec 原文自证「真读」+ 切角色重 cite —— 每 feature 几十次仪式输出。163 条 audit **零实证**拦到任何东西 · `cited_specs` 字段**零消费**(写了没人收)· 它想治的病(AI 不读 spec)已被 v8.151 起「brief 消费时点主动推」+ gate 物化接管。**模型越聪明 · 过时仪式越忠实执行 = 越有害**。

### 改动
- **全删**:STAGES.md §2 定义(~25 行)· 11 个 stage 的「必读 cite 清单」表(~140 行)· 各处 📎 指针行 · `stage-complete --cite` 参数与 `cited_specs` 死字段。
- **brief 全面性核查**(cite 表删后 brief = 唯一消费时点推送):13 个 brief **全部**指回对应 stage 文件(导航不丢)· 关键 🔴 推送就位(dev 3 / diagnose 3 / goal 2 / ui_design 3…)· 补 1 处:`_blueprint_brief` 的 TECH 结果行从老五段更新为 v8.181-183 全结构(现状基线/错误处理/依赖影响/查询性能/完工自查)。
- 误删回滚:roles/ 3 行 v8.155 冷审规范(「cite」为普通引用义)· git checkout 恢复。

### 验证
- 净减 ~180 行 + 每 feature 几十次仪式输出归零 · pytest 806 passed。

## v8.198 · loops 对照两修:await-merge 30s 轮询(合并自动下一步)+ yolo fix-retry 10 轮止损

> 对照 claude.com「Getting Started with Loops」:teamwork 是 Turn-based 最佳实践重度实现 · 缺口在 Time-based(结构性等待窗无人看:132h 等合并长尾 · CI 红无人接)+ Goal-based 的 max-attempts(yolo「持续自主解决」无轮次上限 · runaway 风险)。

### 改动
- **`state.py await-merge`**(新 · time-based loop):ship1 / 规划收尾 emit 等合并提示后**跑它** —— 30s 轮询 MR 状态(gh/glab · `--interval/--max-checks` 可调)· **MERGED → emit 下一步**(ship-finalize / 规划 finalize)· WAITING → 重跑续等(用户随时打断改人工)· CLOSED → surface · 连续 3 次查询失败 → FAIL(环境)。`--feature`(读 state.ship.mr_url)或 `--mr-url` 直传(规划场景)。
- **yolo fix-retry 止损**(goal-based max-attempts):同 stage fix-retry **≥10 轮**未收敛 → 硬停 surface(`yolo_rounds_exceeded` 接进 `execute_stage_fix` · 真·硬停的合法扩展:收敛失败 ≠ 继续死磕)· 非 yolo 不受影响(既有「3 次问用户」协议)。
- ship-stage §5 / feature-planning 收尾-1 / SKILL yolo 表同步。

### 验证
- code(`_v8_ship` await-merge · `_v8_engine` 止损)+ doc ×3 · `test_loops_v8198` +4 · pytest 806 passed(基线三失败已由并行修复清零)。
