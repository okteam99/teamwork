# Triage Stage：teamwork 入口分诊（v7.3.10+P0-106 重写为 5 mode 分诊）

> teamwork 的**真正入口** · 仅 1 件事：根据用户输入决定走哪个 mode（5 选 1）。
>
> 🟢 **Stage 性质**：极简 · 单一职责 · 不读项目级文件 · 仅看用户输入 + 命令前缀。
>
> 🔴 **替代关系**（v7.3.10+P0-106）：
> - 原 triage Step 1.5/1.6 Pull 路径 → 升级为 mode A · 在本 stage 内分诊
> - 原 triage Step 2-9（KNOWLEDGE / ADR / 角色 / state.json）→ 迁到 [prepare-stage.md](./prepare-stage.md) · 仅 mode B 触发
> - 原 init-stage.md Step 0 命令解析 → 迁到本 stage 动作 1
> - 原 init-stage.md Step 1 SKILL_ROOT / Step 1.2 / Step 2 / Step 3 → 各 mode 内部按需触发（mode B 走 prepare-stage · mode C/D 各自实现）

---

## 本 Stage 职责

**只做 2 件事**：

1. 解析命令前缀（`auto` / `继续` / `ship` / 普通）
2. 5 mode 分诊（仅看用户消息 + 命令前缀 · 不读任何 teamwork 项目级文件）

---

## Input Contract

### 必读输入

```
- 用户原始消息（自然语言 / `/teamwork ...` 命令参数）
- skill 加载已注入的 SKILL.md / RULES.md / FLOWS.md 等框架内部文档（已在主对话上下文 · 不需 read）
```

### 进入条件

```
- skill 已加载
- 用户输入消息已收到
- 红线 R8 写操作硬门禁生效
```

---

## 入口 Read 顺序

🔴 **不需要任何 Read**·triage 仅看用户消息 + 命令前缀。SKILL.md 知识地图 / RULES.md 已在 prompt 上下文。

---

## Process Contract

### 动作 1：解析命令前缀（原 init-stage.md Step 0 迁入）

```
/teamwork auto [需求]         → AUTO_MODE=true · 需求 = "[需求]"
/teamwork auto 继续           → AUTO_MODE=true · 继续进行中 Feature
/teamwork auto ship F{编号}   → AUTO_MODE=true · 进入 Ship Stage
/teamwork [需求]              → AUTO_MODE=false（手动 · 默认）
/teamwork 继续                → AUTO_MODE=false · resume 路径
/teamwork ship F{编号}        → AUTO_MODE=false · resume + jump-to-ship
/teamwork（空）               → AUTO_MODE=false · status 路径
/teamwork force-init          → 强制走全量校验（兜底）
```

🔴 **silent execution**（v7.3.10+P0-105）：不输出"命令解析结果 = X"。

### 动作 2：5 mode 分诊

根据用户消息 + 命令前缀路由到 5 mode 之一：

```
判定优先级（先匹配先生效）：

1. 命令前缀强制：
   ├── `继续` / `继续 F#` → C · resume
   ├── `ship F#` → C · resume + jump-to-ship
   ├── `（空）` / 用户消息含「现在到哪 / 看板 / Feature 状态」 → D · status

2. 用户消息推进动词强制：
   ├── 含「实现 / 创建 / 修复 / 改名 / 重构 / 删除 / 加 / 做」+ 明确动作 → B · execute

3. 用户消息讨论关键词：
   ├── 含「我感觉 / 我觉得 / 你怎么看 / 是不是 / 该不该 /
   │   想讨论 / 我有个想法 / 怎么改 / 哪种更合理 / X vs Y / 建议 / 推荐」
   │   ∧ 没有推进动词
   │   ∧ 没有 Feature 编号 / `auto` / `ship` 前缀
   │   → E · discuss

4. 用户消息查询关键词：
   ├── 含「看下 / 看一下 / 看看 / 调研 / 解释 / 怎么 / why /
   │   为什么 / 是否需要 / 是否应该 / 分析下 / 检查下 /
   │   定位 / 排查 / 解读 / 为什么报错」
   │   ∧ 没有推进动词
   │   ∧ 没有 Feature 编号 / `auto` / `ship` 前缀
   │   → A · query

5. 默认 → B · execute
```

### 5 Mode 行为速查

| mode | 路径 | 开销 |
|------|-----|------|
| **A · query** | 直接 grep / Read / 答 + 跟进引导（终止 · 不进后续 stage）| ~80 tokens |
| **B · execute** | 进 [prepare-stage](./prepare-stage.md) → 流程类型识别 → 业务 stage 链 | ~600-850 tokens |
| **C · resume** | 找 state.json + jump-to-stage（精准跳到 current_stage）| ~300 tokens |
| **D · status** | 加载 Feature 看板 + 输出（终止）| ~400 tokens |
| **E · discuss** | 开放讨论 + 选项 + 推荐 + 询问 → 升级 mode | ~150 tokens |

详细规范：
- A · query：本文件 § A · query 段
- B · execute：[stages/prepare-stage.md](./prepare-stage.md)
- C · resume：本文件 § C · resume 段
- D · status：本文件 § D · status 段
- E · discuss：[standards/discussion-mode.md](../standards/discussion-mode.md)

---

## A · query：事实查询

> 触发：用户问代码 / 项目事实 / 排查报错 · 不创建 Feature · 不写文件。

```
执行：
  1. pwd 校验（确保在项目内 · cwd 默认即可 · 不需检测 SKILL_ROOT）
  2. 排查类查询特殊路由（v7.3.10+P0-109 · 见下方 § 排查类查询）：
     用户消息含「报错 / 502 / 查 log / 排查 / 异常 / 服务挂了 / 查环境 / 查 DB / 查 Redis / 部署 / 回滚」
     → init_triage.py 在 triage 入口已确保 TROUBLESHOOTING.md 存在（v7.3.10+P0-126）
     → 按文档步骤执行；脚本 advisory `empty-skeleton` / `skeleton-created` 命中时答案末尾一句话提示补充
  3. 按用户关键词 grep / Glob 找实际代码 / 文件
  4. Read 找到的关键文件（≤5 个 / ≤500 行）
  5. 给初步答案（直接 · 不输出"流程步骤描述"）
  6. 按需补充 read：
     ├── 答案涉及"是否做过 X" → pull KNOWLEDGE.md 相关段
     ├── 答案涉及具体架构决策 → pull ADR INDEX
     └── 答案涉及多子项目 → pull teamwork_space.md
  7. 答案末尾加跟进引导：
     "如果你想动手 {改/做/修}，请回复 'Feature 流程' / 'Bug 流程' / 'Micro 流程'，
      我会切到 mode B 走完整 prepare。"

silent execution：
  ❌ 不输出"进入 mode A" / "现在直接定位 X"
  ❌ 不输出"按需直查：定位 ..."等计划叙事
  ❌ 不输出"找到核心链路 · 现在查 ..."等进度叙事
  ✅ 主对话只有：实际答案 + 跟进引导
```

### 排查类查询特殊路由（v7.3.10+P0-109）

> 触发关键词：`报错 / 502 / 5xx / 异常 / panic / fatal / 崩溃 / 服务挂了 / 查 log / 查日志 / 排查 / 调试 / 查环境 / 查 DB / 查数据库 / 查表 / 查 Redis / 查缓存 / 部署 / 回滚 / 上线`

**优先级 1：固定 read 项目根 TROUBLESHOOTING.md**（v7.3.10+P0-126：tools/init_triage.py 在 triage 入口已物化创建 + 空骨架检测 · 必存在）

```
查 init_triage.py 输出的 project_files["TROUBLESHOOTING.md"]：
  ├── is_empty_skeleton=false → silent read · 按文档步骤执行（kubectl / psql / redis-cli / curl 等具体命令）
  │              · 遵守文档里的安全约束（production 写操作 ⏸️ 用户授权 · 红线 R8 协同）
  │              · 不复述 secret / token / 密码到主对话
  │
  └── is_empty_skeleton=true（advisory.topic ∈ {empty-skeleton, skeleton-created}）
                → PMO 用通用方法尝试排查（kubectl 探索 / grep 代码 / curl 接口）
                + 答案末尾**一句话**提示用户：
                  "💡 项目根 TROUBLESHOOTING.md 是 teamwork 自动创建的空骨架 ·
                   你可以按项目栈补充具体命令（kubectl / psql / 部署回滚链等）·
                   teamwork 下次排查时会自动 read 已填内容。"
```

🔴 **空骨架检测**（v7.3.10+P0-126 物化）：
- 由 [tools/init_triage.py](../tools/init_triage.py) 完成 · 硬编码 marker = "本文是 teamwork prepare-stage 自动创建的空骨架"
- PMO 不再自己 grep · 直接读脚本返回 `is_empty_skeleton` 布尔值
- 治本旧 bug：spec 让 grep `{TODO 由用户填写}` 但模板里实际无此字符串 → grep 永不命中 → 永远误判已填

🔴 **不强推具体命令**（v7.3.10+P0-109）：
- teamwork 提供空骨架（4 段结构）但**不规范具体命令**（每个项目栈不同 · K8s vs Docker vs Serverless）
- 用户按项目实际维护内容
- 类比 [teamwork_space.md 模板模式](../templates/teamwork-space.md)：teamwork 创建空骨架 · 具体值用户填

🔴 **silent read 原则**：
- ✅ 不输出"我现在 read TROUBLESHOOTING.md"
- ✅ 不输出"已读文档 · 按 § X 执行"
- ✅ 直接给排查结果

🔴 **production 写操作**（与红线 R8 协同）：
- 即便 TROUBLESHOOTING.md 列出了 production 写操作命令 · PMO 仍必须 ⏸️ 用户暂停点明确授权
- TROUBLESHOOTING.md § 八「安全约束」是软指引 · 红线 R8 是硬门禁

---

## C · resume：接续 Feature

> 触发：命令前缀 `继续` / `ship F#` · 已有进行中 Feature。

```
执行：
  1. SKILL_ROOT 检测（这时才需要 · 后续 read state.json 用）
  2. 找 docs/features/{Feature}/state.json
     ├── 用户指定了 Feature 编号 → 直接定位
     └── 用户说"继续"未指定 → 按 updated_at 最新 + 非 completed 的 Feature
  3. Read state.json → 取 current_stage
  4. 跳过 prepare-stage（已加载过 · 用户在已建立的 Feature 里）
  5. 直接进入 current_stage 的入口实例化（如适用）
  
silent execution：
  ❌ 不输出"进入 mode C" / "现在恢复 F032"
  ✅ 直接给当前 Stage 的工作内容（如 Goal-Plan 子步骤 N / Dev RD 身份切换）
```

---

## D · status：Feature 看板

> 触发：`/teamwork`（空命令）/ 用户问"现在到哪"。

```
执行：
  1. SKILL_ROOT 检测（read teamwork_space.md / 各 state.json 用）
  2. 加载项目空间（teamwork_space.md）
  3. 扫描各子项目 docs/features/*/state.json（current_stage / updated_at / blocking）
  4. 排除 current_stage == "completed"
  5. 输出 Feature 看板（按 updated_at 降序）
  6. 🔴 有进行中 Feature → 给优先级建议（💡 + 📝）
     无进行中 Feature → 等待新需求
  7. 终止（不进任何 stage）

输出格式：
  📋 Feature 状态看板
  | 子项目 | Feature | 当前阶段 | 合法下一阶段 | 阻塞 | 最后更新 |
```

---

## B · execute：进入 prepare-stage

> 触发：默认 / 推进动词 / `auto X`。

```
执行：直接进入 stages/prepare-stage.md · 由 prepare-stage 完成：
  - SKILL_ROOT / CLAUDE.md / 项目空间 / KNOWLEDGE / ADR
  - 流程类型识别（5 种）
  - 流程感知懒加载
  - state.json 创建
  - 进入对应业务 stage 链
```

详见 [stages/prepare-stage.md](./prepare-stage.md)。

---

## E · discuss：想法讨论

> 触发：含 E 关键词 + 无推进动词 + 无 Feature 编号。

```
执行：详见 standards/discussion-mode.md。

简略：
  1. PMO 综合视角评估（引用 PL / 架构师 / QA 等多角色思考维度 · 不切身份）
  2. 按话题路由 silent read（PROJECT / ROADMAP / KNOWLEDGE / ADR / state.json 等）
  3. 输出：观点 + 论证 + 选项 + 推荐 + 询问
  4. 用户拍板后升级 mode（B/A/C/D）
  5. 不写任何文件 · 不创建 Feature · 不进 stage 链
```

详见 [standards/discussion-mode.md](../standards/discussion-mode.md)。

---

## Output Contract

### 输出产物

```
A · query   → 答案 + 跟进引导（终止）
B · execute → 跳转到 prepare-stage（产物由 prepare-stage 决定）
C · resume  → 跳转到 current_stage（产物由该 stage 决定）
D · status  → Feature 看板（终止）
E · discuss → 选项 + 推荐 + 询问（用户拍板后升级 · 终止本轮）
```

---

## 主对话输出 Tier 应用

```
Tier 1（必看）：
  - 实际答案（A）/ 看板（D）/ 当前 Stage 工作内容（C）/ 选项 + 推荐（E）
  - prepare-stage 的关键产物（B 路径触发）

Tier 2（命中折叠）：
  - 暂停模板（如 E · discuss 的"回 1/2/3"）

Tier 3（默认不输出 · v7.3.10+P0-105 silent）：
  - "进入 mode X" / "Step Y 进行中" / "现在 read Z" 等仪式叙事
  - 命令解析中间状态 / 路由判定过程
```

详见 [standards/output-tiers.md](../standards/output-tiers.md) 反模式 5。

---

## 与历史架构的对应

```
原 triage 9 步 → 拆分到：
  Step 1   用户承接（→ 隐式承接 · 本文件不输出）
  Step 1.5 意图轻重分流 → 升级为 5 mode 分诊（含 A/B/C/D/E）
  Step 1.6 Pull 路径 → 本文件 § A · query
  Step 2   KNOWLEDGE 扫描 → prepare-stage Step 5
  Step 3   ADR 扫描 → prepare-stage Step 6
  Step 4   角色 + 外部模型 → prepare-stage Step 9-10（流程懒加载）
  Step 5   流程类型识别 → prepare-stage Step 7
  Step 6-7 流程描述 → prepare-stage Step 12
  Step 8   双对齐暂停 → prepare-stage Step 13
  Step 9   state.json 创建 → prepare-stage Step 14（流程懒加载）

原 init 5 步 → 拆分到：
  Step 0   命令解析 → 本文件动作 1
  Step 1   SKILL_ROOT 检测 → 各 mode 按需（B/C/D 路径触发）
  Step 1.2 版本校验 → prepare-stage Step 2
  Step 2   项目空间 → prepare-stage Step 3
  Step 3   Feature 看板 → 本文件 § D · status（仅 mode D 触发）
```

末。
