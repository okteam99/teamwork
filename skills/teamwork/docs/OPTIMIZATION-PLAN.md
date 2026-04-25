# Teamwork Skill 优化方案

> 基于对全部 24 个文件（12,925 行）的完整 Review，逐条给出可执行的优化方案。
> 日期：2026-04-11

---

## 问题 1：复杂度与 Token 成本矛盾

### 问题诊断

| 文件 | 行数 | 加载频率 |
|------|------|----------|
| TEMPLATES.md | 2,977 | 高（每个阶段写文档都要读） |
| RULES.md | 1,851 | 高（PMO 每次流转都要查） |
| ROLES.md | 1,590 | 中（首次加载 + compact 后恢复） |
| SKILL.md | 1,546 | 高（始终加载） |

单个 Feature 完整流程下来，仅规范文件的读取就会消耗大量 context。尤其 compact 后恢复需要重新读取核心文件，进一步放大成本。

### 优化方案

#### 1A：TEMPLATES.md 按文档类型拆分

当前 TEMPLATES.md 包含 21 个模板，但每次只需要 1-2 个。拆分后按需加载单个模板文件，减少 90%+ 的无效加载。

**拆分方案**：

```
templates/
├── README.md              # 索引文件（~30行），列出所有模板及加载时机
├── prd.md                 # PRD 标准模板 + 技术类 PRD 模板（~170行）
├── tc.md                  # TC 模板 + TC-REVIEW 模板（~180行）
├── tech.md                # TECH 技术方案模板（~140行）
├── ui.md                  # UI 设计模板（~63行）
├── status.md              # STATUS.md 模板（~100行）
├── roadmap.md             # ROADMAP.md 模板（~85行）
├── project.md             # PROJECT.md 模板（~100行）
├── architecture.md        # ARCHITECTURE.md + database-schema 模板（~360行）
├── knowledge.md           # KNOWLEDGE.md 模板（~200行，从455行精简）
├── teamwork-space.md      # teamwork_space.md 模板（~257行）
├── bug-report.md          # BUG-REPORT.md 模板（~60行）
├── config.md              # RESOURCES.md + .teamwork_localconfig + external/README（~144行合并）
├── dependency.md          # DEPENDENCY-REQUESTS.md 模板（~50行）
├── e2e-registry.md        # E2E 回归测试中心模板（~90行）
└── pl-pm-feedback.md      # PL-FEEDBACK + PM-RESPONSE 模板（~152行）
```

**SKILL.md 中的加载指引更新为**：

```
| 场景 | 需读取的模板文件 |
|------|-----------------|
| PM 写 PRD | templates/prd.md |
| QA 写 TC | templates/tc.md |
| RD 写技术方案 | templates/tech.md |
| Designer 写 UI | templates/ui.md |
| PMO 创建 STATUS | templates/status.md |
| PM 写 ROADMAP | templates/roadmap.md |
```

**预计收益**：每次文档编写从加载 ~2977 行降低到加载 ~100-360 行，减少 85-95%。

#### 1B：RULES.md 热路径精简

当前 RULES.md 已有热路径索引（前 21 行），但索引只是指向行范围，PMO 仍需读取大段内容。

**优化**：将 RULES.md 中 PMO 最高频使用的三块内容提取为独立文件：

```
rules/
├── README.md              # 精简版 RULES.md（~400行）：暂停条件 + 技术方案复杂度 + Bug 判断 + 编号规则
├── flow-transitions.md    # 阶段状态转移表（6个子表，~350行）：PMO 流转时按需加载
├── gate-checks.md         # 门禁规则 + 校验输出格式（~200行）：每次流转加载
└── subagent-rules.md      # Subagent 执行规则（~300行）：启动 Subagent 时加载
```

**预计收益**：PMO 日常流转从读 1851 行降到读 ~200-400 行。

#### 1C：KNOWLEDGE.md 模板瘦身

当前 KNOWLEDGE 模板占 455 行，其中大量是示例。精简为核心结构 + 1 个示例（~120 行），减少 70%。

---

## 问题 2：规则冗余与自我矛盾风险

### 问题诊断

通过全文搜索，发现以下核心规则在多个文件中重复定义：

| 规则 | 出现次数 | 分布文件 |
|------|---------|---------|
| 禁止跳过 | 10 次 | INIT/SKILL/ROLES/RULES |
| 暂停点必须 | 8 次 | INIT/SKILL/RULES |
| 闭环验证 | 7 次 | SKILL/ROLES/RULES |
| 禁止擅自简化 | 4 次 | INIT/SKILL/RULES |
| PMO 只做 | 3 次 | INIT/SKILL/PRODUCT-OVERVIEW |
| 流程只有四种 | 2 次 | INIT/SKILL |

具体问题：
- INIT.md 第 175 行 "Bug 处理" vs SKILL.md 第 18 行 "Bug"，措辞不一致
- RULES.md 第 271 行和第 276 行，几乎相同的"必经阶段（禁止跳过）：架构师 Code Review"出现两次，疑似 copy-paste 遗漏

### 优化方案

#### 2A：建立"单一权威定义 + 引用"模式

**核心原则**：每条规则只在一个地方完整定义，其他地方用引用。

**权威定义位置**：

| 规则类别 | 权威定义文件 | 其他文件的处理方式 |
|---------|------------|-------------------|
| 绝对红线（10条） | SKILL.md §红线 | INIT.md 的 CLAUDE.md 注入段改为 `📎 完整红线见 SKILL.md §红线` + 仅保留编号列表（不重复全文） |
| 暂停条件表 | RULES.md §一 | SKILL.md 中改为 `📎 完整暂停条件表见 RULES.md §一` |
| 流转规则 | RULES.md §四 | ROLES.md 中引用而非重复 |
| 闭环验证 | RULES.md §三 | SKILL.md/ROLES.md 改为引用 |

#### 2B：INIT.md 注入 CLAUDE.md 的内容精简

当前 INIT.md 第 165-209 行注入到 CLAUDE.md 的内容包含完整的 10 条红线全文。这段内容会在每次对话中被加载，是 token 成本最高的重复。

**优化为**：

```markdown
<!-- teamwork-rules-v5 -->
## Teamwork 协作模式

本项目使用 Teamwork 多角色协作流程。

### 🔴 流程合规红线（10 条，详见 SKILL.md）
1. PMO 不写代码  2. 只有四种流程  3. 禁止擅自简化
4. PMO 先承接    5. 暂停点必须停  6. 需求类型四选一
7. 流程名四选一  8. Planning 只出文档  9. 闭环验证  10. 暂停必给建议

### 激活后行为
1. 加载 skill 规范 → 2. 遵循多角色流程 → 3. 每次回复含状态行

### Hooks 自动化
SessionStart / PreCompact / PostCompact / Stop（详见 hooks/hooks.json）
```

**预计收益**：CLAUDE.md 注入段从 ~45 行降到 ~15 行，每次对话节省约 30 行 context。

#### 2C：修复具体不一致

| 位置 | 问题 | 修复 |
|------|------|------|
| INIT.md:175 vs SKILL.md:18 | "Bug 处理" vs "Bug" | 统一为 "Bug" |
| RULES.md:271 vs 276 | 重复的"必经阶段（禁止跳过）" | 删除重复行，保留一处 |
| SKILL.md:602 | "Bug 修复闭环验证" 引用文字，非规则定义 | 改为明确引用格式 `📎 见 RULES.md §三` |

---

## 问题 3：流程过重问题

### 问题诊断

一个最简单的 Feature（如"把配置项 A 从 true 改为 false"），当前必须走完 12 个阶段：
PRD → PL-PM 讨论 → PRD 技术评审 → 设计 → TC → 技术方案 → 架构师方案评审 → TDD 开发 → Code Review → QA 审查 → 集成测试 → QA Lead 总结 → PM 验收

豁免条件极严格（必须用户说"跳过流程"），而大多数用户不会意识到需要主动说这句话。

### 优化方案

#### 3A：引入"轻量 Feature 路径"（PMO 主动建议，用户确认）

在 SKILL.md 的流程选择规则中增加一条判断逻辑：

```
PMO 初步分析后，如果同时满足以下全部条件：
├── 改动文件 ≤ 3 个
├── 无 UI 变更
├── 无架构变更（不引入新依赖、不改数据库、不改公共接口）
├── 不影响其他功能
└── 方案明确（无多方案权衡）

则 PMO 输出：
📋 PMO 初步分析
├── ...（正常分析）
├── 💡 轻量路径建议：本需求改动范围小且方案明确，建议走轻量路径：
│   PRD（精简版） → TC → RD 开发 → RD 自查 → 🔴 架构师 Code Review → QA 验证 → PM 验收
│   跳过：PL-PM 讨论、PRD 多角色评审、Designer 设计、技术方案、QA Lead 总结
├── 📝 理由：{具体原因}
└── ⏸️ 请确认：走轻量路径 / 走完整流程

🔴 约束：
├── 用户未确认前，默认走完整流程
├── 架构师 Code Review 不可跳过（即使轻量路径）
├── PMO 的判断可能有误，用户有最终决定权
└── 轻量路径的 PRD 使用精简模板（只需：需求描述 + 验收标准 + 影响范围）
```

**与现有豁免规则的关系**：
- 现有豁免规则（用户说"跳过流程"）保留不变，作为"完全跳过"的 escape hatch
- 轻量路径是"部分精简"，仍保留核心质量门禁
- PMO 主动建议但用户决定，不违反"禁止擅自简化"红线

#### 3B：精简版 PRD 模板

在 templates/prd.md 中增加一个精简版：

```markdown
## PRD（轻量版）

### 需求描述
{一段话说明要做什么}

### 验收标准
- [ ] {标准1}
- [ ] {标准2}

### 影响范围
- 修改文件：{文件列表}
- 影响功能：无 / {功能列表}
```

---

## 问题 4：Codex 集成的实用性

### ✅ 已解决（2026-04-14）

**原问题**：agents/README.md §三 设计了 Codex CLI 作为部分 Subagent（QA 代码审查、集成测试）的通用执行引擎，但实用性存疑。

**解决方式**：
- 移除了 Codex CLI 作为通用执行引擎的设计，所有 Subagent 统一使用 Claude Task 执行
- 新增了独立的 **Codex Code Review** 阶段（stages/review-stage.md），Codex CLI 仅用于该阶段的外部独立代码审查
- agents/README.md §三 改为 Codex Code Review 专用的 CLI 调用规范
- INIT.md Step 3.5 保留检测但限定用途为 Codex Code Review
- agents/qa-code-review.md、integration-test.md 移除了"默认执行引擎：Codex CLI"标注

---

## 问题 5：前端 Standards 过于单薄

### 问题诊断

| 文件 | 行数 | 覆盖内容 |
|------|------|---------|
| common.md | 417 | 测试原则、TDD 清单、架构规范、自查规范、QA 审查项 |
| backend.md | 606 | TDD Red-Green-Refactor、集成测试、API 规范、日志规范 |
| frontend.md | 115 | 测试分层、TDD 流程、E2E 测试（极简） |

frontend.md 内容量不到 backend.md 的 1/5，缺失大量前端开发关键规范。

### 优化方案

#### 5A：补充 frontend.md 到 ~400 行

建议补充以下章节：

```markdown
## 前端测试分层（已有，保留）

## 前端 TDD 流程（已有，保留）

## 组件测试规范（新增，~60行）
├── 组件测试策略（交互测试 vs 快照测试 vs 视觉回归）
├── 测试工具选择（Testing Library 优先于 Enzyme）
├── 组件测试模板（渲染测试 + 交互测试 + 边界状态测试）
└── Mock 策略（API Mock / Context Mock / Router Mock）

## 样式与 UI 规范（新增，~50行）
├── CSS 方案选择指引（CSS Modules / Tailwind / CSS-in-JS）
├── 响应式断点标准
├── 主题 / 设计令牌（Design Tokens）使用规范
└── 样式命名约定

## 状态管理规范（新增，~40行）
├── 本地状态 vs 全局状态判断标准
├── 状态库选择指引（useState / useReducer / Zustand / Redux）
├── 数据获取规范（SWR / React Query / 自定义 hooks）
└── 缓存与乐观更新策略

## 性能规范（新增，~50行）
├── 性能预算（LCP < 2.5s / FID < 100ms / CLS < 0.1）
├── 代码分割策略（路由级 lazy load / 组件级动态导入）
├── 图片优化（WebP/AVIF / 懒加载 / 尺寸约束）
├── Bundle 分析（定期检查，增量 > 50KB 需说明）
└── 渲染优化（React.memo / useMemo / useCallback 使用标准）

## 无障碍访问（新增，~30行）
├── 语义化 HTML（优先原生元素）
├── ARIA 标签规范
├── 键盘导航支持
└── 颜色对比度要求（WCAG AA）

## E2E 测试规范（已有，扩充 ~40行）
├── E2E 测试工具（Playwright 优先）
├── E2E 测试编写原则（用户视角、避免实现细节）
├── 测试数据管理（fixtures / seed / mock API）
└── CI 集成（并行执行、失败重试、截图上传）

## 构建与部署规范（新增，~30行）
├── 构建工具配置标准
├── 环境变量管理（.env 分层）
├── 静态资源版本策略（content hash）
└── Source Map 策略（生产环境上传到错误监控，不公开）
```

#### 5B（可选）：前端规范按框架细分

如果项目同时使用 React 和 Vue（或其他框架），可以进一步拆分：

```
standards/
├── common.md        # 通用
├── backend.md       # 后端
├── frontend.md      # 前端通用
├── frontend-react.md  # React 特定规范
└── frontend-vue.md    # Vue 特定规范
```

---

## 问题 6：Hooks 脚本健壮性

### 问题诊断

通过代码审查发现以下问题：

| 严重度 | 文件 | 问题 |
|--------|------|------|
| 🔴 高 | post-stop.sh:51 | 换行符双重转义 bug：`constraints+="${line}\n"` 拼接的是字面量 `\n`，后续 JSON 转义会变成 `\\n`，导致输出损坏 |
| 🔴 高 | 所有脚本 | 硬编码假设 `teamwork_space.md` 必须存在于项目根，否则所有 hooks 静默退出 |
| 🔴 高 | 所有脚本 | 硬编码中文关键词（"当前阶段"/"当前角色"/"已完成"），STATUS.md 格式变化即失效 |
| 🟡 中 | post-stop.sh:71,88 | `|| true` 静默吞掉 grep/sed 错误，空值与解析失败不可区分 |
| 🟡 中 | post-stop.sh:89 | 空日期被判为"过期"（空字符串 != 今天日期 → 恒真） |
| 🟢 低 | hooks.json | 10 秒超时对大型项目可能不够 |
| 🟢 低 | 所有脚本 | JSON 转义函数不处理 null 字节和非法 UTF-8 |

### 优化方案

#### 6A：修复换行符 bug（post-stop.sh:51）

```bash
# 修复前（字面量 \n）
constraints+="${line}\n"

# 修复后（真正的换行符）
constraints+="${line}"$'\n'
```

#### 6B：增加项目根发现的降级逻辑

```bash
find_teamwork_root() {
    local dir="$PWD"
    while [ "$dir" != "/" ]; do
        # 优先检查 teamwork_space.md
        if [ -f "$dir/teamwork_space.md" ]; then
            echo "$dir"
            return 0
        fi
        # 降级：检查 docs/features/ 目录存在（单子项目模式可能没有 teamwork_space.md）
        if [ -d "$dir/docs/features" ]; then
            echo "$dir"
            return 0
        fi
        dir=$(dirname "$dir")
    done
    return 1
}
```

#### 6C：增加解析值校验

```bash
# 修复前
phase=$(grep -m1 '当前阶段' "$status_file" 2>/dev/null | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//' || true)

# 修复后：增加格式校验
phase_raw=$(grep -m1 '当前阶段' "$status_file" 2>/dev/null || true)
if [[ "$phase_raw" == *"|"* ]]; then
    phase=$(echo "$phase_raw" | sed 's/.*|[[:space:]]*//' | sed 's/[[:space:]]*|.*//')
else
    phase=""  # 明确设为空，而非拿到一行非表格内容
fi
```

#### 6D：修复空日期误判

```bash
# 修复前
if [ "$update_date" != "$today" ]; then

# 修复后
if [ -n "$update_date" ] && [ "$update_date" != "$today" ]; then
```

#### 6E：超时调整

```json
{
    "type": "command",
    "command": "bash ${CLAUDE_PLUGIN_ROOT}/hooks/session-restore.sh",
    "timeout": 20
}
```

将三个 hooks 的超时从 10s 提升到 20s，给大型项目留出余量。

#### 6F：增加错误日志

在每个脚本开头增加：

```bash
log_warn() {
    echo "[teamwork-hook][warn] $1" >&2
}
```

在关键解析失败处调用 `log_warn`，方便调试。

---

## 问题 7：单人 vs 多人协作的模糊地带

### 问题诊断

`.teamwork_localconfig.md` 支持 scope 配置（全部 / 指定子项目），暗示多人协作场景。但整个框架的对话模型是单 Claude 会话，多人同时操作同一项目会导致：

- STATUS.md 被不同会话并发写入，产生冲突
- ROADMAP.md 状态被覆盖
- 两个会话可能同时推进同一个 Feature

### 优化方案

#### 7A：在文档中明确并发模型

在 SKILL.md 或 README.md 中增加：

```markdown
## 协作模型

### 单人模式（默认）
一个用户 + 一个 Claude 会话操作整个项目。
.teamwork_localconfig.md 的 scope 用于聚焦关注范围，而非并发控制。

### 多人模式（实验性）
多个用户各自使用 Claude 会话操作不同子项目。

🔴 多人模式约束：
├── 每个子项目同一时刻只能有一个会话在操作
├── 不同用户必须负责不同的子项目（scope 不重叠）
├── 跨子项目需求由一个用户统一协调（PMO 角色）
├── 如遇到 STATUS.md 被外部修改 → PMO 暂停，提醒用户检查
└── 不支持同一子项目的并发开发

### 不支持的场景
├── 两个会话同时修改同一个 Feature
├── 两个会话同时操作 teamwork_space.md
└── 无锁机制，并发安全依赖用户自律
```

#### 7B（可选）：简单的文件锁机制

在 hooks 中增加一个轻量锁：

```bash
# session-restore.sh 开头
LOCK_FILE="$ROOT/.teamwork_lock"
SESSION_ID="${CLAUDE_SESSION_ID:-$(date +%s)}"

if [ -f "$LOCK_FILE" ]; then
    existing=$(cat "$LOCK_FILE")
    log_warn "另一个会话 ($existing) 正在操作此项目"
    # 不阻塞，只警告
fi
echo "$SESSION_ID" > "$LOCK_FILE"

# post-stop.sh 结尾
rm -f "$ROOT/.teamwork_lock" 2>/dev/null
```

这不是真正的锁（无原子性），但足以提醒用户注意并发问题。

---

## 附加建议

### A1：TEMPLATES.md 拆分（详见问题 1A，此处补充迁移步骤）

**迁移步骤**：
1. 创建 `templates/` 目录
2. 按上述方案拆分为 15 个文件
3. 原 TEMPLATES.md 改为 `templates/README.md`（索引）
4. 更新 SKILL.md 中的"按需加载文件"表
5. 更新所有引用 TEMPLATES.md 的位置（INIT.md / ROLES.md / RULES.md 中的 `📎 模板见 TEMPLATES.md`）
6. 测试：确保各角色在对应阶段能找到正确的模板文件

### A2：增加快速上手示例

在 README.md 中补充一个"5 分钟快速上手"章节，展示从 `/teamwork 实现一个简单功能` 到完成的完整对话摘要（不需要展示全部细节，只展示关键节点和用户需要做的操作）。

### A3：增加 CHANGELOG.md

```markdown
# Changelog

## v4（当前）
- 中台子项目支持（business / midplatform）
- PL-PM Teams 讨论机制
- E2E 回归测试中心
- QA Lead 质量总结阶段
- 自下而上影响升级评估

## v3
- 业务架构与技术架构对齐方案落地
- Product Lead 三种工作模式
- CHG 变更记录机制
- Workspace Planning 流程

## v2
- 多子项目模式
- Hooks 自动化（SessionStart / PreCompact / Stop）
- 按需加载文件机制

## v1
- 基础 8 角色协作框架
- Feature / Bug / 问题排查 / Feature Planning 四种流程
```

### A4：KNOWLEDGE.md 模板精简

当前 455 行的 KNOWLEDGE 模板包含过多示例。精简为：
- 核心结构定义（~30 行）
- 一个完整示例（~40 行）
- 类型说明表（~20 行）
- 总计 ~90 行，减少 80%

---

## 优先级排序

| 优先级 | 方案 | 预计工作量 | 预计收益 |
|--------|------|-----------|---------|
| P0 | 6A: 修复换行符 bug | 5 分钟 | 修复数据损坏 |
| P0 | 6D: 修复空日期误判 | 5 分钟 | 修复逻辑错误 |
| P0 | 2C: 修复措辞不一致 | 10 分钟 | 消除歧义 |
| P1 | 1A: TEMPLATES 拆分 | 2 小时 | 减少 85-95% 模板加载量 |
| P1 | 3A: 轻量 Feature 路径 | 1 小时 | 大幅提升简单需求效率 |
| ~~P1~~ | ~~4A: 移除 Codex~~ | ~~30 分钟~~ | ✅ 已解决（2026-04-14） |
| P1 | 6B-6F: hooks 健壮性 | 1 小时 | 提升可靠性 |
| P2 | 2A-2B: 规则去重 | 2 小时 | 减少 context 消耗 + 消除矛盾风险 |
| P2 | 1B: RULES 拆分 | 1.5 小时 | 减少 RULES 加载量 |
| P2 | 5A: 前端规范补充 | 1.5 小时 | 提升前端项目支持 |
| P3 | 7A: 协作模型文档 | 30 分钟 | 明确使用边界 |
| P3 | A2: 快速上手示例 | 30 分钟 | 降低上手门槛 |
| P3 | A3: CHANGELOG | 15 分钟 | 版本管理 |
| P3 | A4: KNOWLEDGE 精简 | 20 分钟 | 减少模板体积 |

---

> 以上方案均为建议，请逐条确认是否执行。确认后我可以直接动手修改对应文件。

---

## 问题 8：角色与执行方式耦合（2026-04-15 新增）

### 问题诊断

当前 agents/ 目录混合了两种不同性质的文件：
- **真正的 Subagent spec**：dev-stage.md、test-stage.md、review-stage.md、pl-pm-discuss-stage.md、ui-design-stage.md、browser-e2e-stage.md — 这些由 PMO 通过 Task 工具 dispatch
- **主对话角色规范**：prd-review.md、tc-review.md、arch-tech-review.md — 这些在主对话中 PMO 切换角色执行，不是 Subagent

同时 ROLES.md（1,635 行）把所有角色定义集中在一个文件里，每个角色包含：触发条件、职责、输出标准、模板、反模式。PMO 每次只需要当前角色的定义，但被迫读到不相关角色的内容。

### 优化方案

#### 8A：roles/ 与 agents/ 分离

```
roles/                    ← 角色定义（职责 + 输出标准 + 触发条件）
├── pmo.md               ← PMO（从 ROLES.md L7-523 提取，517 行 → 精简到 ~200 行，模板引用 templates/）
├── product-lead.md      ← PL（从 ROLES.md L524-766 提取，243 行）
├── pm.md                ← PM（L767-918，152 行）+ prd-review.md 内容合并
├── designer.md          ← Designer（L919-1002，84 行）
├── qa.md                ← QA（L1003-1160，158 行）+ tc-review.md 内容合并
├── rd.md                ← RD + 架构师（L1161-1530，370 行）+ arch-tech-review.md 内容合并
└── anti-patterns.md     ← 反模式集中（L1531-1607，77 行）

agents/                   ← 只保留 Subagent spec + 通用规范
├── README.md            ← 执行方式速查表 + 通用执行约束（保持不变）
├── dev-stage.md         ← 🤖 Subagent（保持）
├── test-stage.md      ← 🤖 Subagent（保持）
├── review-stage.md ← 🤖 Subagent（保持）
├── pl-pm-discuss-stage.md     ← 🤖 Subagent（保持）
├── ui-design-stage.md         ← 🤖 Subagent（保持）
├── browser-e2e-stage.md            ← 🤖 Subagent（保持）
└── （Chain 内部子规范保持不变）

移出 agents/ → 合并到 roles/：
├── prd-review.md → roles/pm.md（PRD 技术评审维度）
├── tc-review.md → roles/qa.md（TC 技术评审维度）
├── arch-tech-review.md → roles/rd.md（架构师方案评审维度）
└── qa-lead-review.md → 归档删除（已从流程移除）
```

#### 执行步骤

1. 创建 roles/ 目录
2. 从 ROLES.md 按角色拆分为独立文件，同时精简（PMO 的模板引用 templates/，不内联）
3. 把 agents/ 里 3 个主对话 spec 的内容合并到对应 roles/ 文件
4. ROLES.md 改为索引文件（~30 行，指向 roles/*.md）
5. 更新所有引用（SKILL.md / RULES.md / agents/README.md / REVIEWS.md）
6. agents/README.md §五 文件索引更新（移除已迁出的文件）

#### 预期收益

- 角色定义按需加载：PMO dispatch RD 时只读 roles/rd.md，不用加载 1,635 行的 ROLES.md
- agents/ 目录干净：只有真正被 Task 工具 dispatch 的 Subagent spec
- 主对话评审规范跟随角色：PM 的 PRD 技术评审维度在 roles/pm.md 里，不在 agents/prd-review.md 里
- ROLES.md 从 1,635 行变成 ~30 行索引

#### 预估工作量

~30 分钟（主要是拆文件 + 更新引用）

#### 优先级

P2（架构优化，不影响功能正确性，但显著降低 token 消耗）

---

## 问题 9：Review 分散在三个 Stage 中（2026-04-15 新增）

### 问题诊断

三个代码审查活动散落在不同 stage 里，无法并行：
- 架构师 Code Review → 在 Dev Stage 内部（串行在 RD 开发后）
- Codex Review → 独立 stage（review-stage.md）
- QA 代码审查 → 在 Test Stage 内部（串行在测试前）

### 优化方案

#### 拆为 Dev → Review → Test 三段式

```
stages/
├── dev-stage.md          ← RD 开发 + 单元测试（TDD：写测试→实现→跑测试确认通过）
├── review-stage.md       ← 🆕 三个 review 并行：
│   ├── 架构师 Code Review（从 Dev Stage 拆出）
│   ├── Codex Review（从独立 stage 合入）
│   └── QA 代码审查（从 Test Stage 拆出）
│   └── 汇合：有问题 → RD 修复 → PMO 判断重跑哪些 review
├── test-stage.md         ← 从 test-stage.md 改名，集成级测试：
│   ├── 集成测试 ┐
│   └── API E2E  ┘ 并行（单元测试已在 Dev Stage 完成）
├── pl-pm-discuss-stage.md
├── ui-design-stage.md
└── browser-e2e-stage.md

删除：review-stage.md（合入 review-stage.md）
```

#### 流转链变化

```
Feature 流程：
... → Dev Stage（纯 RD 开发）→ Review Stage（三 review 并行）→ Test Stage（三测试并行）→ Browser E2E → PM 验收

修复循环：
Review Stage 有问题 → RD 修复 → 重跑 Review Stage（PMO 判断重跑哪些 review）
Test Stage 有问题 → RD 修复 → 重跑 Test Stage
```

#### 关键设计决策

架构师 CR 修复循环的变化：
- 当前：Dev Stage 内部 RD 写代码 → 架构师 CR → 发现问题 → RD 立即修 → 架构师再审（零 PMO relay）
- 改后：Dev Stage 只管 RD 写代码 → PMO dispatch Review Stage → 架构师发现问题 → PMO dispatch RD 修 → PMO dispatch Review Stage 重跑（每轮 2 次 PMO relay）

代价：修复循环多了 PMO relay 开销。
收益：三个 review 并行，总时间从串行 3 段降为并行 1 段；三个 review 的发现可以合并为 1 轮修复。

#### 执行步骤

1. 创建 stages/review-stage.md（三 review 并行定义）
2. 改写 stages/dev-stage.md（去掉架构师 CR 和修复循环）
3. 改写 stages/test-stage.md → 重命名为 test-stage.md（去掉 QA 代码审查）
4. 删除 stages/review-stage.md（合入 review-stage.md）
5. 改写 flow-transitions.md（Feature + 敏捷流程）
6. 改写 RULES.md 流转链
7. 更新所有引用

#### 预估工作量

~45 分钟

#### 优先级

P1（显著提升并行度，减少 review 总耗时）
```

---

## 问题 10：v7 重构后的待清理项（2026-04-15）

### ✅ 已完成
- flow-transitions.md 完整重写（8 stage 结构）
- RULES.md Feature 流转链重写
- stages/ 目录 8 个 stage 文件就绪
- roles/ 目录 6 个角色文件就绪
- agents/ 只保留 README.md + 5 个任务单元规范

### ✅ v7.1 清理已完成（2026-04-15）

1. ✅ **STATUS-LINE.md 阶段对照表更新** — 示例更新为 8-stage 阶段名
2. ✅ **ui-design-stage.md 内容重写** — 已在 v7 重构中完成（只做 Feature UI，全景拆到 Panorama Stage）
3. ✅ **旧引用清理** — RULES.md / FLOWS.md / REVIEWS.md / SKILL.md / STATUS-LINE.md / agents/README.md / standards/ / gate-checks.md 中的旧阶段名全部更新
4. ✅ **agents/README.md 速查表完整更新** — 反映 8-stage 结构，Blueprint Stage 合并 4 个旧行
5. ✅ **INIT.md CLAUDE.md 模板更新** — 已适配（红线 13 条+8-stage 引用 flow-transitions.md）
6. ✅ **templates/status.md 更新** — 显示名映射表完整重写，按流程分组
7. ✅ **敏捷需求流程的 RULES.md 流转链** — 已正确引用 8-stage 名称

---

## 问题 11：Worktree 集成（2026-04-15 新增）

### ✅ 已完成（2026-04-15）

### 需求

每个 Feature 使用独立 git worktree，代码隔离，并行开发不冲突。

### 方案（已实施）

**INIT.md 启动时检查**：
- .teamwork_localconfig.md 增加 worktree 策略字段（off/auto/manual，默认 off）
- 检查当前是否在某个 Feature worktree 中（git worktree list）
- 输出到启动报告

**Dev Stage 集成**：
- worktree=auto → PMO 预检时自动创建：`git worktree add ../feature-{编号} -b feature/{编号}`
- Dev/Review/Test Stage 在 worktree 目录中执行
- Feature 完成后 PMO 清理 worktree：`git worktree remove ../feature-{编号}`

**flow-transitions.md 变化**：
- Dev Stage 前增加 worktree 创建检查（L2 预检的一部分）
- PM 验收后增加 worktree 清理步骤

### 优先级

P2（增强功能，不影响核心流程）

---

## 问题 12：⚡ auto 模式一次性总开关（2026-04-19 新增 · P0-11）

### ✅ 已完成（2026-04-19）

### 需求

teamwork 暂停点密集（单个 Feature 10+ 次 ⏸️），对"我心里有数、按你建议推"的场景体验重。需要一次性总开关让 PMO 按 💡 自动推进，但保留关键决策的强制暂停。

### 方案（已实施）

**入口（INIT.md Step 0）**：
- `/teamwork auto [需求]` / `auto 继续` / `auto ship F{编号}` → AUTO_MODE=true
- 其他形式（`/teamwork [需求]` / `/teamwork 继续` / `/teamwork` 无参）→ AUTO_MODE=false

**作用域**：**单次命令周期**（仅本次 /teamwork 生命周期）
- 用户重新 /teamwork（不带 auto）→ 自动重置
- 运行时用户消息含「停 / 暂停 / manual / 等一下 / 先等等」→ 立即关闭
- compact 后 → 默认 false
- 🔴 **不持久化**到 localconfig / state.json（避免"以为关了其实没关"的事故面）

**豁免范围**（按 💡 自动推进）：
- 普通方案 / PRD / UI / TC / TECH 草稿 review 后流转
- 阶段切换、Plan Stage 入口 preflight（4 硬门禁全 ✅ 时）
- dispatch 前检、review 结果接受、摘要流转
- 非强制保留的 ⏸️

**强制保留项**（即便 AUTO_MODE=true 也必须 ⏸️）：
- PM 验收三选项 / Ship worktree 清理 / Ship push FAILED（v7.3.10+P0-15 更新，详见 问题 15）
- Dev / Test BLOCKED 或 FAILED、Review FAILED
- PL-PM 分歧 / Blueprint concerns / MUST-CHANGE
- Micro 用户验收与升级确认
- 外部依赖已就绪恢复
- Planning / PL 模式最终确认
- 13 红线触发 / 破坏性 git / DB 操作
- 用户消息含「？/ 确认下 / 等我看看 / 核对一下」等意图不确定语气

> 🔄 v7.3.10+P0-15 更新：原"Ship 关键操作（ship_policy=confirm 下）/ Ship 冲突"暂停点已在 P0-15 Ship Stage MR 化后移除（ship_policy 字段废弃，PMO 不再做合并/解冲突）。

~~**ship_policy 正交**：auto 是 session 级总开关，ship_policy 是 Ship Stage 细粒度；auto **不覆盖** `ship_policy=confirm`。~~ 🔄 v7.3.10+P0-15 已废弃：ship_policy 字段随 Ship Stage MR 化一并移除。

**显示与日志**：
- STATUS-LINE 第一行在 `🔄 Teamwork 模式` 与 `|` 间插入 `⚡ AUTO` 徽章（AUTO_MODE=true 时）
- 每个豁免暂停点输出 `⚡ auto skip: {决策简述} | 💡 {建议} | 📝 {理由}`
- 命中强制保留时输出「⚡ auto 模式已开启，但此暂停点强制保留」提示

### 影响文件

- `INIT.md`：Step 0 命令行解析
- `roles/pmo.md`：新增「⚡ auto 模式暂停点豁免规则」章节
- `rules/flow-transitions.md`：顶部新增「⚡ auto 模式豁免速查」块
- `STATUS-LINE.md`：第一行 ⚡ AUTO 徽章 + 规则 + 示例
- `docs/CHANGELOG.md`：P0-11 条目 + P0 影响面更新

### 与 P0-9 的对称设计

| 设计 | 默认 | 显式 opt-in 时机 |
|------|------|----------------|
| P0-9 worktree | off | 改 localconfig `worktree: auto/manual` |
| P0-11 auto 模式 | false | 每次 /teamwork auto [需求] |

两者都刻意不把复杂性藏在默认值里，由用户显式开启，自担理解成本。

### 优先级

P0（高频场景体验问题，收益面大）

---

## 问题 13：Codex 交叉评审对 Plan / Blueprint Stage 成本过高（2026-04-20 新增 · P0-13）

### ✅ 已完成（2026-04-20）

### 需求

用户反馈 "Feature 流程每次都强制 Codex 成本太高，PRD 流程也不需要"。审计：Plan + Blueprint Stage 的 Codex 交叉评审每次 +10-20 min + ~10K token，对小改动 / 内部视角已充分的场景 ROI 偏低。

### 方案（已实施）

**范围拆分（保留高价值 Codex，下调低价值 Codex）**：

| Stage | Codex 类型 | P0-13 前 | P0-13 后 | 理由 |
|-------|-----------|---------|---------|------|
| Plan | 文档交叉评审（PRD） | 🔴 强制 | 🟡 opt-in（默认 OFF） | 内部多视角（PM+PL+RD+Designer+QA+PMO）已覆盖 PRD 质量下限 |
| Blueprint | 文档交叉评审（TC+TECH） | 🔴 强制 | 🟡 opt-in（默认 OFF） | 4 步内部闭环已覆盖技术设计评审 |
| Review | 代码审查（code） | 🔴 强制 | 🔴 强制（不变） | 代码层最后一道 gate，盲区独立采样 + 静态分析最有价值 |

**开关机制（state.json 持久化 + PMO 初步分析决策）**：
- state.json 新增 `codex_cross_review = {enabled, decided_at, decided_by, note}` 字段，默认 `enabled: false`
- PMO 初步分析 4 种输出格式（Feature / 敏捷需求 / Feature Planning / 跨子项目）均新增「🤖 Codex 交叉评审决策」行
- 用户 4 选 1（默认不开 / 全开 / 只开 Plan / 只开 Blueprint）
- PMO 建议逻辑：大改动 / 跨子项目 / 高风险 → 建议开；小改动 / 单文件 / Bug 修复 → 建议不开

**执行层条件化（2 Stage md 全方位改造）**：
- `stages/plan-stage.md` 7 处改造（Input Contract / Process Contract Step 3 / 过程硬规则 5 项 / Output Contract 表格 / 机器校验 / 执行报告模板）
- `stages/blueprint-stage.md` 8 处改造（同上 + Done 判据 + AI Plan 模式指引）
- 条件统一：`state.codex_cross_review.enabled == true` 时必做，== false 时整段跳过 + 评审文件尾部声明"Codex 已关闭"

### 影响文件

- `templates/feature-state.json`：新增 `codex_cross_review` 字段
- `templates/codex-cross-review.md`：§二适用场景表全行改 opt-in；新增 §2.1 PMO 初步分析决策；§八 R7 改写
- `stages/plan-stage.md`：条件化 Codex Step 3 / 硬规则 / 产物表 / 校验
- `stages/blueprint-stage.md`：条件化 Codex Step 5 / 硬规则 / 产物表 / 校验 / Done 判据 / 执行报告
- `stages/review-stage.md`：新增"本 Stage Codex 不受 P0-13 开关影响"明确声明
- `roles/pmo.md`：新增「🤖 Codex 交叉评审开关决策」独立章节
- `FLOWS.md`：PMO 初步分析 4 种输出格式新增 Codex 决策行
- `templates/review-log.jsonl`：顶部注释说明 plan-codex-review / blueprint-codex-review 行条件化，review-codex 保持强制
- `docs/CHANGELOG.md`：P0-13 条目

### 与先前 P0 的协同

| 开关 | 默认 | 显式 opt-in 时机 | 作用域 |
|------|------|----------------|-------|
| P0-9 worktree | off | localconfig `worktree: auto/manual` | 工作区持久 |
| P0-11 AUTO 模式 | false | `/teamwork auto [需求]` | 单次命令周期 |
| P0-13 codex_cross_review | false | PMO 初步分析 4 选 1 | 单 Feature 持久（state.json） |

三者共同原则：**复杂性不藏默认值，用户显式开启自担理解成本**。P0-13 的作用域是"单 Feature"，介于 P0-9（工作区级）和 P0-11（单次会话）之间，粒度最匹配 Codex 的使用场景。

### 兼容性

- 既存 state.json（缺 codex_cross_review 字段）→ PMO 按 `enabled=false` 默认处理，不触发迁移
- 既存完成的 Feature 不受影响；进行中 Feature 由 PMO 在下次 Stage 入口补写字段
- Review Stage Codex 代码审查：🔴 强制不变，完全复用原规范（review-stage.md + codex-agents/code-reviewer.toml）

### 优先级

P0（成本治理，用户明确反馈）

---

## 问题 14：Dev Stage 默认 subagent 偏保守，主对话更匹配多数 Feature（2026-04-22 新增 · P0-14）

### ✅ 已完成（2026-04-22）

### 需求

用户反馈"开发阶段在主对话，是否合理，不要求在 subagent，由 RD 自行规划 Plan 模式"。审计发现 v7.3.9 虽在文档宣称"Dev Stage AI 自主判断"，实际 3 处默认偏向 subagent：
1. `agents/rd-develop.md` 整篇"RD Subagent"视角（标题 / 执行摘要 / NEEDS_FIX 自降都按 subagent 措辞）
2. `templates/feature-state.json` planned_execution.dev 示例直接给 approach="subagent"
3. `agents/README.md` §一默认表判断列"≤3 文件 → main"，隐含 >3 文件即 subagent（实战多数 Feature 都 >3 文件）

### 方案（已实施）

**默认翻转 + dual-mode 化**：

| 维度 | P0-14 前 | P0-14 后 | 触发 subagent 阈值 |
|------|---------|---------|------------------|
| Dev Stage 默认 approach | 隐式 subagent（文档宣称 AI 自主但细节全偏 subagent）| `main-conversation` | TECH.md 文件清单 >10 / 预期产出 >500 行 / 需独立聚焦或跨模型独立性 |
| rd-develop.md 视角 | RD Subagent 单视角 | Dual-Mode（7 维对比表 + 5 条共同契约） | - |
| 执行摘要模板 | 单一"RD Subagent 执行摘要" | 4.1a 主对话（边做边汇报）+ 4.1b subagent（完成后一次性）| - |

**dual-mode 共同契约（两模式完全一致）**：
- TDD 红-绿-重构三步必走（§三.1）
- UI 还原权威层级 + 自检清单（§三.4，P0-12 成果）
- RD 自查 7 维度（§三.3）
- 产物格式 + auto-commit
- DONE / NEEDS_FIX / FAILED 三态 gate + UI 还原缺失自降 NEEDS_FIX

**灰色地带判定示例**（dev-stage.md AI Plan 指引新增）：
- 「10 文件 / 400 行 / 单模块」→ 主对话（边界内）
- 「12 文件 / 600 行 / 跨前后端」→ subagent（超边界）
- 「8 文件 / 300 行 / 3 轮 TDD 调试」→ 主对话（调试需要过程可见）
- 存疑时向默认倾斜

### 影响文件

- `agents/rd-develop.md`：标题 + §一 角色定位（对比表 + 共同契约）+ §二 输入文件（模式对比）+ §四 执行摘要拆双模板；§三 TDD / UI 还原 / 开发约束 / RD 自查全部保持不变
- `stages/dev-stage.md`：AI Plan 指引表从"AI 自主判断"改为"默认主对话 + 超阈值 opt-in"；新增灰色地带判定示例；Duration baseline 主对话路径前置
- `agents/README.md`：§一默认表 Dev Stage 行改 `main-conversation（v7.3.9+P0-14 默认）` + 判断列精确化
- `templates/feature-state.json`：planned_execution.dev 主示例改 approach="main-conversation" + rationale 引用 P0-14；保留 `_subagent_alternative_example` 作为 opt-in 样例
- `docs/CHANGELOG.md`：P0-14 条目

### 根因分析

**为什么 v7.3.9 "AI 自主"没生效**：
- 规范层（README §一"AI 自主"）与执行层（rd-develop.md 全篇 subagent 语境 + state.json 示例 subagent）不一致 → RD 启动时第一眼看到的是"subagent 默认"
- 判断规则 "≤3 文件 → main" 阈值过低 —— 实战 Feature 多为 5-10 文件，本该走主对话却因规则自动分流到 subagent
- 缺乏"主对话模式执行摘要模板" → RD 即便想走主对话也不知道产出长什么样 → 回退 subagent

**为什么主对话是更优默认**：
- 省冷启动：subagent 单次冷启动 3-5 min，Dev Stage 经常需多轮调试 → 累积冷启动税高
- 复用已加载 context：Plan / Blueprint 已加载 PRD/TC/TECH（5-10K token），主对话直接复用 vs subagent 按 dispatch 重读
- TDD 过程可见：用户可以在红-绿-重构中途发现方向偏差 + 介入调试，subagent 完成后才回到用户视野
- Dev Stage 是 RD 单视角执行，独立性价值低（不像 Review Stage 需要 Codex / QA 跨视角盲区兜底）

### 与先前 P0 的协同

| P0 | 默认改动 | 开关粒度 | 对齐的用户反馈 |
|----|--------|---------|--------------|
| P0-9 | worktree 默认 off（v7.3.8 引入 auto，P0-9 回撤到 off）| 工作区持久 | "worktree 太重不想默认开" |
| P0-13 | Plan/Blueprint Codex 默认 OFF | 单 Feature（state.json）| "Codex 每次强制成本太高" |
| P0-14 | Dev Stage 默认 main-conversation | 单 Stage（Execution Plan）| "开发要不要 subagent 由 RD 自己规划" |

三者共同脉络：**框架默认向"轻成本 + 可见性"倾斜，重成本/强隔离路径保留为 opt-in**。用户关心的是冷启动税 / 成本 / 过程可见性，框架原先为了"保险"走了强隔离默认 —— P0-9 / P0-13 / P0-14 三连做的是一致的校准。

### 兼容性

- 既存 Feature（已完成 Plan/Blueprint）不受影响；Dev Stage 未启动的进入时按新默认
- 既存 dispatch_log / Codex CLI 子 agent（若有）全部保留 —— subagent 模式路径完整保留，仅非默认
- state.json schema 不变（approach 字段本就支持 main-conversation / subagent / hybrid）
- rd-develop.md dual-mode 化后，原 subagent 模式的 Input / Process / Output 契约完全保留

### 优先级

P0（用户反馈，直接改善开发节奏体验）

---

## 问题 15：Ship Stage 让 PMO 承担本地 merge / push merge_target / 冲突解决，职责过重（2026-04-22 新增 · P0-15）

### 现象

v7.3.9 Ship Stage 设计的 6 步流让 PMO 直接介入代码层操作：

1. 净化（合理）
2. `git push origin {feature branch}`（合理）
3. `git rebase origin/{merge_target}`（可选）—— PMO 改分支历史
4. 切 `merge_target` + `git merge --no-ff {feature branch}` —— PMO 合并
5. `git push origin {merge_target}` —— PMO 推主干
6. worktree 清理（合理）

配套：红线 #1 ("PMO 非 Micro 流程下不得改代码") 开了 Ship 例外条款，允许 PMO 解 git 冲突标记（仅消除 marker，解完必须单测全绿）。

### 问题

1. **职责越界**：PMO 是"流转守门员"，现在变成"代码合入执行者" —— 做 rebase / merge / 解冲突都是代码层决策
2. **红线 #1 被稀释**：绝对红线开例外条款，信任边界表达弱化
3. **多人协作风险高**：PMO 直接 push merge_target 可能覆盖他人改动 / 污染主干 / 绕过平台代码评审 / 绕过 CI 门禁
4. **冲突解决路径复杂**：v7.3.9 需要区分"PMO 可解（简单 marker）vs 必须升级用户（跨函数/跨文件）"，判定标准"解完单测全绿"需要 PMO 跑测试 → 更多代码层动作
5. **与主流 git workflow 不符**：GitHub Flow / GitLab Flow / Trunk-Based 核心都是"push 分支 + 平台合入"，直连合并是反模式
6. **MR/PR 平台的价值被绕过**：代码评审 / CI/CD 检查 / 审批流 / 合规审计 —— 这些 PMO 本地 merge 都没有

### 用户反馈

> "当前 Ship 流程是什么，是否可以简化，例如开发完成后新分支的代码提交 push 后，生成 MR create 链接由用户创建 MR 可以了，这个 MR create 链接要记到 state.json 中，方便以后回溯，然后清理 worktree（如有），不删远程 feature 分支"
>
> "不要 direct-merge，给了 MR 或 PR 后合入一下不麻烦"
>
> "mr_create_url 就可以"

用户诉求非常清晰：PMO 只负责送到平台门口，合入交给平台 + 用户。

### 处理方案

将 Ship Stage 从 6 步直连合并流改为 **3 步 MR 流**：

**v7.3.10+P0-15 3 步流**：

1. **净化**（不变，灰名单策略保留）
2. **push feature + 生成 MR/PR create URL**：
   - `git push origin {feature branch}`
   - 读 `git remote get-url origin` → 按 host 匹配（github.com / gitlab.com / gitee.com / bitbucket.org / 自建 gitlab）→ 生成对应平台的 MR/PR create URL
   - 未识别平台（unknown）→ 尝试读 localconfig `mr_url_template`；仍不可用 → `mr_create_url=null` + 在完成报告 concerns 标注"未识别平台，请手动创建 MR"
3. **worktree 清理**（不变，保留 `ask/keep/remove` 策略）

**硬规则（从 Ship Stage 移除）**：

- ❌ 禁止本地 `git merge` / `git rebase` / `git cherry-pick` 到 merge_target
- ❌ 禁止 `git push origin {merge_target}`
- ❌ 禁止 PMO 解冲突（push feature 失败 → ⏸️ 用户决策，不重试、不降级）
- ❌ 禁止伪造 / 猜测 MR URL（unknown 平台 → null + concerns 标注）
- ❌ 禁止删除远程 feature 分支（用户可能要在 MR 合入后手动删）

**红线 #1 简化**：移除 Ship 例外条款。"PMO 非 Micro 流程下不得改代码" 回到真正的绝对红线，不再维护例外清单。

### state.json.ship 字段重构

**移除**：`rebase_status` / `merge_commit_hash` / `push_status`（PMO 不做这些操作）

**新增/保留**：

```json
"ship": {
  "sanitize_log": { "residual_commits": [], "cleaned_files": [], "suspicious_files": [] },
  "git_host": "github | gitlab | gitlab-self-hosted | gitee | bitbucket | unknown",
  "mr_create_url": "完整链接 / null",
  "feature_pushed_at": "时间戳",
  "worktree_cleanup": "cleaned | deferred | n_a",
  "shipped": true
}
```

### localconfig 字段变化

**移除**：`ship_rebase_before_push`（不再做 rebase）/ `ship_policy`（不再有 merge+push 暂停点）

**保留**：`merge_target` / `worktree_cleanup`

**新增**：`mr_url_template`（可选）—— 自建 GitLab / 企业 git 自定义链接格式，支持 `{remote_url}` / `{repo_path}` / `{feature_branch_enc}` / `{merge_target}` 占位符

### 暂停点收敛

v7.3.9 Ship Stage 3 个暂停点：

1. `ship_policy=confirm` 下 merge+push 待确认
2. worktree 清理待确认
3. Ship Stage 冲突 / FAILED → 用户 3 选 1

v7.3.10+P0-15 Ship Stage 1 个常规 + 1 个异常暂停点：

1. worktree 清理待确认（常规，不变）
2. push FAILED → 用户 2 选 1（手工处理后复跑 / 取消 Ship）

### 收益

- **职责边界清晰**：PMO = 流转守门员，不碰代码层决策；平台 + 用户 = 代码合入者
- **红线 #1 真·绝对**：无例外条款，信任模型简洁
- **多人协作友好**：MR/PR 平台的代码评审 / CI / 审批 / 审计全部自然走到
- **无冲突解决成本**：PMO 不解冲突 → 不需要单测全绿校验 / 无中间态
- **暂停点从 3 降到 1+1**：用户交互次数减半

### 兼容性（破坏性变更）

- v7.3.9 已完成 Ship 的 Feature 保留旧 state.json.ship 字段（审计痕迹），不强制迁移
- v7.3.9 进行中、未到 Ship Stage 的 Feature 进入 Ship 时走新流程、写新字段
- localconfig 的 `ship_rebase_before_push` / `ship_policy` 字段 PMO 自动忽略（不报错），建议用户升级时手动清理
- Codex CLI 子 agent 不受影响（Ship Stage 始终 PMO 主对话自主，不走 subagent）

### 与 P0-9（worktree 默认 off）/ P0-13（Codex opt-in）/ P0-14（Dev 默认主对话）的脉络对照

| 编号 | 主题 | 简化方向 | 共同脉络 |
|------|------|----------|----------|
| P0-9 | worktree 默认 off | 保守兜底 → 默认轻量 | 框架默认向"轻成本"倾斜 |
| P0-13 | Plan/Blueprint Codex 默认 OFF | 强制 → opt-in | 重成本路径变 opt-in |
| P0-14 | Dev Stage 默认主对话 | 默认 subagent → 默认主对话 | 职责默认回主对话 |
| P0-15 | Ship Stage MR 化 | PMO 直连合并 → MR 模式 | 框架不越界做平台该做的事 |

四者共同脉络：**框架做好自己的事（状态机 / 流转 / 质量门禁），不越界做工具链 / 平台该做的事**。用户对"代价 vs 价值"的敏感度很高，框架原先为了"更安全"或"更一致"走了重路径 —— P0 系列做的是一致的校准。

### 优先级

P0（用户反馈，直接简化 PMO 职责边界 + 降低协作风险）

---

## 问题 16：Micro 流程 v7.3 放宽后 7 文件残留 "RD Subagent" 旧描述，自相矛盾（2026-04-23 新增 · P0-16）

### 问题诊断

> 用户反馈："Micro 流程是否还强制 RD 在 subagent 下执行，预期是 Micro 流程在初步分析后，PMO 自行判断是否切 Plan 模式还是以 RD 角色身份直接在主对话修改"

v7.3 早已放宽：FLOWS.md §六「Micro 流程」+ SKILL.md 红线 #1 Micro 例外 + SKILL.md L122-126「AI Plan 模式 Micro 例外」三处明确「PMO 可直接改代码，无需 Subagent / Execution Plan / dispatch」。但其他 7 个文件未同步更新：

| 文件 | 位置 | 残留旧描述 |
|------|------|------------|
| SKILL.md | L320 六种流程速查 | `Micro → ... RD Subagent 执行 → ⏸️用户验收` |
| RULES.md | L521-547 Micro 流程自动流转图 | `🤖 RD Subagent 执行改动（🔴 PMO 禁止自己改，即使只改一行）` |
| RULES.md | L720 功能完成时 PMO 校验 | `校验 PMO 分析→用户确认→RD Subagent→用户验收 四步` |
| rules/flow-transitions.md | L39-40, L52 豁免表 | `Micro 流程：🤖 RD Subagent → 用户验收` |
| rules/flow-transitions.md | L167-177 Micro 流程表 | 表头: `PMO 禁止自己改代码，必须启 RD Subagent`；4 行表均基于 RD Subagent 路径 |
| roles/pmo.md | L5 | `Micro 流程下 PMO 可直接改代码（零逻辑变更白名单内），但必须走 Plan 模式规划 + 用户确认流程`（与 FLOWS.md §六 冲突）|
| roles/pmo.md | L748 auto 豁免表 | `Micro 分析 → Micro 变更说明` |
| roles/pmo.md | L1379 反模式 | `即使只改一行也必须启 RD Subagent` |
| roles/pmo.md | L1388-1399 小改动决策树 | `🔴 任何情况下 PMO 都不能自己动手改代码` |
| STATUS-LINE.md | L201 示例 | `下一步：🤖 启动 RD Subagent` |
| STATUS-LINE.md | L277-280 阶段对照表 | `Micro 变更说明 / 🤖 RD Subagent（Micro）` 两行基于 Subagent 语义 |
| standards/common.md | L242 L1 预检 | `包括 Micro 流程的 RD Subagent` |
| standards/common.md | L354 预检级别速查 | `Micro | RD Subagent | L1` |

### 影响

- **自相矛盾**：同一套规范里有文档说"PMO 直接改"、有文档说"必须启 RD Subagent"，PMO 按哪一份读都无法确定。
- **强制路径错位**：部分描述（如 flow-transitions.md L169）用"🔴"标注"必须启 RD Subagent"，这让读规范的 PMO 在实际跑 Micro 时倾向启 Subagent，违背 v7.3 放宽的初衷。
- **决策空间丢失**：用户期望的模型是"PMO 自行判断直接改 / 升级 Plan 模式"，但残留描述把 Micro 锁死为"必走 Subagent"一条路。

### 根因

v7.3 放宽红线时只改了 FLOWS.md §六 + SKILL.md 红线体系，未做跨文件一致性清理。这些残留从 v7.2 继承下来，看起来仍在"正常工作"，但实际上对读者产生误导。

### 优化方案

对 7 个文件 12 处残留做统一修订：全部改为「PMO 自行判断执行方式（✍️ 主对话以 RD 身份直接改 / 🔀 升级为 Plan 模式走敏捷或 Feature）」。

关键修订点：
1. 流转表 / 流程图中把「🤖 RD Subagent 执行」节点替换为「PMO 执行改动（主对话直接改）」+ 升级判定支路
2. 反模式 / 决策树中把「任何情况下 PMO 都不能改代码」拆成 Micro 外（禁止）/ Micro 内（可直接改）双分支
3. 阶段对照表 / 状态行示例改为 `PMO 执行改动中` / `等待用户验收`
4. 预检级别表 Micro 行从「L1」改为「—（不启 Subagent）」
5. 所有描述加 v7.3 放宽 + P0-16 明确标注，让读者知道这不是新规则，是对既有规则的一致性补齐

### 收益

- **消除自相矛盾**：Micro 流程描述从"两份互斥规范"归一到"PMO 自行判断"
- **显式承载用户意图**：双路径（直接改 / 升级 Plan）在规范里写明，而非"隐含在 Micro 升级条件"中
- **红线体系清晰**：Micro 外 PMO 不得改代码 + Micro 内 PMO 可直接改（零逻辑白名单），无需维护"什么时候启 Subagent"

### 与 P0-9 / P0-13 / P0-14 / P0-15 的脉络对照

| 编号 | 主题 | 简化方向 | 共同脉络 |
|------|------|----------|----------|
| P0-9 | worktree 默认 off | 保守兜底 → 默认轻量 | 框架默认向"轻成本"倾斜 |
| P0-13 | Plan/Blueprint Codex 默认 OFF | 强制 → opt-in | 重成本路径变 opt-in |
| P0-14 | Dev Stage 默认主对话 | 默认 subagent → 默认主对话 | 职责默认回主对话 |
| P0-15 | Ship Stage MR 化 | PMO 直连合并 → MR 模式 | 框架不越界做平台该做的事 |
| P0-16 | Micro 流程去 Subagent 化 | 强制 Subagent → PMO 自行判断 | 默认主对话 + 最小闭环，去除多余仪式 |

P0-16 是 P0-14（Dev Stage 默认主对话）在 Micro 流程的对偶：都是把"默认启 Subagent"的旧保守路径回归到"默认主对话 / 默认自行判断"。

### 优先级

P0（用户反馈，文档一致性问题，无代码影响）

---

## 问题 17：Init.md Step 1.2 每次启动都 Read + diff CLAUDE.md，token 重复消耗（2026-04-23 新增 · P0-17）

### 问题诊断

> 用户反馈："目前读 Init.md 的逻辑是什么，从 token 占用角度，是否有优化空间"
> 用户反建议："我们是否在 .teamwork_localconfig.md 中加一个当前 teamwork 版本，如果和 skill.md 版本不一致的时候再去做 claude.md 和 agent.md 检查，更合理，复用本地的轻量级文件。"

INIT.md 启动必做 3 步中 Step 1.2 固定动作：Read 项目根 `{HOST_INSTRUCTION_FILE}`（CLAUDE.md / AGENTS.md）→ 对照 37 行模板**逐字符 diff** → 不一致则替换。

| 段落 | 行数 | 每次启动 token 成本 |
|------|------|---------------------|
| Step 0 AUTO 解析 | 65 | ~1500（规则描述） |
| Step 1.1 宿主检测 | 15 | ~400 |
| **Step 1.2 CLAUDE.md 校验** | **72**（含 37 行模板） | **~2000-3500（Read 文件 + diff 比对 + 模板加载）** |
| Step 2 项目空间加载 | 23 | ~600 |
| Step 3 Feature 看板 | 17 | ~300 |

Step 1.2 占启动总 token 的 40-55%，但**日常启动 99%+ 场景都是"skill 未升级 → 模板未变 → diff 必然一致"的重复工作**。

### 影响

- **高频重复 I/O**：每次 `/teamwork` 启动都做一次等价于"读文件 + 字符比对 + 模板内存加载"的工作，但结果几乎恒定
- **漂移自愈能力的真实触发频率极低**：skill 升级频率 = 周/月级；启动频率 = 日级 → 漂移检测在 99%+ 场景是空跑
- **token 浪费直接影响用户体验**：长会话 compact 后 teamwork 重启启动成本叠加到上下文压力

### 根因

CLAUDE.md 模板内容只在 skill 升级时才会变化，但 Step 1.2 把"模板漂移检测"做成了每次启动必跑的硬校验——用高频成本买低频收益。

### 优化方案

用 `.teamwork_localconfig.md` 中的 `teamwork_version` 字段做缓存标志：

1. **SKILL.md frontmatter 新增 `version: 7.3.10+P0-17`**（单一权威版本号，放 frontmatter 使解析成本最低）
2. **templates/config.md localconfig 模板加 `teamwork_version:` 段**（🔴 PMO 自动维护，禁止手改）
3. **INIT.md Step 1.2 重写为缓存-校验-回写模式**：
   - 1.2-a：读 SKILL.md frontmatter `version` → `SKILL_VERSION`
   - 1.2-b：读 localconfig `teamwork_version` → `LOCAL_VERSION`
   - 1.2-c：比对
     - ⚡ fast path（一致，99%+ 场景）→ 跳过 CLAUDE.md Read + diff，输出"⚡ CLAUDE.md 校验跳过"
     - 🔄 full path（不一致 / null）→ 走原 P0-17 前全量校验 + 回写 localconfig
     - 🚨 SKILL_VERSION=null → 降级全量 + ⚠️ 提示
4. **INIT.md Step 0 加 `/teamwork force-init` 逃生舱**：用于强制全量校验（怀疑 CLAUDE.md 被外部工具手改时）

### 收益

- **启动 token 节省 ~65-75%**：
  - fast path 总成本：Step 0 ~1500 + Step 1.1 ~400 + Step 1.2 ~200（版本比对）+ Step 2 ~600 + Step 3 ~300 = ~3000
  - P0-17 前成本：Step 0 ~1500 + Step 1.1 ~400 + Step 1.2 ~3000 + Step 2 ~600 + Step 3 ~300 = ~5800
  - 节省率 = (5800-3000) / 5800 ≈ 48%；如果只看 Step 1.2 本段，节省率 = (3000-200) / 3000 ≈ 93%
- **漂移自愈保留**：skill 升级 → 版本不一致 → 一次性全量修复 → 此后跳过。语义等价于 P0-17 前
- **复用既有机制**：localconfig 已 gitignore、已是 Step 2 必读文件，作为缓存载体无额外 I/O 成本
- **多开发者兼容**：每开发者各自维护 localconfig 版本，不产生 git 冲突

### 兼容性

非破坏性向前兼容：
- P0-16 用户升级到 P0-17：首次启动 LOCAL_VERSION=null → 走全量 + 写回 → 此后稳态 fast path
- localconfig 缺失：首次启动创建最小版 localconfig（scope:all + teamwork_version）
- CLAUDE.md 被用户手改但 skill 未升级：版本仍命中 → 跳过校验 → 用户修改被保留（"respect user edits"；需强制恢复用 `/teamwork force-init`）
- 用户伪造 teamwork_version：理论绕过风险 → 靠模板注释"禁止手改" + force-init 兜底

### 与 P0-9 / P0-13 / P0-14 / P0-15 / P0-16 的脉络对照

| 编号 | 主题 | 简化方向 | 共同脉络 |
|------|------|----------|----------|
| P0-9 | worktree 默认 off | 保守兜底 → 默认轻量 | 框架默认向"轻成本"倾斜 |
| P0-13 | Plan/Blueprint Codex 默认 OFF | 强制 → opt-in | 重成本路径变 opt-in |
| P0-14 | Dev Stage 默认主对话 | 默认 subagent → 默认主对话 | 职责默认回主对话 |
| P0-15 | Ship Stage MR 化 | PMO 直连合并 → MR 模式 | 框架不越界做平台该做的事 |
| P0-16 | Micro 流程去 Subagent 化 | 强制 Subagent → PMO 自行判断 | 默认主对话 + 最小闭环 |
| P0-17 | INIT.md Step 1.2 版本缓存 | 每次硬校验 → 版本命中时跳过 | 高频成本只在真正需要时付出 |

P0-17 与 P0-9/13/14/15/16 共享同一"去除多余仪式 / 成本只在真正需要时付出"哲学：默认路径从"每次硬跑一次"回归到"有缓存则跳、无缓存或升级才跑"。

### 优先级

P0（用户反馈，启动体验优化，无破坏性变更）

---

## 问题 18：ok / 好 / 可以 等模糊确认被强制要求二次复述，与实际用户意图不符（2026-04-23 新增 · P0-18）

### 问题诊断

> 用户反馈："加一个指令说明，ok = 按建议"

现有规范（RULES.md §模糊确认处理 L186 + STATUS-LINE.md L316）：

```
🔴 禁止把「好」「行」直接视为全面授权（因为不对应具体编号）
模糊确认（≤5 字：好/可以/OK）→ 🔴 PMO 先复述阶段链再等二次确认
```

### 影响

- **与用户意图错位**：红线 #10 已强制每个 ⏸️ 暂停点必须输出 💡 推荐 + 📝 理由，用户回复 ok 在"有 💡"的上下文中 ≈ 100% 是"按推荐走"意图。但规范要求 PMO 复述 + 二次确认，给用户额外打字负担
- **多决策点摩擦放大**：用户想"两项都按推荐"要打 `1A 2A`（5 字符），而 ok 只需 2 字符
- **规范自相割裂**：红线 #10 投入成本让 💡 一定出现，但 💡 的语义价值未被充分使用——💡 只是"参考建议"，而不是"可以被 ok 直接引用"的编号

### 根因

旧规则的设计语境是"防止无上下文的 ok 被误解"。但红线 #10 本身已经建立了上下文（💡 明确存在于每个暂停点），ok 不是孤立语句而是对 💡 的引用。旧禁令属于在过强约束下二次保险，代价是日常交互摩擦。

### 优化方案

约定 **ok = 按 💡 建议**：

1. **识别清单**：`ok` / `OK` / `Ok` / `好` / `可以` / `行` / `嗯` / `按建议` / `按推荐`
2. **映射规则**：
   - 单决策点：等价于回复 💡 对应选项编号（`💡 在 A` → `ok ≈ 1A`）
   - 多决策点：等价于所有决策点都选 💡（`ok ≈ 1A 2A 3A`）
3. **前置条件**：当前暂停点至少有 1 个 💡（红线 #10 本就强制，事实上总是满足）
4. **PMO 强制 cite**：处理时输出一行『✅ 已按 💡 建议处理：{决策 1}→{选项}{，决策 2}→{选项}…』作为审计痕迹
5. **边界保留**（不适用 ok 约定）：
   - 破坏性操作（force push / drop 表 / 删分支）—— 本就是强制保留暂停点，ok 不可替代
   - 无 💡 的暂停点（罕见，违反红线 #10）—— 退回到原复述+二次确认路径
   - ok 后紧跟非空白字符（"ok 但先看下 X"）—— 按完整语句解析，不走本约定

### 收益

- **交互摩擦降低**：最常见的"采纳推荐"从 `1A 2A`（5 字符）→ `ok`（2 字符），命令式对话更自然
- **规范语义自洽**：红线 #10（暂停点必须给 💡）与 ok 约定形成闭环，💡 升级为"可直接引用的决策编号"而不是空泛的"参考建议"
- **审计不丢失**：PMO 强制 cite 一行『✅ 已按 💡 建议处理：…』确保用户立刻看到 ok 被如何解读，防止误解
- **破坏性兜底保留**：强制保留暂停点（见 flow-transitions.md）+ ok+补充语句 + 无 💡 暂停点 三条边界保持原约束

### 与 P0-17 的关系

| 编号 | 主题 | 简化方向 | 共同脉络 |
|------|------|----------|----------|
| P0-17 | INIT.md Step 1.2 版本缓存 | 每次硬校验 → 版本命中时跳过 | 去除多余技术开销 |
| P0-18 | ok = 按 💡 建议 | 每次复述+二次确认 → 有 💡 则直接按推荐 | 去除多余人机摩擦 |

P0-17 针对框架自身的 token 成本，P0-18 针对人机交互的字符成本，同为"成本只在真正需要时付出"哲学在不同层面的实例。

### 优先级

P0（用户反馈，交互体验优化，非破坏性向前兼容）
