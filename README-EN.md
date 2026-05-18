# Teamwork

A state-machine-driven AI development orchestrator. `state.py` validates proactively and tells the AI what to do next — the AI runs a command and immediately knows the next step, instead of recalling specs from memory.

[中文](./README.md) · Version: **v8.0**

---

## Design Philosophy

**Enumerable rules go into code; non-enumerable judgment stays with the AI.**

| Category | Examples | Home |
|----------|----------|------|
| Enumerable | State transitions, entry prerequisites, exit artifacts, field schema, flow closed-set, pause-point protocol | `tools/state.py` (materialized checks) |
| Non-enumerable | PRD completeness, architecture soundness, code elegance, pause-point recommendation wording | AI decides |
| User sovereignty | Code layout, business terms, diagnostic commands | User fills in; teamwork reads on demand |

### v7 → v8 Paradigm Shift

```
v7 (replaced):                          v8:
PMO recalls + reads spec markdown        AI runs state.py xx-start
  ↓                                      ↓
schedules stage/role from memory         state.py validates + emits brief proactively
  ↓                                      ↓
state.py passively records               AI executes per brief → runs xx-complete
                                         ↓
                                         state.py checks artifacts + auto-advances stage
```

v8 materializes 16/17 sub-clauses of the 9 red lines into `state.py` — rules shift from "AI self-discipline" to "tool enforcement".

### How Multi-Role Collaboration Works

When a single role covers multiple perspectives, they mask each other — PM's "what the user wants" buries QA's "edge cases"; the architect's "elegance" buries RD's "delivery deadline". Teamwork assigns roles by specialty, with PMO orchestrating:

- **Create-critique loop**: PM writes PRD → PL critiques from business direction → PM revises. A single role's single-pass output skips blind spots masked by its own perspective.
- **Attention reallocation**: switching roles = switching checklists = activating different evaluation dimensions
- **Forced re-read**: a role switch forces the AI to re-read the same document with new questions
- **Heterogeneous-model review**: review brings in a heterogeneous model (when claude is the main window, external = codex, and vice versa) — a cross-model perspective exposes same-model self-review blind spots

You only provide requirements and make decisions at key checkpoints.

---

## Getting Started

### Install

```bash
# Auto-detects the host environment (Claude Code / Codex CLI / Gemini CLI)
npx skills add okteam99/teamwork
```

On session start, `tools/bootstrap.py` automatically maintains the project skeleton (KNOWLEDGE / TROUBLESHOOTING / GLOSSARY), host instruction-file injection sections, and version checks — all silent, no interruption.

### Upgrade

```bash
npx skills update okteam99/teamwork
```

### Start a Flow

```bash
# Feature (full requirement → design → dev → test → acceptance → delivery)
/teamwork implement user login

# Agile requirement (≤5 files, clear plan, no UI/architecture change)
/teamwork add an export-CSV button to the user list

# Micro (zero-logic change — copy / style / asset replacement)
/teamwork replace the homepage logo with the new image

# Bug fix
/teamwork the login page returns 500 on mobile

# Investigation (no code output, just root-cause)
/teamwork P95 latency rose in production over the last 3 days, take a look

# Feature Planning (break down the ROADMAP, no code output)
/teamwork plan the e-commerce recommendation system
```

### What You Do vs What the AI Does (Feature flow)

| Stage | You | AI |
|-------|-----|-----|
| Start | Give a one-line requirement | PMO 5-mode triage + flow-type identification + prepare sub-flow emits the 4-item config pause point |
| Confirm config | Reply `ok` / change an item | PMO creates the worktree + `state.py init-feature` enters the state machine |
| goal | Wait / correct | PM drafts PRD + multi-role parallel review + converge |
| Confirm PRD | Reply `ok` | — |
| ui_design (optional) | Wait | Designer produces UI + preview + syncs sitemap |
| blueprint | Wait | RD drafts TECH + QA drafts TC + architect + heterogeneous-model review |
| dev | Wait | RD implements via TDD + unit tests + machine checks |
| review | Wait | Architect + QA + heterogeneous model — three independent reviews |
| test | Wait (start the app if needed) | QA integration + api-e2e |
| pm_acceptance | Reply `ok` / feedback | PM verifies AC item by item + three-option decision |
| **ship Phase 1** | Click merge on the platform | sanitize → push branch → create MR via CLI → ⏸️ await merge |
| **ship Phase 2** | Wait | Verify merge + finalize + clean up worktree → ✅ completed |

Typical Feature pause points: **3-5**.

---

## 5-Mode Entry Triage

The teamwork entry is PMO's main-conversation **5-mode triage** (not a state.py command — see [SKILL.md § Triage Entry Spec](./skills/teamwork/SKILL.md)):

| Mode | Trigger | Behavior | Handover |
|------|---------|----------|----------|
| **A · query** | look / check / why / investigate / explain | grep + Read answer + follow-up guidance | Close in main conversation |
| **B · execute** | implement / fix / change / do / develop | audit_line + recognize execute intent | → prepare sub-flow |
| **C · resume** | continue / resume / ship F032 | Find state.json + jump to current_stage | → state machine |
| **D · status** | status / where are we / board | Load Feature board + output | Close in main conversation |
| **E · discuss** | I feel / what do you think / X vs Y | Multi-perspective discussion + options + recommendation | Close (can escalate to B after convergence) |

After mode B is identified, it runs the **prepare sub-flow** ([docs/prepare.md](./skills/teamwork/docs/prepare.md)): flow-type identification → worktree decision → emit the 4-item config pause point (Feature ID / merge_target / worktree path / branch) → user confirmation → `git worktree add` + `state.py init-feature`.

## 6 Flow Types + Stage Chains

| Flow | Use case | Stage chain | Default pause points |
|------|----------|-------------|----------------------|
| **Feature** | Full feature development | goal →(ui_design)→ blueprint → dev → review → test →(browser_e2e)→ pm_acceptance → ship | 3-5 |
| **Agile requirement** | ≤5 files + clear plan + no UI/architecture change | goal → blueprint_lite → dev → review → test → pm_acceptance → ship | 2-3 |
| **Bug** | Production/local defect | dev → review → test → pm_acceptance → ship | 3-4 |
| **Micro** | Zero-logic change (copy/style/asset/config) | dev → pm_acceptance → ship | 2 |
| **Feature Planning** | Break a product goal into a ROADMAP | Not in the state machine · PMO main-conversation | 1 |
| **Investigation** | Root-cause only | Not in the state machine · like mode A | 0-1 |

The 4 state-machine flows (Feature / Agile / Bug / Micro) run the `state.py` stage chain; Feature Planning / Investigation do not enter the state machine and are executed by PMO in the main conversation.

---

## Advanced Usage

### Flow Control

```bash
/teamwork status      # Current state (where we are / next step / pending decisions)
/teamwork continue    # Resume an interrupted flow (via state.json · not conversation memory)
```

Pause-point options are numbered (💡 recommended item is listed first) — **just reply with a number**. Global shortcuts: `ok` = take the recommendation, `all default` = use all defaults, plus `continue` / `skip` / `bypass`.

### Role System

| Role | Responsibility |
|------|----------------|
| **PMO** | Flow orchestration: accept input → 5-mode triage → schedule roles → maintain state.json → pause points |
| **PL** (Product Lead) | Product direction: product-overview onboarding / business-topic discussion / change cascade |
| **PM** | PRD + structured AC + final acceptance |
| **Designer** | UI restoration + sitemap (sitemap + preview) |
| **Architect** | Tech Review (blueprint) + Code Review (review) + ARCHITECTURE.md + ADR |
| **QA** | TC (AC↔test binding) + integration / api-e2e + Code Review |
| **RD** | TDD implementation + unit tests + self-check + bug investigation report |
| **External Reviewer** | Heterogeneous-model code review (codex / claude · independent stance) |

In v8, role collaboration uses **main-conversation identity switching** (no Subagent dispatch) — switching roles = switching checklists + forced re-read.

### Test System (4 Layers)

| Layer | Scope | Stage |
|-------|-------|-------|
| unit | Single class / function red-green loop | dev (TDD) |
| integration | In-process cross-module / service contract | test |
| api-e2e | Live cross-process (real binary + real HTTP) | test |
| browser-e2e | UI interaction flow + screenshots | browser_e2e (optional) |

### Worktree Strategy

Defaults to `auto`. The prepare sub-flow creates an isolated worktree for each Feature (`{worktree_root_path}/{Feature-ID}` · default `worktree_root_path=.worktree`); dev works inside the worktree; ship Phase 2 cleans up after verifying the merge. `init-feature` materially validates the worktree path convention + cwd. Configurable in `.teamwork_localconfig.json`.

### Pending-Needs Pool

Items found across Features/sessions that are "out of current scope but should be done" are recorded in `teamwork-space.md § Pending-Needs Pool` (`PENDING-NNN`). When the user asks "what else is pending / backlog", PMO lists them automatically. Once turned into a Feature/Bug, the entry is removed from the table immediately, keeping the pool lightweight.

### Product Planning System

The Product Lead (PL) role maintains `product-overview/` (business architecture + execution handbook). For product-direction topics, PMO schedules PL for discussion; when a conclusion needs to land, PL triggers a downstream cascade into Feature Planning based on the change level (function / business module / direction). When a conflict with upstream docs is found mid-development, a bottom-up impact escalation is triggered.

### Cross-Host Compatibility

| Host | Instruction file |
|------|------------------|
| Claude Code | CLAUDE.md |
| Codex CLI | AGENTS.md |
| Gemini CLI | GEMINI.md |

`bootstrap.py` automatically maintains the teamwork injection section of the corresponding instruction file per host.

---

## Core Guarantees · 9 Red Lines R1-R9

v8 turns the red lines from "AI self-discipline" into "tool enforcement" — only R3 remains a soft rule (non-enumerable):

| Red line | Content | v8 materialized home |
|----------|---------|----------------------|
| **R1** Code-write authority to RD | Code/tests/build by the RD role; external models review-only | state.py checks identity switch on write ops |
| **R2** Flow-type closed-set | 6 flows · no self-invented variants | `init-feature --flow-type` enum |
| **R3** PMO unified intake | All user input is taken by PMO first | Kept as AI judgment (soft rule) |
| **R4** Flow boundary | No simplification / no inflation / must give step description | state.py enforces stage chain by flow_type |
| **R5** Pause-point protocol | Must await user confirmation + give 💡 recommendation + numbered | state.py emits pause-point markdown |
| **R6** Planning produces docs only | No code · no auto-starting a Feature | `init-feature` rejects "Feature Planning" |
| **R7** Evidence closure | Claiming "done" requires commit + actual output | `xx-complete` checks commit exists + artifacts |
| **R8** Write-op hard gate chain | Reject stage-start before prepare done · ship CLI-first | state.py internal materialized interception |
| **R9** Session bootstrap | Entry must run bootstrap.py + PMO triage | `tools/bootstrap.py` |

### Key Quality Mechanisms

- **Contractualized stages**: each stage has prerequisites (entry checks) / artifacts (output shape) / evidence_checks (completion evidence), materialized by state.py
- **AC↔Test strong binding**: `PRD.md`'s `acceptance_criteria[].id` ↔ `TC.md`'s `tests[].covers_ac`; `verify-ac.py` auto-checks coverage completeness
- **Multi-perspective review**: architect / QA / heterogeneous model produce three structurally independent artifacts, avoiding the "the last review already said it's fine" applause effect
- **fix-retry loop**: review / test failures retry within the stage (no stage switch), audit keeps rounds[]
- **State recovery**: `{Feature}/state.json` is the single source of truth for flow state, with `_state_checksum` self-protection; after a new conversation / compaction, reading state.json restores everything
- **ADR + KNOWLEDGE**: the three-question trigger auto-records ADRs; `KNOWLEDGE.md` converges into Gotcha / Convention / Architecture with hard triggers

See the full 9-red-line rationale in [docs/v8-redesign/00-MANIFESTO.md](./skills/teamwork/docs/v8-redesign/00-MANIFESTO.md).

---

## Documentation Map

| File | Purpose |
|------|---------|
| [SKILL.md](./skills/teamwork/SKILL.md) | Main entry: design philosophy + command list + Triage entry spec + 9 red lines + project-level doc architecture |
| [FLOWS.md](./skills/teamwork/FLOWS.md) | 6 flow types — telos and use cases |
| [STAGES.md](./skills/teamwork/STAGES.md) | 10-stage index + common cite discipline |
| [ROLES.md](./skills/teamwork/ROLES.md) | Role index (→ roles/*.md) |
| [STANDARDS.md](./skills/teamwork/STANDARDS.md) | Technical standards index (→ standards/*.md) |
| [TEMPLATES.md](./skills/teamwork/TEMPLATES.md) | Document template index |
| [docs/prepare.md](./skills/teamwork/docs/prepare.md) | mode B → preparation sub-flow before entering the state machine |
| [docs/feature-planning.md](./skills/teamwork/docs/feature-planning.md) | Feature Planning flow guide (not in the state machine) |
| [docs/conventions.md](./skills/teamwork/docs/conventions.md) | Feature ID + worktree path naming conventions |
| [stages/*.md](./skills/teamwork/stages/) | Each stage's telos + Output Contract (validation goes into state.py) |
| [roles/*.md](./skills/teamwork/roles/) | Role telos + authoring guidelines |
| [standards/*.md](./skills/teamwork/standards/) | Technical standards (common / backend / frontend / tdd, etc.) |
| [tools/state.py](./skills/teamwork/tools/state.py) | The sole orchestrator entry (≈ 39 commands) |
| [tools/bootstrap.py](./skills/teamwork/tools/bootstrap.py) | Session-start maintenance |
| [docs/v8-redesign/00-MANIFESTO.md](./skills/teamwork/docs/v8-redesign/00-MANIFESTO.md) | Design constitution · paradigm shift · 9-red-line homes |
| [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) | Full version changelog |

---

## Version

**v8.0** — Paradigm shift: from "PMO recalls and reads specs to schedule" to "state.py state-machine-driven + the AI knows the next step by running a command". Not backward-compatible; migrate old Features with `state.py migrate-v7-to-v8 --feature <path>`.

See the full changelog in [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md).

---

## License

MIT
