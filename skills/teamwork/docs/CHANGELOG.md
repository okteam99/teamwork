# Changelog

> 📦 v8.80 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.81 · ship1 知识沉淀闸门(distill · 过程/知识两层 · 防归档丢知识 · dev-only)

> 用户:文档分过程/知识两层 · 过程产物(feature 目录)归档前,「描述代码」的知识必须先 graduate 到知识层(随 feature MR 合)· 否则归档 = 埋掉未沉淀的知识。本版落 ship1 distill 硬闸门(归档的知识安全前置 · 归档本身见后续 v8.82)。

### sanitize 加 `--distill` 硬闸门(知识层 6 项)
- `ship-phase --action sanitize` 必带 `--distill`(JSON · knowledge/adr/reg/retro/architecture/db_schema)· 缺 / 非法 / 缺项 → BLOCK。
- R0:强制 AI **逐项走一遍**知识层(每项记 `updated/promoted <what>` 或显式 `none`/`n/a`)· 质量留 AI · 「走没走」进脚本。记 `ship.distill` 留痕。
- 知识层 6 项:KNOWLEDGE(gotcha/约定)· ADR(决策)· REG(测试场景)· retro(复盘)· **ARCHITECTURE.md · database-schema.md**(用户特别要求查这俩 living 文档是否需更)。
- 「描述代码的文档随代码进 MR」:6 项写的知识层文件在 worktree commit · 随本次 feature MR 一起 review + 合(ship1 · 合入前)。

### 🔴 迁移↔schema 机械校验(治本 schema 文档 drift)
- feature diff 含 `migration` 文件 **且** `db_schema` 声明无变更 **且** `database-schema.md` 未更 → **BLOCK**(改了表却称无库改 = 矛盾)。纯数据迁移 → db_schema 写 `data-only migration`。best-effort(无法 diff 则跳过)。

### 实现 + 验证
- `_v8_ship.py`:`DISTILL_KEYS` + `_validate_distill` + `_check_migration_schema` + sanitize 接线 + `--distill` argparse。
- pytest:**67 failed / 446 passed**(baseline 67 · 新增 7 测试[缺/非法/缺项/空值/有效记录 + 迁移↔schema BLOCK/放行]· 零回归)。
- ship-stage.md §14(distill 闸门 + 过程/知识两层 + 6 项表)。

### 后续
- v8.82:archive(过程层 feature 目录 zip+rm · 随收尾 MR · 语义检测改「zip 存在」)+ ROADMAP/WS forced-marker。distill(本版)是归档的知识安全前置。

---

## 更早版本(v8.80 → v1)

完整历史已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)(v8.0 之前的 v7/v6/… 旧系统亦在此)。
