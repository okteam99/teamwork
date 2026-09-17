# Teamwork

An AI works from a team-collaboration perspective — through **flow orchestration + perspective switching + contractualized stages + a machine-readable state machine** — to drive the complete software lifecycle from product planning to delivery.

[中文](./README.md) · Version: **v8.360** (version source of truth = [SKILL.md](./skills/teamwork/SKILL.md) frontmatter)

---

## What We Solve

**An AI writing software under weak supervision faces four unavoidable, structural risks** — they do not disappear as models get smarter. Each of Teamwork's four pillars addresses one:

| Fundamental risk | Why it's unavoidable | Teamwork's answer |
|-----------------|---------------------|-------------------|
| **Intent drift** (building the wrong thing) | Information asymmetry: no model, however smart, knows what the user didn't say | Pause points / intent gates (prepare intent check · goal deep gate · panorama user confirmation) |
| **Quality blind spots** (building it badly) | Self-review blindness is mathematical: a model can't see its own gaps | **Isolated cold review · one shared checklist across lanes · a different model per lane** (independent sampling — not a persona swap inside the same context) |
| **State drift** (losing / corrupting things) | Finite context is physical: long flows drift when they rely on memory | Machine-readable state machine + materialized artifact gates + worktree isolation |
| **Knowledge loss** (repeating mistakes) | Every session starts from zero | KNOWLEDGE distillation + cross-project audit harvest feedback loop |

Cross-project audit evidence (as of v8.191 · 163 shipped-feature audits): zero state-machine escapes (bypass 0/163) · 92 real issues caught by review · 32 cases where pause points genuinely reshaped the design · the last ~20 releases were all driven by audit data.

## Premise

Teamwork matches along two dimensions:

**Match the flow to the need**: looking up code, fixing a bug, and building a feature require entirely different collaboration depth. Entry triage (5 modes: query / execute / resume / status / discuss) matches intent to the right flow — simple tasks get a simple flow, complex needs get the full flow.

**Assemble rigor from risk**: the flow is not a fixed ritual — four dimensions get dialed per feature: spec depth (PRD? TECH?) · evidence gate (is there observable behavior?) · verification depth (is dev's own testing enough?) · review rigor (how many lanes × which models). The six named tiers (micro / floor / tiny / lite / medium / full) are only a starting point; after picking one you still re-check every dimension. Every stage boundary is an **explicit revision point** — a fact you didn't have at assembly time changes the plan, and adding rigor costs the same as removing it.

**Independence comes from isolation, not from identity**: drafting and reviewing happen in **separate contexts** (isolated subagents · never fed the drafter's reasoning), and lanes **stagger models**. Each stage has one **shared cold-review checklist** — however many lanes you configure, they all run the full checklist, not a per-role slice (slicing leaves seams nobody owns). Annual audit evidence: direction-checklist review produced **2.1×** the findings of role-focus review, at an 82.3% adoption rate.

You only provide requirements and make decisions at key checkpoints.

### Why Cold Review Works

- **Isolation produces independence**: an AI reviewing what it just drafted fills its own gaps from memory. Review runs in an **independent subagent**, never fed the drafter's reasoning — the blank-slate effect is exactly the point, and it beats "switch persona in the same conversation".
- **Model stagger decorrelates**: lanes use **different models** (at least one ≠ the session's main model). Same model twice = correlated blind spots — both lanes go blind together.
- **The checklist covers; the phrasing confronts**: one checklist per stage, three sections, all mandatory — ⚔️ **Challenge** (must be written as "I tried to prove X false, and the result was…" — ticking a box is not allowed) · 🔍 **Verify** ("checked, nothing found" is a valid answer) · 💡 **Off-checklist insight** (what the checklist didn't ask but you think matters). That last one is the framework's self-discovery channel: historically most real gaps were not on the checklist at the time.
- **Model tier follows the work**: checking against an existing checklist → verification tier; writing out an agreed plan → execution tier; having to come up with what isn't on the checklist → depth tier (PRD / TECH drafting and first-round cold review — never downgraded). If a cheaper model's output wouldn't be worse, there is no reason to pay for the expensive one.

> 📎 Earlier versions produced multiple perspectives by having the main conversation switch personas. **Drafting is still split by specialty** (PM writes the PRD · RD the TECH · QA the TC · Designer the visuals), but **review is no longer sliced by role** — independence comes from isolation and model difference, coverage comes from the checklist.

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

# Small change (lightweight Feature — assembly scales down to the tiny/lite tier)
/teamwork add an export-CSV button to the user list

# Micro preset (zero-logic change — copy / style / asset replacement)
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
| PRD | Wait / correct | PM drafts PRD + N isolated cold-review lanes (one shared checklist) + converge |
| Confirm PRD | Reply ok | — |
| Design | Wait | Designer produces UI + syncs the panorama |
| Tech plan | Wait | RD drafts TECH + QA drafts TC + architect + third-perspective review |
| Dev | Wait | RD implements via TDD + unit tests + machine checks |
| Review | Wait | Architect + QA + **independent third perspective** (default same-model cold review · heterogeneous optional) — three independent reviews |
| Test | Wait (start the app if needed) | QA integration tests + scripted API E2E |
| Acceptance | Reply ok / feedback | PM-perspective acceptance + PMO compiles delivery report + auto-commit |
| **Ship Phase 1** | Click the merge button | Sanitize + knowledge distill + archive (merged atomically with the feature MR) + MR/PR created · user_card with the MR link on top + 📦 delivery summary → **await-merge 30s polling** (auto-advances to Phase 2 once the merge is detected) |
| **Ship Phase 2** | Wait | Zero-content cleanup: verify delivery + worktree cleanup + main-branch sync → ✅ |

Typical Feature pause points: **3-5**.

### What You Do vs What the AI Does (Product-Direction Planning)

The breakdown from business overview to concrete Features — led by PL (Product Lead), orchestrated by PMO, landed by PM.

| Stage | You | AI |
|-------|-----|-----|
| Start | Give a one-line direction (e.g. "build an e-commerce recommender" / "adjust the business model") | PMO recognizes product-direction input · schedules PL |
| Business overview | Answer PL's key questions (users / value / scenarios) | PL guides building product-overview (business architecture + WS breakdown) |
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

## Flow Types — Which One (closed set)

Machine layer: `flow_type ∈ {Feature, Bug}` plus a Feature weight preset `preset ∈ {micro, floor, tiny, lite, medium, full}` (**six tiers — named combinations of the four dimensions**, not six separate flows). Weight is carried by **four-dimension assembly**; a tier is only the starting point — you still re-check each dimension after picking one.

| Flow | Use case | Output | Default pause points |
|------|----------|--------|----------------------|
| **Feature · full** | Feature development (default) | Code + docs + tests | 3-5 |
| **Feature · micro** | Zero-logic change (copy/style/asset/config-constant whitelist · ≤5 files) — skips review/test, still user acceptance + ship | Code (direct edit) | 2 (confirm + acceptance) |
| **Bug** | Defect already identified — **diagnose first** (root cause + fix plan confirmed by user before any fix) | Fix + BUG report + regression tests | 3-4 |
| **Feature Planning** | Break a product goal into a ROADMAP (no code · R6 · not in the state machine) | WS + ROADMAP + panorama | **1** (final summary confirmation only) |
| **Investigation** | Root-cause only, no code output (not in the state machine · investigate-first law) | Investigation report + follow-up todos | 0-1 |

The flow type is identified by the prepare sub-flow at the mode-B entry (evidence-first triage); you only confirm at pause points. Feature / Bug enter the state machine and run the stage chain; Feature Planning / Investigation are executed by PMO in the main conversation.

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

- **`auto_mode`**: the AI handles **stage-to-stage flow** for you — it only auto-accepts + documents "user-decision" pause points (e.g. PRD / UI confirmation, with a `concerns WARN` left for audit); **review work (N isolated cold-review lanes with staggered models) still runs for real**.
- **`yolo` (v8.63 · fully unattended · 🔴 high-risk)**: a superset of `auto_mode` with **zero stops** (even PM acceptance + MR merge are automatic). Enable with `init-feature --yolo [<integration-branch>]` (implies `auto_mode`); switch mid-flow via `state.py set-mode --feature <F> --yolo [<branch>] --reason '...'` (audited — don't raw-write `state.json`).

🔴 **yolo is NOT "simplify / speed up" — it's "heavier review"**: unattended = nobody watching → automated review is the only safety net and must be kept / strengthened, **never weakened**. Every configured review lane **runs for real, none dropped** (lane count comes from assembly · each lane runs the full three-section checklist) · the third perspective is a **model-staggered isolated subagent cold review** (the only form). 🔴 **Merges must land on a `yolo/` isolation branch first**: each feature records its open questions on that branch, confirmed in one pass when the yolo branch merges to its target.

🔴 **Hard gate**: a yolo `merge_target` **must be a non-main branch** (main / master) — auto-merges only land on integration branches like `dev` / `staging` / `integration`; promotion to the main branch stays **human-gated**. Give yolo a dedicated integration branch (e.g. `--yolo yolo/feat-x`) to isolate auto-merged code. Per-feature opt-in (not sticky · passed explicitly each time).

### Specialties and Review

**Process specialties** (drafting side — still split by discipline):

- **PMO** (orchestration): take user input → identify the flow → maintain the state machine → pre-checks and pause points
- **Product Lead (PL)**: product direction. Guided mode (build product-overview from zero) / discussion mode / execution mode (change cascade + Change Request lifecycle)
- **PM**: PRD + structured ACs + final acceptance
- **Designer**: UI fidelity + panorama (sitemap + preview)
- **RD**: TECH drafting + implementation + self-check
- **QA**: TC drafting (AC↔test binding) + integration / API E2E tests

**Review is not sliced by role**: each stage has one shared cold-review checklist, and however many lanes are configured, **all of them run the full checklist**. The `pl` / `external` / `architect` entries in the roster are **lane labels** — they decide where the artifact lands and whether the lane is cross-session isolated, **not what gets checked**. Assembly only dials **lane count × model**.

> Why it changed: slicing by role leaves seams — "is this item PL's or external's?" — and whatever nobody owns gets missed. Annual audit evidence: direction-checklist review produced 2.1× the findings of role-focus review. The **perspectives** (technical soundness, test coverage, …) are still there — as checklist items, not as separate seats.

Orchestration and `state.py` commands always stay with the PMO main conversation; in-stage work is dispatched to subagents as needed (context isolation · review lanes must be isolated).

### Cross-Host Compatibility

| Host | Detection | Instruction file |
|------|-----------|------------------|
| Claude Code | .claude/ | CLAUDE.md |
| Codex CLI | .codex/ | AGENTS.md |
| Gemini CLI | .gemini/ | GEMINI.md |

On session start, `bootstrap.py` performs system maintenance (skeletons / localconfig self-heal / codex agent toml deployment · cleanup of legacy injected blocks and legacy hooks). Since v8.211 it **no longer injects** host instruction files (CLAUDE.md / AGENTS.md / GEMINI.md) — in shared repos the injected block would pollute non-teamwork users; key info (PMO role / worktree discipline / subagent authorization) lives solely in SKILL.md, and bootstrap auto-removes legacy injected blocks.

### Collaboration Model

**Single-user mode (default)**: one user + one AI session operating the entire project. The `scope` in `.teamwork_localconfig.json` is for focusing attention, not concurrency control.

**Multi-user mode (experimental)**: multiple users each operate different sub-projects in independent sessions. Constraints: each sub-project may have only one session at a time; different users must own non-overlapping sub-projects (non-overlapping scope); cross-sub-project needs are coordinated by one user; concurrent development of the same sub-project is not supported.

### Worktree Strategy

**Defaults to `auto`**. The prepare sub-flow creates an isolated worktree for each Feature (`{worktree_root_path}/{Feature-ID}` · default `worktree_root_path=.worktree`); the Dev Stage works inside the worktree; the Ship Stage's second phase cleans up after verifying the merge. `init-feature` materially validates the worktree path convention + cwd. Suited for running multiple Features in parallel while keeping the main branch stable. Configurable in `.teamwork_localconfig.json`.

### Pending-Needs Pool

Items found across Features/sessions that are "out of current scope but should be done" are recorded in `product-overview/PENDING.md` (externalized from teamwork-space.md · read only when a backlog query hits). When the user asks "what else is pending / backlog", PMO lists them automatically; once turned into a Feature/Bug, the entry is removed from the pool, keeping it lightweight.

### Product Planning System

Teamwork has a built-in **Product Lead (PL)** role that maintains the product-planning docs:

```
product-overview/
├── {项目名}_业务架构与产品规划.md          # business architecture & product planning (files are generated with Chinese names)
├── workstream/                             # WS-NN.md · planning units (the core)
└── {项目名}_Product_Plan.md                # optional
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

When tasks are executed directly in the main conversation (PRD discussion, integrating and revising the plan, environment setup), artifacts **must be written to disk with the standard YAML frontmatter** — audited on the same footing as subagent output. 🔴 **Review is not one of them** — cold review always runs in an isolated subagent: self-review in the main conversation means the same context and therefore no independence (a framework red line, enforced by a machine gate).

### The Cold-Review Checklist (one per stage · every lane runs it)

Three sections, all mandatory, each gated by machine checks:

- ⚔️ **Challenge**: must be phrased as "I tried to prove ⟨X⟩ false, and the result was…" — **ticking a box is not allowed**. Neutral verification flattens challenge items into checkmarks (evidence: the role was always there, yet "is this constraint actually required?" stayed a blind spot — because it was never written as a question).
- 🔍 **Verify**: feasibility / testability / test authenticity / code-quality blind spots — each lane declares its `coverage`, and "checked, nothing found" is a valid answer.
- 💡 **Off-checklist insight**: what the checklist didn't ask but you think matters (≥1, or an explicit "none + why"). **Never padding**.

The artifact is a **single REVIEW.md** (frontmatter lists `reviewers` / `review_models` / `coverage` / `outside_checklist_insight` per lane, plus a machine-readable findings ledger); the external lane's cold-review output lands separately under `external-cross-review/*.md`.

🔁 **Verification rounds are scope-locked** (Round 2+): only re-adjudicate last round's open findings plus knock-on effects at the revision sites — **no full re-scan**. New findings must originate from the revision sites, or be BLOCKER-level with an explicit "why round 1 missed this". This is what keeps multi-round review from mining edge cases into "problems".

### fix-retry Loop

When review / test fails, it retries within the stage (RD fixes the code → re-review / re-run), without switching stages; the audit keeps `rounds[]` recording the full loop. It advances to the next stage only when it finally passes.

### ADR Decision Records

When a discussion triggers one of the three questions (Why / Options / Tradeoff) and a non-trivial decision is made, an ADR is automatically written to `{subproject}/docs/adr/` (**the only location** — never inside the Feature directory). PMO scans relevant ADRs at the goal/blueprint entry and injects the context, preventing old decisions from being forgotten and re-debated.

### KNOWLEDGE 4-Category Convergence

The project-level `project-specs/KNOWLEDGE.md` (AI-distilled) has four categories: **Gotchas** (pitfalls) / **clarified ambiguities** / **user preferences** / **rejected directions**. Each has a hard trigger timing (e.g. write a Gotcha after debugging, record an ambiguity once clarified) — not relying on self-discipline, so the same pitfall isn't hit again. Division of labor: development rules go to `project-specs/DEV-RULES.md` (human-maintained) · architecture lands in ADR / ARCHITECTURE · retrospectives live separately in `retros/`.

### Ship Stage

**Phase 1 (inside the worktree · full delivery)**: sanitize commits → **knowledge distill** (graduate "code-describing" knowledge into the knowledge layer — KNOWLEDGE / ADR / REG / ARCHITECTURE / database-schema) → **archive** (feature-dir archival + planning status flip · a single commit merged atomically with the feature MR) → push branch → create MR via CLI → emit the user_card (MR link on top) + 📦 delivery summary → **await-merge 30s polling** (runs in every mode · detects MERGED and auto-advances to Phase 2).

**Phase 2 (ship-finalize · main worktree · zero-content cleanup)**: verify-delivered (confirm the delivery landed) → remove worktree → pull-sync the main branch · mark state.json completed.

MR/PR is actually created by PMO via the `gh` / `glab` CLI with a real link · when the CLI is unavailable, a URL is generated from the platform template as a fallback + the user is prompted to click manually.

The PM acceptance pause point is 3-way: ① pass + Ship (auto-enter Ship Stage) ② pass but don't Ship ③ fail + dispatch a fix.

### Project Diagnostic Toolkit — TROUBLESHOOTING.md

When teamwork mode A query / E · discuss touches "diagnose / error / check logs / check the environment", PMO automatically reads `project-specs/TROUBLESHOOTING.md`:

- **Fixed path**: `{project}/project-specs/TROUBLESHOOTING.md` (bootstrap auto-creates an empty skeleton · legacy files scattered at the project root are migrated in automatically)
- **teamwork provides a template**: [templates/troubleshooting.md](./skills/teamwork/templates/troubleshooting.md) (4-section minimal skeleton: environment / check logs / check data & cache / common errors + safety constraints + maintenance)
- **Content distilled by user and AI together**: teamwork doesn't assume a tech stack (K8s vs Docker vs Serverless) · doesn't prescribe specific commands
- Complementary to [KNOWLEDGE.md](./skills/teamwork/templates/knowledge.md): KNOWLEDGE = pitfalls to watch · TROUBLESHOOTING = operational steps

### Third-Perspective Review — Read-Only

Cold-review lanes in teamwork are **read-only** · they have no code-write authority (red line R1):

- Every review lane is an **isolated subagent**, with **models staggered across lanes** (at least one ≠ the session's main model); independent sampling exposes same-model self-review blind spots
- Review lanes produce markdown artifacts only · they do not modify code
- 📎 **Cross-vendor CLI heterogeneity (codex / gemini) has been retired**: cold starts, slow security-review paths and login failure modes slowed the flow badly, while same-vendor model stagger already delivers the independence benefit

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
| **R2** Flow-type closed-set | `{Feature, Bug}` + preset `{micro, floor, tiny, lite, medium, full}` + non-state-machine Planning / Investigation · no self-invented variants |
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
| [FLOWS.md](./skills/teamwork/FLOWS.md) | Flow closed-set telos (Feature/Bug × preset + 2 outside the state machine) and use cases |
| [STAGES.md](./skills/teamwork/STAGES.md) | 11-stage index + common cite discipline |
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

Currently **v8.360** (version source of truth = [SKILL.md](./skills/teamwork/SKILL.md) frontmatter). Changelog in [docs/CHANGELOG.md](./skills/teamwork/docs/CHANGELOG.md) (latest 5 versions) · older history via git log (CHANGELOG-ARCHIVE is **periodically wiped**).

---

## License

MIT
