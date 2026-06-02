# Changelog

> 📦 v8.85 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.86 · 浏览器验证截图 → 系统临时目录(不污染主工作区根 · dev-only)

> 用户:有些流程会调用浏览器截图,这些(自检「看一眼」的)截图应放临时文件,别落主工作区根。实证:`<repo>/f<id>-full-en.png` 等散落仓库根目录。

### 约定:transient 浏览器验证截图 → `${TMPDIR:-/tmp}/teamwork/<feature_id>/screenshots/`
- ui_design 预览验证(`browse 截图` 自检渲染)+ 各 stage 顺手核对 UI 的截图 = **一次性验证产物**(AI 自己看 · 非交付 · 不 commit)· 现统一写**系统临时目录**(按 feature 命名 · session 内可复寻 · 系统自动回收 · 零工作区脚印 · 不需 gitignore)。
- 治本 worktree 红线:此前无落点约定 → AI 随手存仓库根 → 污染主工作区 / 并行 Feature 基线。
- **⚠️ 与 browser_e2e 证据区分**:`browser_e2e` stage 的**证据截图**是交付物 · 仍落 `<feature_dir>/screenshots/*.png`(committed · pm_acceptance 复核)· **不**走临时目录。临时目录只放非证据的自检截图。

### 落点
- `docs/conventions.md` §12.5(新增 · transient 截图位置 + 与证据区分 + mkdir 示例)。
- `stages/ui-design-stage.md` §3 same-stack 预览「browse 截图」→ 点明存系统临时目录 · 不落 worktree 根。
- `SKILL.md` worktree 红线加一条:浏览器「看一眼」截图 → 系统临时目录 · 绝不落 worktree / 主工作区根(browser_e2e 证据例外)。

### 验证
- 纯 spec/约定改动(无 code)· pytest **3 failed / 463 passed**(baseline 3 = scan-spec 既有 · 零回归)。
