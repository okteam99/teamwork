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

### 待下轮执行

1. **STATUS-LINE.md 阶段对照表更新**
   - 当前表还是旧阶段名（Dev Stage / Verify Stage 已更新，但整体结构需适配 8 stage）
   - 需要新增 Plan Stage / Blueprint Stage / Panorama Design Stage / Review Stage / Test Stage 的状态行显示

2. **ui-design-stage.md 内容重写**
   - 当前还是从旧 agents/ui-design.md 复制的原始内容（包含全景维护规则等已拆出的内容）
   - 需要按新 stage 格式重写（只做 Feature UI，不动全景）

3. **旧引用清理**
   - 散落在 RULES.md / FLOWS.md / REVIEWS.md 等文件中的旧阶段名、旧路径
   - grep "PL-PM Teams 讨论" / "TC 技术评审" / "架构师方案评审" 等旧的主对话阶段名 → 更新为对应 stage 名

4. **agents/README.md 速查表完整更新**
   - 速查表需要反映 8 stage 结构（部分已更新，需完整检查）

5. **INIT.md CLAUDE.md 模板更新**
   - 模板中的流程描述需要适配 8 stage

6. **templates/status.md 更新**
   - 阶段合法值列表需要适配 8 stage

7. **敏捷需求流程的 RULES.md 流转链更新**
   - 当前敏捷流转链还有旧内容，需要适配新 stage 结构
