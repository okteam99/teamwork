# 流程质量审计回收（`~/.teamwork/audit/`）

> **telos**：框架层面跨项目搜集流程质量。每个 consuming 项目 ship2（`ship-finalize` PASS）后 · 工具静默落一份 `<feature_id>.md` 到 **`~/.teamwork/audit/`**（本机所有项目共享的回收点 · env `TEAMWORK_AUDIT_DIR` 可覆盖〔测试用〕）· AI 静默补三段判断。框架改进 session harvest 这里 → 蒸馏进 [RETRO-LEDGER.md](../RETRO-LEDGER.md)。

## 一份审计记录含什么
- **实际数据**（工具确定性抽 · 不可幻觉 · 喂 kill-criteria 决策）：来源项目 / flow / 实走 stages / 总时长 / **各阶段耗时**（stage_contracts.duration_minutes）/ **耗时分析**（🔴 工作阶段总和 + 最耗时**工作**阶段% · pm_acceptance 等用户决策等待墙钟单列不计入最耗时 · 与总时长差 = 阶段间等待）/ **主对话 host + 模型**（model 由 PMO ship-finalize `--main-model` 声明 · 缺省只记 host）/ concerns / bypass · 细数据指向该项目 `PROCESS-LEDGER.md` 行。
- **做的好的 / 发现的问题 / 待优化的**（AI 静默填 · 照实抄 REVIEW.md·state · 空写「无」）：`发现的问题` 段 = 框架级 bug / 工具判例的回收口（取代旧易逝 digest 的「建议反馈 teamwork」行）。

## 为什么落 `~/.teamwork/audit/` 而非项目 / 框架仓
- **项目侧**（`project-specs/PROCESS-LEDGER.md`）= 项目自己的流程数据（per-feature · 项目年检用）。
- **框架仓**（`docs/RETRO-LEDGER.md`）= 框架自省蒸馏（per-version · 永久 · 发版时写）。
- **`~/.teamwork/audit/`**（安装目录之外 · 非 git）= 两者之间缺失的 rollup 回收层：跨项目原始审计 · 待框架 harvest。consuming 项目**不自改框架 spec** · 只往这里投递 · 框架来取。与 backups / prepare_check_audit 同域（`~/.teamwork`）· 运行时数据不落 skill 安装目录。

## harvest（框架改进 session）
- 读 `~/.teamwork/audit/` 全部 `*.md` · 按 `source_project` / `flow_type` 聚合；旧回收点（skill 安装目录 `docs/audit/`）可能残留历史审计文件 · **harvest 时两处都看**；
- 算三指标：external 采纳率 · 各角色真 finding 率 · 暂停点干预率（细数据回到各项目 PROCESS-LEDGER）；
- 收集 `发现的问题` 段的框架级判例 → 决定是否立项改进 → 蒸馏一行进 RETRO-LEDGER；
- 已 harvest 的可删（原文 git 不存 · 是 transient 回收料 · 同 `~/.teamwork/external-review-logs/`）。

🔴 运行时 `<feature_id>.md` 文件 **git 不跟踪**（框架仓 docs/audit/ 仅本 README 入库）· 它们是本机 transient 回收料。**抗覆盖依据**：落点在 skill 安装目录**之外**（`~/.teamwork/audit/` · update.py 只对账安装目录）；旧位置（安装目录 `docs/audit/`）的历史遗留由 update.py 对账豁免白名单（`RECONCILE_EXEMPT_PREFIXES`）保护 · 不会被当幽灵文件删除。
