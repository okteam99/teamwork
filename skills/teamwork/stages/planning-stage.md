# Planning Stage

---

## 怎么做

### 1. 加载上下文
读 PROJECT.md(若存在 · 当前业务架构)· 用户需求

### 2. 起草 PROJECT.md
§业务架构 + §执行手册 + §关键决策 · PL(Product Lead)主导

### 3. 起草 ROADMAP.md
Feature 列表 + 优先级 + 排期(当前/下一/储备)

### 4. 起草 sitemap.md
信息架构 · 页面层级 · 模块边界

### 5. PL-PM 讨论 + 多角色 review
PL 把方向 · PM 把可执行性 · Architect 把技术可行

### 6. complete
`state.py planning-complete ...` · 自动转 completed(不进 dev · R6)

---

## 必读 cite 清单(P0-11 · 各 substep 动手前主对话输出)

| Substep | 必读 spec | 段 | cite 关键点 |
|---------|----------|----|------------|
| 1. 加载上下文 | `roles/product-lead.md` | § Telos | 产品方向视角 |
| 2. 起草 PROJECT.md | `roles/product-lead.md` | § 业务架构起草 | 业务能力 vs 技术架构边界 |
| 3. 起草 ROADMAP.md | `roles/product-lead.md` | § ROADMAP 维护 | Feature 列表粒度 · 不细化到 task |
| 4. 起草 sitemap.md | `roles/designer.md` | § 信息架构 | 页面层级 |
| 5. PL-PM 讨论 + 多角色 review | `roles/pm.md` | § 与 PL 协作 | 可执行性把关 |
| 6. complete | — | — | (无 · 自动转 completed · 不出代码 R6) |


**输出格式**(每个 substep 动手前必在主对话输出):
```
📖 cite:
- <spec> § <段>:"<引该段 1 句关键原文 · 证明真读>"
```

**强约束**(R5+P0-11 软约束 · 用户监督):
- 标 "—" 的 substep 无 cite 要求(状态机操作 / 用户暂停 / 已物化)
- 其余 substep **动手前必输出 cite 块** · 缺 cite 视为 process 违规(用户可叫停)
- cite 必含 § 段标题 + 至少 1 句原文(原文必真实存在于该 spec · 不可瞎编)
- AI 在 stage 内多次切角色 · 每次切换前重新 cite 该角色规范

**为什么 cite**:
- brief 列路径(P0-4)只解决"AI 找不到路径"· 不保证 AI 真读
- complete 时校验太晚(AI 已做完)
- substep 动手前 cite = 事前提醒 · 强制 AI 翻一眼 spec
- 物化死角(state.py 看不到 markdown Read 动作)· 软约束 + 用户监督兜底

## 注意事项

### 坑 1 · R6 红线 · Planning 出代码
直接进 dev 写代码 · 违 R6。
 **对策**:planning 只产 3 个文档 · 完成后自动 completed · Feature 启动需用户主动选(不自启)

### 坑 2 · PROJECT.md 业务架构 vs 技术架构混淆
把"用什么数据库"写进业务架构 · 应在 ARCHITECTURE.md。
 **对策**:业务架构 = 业务能力 / 服务边界 · 技术架构 = 系统设计 · 各归各处

### 坑 3 · ROADMAP 细化到 task 级
task 是 Feature 内 PRD 的事 · ROADMAP 只到 Feature 名 + 简述。
 **对策**:ROADMAP 一 Feature 一行 · 标题 + 优先级 + 状态

### 坑 4 · sitemap 与单 Feature UI.md 重复
两处同步成本高。
 **对策**:sitemap = 整体页面架构 · 单 Feature UI.md = 本 Feature 涉及的页面 · 后者不重复全局

### 坑 5 · Planning 完成自动启 Feature
用户没拍板就开 dev · 越权。
 **对策**:Planning 完成进 completed(不进 dev)· 用户主动跑 `/teamwork <feature>` 启动新 Feature 流程

---

## Output Contract(产物形态参考)

### `PROJECT.md(项目根)`
§业务架构 + §执行手册 + §关键决策

### `ROADMAP.md(项目根)`
Feature 列表 + 优先级 · 一 Feature 一行

### `sitemap.md(项目根)`
信息架构 · 页面层级

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `PLANNING_SPEC`
- 入口规范:[../TRIAGE.md](../TRIAGE.md)
