# Teamwork

Your AI dev team — one AI works as a full team, with role-based perspectives and quality-gated stages.

[中文文档](./README.md)

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

### Key Features

- **8-Stage architecture**: Plan / UI Design / Panorama Design / Blueprint / Dev / Review / Test / Browser E2E, each with dedicated specs and quality gates
- **BlueprintLite Stage**: Lightweight blueprint for agile flow (QA simplified TC + RD implementation plan, no reviews), keeping Dev Stage uniform across all flow types
- **Strict stage transition verification**: Cross-Stage transitions must cite `flow-transitions.md` source text + line number; Stage-internal steps use lightweight markers (📌 Blueprint 1/4) to reduce process tax
- **PMO pre-checks & hard gates**: L1/L2/L3 pre-checks required before dispatch; no write operations before PMO initial analysis
- **PMO write boundary**: Runtime-affecting changes must follow full process (with quality gates); documentation changes PMO can make directly with annotation
- **Cross-host compatibility**: Supports Claude Code / Codex CLI / Gemini CLI via `{SKILL_ROOT}` variable and host auto-detection (includes install.sh for one-click deployment)
- **File-path-first Subagent input**: Subagents read original files directly instead of relying on PMO summary relay, reducing information decay
- **Dispatch file protocol**: Every Subagent dispatch generates one markdown file (`{Feature}/dispatch_log/{NNN}-{subagent}.md`) — the file is both input and audit record; Subagent prompt shrinks to ~5 lines (just pointing to the dispatch file). Full INDEX aggregate view, parallel/re-dispatch/degradation all traceable
- **Degradation WARN logs**: Every fallback path (failed Subagent dispatch, Codex CLI unavailable, host lacking TodoWrite, worktree unavailable, etc.) must emit a structured WARN log — silent degradation is treated as a violation of closed-loop verification
- **Blueprint Stage as Subagent**: 4-step internal loop runs in Subagent, keeping main dialog context free
- **Worktree integration**: Optional git worktree strategy (off/auto/manual), Dev Stage auto-creates/cleans Feature branch worktrees
- **Product Lead role**: Three modes — Guided Init (build product-overview from scratch), Discussion (product direction with CHG records), Execution (cascade changes across sub-projects)
- **Change cascade**: 3-level impact assessment (L1 Feature / L2 Module / L3 Direction) with bottom-up escalation
- **Multi-role review**: PRD / TC / technical plans reviewed from multiple professional perspectives
- **Product-wide UI design**: design/sitemap.md + design/preview/overview.html as single source of truth for product UI
- **Multi-project mode**: teamwork_space.md orchestrates multiple sub-projects with business / midplatform types and cross-project dependency tracking
- **Feature status tracking**: STATUS.md in each Feature directory serves as single source of truth; PMO auto-updates on every stage transition
- **Closed-loop verification**: "Done" claims must include actual command output (test/build results)
- **Pause-point control**: Key decision nodes wait for explicit user confirmation, must include recommendations (💡) and rationale (📝)
- **TDD-driven development**: Tests are written before implementation code
- **State recovery**: Sessions can resume from interruption via `CONTEXT-RECOVERY.md`

## Installation

```bash
# Auto-detects host environment (Claude Code / Codex CLI)
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
# Start a feature workflow
/teamwork implement user login

# Plan product features
/teamwork plan a recommendation system for the e-commerce app

# Report a bug
/teamwork login page returns 500 error on mobile

# Small change (agile: ≤5 files, clear approach)
/teamwork add CSV export button to user list

# Micro change (zero-logic: assets/copy/config)
/teamwork replace the homepage logo with new image

# Check current status / resume interrupted flow
/teamwork status
/teamwork continue

# Switch role
/teamwork pm | designer | qa | rd | pmo

# Exit teamwork mode
/teamwork exit
```

> Note: Product Lead is dispatched automatically by PMO. Flow type is auto-detected by PMO.

## Cross-Host Compatibility

Teamwork auto-detects the host environment via `{SKILL_ROOT}` variable:

| Host | Detection | SKILL_ROOT | Instruction File |
|------|-----------|------------|------------------|
| Claude Code | Task tool + .claude/ dir | .claude/skills/teamwork | CLAUDE.md |
| Codex CLI | .codex/ or .agents/ dir | .agents/skills/teamwork | AGENTS.md |
| Gemini CLI | .gemini/ dir | .gemini/skills/teamwork | GEMINI.md |
| Generic | None matched | Inferred from SKILL.md | AGENTS.md |

Subagent dispatch adapts to host: Claude Code uses Task tool, Codex CLI uses agent toml spawn, hosts without Subagent support fall back to main-dialog execution.

## File Structure

```
teamwork/
├── skills/
│   └── teamwork/
│       ├── SKILL.md              # Entry point — red lines, file index, quick nav
│       ├── INIT.md               # 🔴 Must-read on every start (host detection + workspace + board)
│       ├── FLOWS.md              # Flow specs: 6 flow types with selection & execution rules
│       ├── ROLES.md              # Role index (→ roles/*.md)
│       ├── RULES.md              # Core rules: pause, transition, change, closed-loop verification
│       ├── REVIEWS.md            # Review specs (PRD / TC / UI acceptance)
│       ├── STANDARDS.md          # Coding standards index
│       ├── STATUS-LINE.md        # Status line format + user intent detection + stage mapping
│       ├── TEMPLATES.md          # Document template index
│       ├── CONTEXT-RECOVERY.md   # Session interruption recovery mechanism
│       ├── install.sh            # One-click install (auto-detects host)
│       │
│       ├── roles/                # Role definitions (loaded on demand)
│       │   ├── pmo.md
│       │   ├── product-lead.md
│       │   ├── pm.md
│       │   ├── designer.md
│       │   ├── qa.md
│       │   └── rd.md             # RD + Architect (design review + Code Review)
│       │
│       ├── rules/                # Split core rules
│       │   ├── flow-transitions.md   # 🔴 Stage transition table (single source of truth)
│       │   ├── gate-checks.md        # PMO pre-checks (L1/L2/L3) + Stage-internal markers
│       │   └── naming.md             # Naming conventions
│       │
│       ├── stages/               # Stage specs (loaded by PMO on dispatch)
│       │   ├── plan-stage.md         # PM/QA plan + test cases
│       │   ├── panorama-design-stage.md
│       │   ├── ui-design-stage.md
│       │   ├── blueprint-stage.md    # Tech plan + architect review (Subagent loop)
│       │   ├── blueprint-lite-stage.md # Agile-only lightweight blueprint
│       │   ├── dev-stage.md          # RD TDD dev + self-check + worktree integration
│       │   ├── review-stage.md       # Architect CR + Codex Review
│       │   ├── test-stage.md         # QA code review + integration test + API E2E
│       │   └── browser-e2e-stage.md  # Browser E2E (optional)
│       │
│       ├── agents/               # Task units (referenced by stages)
│       │   ├── README.md             # Dispatch conventions + host-adaptive dispatch
│       │   ├── rd-develop.md
│       │   ├── arch-code-review.md
│       │   ├── qa-code-review.md
│       │   ├── integration-test.md
│       │   └── api-e2e.md
│       │
│       ├── codex-agents/         # Codex CLI custom agent definitions
│       │   ├── README.md
│       │   ├── rd-developer.toml
│       │   ├── reviewer.toml
│       │   ├── tester.toml
│       │   ├── planner.toml
│       │   ├── designer.toml
│       │   ├── e2e-runner.toml
│       │   └── hooks.json
│       │
│       ├── standards/            # Coding standards by tech stack
│       │   ├── common.md             # Shared: TDD checklist, architecture, self-check
│       │   ├── backend.md            # Backend: TDD, API, logging, DB migration
│       │   └── frontend.md           # Frontend: test layers, E2E, component testing
│       │
│       └── templates/            # Document templates
│           ├── prd.md / tc.md / tech.md / ui.md
│           ├── architecture.md / project.md / roadmap.md
│           ├── teamwork-space.md / config.md / dependency.md
│           ├── status.md / bug-report.md / knowledge.md / retro.md
│           ├── e2e-registry.md / pl-pm-feedback.md
│           └── README.md
│
├── README.md / README-EN.md
└── .gitignore
```

## Feature Workflow (8-Stage)

```
PMO analysis → type identification + cross-Feature conflict check → ⏸️ User confirms
  ↓
PM → PRD draft
  ↓
🤖 PL-PM collaborative discussion (multi-round convergence) → PRD finalized
  ↓
🤖 PRD technical review (PM / RD / Designer / QA / PMO perspectives)
  ↓
⏸️ User confirms PRD
  ↓
🔗 UI Design Stage (if UI needed) → sync product-wide design
  ↓
⏸️ User confirms design
  ↓
🔗 Plan Stage (QA Test Plan + BDD Cases)
  ↓
🤖 TC technical review → auto-transition if no blockers
  ↓
🔗 Blueprint Stage (RD tech plan → Architect review, Subagent loop)
  ↓
⏸️ User confirms tech plan (complex solutions only)
  ↓
🔗 Dev Stage (RD TDD dev + unit tests + self-check, with actual test output)
  ↓
🔗 Review Stage (Architect Code Review + Codex Review, parallel)
  ↓
🔗 Test Stage (QA code review + integration test + API E2E, with actual output)
  ↓
🔗 Browser E2E Stage (if UI, optional)
  ↓
Designer → UI acceptance review (if UI, max 3 rounds)
  ↓
PM → final acceptance
  ↓
PMO → completion report (knowledge + tech debt + schema/API + PROJECT.md + design sync)
```

## Agile Workflow

```
PMO analysis → identified as agile (≤5 files, no UI/arch changes, clear approach) → ⏸️ User confirms
  ↓
PM → simplified PRD (core requirements + acceptance criteria) → ⏸️ User confirms
  ↓
🔗 BlueprintLite Stage (QA simplified TC + RD implementation plan, main dialog, no reviews)
  ↓
🔗 Dev Stage (RD TDD dev, same as Feature flow)
  ↓
🔗 Review Stage (Architect CR, same as Feature flow)
  ↓
PM → acceptance
  ↓
PMO → completion report
```

## Feature Planning Workflow

```
PMO analysis → identify as Feature Planning → determine scope
  ↓
📁 Sub-project level:
  PM → clarify product goals with user
    ↓
  🤖 Designer → full rebuild of product-wide UI (Subagent, if UI)
    ↓
  ⏸️ User confirms product-wide design
    ↓
  PM → update PROJECT.md
    ↓
  PM → decompose ROADMAP.md (Wave-based batches + parallel execution)
    ↓
  ⏸️ User confirms ROADMAP
    ↓
  Execute each Feature via standard Feature workflow

🌐 Workspace level:
  PM → discuss overall architecture with user
    ↓
  PM → update teamwork_space.md
    ↓
  ⏸️ User confirms workspace architecture
    ↓
  For each affected sub-project → run sub-project level Planning
    ↓
  PMO → finalize teamwork_space.md
    ↓
  ⏸️ User final confirmation
```

## Product Planning & Product Lead

Teamwork includes a built-in product planning system managed by the **Product Lead (PL)** role. When product-level planning or decisions are needed, PMO automatically dispatches PL.

### Product Planning Documents

```
product-overview/
├── {project}_Business_Architecture.md    # Positioning, business flows, revenue model, feature plan
├── {project}_Execution_Handbook.md       # Execution lines, milestones, acceptance criteria
└── {project}_Product_Plan.md             # Optional · external product plan
```

Product planning documents serve as upstream input for Feature Planning and the top-level basis for change cascades.

### Product Lead — Three Modes

**Guided Init**: When `product-overview/` doesn't exist during project initialization, PMO automatically switches to PL guided mode. PL walks the user through building product planning documents from scratch via structured Q&A.

**Discussion Mode**: When the user raises product-direction topics (e.g., adjusting business model, adding/removing business lines), PMO dispatches PL into discussion mode. After reaching consensus, PL writes conclusions to product-overview docs and generates CHG change records.

**Execution Mode**: When discussion conclusions need implementation, PL produces a change impact assessment report, evaluates scope and level. After user confirmation, downstream cascade is triggered:

```
Product Lead assessment → Change level determination
  ├── Level 1 (Feature) → Enter Feature Planning directly
  ├── Level 2 (Module) → Update product-overview → Sub-project Feature Planning
  └── Level 3 (Direction) → Update product-overview → Workspace-level Feature Planning
```

### Change Cascade & Bottom-Up Impact Escalation

During development, if the current Feature conflicts with upstream documents (e.g., existing ROADMAP Features conflict, product architecture needs adjustment), PM/RD triggers **bottom-up impact escalation**. PMO traces upward to find the highest-level document requiring change, PL evaluates, then cascades downward.

## Collaboration Model

### Single-user mode (default)
One user + one AI session operating the entire project. `.teamwork_localconfig.md` scope is for focusing attention, not concurrency control.

### Multi-user mode (experimental)
Multiple users each using independent AI sessions on different sub-projects. Constraints: one session per sub-project at a time, non-overlapping scopes, cross-project coordination by one user.

## Red Lines (Summary)

Full red lines in [SKILL.md](./skills/teamwork/SKILL.md), core 13 points:

1. **PMO write boundary**: Runtime-affecting changes (code/tests/config) → must follow process with full quality gates; documentation changes PMO can make directly with annotation
2. **Six flow types only**: Feature / Bug / Issue Investigation / Feature Planning / Agile / Micro
3. **No unauthorized simplification**: Each requirement follows its full flow; "simple" is not a reason to skip stages
4. **PMO receives all input**: All user input goes through PMO first
5. **Pause points must wait**: Including Micro's user confirmation and acceptance
6. **Closed-loop verification**: "Done" must include actual command output
7. **Pause points must advise**: Recommendations (💡) + rationale (📝) required
8. **Write operation hard gate**: No write operations before PMO initial analysis
9. **No unauthorized pauses**: Auto-transition nodes (🚀) cannot insert questions
10. **PMO pre-check required**: L1/L2/L3 pre-checks before any Subagent dispatch

## License

MIT
