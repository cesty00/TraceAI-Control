# TraceAI-Control Release Readiness Checklist

## Purpose

This checklist defines the minimum evidence required before TraceAI-Control can be promoted from controlled internal testing to a daily-use internal release.

It is intended for Robocop, maintainers, and release reviewers.

A release claim is not accepted unless the required evidence is recorded and inspectable.

---

## Release levels

### Internal pilot

Use this level when the application is ready for supervised testing by a small number of users.

Minimum label:

```text
v0.9.0-rc1
```

Allowed state:

```text
controlled internal pilot
```

### Daily-use internal release

Use this level when the application can be used routinely by trained internal users.

Minimum label:

```text
v0.9.x
```

Allowed state:

```text
daily-use internal release
```

### Unsupervised production release

This level is out of scope until explicitly approved.

---

## Mandatory evidence for release candidate

A release candidate requires all of the following:

```text
[ ] Current main branch identified
[ ] Release candidate tag or version name proposed
[ ] CHECKPOINT.md reviewed
[ ] README.md reviewed
[ ] AGENTS.md reviewed
[ ] docs/robocop_operating_manual.md reviewed
[ ] docs/robocop_roles_and_skills.md reviewed
[ ] No open PRs that block release
[ ] No stale PR treated as active work
[ ] GitHub Actions / TraceAI Diagnostics run completed
[ ] Diagnostic artifact available and not expired
[ ] pytest PASS confirmed from artifact
[ ] reference_comparison.md = PASS where applicable
[ ] diagnostic-summary.md inspected
[ ] real_audit_checklist_report.docx generated where applicable
[ ] real_audit_checklist_ui.json generated where applicable
[ ] Windows artifact or Windows validation evidence available
[ ] User-facing daily workflow documented
[ ] Support / diagnostic ZIP guidance documented or explicitly deferred
[ ] Known blocking errors mapped or documented
[ ] Release limitations documented
```

---

## Mandatory real-case validation

Before daily-use release, validate at least these scenarios using real or realistic anonymized fixtures:

| Scenario | Required evidence |
|---|---|
| FINISHED_PRODUCT complete | DOCX + UI JSON generated with expected verdict and evidence |
| FINISHED_PRODUCT incomplete | explicit INCOMPLETE behavior preserved |
| WMS-only / PRD missing | missing data remains explicit; no false upstream evidence |
| no matching records | typed user-actionable error |
| ambiguous case type | AmbiguousCaseTypeError behavior preserved |
| corrupt or unreadable official source | DataQualityBlockingError behavior implemented or documented as known gap |
| diagnostic ZIP generation | ZIP contains expected support files |
| Windows execution path | artifact launches or validation evidence exists |

If a scenario is deferred, the release notes must explicitly say so.

---

## User-facing release requirements

A daily-use release must provide clear instructions for non-technical users:

```text
[ ] how to select the source folder
[ ] which source files are expected
[ ] how to enter product code and lot
[ ] how to run source verification
[ ] how to preview the audit checklist
[ ] how to generate DOCX
[ ] how to generate Diagnostic ZIP
[ ] what to do when an error appears
[ ] where output files are saved
[ ] what files may be sent to support
[ ] what files may contain sensitive data
```

---

## Packaging requirements

Before daily-use release, confirm:

```text
[ ] version or tag exists
[ ] release notes exist
[ ] dependency source is clear: requirements.txt, pyproject.toml, or explicit workflow install list
[ ] supported Python version is documented
[ ] supported Windows version or environment is documented
[ ] build info includes commit/version where applicable
[ ] artifact download path is documented
[ ] rollback or previous version recovery is documented or explicitly deferred
```

---

## Blocking gaps

The following gaps block daily-use release unless explicitly accepted by the user as known limitations:

```text
[ ] no official GitHub validation artifact
[ ] missing pytest PASS evidence
[ ] missing reference comparison where applicable
[ ] generated DOCX not inspected for release scenario
[ ] generated UI JSON not inspected for release scenario
[ ] unclear operator workflow
[ ] unclear support/diagnostic ZIP contents
[ ] known generic error on common user input
[ ] stale PR treated as active work
[ ] CHECKPOINT.md and README.md disagree on current state
[ ] release based on branch validation that is not merged to main
```

---

## Release decision output

Robocop must report release decisions using this format:

```text
Release status:
Target release level:
Main commit reviewed:
Evidence inspected:
Blocking gaps:
Non-blocking gaps:
Known limitations:
User-facing risks:
Technical risks:
Recommended next PR:
Can release as:
Cannot release as:
```

---

## Current known release gap

As of the introduction of this checklist, `ERRORS-01_PR2_4` must not be considered complete unless rebuilt from current `main`, merged, and officially validated.

The old PR #88 is closed and not merged. It must not be used as the implementation base.

Only the idea may be reused:

```text
official source present but unreadable/corrupt -> DataQualityBlockingError
```
