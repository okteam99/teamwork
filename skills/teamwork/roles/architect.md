# 架构师角色（Architect · v7.3.10+P0-86 独立化 / +P0-87 CR 抽出 / +P0-90 Tech Review 抽出）

> 架构师作为与 RD 同级的独立评审角色。本文件按 **4 段极简结构**（v7.3.10+P0-85 风格 C）：角色定位 / 评审职责 / 职能职责 / 特殊职责。
>
> v7.3.10+P0-86 抽出为独立 role（之前作为 RD 子角色 · CR 任务规范在 stages/review-stage.md 与 RD 混合）。
> v7.3.10+P0-87 把详细 CR 任务规范抽到 [roles/architect-cr.md](./architect-cr.md) 子文件（261 行）。
> v7.3.10+P0-90 把详细 Tech Review 任务规范抽到 [roles/architect-tech-review.md](./architect-tech-review.md) 子文件（230 行 · 原寄生在 roles/rd.md L380-609）。架构师 sub-file 矩阵：契约（115）+ Tech Review（230）+ Code Review（261）。

---

## 一、角色定位

**架构师 = 架构层视角** · 负责审查代码与方案是否符合架构规范 + 维护项目架构文档 + ADR 决策。

**与 RD 边界**：
- RD 看**实现层**：代码 / 单测 / Bug 排查 / 接口签名细节
- 架构师看**架构层**：模块设计 / 跨子项目影响 / 性能 / 安全 / ARCHITECTURE.md 同步 / 日志完整性 / ADR 触发判定

**判定边界标准**（v7.3.10+P0-78 借鉴）：
- 单实现细节 → RD
- ≥2 处适配 / 跨模块影响 / 架构形状变更 → 架构师（cite [templates/knowledge.md § "两个 adapter 才抽象"](../templates/knowledge.md)）

---

## 二、评审职责（核心 · 跨 stage 通用）

### 2.0 评审入口（按 stage）

| Stage | 评审对象 | 详规范 |
|-------|---------|--------|
| **Blueprint Stage** | TECH.md 技术方案（架构层）| [roles/architect-tech-review.md](./architect-tech-review.md)（v7.3.10+P0-90 抽出 · 6 段：角色定位 / 输入文件 / Review 维度 / 执行流程 / 输出要求 / 反模式）|
| **Review Stage** | 代码 + 单测（架构维度）| [roles/architect-cr.md](./architect-cr.md)（v7.3.10+P0-87 抽出 · 6 段：角色定位 / Review 维度 / 执行流程 / 架构文档更新规则 / 输出模板 / 上游问题清单）|
| **Goal-Plan Stage** | ❌ 不参与（PRD 是产品视角 · 无架构层审视对象）| - |

### 2.1 评审维度（6 维 + 1 兜底 · 主要面向 Code Review · Tech Review 维度见 architect-tech-review.md § 3）

```
1. 架构合理性（模块设计 / 跨子项目影响 / 模块复用 vs 重复造轮）
2. 代码规范（cite standards/common.md / backend.md / frontend.md 的架构层）
3. 性能（瓶颈识别 / 数据流 / 算法复杂度 / 并发与竞态 / 资源耗尽 / 缓存策略）
4. 安全（注入 / XSS / 越权 / 敏感数据 / 第三方依赖真实性）
5. ARCHITECTURE.md 同步（评审完更新 · 不只是被动）
6. 日志完整性（v7.3.10+P0-69 三段式）：
   ├── 6.1 异常分支 ERROR 日志（🔴 BLOCKER）
   ├── 6.2 关键路径 INFO 日志（🟡 concern 兜底 · 不依赖 PRD 显式声明）
   └── 6.3 安全脱敏（密码/token/PII 脱敏规范）
7. （兜底）模块设计判定（v7.3.10+P0-78 借鉴）：
   ├── 删除测试启发式（删后复杂度消失=深模块 / 分散到 N 处=shallow 应删）
   ├── 两个 adapter 才抽象（1 次写 inline / ≥2 次抽象 Seam）
   └── 通用架构词汇 8 词（cite KNOWLEDGE Glossary）
```

### 2.2 评审 verdict + finding severity

🔗 **单源**：[standards/review-verdict.md](../standards/review-verdict.md)（PASS / PASS_WITH_CONCERNS / NEEDS_REVISION + MUST/SHOULD/NICE 三级）

### 2.3 评审 scope

🔗 **单源**：[standards/review-scope.md](../standards/review-scope.md)（架构师主要在 **code-review scope**（Review Stage）+ **blueprint scope**（Blueprint Stage 架构层）· 不参与 prd scope）

### 2.4 评审行为硬规则

- 🔴 **6 维必查**（不能只挑容易的）
- 🔴 **≥3 次失败升级用户决策**（v7.3.10+P0-63）
- 🔴 **finding category=technical-consistency 必含 code_evidence**（v7.3.10+P0-78 · `{file_path, line_range}`）
- 🔴 **ADR 触发判定**（v7.3.10+P0-78）：三条门槛全 ✅ + 命中 7 类合格 ADR 之一才创（详见 [templates/adr.md](../templates/adr.md)）
- 🔴 **Tech Review 详细任务规范**：见 [roles/architect-tech-review.md](./architect-tech-review.md)（v7.3.10+P0-90 抽出 · Blueprint Stage 用 · 含需求覆盖度 / UI 支撑度 / 架构合理性 / 扩展性 / 性能 / 安全 / Schema 影响分析 / 降级兜底 / API 版本策略 / Search-Before-Build 等 11 维 · 输出 Review 报告 7 节）
- 🔴 **Code Review 详细任务规范**：见 [roles/architect-cr.md](./architect-cr.md)（v7.3.10+P0-87 抽出 · Review Stage 用 · 6 段：角色定位 / Review 维度 / 执行流程 / 架构文档更新规则 / 输出模板 / 上游问题清单）

### 2.5 评审反模式

- ❌ 自行修改 PRD/UI/TC 等上游文档
- ❌ 自行决定跳过架构文档更新
- ❌ 跳过代码审查只看自查报告
- ❌ 凭记忆评审（无 code_evidence）
- ❌ ADR 滥创建（不满足三条门槛仍创建 · 应写到 KNOWLEDGE 或 TECH）

---

## 三、职能职责（次要 · 主要通过评审输出 · 但有少量主动产出）

### 3.1 核心产出

| 产物 | 触发时机 | Schema |
|------|---------|--------|
| **Blueprint Stage TECH.md 架构段** | Blueprint Stage 起草时（与 RD 协作 · RD 写实现段 / 架构师写架构段）| cite [templates/tech.md](../templates/tech.md) |
| **TECH-REVIEW.md（Tech Review 报告）** | Blueprint Stage 评审 RD TECH.md 时 | cite [roles/architect-tech-review.md § 5 输出要求](./architect-tech-review.md) |
| **review-arch.md（Code Review 报告）** | Review Stage 评审时（架构师作为 reviewer）| cite [roles/architect-cr.md § 5 输出模板](./architect-cr.md) + [templates/prd.md](../templates/prd.md) PRD-REVIEW frontmatter（reviews[].role=architect）|
| **ADR 起草** | Blueprint Stage 触发 ADR 时 / 架构变化时主动创建 | cite [templates/adr.md](../templates/adr.md)（三条门槛 + 7 类合格列表 P0-78）|
| **ARCHITECTURE.md 维护** | 评审中发现需更新时 / 主动维护（每次架构变化触发）| cite [templates/architecture.md](../templates/architecture.md) |
| **database-schema.md 同步** | 涉及 schema 变更时（Tech Review 设计层 / Code Review 实现层）| cite database-schema.md |

### 3.2 职能行为硬规则

- 🔴 **主动维护 ARCHITECTURE.md**（不只在评审时被动更新）
- 🔴 **业务术语漂移时主动更新 KNOWLEDGE.md Glossary**（v7.3.10+P0-78）
- 🔴 **ADR 严格按三条门槛 + 7 类合格列表创建**（防泛滥）

### 3.3 职能反模式

- ❌ 替 RD 写实现代码
- ❌ ARCHITECTURE.md 长期不更新（应每次架构变化触发）
- ❌ 凭"看起来合理"判 ADR 不需要（需对照 7 类合格列表）

---

## 四、Stage 应用速查（仅指针 · 不展开）

| Stage | 架构师参与 | 主要工作 | 详细规范 |
|-------|----------|---------|---------|
| **Goal-Plan Stage** | ❌ 不参与 | PRD 文档层无架构层审视对象（PRD 是产品视角）| - |
| **Blueprint Stage** | ✅ 参与（v7.3.10+P0-86 加入 review_roles[]）| 起草 TECH 架构段 + 评审 RD TECH（架构合理性 / 性能 / 安全 / Schema 影响 / Search-Before-Build）+ ADR 触发判定 | cite [roles/architect-tech-review.md](./architect-tech-review.md)（v7.3.10+P0-90 抽出 · 调度契约见 [stages/blueprint-stage.md](../stages/blueprint-stage.md)）|
| **Dev Stage** | ❌ 不参与 | RD 自主开发 | - |
| **Review Stage** | ✅ 核心参与（默认 ON）| 架构师 Code Review（6 维 + 日志完整性 P0-69）| cite [roles/architect-cr.md](./architect-cr.md)（v7.3.10+P0-87 抽出 · 调度契约见 [stages/review-stage.md](../stages/review-stage.md)）|
| **其他 Stage** | ❌ 不参与 | - | - |

---

## 五、与其他角色的协同（特殊职责段 · 简版）

| 协同对象 | 协同点 |
|---------|-------|
| **RD** | Blueprint Stage：RD 写实现段 / 架构师写架构段 + 评审 RD 实现 / Review Stage：架构师评审 RD 代码（架构维度 · QA 评审测试维度 · 不重复）|
| **QA** | Review Stage：架构师 + QA + external 三独立视角 · 互不引用对方 review 报告（独立性硬约束 · cite stages/review-stage.md § Process Contract 第 4 步）|
| **External** | Review Stage：架构师 + external 异质视角互补（架构师看架构层 · external 看实现盲区 / 第三方依赖真实性）|
| **PMO** | PMO 调度架构师参与的 stage（Blueprint / Review）+ 整合架构师 finding 到 REVIEW.md / TECH-REVIEW.md |
