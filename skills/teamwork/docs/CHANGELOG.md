# Changelog

> 📦 v8.87 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.88 · 外部评审诚实降级自审兜底(self-review-fallback · 异质不可用时 · dev-only)

> 用户:codex 环境下异质 claude 不可用(未登录/配额满)怎么办?是否用自身模型独立环境兜底?决策 **B**:加**诚实降级**——同模型 fresh exec 自审作弱安全网,但**绝不冒充异质、不满足 P0-154**(teamwork §11.1 早已把「同模型子进程」归类为非异质:只隔离对话历史不隔离权重 · 同盲点)。

### `external-review --self-review-fallback --reason '<原因>'`
- 异质 CLI **客观不可用**(未装/未登录/配额满·已重试失败)时 · 跑**宿主自身模型** fresh exec 自审(故意同源 · 绕异质校验)。
- 🔴 **结构性不满足门禁**:落 `self-review/<stage>-<model>.md`(**不进** `external-cross-review/`)· P0-154 只查 `external-cross-review/` → 自审永远不满足异质门禁。
- **诚实标注**:frontmatter `review_role: self-degraded · heterogeneous: false · degraded: true · degraded_reason` + 正文顶 banner;emit `degraded/heterogeneous/satisfies_p0_154:false`;写 `concern WARN`(retro 可见)。
- **必带 `--reason`**(异质为何不可用 + 重试证据)· gemini 宿主无 runner → FAIL 指向 change-review-roles。
- 要继续仍须:① 修环境重跑真异质 · 或 ② `change-review-roles` 移除 external(本自审作 audit evidence)。**不可**当 external 通过证据。

### 实现 + 验证
- `state.py`:`cmd_external_review` 加 self_fallback 分支(model=宿主自身·绕同源块)+ 输出路由 `self-review/` + degraded frontmatter/banner + concern + emit 标记 + `--self-review-fallback`/`--reason` argparse。异质主路径(elif/else)字节不变。
- live 实跑验证:codex host→自审 claude · 产物落 self-review/ · frontmatter/banner/concern 齐 · external-cross-review/ 不创建(门禁结构性未满足)。
- pytest **3 failed / 467 passed**(baseline 3 = scan-spec 既有 · 零回归 · +3 测试:reason 必填 / gemini 拒绝 / 路由 self-review)。
- spec:review-stage.md §4 + standards/external-model-usage.md §11.1。

### 后续(未做 · 待确认)
- prepare 阶段**早检测**异质模型可用性(fail-fast + 预决策)· 与本版降级机制互补(本版是 review-time 降级 · prepare 是 kickoff-time 预警)· 不替代 review 门禁(可用性瞬时)。
