# Changelog

> 📦 v8.82 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.83 · 文档卫生(死链修复 + 归档引用去权威化 + 删 v7 死测试 · dev-only)

> 用户:整体 review teamwork 各文档,清「没必要内容」,尤其**旧文档引用 / archive 文档引用**。机械扫描(link-resolution + grep + 测试)定位后批量修。

### A · 死链修复(明确 bug · 3 处)
- `roles/external-reviewer.md`:`../docs/v8-redesign/{00-MANIFESTO,01-COMMAND-SCHEMA}.md` **缺 `archive/` 段** → 死链(v8.78 归档搬迁时漏改这一个 · 其余 7 role 文件都对)。
- `templates/knowledge.md`:`[TRIAGE.md](../TRIAGE.md)`(文件不存在)→ `SKILL.md § Triage 入口规范`(triage 已并入 SKILL.md)。

### B · 归档命令 schema 引用去权威化(~11 处)
- 8 个 role 文件 + `_v8_engine.py`/`_v8_ship.py`/`_v8_stage_specs.py`/`state.py` 头注 + `SKILL.md` 原把 `docs/archive/v8-redesign/01-COMMAND-SCHEMA.md`(v8.0 冻结快照)当「命令 schema」引 —— 但命令现行权威 = `state.py --help` + `_v8_stage_specs.py`。统一改指 live 权威;`01-COMMAND-SCHEMA.md` 仅保留为「v8.0 归档快照 · 勿当现行」。
- `00-MANIFESTO.md`(9 红线 rationale / 设计哲学)是历史原理 · 不腐 · **保留**为 rationale 引用。

### C · 删 v7 死测试(测试套 67 failed → 3 failed)
- `tools/tests/test_render_{status_line,afk_skip,decision_pause,flow_transition}.py` 4 个文件 subprocess 调用 **v8 已删除**的 v7 `render-*.py`(`scripts-policy.md R-SP-6` 明示废弃 · 由 state.py 自 emit 取代)· 无 live 代码调用 → 纯死测试 · 删除。

### 验证 + 留存
- 机械验证:link-resolution 脚本(live 死链 46→12 · 余 12 全是 `templates/` 占位符示例 · 非真链)· `01-COMMAND-SCHEMA` 残留引用均已加「归档快照」caveat。
- pytest:**3 failed / 460 passed**(原 67 failed 中 64 个是被删的 render 死测试)。
- 未动:`CHANGELOG-ARCHIVE.md` ~30 死链(归档冻结 · 不维护)· `scan-spec-consumer` 3 个真实断言失败(输出 drift · 单独排查项 · 非本轮范围)。
