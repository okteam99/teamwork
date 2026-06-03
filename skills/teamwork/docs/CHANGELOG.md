# Changelog

> 📦 v8.88 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.89 · 本地敏感配置统一目录 `.teamwork-local-env/`(kubeconfig/密码/API key · dev-only)

> 用户:本地敏感配置(kubeconfig / DB 密码 / 个人 API key)散落 · 规范一个统一目录、默认 gitignore、TROUBLESHOOTING 配合读、session 初始化自动创建。决策 **A**(默认自动建)。

### bootstrap 自动维护 `.teamwork-local-env/`(项目根 · `maintain_local_env`)
- **缺失 → 自动建**:目录 + `config.properties` 模板(注释示例 · **无真密钥**)+ 目录内 `.gitignore`(`*`)。
- **已存在 → skip**:绝不覆盖用户真 secret(仅补缺失的目录内 .gitignore)。skill 仓自身 skip。
- **opt-out**:`.teamwork_localconfig.json` 的 `local_env_auto_create: false`(默认 true)。
- 用途:键值型(DB 密码 / API key / token)→ `config.properties`(`KEY=value`);整文件型(kubeconfig / 证书)→ 直接放本目录。

### 🔐 双重 gitignore(防御纵深 · secret 绝不进仓库)
- 项目根 `.gitignore` 加 `.teamwork-local-env/`(`maintain_gitignore_worktree`)· **且**目录内自带 `.gitignore`(`*`)—— 即便根 .gitignore 漏/子 repo/手删,目录仍自我忽略全部内容。
- 与 `.teamwork_localconfig.json` 严格区分:前者 = **你的** secret(gitignored)· 后者 = **teamwork 自己**的配置(可提交)。

### 配套
- **template** `templates/local-env-config.properties`(带警告头 + 注释示例 + kubeconfig 用法)。
- **TROUBLESHOOTING.md 模板** §五:本地敏感配置来源(从 `.teamwork-local-env/` 加载的命令示例 · 真值只在此目录 · 本文只写变量名)。
- **conventions.md §13** + **localconfig 模板/config.md** 文档化 `local_env_auto_create`。

### 验证
- live 实跑:created(目录+模板+目录内.gitignore)/ existed(secret 保留不覆盖)/ disabled(opt-out 不建)/ 根 gitignore appended 全验证。
- pytest **3 failed / 470 passed**(baseline 3 = scan-spec 既有 · 零回归 · +3 测试:created/不覆盖/opt-out)· 修 `test_gitignore_already_present`(加新 pattern)。
