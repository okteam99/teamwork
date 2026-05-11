# E · discuss 模式规范（v7.3.10+P0-106 新建 · L2 专项规范）

> 🔴 **本文件是 E · discuss 模式的唯一权威源**。triage-stage.md 5 mode 分诊段 cite 本文件。
>
> 🟢 **设计来源**：v7.3.10+P0-106 实战触发——这次对话本身（P0-101 → P0-106 全是 discussion）暴露当前 4 mode（A/B/C/D）漏掉了"想法讨论"场景 · ~30% 实际使用没明确处理。

---

## 一、E · discuss 是什么

**入口 mode 之一** · 用于用户的"想法讨论 / 设计对齐 / 求建议 / 比方案"场景。

```
特征：
  - 用户还没拍板要做什么
  - 在评估方案 / 求建议 / 比对选项 / 表态求验证
  - 还没创建 Feature
  - 还没有 PRD

输出：观点 + 论证 + 选项 + 推荐 + 询问 → 用户拍板后升级到 B/A/C/D
```

---

## 二、触发规则

### 触发关键词（用户消息含 ANY · 即倾向 E）

```
- "我感觉 / 我觉得 / 我认为 / 我倾向"
- "你怎么看 / 你觉得 / 你认为 / 你建议"
- "是不是 / 是否应该 / 该不该"
- "想讨论 / 讨论下 / 聊聊"
- "我有个想法 / 有个想法"
- "怎么改 / 怎么做更合理 / 哪种更合理 / 哪个更好"
- "X vs Y" / "X 还是 Y" / "A 还是 B"
- "建议 / 推荐 / 评估下"
```

### 排除规则（这些走其他 mode）

```
- 含具体代码 / 文件 + "看下" → A · query（事实查询）
- 含推进动词「做 / 实现 / 修复 / 创建 / 重构」+ 明确动作 → B · execute
- 含「为什么报错 / 怎么会 / 排查」 → A · query（诊断查询）
- 命令前缀 `/teamwork 继续` / `/teamwork ship F#` → C · resume
- `/teamwork` 空参 / "现在到哪" → D · status
```

### 边界 case（双关键词冲突）

```
"看下 F032 该不该 ship" 
  → 含"看下" + Feature 编号 + "该不该"（E 关键词更强）
  → 优先 E · discuss（先讨论是否该 ship · 拍板后升级 C · resume + ship）

"PRD 这样写是不是太复杂了"
  → E 关键词 + 触及具体产物
  → E · discuss（讨论 + 内部按需 read PRD · 给评估）

"建议这个架构怎么改"
  → E 关键词
  → E · discuss

"看下这段代码我感觉有问题"
  → 含 "看下" + E 关键词
  → 优先 E · discuss（"我感觉" 比 "看下" 更强）
  → 内部按需 grep 该段代码 · 给评估

"实现 X · 我觉得用 Y 方案更好"
  → 推进动词「实现」+ E 关键词
  → 默认 E · discuss + 询问"是先讨论方案再实施 还是直接按 Y 方案实施"
  → 用户回答后切对应 mode
```

---

## 三、E · discuss 行为规范

### 必做

```
✅ PMO 综合视角评估
   - 引用 PL / 架构师 / QA / RD / Designer 等多角色思考维度
   - 不切角色身份（不写 "切到 PL 角色" 等）
   - 不写任何文件
   
✅ 输出格式
   - 当前方案的优缺点诊断（如适用）
   - 替代方案 N 个 + 各自适用场景
   - 推荐 💡 + 理由 📝
   - 询问下一步（"回 1/2/3" 或开放询问）

✅ silent read（按需 · 不输出过程）
   - 内部按话题路由 read 项目级文档
   - read 后直接给答案 · 不输出"我现在 read X"
```

### 禁止

```
❌ 不强制 grep 代码（除非讨论中明确触及具体文件）
❌ 不全扫 KNOWLEDGE / ADR（仅按话题相关段 read）
❌ 不创建 Feature / 不进 prepare-stage
❌ 不写任何 state.json
❌ 不进任何业务 stage 链
❌ 不切角色身份（不写 "切到 PL 角色 ..."）
❌ 不创建评审记录（PRD-REVIEW.md / TC-REVIEW.md 等）
❌ 不修改 PROJECT/ROADMAP/sitemap（这些是 mode B 流程的产物）
```

---

## 四、知识地图（按话题路由 read）

PMO 在 E · discuss 时按话题路由按需 read 项目级文档。**完整知识地图见 [SKILL.md § 项目级文档信息架构](../SKILL.md)**·本段仅列 discuss 相关 read 路由：

| 用户讨论话题 | PMO 内部 read | 备注 |
|-----------|------------|-----|
| 产品方向 / Feature 优先级 / Roadmap | PROJECT.md + ROADMAP.md | 按相关段 |
| 信息架构 / 页面层级 | sitemap.md | 按相关段 |
| 架构决策 / 技术选型 / 历史方案 | adrs/INDEX.md + ARCHITECTURE.md | 跨 Feature 扫 |
| Convention / 命名约定 / Gotcha / 踩坑 | KNOWLEDGE.md | 关键词命中段 |
| **排查 / 报错 / 查 log / 查环境 / 查 DB / 查 Redis / 部署 / 回滚**（v7.3.10+P0-109）| **TROUBLESHOOTING.md（项目根）**| 类比 teamwork_space.md 处理 · v7.3.10+P0-118-B 起 prepare-stage Step 3 主动创建空骨架 · 用户首次排查时 PMO 检测模板原样未填 → 一句话提示补充 |
| 多子项目 / 跨项目依赖 | teamwork_space.md | 子项目清单 |
| F\d+（具体 Feature）| docs/features/{F}/state.json + 相关产物 | 按 Feature 编号 |
| 数据库 / schema | docs/architecture/database-schema.md | 按相关段 |
| 评审历史 / 评审决策 | review-log.jsonl | 跨 Feature 扫 |
| 涉及具体代码 | grep + Read 实际代码 | 按关键词 |
| 框架 / teamwork 自身 | SKILL.md / RULES.md / 各 stage spec | 已注入·直接用 |

**silent read 原则**（v7.3.10+P0-105 通用）：
- 不输出"我现在 read X 看看" / "我先去 read Y"
- 内部 read · 仅读相关段
- read 后直接给答案

---

## 五、与其他流程的边界

### E · discuss vs PL 讨论（Goal-Plan 子步骤 2）

**不重合 · 不会触发**（不同抽象层）：

| 维度 | E · discuss（mode 层）| PL 讨论（Stage 子步骤层）|
|------|------------------|-------------------|
| 时机 | Feature 创建**之前** | Feature 创建**之后** · PRD 已有 |
| 产物 | 无（讨论结果可能升级为 Feature）| PRD-REVIEW.md PL section |
| 状态 | 不写 state.json | 写 state.json（评审 round）|
| 角色 | PMO 综合视角 · 不切身份 | PL 评审身份切换 |
| 范围 | 任意话题 | 仅 PRD 内容 |

**升级路径**：E · discuss → 用户拍板 → mode B → Feature 流程 → Goal-Plan Stage 子步骤 2 PL 讨论（**那时才真正切 PL 身份 + 写 PRD-REVIEW.md**）

**E · discuss 中允许引用 PL 视角 · 但不切身份不写文件**：
```
✅ "从 PL 视角（产品方向）：...这个方向值得做的理由..."
❌ "切到 PL 角色 · 我评估这个 PRD ..."
```

### E · discuss vs Feature Planning 流程

**精简后职责正交化**（v7.3.10+P0-106）：

```
E · discuss（mode 层）= 所有"未拍板的讨论"统一入口
                        - 不写文件
                        - 给方案 + 推荐 + 询问

Feature Planning 流程（mode B 内部）= 仅"写多文档"执行流程
                                       - 不再做内部讨论（已废弃 · 讨论部分迁 E · discuss）
                                       - 仅 PMO 把 E · discuss 结论落到 PROJECT/ROADMAP/sitemap
```

**升级路径**：E · discuss 讨论 Q4 Roadmap → 用户拍板"调整 F033 优先级" → mode B → Feature Planning 流程 → 仅 1 步：PMO 把结论写入 ROADMAP.md。

### E · discuss vs 变更管理流程

**不直接触发**：

```
E · discuss 中讨论"修改产品方向" → 用户拍板 → mode B → prepare-stage 变更归属检查 → 触发变更管理流程
```

E · discuss 是变更管理的**前置讨论** · 不能从 E 直接跳过 prepare-stage 创建 change-request.md。

### E · discuss vs 跨 Feature 影响升级评估

**不直接执行**：

```
E · discuss 可能识别"这个想法影响多 Feature" → 给评估 + 推荐
但跨 Feature 影响升级评估是 Stage 出口的事 · E · discuss 不直接执行
```

---

## 六、升级路径

E · discuss 答完后用户回应 → 升级到对应 mode：

```
用户回应                           → 升级到的 mode
─────────────────────────────────────────────────
"ok 按推荐走"                     → B · execute（视讨论结果开 Feature/Bug/Micro/敏捷/Planning）
                                    
"先看下当前是怎么实现的"           → A · query（grep 找代码）

"再讨论下 X 这个点"                → 留在 E · discuss

"按 Feature 流程做"                → B · execute（强制 Feature 流程）
"按 Micro 流程"                    → B · execute（强制 Micro 流程）
"按敏捷需求"                       → B · execute（强制敏捷流程）

"现在到哪了"                       → D · status
"继续 F032"                        → C · resume

"算了 · 不做"                      → 终止（不升级 · 留在 E）
```

---

## 七、反模式

### 反模式 1：E · discuss 中切角色身份

```
❌ "切到 PL 角色 · 我评估这个产品方向 ..."
❌ "我作为架构师评审这个技术方案 ..."

→ E · discuss 没有 PRD / 没有 Feature · 不能切身份
→ 引用视角可以（"从 PL 视角看 ..."）· 切身份不行
```

### 反模式 2：E · discuss 中创建评审记录

```
❌ 创建 PRD-REVIEW.md / TC-REVIEW.md
❌ 创建 change-request.md
❌ 修改 ROADMAP.md / PROJECT.md / sitemap.md

→ E · discuss 不写任何文件 · 写文件需 mode B 流程
```

### 反模式 3："建议你 X · 我现在就去执行"

```
❌ "我建议启动 Feature Planning · 我现在去执行"
❌ "我推荐做 X · 我现在去创建 state.json"

→ 必须用户拍板 · PMO 不能自创流程升级
→ 应输出："推荐 X · 选项：1. 走 X / 2. 不走 / 3. 其他"
```

### 反模式 4：E · discuss 中输出"流程仪式叙事"

```
❌ "进入 discuss mode"
❌ "现在开始讨论 X"
❌ "我先 read Y 看看再给意见"

→ silent execution（v7.3.10+P0-105）
→ 直接给观点 + 选项 · 不输出 mode 标题 / read 过程
```

### 反模式 5：grep 一通找不到对应代码

```
❌ 用户："我感觉 X 模块设计有问题 · 你怎么看"
❌ PMO 立即 grep "X 模块" 找一通找不到 · 给"没找到 X 模块"

→ E · discuss 不强制 grep 代码
→ 应先评估"X 模块"是否真存在（基于已注入的 ARCHITECTURE / KNOWLEDGE）
→ 若用户描述模糊 · 反问"你说的 X 模块是指 [候选 1/2/3] 哪个"
```

---

## 八、PMO 自检 checklist

```
□ 用户消息是否真触发 E（含触发关键词且无排除规则）？
□ 是否给了观点 + 论证 + 选项 + 推荐？
□ 是否引用了多角色视角（PL / 架构师 / QA / RD / Designer）做综合评估？
□ 是否避免了切身份 / 写文件 / 创建评审记录？
□ silent read：read 过程是否未输出叙事？
□ 末尾是否给"回 1/2/3"或开放询问？
□ 升级路径是否清晰（每个选项触发哪个 mode）？
```

---

## 九、与其他规范的关系

- 触发分诊 → [stages/triage-stage.md § 5 mode 分诊](../stages/triage-stage.md)
- 知识地图（完整版）→ [SKILL.md § 项目级文档信息架构](../SKILL.md)
- silent execution 原则 → [standards/output-tiers.md § 反模式 5](./output-tiers.md)
- 红线 R3 PMO 统一承接（隐式承接）→ [SKILL.md § 红线](../SKILL.md)
- 红线 R4 流程边界（不写 state.json / 不创建 Feature）→ 同上

末。
