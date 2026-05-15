# v8.0 Manifesto · Code-driven Orchestration

> teamwork 从「AI 多角色协作框架」转型为「状态机驱动的 AI 开发编排器」。
> 本文是 v8.0 重构的设计宪法。所有细节文档以此为准。

---

## 一、根本判据(取代 v7 所有划界原则)

**可枚举的规则进脚本,不可枚举的判断留 AI。**

| 类别 | 例子 | 归宿 |
|------|------|------|
| 可枚举:状态转移、入口前置、出口产物、字段 schema、流程闭集、暂停点协议、暂停黑名单、命令格式 | 9 红线中 16/17 子条目 | `tools/state.py` |
| 不可枚举:PRD 是否完整、架构是否合理、代码是否优雅、暂停点建议怎么写、ADR 是否值得记录 | R3 PMO 统一承接 | AI 自决 |
| 项目主权领域:代码布局、业务术语、排查命令 | src/ docs/ tests/、KNOWLEDGE.md 内容 | 用户填,teamwork 按需读 |

---

## 二、范式切换

### v7 范式(被替换)
```
PMO 凭记忆 + 读 spec markdown + cite 自觉
       ↓
   按记忆调度 stage / 调度 role
       ↓
state.py 被动记录(只做状态机骨架校验)
```

**问题**:
- spec 累积膨胀,加 1 删 1 / 文件 300 行 / 红线生命周期等元规则全是抗膨胀工程
- AI 心智过载,跨 stage 时 cache 失效,凭印象编造
- 100+ 个 P0 patch 大半在治"AI 凭印象出错"的具体 case

### v8 范式
```
AI 跑 state.py xx-stage-start
       ↓
state.py 主动校验 + 主动告知下一步(stdout JSON + markdown brief)
       ↓
AI 按 state.py 指示执行(写文档 / 跑命令 / dispatch subagent)
       ↓
AI 跑 state.py xx-stage-complete
       ↓
state.py 校验产物 + 自动转移到下一 stage + 输出 next-stage brief
```

**收益**:
- AI 不读 spec markdown,不需要记忆,跑命令即知做什么
- 规则进代码 → 单元测试覆盖 / 可重构 / 可静态分析
- AI 模型迭代时,失效规则只需删代码

---

## 三、state.py 三类命令边界

```
1. 初始化类
   ├── init-feature        创建 state.json
   ├── triage              session 入口 5 mode 分诊
   └── prepare             mode B 重型准备

2. 状态流转类(每 stage 一对)
   ├── goal_plan-start / goal_plan-complete
   ├── ui_design-start / ui_design-complete
   ├── panorama_design-start / panorama_design-complete  (仅 Planning)
   ├── blueprint-start / blueprint-complete
   ├── blueprint_lite-start / blueprint_lite-complete    (仅敏捷需求)
   ├── dev-start / dev-complete
   ├── review-start / review-complete
   ├── test-start / test-complete
   ├── browser_e2e-start / browser_e2e-complete
   ├── pm_acceptance-start / pm_acceptance-complete
   └── ship-start / ship-phase / ship-complete            (Ship 内部多动作)

3. 逃生 / 维护类
   ├── *-start --bypass --reason --user-confirmed --missing  逃生通道
   ├── recover --reason       state.json 被外部改后认证 checksum
   ├── snapshot               只读查询
   ├── validate               schema 全量校验
   ├── raw-read / raw-write   逃生舱(用户主动)
```

**18 现有命令 → ~25 v8 命令**(数量增,但语义清晰、职责正交)。

**全部删除**:
- `enter-stage` / `satisfy-gate` / `complete-stage`(通用命令 → 各 stage 专属)
- `ship-sanitize` / `ship-push` / `ship-confirm-merged` / `ship-cleanup` / `ship-closed`(→ `ship-phase --action`)
- `pm-decision`(→ `pm_acceptance-complete --decision`)
- `add-concern` / `bug-frontmatter` / `micro-validate`(内部化,不暴露 user-facing)

---

## 四、xx-stage-start 通用契约

### 必传参数

```
--feature <path>     feature artifact_root 路径
```

### 逃生参数(全部必带)

```
--bypass                       逃生标志
--reason <非空字符串>          进 concerns WARN
--user-confirmed               缺则物理拦截(防 AI 自决)
--missing <逗号分隔列表>       明确跳过哪些前置
```

### 内部校验序列

```
1. state.current_stage == 上一 legal stage  (转移合法)
2. state.completed_stages 包含上一 stage
3. 上一 stage 的 stage_contracts.output_satisfied == true
4. stage 专属前置 artifact 存在(file existence)
5. stage 专属 evidence(git history / dispatch_log / 外部工具运行结果)
6. 按 state.flow_type 选择校验路径(Feature / Bug / 敏捷 / Micro / Planning / 排查)
```

任一失败 → `verdict: FAIL` + `missing_prerequisites[]` + 每条 `hint`。

### 输出 schema

```json
{
  "verdict": "PASS" | "FAIL",
  "stage": "dev",
  "phase": "start",
  "transition": "blueprint → dev",
  "missing_prerequisites": [
    {
      "id": "prd_reviewed",
      "check": "state.stage_contracts.goal_plan.output_satisfied == true",
      "actual": false,
      "hint": "返回 goal_plan stage 完成 PRD review · 跑 `state.py goal_plan-complete`",
      "auto_fixable": false
    }
  ],
  "auto_actions_executed": [
    "enter-stage dev"
  ],
  "next_action_brief": "..."   // PASS 时:markdown · 告诉 AI 这 stage 要做什么
}
```

### PASS 时的 next_action_brief

```markdown
## Dev Stage · 你要做什么

### Telos
按 TECH.md 实现代码 · TDD 红绿循环 · 单测全绿 · auto-commit。

### 必读 artifacts (按出现顺序)
1. {Feature}/PRD.md          - 需求与 AC
2. {Feature}/TECH.md         - 技术方案
3. {Feature}/TC.md           - 测试用例(QA 起草 · 实现时参照)
4. KNOWLEDGE.md (项目根)     - 项目级 Gotcha / Convention
5. UI.md + preview/*.html (如 ui_design 已完成) - UI 还原依据

### 必跑工具
- 项目 build 命令(从 PROJECT.md 或 .teamwork_localconfig.md 读)
- 项目 test 命令
- TDD 红绿循环

### 必产物
- 代码改动 commit (auto-commit hash 必传 dev-complete)
- 测试代码 commit
- 自查通过(roles/rd.md 自查清单 → 已编码到 dev-complete 校验)

### 暂停点
- 无(dev stage 内部全自动 · 完成后 dev-complete 自动转 review)

### 完成方式
跑 `state.py dev-complete --feature {path} --auto-commit <hash> --artifacts <...>`
```

---

## 五、xx-stage-complete 通用契约

### 必传参数

```
--feature <path>         feature artifact_root 路径
--auto-commit <hash>     stage 产出的 git commit 锚定(防编造)
--artifacts <逗号分隔>   本 stage 实际产出文件清单
```

### 可选参数

```
--cite <field1,field2,...>  AI 声明读了什么 spec(进 cited_fields)
```

### 内部校验序列

```
1. state.current_stage == 本 stage
2. stage 专属产物存在(file existence + frontmatter schema)
3. auto-commit 在 git history(`git cat-file -e <hash>`)
4. artifacts 在 commit changeset 内(防 AI 编造 hash)
5. 外部评审 artifact 存在性(blueprint/review/test 阶段)
6. 测试运行 evidence(test-complete 必检 pytest/jest stdout)
7. AC↔Test 覆盖(blueprint-complete / test-complete 跑 verify-ac.py)
```

### 自动副作用

```
1. 自动 satisfy 三 gate (input/process/output_satisfied = true)
2. 自动设 stage_contracts.X.completed_at
3. 自动 auto_commit 入 stage_contracts.X
4. 自动写 review-log.jsonl 一条 stage_completed 记录
5. 自动 enter-stage 转移到下一 stage(legal_next_stages 唯一时)
6. 多 legal 选项时(如 review 可去 test 或回 dev)→ 输出选择菜单 · 不自动转移
```

### 输出 schema

```json
{
  "verdict": "PASS" | "FAIL",
  "stage": "dev",
  "phase": "complete",
  "missing_artifacts": [...],
  "satisfied_gates": ["input", "process", "output"],
  "transitioned_to": "review",
  "next_stage_brief": "..."    // 下一 stage 的 next_action_brief
}
```

---

## 六、错误处理协议

### 重试循环(PMO 优先按建议来)

```
xx-stage-start FAIL
   ↓
state.py 返回 missing_prerequisites[] · 每条带 hint
   ↓
PMO 按 hint 自动执行修复(silent 执行 · 不打扰用户)
   ↓
重跑 xx-stage-start
   ↓
   ┌── PASS  → 继续下一 stage 工作
   │
   └── FAIL → 看新 hint → 再修(最多 3 次)
   
   重试 3 次仍 FAIL
      ↓
PMO 输出 ⏸️ 暂停点给用户:
   "Stage X 入口缺 {missing_items} · 重试 3 次未解决
    1. 继续尝试(建议:具体下一步动作)
    2. 跳过前置 · ⚠️ 风险:{state.py 自动评估的影响}
    3. 其他指示"
   ↓
用户回 "2"
   ↓
PMO 调:
   state.py xx-start --feature {path} 
                     --bypass 
                     --reason "用户确认跳过 {具体原因}" 
                     --user-confirmed 
                     --missing prd_reviewed,external_review
   ↓
state.py:
   ✅ 通过 stage-start
   ✅ 自动写 concerns WARN
   ✅ 自动追加 bypass_log[] 到 state.json
```

### bypass_log schema

```json
{
  "bypass_log": [
    {
      "stage": "dev",
      "phase": "start" | "complete",
      "at": "2026-05-14T08:16:01Z",
      "missing": ["prd_reviewed", "external_review"],
      "reason": "<用户提供的非空字符串>",
      "user_confirmed": true,
      "retry_count_before_bypass": 3,
      "concerns_id": "<对应 concerns 条目时间戳>"
    }
  ]
}
```

### --user-confirmed 的物化语义

state.py 无法物理验证"用户真的说了",但:
- 此 flag 的存在性 = AI 声称用户已确认
- 缺此 flag + 带 --bypass → state.py 立即 FAIL(防 AI 自决逃生)
- 审计时若发现 AI 自加此 flag(对话历史中无用户确认) = 红线违规

---

## 七、state.json 新 schema(v8)

### 顶层字段(变化部分)

```json
{
  "schema_version": "v8.0",                    // 新增:替代 v7.3.10+P0-X 累积版本号
  "feature_id": "DEV-F001-example",
  "flow_type": "Feature",                       // 6 enum 闭集
  "current_stage": "dev",
  "completed_stages": ["goal_plan", "blueprint"],
  "legal_next_stages": ["review"],
  
  "stage_contracts": {
    "dev": {
      "started_at": "...",
      "completed_at": "...",
      "duration_minutes": 25,
      "input_satisfied": true,
      "process_satisfied": true,
      "output_satisfied": true,
      "auto_commit": "abc123",
      "artifacts": ["src/foo.py", "tests/test_foo.py"],
      "cited_specs": ["roles/rd.md", "standards/tdd.md"],
      "evidence": {                              // v8 新增:事实证据闭环
        "git_commit_exists": true,
        "artifacts_in_commit": true,
        "tests_run_stdout": "...",
        "tests_exit_code": 0
      }
    }
  },
  
  "bypass_log": [...],                          // v8 新增
  
  "concerns": [...],                            // 保留
  "review_log_path": "review-log.jsonl",        // 保留
  
  "ship": {...},                                // 保留(ship 子状态机)
  "environment_config": {...},                  // 保留
  "worktree": {...},                            // 保留
  "blocking": {...}                             // 保留
}
```

### 删除的字段(v8 不再使用)

```
planned_execution         (Execution Plan 进 state.py 内部 · 不再 AI 写 state)
executor_history          (并入 review-log.jsonl)
detection_evidence        (并入 stage_contracts.X.evidence)
```

---

## 八、暂停点二分(自动 vs 用户确认)

### 自动流转(state.py 内部处理 · 不暴露)

stage 完成 + legal_next 唯一 → 自动 enter-stage 转移 → 调用 next stage 的 -start

### 用户暂停(state.py emit · AI 复制粘贴给用户)

state.py xx-stage-complete 在以下情况 emit 暂停点 markdown:

```
1. legal_next_stages 多选(review → test or dev / pm_acceptance → ship or dev)
2. PM 验收三选项(approved_and_ship / approved_no_ship / rejected_with_feedback)
3. Ship Phase 1 → Phase 2 间断点(等用户在平台 merge)
4. 重试 3 次仍 FAIL → 逃生选项
```

每个暂停点 state.py 输出标准 markdown 块:

```markdown
⏸️ {pause_point_name}

📚 决策参考
- /abs/path/PRD.md
- /abs/path/TECH.md
- /abs/path/test-report.md

🔢 请选择
1. 💡 {推荐项 + 推荐理由}
2. {其他选项}
3. ...
N. 其他指示

📝 回复:数字(如 `1`) · 多决策点 `1A 2B`
```

AI 复制 state.py 输出的暂停点 markdown 给用户,**自己不组装格式**。

---

## 九、Stage 间过渡(next_stage_brief)

完成上一 stage 后,state.py 自动 emit 下一 stage 的 brief。

brief 内容由 state.py 按 stage 模板渲染,**不依赖 AI 读 markdown spec**。

模板内含:
- Telos(为什么这个 stage 存在)
- 必读 artifacts(按出现顺序)
- 必跑工具(从 .teamwork_localconfig.md / PROJECT.md / package.json 等推断)
- 必产物
- 完成方式(具体 state.py 命令)

---

## 十、版本号策略

### v7 → v8 不向下兼容

```
v7.3.10+P0-156 → v8.0.0  (Code-driven Orchestration)
```

理由:
- 公共接口破坏(enter-stage / satisfy-gate / complete-stage 删除)
- state.json schema 变更(schema_version 标识)
- skill markdown 大幅减负(老 spec 引用失效)

### 老 Feature 的 state.json 迁移

```
state.py migrate-v7-to-v8 --feature <path>
```

读老 schema → 转换字段 → 写新 schema_version=v8.0
未跑迁移的老 Feature → state.py v8 拒绝处理 + 提示跑 migrate。

---

## 十一、与红线 R1-R9 的最终归宿

### 11.1 · 归宿表

| 红线 | v7 形态 | v8 归宿 |
|------|--------|---------|
| R1 代码写权归 RD | spec 自觉 | state.py 校验"写操作时身份切换"(改后端可加 hook 拦截) |
| R2 流程类型闭集 | spec 自觉 | `init-feature --flow-type` enum |
| R3 PMO 统一承接 | spec 自觉 | **保留 AI 自决**(不可枚举) |
| R4(a) 不简化 | spec 自觉 | state.py 按 flow_type 强制 stage 链 |
| R4(b) 不膨胀(容量焦虑黑名单) | spec 自觉 | state.py emit 时不出现这些措辞 |
| R4(c) 必给步骤描述 | spec 自觉 | state.py xx-start 自动输出 next_action_brief |
| R5(a) 暂停必等确认 | spec 自觉 | state.py emit 暂停点 markdown,AI 不会自动续写 |
| R5(b) 必给建议 + 编号 | spec 自觉 | state.py emit 暂停点强制格式 + SKILL.md § 暂停点标准模板(PMO 主对话兜底) |
| R5(c) 状态行 + 决策参考 | spec 自觉 | state.py 每命令尾部 emit 状态行 + 暂停点强制 📚 决策参考 |
| R6 Feature Planning 不出代码 | spec 自觉 | Feature Planning 不进状态机(init-feature reject)· 由 PMO 主对话执行 |
| R7(a) 实测输出 | spec 自觉 | state.py xx-complete 必传 --auto-commit + 校验 commit 存在 |
| R7(b) 声明即承诺 | spec 自觉 | state.py xx-start emit "你应该做什么"(替代 Execution Plan) |
| R7(c) evidence-binding | state.json schema | 强化:全 stage 必检 evidence 字段 + checksum stamp |
| R8(a) 流程入口门禁 | spec 自觉 | state.py 在 prepare 完成前拒绝 stage-start |
| R8(b) Subagent dispatch 预检 | spec 自觉 | state.py 内部封装 dispatch(AI 不直接调 Task tool) |
| R8(c) Ship Phase 1 CLI-first | state.py schema | 已物化(P0-113) |
| R9 session bootstrap 必跑 triage | init_triage.py | tools/bootstrap.py + PMO 按 TRIAGE.md 分诊 |

**16/17 红线进代码**。仅 R3 留 AI 自决 · 加 R4 / R5(b) / bypass 等行为约束(SKILL.md § PMO 软约束 兜底)。

### 11.2 · 详细 rationale(从 RULES.md v8.x 迁入 · v8.15 RULES.md 删除)

#### R1 · 代码写权归 RD

代码 / 测试 / 构建配置写操作必须由 RD 角色执行。
- 多角色分工 = 不同 checklist。让 PM 写代码 / 让 RD 起草 PRD · 都会让该角色的关注点被另一职责淹没。
- **外部模型例外**:codex / claude / gemini 等外部模型仅只读评审(OpenAI ToS 合规)。
- **Ship Stage 例外**:第二段 finalize 允许 PMO push merge_target(严格限定 state.json + BUG-REPORT.md frontmatter)。

#### R2 · 流程类型闭集

6 种流程(Feature / Bug / Micro / 敏捷需求 / Feature Planning / 问题排查)是经过实证的闭集。
防止 AI 发明"Feature 变更""敏捷 Bug"等变体 · 每种变体都引入隐藏路径 · 长期累积成不可维护状态机。

#### R3 · PMO 统一承接(唯一软约束)

所有用户输入由 PMO 角色先承接 · 禁止其他角色直接响应。
多角色对话场景下 · 如果用户输入直接打到 RD/Designer · 容易让角色越权(RD 直接接需求 → 跳过 PM 的 PRD)。

state.py 无法物理判断"谁在响应" · 依赖 AI 自觉。这是 9 红线中唯一仍是软约束的一条。

#### R4 · 流程边界

3 子条:
- **(a) 不简化**:每种需求走对应级别的完整流程 · "简单""文件少""无风险" 不构成跳过理由
- **(b) 不膨胀**:自动流转节点禁止插入暂停 · "回合边界""容量预算""让用户看进度" 不构成暂停理由
- **(c) 必给步骤描述**:选定流程类型后必须给完整步骤(阶段链 + 每个阶段大致做什么 + 预期产出)

简化 = 失去多视角检查 · 膨胀 = AI 凭印象塞暂停点骚扰用户。

#### R5 · 暂停点协议

3 子条:
- **(a) 暂停必等确认**:暂停点必须等用户明确回复 · 不能 AI 自行决定
- **(b) 必给建议 + 编号**:任何要求确认的内容必须含 💡 推荐项 + 📝 理由 + 编号化(详 SKILL.md § 暂停点标准格式)
- **(c) 状态行 + 决策参考**:暂停点 final response 必须含状态行 + 📚 决策参考绝对路径

无编号 = 用户要打字 · 无推荐 = 用户要现做决策 · 无路径 = 用户找不到要看的文件。这些都把心智负担转给用户。

#### R6 · Feature Planning 不出代码

Feature Planning 流程只产 PROJECT.md / ROADMAP.md / sitemap.md · 禁止产代码 · 禁止自启 Feature 流程。
Planning 是产品方向决策 · 不应该 AI 自动跳过决策直接开 dev。

v8 物化:Feature Planning 不进状态机 · `init-feature --flow-type "Feature Planning"` 被 reject · 由 PMO 主对话执行(详 docs/feature-planning.md)· 物理上不会出代码。

#### R7 · 证据闭环

3 子条:
- **(a) 实测输出**:声称"完成"必须附实际命令 stdout / 测试结果 / 构建输出
- **(b) 声明即承诺**:Stage 开始前必须输出 Execution Plan(approach / rationale / steps remaining / estimated)
- **(c) 事实字段 evidence-binding**:外部观察的判定(commit hash / mr_url / test exit-code 等)必须含 command + stdout + exit_code + timestamp

AI 会"凭印象"声称完成 / 声称读了规范 / 声称跑了测试。证据闭环是物理拦截的根基。

#### R8 · 写操作硬门禁链

3 子条:
- **(a) 流程入口门禁**:PMO 未输出初步分析前禁止任何写操作
- **(b) Subagent dispatch 预检**:dispatch 前完成 L1/L2/L3 预检 · 未通过不得 dispatch
- **(c) Ship Phase 1 CLI-first**:push 完后必检 gh/glab CLI · 可用必走 CLI 创 MR · git push 输出的 hint URL 是 trap

写操作不可逆 · 一旦进入"AI 自驱写代码"模式 · 错误会快速放大。门禁链是给用户的最后干预机会。

#### R9 · session bootstrap 必跑 triage

新 session 首条 PMO 响应前必先按 TRIAGE.md 完成 5 mode 分诊 · 在响应中输出 audit_line。
session 启动是 AI 最容易"凭印象"的时刻(没读任何 spec · 没看 state.json)。triage 是兜底物化。

v8 物化:
- `tools/bootstrap.py` session 入口必跑(silent · 系统维护)
- TRIAGE.md 是 PMO 主对话行为权威(triage **不是** state.py 命令)
- audit_line 由 PMO 自己输出 · 用户监督

### 11.3 · bypass 协议

```
PMO 重试 3 次仍 FAIL → 暂停点询问用户 → bypass:

state.py xx-start --bypass --reason "<用户提供>" --user-confirmed --missing <ids>
   ↓
state.py:
  - 校验 --user-confirmed 必带(防 AI 自决)
  - 校验 --missing 覆盖实际 missing
  - 通过 + 自动写 bypass_log[] + concerns WARN(完整审计闭环)
```

`--user-confirmed` 的物化语义:state.py 无法物理验证"用户真的说了" · 但此 flag 的存在性 = AI 声称用户已确认。审计时若发现 AI 自加此 flag(对话历史无用户确认)= 红线违规。
