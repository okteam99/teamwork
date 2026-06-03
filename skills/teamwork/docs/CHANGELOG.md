# Changelog

> 📦 v8.90 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.91 · bootstrap 启动自愈 localconfig schema(缺字段补默认值 · dev-only)

> 用户:bootstrap.py 启动时检查 `.teamwork_localconfig.json`,`_bootstrap` 段字段不足的要补上默认值。

### `ensure_localconfig_complete`(bootstrap.py · 每次启动跑)
- **治本**:localconfig 由老版 bootstrap / 手建 / 部分写入时,`_bootstrap` 子键(`skill_version`/`host`/`last_maintain_at`/`last_maintain_results`)或**新增 feature 开关**(`archive_on_ship`/`local_env_auto_create`/`disable_heterogeneous_review`/`id_strategy`)缺失;且**版本命中 `skip_maintain` 时这些缺口永不补**(`write_bootstrap_marker` 只在 maintain 跑时重写 `_bootstrap`,且从不补新 config 键)→ 用户也看不到新选项。
- **行为**:补全 `_bootstrap` 4 子键 + 所有已知顶层 config 键的默认值。🔴 **additive only · 绝不覆盖**用户已有值(含显式 false/null);只在**已存在**的 localconfig 上跑(不存在 = 冷启动,由 prepare/maintain 创建,不在此凭空造);**无变化不写盘**(防 churn);skill 仓自身 skip。
- **接线**:跑在 maintain 之后(无论 skip 与否),覆盖 `skip_maintain` 缺口;结果落 `result.localconfig_backfill`(audit)。
- **默认源**:`LOCALCONFIG_CONFIG_DEFAULTS` + `LOCALCONFIG_BOOTSTRAP_DEFAULTS`(🔴 与 `templates/teamwork_localconfig.json` 保持同步,新增字段两处都加)。

### 验证
- live:incomplete(缺 `_bootstrap` + 新开关)→ backfilled 且用户值(merge_target=dev/worktree=off)保留;complete → `status:complete` 不写盘;absent → skip 不创建;部分 `_bootstrap` 子键 → 只补缺的。
- pytest **3 failed / 480 passed**(baseline 3 = scan-spec 既有 · 零回归 · +5 测试:补全保留用户值 / 部分 `_bootstrap` 补缺 / complete 不写 / absent 不建 / skill_root skip)。
