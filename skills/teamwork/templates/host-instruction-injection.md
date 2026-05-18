# Teamwork Host Instruction Injection Template

> 本文件是 `tools/sync-drift.py` 注入到用户项目根 `CLAUDE.md` / `AGENTS.md` 的 canonical 内容源。
>
> 🔴 **设计原则**：
> - **极简**：仅 cite SKILL.md · 不复述红线全文（避免 token 重复）
> - **稳定 marker**：`<!-- TEAMWORK_BEGIN:section vX.X.X -->` ... `<!-- TEAMWORK_END:section -->`
> - **版本敏感**：marker 上 version 字段 · sync-drift.py 比对决定是否更新
> - **用户内容外置**：marker 之间是 teamwork 管 · 之外是用户自由编辑 · 互不污染
>
> 当前注入 1 个 section · 后续需要时按需扩 section。

---

## Section: teamwork-pointer

注入到 CLAUDE.md / AGENTS.md 顶部（用户已有内容则插在最前 · 不覆盖）。

```markdown
<!-- TEAMWORK_BEGIN:teamwork-pointer v8.1 -->
## Teamwork 协作模式

本项目使用 [Teamwork](https://github.com/okteam99/teamwork) 多角色协作流程。

- **完整规范**：`~/.claude/skills/teamwork/SKILL.md`（Claude Code）/ `~/.codex/skills/teamwork/SKILL.md`（Codex CLI）
- **9 条 L1 红线** + Stage 流转 + 暂停点协议 详见 SKILL.md
- **新 session 必跑** `python3 {SKILL_ROOT}/tools/bootstrap.py`（系统维护）+ 按 [SKILL.md § Triage 入口规范](../SKILL.md) 入口规范分诊
- **state.json 写操作** 走 `tools/state.py` 单源（详 SKILL.md § PMO 软约束）

🔴 PMO 是项目流程统一承接者 · 不直接动代码 · 调度 RD/QA/Designer/架构师 完成实施。

🔴 **worktree 模式写文件路径**：Feature 进 worktree 后 · 所有代码/文档/测试文件读写一律用 **worktree 内路径**（推荐绝对路径）。部分宿主的 patch/写工具不继承 shell `cwd`（如 codex `apply_patch`）· 用相对路径会落到主工作区污染主分支。
<!-- TEAMWORK_END:teamwork-pointer -->
```
