# Prepare · 进状态机前的准备子流程

> **可重入子流程** · 任何"决定要走某流程"的 PMO 主对话点都走一次。
> 输入:用户意图(自然语言 / Feature Planning 中的 BL-NNN / 升级讨论收敛)
> 输出:`state.py init-feature` 命令的 5 项参数(flow_type + feature_id + worktree_path + branch + merge_target)

---

## 1. 触发场景

| 场景 | 何时走 |
|---|---|
| **新 session · mode B execute** | TRIAGE.md mode 分诊判 B → 进 prepare |
| **mode E discuss 升级 B** | 讨论收敛后 PMO 主动建议升级 → 进 prepare |
| **Feature Planning 完成后启 Feature** | PL 在 ROADMAP 拆完后 · 用户拍板某 BL → PMO 同 session 走 prepare 启动 Feature |
| **mode A/D 转 B**(罕见) | 用户从查看/状态切到执行 → 进 prepare |

**非触发场景**(prepare 不跑):
- mode A query / mode D status:不进状态机
- mode C resume:已有 state.json · 直接 jump
- Feature Planning 流程本身:由 PMO 主对话按 [docs/feature-planning.md](./feature-planning.md) 执行 · 不需 prepare(不进状态机)
- 问题排查流程:同上 · 不进状态机

---

## 2. Step 1 · 流程类型识别(6 闭集 · R2 红线)

PMO 按以下关键词表判定 user input 落入哪类流程:

| 关键词模式 | 流程类型 |
|----------|---------|
| 规划 / Feature Planning / feature planning / 更新 roadmap / 拆 roadmap / 路线图 / 全景 / 做电商 / 做 SaaS / 商业模式调整 | **Feature Planning** |
| 排查 / 查 log / 诊断 / why X 慢 / 调研 / 分析根因 | **问题排查** |
| 修复 / bug / 报错 / 500 / 502 / 挂了 / 无法登录 / 生产问题 | **Bug** |
| 换 logo / 换图 / 改文案 / 改样式 / 改颜色 / 改配置常量 | **Micro** |
| 加按钮 / 加导出 / 加字段 / 列表加列 | **敏捷需求** |
| 实现 / 开发 / 做功能 / 新建模块 | **Feature**(兜底)|

落入 6 闭集之一(R2 红线 · enum 强制)。

**触发场景为 "Feature Planning 启 Feature"** 时:flow_type 默认 `Feature`(因为是从 BL-NNN 启动具体功能 · BL 已经决定了"做什么")。

---

## 3. Step 2 · worktree 决策模板

PMO 按 flow_type 算 branch 前缀 + worktree path 建议:

| flow_type | branch 前缀 | worktree |
|----------|-----------|---------|
| Feature | `feature/` | 必 |
| 敏捷需求 | `agile/` | 必 |
| Bug | `fix/` | 必 |
| Micro | `micro/` | 必 |
| Feature Planning | — | 不进状态机 · 不走 prepare |
| 问题排查 | — | 不进状态机 · 不走 prepare |

**worktree path 默认** = `{worktree_root_path}/{Feature-ID}` ·
其中 `worktree_root_path` 解析顺序:
1. `state.json.environment_config.worktree_root_path`(已存在 Feature)
2. 项目根 `.teamwork_localconfig.md` 的 `worktree_root_path` 字段
3. 默认 `.worktree`(项目根子目录)

完整规范见 [docs/conventions.md § 9-11](./conventions.md)。

---

## 4. Step 3 · emit 暂停点 markdown

PMO 复制给用户(R5 暂停点协议 · 必给推荐 + 编号 + 决策参考):

```markdown
⏸️ 进入流程前请确认 4 项:

📋 **流程类型**:<flow_type>
📋 **理由**:<识别理由>
📋 **首个 stage**:<first_stage>

请提供:
1. **Feature ID**(如 PTR-F033-Credit-Note-Adjustment · 编号规则见 [docs/conventions.md § 1](./conventions.md))
2. **merge_target**(如 staging / main)
3. **worktree path**(默认:`{worktree_root_path}/<FEATURE-ID>` · 见 [docs/conventions.md § 9](./conventions.md))
4. **branch**(默认:`<branch-prefix><FEATURE-ID>`)

回复 4 项或 "all default" 用默认值(仅需 Feature ID + merge_target)

📎 **是否需要 UI Design Stage** 由 goal-complete 时 `--needs-ui` 决策 · prepare 入口不强制提前拍板。
```

flow_type → first_stage 映射:
- Feature / 敏捷需求 → `goal`
- Bug / Micro → `dev`
- Feature Planning / 问题排查 → 不进状态机 · prepare 在这两个流程上不调用

---

## 5. Step 4 · 用户确认后 · PMO 显式执行

```bash
# 用户回(或 all default):
# 1. Feature ID: PTR-F033
# 2. merge_target: staging
# 3. worktree path: <repo>/.worktree/PTR-F033
# 4. branch: feature/PTR-F033

# PMO 跑(在主工作区 cwd · 不是 worktree):
git fetch origin
git worktree add -b feature/PTR-F033 <worktree-path> origin/staging
cd <worktree-path>

# 此刻 cwd 在 worktree 内 · 进状态机:
state.py init-feature \
 --feature docs/features/PTR-F033 \
 --feature-id PTR-F033 \
 --flow-type Feature \
 --merge-target staging \
 --branch feature/PTR-F033 \
 --worktree-mode auto \
 --worktree-path <worktree-path>
```

---

## 6. 与状态机的接口

prepare 完成 = init-feature 前置满足:
- ✅ flow_type / feature_id 已用户确认
- ✅ worktree 物理已创建(PMO 显式跑)
- ✅ cwd 在 worktree 内(PMO 显式 cd)
- ✅ branch / merge_target 已用户确认

**init-feature 拒绝条件**(状态机入口物化拦截):
- worktree_mode != off 但 cwd 不在 worktree → FAIL
- worktree_mode != off 但 worktree 物理不存在 → FAIL
- flow_type ∈ {Feature Planning, 问题排查} → reject(不进状态机)

**prepare 不做的事**:
- ❌ 不写 state.json(state.json 由 init-feature 创建)
- ❌ 不创建 worktree(由 PMO 显式跑)
- ❌ 不自动跑 git(防漏看用户确认)

---

## 7. 错误处理

### 7.1 · 流程类型识别错(关键词模糊)

PMO 识别不准 → 在暂停点列出"我猜是 X · 你确认是 Y/Z?"让用户拍板。

### 7.2 · 用户拒绝 worktree 默认值

部分用 default + 部分自定 → PMO 用混合值跑 git worktree add。
全否决 → 等用户给完整 4 项。

### 7.3 · git worktree add 失败

- branch 已存在 → `git worktree remove <path>` + `git branch -D <branch>`
- origin/base 不存在 → `git fetch origin`
- path 已存在但非 worktree → 删 path 或换 path

错误处理由 PMO 主导 · 不在 state.py 状态机里。

---

## 8. 红线

### R-P1 · 必经用户确认

prepare 输出暂停点后 · 必须等用户明确回 4 项配置(或 "all default")。
**不可** PMO 自己拍板 worktree path / branch / merge_target。

### R-P2 · 用户未确认前不进状态机

PMO 在用户未确认前 · **不可** cd / git worktree add / init-feature。
违规 = 主 tree 污染风险(实证 PTR-F033 case)。

### R-P3 · 不可枚举判断留 PMO

意图总结 / 流程类型识别的不可枚举部分 → PMO 主对话判断(模糊时问用户)。
关键词表是辅助 · 不是强制 · PMO 可基于上下文覆盖默认。

---

## 9. 相关文档

- [TRIAGE.md](../TRIAGE.md) — 5 mode 入口分诊(prepare 由 mode B / mode E 升级触发)
- [docs/feature-planning.md § 5](./feature-planning.md) — Feature Planning 完成后启 Feature 走 prepare
- [docs/conventions.md](./conventions.md) — Feature ID + worktree path 编号规范
- [SKILL.md](../SKILL.md) — 顶层叙事 + 项目级文档信息架构
- [RULES.md § R2 / R5](../RULES.md) — 流程闭集 + 暂停点协议红线 rationale
