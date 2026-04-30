# Teamwork

Your AI dev team — one AI works as a full team, with **role-based perspectives + contract-based stages + machine-readable state machine**, letting one person drive the complete software lifecycle from product planning to delivery.

[中文文档](./README.md) · Version: **v7.3.10+P0-60**

> ⚠️ **English doc lags behind** — only key sections updated for current version. For the full up-to-date spec, see the [Chinese README](./README.md) and the authoritative [CHANGELOG](./skills/teamwork/docs/CHANGELOG.md).

## Overview

Teamwork lets one AI work as a complete development team. Each role represents a professional direction of concern — PM ensures requirement completeness, QA ensures test coverage, RD ensures implementation quality, Architect ensures technical soundness, Designer ensures user experience. PMO orchestrates the process and manages information flow between stages. Not multiple AIs having meetings — it ensures every artifact is examined from enough professional angles. Users only need to state requirements and make decisions at key checkpoints. Compatible with Claude Code, Codex CLI, and other AI coding tools.

Six workflow types are supported:

- **Feature** — Full cycle: requirements → design → development → testing → acceptance
- **Bug Fix** — Investigate → assess → fix → verify → sync docs
- **Issue Investigation** — Root cause analysis with recommended next steps (no code output)
- **Feature Planning** — Decompose product goals into a prioritized ROADMAP with Wave-based execution batches and dependency tracking
- **Agile** — Streamlined flow for small changes (≤5 files, no UI/architecture changes, clear approach)
- **Micro** — Minimal channel for zero-logic changes (assets, copy, styles, config constants)

### Design Philosophy

The core challenge of software engineering isn't writing code — it's examining the same artifact from multiple professional angles. Each Teamwork role represents a professional direction of concern (PM→requirement completeness, QA→test coverage, RD→implementation quality, Architect→technical soundness, Designer→user experience, PL→product direction). PMO orchestrates the process and manages information flow.

Why multi-role switching works: create-critique cycles (PM writes PRD → PL critiques from business angle → PM revises), attention reallocation (switching roles = switching checklists = activating different evaluation dimensions), and forced re-reading (role switches force the AI to re-read the same document with new questions).

### Key Features (v7.3 Series)

#### Architecture Layer

- **Three-Contract Stages** (v7.3): Every stage file is structured as **Input Contract / Process Contract / Output Contract**. Specifies **what to produce** (output contracts), not **how to get there** (execution mode).
- **AI Plan Mode** (v7.3, 3-line core): Before each stage, the AI outputs an Execution Plan in main conversation (Approach / Rationale / Role specs loaded / Estimated). Execution mode (main conversation / Subagent / hybrid) is decided by the AI based on scale/complexity, not hard-bound to Subagent.
- **AC↔Test Strong Binding** (v7.3): PRD.md and TC.md YAML frontmatter are machine-readable. `acceptance_criteria[].id` ↔ `tests[].covers_ac` are one-to-one bound. `python3 {SKILL_ROOT}/templates/verify-ac.py {Feature}` auto-validates coverage completeness, eliminating "requirement → code" drift.
- **state.json Machine-Readable State Machine** (v7.3.2): Each Feature directory's `state.json` is the **single source of truth** for flow state, replacing the original STATUS.md. Contains `current_stage / completed_stages / legal_next_stages / stage_contracts / planned_execution / executor_history`. Single anchor for compact recovery.
- **Main-Conversation Artifact Protocol** (v7.3 §6): When tasks are executed directly in main conversation (PRD discussion, architect review, env setup), artifacts must follow YAML frontmatter spec. Forms complete closed loop with the Subagent dispatch protocol.

#### Flow Layer

- **Six Flow Types** (Feature / Bug / Issue / Feature Planning / Agile / Micro): Automatically identified by PMO's initial analysis. Each has explicit entry criteria, step description, and completion standards.
- **Truly Lightweight Micro** (v7.3, red line #1 Micro exception): PMO can directly modify code (zero-logic whitelist changes). **No Subagent, no Execution Plan, no dispatch file required**. Only retains "analysis → user confirm → execute → accept" minimum closed loop.
- **Pause Point Compression** (v7.3.4):
  - UI Design + Panorama Design merged into one "design batch" pause (Designer produces Feature UI + panorama incremental sync in one pass)
  - PM Acceptance + commit + push merged into one pause (PMO auto-commits locally; user picks 3-way for push)
  - Typical Feature pause points reduced from 6-8 to 4-5
- **Numbered Options** (v7.3.5): All options listed as `1/2/3...`. Recommended option marked 💡 and listed first. Last option is always "other instructions". User replies with a single digit (no typing required).
- **Flow Step Description** (v7.3): PMO initial analysis must provide the **full step description** of the chosen flow (stage chain + what each stage does + pause points). User confirms based on steps, not just flow name.

#### Execution Layer

- **Dispatch File Protocol**: Each Subagent dispatch produces `{Feature}/dispatch_log/{NNN}-{subagent}.md`. The file is both input and audit record. Main conversation ↔ Subagent handoff is structured. Parallel/re-dispatch/degradation all traceable.
- **Key Context (6 categories)**: Every dispatch must fill 6 categories (historical decisions / current focus / cross-Feature constraints / identified risks / degradation grants / priority tolerance). Write `-` when absent (proves PMO judged).
- **Multi-Perspective Review** (Architect / QA / Codex, three independent tracks): Architect defaults to main conversation (preserves project architecture context + skeptic perspective prevents rubber-stamping). QA / Codex go through Subagent for independent perspective. Three artifacts are structurally independent (independent generated_at / files_read / no cross-reference, machine-verifiable).
- **Scripted API E2E**: Subagent generates reusable Python scripts (`tests/e2e/F{N}/api-e2e.py`) instead of one-off curl. 4 assertion categories (status / body / DB / side effects). Scripts committed as Feature deliverables.
- **Duration Metrics Closed Loop** (v7.3.3): Each stage auto-records `started_at / duration_minutes / estimated_minutes / variance_pct / dispatches_count / retry_count / user_wait_seconds`. Feature completion report auto-aggregates a duration stats table. retros/*.md supports cross-Feature trend analysis.
- **Auto-Commit, User-Decides-Push** (v7.3.4): After PM acceptance → PMO auto-commits locally (structured message with AC coverage + review status + duration summary) → ⏸️ user picks 3-way (push / local only / reject for fix). PMO **cannot auto-push**; user retains full control of remote push.

#### Quality Assurance

- **Closed-Loop Verification Red Line**: RD/QA claims of "complete" must include actual command output (test/build results). PMO completion report must cite real data. No empty "done" statements.
- **Mandatory WARN Logs for Degradation**: All degradation paths (Subagent failure, Codex unavailable, host doesn't support TodoWrite, worktree unavailable, etc.) must emit structured WARN logs. Silent degradation violates the closed-loop verification red line.
- **PMO Preflight L1/L2/L3**: Before dispatching any Subagent, the corresponding preflight must pass. Failed preflight → no dispatch.
- **Product Panorama Protection** (v7.3.4): The panorama (`design/sitemap.md` + `design/preview/overview.html`) is **confirmed product + business logic truth**. Feature flow defaults to **incremental merge**, no rewriting. Any modification must add red annotation to sitemap + list diff in execution report. Structural changes (delete page / restructure nav) → suggest Feature Planning flow instead.
- **TDD + Machine Verification**: Tests-first recommended (soft constraint). Unit tests, typecheck, lint are Dev Stage Output Contract hard gates.
- **State Recovery**: New session/post-compact reads `{Feature}/state.json` to recover. Not dependent on conversation memory.

## Host Compatibility

Teamwork auto-detects host environments via the `{SKILL_ROOT}` variable:

| Host | Detection | SKILL_ROOT | Instruction File |
|------|-----------|------------|------------------|
| Claude Code | Task tool + .claude/ dir | .claude/skills/teamwork | CLAUDE.md |
| Codex CLI | .codex/ or .agents/ dir | .agents/skills/teamwork | AGENTS.md |
| Gemini CLI | .gemini/ dir | .gemini/skills/teamwork | GEMINI.md |
| Generic | No match | Inferred from SKILL.md | AGENTS.md |

Execution mode auto-adapts: Claude Code uses Task tool for Subagent dispatch; Codex CLI uses agent TOML spawn; hosts without Subagent support degrade to main-conversation execution (PMO chooses via AI Plan Mode).

## Collaboration Models

### Single-User Mode (default)
One user + one Claude session operates the entire project. `.teamwork_localconfig.md` scope is for focusing attention, not concurrency control.

### Multi-User Mode (experimental)
Multiple users use separate Claude sessions on different sub-projects.

Constraints:
- Each sub-project can have only one active session at a time
- Different users must own different sub-projects (no scope overlap)
- Cross-sub-project requirements coordinated by one user
- No concurrent development on the same sub-project

## Install

```bash
# Auto-detect host (Claude Code / Codex CLI)
npx skills add okteam99/teamwork

# Or manual install
bash skills/teamwork/install.sh
```

## Upgrade

```bash
npx skills update okteam99/teamwork
```

## Usage

```bash
# Start Feature flow
/teamwork implement user login

# Start Feature Planning
/teamwork plan an e-commerce recommendation system

# Report a bug
/teamwork login page returns 500 on mobile

# Small change (Agile: ≤5 files, clear approach)
/teamwork add CSV export button to user list

# Minor change (Micro: zero-logic, PMO modifies directly)
/teamwork replace homepage logo

# View status / resume an interrupted flow
/teamwork status
/teamwork continue

# Switch role
/teamwork pm | designer | qa | rd | pmo

# Exit collaboration mode
/teamwork exit
```

> Note: Product Lead is auto-dispatched by PMO, no manual switching. Flow type is auto-detected by PMO.

## File Structure

```
teamwork/
├── skills/
│   └── teamwork/
│       ├── SKILL.md                  # Main entry: red lines, AI Plan Mode, file index
│       ├── INIT.md                   # 🔴 Mandatory on each startup (host detection + project space + kanban)
│       ├── FLOWS.md                  # Flow specs: six flow types with detailed execution rules
│       ├── ROLES.md                  # Role index (→ roles/*.md)
│       ├── RULES.md                  # Core rules: pause / transition / change / closed-loop verification
│       ├── REVIEWS.md                # Review specs (PRD / TC / UI restoration)
│       ├── STANDARDS.md              # Coding standards index
│       ├── STATUS-LINE.md            # Status line format + user intent recognition + stage mapping
│       ├── TEMPLATES.md              # Document template index
│       ├── CONTEXT-RECOVERY.md       # New session / interruption recovery
│       ├── PRODUCT-OVERVIEW-INTEGRATION.md  # product-overview/ and PL integration rules
│       ├── install.sh                # One-click install (auto host detection)
│       │
│       ├── roles/                    # Full role definitions (load on demand)
│       │   ├── pmo.md
│       │   ├── product-lead.md
│       │   ├── pm.md
│       │   ├── designer.md
│       │   ├── qa.md
│       │   └── rd.md                 # RD + Architect (solution review + Code Review)
│       │
│       ├── rules/                    # Split core rules
│       │   ├── flow-transitions.md   # 🔴 Stage transition table (single source of truth)
│       │   ├── gate-checks.md        # PMO preflight + state.json sync rules
│       │   └── naming.md             # Naming conventions
│       │
│       ├── stages/                   # Stage specs (three-contract structure)
│       │   ├── plan-stage.md         # PM PRD + PL-PM discussion + multi-perspective review
│       │   ├── ui-design-stage.md    # Feature UI + panorama incremental (v7.3.4 merged)
│       │   ├── panorama-design-stage.md  # Panorama rebuild mode (Feature Planning only)
│       │   ├── blueprint-stage.md    # QA TC + RD TECH + architect solution review
│       │   ├── blueprint-lite-stage.md  # Lightweight blueprint for Agile flow
│       │   ├── dev-stage.md          # RD TDD dev + unit tests + worktree integration
│       │   ├── review-stage.md       # Three independent perspectives (Architect / QA / Codex)
│       │   ├── test-stage.md         # Env prep + integration tests + scripted API E2E
│       │   └── browser-e2e-stage.md  # Browser E2E (semi-auto, optional)
│       │
│       ├── agents/                   # Task units + protocols
│       │   ├── README.md             # Execution mode ref + Dispatch Protocol §4 + Main-Conv Artifact §6
│       │   ├── rd-develop.md
│       │   ├── arch-code-review.md
│       │   ├── qa-code-review.md
│       │   ├── integration-test.md
│       │   └── api-e2e.md            # Scripted API E2E spec
│       │
│       ├── codex-agents/             # Codex CLI custom agent definitions
│       │   ├── README.md
│       │   ├── rd-developer.toml / reviewer.toml / tester.toml
│       │   ├── planner.toml / designer.toml / e2e-runner.toml
│       │   └── hooks.json
│       │
│       ├── standards/                # Coding standards by tech stack
│       │   ├── common.md             # Common: TDD / architecture / self-check / WARN logs
│       │   ├── backend.md            # Backend: API, logs, DB migrations
│       │   └── frontend.md           # Frontend: test layers, E2E, component tests
│       │
│       └── templates/                # Document templates
│           ├── prd.md                # With YAML frontmatter acceptance_criteria[]
│           ├── tc.md                 # With YAML frontmatter tests[].covers_ac
│           ├── tech.md / ui.md
│           ├── architecture.md / project.md / roadmap.md
│           ├── teamwork-space.md / config.md / dependency.md
│           ├── feature-state.json    # Feature state machine (v7.3.2 replaces status.md)
│           ├── verify-ac.py          # AC↔test coverage verification (standard impl)
│           ├── bug-report.md / knowledge.md / retro.md
│           ├── e2e-registry.md / pl-pm-feedback.md
│           ├── review-log.jsonl / dispatch.md
│           └── README.md
│
├── README.md / README-EN.md
└── .gitignore
```

## Feature Flow Overview (v7.3 contracts + v7.3.4 compressed pauses)

```
PMO initial analysis (type detection + flow step description + cross-Feature conflict check)
  ↓
⏸️ User confirms flow (based on step description, reply with digit 1/2/3)
  ↓
🔗 Goal-Plan Stage (PM PRD + PL-PM discussion + multi-perspective review · v7.3.10+P0-53 renamed from Plan)
  ↓
⏸️ User confirms PRD (reply with digit)
  ↓
🔗 UI Design Stage (if UI needed; v7.3.4 merges panorama incremental)
  Designer produces in one pass: Feature UI + HTML preview + panorama incremental sync (🟡 cautious modification)
  ↓
⏸️ User confirms "design batch" (UI + panorama reviewed together, single pause)
  ↓
🔗 Blueprint Stage (QA TC + RD TECH + architect solution review; AC↔test binding)
  ↓
⏸️ User confirms technical solution
  ↓
📋 PMO L2 preflight → 🔗 Dev Stage (AI Plan decides main-conv/Subagent; TDD + unit tests + machine verification)
  ↓ 🚀 auto
🔗 Review Stage (Architect in main conv + QA/Codex Subagent parallel; three structurally independent artifacts)
  ↓ 🚀 auto
🟡 Test Stage pre-confirmation (reply digit: 1 execute now / 2 defer / 3 skip)
  ↓
🔗 Test Stage (env in main conv + integration tests + scripted API E2E)
  ↓
Browser E2E (if needed, reply digit to decide)
  ↓
🔗 PM Acceptance + commit + push (v7.3.4 merged pause)
  PM completes acceptance → PMO auto-commits locally (structured message)
  ⏸️ User replies digit:
    1. ✅ Approve → auto commit + push
    2. ✅ Approve → local commit only (user retains push decision)
    3. ❌ Reject → provide info, route to fix stage
    4. Other instructions
  ↓
PMO completion report (deliverables + flow integrity + doc sync + ⏱️ duration stats + 📦 Commit & Push status)
```

Typical Feature pause points: **3-5** (flow / PRD / design batch / solution / acceptance+commit+push).

## Agile Flow Overview

```
PMO analysis → detects Agile (≤5 files, no UI/architecture change, clear approach) → ⏸️ user confirms
  ↓
PM → simplified PRD (core requirements + structured AC) → ⏸️ user confirms
  ↓
🔗 BlueprintLite Stage (QA simplified TC + RD implementation plan, main-conv, no review)
  ↓
🔗 Dev Stage → Review Stage → Test Stage (same as Feature)
  ↓
PM Acceptance + commit + push (digit reply 1/2/3/4) → PMO completion report
```

## Micro Flow Overview (v7.3 truly lightweight)

```
PMO analysis + entry criteria check + flow step description
  ↓
⏸️ User confirms Micro (reply digit 1/2/3/4)
  ↓
PMO directly modifies code (🟢 no Subagent, no Execution Plan, no dispatch)
  ↓
⏸️ User acceptance (manual test / visual verify)
  ↓
PMO completion report (with Micro post-audit)
```

Entry criteria: zero-logic changes + changes within whitelist (asset replacement / copy / styles / config constants / comments).

## Feature Planning Flow Overview

```
PMO analysis → detects Feature Planning → assesses scope
  ↓
📁 Sub-project level:
  PM → discuss product direction with user → ⏸️ user confirms
    ↓
  🔗 Panorama Design Stage (rebuild mode, if UI) → ⏸️ user confirms panorama
    ↓
  PM → update PROJECT.md → decompose ROADMAP.md (Wave + dependencies + parallelism)
    ↓
  ⏸️ User confirms ROADMAP → each Feature enters standard Feature flow

🌐 Workspace level:
  PM → discuss overall architecture → update teamwork_space.md → ⏸️ user confirms
    ↓
  For each affected sub-project → execute sub-project-level Planning
    ↓
  PMO → finalize teamwork_space.md → ⏸️ user final confirmation
```

## Product Planning and Product Lead

Teamwork has a built-in product planning system maintained by the **Product Lead (PL)** role. PMO auto-dispatches PL when product-level planning and decisions are needed.

### Product Planning Documents

```
product-overview/
├── {project}_业务架构与产品规划.md    # Product positioning, business flow, revenue model, feature planning
├── {project}_执行手册.md              # Execution lines, milestones, acceptance criteria
└── {project}_Product_Plan.md          # Optional · external product plan
```

Product planning docs are upstream inputs to Feature Planning and the top-level basis for change cascading.

### Product Lead's Three Modes

**Guided Mode**: On first project initialization, if `product-overview/` doesn't exist, PMO auto-switches to PL Guided Mode. PL guides the user to build product planning docs from scratch via structured Q&A (business architecture → execution manual → project init).

**Discussion Mode**: When the user raises product-directional topics (adjust business model, add/remove business lines), PMO detects and dispatches PL to Discussion Mode. Once consensus is reached, PL writes conclusions to product-overview docs and generates a CHG change record.

**Execution Mode**: When discussion conclusions need implementation, PL produces a change impact assessment report, evaluating scope and level. Upon user confirmation, triggers downstream cascading:

```
Product Lead assessment → change level determination
  ├── Level 1 (feature-level) → directly enter Feature Planning
  ├── Level 2 (module-level) → update product-overview → sub-project Feature Planning
  └── Level 3 (direction-level) → update product-overview → workspace-level Feature Planning
```

### Change Cascading and Bottom-Up Escalation

During development, if a Feature conflicts with upstream docs (ROADMAP conflict, architecture adjustment needed), PM/RD triggers **bottom-up impact escalation**. PMO traces upward until finding the highest-level doc needing change. PL assesses, then cascades downstream.

## Red Lines (15 points; full list in [SKILL.md](./skills/teamwork/SKILL.md))

1. **PMO write-op boundary**: Non-Micro flow runtime changes → must follow full flow; Micro flow PMO can modify directly (whitelist zero-logic); pure docs PMO can modify (requires annotation)
2. **Six flows**: Feature / Bug / Issue / Feature Planning / Agile / Micro, no custom flows
3. **No self-simplification**: Each requirement goes through its full flow; "simple/small/pure port" is not a skip reason
4. **PMO is single entry point**: All user input handled by PMO first
5. **Pause points require explicit confirmation**: Including Micro user confirmation and acceptance
6. **Requirement type / flow type** enum-restricted (6 types)
7. **Feature Planning outputs docs only**, no code
8. **Closed-loop verification**: "Complete" must include actual command output
9. **Pause points require suggestion + numbered options** (v7.3.5): 💡 advice + 📝 reason + 1/2/3 numbered + last option is "other instructions"
10. **Write-op hard gate**: PMO must output initial analysis before any write operation
11. **No pausing at non-pause points**: 🚀 auto-transition nodes forbid injecting questions
12. **PMO preflight**: Must complete L1/L2/L3 preflight before any dispatch
13. **Subagent preflight required**
14. **AI Plan Mode red line** (v7.3): Each stage start requires 3-line Execution Plan output; Plan written to state.json.planned_execution
15. **Flow confirmation red line** (v7.3): PMO must provide full flow step description; user confirms based on steps

## Version History

- **v7.3.5**: Numeric pause point options (user replies with a digit)
- **v7.3.4**: Pause point compression (UI+panorama merged, acceptance+commit+push merged 3-way)
- **v7.3.3**: Stage duration metrics closed loop (duration / variance / retry / user_wait)
- **v7.3.2**: STATUS.md deprecated, state.json becomes single Feature state file
- **v7.3.1**: Rule alignment and ceremony reduction (Execution Plan 3-line core)
- **v7.3**: Three-contract stages + AI Plan Mode + AC↔test binding + main-conversation artifact protocol + state.json
- **v7.2**: Dispatch file protocol + scripted API E2E + progress visibility + Key Context
- **v7.1 and earlier**: Multi-role review, multi-sub-project mode, change cascading, closed-loop verification, and other foundational architecture

Full changelog in [skills/teamwork/docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md).

## License

MIT
