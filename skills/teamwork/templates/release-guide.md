# RELEASE-GUIDE 模板

> 位置:`project-specs/RELEASE-GUIDE.md`(workspace 级 · 与 DEV-RULES 同级)· 详 [docs/conventions.md §13](../docs/conventions.md)
>
> **本文件 = 本项目「怎么发布上线」的规范**:用户说「发布 / 上线 / 发版」时 PMO **必读本文件并照此执行**。
>
> 🔴 **人/团队维护**:bootstrap 只在文件**不存在**时从模板创建(模板自带通用默认流程 · 可直接用);项目有自己的发布链路(CI/CD / 审批 / 灰度)→ 人改本文件 · AI 发现值得固化的发布约定 → 提示用户加 · 不代写。
>
> 🔴 **边界**:本文件管「**版本发布到线上**」(集成分支 → 生产分支);单 feature 的交付(feature 分支 → 集成分支)归 ship stage(ship1 MR + await-merge)· 别混。

```markdown
# {项目名} 版本发布规范(RELEASE-GUIDE)

> 触发:用户明确要求「发布 / 上线 / 发版」· PMO 照本流程执行 · 🔴 合入动作永远归用户(用户主权)。

## 默认发布流程(staging → main)

1. **核对 staging**:确认本次要上线的内容已全部合入 `staging` · 列出内容清单(feature/MR 列表)给用户过目。
2. **创建发布 MR/PR**:`staging` → `main`(CLI-first:`gh pr create` / `glab mr create` · 标题含日期/版本与内容概要 · 描述列本次上线清单)。
3. 🔴 **给出 URL**:MR/PR URL **置顶独立行**原样贴给用户(不埋段落 · 不转写 —— 同 ship1 user_card 纪律)。
4. 🔴 **提醒用户合入**:AI 不代点合并 · 可跑轮询监控合入状态(合入后播报)。
5. **发布后义务**:核对各 feature REVIEW 的 release-gated 待补证据(deferred 项:真实 rollout/rollback · 生产 soak · 生产平台 smoke)· 逐项补跑并回填状态。

## 环境与分支

> 本项目分支模型(默认:`staging` = 集成 · `main` = 生产)· 与默认不同改这里。

## 项目特有步骤(按需 · 无则删)

> 如:tag / 版本号规则 · CHANGELOG 更新 · 通知渠道 · 回滚预案 · 审批人 · 灰度/金丝雀。
```

## 与其他文档的协作

- 🔗 [stages/ship-stage.md](../stages/ship-stage.md) — 单 feature 交付(feature → 集成分支)· 本文件接它的下游(集成 → 生产)
- 🔗 [stages/review-stage.md § release-gated](../stages/review-stage.md) — 发布后待补证据的来源(deferred 项)
- 🔗 `DEV-RULES.md` — 开发规范;本文件只管发布流程
