# Changelog

> 📦 v8.91 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.92 · review-stage §5 澄清「汇总层 ≠ 合并」(防三视角揉进一个 REVIEW.md · doc-only)

> 用户:看下面的 case,是否是 review 规范写的不清楚 —— 案例里 AI 跑完 arch/qa/external 三视角后只写了一份汇总 `REVIEW.md`(+ `reviewers:[…]` list),review-complete 因缺 per-role 文件 FAIL,补 `REVIEW-arch.md`/`REVIEW-qa.md` 后才过。

### 诊断:不是「漏写」· 是 §5 决策点的认知陷阱
- per-role 文件其实在 **8 处**写明(stage.md §2/§3/命令清单/质量基线/Output Contract + `_review_brief` 结果清单/完成命令 `--artifacts` + `REVIEW_SPEC.artifacts` 硬门禁)→ 信息完整,gate 弹回是**正确行为**(不动 gate)。
- 但 **§5「汇合 → REVIEW.md」** 落在「AI 决定产物形态」那一步,四个信号合力把人往「一个文件搞定」带:① "汇合" 字面像 merge into one;② `reviewers:[arch,qa,external]` 是 list-frontmatter 暗示"一个文件装所有视角";③ per-role 文件零内容校验显得像可选脚手架;④ gate 重点 `reviewers_match` 只查 REVIEW.md。多视角独立性 WHY(防鼓掌效应)又埋在质量基线、没出现在决策点。

### 改法(doc-only · 不动 gate 逻辑)
- **`stages/review-stage.md` §5**:标题改「🔴 汇总层 · 不是合并:arch/qa/external 三份产物都要独立留盘」+ 正文点明「REVIEW.md 是三份产物**之上**的汇总,**不替代**它们(P0 门禁硬要求 · 原因:多视角独立性 SOP 防鼓掌效应)」+ 显式警告「别揉进一个 REVIEW.md + reviewers list 就交差 → review-complete 会因缺 per-role 文件 FAIL」。
- **§cite 表第 5 行**:从「(整合 · 无 spec cite)」改为「(汇总层 · REVIEW-arch/qa 已各自落盘 · REVIEW.md 只汇总不替代)」。

### 验证
- doc-only · 无代码变更 · gate 与测试不受影响(per-role 硬门禁本就正确)。
