# Teamwork

状态机驱动的 AI 开发编排器。`state.py` 主动校验 + 主动告知 —— AI 跑命令即知做什么,不再读 spec 凭记忆。

[English](./README-EN.md) · Version: **v8.0**

---

## 设计哲学

**可枚举的规则进脚本,不可枚举的判断留 AI。**

| 类别 | 例子 | 归宿 |
|------|------|------|
| 可枚举 | 状态转移、入口前置、出口产物、字段 schema、流程闭集、暂停点协议 | `tools/state.py`(物化校验) |
| 不可枚举 | PRD 完整性、架构合理性、代码优雅度、暂停点建议文案 | AI 自决 |
| 用户主权 | 代码布局、业务术语、排查命令 | 用户填,teamwork 按需读 |

### v7 → v8 范式切换

```
v7(被替换):                          v8:
PMO 凭记忆 + 读 spec markdown            AI 跑 state.py xx-start
  ↓                                      ↓
按记忆调度 stage / role                  state.py 主动校验 + 主动告知 brief
  ↓                                      ↓
state.py 被动记录                        AI 按 brief 执行 → 跑 xx-complete
                                         ↓
                                         state.py 校验产物 + 自动转下一 stage
```

v8 把 9 红线中 16/17 子条目物化进 `state.py` —— 规则从"靠 AI 自觉"变成"工具强制"。

### 多角色协作机制

单角色覆盖多视角时会互相遮蔽 —— PM 的"用户想要"盖住 QA 的"边界情况",架构师的"优雅"盖住 RD 的"交付期"。Teamwork 按专业分配角色,PMO 编排:

- **创建-批评循环**:PM 写 PRD → PL 从业务方向批评 → PM 修订,单角色单轮产出会跳过被自身视角遮蔽的盲区
- **注意力重分配**:切换角色 = 切换 checklist = 激活不同评价维度
- **强制重读**:角色切换迫使 AI 带着新问题重读同一份文档
- **异质模型 Review**:评审引入异质模型(claude 主窗口时 external = codex,反之亦然),跨模型视角揭露同模型自评盲区

你只需提需求 + 关键节点做决策。

---

## 第一次用

### 安装

```bash
# 自动检测宿主环境(Claude Code / Codex CLI / Gemini CLI)
npx skills add okteam99/teamwork
```

session 启动时 `tools/bootstrap.py` 自动维护项目骨架(KNOWLEDGE / TROUBLESHOOTING / GLOSSARY)、宿主指令文件注入段、版本校验 —— 全程 silent,不打扰用户。

### 升级

```bash
npx skills update okteam99/teamwork
```

### 启动一个流程

```bash
# Feature(完整需求 → 设计 → 开发 → 测试 → 验收 → 交付)
/teamwork 实现用户登录功能

# 敏捷需求(≤5 文件、方案明确、无 UI/架构变更)
/teamwork 在用户列表增加导出 CSV 按钮

# Micro(零逻辑变更的文案 / 样式 / 资源替换)
/teamwork 把首页 logo 换成新的图片

# Bug 处理
/teamwork 登录页面在手机端返回 500 错误

# 问题排查(不产出代码,只定位根因)
/teamwork 最近 3 天生产环境 P95 延迟变高了,帮我看看

# Feature 规划(拆 ROADMAP,不产出代码)
/teamwork 规划电商推荐系统
```

### 你做什么 vs AI 做什么(Feature 流程)

| 阶段 | 你做的事 | AI 做的事 |
|------|----------|-----------|
| 起点 | 给一句话需求 | PMO 5 mode 分诊 + 流程类型识别 + prepare 子流程 emit 4 项配置暂停点 |
| 确认配置 | 回 `ok` / 改某项 | PMO 建 worktree + `state.py init-feature` 进状态机 |
| goal | 等 / 纠偏 | PM 起草 PRD + 多角色并行评审 + 收敛 |
| 确认 PRD | 回 `ok` | — |
| ui_design(可选) | 等 | Designer 产出 UI + preview + 同步全景 |
| blueprint | 等 | RD 起草 TECH + QA 起草 TC + 架构师 + 异质模型评审 |
| dev | 等 | RD 按 TDD 实现 + 单测 + 机器校验 |
| review | 等 | 架构师 + QA + 异质模型三视角独立 Review |
| test | 等(启应用如需)| QA integration + api-e2e |
| pm_acceptance | 回 `ok` / 反馈 | PM 角度逐条 AC 验收 + 三选项决策 |
| **ship Phase 1** | 平台点 merge | sanitize → push 分支 → CLI 创 MR → ⏸️ 等合并 |
| **ship Phase 2** | 等 | 验证合并 + finalize + 清理 worktree → ✅ completed |

典型 Feature 暂停点:**3-5 个**。

---

## 5 mode 入口分诊

teamwork 入口是 PMO 主对话的 **5 mode 分诊**(不是 state.py 命令,详 [SKILL.md § Triage 入口规范](./skills/teamwork/SKILL.md)):

| mode | 触发场景 | 行为 | 移交去向 |
|------|---------|------|---------|
| **A · query** | 看下 / 查 / why / 排查 / 解释 | grep + Read 答 + 跟进引导 | 主对话闭合 |
| **B · execute** | 实现 / 修复 / 改 / 做 / 开发 | audit_line + 识别 execute 意图 | → prepare 子流程 |
| **C · resume** | 继续 / resume / ship F032 | 找 state.json + jump 到 current_stage | → 状态机 |
| **D · status** | status / 现在到哪 / 看板 | 加载 Feature 看板 + 输出 | 主对话闭合 |
| **E · discuss** | 我感觉 / 你怎么看 / X vs Y | 综合视角讨论 + 选项 + 推荐 | 主对话闭合(收敛后可升 B) |

mode B 识别后走 **prepare 子流程**([docs/prepare.md](./skills/teamwork/docs/prepare.md)):流程类型识别 → worktree 决策 → emit 4 项配置暂停点(Feature ID / merge_target / worktree path / branch)→ 用户确认 → `git worktree add` + `state.py init-feature`。

## 6 流程类型 + stage 链

| 流程 | 适用场景 | stage 链 | 默认暂停点 |
|------|----------|----------|-----------|
| **Feature** | 完整功能开发 | goal →(ui_design)→ blueprint → dev → review → test →(browser_e2e)→ pm_acceptance → ship | 3-5 |
| **敏捷需求** | ≤5 文件 + 方案明确 + 无 UI/架构变更 | goal → blueprint_lite → dev → review → test → pm_acceptance → ship | 2-3 |
| **Bug** | 线上/本地缺陷 | dev → review → test → pm_acceptance → ship | 3-4 |
| **Micro** | 零逻辑变更(文案/样式/资源/配置) | dev → pm_acceptance → ship | 2 |
| **Feature Planning** | 从产品目标拆 ROADMAP | 不进状态机 · PMO 主对话执行 | 1 |
| **问题排查** | 仅定位根因 | 不进状态机 · 类 mode A | 0-1 |

进状态机的 4 类(Feature / 敏捷需求 / Bug / Micro)走 `state.py` stage 链;Feature Planning / 问题排查不进状态机,由 PMO 主对话执行。

---

## 进阶使用

### 流程控制

```bash
/teamwork status      # 查看当前状态(走到哪 / 下一步 / 待决策点)
/teamwork 继续         # 恢复被中断的流程(靠 state.json · 不依赖对话记忆)
```

暂停点选项编号化(💡 推荐项标第一),**回复一个数字即可**。全局快捷词:`ok` = 按推荐建议、`all default` = 全用默认值、`继续` / `跳过` / `bypass`。

### 角色体系

| 角色 | 职责 |
|------|------|
| **PMO** | 流程编排:承接输入 → 5 mode 分诊 → 调度角色 → state.json 维护 → 暂停点 |
| **PL**(Product Lead) | 产品方向:product-overview 引导 / 业务话题讨论 / 变更级联 |
| **PM** | PRD + 结构化 AC + 最终验收 |
| **Designer** | UI 还原 + 全景(sitemap + preview) |
| **架构师** | Tech Review(blueprint)+ Code Review(review)+ ARCHITECTURE.md + ADR |
| **QA** | TC(AC↔test 绑定)+ integration / api-e2e + Code Review |
| **RD** | TDD 实现 + 单测 + 自查 + Bug 排查报告 |
| **External Reviewer** | 异质模型代码评审(codex / claude · 立场独立) |

v8 角色协作走**主对话身份切换**(不 dispatch Subagent)—— 切换角色 = 切换 checklist + 强制重读。

### 测试体系(4 层)

| 层 | 范围 | 归 stage |
|----|------|---------|
| unit | 单类 / 单函数 红绿循环 | dev(TDD) |
| integration | 进程内跨模块 / 服务契约 | test |
| api-e2e | live 跨进程(真 binary + 真 HTTP) | test |
| browser-e2e | UI 交互流 + 截图 | browser_e2e(可选) |

### Worktree 策略

默认 `auto`。prepare 子流程为每个 Feature 创建隔离 worktree(`{worktree_root_path}/{Feature-ID}` · 默认 `worktree_root_path=.worktree`),dev 在 worktree 内开发,ship Phase 2 验证合并后清理。`init-feature` 物化校验 worktree 路径约定 + cwd。可在 `.teamwork_localconfig.json` 配置。

### 待规划需求池

跨 Feature/session 发现的"本次范围外但要做"事项,记入 `teamwork-space.md § 待规划需求池`(`PENDING-NNN`)。用户问"还有什么待做 / pending / backlog"时 PMO 自动列出。转 Feature/Bug 后立即从表删除,池始终轻量。

### 产品规划体系

Product Lead(PL)角色维护 `product-overview/`(业务架构 + 执行手册)。产品方向性话题 PMO 调度 PL 讨论;讨论结论落地时 PL 按变更级别(功能 / 业务模块 / 方向)触发下游级联到 Feature Planning。开发中发现与上游文档矛盾时触发自下而上影响升级。

### 跨宿主兼容

| 宿主 | 指令文件 |
|------|----------|
| Claude Code | CLAUDE.md |
| Codex CLI | AGENTS.md |
| Gemini CLI | GEMINI.md |

`bootstrap.py` 按宿主自动维护对应指令文件的 teamwork 注入段。

---

## 核心保证 · 9 红线 R1-R9

v8 把红线从"靠 AI 自觉"变成"工具强制" —— 仅 R3 仍是软规则(不可枚举):

| 红线 | 内容 | v8 物化归宿 |
|------|------|------------|
| **R1** 代码写权归 RD | 代码/测试/构建由 RD 角色;外部模型仅只读评审 | state.py 校验写操作时身份切换 |
| **R2** 流程类型闭集 | 6 种流程 · 禁止自创变体 | `init-feature --flow-type` enum |
| **R3** PMO 统一承接 | 所有用户输入由 PMO 先承接 | 保留 AI 自决(软规则) |
| **R4** 流程边界 | 不简化 / 不膨胀 / 必给步骤描述 | state.py 按 flow_type 强制 stage 链 |
| **R5** 暂停点协议 | 必等用户确认 + 必给 💡 推荐 + 编号化 | state.py emit 暂停点 markdown |
| **R6** Planning 只出文档 | 不出代码 · 不自启 Feature | `init-feature` reject "Feature Planning" |
| **R7** 证据闭环 | 声称完成必附 commit + 实测输出 | `xx-complete` 校验 commit 存在 + artifacts |
| **R8** 写操作硬门禁链 | prepare 完成前拒绝 stage-start · ship CLI-first | state.py 内部物化拦截 |
| **R9** session bootstrap | 入口必跑 bootstrap.py + PMO 分诊 | `tools/bootstrap.py` |

### 关键质量机制

- **契约化 Stage**:每 stage 有 prerequisites(入口校验)/ artifacts(产物形态)/ evidence_checks(完成证据),由 state.py 物化
- **AC↔Test 强绑定**:`PRD.md` 的 `acceptance_criteria[].id` ↔ `TC.md` 的 `tests[].covers_ac`,`verify-ac.py` 自动校验覆盖完整性
- **多视角 Review**:架构师 / QA / 异质模型三份产物结构独立,避免"前一份说没问题"的鼓掌效应
- **fix-retry 循环**:review / test 失败 stage 内 fix-retry(不切 stage),audit 留 rounds[]
- **状态恢复**:`{Feature}/state.json` 是流转状态单一权威,含 `_state_checksum` 自防护;新对话 / compact 后读 state.json 即恢复
- **ADR + KNOWLEDGE**:三问触发器自动落 ADR;`KNOWLEDGE.md` 分 Gotcha / Convention / Architecture 三类硬触发收敛

详细 9 红线 rationale 见 [docs/v8-redesign/00-MANIFESTO.md](./skills/teamwork/docs/v8-redesign/00-MANIFESTO.md)。

---

## 文档导航

| 文件 | 作用 |
|------|------|
| [SKILL.md](./skills/teamwork/SKILL.md) | 主入口:设计哲学 + 命令清单 + Triage 入口规范 + 9 红线 + 项目级文档架构 |
| [FLOWS.md](./skills/teamwork/FLOWS.md) | 6 流程类型 telos 与适用场景 |
| [STAGES.md](./skills/teamwork/STAGES.md) | 10 stage 索引 + 通用 cite 纪律 |
| [ROLES.md](./skills/teamwork/ROLES.md) | 角色索引(→ roles/*.md) |
| [STANDARDS.md](./skills/teamwork/STANDARDS.md) | 技术规范索引(→ standards/*.md) |
| [TEMPLATES.md](./skills/teamwork/TEMPLATES.md) | 文档模板索引 |
| [docs/prepare.md](./skills/teamwork/docs/prepare.md) | mode B → 进状态机前的准备子流程 |
| [docs/feature-planning.md](./skills/teamwork/docs/feature-planning.md) | Feature Planning 流程指南(不进状态机) |
| [docs/conventions.md](./skills/teamwork/docs/conventions.md) | Feature ID + worktree path 命名规范 |
| [stages/*.md](./skills/teamwork/stages/) | 各 stage Telos + Output Contract(校验进 state.py) |
| [roles/*.md](./skills/teamwork/roles/) | 角色 telos + 创作要点 |
| [standards/*.md](./skills/teamwork/standards/) | 技术规范(common / backend / frontend / tdd 等) |
| [tools/state.py](./skills/teamwork/tools/state.py) | 唯一编排器入口(≈ 39 命令) |
| [tools/bootstrap.py](./skills/teamwork/tools/bootstrap.py) | session 启动维护 |
| [docs/v8-redesign/00-MANIFESTO.md](./skills/teamwork/docs/v8-redesign/00-MANIFESTO.md) | 设计宪法 · 范式切换 · 9 红线归宿 |
| [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) | 完整版本变更记录 |

---

## 版本

**v8.0** —— 范式切换:从"PMO 凭记忆读 spec 调度"到"state.py 状态机驱动 + AI 跑命令即知做什么"。不向下兼容,老 Feature 跑 `state.py migrate-v7-to-v8 --feature <path>` 迁移。

完整变更记录见 [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md)。

---

## License

MIT
