# Robocop Stop Conditions — TraceAI-Control

## Purpose

This document defines when Robocop must stop, report a blocker, and avoid continuing based on stale, contradictory, or unsafe assumptions.

Robocop must prefer a clear blocker report over acting on outdated context.

---

## Supreme stop rule

Robocop must stop when live GitHub state contradicts the current conversation context, previous instructions, local notes, or assumptions.

When this happens, Robocop must refresh from GitHub and report the live state before taking action.

---

## Mandatory stop conditions

Robocop must stop and report a blocker when any of the following is true:

```text
[ ] A PR is described as active, but GitHub shows it closed.
[ ] A PR is described as mergeable, but GitHub shows mergeable:false.
[ ] A PR is described as needing rebase/update, but GitHub shows head_sha == base_sha and changed_files = 0.
[ ] A PR is closed and not merged, but instructions say to continue it.
[ ] A workflow run is missing for the current head SHA.
[ ] A diagnostic artifact is expired or unavailable.
[ ] Artifact contents have not been inspected, but the stage is being promoted to DONE.
[ ] Local tests are being treated as official validation.
[ ] Branch validation is being confused with main-completed status.
[ ] CHECKPOINT.md and README.md disagree on the current official state.
[ ] The requested change touches DTOs, JSON contracts, calculations, source mappings, verdict rules, extraction logic, or unit handling without an explicit stage.
[ ] Business logic would be moved into UI.
[ ] A stale PR or old branch is being used as an implementation base.
[ ] Release readiness is claimed without release checklist evidence.
[ ] User asks for release/daily-use status but no current GitHub state has been checked.
```

---

## Required blocker format

When stopped, Robocop must respond using this format:

```text
Blocaj:
Impact:
Ce este confirmat:
Ce nu este confirmat:
Acțiunea corectă:
```

Robocop must not soften or hide blockers.

A blocker is a safe outcome when continuing would risk corrupting project state.

---

## Closed PR handling

Closed PRs must be handled according to their live state.

### Closed and merged

If a PR is closed and merged:

```text
- do not continue the PR;
- inspect the merge result if needed;
- update or verify CHECKPOINT.md / README.md only if status docs are stale;
- base future work on current main.
```

### Closed and not merged

If a PR is closed and not merged:

```text
- do not reopen mentally;
- do not treat it as active;
- do not use its branch as implementation base;
- extract only the useful idea if still relevant;
- rebuild from current main in a new micro-stage.
```

### Example

Old PR #88 is closed and not merged.

Correct handling:

```text
ERRORS-01_PR2_4_REBUILD_REQUIRED_FROM_MAIN
```

Incorrect handling:

```text
continue PR #88
rebase PR #88
mark PR #88 ready for review
```

---

## Stale branch rule

Robocop must not use stale branches as implementation bases.

A branch is stale when:

```text
- it predates important merged PRs;
- it changes CHECKPOINT.md / README.md using outdated project state;
- it is associated with a closed not-merged PR;
- it has no current workflow run for its head SHA;
- it would rewind validated project status.
```

Correct action:

```text
Create a fresh branch from current main and reimplement only the approved minimal scope.
```

---

## Validation stop rules

Robocop must stop before marking a stage DONE unless all required validation evidence exists.

Required evidence:

```text
[ ] GitHub Actions / TraceAI Diagnostics completed successfully
[ ] Current head or merge commit identified
[ ] Artifact available and not expired
[ ] pytest PASS confirmed from artifact
[ ] reference_comparison.md = PASS where applicable
[ ] diagnostic-summary.md inspected
[ ] DOCX/JSON generated where applicable
[ ] CHECKPOINT.md and README.md updated together after validation
```

If any item is missing, the maximum status is:

```text
IMPLEMENTED_PENDING_VALIDATION
```

---

## Release readiness stop rules

Robocop must stop before claiming daily-use readiness if any of the following is missing:

```text
[ ] release readiness checklist completed
[ ] current main identified
[ ] release version/tag proposed
[ ] Windows artifact or Windows validation evidence available
[ ] user daily workflow documented
[ ] support diagnostic guidance documented or explicitly deferred
[ ] real or realistic case validation completed
[ ] known blocking gaps documented
```

If any item is missing, Robocop may only claim:

```text
pre-release internal candidate
```

or

```text
controlled internal pilot
```

not:

```text
daily-use release
```

---

## Safe action after stopping

After a stop condition, Robocop may proceed only after it has:

```text
1. refreshed live GitHub state;
2. identified current main and relevant PR states;
3. restated what is safe to do;
4. chosen the smallest safe next micro-stage;
5. avoided stale branches and outdated PRs.
```

---

## Standing principle

Robocop must be conservative with project state.

It is better to stop and report a blocker than to continue on stale assumptions.
