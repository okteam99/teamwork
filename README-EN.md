# Teamwork

An AI works from a team-collaboration perspective — through **flow orchestration + role-perspective switching + contractualized stages + a machine-readable state machine** — to drive the complete software lifecycle from product planning to delivery.

[中文](./README.md) · Version: **v8.183** (version source of truth = [SKILL.md](./skills/teamwork/SKILL.md) frontmatter)

---

## Premise

Teamwork matches along two dimensions:

**Match the flow to the need**: looking up code, fixing a bug, and building a feature require entirely different collaboration depth. Entry triage (5 modes: query / execute / resume / status / discuss) matches intent to the right flow — simple tasks get a simple flow, complex needs get the full flow.

**Assign roles by specialty**: when a single role covers multiple perspectives, they mask each other — PM's "what the user wants" buries QA's "edge cases"; the architect's "elegance" buries RD's "delivery deadline". Teamwork assigns by specialty: PM / Architect / QA / RD / Designer each own one dimension (requirements / architecture / testing / implementation / UX), with PMO orchestrating. Each artifact is examined from its corresponding professional angle, exposing blind spots to another perspective.

You only provide requirements and make decisions at key checkpoints.

### How Multi-Role Switching Works

- **Create-critique loop**: PM writes PRD → PL critiques from business direction → PM revises. A single role's single-pass output skips blind spots masked by its own perspective.
- **Attention reallocation**: switching roles = switching checklists = activating different evaluation dimensions
- **Forced re-read**: a role switch forces the AI to re-read the same document with new questions, surfacing far more than "think again"
- **Heterogeneous-model review**: review brings in a heterogeneous model for an independent pass (when claude is the main window, external = codex automatically, and vice versa) — a cross-model perspective exposes same-model self-review blind spots

---

## Getting Started

### Install

```bash
# Auto-detects the host environment (Claude Code / Codex CLI / Gemini CLI)
npx skills add okteam99/teamwork
```

### Upgrade

```bash
npx skills update okteam99/teamwork
```

### Start a Flow

```bash
# Feature (full requirement → design → dev → test → acceptance → delivery)
/teamwork implement user login

# Small change (Agile: ≤5 files, clear plan, no UI/architecture change)
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

### What You Do vs What the AI Does (Product Iteration)

| Stage | You | AI |
|-------|-----|-----|
| Start | Give a one-line requirement | PMO initial analysis + flow-type identification + full step description |
| Confirm flow | Reply ok / feedback | Read the necessary knowledge-base docs · start the flow |
| PRD | Wait / correct | PM drafts PRD + multi-role parallel review + converge |
| Confirm PRD | Reply ok | — |
| Design | Wait | Designer produces UI + syncs sitemap |
| Tech plan | Wait | RD drafts TECH + QA drafts TC + architect + heterogeneous-model review |
| Dev | Wait | RD implements via TDD + unit tests + machine checks |
| Review | Wait | Architect + QA + **heterogeneous model (e.g. codex / claude)** — three independent reviews |
| Test | Wait (start the app if needed) | QA integration tests + scripted API E2E |
| Acceptance | Reply ok / feedback | PM-perspective acceptance + PMO compiles delivery report + auto-commit |
| **Ship Phase 1** | Click the merge button | Knowledge distill + MR/PR created · link given → ⏸️ await merge |
| **Ship Phase 2** | Wait | Verify merge + wrap-up via MR (terminal state + process artifacts archived as zip) + worktree cleanup + main-branch sync → ✅ |

Typical Feature pause points: **3-5**.

### What You Do vs What the AI Does (Product-Direction Planning)

The breakdown from business overview to concrete Features — led by PL (Product Lead), orchestrated by PMO, landed by PM.

| Stage | You | AI |
|-------|-----|-----|
| Start | Give a one-line direction (e.g. "build an e-commerce recommender" / "adjust the business model") | PMO recognizes product-direction input · schedules PL |
| Business overview | Answer PL's key questions (users / value / scenarios) | PL guides building product-overview (business architecture + execution handbook) |
| Confirm overview | Reply ok / correct | PL lands the product-overview/ docs |
| Direction discussion | Raise topics (add/remove business lines / business-model change) | PL discussion mode: multi-perspective analysis + options + recommendation |
| Decide direction | Choose a direction | PL enters execution mode · determines change level (function / business module / direction) |
| ROADMAP breakdown | Wait / correct | PMO orchestrates the ROADMAP breakdown (business line → module → Feature list) |
| Confirm ROADMAP | Reply ok | PMO lands ROADMAP.md + sitemap.md |
| Pick a Feature | Specify the next Feature | PMO transitions into the Feature flow (enters the "Product Iteration" table) |
| Feature completion feedback | Wait | PMO auto-writes back ROADMAP status + updates sitemap |

Typical direction-planning pause points: **1-3** (overview confirmation + direction decision + ROADMAP confirmation).

---

## 5-Mode Entry Triage

The teamwork entry is PMO's main-conversation **5-mode triage** — it looks only at user input to decide the minimal path:

| Mode | Trigger | Behavior |
|------|---------|----------|
| **A · query** | "look / investigate / explain / why / diagnose" + no action verb | Directly grep / Read + answer + follow-up guidance · no stage chain |
| **B · execute** | "implement / fix / create / change" + a clear action | Enter the prepare sub-flow → flow-type identification → business stage chain |
| **C · resume** | "continue F032 / ship F032" | Find state.json + jump to current_stage |
| **D · status** | `/teamwork` (empty command) / "where are we" | Load the Feature board + output |
| **E · discuss** | "I feel / what do you think / X vs Y / suggest / which is better" | Multi-perspective discussion + options + recommendation + ask → escalate mode after the user decides |

**Principle**: start on demand · pick the right flow for the goal.

## 6 Flow Types — Which One

| Flow | Use case | Output | Default pause points |
|------|----------|--------|----------------------|
| **Feature** | Full feature development | Code + docs + tests | 3-5 |
| **Agile requirement** | ≤5 files + clear plan + no UI/architecture change | Code + simplified docs + tests | 2-3 |
| **Micro** | Zero-logic change (copy/style/asset/config constant/doc comment) | Code (direct edit) | 2 (confirm + acceptance) |
| **Bug** | Production/local defect | Fix + BUG report + regression tests | 3-4 |
| **Feature Planning** | Break a product goal into a ROADMAP | PROJECT.md + ROADMAP.md + sitemap.md | **1** (final summary confirmation only) |
| **Investigation** | Root-cause only, no code output | Investigation report + follow-up todos | 0-1 |

The flow type is identified automatically by the prepare sub-flow at the mode-B entry; you only confirm at pause points. Feature / Agile / Bug / Micro enter the state machine and run the stage chain; Feature Planning / Investigation do not enter the state machine and are executed by PMO in the main conversation.

---

## Advanced Usage

### Flow Control

```bash
# View current state (which step / what's next / pending decisions)
/teamwork status

# Resume an interrupted flow (recoverable after a new conversation / compaction, via state.json)
/teamwork continue
```

Pause-point options are numbered (💡 recommended item first, the last option is always "other instructions") — **just reply with a digit**, no typing. Multi-decision combos are supported (e.g. `1A 2B`). Global shortcuts: `ok` = take the recommendation, `all default` = use all defaults.

### Automation levels: auto_mode / yolo

By default teamwork **stops at every user-decision pause point** for your confirmation. Two opt-in levels raise the automation:

- **`auto_mode`**: the AI handles **stage-to-stage flow** for you — it only auto-accepts + documents "user-decision" pause points (e.g. PRD / UI confirmation, with a `concerns WARN` left for audit); **review work (multi-role + heterogeneous model) still runs for real**.
- **`yolo` (v8.63 · fully unattended · 🔴 high-risk)**: a superset of `auto_mode` with **zero stops** (even PM acceptance + MR merge are automatic). Enable with `init-feature --yolo [<integration-branch>]` (implies `auto_mode`); switch mid-flow via `state.py set-mode --feature <F> --yolo [<branch>] --reason '...'` (audited — don't raw-write `state.json`).

🔴 **yolo is NOT "simplify / speed up" — it's "heavier review"**: unattended = nobody watching → automated review (especially **external heterogeneous cross-review**) is the only safety net and must be kept / strengthened, **never weakened**. Zero-stop applies **only** to human-decision points (prepare / pm_acceptance / MR merge); every stage's review roles, the real heterogeneous external-model call (**verified via real run logs — can't be faked**), and test rounds all run in full. Failures / blockers / exhausted retries / bypass are **resolved autonomously by the AI** (priority: resolve > bypass; bypass is a last resort after exhausting fixes, always WARN-logged — `bypass_log` frequency = yolo health).

🔴 **Hard gate**: a yolo `merge_target` **must be a non-main branch** (main / master) — auto-merges only land on integration branches like `dev` / `staging` / `integration`; promotion to the main branch stays **human-gated**. Give yolo a dedicated integration branch (e.g. `--yolo yolo/feat-x`) to isolate auto-merged code. Per-feature opt-in (not sticky · passed explicitly each time).

### Role System

- **PMO** (flow orchestration): accept user input → identify flow → schedule roles → maintain the state machine → pre-checks and pause points
- **Product Lead (PL)**: product direction. Onboarding mode (build product-overview from scratch) / discussion mode (business topics) / execution mode (change cascade + Change Request lifecycle)
- **PM**: PRD + structured AC + final acceptance
- **Designer**: UI restoration + sitemap (sitemap + preview)
- **Architect**: Tech Review (Blueprint) + Code Review (Review Stage) + ARCHITECTURE.md maintenance + ADR decisions
- **QA**: TC (AC↔test binding) + TC tech review (Blueprint) + Code Review + integration tests / API E2E
- **RD**: TDD implementation + unit tests + self-check + bug investigation report
- **External Reviewer**: heterogeneous-model code review (codex / claude · independent-stance hard constraint)

Role collaboration **defaults to main-conversation identity switching** — switching roles = switching checklists + forced re-read; PMO may dispatch a subagent on demand to execute tasks within a stage (context isolation · especially useful on small-context-window hosts), while stage orchestration and state.py commands always stay with the PMO main conversation.

### Cross-Host Compatibility

| Host | Detection | Instruction file |
|------|-----------|------------------|
| Claude Code | .claude/ | CLAUDE.md |
| Codex CLI | .codex/ | AGENTS.md |
| Gemini CLI | .gemini/ | GEMINI.md |

On session start, `bootstrap.py` automatically maintains the teamwork injection section of the corresponding instruction file per host.

### Collaboration Model

**Single-user mode (default)**: one user + one AI session operating the entire project. The `scope` in `.teamwork_localconfig.json` is for focusing attention, not concurrency control.

**Multi-user mode (experimental)**: multiple users each operate different sub-projects in independent sessions. Constraints: each sub-project may have only one session at a time; different users must own non-overlapping sub-projects (non-overlapping scope); cross-sub-project needs are coordinated by one user; concurrent development of the same sub-project is not supported.

### Worktree Strategy

**Defaults to `auto`**. The prepare sub-flow creates an isolated worktree for each Feature (`{worktree_root_path}/{Feature-ID}` · default `worktree_root_path=.worktree`); the Dev Stage works inside the worktree; the Ship Stage's second phase cleans up after verifying the merge. `init-feature` materially validates the worktree path convention + cwd. Suited for running multiple Features in parallel while keeping the main branch stable. Configurable in `.teamwork_localconfig.json`.

### Pending-Needs Pool

Items found across Features/sessions that are "out of current scope but should be done" are recorded in the pending-needs pool in the project-root `teamwork-space.md`. When the user asks "what else is pending / backlog", PMO lists them automatically; once turned into a Feature/Bug, the entry is removed from the pool, keeping it lightweight.

### Product Planning System

Teamwork has a built-in **Product Lead (PL)** role that maintains the product-planning docs:

```
product-overview/
├── {project}_business-architecture-and-product-plan.md
├── {project}_execution-handbook.md
└── {project}_Product_Plan.md              # optional
```

When a project is first initialized and `product-overview/` does not exist, PMO automatically switches to PL onboarding mode. For product-direction topics (business-model adjustments, adding/removing business lines), PMO schedules PL into discussion mode. When a conclusion needs to land, PL enters execution mode and triggers a downstream cascade into Feature Planning based on the change level (Level 1 function / Level 2 business module / Level 3 direction).

If, during development, the current Feature is found to conflict with upstream docs (e.g. a conflicting Feature already in the ROADMAP, or the product architecture needs adjustment), a **bottom-up impact escalation** is triggered: PMO traces upward to the highest-level document that needs to change, then PL evaluates and cascades back down.

---

## Core Guarantees (Quality Mechanisms)

The mechanisms below form the foundation of Teamwork's quality assurance. Each section describes the mechanism itself and the specific problem it targets.

### Contractualized Output

Every Stage file is unified into a **prerequisites (entry checks) / artifacts (output shape) / evidence_checks (completion evidence)** contract. It specifies **where to go** (output contracts), not **how to get there** (execution mode decided by the AI based on scale/complexity). The shape of each stage's output is locked, so downstream isn't blocked by a sloppy previous step.

### Machine-Verifiable — AC↔Test Strong Binding

The YAML frontmatter of PRD.md and TC.md is machine-readable; `acceptance_criteria[].id` ↔ `tests[].covers_ac` are one-to-one bound. The `verify-ac.py` script auto-validates coverage completeness, eliminating "requirement → code" drift.

### Main-Conversation Artifact Protocol

When tasks are executed directly in the main conversation (PRD discussion, architect review, env setup), artifacts **must be written to disk per the YAML frontmatter spec**. Whichever role perspective produced it, the artifact is treated equally at audit time — nothing gets lost just because it was "discussed in the main conversation".

### Multi-Perspective Review

- **Architect**: technical soundness / performance / security / architecture consistency
- **QA**: AC item-by-item check against the implementation / test coverage / edge cases
- **Heterogeneous model (External)**: a cross-model independent review (when claude is the main window, external = codex, and vice versa), run once

The three artifacts are **structurally independent** (each written to its own REVIEW-{role}.md / no cross-reference), machine-verifiable, avoiding the "the last review already said it's fine, so don't look closely" applause effect.

### fix-retry Loop

When review / test fails, it retries within the stage (RD fixes the code → re-review / re-run), without switching stages; the audit keeps `rounds[]` recording the full loop. It advances to the next stage only when it finally passes.

### ADR Decision Records

When a discussion triggers one of the three questions (Why / Options / Tradeoff) and a non-trivial decision is made, an ADR is automatically written to `{Feature}/adrs/`. PMO scans relevant ADRs at the goal/blueprint entry and injects the context, preventing old decisions from being forgotten and re-debated.

### KNOWLEDGE 3-Category Convergence

The project-level `KNOWLEDGE.md` has three categories: **Gotcha** (pitfalls) / **Convention** / **Architecture** (architecture fragments). Each has a hard trigger timing (e.g. write a Gotcha after debugging, a Convention after Review) — not relying on self-discipline, so the same pitfall isn't hit again. Retrospectives are separated from KNOWLEDGE into `retros/`.

### Ship Stage

**Phase 1 (inside the worktree)**: sanitize commits → **knowledge distill** (graduate "code-describing" knowledge into the knowledge layer — KNOWLEDGE / ADR / REG / ARCHITECTURE / database-schema — reviewed + merged with the feature MR) → push branch → create MR via CLI → ⏸️ user merges on the platform.

**Phase 2 (main worktree · fully automatic · re-entrant)**: verify merge → **wrap-up via MR** (no direct push · protected-branch friendly · auto-merged via gh/glab) → **archive** (the process-layer feature dir is zipped into `features/_archive/<id>.zip` and the original dir removed from the main branch — prevents the AI from retrieving stale feature info · code is the single source of truth) → remove worktree → pull-sync the main branch · mark state.json completed.

MR/PR is actually created by PMO via the `gh` / `glab` CLI with a real link · when the CLI is unavailable, a URL is generated from the platform template as a fallback + the user is prompted to click manually.

The PM acceptance pause point is 3-way: ① pass + Ship (auto-enter Ship Stage) ② pass but don't Ship ③ fail + dispatch a fix.

### Project Diagnostic Toolkit — TROUBLESHOOTING.md

When teamwork mode A query / E · discuss touches "diagnose / error / check logs / check the environment", PMO automatically reads the project-root `TROUBLESHOOTING.md`:

- **Fixed path**: project-root `TROUBLESHOOTING.md` (teamwork doesn't look in docs/ · handled like teamwork-space.md)
- **teamwork provides a template**: [templates/troubleshooting.md](./skills/teamwork/templates/troubleshooting.md) (4-section minimal skeleton: environment / check logs / check data & cache / common errors + safety constraints + maintenance)
- **Content maintained by the user**: teamwork doesn't assume a tech stack (K8s vs Docker vs Serverless) · doesn't prescribe specific commands
- **When absent**: PMO gives a one-line prompt to create it from the template (no forcing / no blocking · continues diagnosing with general methods)
- Complementary to [KNOWLEDGE.md](./skills/teamwork/templates/knowledge.md): KNOWLEDGE = pitfalls to watch · TROUBLESHOOTING = operational steps

### External Models — Review-Only

External models codex / claude / gemini are used in teamwork **for read-only review only** · they have no code-write authority (red line R1):

- Review brings in a heterogeneous model for an independent pass; the cross-model perspective exposes same-model self-review blind spots
- External models run read-only · produce only markdown review artifacts · do not modify code

### Evidence-Binding Materialized Interception

Factual fields (mr_url / feature_head_commit / test_exit_code, etc.) must be backed by evidence (command + stdout + exit_code):

- **Interception layer = state.json schema integrity**: when PMO writes a factual field to state.json, it can't go by memory (fabrication won't match the real command format · spot-checked by user/PM)
- **State fields vs factual fields** are clearly delineated: current_stage / phase / verdict are state fields (PMO judges them · no evidence needed) · stdout / mr_url are factual fields (externally observed · evidence required)
- `state.json` carries `_state_checksum` self-protection; writing state.json directly across hosts is physically intercepted

### State Recovery

`{Feature}/state.json` is the **single source of truth** for flow state. After a new conversation / compaction / session restart, reading `state.json` restores everything — no reliance on conversation memory.

### Closed-Loop Verification

RD/QA claims of "done" must include actual command output (test/build results); PMO completion reports must cite real data; empty "done" statements are forbidden. All degradation paths (external model unavailable, worktree unavailable, etc.) must emit structured WARN logs; silent degradation is a violation of the closed-loop verification red line.

### Prompt-Cache Friendly

Docs are organized in a 4-layer model (L0 framework / L1 project / L2 Feature / L3 dynamic), strictly separating stable and dynamic layers; the Stage-entry Read order is fixed and state.json access count is limited, reducing the AI's repeated thinking across stages / Features — the same Feature workflow costs noticeably less and has lower latency on the next push.

### Absolute Red Lines (9 · R1-R9)

Teamwork's 9 core red lines — 8 of them materially enforced by the `state.py` state machine (enumerable rules go into code), and 1 (R3 PMO unified intake) a soft rule in PMO's main conversation.

| Red line | Content (one-liner) |
|----------|---------------------|
| **R1** Code-write authority to RD | Code / tests / build config executed by the RD role; external models review-only |
| **R2** Flow-type closed-set | 6 flows: Feature / Bug / Micro / Agile / Feature Planning / Investigation · no self-invented variants |
| **R3** PMO unified intake | All user input is taken by PMO first · no other role responds directly |
| **R4** Flow boundary | No simplification (no skipping stages) / no inflation (no inserting pauses at auto-advance nodes) / must give step description |
| **R5** Pause-point protocol | Must await user confirmation + give 💡 recommendation + numbered (single decision 1/2/3 · multi-decision 1A 2B) |
| **R6** Planning produces docs only | No code · no auto-starting a Feature flow |
| **R7** Evidence closure | Claiming done requires commit + actual output; factual fields evidence-bound |
| **R8** Write-op hard gate chain | Reject stage-start before prepare is done · Ship Phase 1 CLI-first |
| **R9** Session bootstrap | Entry must run bootstrap.py + PMO 5-mode triage |

Full red-line text in [SKILL.md](./skills/teamwork/SKILL.md) (current authority).

---

## Documentation Map

| File | Purpose |
|------|---------|
| [SKILL.md](./skills/teamwork/SKILL.md) | Main entry: design philosophy + command list + Triage entry spec + 9 red lines + project-level doc architecture |
| [FLOWS.md](./skills/teamwork/FLOWS.md) | 6 flow types — telos and use cases |
| [STAGES.md](./skills/teamwork/STAGES.md) | 12-stage index + common cite discipline |
| [ROLES.md](./skills/teamwork/ROLES.md) | Role index (→ roles/*.md) |
| [STANDARDS.md](./skills/teamwork/STANDARDS.md) | Technical standards index (→ standards/*.md) |
| [TEMPLATES.md](./skills/teamwork/TEMPLATES.md) | Document template index |
| [docs/prepare.md](./skills/teamwork/docs/prepare.md) | mode B → preparation sub-flow before entering the state machine |
| [docs/feature-planning.md](./skills/teamwork/docs/feature-planning.md) | Feature Planning flow guide (not in the state machine) |
| [docs/conventions.md](./skills/teamwork/docs/conventions.md) | Feature ID + worktree path naming conventions |
| [stages/*.md](./skills/teamwork/stages/) | Each stage's Telos + Output Contract |
| [roles/*.md](./skills/teamwork/roles/) | Role telos + authoring guidelines |
| [standards/*.md](./skills/teamwork/standards/) | Technical standards (common / backend / frontend / tdd, etc.) |
| [tools/state.py](./skills/teamwork/tools/state.py) | The sole orchestrator entry |
| [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) | Latest 5 versions (older history via git log) |

For the detailed directory structure see [skills/teamwork/](./skills/teamwork/).

---

## Version

Currently **v8.183** (version source of truth = [SKILL.md](./skills/teamwork/SKILL.md) frontmatter). Changelog in [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) (latest 5 versions) · older history via git log (CHANGELOG-ARCHIVE is **periodically wiped**).

---

## License

MIT
