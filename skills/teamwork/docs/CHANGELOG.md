# Changelog

> 📦 v8.84 及更早(含 v7/v6/… 旧系统)已归档 → [CHANGELOG-ARCHIVE.md](./CHANGELOG-ARCHIVE.md)。本文件**只留最近 1 版**(每次发布把上一版迁入归档)。

## v8.85 · 外部评审 claude 短 prompt 化 + review_start.log liveness(dev-only)

> 用户拍板:提交 review 的 prompt 不超过 200 字符 · 超过则落文档让 review 模型去读;并在最前面加一句「正式 review 前先写 review_start.log(时间戳)到当前目录,证明模型能正常工作」。治本长 argv 卡 / 模型把模板当问题 / 调用方分不清「慢」与「卡死」。

### `_run_claude_review` 改 inline/doc 双模(`_build_claude_review_cmd`)
- **短 prompt(≤200 字符)**:`claude -p <prompt> --output-format text`(纯文本 · 无工具 · 快 · 同旧)。
- **长 prompt(>200)**:prompt 落 `external-review-prompts/<stage>-<model>.md`(已存在则不覆盖;fallback inline 也物化 · 可审计)· argv 只发 **≤200 字符短句**:「先在 cwd 写 `review_start.log`(UTC 时间戳)证明 liveness · 再读 `<doc 相对路径>` 按其做 review · 只输出评审」。
- doc 模式用 **`--allowedTools Write Read`**(只放行读 + 写 liveness 日志 · **不放行 Bash/执行** · 守只读评审)· `cwd=feature_dir`(`review_start.log` + doc 相对路径都落 feature 目录)。

### review_start.log = liveness 信号(治本「分不清慢 vs 卡死」)
- reviewer 启动后**几秒内**先写 `review_start.log` → 后台轮询看到它 = 模型正常工作,继续等;**一直没出现**才是真没响应。state.py 跑完把它读进 emit 的 `liveness_confirmed_at` 并清理(不污染 feature 目录)。
- 超时(rc=124)hint 据 liveness 分流:有日志 = 模型**启动了但没跑完**(慢/限流 · 串行重跑);无日志 = **可能从未响应**(查 auth/网络/并发限流)。🔴 明确**禁止**伪造 `tool_error` 文件 / 自列 external 通过门禁绕过 P0-154。
- `bootstrap.py` gitignore 维护加 `review_start.log`(兜底防 cleanup 失败时残留误入 commit)。

### 验证
- 实测(live):doc 模式 `_run_claude_review` rc=0 · ~30s · 模型确写出 `review_start.log`(timestamp)+ 读 doc + 出评审。短句 argv 实测 ≤200 字符。
- pytest **3 failed / 463 passed**(baseline 3 = scan-spec 既有 · 零回归 · 新增 3 测试[短 inline / 长 doc 模式 argv≤200+allowedTools+cwd / doc 已存在不覆盖])。
- spec:review-stage.md §4 加「同步·慢·别提前 kill + liveness + 超时=FAIL 不旁路」。
