# Changelog

> 📦 v8.77 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.78 · 文档精简 P0+P1 + 治本 e1d12b2 编码损坏(用户 case「统计行数 + 逐文件 review 精简」· dev-only)

> 用户 2026-06-01:"统计 teamwork skills 总行数 · 逐个文件 review · 看哪些文档内容可以精简。" 4 路并行 review 审计后,执行 P0(归档自标记死档)+ P1(修 README 谎报 + 乱码)。乱码排查中发现一个真 bug:**commit e1d12b2「文档清理 P0」批量改写时掉了大量汉字的末字节**,导致 9 文件 invalid-UTF8 + 7 文件 U+FFFD。

### P0 · 归档自标记死档 + CHANGELOG 拆分

- **CHANGELOG 拆归档**:13,116 行 → 主文件**只留最近 1 版**(v8.77→v1 共 249 版迁 `docs/CHANGELOG-ARCHIVE.md` · 每次发布把上一版迁入归档)。v8.0「范式切换 · 不向下兼容」· v7 及更早描述的是已不存在的旧系统。
- **归档 4 个 v8-redesign + DESIGN + change-request**(均自标记「不再维护」/DEPRECATED)→ `docs/archive/`(2,396 行移出活跃集)。重指 **~30 处 cite**(8 角色 + FLOWS/STANDARDS/SKILL×5 + goal-stage + prepare + 6 工具 docstring)· 修 SKILL 文档导航 **死链 02-CLEANUP/03-MIGRATION**(早删但仍被引)· docs/ 顶层 8→6 文件。

### P1 · 修正(非冗余 · 真 bug)

- **agents/README dispatch 谎报**:删「dispatch 文件由 state.py 各 stage-start 自生成」(grep 证实工具零此逻辑)· dispatch 协议从「🔴 硬规则」降为「可选实践」· 对齐 [STAGES.md §4](../STAGES.md)「subagent 不强制 · 无 dispatch 预检协议」。
- **治本 e1d12b2 编码损坏(16 文件 · ~30 处)**:9 文件 invalid-UTF8(掉末字节 · 如 行 `E8A18C`→`E8A1`)+ 7 文件 U+FFFD。根因:e1d12b2 删 `v7.3.10+P0-xx` 元注释时损坏了相邻汉字。用 **git parent(e1d12b2^)还原**逐字符确认 · 全 **102 活跃文件现 clean UTF-8**。

### 验证

- pytest:**67 failed / 429 passed**(baseline 68 · `test_scan_spec_consumer` 因损坏修复 4→3 · **零新增失败**)。
- 全文件 UTF-8 完整性扫描通过 · 无 live 死链。

---

## 更早版本(v8.77 → v1)

完整历史已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)(v8.0 之前的 v7/v6/… 旧系统亦在此)。
