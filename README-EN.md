# Teamwork

Multi-role collaborative development framework for Claude Code.

[中文文档](./README.md)

## Overview

Teamwork simulates **7 specialized roles** — PMO / Product Lead / PM / Designer / QA / RD / Senior Architect — to deliver structured software development workflows inside Claude Code.

Four workflow types are supported:

- **Feature** — Full cycle: requirements → design → development → testing → acceptance
- **Bug Fix** — Investigate → assess → fix → verify → sync docs
- **Issue Investigation** — Root cause analysis with recommended next steps
- **Feature Planning** — Decompose product goals into a prioritized ROADMAP with Wave-based execution batches and dependency tracking

### Key Features

- **9 Subagent-automated stages**: PL-PM Discussion, PRD Review, TC Review, UI Design, Architect TECH Review, TDD Dev + Self-check, Architect Code Review, QA Code Review, Integration Testing
- **PL-PM Teams Discussion**: After PM drafts the PRD, PL and PM engage in multi-round Agent-based discussion to converge and finalize the PRD before review
- **Product Lead role**: Three modes — Guided Init (build product-overview from scratch), Discussion (product direction with CHG records), Execution (cascade changes across sub-projects)
- **Multi-role review**: PRD and TC are automatically reviewed from multiple perspectives via Subagent
- **Product-wide UI design**: design/sitemap.md + design/preview/overview.html as single source of truth for product UI
- **Change cascade**: 3-level impact assessment (L1 Feature / L2 Module / L3 Direction) with bottom-up escalation
- **Multi-project mode**: teamwork_space.md orchestrates multiple sub-projects with business / midplatform types and cross-project dependency tracking
- **Midplatform sub-project support**: midplatform-type sub-projects automatically trigger consumer analysis, compatibility review, and enhanced evaluation processes
- **Feature status tracking**: STATUS.md in each Feature directory serves as single source of truth for status; PMO auto-updates on every stage transition
- **Pause-point control**: Key decision nodes wait for explicit user confirmation
- **Knowledge accumulation**: Lessons learned are captured in KNOWLEDGE.md after each feature
- **TDD-driven development**: Tests are written before implementation code
- **State recovery**: Sessions can resume from interruption by checking document states

## Installation

```bash
npx skills add okteam99/teamwork
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

# Check current status
/teamwork pmo

# Exit teamwork mode
/teamwork exit
```

## File Structure

```
teamwork/
├── skills/
│   └── teamwork/
│       ├── SKILL.md              # Entry point — workflow, state, red lines
│       ├── ROLES.md              # Role definitions (PMO/PL/PM/Designer/QA/RD/Architect)
│       ├── RULES.md              # Core rules (pause, flow, Subagent, change handling)
│       ├── REVIEWS.md            # Review process specs (PRD/TC/UI acceptance)
│       ├── STANDARDS.md          # Coding standards index
│       ├── TEMPLATES.md          # Document templates (PRD/TC/TECH/ROADMAP etc.)
│       ├── agents/               # Subagent specs
│       │   ├── README.md             # Common conventions
│       │   ├── pl-pm-discuss.md      # PL-PM collaborative discussion (Teams mode)
│       │   ├── prd-review.md         # PRD multi-role review
│       │   ├── tc-review.md          # TC multi-role review
│       │   ├── ui-design.md          # Designer UI design (incremental + full rebuild)
│       │   ├── arch-tech-review.md   # Architect TECH review
│       │   ├── rd-develop.md         # RD TDD development + self-check
│       │   ├── arch-code-review.md   # Architect Code Review + arch doc update
│       │   ├── qa-code-review.md     # QA code review (read code + TC verification)
│       │   └── integration-test.md   # QA integration testing
│       └── standards/            # Coding standards by tech stack
│           ├── common.md             # Shared: TDD checklist, architecture, self-check
│           ├── backend.md            # Backend: TDD, API, logging, DB migration
│           └── frontend.md           # Frontend: test layers, E2E, component testing
├── README.md                     # Chinese documentation (default)
├── README-EN.md                  # English documentation
└── .gitignore
```

## Feature Workflow

```
PMO analysis → identify type → switch role
  ↓
PM → PRD draft
  ↓
🤖 PL-PM Teams discussion (Subagent: PL review + PM response, multi-round convergence) → PRD finalized
  ↓
🤖 PRD multi-role review (Subagent: RD / Designer / QA / PMO perspectives)
  ↓
⏸️ User confirms PRD
  ↓
🤖 Designer → UI design (Subagent, if UI needed) + sync product-wide design
  ↓
⏸️ User confirms design
  ↓
QA → TC (BDD/Gherkin format)
  ↓
🤖 TC multi-role review (Subagent: PM / RD / Designer perspectives)
  ↓
RD → technical plan
  ↓
🤖 Architect → TECH review (Subagent)
  ↓
⏸️ User confirms technical plan (complex solutions only)
  ↓
🤖 RD → TDD development + self-check (Subagent)
  ↓
🤖 Architect → Code Review + architecture doc update (Subagent)
  ↓
Designer → UI implementation review (if UI, max 3 rounds)
  ↓
🤖 QA → code review (Subagent: read code + TC verification)
  ↓
QA → integration test pre-check → 🤖 integration test (Subagent)
  ↓
PM → final acceptance
  ↓
PMO → completion report (knowledge + tech debt + schema/API + PROJECT.md + design sync)
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

## License

MIT
