# Blueprint Stage

---

## 怎么做

### 1. 加载上下文
读 PRD.md(权威需求)· ARCHITECTURE.md(系统架构)· KNOWLEDGE.md(项目踩坑/事实)· standards/tdd.md。
🔴 **`project-specs/DEV-RULES.md` 存在 → 必读**(本项目**强制开发规范** · 人维护:API 契约 / 错误处理 / 其他约定 · v8.257 三项制)· TECH 方案**须遵守**;冲突要么改方案、要么在 TECH 显式记原因。不存在 → skip(人维护 doc · 可能未建 · 不硬 FAIL)。

⚡ **§2 与 §3 起草相互独立 → 并行同发**(v8.256 · TC 锚 PRD.AC · TECH 锚设计方案 · subagent 各一)· 完成后互查一致(`tests[].covers_ac` ↔ TECH §测试策略)。

### 2. QA 起草 TC.md
BDD Given/When/Then · frontmatter `tests: [{id, covers_ac, description}]` · 每 AC 至少 1 test

### 3. RD 起草 TECH.md
**§现状基线**(🔴 grounded 真实代码 · 不靠假设)· §模块划分 · §数据模型 · §接口定义 · **§错误处理/异常路径**(失败语义 + 每条 WARN/ERROR 日志 · 不静默吞)· **§依赖与影响**(改契约必列消费方 · grep 不凭记忆)· **§查询性能**(涉 SQL · 分析并给理由)· §TDD 计划含 **§测试策略**(单元/集成/契约 · 哪里要真实 DB/BFF)· **§风险** · 复杂度评估含**简洁性自查**(RD 主动自证 · 防过度设计)。
🔴 §数据模型 必明确标注:本方案**是否涉及数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration)· 涉及 → 触发 §7.5 用户确认暂停点(🛡️ TECH 兜底清单非空同触发 · v8.265)。🔴 **变更最小化先问**(v8.255 · 设计时前移 · 不是确认时补):每个新表/新列过四问(复用既有表列 / 应用层计算 / 不入库 / 并入 JSONB 扩展列)· 全否才入变更表 · 每项带「解决什么问题 + 为何非更简方案不可」(templates/tech.md §变更表清单)—— DB 变更数是简洁性 counter-lens 的重点审查对象。

### 4. Architect Tech Review → TECH-REVIEW.md
frontmatter `reviewers: <state.stage_review_roles.blueprint 全体角色>` + `verdict` · 隔离 subagent 冷审(与 goal 冷审教义一致 · 不喂主对话起草心路;需要 ADR / KNOWLEDGE 背景 → 派发 prompt 附文件路径让其自读)
🔴 frontmatter 字段名是 `reviewers`(复数列表)· 必含 `state.stage_review_roles[blueprint]` 全部角色(reviewers_match evidence 校验)
🔴 **Tech Review 是拦过度设计的最佳时机(改 TECH 比改代码便宜)**:Architect 必过**简洁性 counter-lens** —— 「方案是否过度设计(YAGNI)· 能否更简单达成业务目标 · 每个组件职责是否最小且归对层(该透明的别解析 / 该下沉的别上提)· 🛡️ **兜底按 ROI 审**(降级/安全兜底逐项算 概率×后果 vs 成本 · ROI 不立的删 · 立的必在 §7.5 透出——两个方向都要实证)」。external finding 别盲采:天然偏「加校验」· 每条对照业务目标 + 简洁性取舍(详 `roles/architect.md` Telos)。

### 5. (可选)QA 独立 TC Review
v8.244 默认 QA 并入 §6 外审覆盖方向「可测试」· 复杂 Feature(测试面大)`change-review-roles` 加回时独立启用

### 6. 第三视角冷审(external cross-review · roster 条件式 · v8.244 默认 roster = `[architect, external]`)
按 `state.stage_review_roles.blueprint` roster + localconfig 三层分支(与 §4 Architect 主审 ⚡ 并行同发 · 互不喂对方产出 · 🎭 两路模型错开〔v8.268〕):
- ① **roster 含 external 且 `.teamwork_localconfig.json` 的 `disable_external_review` 显式 `false`(opt-in 异质)** → 跑 `state.py external-review --feature <path> --stage blueprint`(host/model/profile 全自动)· 落 `external-cross-review/blueprint-<model>.md`
- ② **默认(缺省 / `true`)** → **错开模型** subagent 隔离冷审降级承担第三视角(≠主会话模型(如 fable5 会话 → 外审 opus) · v8.268)(产物仍落 `external-cross-review/*.md` · frontmatter 带 `review_via: subagent`)
- ③ **roster 无 external** → 整段 skip(机器校验自动过)

🔴 **外审内容契约(覆盖方向制 · v8.244)**:必覆盖 **可测试**(TC 质量 / 测试策略 —— QA 视角并入 · AC↔TC 机械绑定归 verify-ac)· **方案盲区**(依赖 / 影响面 / 迁移风险)+ 🔴 **AI 自主方向 ≥1**(候选:数据一致性 / 迁移风险 / 性能 / 安全边界 · 按 feature 挑或自造)· 每方向给 finding 或「查过无发现」· 产物 frontmatter 记 `coverage: [...]`(物化门 `cross_review_coverage`)。

详 [standards/external-model-usage.md §十一](../standards/external-model-usage.md)。

### 7. PM 回应 + 修订循环
NEEDS_REVISION 时主对话内闭环 · 不打扰用户

### 7.5 ⏸️ 方案要素确认(条件暂停点 · R5 · DB 变更 / 兜底策略 · v8.265 双触发)
🔴 **触发条件(任一命中即停)**:① TECH 方案涉及**数据库数据结构变更**(新建/删除/修改 表、字段、索引、约束、migration);② TECH **🛡️ 兜底清单非空**(含任何安全兜底/降级兜底 —— ROI 账 + 拍板权都给用户 · 不许默默做)。
blueprint-complete 前 **必 emit R5 标准 1/2/3 暂停点 · 等用户拍板**(两类都命中则一次给全 · 都未命中跳过直接 §8):

🔴 **`auto_mode=true` 时跳过此暂停点** —— auto 用户已显式委托 AI 完成技术决策 · 但 PMO 必 `state.py add-concern --severity WARN --message "auto skip: 方案要素确认 · DB: .../兜底: ..."` 留 audit(详 [SKILL.md § auto_mode=true 时各暂停点行为](../SKILL.md))。

```markdown
⏸️ TECH 方案要素确认(DB 变更 / 兜底策略 · 命中项如下)· 请确认:

**变更点明细**(🔴 必给 · 对象级每条一行 —— 分类概括 / 文件指针不算变更点 · 列与 TECH §变更表清单同构):
| 对象 | 变更 | 解决什么问题 | 为何非更简方案不可 | 破坏性 |
|---|---|---|---|---|
| <表名> | <新增字段 a/b · partial unique index〔条件〕· 新表〔核心列〕· 删/改…> | <没有它哪个 AC/场景会坏> | <否掉的最近更简方案 + 否的理由(四问已过)> | <否 · expand-only / 是:何损> |

**关键迁移策略**(有则必列 · ≤6 行):有损与否 / 唯一约束前历史数据冲突预检 / 历史回填口径 / down migration / 清理周期 / 特殊设计一句话。

**🛡️ 兜底清单**(TECH 含安全/降级兜底时必给 · 无兜底则本块省略 · 照抄 TECH §兜底清单):
| 兜底 | 保护什么失败场景 | 概率×后果 | ROI 结论(vs 实现维护成本) |
|---|---|---|---|
| <重试 N 次 / 降级路径 / 防御层…> | <什么坏了它兜> | <真实概率 × 代价> | <ROI 立得住的账 —— 算不出正账的本不该做> |

1. **确认 DB schema 变更方案 · 进入 dev** 💡 推荐
   理由:表结构改动经评审 · 你认可即进开发
   动作:blueprint-complete → 自动转 dev
2. **调整 DB 方案** — 你对表结构/字段/迁移设计有异议 · RD 修订 TECH §数据模型
3. **其他指示**

📚 决策参考:TECH.md §数据模型(完整字段与迁移顺序 · 指针只作深读补充 · 🔴 不替代上面的明细)
```

🔴 **变更点明细是本暂停点的正文 · 不是可选附件**(v8.242 实证 case:只给「增加诊断投影与快照序号」类分类概括 + 指针 → 用户被迫追问「DB 变更方案是什么」—— 追问一次 = 暂停点白 emit 一轮)。

DB 变更与兜底清单**都未命中** → 跳过此步 · 直接 §8。

### 8. complete
`state.py blueprint-complete ...` · verify-ac.py 自动跑 · external-review artifact 校验

---

## 质量基线

📎 **物化拦截**:`verify-ac.py`(每 AC ↔ TC.md `tests[].covers_ac`) · P0-154(`external-cross-review/*.md` 非空 · roster-gated · v8.204 后默认降级 subagent 冷审)

**SOP**(违反 → review NEEDS_REVISION):
- TECH.md 写"方案"(选型 / 接口 / 数据结构)· 不写函数实现 · 代码细节归 dev stage
- Architect 评审走**隔离 subagent 冷审**(与 goal 冷审教义一致 · 不喂主对话起草心路)· 需要 ADR / KNOWLEDGE 背景 → 派发 prompt 附文件路径让其自读(白板效应恰是要的独立性)
- NEEDS_REVISION 主对话内 PM 闭环修订 · 不打扰用户(R5 + fix-retry 规范)

---

## Output Contract(产物形态参考)

> 📋 **起草模板**(避免找历史 Feature 抄):
> - TC.md → `{SKILL_ROOT}/templates/tc.md`(含 frontmatter + tests[].covers_ac BDD 示例)
> - TECH.md → `{SKILL_ROOT}/templates/tech.md`(结构:复杂度+简洁性自查 · **现状基线**〔grounded 真实代码〕· 技术方案〔架构/数据结构/接口/**错误处理+日志**/**依赖与影响**〕· 实现思路〔改动文件/DB变更/**查询性能**/前端〕· TDD计划〔**测试策略层次**/步骤〕· **风险** · 待决策 · **完工自查**〔RD 实现完逐项打钩〕)
> - TECH-REVIEW.md → 无独立模板 · 见下方 schema · 按评审角色 finding 分段
> - external-cross-review/*.md → 跑 `state.py external-review --feature ... --stage blueprint`(自动落产物 · 不要手写)
>
> 🤖 **校验脚本**:`python3 {SKILL_ROOT}/templates/verify-ac.py {Feature 目录}` ·
> blueprint-complete 自动跑 · 校验 PRD 每条 AC 在 TC.md `tests[].covers_ac` 至少 1 个引用 · 漏覆盖 FAIL。

### `TC.md`
frontmatter `tests: [...]` · AC↔Test 一一绑定 · BDD Given/When/Then

### `TECH.md`
§模块 / §数据 / §接口 / §依赖 / §风险

### `TECH-REVIEW.md`
frontmatter `reviewers`(复数列表 · 含 blueprint 全部评审角色)+ `verdict` · 三视角 finding 汇总

### `external-cross-review/*.md`
第三视角冷审产物按 roster(含 external 时 · 默认错开模型 subagent 冷审 · v8.268)

---

## 相关

- 引擎:[../tools/_v8_engine.py](../tools/_v8_engine.py)
- spec:[../tools/_v8_stage_specs.py](../tools/_v8_stage_specs.py) `BLUEPRINT_SPEC`
- 入口规范:[../SKILL.md § Triage 入口规范](../SKILL.md)
