# 命名规范 · v8.1

> 编号 ID 的格式 / namespace / 升级映射规则。
> 各 stage spec / state.py / templates / TRIAGE.md 一律 cite 本文件。

---

## 1. Feature ID

```
格式: {项目缩写}-F{NNN}-{Kebab-Case-名称}
示例: PTR-F033-Credit-Note-Adjustment
      SVC-PLATFORM-F043-Adapter-MobPower
```

- **项目缩写**:来自 teamwork-space.md(多项目)或 config.md(单项目)的项目缩写字段
- **F-NNN**:三位数字 · **各项目独立递增**(PTR-F033 与 SVC-PLATFORM-F033 可并存 · 不跨项目共享 namespace)
- **名称**:多词用 `-` 拼接 · 不超过 6 词
- **Feature 目录**:`{docs_root}/features/{Feature ID}/`(完整 ID · 不省略名称)

state.py 校验:basename(--feature) 必须包含 --feature-id(防 slug 错位)。

## 2. Bug ID

```
格式: BUG-{项目缩写}-F{NNN}-{seq}
示例: BUG-PTR-F033-001
```

- **F-NNN**:关联的 Feature 编号(独立 Bug 不关联 Feature 用 F000)
- **seq**:三位数字 · **单 Feature 内独立递增**
- **位置**:`{Feature 目录}/bugfix/BUG-...md`

## 3. ADR ID

```
格式: ADR-{NNNN}
示例: ADR-0001
```

- **NNNN**:四位数字 · **全局递增 · 不区分项目**(架构决策跨项目可见 / 单源)
- **位置**:`{项目根}/docs/adr/ADR-NNNN-{topic}.md`
- **superseded 时双向链接**:原 ADR.status=superseded-by-NNNN + 新 ADR.supersedes=NNNN
- 详见 [templates/adr-index.md](../templates/adr-index.md)

## 4. BL ↔ F 映射(规划期 → 执行期)

```
规划期: BL-{NNN}(Roadmap Backlog 编号 · 在 planning stage 分配)
执行期: F-{NNN}(进入 Feature 流程后由 PMO 在 init-feature 时分配)
映射:   各自独立递增 · 通过 ROADMAP 「对应 F编号」列建链接
```

- **BL-NNN**:三位数字 · **各项目独立递增**(同 F-NNN)
- **BL → F 升级时机**:用户拍板某 Backlog 启动 Feature 流程时,PMO 分配下一个 F-NNN(各项目当时 sequence 的下一个)+ 同步回填 ROADMAP「对应 F编号」列
- **不强制同号**:BL-007 启动 Feature 时分配的 F 编号是 F 序列当时的下一位 · 与 BL 数字无关

## 5. Dispatch 文件 ID

```
格式: {NNN}-{subagent-id}.md
示例: 001-rd-developer.md
      002-arch-cr.md
      003-qa-cr.md
```

- **NNN**:三位数字 · **单 Feature 的 dispatch_log/ 目录内独立递增**
- **subagent-id**:来自 stages/*.md § 角色任务规范 中的标签
- 由 state.py 各 stage-start 自动生成 · PMO 不手填

## 6. KNOWLEDGE 子 ID

| 类 | 格式 | 范围 |
|---|---|---|
| Gotcha | `GO-NNN` | 项目内独立递增 |
| Convention | `CV-NNN` | 项目内独立递增 |
| Preference | `PR-NNN` | 项目内独立递增 |
| Out of Scope | `OS-NNN` | 项目内独立递增 |
| Flagged Ambiguity | `FA-NNN` | 项目内独立递增 |
| Glossary 术语 | 术语本身作 anchor · 不编号 | — |

详见 [templates/knowledge.md](../templates/knowledge.md)。

## 7. 项目缩写注册

新项目缩写必须在 teamwork-space.md(多项目)或 config.md(单项目)注册一次。规则:
- **2-12 字符 · 全大写 · ASCII**(易读 · 文件名安全)
- **简单项目**:单字 e.g. `WEB` / `API` / `PAY` / `PTR`(Partner)
- **复合项目**:`-` 分组 e.g. `SVC-PLATFORM` / `OFFER-HOST`
- **避免与已注册项目缩写冲突**(workspace 内全局 unique)

实际已用缩写参考(从 git 历史抽样):`PTR`(Partner)/ `INFRA` / `SVC-PLATFORM` / `WEB` / `ADMIN` / `API` / `PAY`。

---

## namespace 总结

| ID | namespace | 说明 |
|---|---|---|
| F-NNN | **项目独立** | PTR-F033 与 SVC-PLATFORM-F033 可并存 |
| BL-NNN | **项目独立** | 同 F-NNN |
| BUG-...-NNN | **Feature 内独立** | seq 在单 Feature 范围递增 |
| ADR-NNNN | **全局** | 架构决策跨项目可见 |
| Dispatch NNN | **Feature 内独立** | dispatch_log/ 内递增 |
| GO/CV/PR/OS/FA-NNN | **项目独立** | KNOWLEDGE.md 内递增 |

---

## 引用本文件

- [TRIAGE.md § 4.3](../TRIAGE.md) — Feature ID 暂停点收集
- [stages/planning-stage.md § 3](../stages/planning-stage.md) — ROADMAP 起草时 BL-NNN 分配
- [stages/goal-stage.md](../stages/goal-stage.md) — Feature ID 已在 init-feature 时确定
- [templates/bug-report.md](../templates/bug-report.md) — Bug ID 格式
- [templates/roadmap.md](../templates/roadmap.md) — BL ↔ F 映射列说明
- [templates/adr-index.md](../templates/adr-index.md) — ADR-NNNN 维护
