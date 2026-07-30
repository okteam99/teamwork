# Scripts Policy — teamwork 可执行脚本统一规范

> 🔴 **单源原则**：teamwork 所有可执行脚本（业务逻辑层）统一 **python3**。
> bash 仅留宿主级 hook 薄壳（如 CC `settings.json` 的 `SessionStart` / `PreCompact` 等），且**不承载业务逻辑**。

---

## 1. 为什么 python > bash

| 维度 | python3 | bash |
|---|---|---|
| 跨宿主可执行 | ✅ CC / Codex / Gemini 任一宿主显式调用 | ❌ 仅 CC `hooks.json` 自动触发 |
| 可验证 | ✅ stdout JSON + exit_code → R7 evidence-binding 入 state.json | ❌ stderr/echo 静默，无审计 |
| 失败可见 | ✅ 非零退出 → AI 必须处理 | ❌ echo warn 继续，无人看 |
| 测试覆盖 | ✅ `tools/tests/test_*.py` pytest 强制 | ❌ 无回归保护 |
| spec 体系 | ✅ 与 state.py / bootstrap.py 同型 | ❌ 引入 hook 间接层 |
| 依赖底线 | python3（teamwork 已强依赖） | + bash + 宿主 hook 框架 |

**核心结论**：python3 已是 teamwork L3 物化层既定底线（state.py / bootstrap.py / verify-panorama.py 全部 python）。再叠加 bash 业务脚本 = 给单宿主加优化、给跨宿主加债。

---

## 2. 规则

### R-SP-1 业务脚本一律 python3

新增任何可执行脚本（**有业务逻辑** · 非纯宿主 lifecycle 转发）：

- ✅ 必须写在 `tools/*.py`
- ✅ 必须 `#!/usr/bin/env python3` + `chmod +x`
- ✅ 必须有对应 `tools/tests/test_*.py`（pytest · ≥3 case：happy / edge / failure）
- ❌ 不得新增任何宿主 hooks（🔴 v8.213 hooks 已全退役 · hooks/ 目录已删 · bootstrap 只做历史清理）
- ❌ 不得在 hook .sh 之外的 bash 文件里写业务流程

### R-SP-1b 测试效率:优化派生,不是砍用例(v8.299)

🔴 **默认一 test 一断言簇 · 不为省时间合并** —— 测试的主要价值是**失败定位**;
合并把「哪条坏了」变成「有东西坏了」,而这恰恰是出事时最贵的信息。

**优化前先测,别凭印象**。本套件实测(1015 条 / 58s):

| | 条数 | 占比 | 耗时占比 |
|---|---|---|---|
| < 5ms | 623 | **61.4%** | **0.00s** |
| 最慢 50 | 50 | 4.9% | 51.4% |

**61% 的用例本来就免费,合并它们省不到一秒**。成本集中在**进程派生**(起 `state.py` 子进程、
`git init` 建仓),不在用例数量。

**判据与手段**:
1. **只优化 > 50ms 的用例**(占 29% 条数、96% 时间)· < 5ms 的一律不动。
2. **手段是共享 setup,不是合并断言** —— 昂贵的是 setup 不是断言。
   ✅ `setUpClass` 建一次基线仓 + 每例 `copytree`(**保住隔离与失败定位**)
   ❌ 把多个断言塞进一个 test 方法(省不到时间 · 丢定位)
3. **能 import 直调的别起子进程** —— CLI 契约用 1~2 条端到端用例覆盖即可,其余走函数级。
4. **并行优先于任何改造**:`tools/run-tests.sh` 实测 58s → 19.3s(3×)· 零测试改动 · 零定位损失。

🟢 **本条是「手段规定」**(v8.283 分类学里会衰减的那类),故**只写规范不配机器门** ——
判据在这里,守不守看当时值不值。

### R-SP-1c 不在门禁的适用阶段之前跑它(v8.301)

🔴 **注定失败的调用比不调用更糟** —— 它逼调用方把 FAIL 自我解释成「预期的」,
而**「预期的 FAIL」一旦被正常化,真 FAIL 就会被同样对待**。门禁的价值全在「红了就是有事」。

判据两条:
1. **跑之前先问「这个门管的产物,现在存在吗」** —— 不存在 = 还没到它的阶段,别跑。
2. **想验的东西可能已经有门在管** —— 先查该 stage 的 `evidence_checks`,别手跑一个更宽的脚本来验更窄的东西。

**工具侧的义务**:被跑在错误时点时,**给路由信息而不是裸失败** ——
说清「谁在什么时候跑我」「你想验的东西归谁管」。裸失败只留下一个要被解释掉的红。

> why(实证 SVC-CORE-F260728):AI 在 goal 阶段手跑 `verify-ac.py`,必然 FAIL(TC.md 是 blueprint 产物),
> 只能自辩「预期的」。而它想验的「AC 机读块本身」**早已由 goal-complete 的 `prd_template_conformance` 校验** ——
> 净结果是一个注定的红 + 一句自辩 + 零信息。
> 诱导源是 `templates/prd.md` 机读块头的一句「verify-ac + goal-complete 解析此块」——
> 陈述属实,但摆在 goal 阶段的 PRD 里就读成了「去跑 verify-ac 验一下」。**属实的话摆错位置也会误导。**

### R-SP-2 调用一律 spec 显式 cite

所有 python 工具调用必须在对应 stage spec 里 **显式 cite**，不依赖宿主 hook 自动触发：

```markdown
📌 **AC 覆盖校验**（脚本物理拦截 · 不靠 PMO 自觉）：

```bash
python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}
```
```

理由：
- spec cite + state.json evidence-binding = 跨宿主一致的物理拦截
- 宿主 hook 自动触发 = CC-only · Codex/Gemini 永远漂移

### R-SP-3（已废）hook 薄壳规范

hooks 已全退役 · `hooks/` 目录已删 · bootstrap 只做存量项目的历史清理。若未来重新引入宿主 hook:薄壳只做「调 python」转发 · 禁业务逻辑(历史判据 · 详 git 历史)。

### R-SP-4 输出 JSON

所有 python 工具 stdout **必须 JSON**（参考 state.py 格式）：

```json
{
 "verdict": "OK" | "WARN" | "FAIL" | "BLOCKED",
 "action": "...",
 "...": "..."
}
```

理由：
- AI 能机器解析 + 引用具体字段
- state.json evidence-binding 直接存 stdout
- 跨宿主一致

### R-SP-5 退出码契约

| exit | 含义 | AI 处理 |
|---|---|---|
| 0 | PASS · 正常 | 继续 |
| 1 | WARN · 非阻断（如派生视图刷新失败、提醒缺失） | 记录入 state.json · 继续 |
| 2 | FAIL / BLOCKED · 阻断（state.json 不一致 / 真值损坏 / 参数非法） | ⏸️ PMO 暂停 · 用户介入 |

### R-SP-6 ~ R-SP-7（v8 已废弃）

> v7 的 `render-status-line.py` / `render-afk-skip.py` / `render-flow-transition.py` / `render-decision-pause.py` 工具及关联的 feature_context auto-fill 机制,在 v8 中被 `state.py` 各命令的自 emit 行为(状态行 + JSON brief + 暂停点 markdown)取代,本节原内容已删除。

### R-SP-8 每条「🔴/必须」规则必须含「下游消费者」标注

> 🚨 **实战触发**：API-F048-Ollama 代理网关 case · 4.6 instance 自承"我跳的步骤都没有下游消费者标注"——只写"🔴 必须"但没说"跳了谁会发现 / 哪个下游会失败"· AI 内部评估为"只是仪式"而跳掉。
>
> 4.6 原话：「我跳"写了没人读"的步骤 · 不跳"下游有人依赖"的步骤」。

#### 核心规则

```
🔴 spec 中每条「🔴/必须/必填/必读/禁止/不得/强制」级规则
 = MUST 同段内含「下游消费者」标注：跳了之后谁/哪个下游会发现 / 失败 / 拒绝。

❌ writer-only 反模式（命中 → P0-146 候选修复）：
 "🔴 必须创建 state.json" ← 没写跳了谁会坏
 "🔴 PRD-REVIEW.md 必需" ← 同上
 "🔴 角色切换必须 cite" ← 同上

✅ 含消费者推荐写法：
 "🔴 创建 state.json — Blueprint 入口 enter-stage 校验前置 gate · 缺则 exit 1"
 "🔴 写 PRD-REVIEW.md — Blueprint QA 读此文件确认评审覆盖 · 缺则 QA 重审整 PRD"
 "🔴 cite 关键要点 — 不 cite 评审退化为自我对话（实证 API-F048 case · 4.6 自承）"
```

#### 下游消费者标志的有效形式

```
1. 工具校验失败：
 - "exit 1 / exit 2 / BLOCKED / verify fail"
 - "state.py XXX 子命令 reject"
 - "state.py emit 内 cite spec hint"

2. 下游 Stage 拒绝：
 - "Blueprint 入口 gate 校验"
 - "QA 重审整 PRD"
 - "架构师 CR 打回"

3. 用户可见后果：
 - "用户无法验证 PMO 是否跑过"
 - "实证 case PTR-F001-BUG-013 / ADMIN-F012 / API-F048"

4. 状态损坏 / 漂移：
 - "state.json 与 PRD 分裂"
 - "评审退化为自我对话"
 - "ROADMAP 派生值漂移"
```

#### 物化扫描

`python3 tools/scan-spec-consumer.py --limit 30`(`--output-format markdown` / `--limit 0` 全量)—— 输出缺「下游消费者」标注的 🔴 规则候选清单(按 file:line)· 非强制门 · 修复按候选清单渐进推进。

---

## 3. 已存在的 python 工具（参考样板）

| 工具 | 职责 | 模式 |
|---|---|---|
| `tools/state.py` | state.json schema/状态机/evidence-binding 单源 | 子命令 + JSON 输出 |
| `tools/bootstrap.py` | session bootstrap · 骨架维护 + 历史 hooks/注入段清理 | 一次性 boot · JSON 输出 |
| `tools/verify-panorama.py` | 全景设计物化校验 | 校验 + JSON 输出 |
| `tools/run_tests.py` | 框架自身测试套件分片并行 runner | 自学装箱 · 耗时写回 |

---

## 4. 迁移路径（已完结）

bash → python 迁移已完结:`hooks/` 目录整体退役删除(职责由 state.py 各命令 emit + bootstrap 历史清理取代)· 无遗留存量。

---

## 5. 反模式黑名单

❌ 新增 `hooks/post-X.sh` 写业务（绕过本 policy 的隐蔽路径）
❌ python 工具 stdout 非 JSON（破坏 R-SP-4）
❌ 业务流程在 bash hook 里直接写(hook 只做事件转发 · 业务逻辑走 python)
❌ spec 不 cite 工具调用 · 仅靠宿主 hook 自动触发（破坏 R-SP-2 · CC-only 陷阱）
❌ python 工具无对应 test_*.py（破坏 R-SP-1 · 无回归保护）

---

## 6. 与红线层级关系

- 本规范属 **L2 standards 层**（按需 read）
- L1 红线不新增条目（路径 B · 不走路径 C）
- L3 物化层 = `tools/*.py` + `tools/tests/test_*.py`
- 触发：新增脚本时必读 · PMO 起 P0 patch 涉及 hooks/ 或 tools/ 时必读
