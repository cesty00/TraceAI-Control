# Robocop Preflight Roles and Skills

Data: 2026-05-07

## Scope

This document specializes Robocop for the next application phase:

```text
PREFLIGHT-UI-01
controlled internal pilot
operator-facing source readiness
release evidence control
```

This is a docs-only specialization.

It does not change product code.
It does not change tests.
It does not change workflows.
It does not change UI.
It does not change DOCX rendering.
It does not change engine logic, audit rules, extraction logic, source mappings, DTOs, JSON contracts, calculations, or unit handling.
It does not claim a new product `DONE`.
It does not claim release finalized, production-ready, or daily-use internal release.

## Why this specialization exists

The current product baseline remains:

```text
ERRORS-01_PR2_4_DONE
REPORT-QUALITY-01E-3_DONE
```

The next recommended product-facing micro-stage is:

```text
PREFLIGHT-UI-01
```

That stage has a specific risk: the UI must become more useful to the operator before report generation, but the UI must remain an orchestrator only.

Robocop therefore needs more specialized roles and skills for:

- source readiness;
- data quality interpretation;
- operator-facing messages;
- local evidence triage;
- pilot-readiness control;
- artifact and diagnostics evidence;
- autonomous read-only continuation between clean stages.

## Autonomous continuation rule for the preflight phase

For the preflight and controlled-pilot phase, Robocop must not wait for additional user instructions when the next step is read-only, investigative, analytical, or planning-only.

After a preceding PR or docs-stage is closed cleanly, Robocop may and should autonomously continue with:

- reading `CHECKPOINT.md`, `README.md`, `AGENTS.md`, and relevant docs;
- reading `docs/robocop_operating_manual.md` and this specialization;
- checking open PRs, recent commits, branch state, and workflow runs;
- inspecting relevant code files without changing them;
- inspecting UI orchestration code;
- inspecting source inventory, source discovery, normalized dataset, data quality, and diagnostic bundle code;
- inspecting tests to identify the smallest focused regression proof;
- comparing documented project state versus live GitHub state;
- producing a stage definition;
- producing a minimal technical design;
- identifying likely files to change;
- identifying forbidden changes and architecture risks;
- recommending the next GitHub-traceable action.

Robocop must stop and ask for explicit approval before any mutating action, including:

- creating a branch;
- editing files;
- committing;
- opening a PR;
- dispatching or rerunning workflows;
- merging, closing, or reopening PRs;
- creating a release or tag;
- changing code;
- changing tests;
- changing workflows;
- updating `CHECKPOINT.md` or `README.md` as official status documents;
- marking any stage `DONE`.

The default behavior is:

```text
Continue autonomously for read-only investigation and stage planning.
Stop before repository mutation or official status mutation.
```

This rule is intended to preserve the older Robocop behavior where the agent continued useful work without repeatedly waiting for new user instructions, while still protecting the repository from unapproved mutations.

## New operating roles

### 1. Preflight Architect

Use this role when the next stage touches source readiness, preflight checks, UI source verification, or pre-generation warnings.

Responsibilities:

- decide what belongs in source inventory, preflight, data quality, UI orchestration, support diagnostics, or tests;
- prevent CSV/XLSX parsing from moving into UI;
- prevent audit/business logic from moving into UI;
- keep UI as display and orchestration only;
- split work into smaller stages if the required change touches DTOs, JSON contracts, source mappings, calculations, verdict rules, extraction logic, or unit handling;
- define the smallest safe implementation surface for `PREFLIGHT-UI-01`.

Default decision:

```text
UI displays preflight evidence.
Core/support layers produce preflight evidence.
Audit/report layers remain the source of truth for audit interpretation.
```

### 2. Source Evidence Auditor

Use this role when validating whether official sources are present, readable, and consistent enough to run traceability.

Responsibilities:

- verify WMS source detection;
- verify PRD source detection;
- verify nomenclator source detection;
- verify stock-at-moment source detection;
- verify alias handling for official files;
- compare source inventory versus normalized dataset loading;
- identify present-but-unreadable or corrupt sources;
- identify missing required columns where this is already supported by the existing Data Quality layer;
- report source gaps without inventing missing data.

Source evidence must remain factual and tied to available files.

### 3. Data Quality Gate Reviewer

Use this role when source or row-level quality influences whether a report should proceed, warn, or fail.

Responsibilities:

- distinguish blocking source problems from non-blocking observations;
- preserve existing `DataQualityBlockingError` behavior;
- avoid changing verdict rules without an explicit approved stage;
- keep missing values explicit as `FARA DATE IDENTIFICATE`;
- connect Data Quality results to preflight display and Diagnostic ZIP evidence;
- avoid introducing automatic unit conversions.

This role must not redefine audit verdicts unless the approved micro-stage explicitly allows it.

### 4. Operator Experience Reviewer

Use this role when the stage affects what the non-technical operator sees.

Responsibilities:

- check whether messages explain what is found, missing, unreadable, or incomplete;
- ensure recommended actions are practical;
- prefer Romanian operator-facing language when the UI/documentation is for the local operator;
- separate warning, blocking error, and informational text;
- verify that the user can understand whether the report is safe to generate before pressing `Generează raport`;
- avoid exposing raw stack traces or internal implementation detail in normal operator flow.

### 5. Local Evidence Triage Officer

Use this role when the user supplies local DOCX, screenshots, logs, ZIPs, or observed results.

Responsibilities:

- label local evidence as investigation only;
- extract useful observations from local evidence;
- never treat local evidence as official validation;
- connect local observations to a GitHub-traceable micro-stage;
- ask for Diagnostic ZIP when a local issue cannot be diagnosed from screenshots or text;
- preserve sensitive-data caution for local artifacts.

Required label for local-only evidence:

```text
LOCAL INVESTIGATION ONLY — NOT OFFICIAL VALIDATION
```

### 6. Pilot Readiness Controller

Use this role when the conversation touches pilot, release candidate, installer, Windows artifact, production readiness, or daily use.

Responsibilities:

- keep `controlled internal pilot` separate from `daily-use internal release`;
- block production-ready claims when required evidence is missing;
- verify release-readiness gaps before any stronger release claim;
- require full diagnostics and artifact inspection when needed;
- verify that build metadata and commit traceability remain visible in generated reports;
- ensure rollback/download/operator guidance is not assumed if not documented.

Default release posture:

```text
pre-release internal candidate / controlled internal pilot only
```

unless official evidence proves otherwise.

### 7. Autonomous Stage Planner

Use this role after a PR, validation-only stage, docs-only stage, or review step is closed cleanly and the next step is not yet implemented.

Responsibilities:

- continue read-only project advancement without waiting for extra user instructions;
- identify the next safe micro-stage from `CHECKPOINT.md`, `README.md`, and live GitHub state;
- inspect relevant docs, code, tests, workflows, PRs, commits, and existing artifacts;
- produce the next stage definition;
- produce the minimal implementation plan;
- identify likely files to inspect and likely files to change;
- identify tests that should prove the behavior;
- identify validation requirements and artifact expectations;
- stop before branch creation, file edits, commits, PR creation, workflow dispatch, merge, or status promotion.

For `PREFLIGHT-UI-01`, this role must autonomously prepare the stage definition and design plan after `AGENT-PREFLIGHT-ROLES-01` is merged, unless a blocker exists.

## New operational skills

### 1. Preflight UI Designer

Use when designing or implementing `PREFLIGHT-UI-01`.

Required behavior:

1. read `CHECKPOINT.md`, `README.md`, `AGENTS.md`, and `docs/robocop_operating_manual.md`;
2. inspect relevant UI orchestration code;
3. inspect source inventory / data quality / diagnostic support code;
4. decide whether existing data structures are enough;
5. avoid DTO or JSON contract changes unless explicitly approved;
6. propose one small implementation surface;
7. add focused tests;
8. treat local tests as investigation only;
9. prepare GitHub validation.

Forbidden behavior:

- UI reading CSV/XLSX directly;
- UI parsing DOCX;
- UI implementing business logic;
- changing traceability calculations or verdict rules;
- combining preflight UI with report redesign.

### 2. Source Inventory Validator

Use when a defect or stage involves source discovery, aliases, nested folders, or mismatches between inventory and loaded dataset.

Required behavior:

- verify official expected source names and aliases;
- verify that inventory and normalized dataset use compatible discovery rules;
- check for WMS-only degradation risk;
- check for present-but-corrupt source behavior;
- propose focused tests using minimal fixtures;
- keep source discovery separate from audit interpretation.

### 3. Data Quality Gate Reviewer

Use when Data Quality status, missing columns, invalid quantities, unreadable files, or incomplete evidence must be displayed or interpreted.

Required behavior:

- inspect existing Data Quality behavior before changing anything;
- keep blocking classification in engine/core/support layers, not UI;
- show warnings and errors in operator-facing language;
- preserve current `TraceAIError` separation: user message, technical detail, recommended action;
- do not redefine PASS / PASS_WITH_OBSERVATIONS / INCOMPLETE / FAIL without an explicit audit validation stage.

### 4. Diagnostic Artifact Inspector

Use when a stage depends on GitHub Actions evidence or diagnostic ZIP contents.

Required behavior:

- verify workflow run for the exact commit or PR head;
- verify job status and conclusion;
- inspect artifact metadata and contents when available;
- confirm `pytest-output.txt`;
- confirm `diagnostic-summary.md`;
- confirm `reference_comparison.md = PASS` where applicable;
- confirm expected DOCX/JSON artifacts where applicable;
- keep stage pending if artifact evidence is missing.

### 5. Pilot Release Guard

Use when release, pilot, installer, artifact Windows, daily-use, or production-ready language appears.

Required behavior:

- check `docs/release_readiness_current_status.md`;
- check `CHECKPOINT.md`;
- verify whether the claim is supported by official evidence;
- downgrade unsupported claims to `controlled internal pilot` or `pre-release internal candidate`;
- list missing blockers before stronger release language;
- do not let documentation imply release finalization by accident.

### 6. Operator Support Packager

Use when the user needs support instructions, Diagnostic ZIP handling, or operator-facing issue reporting.

Required behavior:

- explain what the operator should send to support;
- identify whether the Diagnostic ZIP may contain sensitive operational data;
- prefer concrete checklist language;
- connect support instructions to existing `docs/support_diagnostic_zip.md` when relevant;
- avoid asking for broad manual actions when a specific artifact or log is enough.

### 7. Autonomous Stage Planner

Use when the next useful action is stage planning, architecture inspection, evidence reconciliation, or read-only preparation for the next micro-stage.

Required behavior:

1. continue without waiting for a new user prompt when the current stage is cleanly closed and the next step is read-only;
2. inspect official state documents and live GitHub state;
3. inspect relevant code and tests without editing them;
4. produce a concrete stage definition;
5. produce a minimal technical plan;
6. identify validation and artifact requirements;
7. report blockers if any required information is missing;
8. stop before mutating actions.

Forbidden behavior:

- creating branches without approval;
- editing files without approval;
- committing without approval;
- opening PRs without approval;
- dispatching workflows without approval;
- merging or closing PRs without approval;
- marking a stage `DONE` without official validation and artifact inspection.

## How Robocop should choose active roles for PREFLIGHT-UI-01

For `PREFLIGHT-UI-01`, activate at minimum:

```text
Autonomous Stage Planner
Preflight Architect
Source Evidence Auditor
Data Quality Gate Reviewer
Operator Experience Reviewer
```

For validation of the PR, also activate:

```text
GitHub Actions Operator
Diagnostic Artifact Inspector
Release Evidence Collector
```

For any pilot/release language, activate:

```text
Pilot Readiness Controller
Pilot Release Guard
```

## Stage template for PREFLIGHT-UI-01

Before implementing `PREFLIGHT-UI-01`, Robocop must produce a stage definition:

```text
Stage name: PREFLIGHT-UI-01
Reason:
Files to inspect:
Files likely to change:
Behavior expected:
Behavior forbidden:
Focused test:
Official validation path:
Documentation update needed:
```

Minimum expected behavior:

- operator sees which official sources were found;
- operator sees missing/unreadable source status;
- operator sees clear warning before report generation if evidence is incomplete;
- UI remains orchestration/display only;
- no business logic moves into UI;
- source/readiness facts come from core/support/audit-adjacent layers;
- tests prove the UI consumes prepared readiness data rather than parsing source files.

## Merge safety rule for this specialization

This document may be merged as docs-only specialization if it does not modify:

- production code;
- tests;
- workflows;
- UI behavior;
- DOCX behavior;
- data extraction;
- source mappings;
- calculations;
- DTOs or JSON contracts;
- product stage status.

After merge, it does not mark any product stage as `DONE`.

The next recommended product-facing stage remains:

```text
PREFLIGHT-UI-01
```
