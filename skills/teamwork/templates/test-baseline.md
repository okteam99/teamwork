# 测试基线失败集（test-baseline · 项目级单源）

> **telos**：brownfield 项目的共享测试套件常带**预存在失败**（base 即红 · 历史重构遗留 / 其他 feature 欠债）。没有登记机制时，**每个**碰到该套件的 feature 都要重复「stash → 跑 base → diff → 在 REVIEW 里论证非本 feature 回归」的甄别成本（同一批失败被逐 feature 反复甄别）。
>
> 本文件把「base 上**已知**的预存在失败」登记成**项目级单源**，让 test gate 改成**差分**判定：
> - **0 个新增失败**（当前失败 ⊆ 本表）→ 红 base 也放行（不是回归）。
> - **有新增失败**（当前失败 − 本表 ≠ ∅）→ = 回归（修）**或** 新出现的预存在（核实后 `--add` 登记原因）。
>
> 下一个 feature 直接读本表，不再重新 derive。

## 用法

```bash
# 登记一个预存在失败（核实确属 base 即红、非本 feature 引入后）
state.py test-baseline --add --feature <feature路径> \
  --test-id "<与 --current-failures 一致的用例 id>" \
  --suite "<套件/命令>" --reason "<为何红 · 谁的债 · 何时清>" [--base-commit <sha>]

# 看当前登记
state.py test-baseline --list --feature <feature路径>

# 差分预览（跑完套件后 · 不写状态）
state.py test-baseline --diff --feature <feature路径> --current "id1,id2,id3"

# 在 test-complete / dev-complete 走差分 gate（红 base + 0 新增 → 放行）
state.py test-complete --integration-test-exit-code 1 --current-failures "id1,id2" ...
```

## 🔴 纪律

- **id 一致**：`--test-id` / `--current-failures` 用**同一种**用例标识（如 pytest nodeid、`suite::case`、vitest 全名）· 工具按字符串精确匹配。
- **登记要有原因 + 清账计划**：不是「把红的都塞进来绕过 gate」· 每条写清「谁的债 / 何时清」· stale 条目（已不再失败）应删（`--diff` 会标 `stale_registered` 提示）。
- **只登记 base 即红的**：本 feature 改动**新引入**的失败**绝不登记** —— 那是回归，必须修。核实方法 = 在 base（无本 feature 改动）上跑该用例确认即红。
- **单源**：执行态在各套件、登记在本表 · test gate 差分自本表 · 不在别处复制。

## 登记表

| 失败用例 (id) | 套件/命令 | 基线 commit | 原因（谁的债 · 何时清） | 登记于 |
|---|---|---|---|---|
<!-- 示例（删之）：| developer_earnings_it::test_settlement | cargo test --lib | a1b2c3d | F-Bv2 重构遗留 · 待 owner 修(REVIEW-#42) | 2026-06-15 | -->
