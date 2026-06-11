# 外部模型合规使用规范

> 🔴 **本文件是 teamwork 调用外部模型(codex / gemini / claude-cli 等)的唯一权威源**。SKILL.md 红线 R1(代码写权归 RD)+ R7(证据闭环)顶层 cite 本文件。
>
> 🟢 **抽出来源**: 实战触发——用户分享 codex 账号收到 OpenAI "cyber abuse" 警告 · 根因是 teamwork 把 codex CLI 当 AI agent 后端用(5/8 profile full sandbox + service_tier=fast + hooks 自动触发 + AI 编排 AI)。
>
> 🟢 **PMO 主路径** = `state.py external-review --feature <path> --stage <stage>` · 详 `state.py external-review --help` + §十一 异质性硬约束。PMO 心智 = 2 个业务参数 · host / model / which / profile / 文件命名 全自动。本文 §五/§六 是底层实现 · 已物化到工具 · PMO 不必读。

---

## 一、核心原则（4 条硬约束）

```
1. 只读约束：外部模型只能读代码 · 不写代码库 · 不能执行命令
 ├── codex 路径：物理拦截 · 所有 codex profile sandbox_mode = "read-only"（写被 sandbox 挡）
 └── claude 路径（纯 `claude -p` · 无工具 / 无 `--bare` · `--strict-mcp-config` MCP 隔离）：评审结果经 **stdout** 返回 · **不写任何文件**（与 codex read-only 对称 · 评审产物由主对话 PMO 落盘）

2. 评审角色约束：外部模型在 teamwork 中**只承担评审角色**
 ├── reviewer.toml（代码评审）/ blueprint-reviewer.toml（蓝图评审）/ prd-reviewer.toml（PRD 评审）
 └── ❌ 禁止承担 dev / test / e2e / design / planner 等"自主执行"角色

3. 输出约束：外部模型只输出 markdown 评审记录
 └── 不输出 patch · 不输出可执行脚本 · 不输出"我已修改了 X 文件"

4. 调用频率约束：受 review_roles[] 控制 · 用户可 opt-out
 ├── 每个 Stage 实例化时 PMO 决策 active_roles 是否含 external
 └── Blueprint + Review **默认含** · 用户在 PMO 初步分析决策项呈现时可显式 opt-out
```

---

## 三、合规架构

```
✅ 合规姿态：
 主对话（Claude Code）
 ↓ 评审请求
 codex CLI（read-only 评审 profile · 输出 markdown）
 ↓ 评审记录
 主对话整合 → 用户决策
 ↓
 实际代码改动由主对话 RD 角色身份切换执行
 （不通过 codex）

❌ 禁止姿态－）：
 主对话 → codex (full sandbox · planner/rd/tester/designer/e2e) → 自主写代码 / 跑测试 / 执行 E2E
```

---

## 四、profile 分类

### ✅ 评审类（活跃 · teamwork 主流程使用）

| profile | sandbox | 用途 | dispatch 时机 |
|---------|---------|------|--------------|
| `reviewer.toml` | read-only | 代码评审（独立视角） | Review Stage external 角色（opt-in） |
| `blueprint-reviewer.toml` | read-only | TC + TECH 蓝图评审 | Blueprint Stage external 角色（**opt-out**） |
| `prd-reviewer.toml` | read-only | PRD 评审 | Goal Stage external 角色（opt-in） |

### 🔴 已废弃

| profile | 原用途 | 替代方案 |
|---------|------|---------|
| `rd-developer.toml` | TDD 开发 | 主对话 RD 角色身份切换（roles/rd.md） |
| `tester.toml` | 集成测试 + API E2E | 主对话 QA 身份切换 + 项目测试命令 |
| `planner.toml` | PM + PL 写 PRD | 主对话 PM/PL 身份切换 + prd-reviewer 评审 |
| `designer.toml` | UI 设计 | 主对话 Designer 身份切换 |
| `e2e-runner.toml` | Browser E2E | 主对话 + Browser MCP（codex 无浏览器能力） |

> 🔴 deprecated profile 已强制 sandbox=read-only · 即便用户手动 ad-hoc 调用也不会触发 cyber abuse 信号。

---

## 五、prompt 注入硬规则

> 🟡 **已物化**:`state.py external-review` 内置 prompt 注入(claude 路径读 `claude-agents/reviewer.md` 模板 · codex 路径 codex CLI 自带 review 模式)。PMO 不必读本节 · 仅 debug / 适配新 reviewer 模型时参考。

调用 codex 时 prompt 头部**必须**包含以下角色边界声明:

```
You are a code reviewer in the Teamwork framework.

🔴 STRICT CONSTRAINTS:
- You are READ-ONLY. Cannot write files. Cannot execute commands.
- Your output is markdown review records ONLY.
- Do NOT generate patches, scripts, or commit messages.
- Do NOT claim to have "modified", "fixed", or "implemented" anything.
- If you find issues, describe them — do not "auto-fix".

If asked to do anything outside review (write code, run tests, modify files):
respond "Out of scope. Teamwork uses external models for review only."
```

详见 `claude-agents/reviewer.md` 的 prompt 模板。

---

## 六、配置约束清单

> 🟡 **已物化**:`state.py external-review` 内置 profile 选择(stage→profile mapping)+ 校验 profile 文件存在 + 校验 reviewer.toml sandbox=read-only(代码内 enforce)。PMO 不必读本节 · 仅 codex profile 配置变更时参考。

```
codex-agents/*.toml 必须满足：
□ sandbox_mode = "read-only"（无例外 · 含 deprecated profile）
□ 不含 service_tier = "fast"（删除该项）
□ 不含 approval_policy 显式声明（走 codex 默认 = on-request）
□ 评审类 profile 的 developer_instructions 含「only review · no write · no exec」
□ deprecated profile 的 description 以 "[DEPRECATED ]" 起首
□ codex-agents/ 目录下不含 hooks.json（删除 · 持久化触发信号）
```

---

## 七、违规处置

| 违规类型 | 处置 |
|---------|------|
| 新增 profile sandbox=full | 阻断（codex CLI 启动时 fail · 红线 R1 违规） |
| 评审 profile 输出 patch / 写文件 | PMO 主对话整合时丢弃该输出 + 告警 |
| 主对话尝试 dispatch deprecated profile | 阻断 + 提示走身份切换替代 |
| 用户手动调用 deprecated profile（read-only） | 允许（已强制 read-only · 无 cyber abuse 风险） |

---

## 八、与 SKILL.md 红线的关系

**SKILL.md 红线 R1（代码写权归 RD）** 顶层：
> 外部模型仅用于只读评审 · 不参与代码写权 · 详见 standards/external-model-usage.md

**SKILL.md 红线 R7（证据闭环）** 顶层：
> 外部模型评审输出走主对话审计 · 不得作为自主 AI agent 后端 · 详见 standards/external-model-usage.md

红线层只保留一句话引用 · 详细 profile 配置 / prompt 注入 / 违规处置全部落本文件单源。

---

## 九、相关文件

- `tools/state.py` external-review 命令 — 调用主路径(详 `state.py external-review --help`)
- `codex-agents/*.toml` — codex profile 配置(全部 read-only · 无 service_tier · state.py 内部按 stage 自动选)
- `claude-agents/reviewer.md` — claude CLI 评审 prompt 模板(state.py 路径自动 pipe 给 claude -p)
- `roles/external-reviewer.md` — external 角色契约
- `templates/external-cross-review.md` — 评审记录模板(§五 整合流程已物化)
- (历史 `claude-agents/invoke.md` / `claude-agents/README.md` / `codex-agents/README.md` 已删除 · 调用细节进 state.py)

---

## 十一、异质性硬约束

> 🔴 **实战触发**:F034 review stage PMO 没找到 `which codex` · 选用 `Agent subagent_type=general-purpose` 起 Claude isolated context 自审 · 标 frontmatter `review_model: claude-opus-4-isolated-context` 「透明」· 用户察觉后承认违 R3 红线。
>
> 🟢 **本节是 PMO 主路径权威源** —— 顶部简介已指向此节 · §五/§六 是已物化的底层细节。

### 11.1 异质性定义(不可妥协)

**external review = 异质模型审查** —— 与主对话宿主模型**统计独立**的 LLM 提供独立视角。

| 类型 | 算不算异质? | 理由 |
|---|---|---|
| 主对话 Claude → codex CLI(GPT) | ✅ 算 | 训练语料 / 推理倾向独立 |
| 主对话 Claude → gemini CLI(Google) | ✅ 算 | 同上 |
| 主对话 Codex → claude-cli | ✅ 算 | 反向也成立(看宿主) |
| 主对话 Claude → `Agent subagent_type=general-purpose` | ❌ **不算** | 同模型 · 同盲点 · isolated context 只隔离对话历史 · 不隔离模型权重 |
| 主对话 Claude → claude-cli 子进程 | ❌ **不算** | 同模型自审 |
| 用 frontmatter `review_model: claude-isolated` 标"透明" | ❌ **不算** | 透明 ≠ 合规;透明只承认"我做了不达标" · 不替代"做达标" |

> **诚实降级自审(self-review-fallback)**:异质 CLI **客观不可用**(未装/未登录/配额满·已重试失败)时 · `external-review --self-review-fallback --reason '...'` → **emit subagent 降级配方**(🔴 v8.108:不再 exec CLI · PMO 起宿主自身模型 `Agent` subagent 自审 · 详 §11.5)· 写 `external-cross-review/`(frontmatter `heterogeneous:false degraded:true degraded_mode:subagent-fallback`)· **满足 P0-154**(降级 · 非异质 · 同盲点)。仍是降级不是异质:能修环境就重跑真异质 / 长期单模型走 `disable_heterogeneous_review`。**绝不偷偷**用 subagent 冒充异质(必显式标 degraded · 见 §11.5)。
>
> **单模型 opt-out(`disable_heterogeneous_review`)**:只有一个模型的用户可在 `.teamwork_localconfig.json` 设 `disable_heterogeneous_review: true`(默认 false)· 则 `external-review` **自动 emit subagent 降级配方**(🔴 v8.108:PMO 起宿主自身模型 subagent 自审 · 不 exec · 详 §11.5)· 落 `external-cross-review/`(**满足 P0-154** · frontmatter 标 `heterogeneous:false degraded:true degraded_mode:config-disabled`)· 让单模型用户能走完流程。代价:**非异质 · 同盲点 · 交叉 review 质量下降** —— 故每次 `bootstrap` 启动**持续 WARN** 提醒(`checks.heterogeneous_review.status=disabled` + `pmo_must_read`)· 建议装好第二个模型 CLI 后删此项恢复异质。与 self-review-fallback 的区别:后者是**临时 stopgap**(不满足门禁)· 本项是**项目级长期策略**(满足门禁 · 但被 startup WARN 持续提醒)。

### 11.2 文件命名硬规约(state.py 物化校验)

`external-cross-review/*.md` 文件名 + frontmatter `review_model` 字段必须:

```
✅ 白名单(必含其一 · case-insensitive):codex / gpt / gemini / deepseek / qwen / llama / grok / mistral
❌ 黑名单(必不含): claude / anthropic / isolated / subagent / general-purpose / self
```

合法示例:
- `code-codex.md` / `prd-gemini.md` / `tech-deepseek.md`
- frontmatter `review_model: codex-1.0` / `review_model: gpt-5-pro`

违规示例(state.py BLOCKED):
- `code-claude-isolated.md`(命中黑名单 `claude` + `isolated`)
- `code-subagent.md`(命中黑名单 `subagent`)
- `external-review.md`(模糊 · 无白名单字面)
- frontmatter `review_model: claude-opus-4-isolated-context`(命中黑名单)

🟢 **例外 · 诚实降级(v8.108)**:frontmatter 含 `degraded:true` + `heterogeneous:false` + `degraded_mode:subagent-fallback` 的降级文件 —— 文件名/标记**可含** `subagent`/`claude`(如 `review-claude-subagent-degraded.md`)· 门禁**先认 degraded marker 放行**(不落黑名单 · 详 §11.5)。🔴 **无** degraded marker 的 subagent/claude 文件仍 BLOCK(F034 伪装)—— 区别在「显式标 degraded 诚实承认非异质」vs「冒充异质」。

state.py 在 `<stage>-complete` evidence 校验时物化拦截 · 详 `_evidence_external_review_artifact`(_v8_stage_specs.py)。

### 11.3 PMO 调用前必做(防 F034 反模式)

```
Step 1:`which codex`(/ gemini / 其他白名单 CLI)
        ├── ✅ 在 → 跑(走合规 §三 架构)
        └── ❌ 不在 → 三选一(🔴 降级优先于移除 · 详 §11.5):
              ① 🟢 降级:`--self-review-fallback --reason '...'` → subagent 同模型自审(满足门禁 · 标 degraded)
              ② 装异质 CLI 恢复真异质
              ③ `change-review-roles` 移除 external(最后手段 · 留 audit)
              · 🔴 绝不**偷偷** substitute(subagent 冒充异质)· 必走 ① 显式标 degraded

Step 2:跑前 cite 上游 Feature 1 个范例(grep F033/external-cross-review/*codex*)
        · 验证范式一致(文件命名 / frontmatter / verdict 结构)

Step 3:跑命令 · 落 *-codex.md / *-gemini.md / 等真异质模型文件
```

### 11.4 反模式黑名单(case 实证)

| 反模式 | 案例 | 治本 |
|---|---|---|
| subagent **冒充异质**(无 degraded marker)| F034 PRD/TECH/Code 3 阶段 fall(2026-05-24)| 11.2 文件名校验 BLOCKED(🟢 诚实降级 subagent 带 marker 合规 · 见 §11.5)|
| 透明 frontmatter 伪装合规 | `review_model: claude-isolated` 自承"不达标"但仍提交 | 11.2 frontmatter 校验 BLOCKED |
| 看到工具不在就 substitute / 直接移除 | "/codex 不能 invoke → 用 Agent 起" 冒充异质 | 11.3 必先 `which` · 不在 → §11.5 降级优先(subagent · 非只能 stop/移除)|
| 没 cite 上游 Feature 范式 | F033 既有 `*-codex.md` 在 worktree 内 · F034 没 grep | 11.3 跑前 cite 范例 |

### 11.5 降级策略 = subagent(🔴 不 exec · 降级而不是去掉)

> 🔴 异质 CLI **客观不可用**(未装/未登录/配额满/持续超时·限流〔串行重跑仍失败〕/`claude -p` 本身坏 · 已重试失败)时 —— **优先降级,不是直接移除 external**。降级**统一走 subagent**(不再 exec CLI 自审)。

- **为什么 subagent 不 exec**:exec 一个 CLI 子进程做自审,反复踩认证 / `--bare` / MCP 卡死 / "Not logged in" / stdin 等坑(出过很多次)。**subagent(`Agent` 工具)在 harness 内跑** —— 同 auth、无子进程 CLI 问题、无 MCP 自动加载。它**仍是同模型自审**(非异质 · 同盲点),但**可靠**。
- **机制**:`state.py external-review --self-review-fallback --reason '<异质为何不可用+重试证据>'`(或项目 `disable_heterogeneous_review:true` 自动触发)→ state.py **不 exec** · emit `verdict: SUBAGENT_FALLBACK` 配方(state.py 是脚本 · 起不了 `Agent`)→ **PMO 起 Agent subagent**(isolated context · 宿主自身模型)产出降级评审 → 写 `external-cross-review/<stage>-<model>-subagent-degraded.md`。
- **满足门禁(降级)**:文件 frontmatter 必含 `heterogeneous:false` + `degraded:true` + `degraded_mode:subagent-fallback` + `degraded_reason:'...'` + `review_via:subagent` → `_evidence_external_review_artifact` 接受(降级 · 满足 P0-154)。**让你继续往下走**(降级而不是去掉)。
- 🔴 **honest-degrade ≠ F034 伪装**:必须**显式**标 `degraded:true degraded_mode:subagent-fallback`(诚实承认非异质)。**无** degraded marker 的 subagent 文件 → 仍落 11.2 黑名单 BLOCK(防偷偷用 subagent 冒充异质)。
- **优先级**:① 降级(subagent · 推荐)→ ② 装异质 CLI 恢复真异质 → ③ `change-review-roles` 移除(最后手段)。能修环境就修真异质;长期单模型走 `disable_heterogeneous_review`。

### 11.6 过程可观测性:prompt-doc 同名 `.log` 实时落盘(v8.139/140)

> 治「发起后完全黑盒」:执行期(最长 timeout 全程)磁盘上原来什么都没有 · 失败要等超时后验尸。

- **审计三件套同目录成组**(`external-review-prompts/`):输入 `<stage>-<model>-<ts>.md`(v8.136 唯一命名)· 过程 `<stage>-<model>-<ts>.log`(同名配对)· 结果 `external-cross-review/<stage>-<model>.md`。codex 路径 v8.139 起同样落审计 doc(执行仍 argv inline · codex 不读 doc)。
- **log 结构**:首行 `[UTC时间戳] START <label> · timeout · cwd · cmd` —— 🔴 **harness 写 · 不靠评审模型自报**(`claude -p` print 模式输出整体到达 · 模型「已开始」行不可能先到;模型挂死/认证失败时恰恰零输出 · harness 行才是诊断锚点)→ `pid=` 行(可 kill/对账)→ **`RUNNING` 心跳行**(v8.140 · 默认 60s · 报已等待秒数 + 已收字节 —— claude -p 完成前 stdout 0 chars 属正常 · 心跳让 tail -f 分清「生成中」vs「卡死」)→ stdout 原样实时追加 + stderr 逐行 `[stderr] ` 前缀(鉴权失败/codex 升级提示/限流**秒级可见** · 不再等超时)→ 尾行 `END · rc · 耗时 · 字节`(超时则 `TIMEOUT` 行 + 保留已收部分输出)。
- **首行 ACK 自证**(v8.140):generated 路径 prompt 尾注入输出契约 —— 评审输出**第一行**必须 `REVIEW-ACK <prompt-doc stem>`(stem 自带 stage/model/UTC 时间戳)。🔴 评审模型**写不了 .log**(claude -p 零工具 · v8.106 故意拔 · codex 沙箱不保证)· 「模型自报开始」物化为可行的**输出回显**:无 liveness 作用(print 模式整体到达)· 价值是**对应性自证**(输出 ↔ 本轮 prompt 绑定 · v8.136 防 stale 从输入侧补到输出侧)。验证:头 200 字符内回显即 `verified`(emit `review_ack`)· 缺失 → `ack_missing` WARN 不 BLOCK;`--prompt-doc` override 路径不注入不验(doc 原样执行契约)。

### 11.7 MCP 隔离:`--strict-mcp-config`(v8.141 · 本地 CLI 2.1.173 四组对照实测)

> 治「claude -p 偶发 MCP 卡死」整类 —— 不赌 CLI 版本连接是否阻塞。

| 案 | flags | 项目 MCP 真 spawn(marker 实测) | 结果 |
|---|---|---|---|
| C1 | 裸 `claude -p` | **True** | 5.4s OK |
| C2 | `--allowedTools Read` | **True** | 4.2s OK |
| C3 | `--strict-mcp-config` | **False** | 4.8s OK |
| C4 | strict + `--allowedTools Read` | **False** | 7.4s OK |

- 🔴 **v8.106 归因翻案**:裸 `claude -p` 也每轮 spawn 消费项目 `.mcp.json` 全部 server(C1)· 卡死与 `--allowedTools` 无关(C2)—— 真正变量 = 项目 MCP 被 spawn + CLI 版本连接行为(2.1.15x 阻塞 → 卡死;2.1.173 不阻塞 → 侥幸不卡)。评审 prompt 自包含零工具 · 本就不该碰项目 MCP。
- **解法**:`--strict-mcp-config` 且**不传** `--mcp-config` = 零 MCP spawn(C3/C4)· 不碰登录上下文(无 `--bare` 认证回归)。已进 `_build_claude_review_cmd` 固定 argv · 测试 pin(`--strict-mcp-config` 必在 + `--mcp-config` 必不在)。
- **解锁备忘**:strict 隔离下 `--allowedTools Read` 实测安全(C4)—— 未来长 prompt 卡 ARG_MAX 可走「短 prompt + reviewer 自己 Read + strict」;当前保持零工具 inline(自包含可靠性优先)。
- **观察方式**:发起时 stderr 即打印 log 路径(后台跑立即可见)· `tail -f <log>` 实时看 · log mtime = 心跳;emit 含 `process_log` 字段(成功/失败都有 · 失败时它就是验尸现场)。
- **重跑 append 叠加**(不覆盖):上一轮失败证据保留 · 全史可溯。

> 🔴 异质 review 的价值 = **独立视角采样盲点**;但同一独立性 = 它**没有完整上下文**(不懂本项目 DEV-RULES / 不知某设计是 intentional / 可能 hallucinate finding)。**照单全收 = 把外部模型的误判 import 进来**。主对话消费 external/异质 review(代码 / PRD / blueprint 通用)必须**逐条裁决**,不是 obey。
>
> 🔴 默认倾向是**相信**异质 review(它语气笃定、又被 teamwork 当门禁跑)—— 这正是要纠的偏:reviewer 的 finding 是**待核实的断言**,不是事实。

### 12.1 裁决三态(每条 external finding 落其一 · 带依据)

| 裁决 | 判据 | 处置 |
|---|---|---|
| ✅ confirmed | 回读实际代码 / AC / DEV-RULES 核实**确为真问题** | 修(进 fix-retry)· REVIEW.md 记 finding + 依据 |
| ❌ rejected | false positive / 误解 intentional 设计 / 与 DEV-RULES 冲突 / reviewer 没看全上下文 | **不修** · 🔴 **必记驳回依据**(指真实代码 / 规约 / 业务目标)· 不静默忽略 |
| ⏸️ deferred | 真问题但**本 Feature 范围外** | → `product-overview/PENDING.md` · 不本轮强塞 |

### 12.2 两头都是反模式

- ❌ **盲采(over-trust · 默认倾向)**:reviewer 说啥改啥 → import 误判 / 无谓 churn / 按错误 finding 改出 regression。
- ❌ **盲驳(under-trust)**:嫌麻烦全 dismiss 让它过门禁 → 异质 review 形同虚设(等于没跑 · 违 P0-154 初衷)。
- ✅ **裁决(adjudicate)**:每条独立核实 → 三态归类 → 带依据落 REVIEW.md。**举证责任在主对话** —— rejected 必给"为什么不是问题"的实证(真实文件 / 规约 / 目标),不是一句"我觉得没事"。

### 12.3 裁决 grounded 实际代码(不轻信 reviewer 断言)

- finding 是**待核实断言**:裁决前**回读真实代码 / PRD.AC / DEV-RULES 自己确认**,不轻信 reviewer 的转述/推断(同 [feature-planning](../docs/feature-planning.md) decisive 前提「核验真实文件 · 不轻信摘要」的 epistemics)。
- reviewer 与本项目 **DEV-RULES 冲突 → DEV-RULES 优先**(它是人定的项目真相;reviewer 给的是通用最佳实践 · 可能不适配本项目)。
- 高置信但与你核实结果**矛盾**的 finding:以**真实代码**为准 · 不被 reviewer 的笃定语气带走。

