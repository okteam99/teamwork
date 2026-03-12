# Teamwork

Multi-role collaborative development framework for Claude Code.

[中文文档](./README.zh-CN.md)

## Overview

Teamwork simulates **6 specialized roles** — PMO / PM / Designer / QA / RD / Senior Architect — to deliver structured software development workflows inside Claude Code.

Four workflow types are supported:

- **Feature** — Full cycle: requirements → design → development → testing → acceptance
- **Bug Fix** — Investigate → assess → fix → verify → sync docs
- **Issue Investigation** — Root cause analysis with recommended next steps
- **Feature Planning** — Decompose product goals into a prioritized Feature Backlog with dependencies

### Key Features

- **7 Subagent-automated stages**: PRD Review, TC Review, UI Design, Architect TECH Review, TDD Dev + Self-check, Architect Code Review, Integration Testing
- **Multi-role review**: PRD and TC are automatically reviewed from multiple perspectives via Subagent
- **Pause-point control**: Key decision nodes wait for explicit user confirmation
- **Knowledge accumulation**: Lessons learned are captured in KNOWLEDGE.md after each feature
- **TDD-driven development**: Tests are written before implementation code

## Installation

```bash
npx skills add okteam99/teamwork
```

## Usage

```bash
# Start a feature workflow
/teamwork implement user login

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
│       ├── SKILL.md              # Entry point — workflow & state management
│       ├── ROLES.md              # Role definitions & responsibilities
│       ├── RULES.md              # Core rules (pause, flow, Subagent)
│       ├── REVIEWS.md            # Review process specs
│       ├── STANDARDS.md          # Coding & documentation standards
│       ├── TEMPLATES.md          # Document templates (PRD/TC/TECH etc.)
│       └── agents/               # Subagent specs
│           ├── README.md             # Common conventions
│           ├── prd-review.md         # PRD multi-role review
│           ├── tc-review.md          # TC multi-role review
│           ├── ui-design.md          # Designer UI design
│           ├── arch-tech-review.md   # Architect TECH review
│           ├── rd-develop.md         # RD TDD development + self-check
│           ├── arch-code-review.md   # Architect Code Review
│           └── integration-test.md   # QA integration testing
├── README.md
├── README.zh-CN.md
└── .gitignore
```

## Feature Workflow

```
PMO analysis → identify type → switch role
  ↓
PM → PRD
  ↓
🤖 PRD multi-role review (Subagent)
  ↓
⏸️ User confirms PRD
  ↓
🤖 Designer → UI design (Subagent, if UI needed)
  ↓
⏸️ User confirms design
  ↓
QA → TC (test cases)
  ↓
🤖 TC multi-role review (Subagent)
  ↓
RD → technical plan
  ↓
🤖 Architect → TECH review (Subagent)
  ↓
⏸️ User confirms technical plan
  ↓
🤖 RD → TDD development + self-check (Subagent)
  ↓
🤖 Architect → Code Review (Subagent)
  ↓
Designer → UI implementation review (if UI)
  ↓
QA → code review
  ↓
QA → integration test pre-check → 🤖 integration test (Subagent)
  ↓
PM → final acceptance
  ↓
PMO → completion report + knowledge capture
```

## Feature Planning Workflow

```
PMO analysis → identify as Feature Planning
  ↓
PM → clarify product goals
  ↓
PM → decompose into Feature list (P0/P1/P2) + dependencies
  ↓
PM → output BACKLOG.md
  ↓
⏸️ User confirms Backlog
  ↓
Execute each Feature via standard Feature workflow
```

## License

MIT
