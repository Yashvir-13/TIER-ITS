# Teamwork agent teams (/teamwork-preview)

The `/teamwork-preview` command runs a collaborative multi-agent team designed for large software projects, complex simulations, and deep research tasks. When work spans multiple days, involves refactoring across dozens of files, or tackles open-ended math and systems challenges, Teamwork coordinates specialized agents to deliver thoroughly tested, working results.

* * *

## Overview

Software engineering and scientific research often run into problems that are simply too large or complex for a single agent session to handle reliably:

1.  **Large-scale refactoring & migrations**: Upgrading frameworks, modernizing legacy APIs, or changing dozens of files across coupled subsystems.
2.  **Systems research and simulation**: Building complex systemsâ€”like cycle-accurate CPU simulators, distributed consensus engines, or kernel subsystemsâ€”that require continuous testing against hardware oracles.
3.  **Mathematical proofs & research**: Exploring theoretical proofs, deriving mathematical bounds, and running automated counterexample searches.
4.  **Long-running projects without context bloat**: Breaking large tasks into modular milestones where agents coordinate through clean artifact handoffs instead of overloading a single conversation context.

Teamwork solves this by pairing specialized agents together, running independent verification checks at every milestone, and working inside isolated project directories.

* * *

## Multi-agent architecture and roles

Teamwork organizes multi-agent collaboration into clear orchestration, implementation, and verification tiers:

![Teamwork Multi-Agent Architecture](/assets/image/blog/teamwork-multi-agent-architecture.svg)

### Core orchestration and execution roles

*   **Sentinel**: The coordinator that takes over once you approve the prompt. Sentinel records your request, routes tasks, posts periodic progress updates, and spawns the [Success Auditor](#adversarial-verification-gates) before wrapping up.
*   **Project Orchestrator**: A dedicated manager spawned to run the project. It breaks the approved brief into structured milestones, coordinates parallel work tracks, delegates every unit of work, and hands off to a fresh successor between milestones to prevent context degradation.
*   **Explorers**: Read-only research agents that explore the repository, trace call chains from entry points, and evaluate candidate solutions without modifying any source files.
*   **Workers**: Implementation agents equipped with terminal and file tools to build components, refactor code, and write unit tests in focused, non-overlapping tracks.

### Adversarial verification gates

To catch bugs early and ensure code actually works, candidate changes must pass independent verification checks before a milestone is approved:

*   **Critic**: Performs independent code reviews, evaluating correctness, logical completeness, robustness, interface conformance, and adherence to project code style.
*   **Challenger**: Actively stress-tests the code by building adversarial test suites, edge cases, failure-path probes, and worst-case inputs that stress runtime and memory.
*   **Auditor**: Validates work against the selected integrity mode and checks test evidence against real command output, ensuring tests genuinely passed rather than being mocked or skipped.
*   **Success Auditor**: The final reviewer spawned by [Sentinel](#core-orchestration-and-execution-roles). It runs a full end-to-end verification pass and must confirm everything works before [Sentinel](#core-orchestration-and-execution-roles) presents the finished project to you.

* * *

## Execution paths

Teamwork automatically adjusts team composition, verification depth, and agent roles based on the task and your prompt:

| Execution Path | Best For | Trigger / Opt-in Signal |
| :-- | :-- | :-- |
| **General (Distributed coding)** | Multi-file SWE, large-scale refactoring, systems simulation, and research. | _Default_ (automatically selected). |
| **Iterative coding (lighter SWE tasks)** | One self-contained change â€” a bug fix, a small feature, or a contained refactor. This path cannot decompose the task. | Explicit prompt signal (e.g., _â€œkeep it smallâ€_, _â€œkeep it focusedâ€_). |
| **Document Review** | Multi-angle critique and synthesis of papers, RFCs, and design docs. | Review requests (e.g., _â€œreview this paperâ€_, _â€œcritique this design docâ€_). |
| **Math / Proof** | Mathematical problem solving, formal bounds, and theorem proving. | Math prompts (e.g., _â€œprove theorem Xâ€_, _â€œverify mathematical boundsâ€_). |
| **Math / Proof (Large Team)** | High-scale tournament networks for hard conjectures and combinatorial search. | Explicit scale signal (e.g., _â€œUse a very large team of agentsâ€_). |

* * *

## Two-phase workflow

To ensure alignment before writing code and avoid constant back-and-forth interruptions, Teamwork splits every project into two clear phases:

### Phase 1: Prompt crafting (scoping interview)

During Phase 1, the main Antigravity agent conducts a structured interview with you. The interview follows a simple principle: **Specify What, Not How**:

1.  **Scope & Objectives**: Clarifies what you want built, its purpose (demo, production, eval, exploration), and the audience.
2.  **Requirements**: Drafts several requirement blocks covering only what you actually care about.
3.  **Independent Verification**: Agrees on an objective check for each requirement â€” a test suite, reference benchmark or metric script, or an independent agent judging against an explicit rubric.
4.  **Acceptance Criteria**: Defines clear, testable criteria for considering the project complete.
5.  **Project Working Directory**: Establishes a dedicated workspace folder, defaulting to `~/teamwork_projects/{PROJECT_NAME}`.

At the end of Phase 1, the main Antigravity agent creates a reviewable **prompt artifact**. You can review the prompt, adjust details, and approve execution with a single confirmation.

### Phase 2: Autonomous execution (structured handoffs)

Once approved, [Sentinel](#core-orchestration-and-execution-roles) hands off the project to the [Project Orchestrator](#core-orchestration-and-execution-roles), which coordinates the team autonomously without needing step-by-step prompts.

Agents coordinate and share progress using structured artifacts in the workspace:

*   **Request artifact**: Captures your initial prompt, goals, constraints, and testable acceptance criteria.
*   **Project plan artifact**: Tracks the milestone roadmap, active workstreams, and dependency flow.
*   **Progress artifact**: Records live milestone status and completed tracks.

* * *

## Integrity modes

Teamwork uses three internal integrity modes to align verification depth with project requirements. During the Phase 1 interview, your agent asks which shortcuts should be off-limits and maps your answers to a mode, which is recorded in the prompt artifact:

| Mode | Purpose | Verification Behavior |
| :-- | :-- | :-- |
| `development` | Rapid iteration | Lenient. Flags only fabricated outputs and facade implementations; code reuse, libraries and pre-built frameworks are all permitted. (Default.) |
| `demo` | Reproducible presentation | Moderate. Adds: no copying core logic from open source, no delegating core work to external tools, no reading test source to reverse-engineer expected behavior. |
| `benchmark` | Thorough evaluation | Maximum strictness. Fully independent, from-scratch implementation; language standard library only. |

For example, if you rule out all four shortcuts, the run uses `benchmark` mode, and the [Auditor](#adversarial-verification-gates) enforces strict verification rules: disallowing mocked test passes, validating ground-truth evaluations against real system execution.

* * *

## Safety, workspaces, and isolation

Teamwork includes built-in safeguards to ensure parallel agent work remains safe, predictable, and easy to audit:

*   **Dedicated Project Working Directories**: All operations run inside dedicated workspace folders (defaulting to `~/teamwork_projects/{PROJECT_NAME}`), keeping your main repository clean and avoiding unintended side effects.
*   **Exclusive File Ownership**: To prevent merge conflicts and race conditions, the [Project Orchestrator](#core-orchestration-and-execution-roles) assigns specific files to individual [Workers](#core-orchestration-and-execution-roles). Multiple workers never edit the same file at the same time.
*   **Per-Agent Scratch Directories**: Each subagent has its own working directory and writes its helper scripts, notes, and logs there rather than in the project root.
*   **Structured State & Artifact Handoffs**: Every state change, command run, review comment, and verification log is recorded in the project plan and progress artifacts, alongside conversation logs. You can monitor live progress across agent tracks in the UI subagent panel or CLI status bar.
*   **Autonomous Execution with Guardrails**: Once you approve the initial prompt, the team works through milestones autonomously, with the [Auditor](#adversarial-verification-gates) and [Success Auditor](#adversarial-verification-gates) verifying results before final handoff.

* * *

## How to use /teamwork-preview

*   [Antigravity 2.0](#tab-panel-41)
*   [Antigravity CLI](#tab-panel-42)

Start a new conversation and invoke `/teamwork-preview` with your goal:

```
/teamwork-preview Migrate our REST API service from Express to Fastify, including full test coverage, TypeScript typing, and benchmark validation.
```

Your agent will start the Phase 1 scoping interview and generate the prompt artifact. Once you approve the prompt, the multi-agent team begins autonomous execution.

In the terminal interface, run `/teamwork-preview` at the prompt:

```
/teamwork-preview Design and implement a cycle-accurate memory controller with lockstep simulation tests.
```

You can monitor active subagents, jump directly to subagents waiting for approval using Alt+J, or inspect milestone progress in the project plan and progress artifacts in real time.

* * *

## Next steps

Explore related documentation and guides:

*   [Boost deep reasoning (`/boost`)](/docs/boost): Explore on-demand deep reasoning for interactive pair programming.
*   [Subagents architecture](/docs/subagents): Learn how background subagents execute parallel workstreams.
*   [Slash commands overview](/docs/slash-commands): Explore the complete catalog of slash commands in Antigravity.
*   [Implementation plans (`/plan`)](/docs/implementation-plan): Master reviewable planning artifacts and structured workflows.
*   [Rules](/docs/rules): Persist project-wide patterns and conventions.
*   [Antigravity Overview](/docs/overview): Explore core features and workflows in Antigravity.