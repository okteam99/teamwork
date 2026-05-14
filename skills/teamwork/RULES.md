# RULES · v8.0

> v8 起,所有可枚举规则物化进 `tools/state.py`。
> 本文件只保留**红线 rationale**(为什么这么设计 · 不讲怎么校验)。
> 校验逻辑全部在 `tools/_v8_engine.py` + `tools/_v8_stage_specs.py` + `tools/_v8_ship.py`。

---

## 9 红线 rationale

### R1 · 代码写权归 RD

**Why**:代码 / 测试 / 构建配置写操作必须由 RD 角色执行。
- 多角色分工 = 不同 checklist。让 PM 写代码 / 让 RD 起草 PRD,都会让该角色的关注点被另一职责淹没。
- **外部模型例外**:codex / claude / gemini 等外部模型仅只读评审(OpenAI ToS 合规)。
- **Ship Stage 例外**:第二段 finalize 允许 PMO push merge_target(严格限定 state.json + BUG-REPORT.md frontmatter)。

**v8 物化**:state.py 内部封装 dispatch · stage spec 在 brief 中明确告知"你是 RD 身份"。

---

### R2 · 流程类型闭集

**Why**:6 种流程(Feature / Bug / Micro / 敏捷需求 / Feature Planning / 问题排查)是经过实证的闭集。
防止 AI 发明"Feature 变更""敏捷 Bug"等变体 · 每种变体都引入隐藏路径 · 长期累积成不可维护状态机。

**v8 物化**:`init-feature --flow-type` 是 enum 强制 · prepare 流程识别在 6 enum 内闭合。

---

### R3 · PMO 统一承接

**Why**:所有用户输入由 PMO 角色先承接 · 禁止其他角色直接响应。
多角色对话场景下 · 如果用户输入直接打到 RD/Designer · 容易让角色越权(RD 直接接需求 → 跳过 PM 的 PRD)。

**保留 AI 自决**:这一条不可枚举(state.py 无法物理判断"谁在响应"),依赖 AI 自觉。

**v8 物化**:仅软约束 · 通过 stage spec 在 brief 中持续强调。这是 9 红线中唯一仍是软约束的一条。

---

### R4 · 流程边界

**Why**:三个子条:
- (a) 不简化:每种需求走对应级别的完整流程 · "简单""文件少""无风险"不构成跳过理由。
- (b) 不膨胀:自动流转节点禁止插入暂停 · "回合边界""容量预算""让用户看进度"等不构成暂停理由。
- (c) 必给步骤描述:选定流程类型后必须给完整步骤(阶段链 + 每个阶段大致做什么 + 预期产出)。

简化 = 失去多视角检查 · 膨胀 = AI 凭印象塞暂停点骚扰用户。

**v8 物化**:
- state.py 按 flow_type 强制 stage 链 · 跳过用 bypass 协议(必 --user-confirmed)。
- state.py emit 暂停点 markdown 替代 AI 自己写格式 · 自动避开"容量焦虑"措辞。
- prepare 命令自动输出步骤描述。

---

### R5 · 暂停点协议

**Why**:三个子条:
- (a) 暂停必等确认:暂停点必须等用户明确回复 · 不能 AI 自行决定。
- (b) 必给建议 + 编号:任何要求确认的内容必须含 💡 推荐项 + 📝 理由 + 编号化(1/2/3 或多决策 1A 2B)。
- (c) 状态行 + 决策参考:暂停点 final response 必须含状态行 + 📚 决策参考绝对路径。

无编号 = 用户要打字 · 无推荐 = 用户要现做决策 · 无路径 = 用户找不到要看的文件。这些都把心智负担转给用户。

**v8 物化**:state.py xx-complete 在多 legal_next / 决策类场景自动 emit 标准暂停点 markdown(强制 5 行格式 + 编号 + 推荐项 + 决策参考路径)。

---

### R6 · Feature Planning 只出文档

**Why**:Feature Planning 流程只产 PROJECT.md / ROADMAP.md / sitemap.md · 禁止产代码 · 禁止自启 Feature 流程。
Planning 是产品方向决策 · 不应该 AI 自动跳过决策直接开 dev。

**v8 物化**:Feature Planning 不进状态机 · `init-feature --flow-type "Feature Planning"` 被 reject · 由 PMO 主对话执行(详 docs/feature-planning.md)· 物理上不会出代码。

---

### R7 · 证据闭环

**Why**:三个子条:
- (a) 实测输出:声称"完成"必须附实际命令 stdout / 测试结果 / 构建输出。
- (b) 声明即承诺:Stage 开始前必须输出 Execution Plan(approach / rationale / steps remaining / estimated)。
- (c) 事实字段 evidence-binding:外部观察的判定(commit hash / mr_url / test exit-code 等)必须含 command + stdout + exit_code + timestamp。

AI 会"凭印象"声称完成 / 声称读了规范 / 声称跑了测试。证据闭环是物理拦截的根基。

**v8 物化**:
- xx-complete 必传 `--auto-commit` · state.py 跑 `git cat-file -e` 校验
- `--artifacts` 列出的文件必须在 commit changeset 内(防伪 commit hash)
- `--test-stdout` + `--test-exit-code` 必传(dev/test stage)
- Ship 类命令必传 `--feature-head-commit` / `--merge-commit-hash`(已 v7 P0-101 物化)

---

### R8 · 写操作硬门禁链

**Why**:三个子条:
- (a) 流程入口门禁:PMO 未输出初步分析前禁止任何写操作。
- (b) Subagent dispatch 预检:dispatch 前完成 L1/L2/L3 预检 · 未通过不得 dispatch。
- (c) Ship Phase 1 CLI-first:push 完后必检 gh/glab CLI · 可用必走 CLI 创 MR · git push 输出的 hint URL 是 trap。

写操作不可逆 · 一旦进入"AI 自驱写代码"模式 · 错误会快速放大。门禁链是给用户的最后干预机会。

**v8 物化**:
- prepare 未完成前 stage-start 拒绝(state.py 内部校验)
- ship-phase --action push 强制 enum + URL 二选一(P0-113 沿用)
- linked worktree 拦截(P0-156 沿用)
- destructive op 前合并未确认拦截(P0-124 沿用)

---

### R9 · session bootstrap 必跑 triage

**Why**:新 session 首条 PMO 响应前必跑 state.py triage · 在响应中 cite audit_line。
session 启动是 AI 最容易"凭印象"的时刻(没读任何 spec · 没看 state.json)。triage 是兜底物化。

**v8 物化**:`state.py triage` 命令输出 audit_line 字段 · PMO 必须在首条响应可见 cite。

---

## v8 新增:bypass 协议

```
PMO 重试 3 次仍 FAIL → 暂停点询问用户 → bypass:

state.py xx-start --bypass --reason "<用户提供>" --user-confirmed --missing <ids>
 ↓
state.py:
 - 校验 --user-confirmed 必带(防 AI 自决)
 - 校验 --missing 覆盖实际 missing
 - 通过 + 自动写 bypass_log[] + concerns WARN(完整审计闭环)
```

`--user-confirmed` 的物化语义:state.py 无法物理验证"用户真的说了",但此 flag 的存在性 = AI 声称用户已确认。审计时若发现 AI 自加此 flag(对话历史无用户确认)= 红线违规。

---

## 从 v7 16 红线 → v8 9 红线

| 范式 | red lines 数 | spec 行数 | 校验方式 |
|------|------------|---------|---------|
| v7 | 16 + 三层级(L1 核心 / L2 专项 / L3 工具)| RULES.md 1883 | AI 自觉 cite + Read |
| v8 | 9(R3 软 + 其他物化)| RULES.md ~180 | state.py 物化拦截 |

v8 把可枚举的 16/17 子条目物化进 state.py。RULES.md 不再讲"怎么校验",只讲"为什么这么设计"。
具体校验代码:[tools/_v8_engine.py](./tools/_v8_engine.py) + [tools/_v8_stage_specs.py](./tools/_v8_stage_specs.py) + [tools/_v8_ship.py](./tools/_v8_ship.py)。

---

## 相关

- [SKILL.md](./SKILL.md) — 命令清单 + 5 mode + 6 流程闭集
- [docs/v8-redesign/00-MANIFESTO.md](./docs/v8-redesign/00-MANIFESTO.md) — 设计宪法
- [tools/state.py](./tools/state.py) — 红线物化拦截层入口
