# Changelog

> 📦 v8.78 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.79 · artifact ID 默认改 UTC 时间戳号段(治本多机并行撞号 · ⚠️ 默认行为变更 · 用户拍板 · dev-only)

> 用户提案 2026-06-02:artifact ID 顺序号 `max+1`(扫本地目录取 max)在多 clone/多 agent 并行下必然 race —— AON 实测 324 feature 中 **13 组撞号**(2 组活跃)。同项目 DB migration 版本号早已同因改时间戳。用户拍板:**默认改新规则**(非 opt-in)。

### ⚠️ 默认行为变更(全体 teamwork 项目)
- **新建 feature 的 ID 号段默认 = UTC0 秒级时间戳 `YYMMDDHHMMSS`(12 位)**,如 `SVC-PLATFORM-F260601143012-Offer-Ranking`。
- 要回旧顺序号(`PTR-F045`):`.teamwork_localconfig.json` 设 `id_strategy: sequential` **opt-out**。
- **存量 ID 不重编号**(改 ship 过的目录会断 git/ROADMAP 引用)· 新旧天然可区分(3-4 位 vs 12 位)· migration 版本号格式不动。

### 根因 + 两层互补修复
- 根因:密集顺序号 + 分布式分配 = 必然 race(无原子中心分配器)。
- **timestamp 策略**(默认):各机各自生成不同秒 → 跨 clone 免协调防撞(根治)。
- **撞号硬校验**(R0 物化):`init-feature` 目标号段被**另一**目录占用 → FAIL · 兜**同 clone** race(任一策略生效)。两层治不同 race 拓扑(跨 clone vs 同 clone)· 互补不可替代。

### 实现(blast radius 受限)
- `state.py`:`_read_id_strategy`(走查 localconfig 到 .git 边界)+ `_detect_id_collision` + `cmd_prepare_check` 按 strategy 分支 + `cmd_init_feature` 撞号硬校验(`--force` 可逃生)。
- 既有 ID 解析正则本就变长匹配 + basename 子串校验 → **零改动兼容 12 位 ID**。
- `templates/teamwork_localconfig.json` + `templates/config.md` + `docs/conventions.md §1` 同步。

### 验证
- pytest:**67 failed / 437 passed**(baseline 67 · 新增 8 测试全过 · 零回归)· 覆盖 AC1-AC6(双策略 + 非法值兜底默认 + 撞号 FAIL/force/distinct + 时间戳 ID 接受)。

---

## 更早版本(v8.78 → v1)

完整历史已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)(v8.0 之前的 v7/v6/… 旧系统亦在此)。
