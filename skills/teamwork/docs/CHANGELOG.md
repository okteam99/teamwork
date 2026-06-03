# Changelog

> 📦 v8.89 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.90 · 单模型用户可禁异质评审(`disable_heterogeneous_review` · 默认开异质 · dev-only)

> 用户:只有一个模型(如 codex 环境下 claude 不可用/未登录/配额满)时,允许降级到当前模型 exec 自审;可在 `.teamwork_localconfig.json` 配置是否禁用异质,**默认关**(异质开);禁用时默认用 exec;每次 teamwork 启动 WARN 提醒交叉 review 质量下降、建议恢复异质。

### localconfig `disable_heterogeneous_review`(默认 false = 异质开)
- `true` → `external-review` **自动**用宿主自身模型 fresh exec 自审(无需 `--self-review-fallback`),落 `external-cross-review/<stage>-<model>.md`(**满足 P0-154** · 让单模型用户走完流程)· frontmatter 标 `heterogeneous:false degraded:true degraded_mode:config-disabled` + 正文 banner + 写 `concern WARN`。
- `_read_disable_heterogeneous_review`(state.py · 向上找 localconfig 到 `.git` 边界 · 默认 false)。
- 🔴 **review-complete 门禁配套**(否则单模型用户在 review-complete 仍被异质硬校验卡死 = 功能形同虚设):`_evidence_external_review_artifact`(`_v8_stage_specs.py`)在 `disable_heterogeneous_review:true` 时**接受** external-cross-review/ 里标 `degraded:true heterogeneous:false` 的降级自审 —— 但仍 **BLOCK 未标记 degraded 的同模型文件**(防手写伪装)· 异质项目(默认)的硬校验**不受影响**。

### 🔴 每次启动 WARN(bootstrap · 持续提醒)
- `bootstrap.py` 检测 `disable_heterogeneous_review:true` → `checks.heterogeneous_review.status=disabled` + warning · 并把一行 forewarn 提进 `pmo_must_read`(顶部 digest · 抗 `head` 截断)· PMO 须告知用户「已禁用异质 · 交叉 review 质量下降 · 建议装第二模型 CLI 后恢复」。

### 与 v8.88 self-review-fallback 的区分(两种降级)
- **v8.88 `--self-review-fallback`**(异质**暂时**不可用的临时 stopgap):落 `self-review/` · **不满足 P0-154** · 仍须修环境重跑或 `change-review-roles` 移除 external。
- **v8.90 `disable_heterogeneous_review`**(**项目级长期策略** · 单模型):落 `external-cross-review/` · **满足 P0-154** · 但被 startup WARN 持续提醒。
- emit `degraded_mode` 区分二者;`satisfies_p0_154` 分别 false / true。

### 验证
- live:config-disabled external-review → model=宿主自身 · 落 external-cross-review/(满足门禁);bootstrap → pmo_must_read 含「异质评审已禁用」+ checks.heterogeneous_review=disabled。
- pytest **3 failed / 472 passed**(baseline 3 = scan-spec 既有 · 零回归 · +2 测试:helper 默认/true · config-disabled 路由)。
- spec:standards/external-model-usage.md §11(单模型 opt-out)+ localconfig 模板/config.md 文档化。
