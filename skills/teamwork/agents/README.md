# Teamwork Subagent 执行协议

> Teamwork 以 **Stage 为权威**(角色任务规范在 `stages/*.md`)。本文件只保留 **Subagent 执行协议**(dispatch / 通用约束 / Progress Log / 主对话产物)。
> PMO 用 Subagent 时让其先读本文件 + 对应 Stage 文件;主对话路径可跳过本文件。
> 用不用 subagent 由 PMO 自决(判据 [STAGES.md §4](../STAGES.md):子任务**边界清晰且够大**才派)。external 异质评审**不走本协议** —— 权威 = [standards/external-model-usage.md §11](../standards/external-model-usage.md)(`state.py external-review` 一条命令)。

---

## 一、模型档位 + 并行姿态(v8.225 · 判断框架 · 非型号枚举)

**档位按任务性质判(不绑型号 · 型号随代际漂移 · 映射列仅当前示例)**:

| 档位 | 任务性质判据 | 当前映射(示例 · 会漂移) | 典型并行形态 |
|---|---|---|---|
| **深度档**(最强可用) | 创造性产出 + 深度判断:规划/拆解 · TECH 方案 · 架构 Code Review · PRD 起草 · 根因诊断 · **关键裁决**(finding 采驳) | Claude: Fable/Opus · GPT: 最高推理档 | 多方案并行探索 + 主对话裁决 |
| **执行档**(默认) | 写代码实现 / 集成 / 修复 —— **主对话继承会话模型即是**(不主动降) | Claude: 会话模型 · GPT: 标准档 | 多模块 subagent 各写各的(worktree 内路径) |
| **验证档**(轻) | 校验型/枚举型:TC 覆盖对照 · 测试执行 · 格式核对 · 机械外化 · 路由分诊 | Claude: Sonnet/Haiku · GPT: mini 档 | 冷审/验证 fan-out(隔离并行) |

🔴 **三条硬边界**:① 架构 CR 与关键裁决**不降档**(深度判断降档 = 质量盲区回归);② **评审独立性优先于档位**(冷审 fresh context 比模型强弱重要 —— 两个轻模型冷审 > 一个强模型热审);③ 主对话模型 = **用户主权**(AI 只建议不切换)。

📎 **并行姿态 + 声明制(PMO 派发方规则 · 单源 = [SKILL.md](../SKILL.md) § 全局规则「subagent / teammate」条目 · v8.241 去重)**:开工先问「哪些子任务可以并行」· 每次派发声明 **model + 一句为什么**(dispatch Meta 的 `model/model_reason` 字段)· ultracode 开启冷审/验证 fan-out 优先 Workflow —— 全文与护栏见 SKILL 单源(此处不复制 · 防双载体 drift);本表 + 三条硬边界是 SKILL 反向引用的**档位单源**(v8.230)。

## 二、通用执行约束

- **读取顺序**:① 本文件 → ② 对应 `stages/*.md` → ③ Stage 指定的项目文件(PRD/TC/TECH…)。
- **代码质量**:守 `standards/` + `DEV-RULES.md` + `KNOWLEDGE.md`;禁 TODO/FIXME/占位符;禁不完整片段;文件直接写项目目录(worktree 模式写 **worktree 内路径**)。
- **异常处理**:编译错/测试败/规范问题 → 自行修复继续;上游文档矛盾/方案不可实现/环境问题 → **记录并上报**(来源/问题/影响/建议)· 继续做可实现部分。
- **输出规范**(返回主对话必含):① 执行摘要 ② 产出清单 ③ 问题清单(无则写「无」) ④ 角色报告(格式见对应 Stage)。
- **危险命令红线** 🔴(任何理由都禁):递归强删根/家/当前目录 · 变量可能为空的 `rm -rf $VAR` · 主分支 force-push / 未确认 `reset --hard` · 生产库 DROP/TRUNCATE · `chmod -R 777` · `curl | bash` · 凭证写入代码/日志。白名单:构建产物目录清理(dist/build/node_modules)· 个人 feature 分支 force-push · 测试库(连接串含 test/mock)的 DROP。命中灰区 → 停止 + 记 Concerns + 返回 `DONE_WITH_CONCERNS`。

## 三、PMO dispatch 协议

### 宿主方式速查

- **Claude Code** → `Task` 工具(model 参数指定)
- **Codex CLI** → prompt 指示 spawn 自定义 agent(`.codex/agents/*.toml` · bootstrap 部署)
- **Gemini CLI / 不支持宿主** → 主对话内串行执行(降级 · 丧失并行不丧失功能)

🔴 **降级必输出 WARN**(硬规则 · 静默降级 = 隐藏问题):任何「首选方案不可用 → 走兜底」路径,PMO 在主对话输出 `⚠️ WARN [degradation-fallback]`(reason / from / to / stage / impact)。

### 文件化 dispatch(可选实践 · PMO 自决)

把 dispatch 信息写进 markdown 文件 · Subagent 读文件执行 · 完成 append Result 回同一文件(避免 prompt 塞长文本 + 留审计):

- **位置**:`{Feature}/dispatch_log/NNN-{标签}.md`(三位序号 · 并行各独立文件 · INDEX.md 汇总)· 🔴 state.py 不生成 dispatch 文件。
- **Subagent prompt 极简**(~5 行):角色名 + dispatch 文件绝对路径 + 执行规则(按 Input files 按序读 · 产出 Expected deliverables · 实时维护 Progress Log · 完成 append Result · 未 append = FAILED)。
- **字段责任**:PMO dispatch 前填 Meta(🔴 v8.235 含 **model + model_reason 一句** · 按档位表对档)/ Task / Input files / Additional inline context / **Key Context** / Edit scope / Expected deliverables / Return format;Subagent 执行中填 **Progress Log**、完成前填 **Result**。
- **注入策略**:长文档(PRD/TC/TECH/standards)→ Input files 让其自读;短约束(仓库级指令文件/短配置)→ inline 复制原文;Result 必含 `Files read` 清单(可追溯)。
- **Edit scope**(标准段):允许读写 {子项目} + {Feature 目录};只读 project-specs/ + {SKILL_ROOT}/standards/;🚫 其他子项目 · 敏感文件(.env/credentials/*secret*)· .git/ 直接操作。违反 → 停止 + Concerns + `DONE_WITH_CONCERNS`。

### 🎯 Key Context(6 类 · 硬规则)

只写 **Input files 里读不到**的信息 · 逐项判断 · 无则写 `-`(证明已判断 · 留空/删字段 = Subagent 返 NEEDS_CONTEXT)· 必附证据链(来源文件+位置):

1. 历史决策锚点(用户已拍板的选择) 2. 本轮聚焦点(重派/修复必填) 3. 跨 Feature 约束(禁改文件/兼容) 4. 已识别风险/历史陷阱 5. 降级授权 6. 优先级/容忍度

反模式:全写 `-` 偷懒(审查环节暴露)· 复制 PRD 内容进来(Subagent 会自读)· 「注意代码质量」式废话。

### Progress Log(🔴 硬规则 · 实时 + flush)

宿主 Task API 同步阻塞,但**文件系统是天然异步通道** —— Subagent 写 dispatch 文件 · 主对话并发 Read 同一文件:

- **Subagent**:每 Step 开始/完成**立即 append** `- [HH:MM:SS] step-start/step-done Step N(耗时)` + 异常事件(step-concern/blocked/degradation)· 🔴 立即 flush(Python `flush+fsync` / shell `>>` / Edit 工具天然原子)· 🚫 禁跑完一次性补(崩溃丢中段)。
- **PMO**:dispatch 前 TodoWrite 预声明 Step 列表(用户先看到「接下来 N 步」);运行中用户问进度 / >5min / 并行多路 → **Read Progress Log 段**增量汇报(🚫 别读 subagent session JSONL 当进度源);长时无新行(>预估 2x)= 疑似卡死;dispatch 后转时间轴回放 + 高亮异常。Progress Log 缺失/断档 → 摘要标「进度不可追溯」WARN。

### 完成后处理(状态分级)

PMO 读 dispatch 文件确认 Result 已 append(未 append = FAILED)→ 按 Status 处理 → 更新 INDEX.md → 输出阶段摘要(含时间轴):

| 状态 | PMO 处理 |
|------|----------|
| ✅ DONE | 正常流转 |
| ⚠️ DONE_WITH_CONCERNS | 读 concerns · 关键的先处理再流转 |
| 🔄 NEEDS_CONTEXT | 补上下文 → 重新 dispatch(不降级) |
| 🔁 QUALITY_ISSUE | 走打回机制 |
| ❌ BLOCKED | 触发打回 · 不降级 |
| 💥 FAILED | 降级主对话执行(必输出 WARN) |

🔴 升级策略:缺上下文 → 补了重派;任务太大 → 拆小;真做不了 → 降级主对话 + WARN。**永远不要在不改变任何条件下重试同一个 Subagent**。Subagent 异常不卡流程 · 降级后仍须完成该阶段任务。

## 四、主对话产物协议(简)

主对话直接执行 stage 任务时,产物**必须落盘**(不能只在对话记忆):产物形态按各 `stages/*.md` **Output Contract**;需要独立性审计的产物(如三视角评审)frontmatter 带 `files_read[]`(证明只读了 Input Contract 文件 · 未读其他视角报告)+ 独立时间戳 —— review-stage Output Contract 有硬校验项。

## 五、索引

stages/ 编排见 [STAGES.md](../STAGES.md) · 角色定义见 [ROLES.md](../ROLES.md) · external 异质评审见 [standards/external-model-usage.md](../standards/external-model-usage.md)。
