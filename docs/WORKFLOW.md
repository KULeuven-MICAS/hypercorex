# Workflow

How planning and execution work together in this repo. Both sides follow this file.

## 1. Two sides, linked only by files

- **claude.ai (a Project)** is where we plan: design, trade-offs, papers, background.
- **Claude Code** is where we execute. It runs on Ryan's machine and runs pixi, the tests and, later, the simulator.
- The two sides can't see each other's chats, knowledge or memory. They share only the files in this repo.
- Ryan moves the files by hand. He commits the docs that claude.ai writes, and he uploads the updated docs to the Project. This is on purpose, so he sees every change of plan.

## 2. The documents

| File | Holds | Written by | Lifetime |
|---|---|---|---|
| `CLAUDE.md` | What the repo is, commands, conventions, guard rails | both, rarely | stable |
| `docs/WORKFLOW.md` | This file | both, rarely | stable |
| `docs/STATUS.md` | Overall progress: milestones, planned tasks, done PRs, baselines, open items | planned in claude.ai; updated by Claude Code | whole project |
| `docs/DECISIONS.md` | Numbered decisions that hold across PRs | both; numbers come from the file | whole project |
| `docs/ARCHITECTURE.md` | Components and their interfaces as they are now, plus the planned ones marked as planned | Claude Code, with each change | current state; no history |
| `docs/HOUSEKEEPING.md` | Rules: code and doc style, formats, naming, where files go, tests, commits | both | whole project |
| `docs/PR.md` | The current PR only: goal, steps, definition of done, status | claude.ai writes it; Claude Code writes back | one PR; deleted at close (D26) |

**Decisions.** One entry per decision:
- what was decided and why, in one to three sentences;
- what it amends or closes, and where the detail lives;
- an area tag (`scope`, `env`, `sw`, `hw`, `test`, `docs`).

Numbers never change and are never reused. An amended entry gets an "Amended by Dn" line. A replaced entry keeps its number, shortened to what it said and what replaced it. The file keeps the next free number and an index by area at the top.

**Open items.** These are questions not decided yet. They live in STATUS, numbered and never reused, with the next free number written above the list. A closed item is removed, and the decision that closed it says so.

**Baselines.** Accuracy numbers live in a table in STATUS, with the Config and seed that produced them.

**Conflicts.** Before suggesting anything, either side checks it against DECISIONS. If it contradicts a decision, say which one, and propose a new decision with the next free number.

## 3. The cycle for one PR

1. **Name it.** A planning session starts by picking the PR name, e.g. `s0-clean-slate`. The same name is used for the branch (off `main`) and for the GitHub PR (into `main`).
2. **Plan in claude.ai.** The PR starts as a discussion. Ryan says what he wants, and claude.ai answers with the design questions it raises, each with two or three options and a recommendation, checked against DECISIONS.
3. **Write the context docs.** Once we agree, claude.ai writes:
   - `docs/PR.md`, from the template in section 6;
   - the matching edits to STATUS and DECISIONS (new entries with their numbers);
   - edits to CLAUDE.md or HOUSEKEEPING, if a convention changes.

   The docs are written for a reader who has not seen the conversation: decisions come with their reasons, and nothing says "as discussed".
4. **Commit the context docs.** Ryan creates the branch and commits the context docs as its first commit.
5. **Sync check in Claude Code (plan mode, no edits).** Claude Code reads CLAUDE.md, this file, PR.md, DECISIONS and STATUS, then reports:
   - whether the sync header matches the repo (section 5);
   - each "Assumption to verify", confirmed or not, with the file and line;
   - any step that conflicts with the code or with a decision.

   If a mismatch changes a decision or the scope, Ryan takes it back to claude.ai and we replan. Smaller mismatches go into PR.md's Status, and work goes on.
6. **Execute one step at a time.** For each step in PR.md, Claude Code:
   - edits the working tree only, and never commits or pushes;
   - runs the step's checks;
   - updates PR.md's Status and every doc the step touches;
   - reports as in section 4 and stops.

   Ryan inspects, tests, may change things himself, and commits. Claude Code continues from the tree as Ryan left it; his edits win.
7. **Close.** When the Definition of done holds:
   - Claude Code updates STATUS (tasks, the done-PR row, baselines and open items) and completes PR.md's Status.
   - Ryan uploads the updated docs, PR.md included, to the Project, and uses PR.md's text as the GitHub PR description.
   - The branch's last commit deletes `docs/PR.md` and sets STATUS's "Current PR" to none (D26). Ryan then merges.
   - Between PRs, `main` has no PR.md. If Claude Code starts without one, no PR is in progress: it stops and asks what to work on. The next PR's planning writes a new PR.md.
8. **Replan.** When Ryan uploads an updated PR.md, claude.ai reads its Status / Open questions first and continues from there.

Small, code-heavy planning, where the details depend on the existing code, can happen directly in Claude Code's plan mode. Its outcome still lands in PR.md, and any decision still lands in DECISIONS.

## 4. Rules for each step

- The report after a step gives:
  - the files changed;
  - the check commands and their actual output (test counts, accuracy with its seed, "no output" for a byte-equal `cmp`, lint clean);
  - the steps still to do;
  - the guard rails kept (CLAUDE.md);
  - anything that could not be run, and what was run instead.
- Each step updates STATUS, DECISIONS, ARCHITECTURE and HOUSEKEEPING where it touches them. A code change without its doc change is not done.
- A test that is dropped or merged is named, with the reason. Otherwise the test count only goes up.
- A change of behaviour, even a bug fix, gets a step of its own. It never hides inside a cleanup.
- A plot change lists what to check by eye, and where.
- A decision made during execution gets the next free number in DECISIONS in the same step, plus a line in PR.md's Status.

## 5. Staying in sync

PR.md starts with a sync header:

```
PR: <name>          Branch: <name> (from main at <commit>)
Next free D: <n>    Next free open item: <m>
Last planned: <date>, claude.ai    Last updated: <date>, <claude.ai | Claude Code>
```

- claude.ai fills it in when it writes the plan. Claude Code checks it at the sync check and updates "Last updated" with every write-back.
- If the header's numbers don't match DECISIONS or STATUS, the side that notices stops and says so before doing anything else.
- claude.ai plans only from the docs Ryan uploads. Anything that depends on code it hasn't seen goes under "Assumptions to verify".
- Durable rules change in this file, CLAUDE.md or HOUSEKEEPING, never only in a chat.

## 6. PR.md template

```markdown
# <PR name>

<sync header>

## Goal
One or two sentences: what this achieves and why.

## Context
Only the background Claude Code needs.

## Decisions
- D<n> — <decision> — <reason>   (full entry in DECISIONS.md)
- <PR-local choice> — <reason>

## Constraints & interfaces
Parameters, data formats, tools and versions, files that must not change.

## Assumptions to verify against the code
- ...

## Steps
Each step: ID, what to do, and its check command with the expected output.

## Definition of done
Concrete, testable criteria.

## Status / Open questions
(Updated by Claude Code: progress per step, deviations and why, questions for the next planning round.)
```

## 7. After a milestone

**Walk-through.** A milestone that changes how the flow is used ends with a walk-through in `sw/examples/<name>/README.md`, plus a test that checks every number it states.

**Housekeeping.** This is a PR of its own that removes loose code without changing behaviour. Before any edit, Claude Code lists its findings by file and by kind (remove, merge, move, reword), with rough sizes, plus what it would leave alone and why. It looks for:
- dead code;
- duplicated helpers;
- test helpers copied between files;
- stale comments;
- drift between the docs and the code.

Ryan picks what goes in. "No behaviour change" is proven by comparing outputs before and after (seeded accuracies, results tables, iM contents byte for byte).

## 8. Principles

- **One vertical slice before generality.** Take the simplest case all the way through, then generalise when a real case needs it.
- **Decide in one place, derive everywhere else.** The Config decides. Item memories, encoders, the AM, the runner and later the HW build derive from it.
- **Text where it can be.** Configs are JSON, results are CSV, docs are Markdown. HV arrays are `.npy`/`.npz`, which are deterministic bytes.
- **Every number is checked.** Numbers in docs and papers come from commands in the repo, and a test checks them.
- **Deterministic outputs.** The same Config and seed give byte-identical output.
- **The Python model is the golden reference.** The RTL is checked against it bit for bit.
