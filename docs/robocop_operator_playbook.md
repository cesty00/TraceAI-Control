# Robocop Operator Playbook — TraceAI-Control

Data: 2026-05-09

## Scop

Acest document este colecția canonică de template-uri procedurale și runbook-uri scurte pentru operator și pentru Robocop.

Acesta este locul unic pentru template-uri reutilizabile.

Nu păstrează starea curentă a proiectului.
Nu redefinește semantica de validare.
Nu declară release, production-ready, daily-use sau `DONE`.

## How to use this playbook

Reguli:

1. Alege template-ul care corespunde acțiunii.
2. Completează doar cu date confirmate.
3. Nu transforma câmpurile goale în presupuneri.
4. Dacă dovada nu există, spune explicit că lipsește.

## PR Review Template

```text
PR Review

PR:
Branch:
Scope expected:
Changed files reviewed:
What is confirmed:
What is out of scope:
Risks:
Validation seen:
Artifact evidence seen:
Recommendation:
```

## Merge Approval Template

```text
Merge Approval

PR:
Branch:
Head SHA:
Scope matches approved stage:
Workflow status:
Artifact inspection:
Known limits:
What merge will prove:
What merge will not prove:
Recommendation:
```

Regulă:

Merge approval nu spune niciodată automat că etapa este `DONE`.

## Post-Merge Validation Template

```text
Post-Merge Validation

Main commit:
Workflow:
Run id / run number:
Workflow conclusion:
pytest evidence:
reference_comparison.md:
DOCX / JSON evidence:
Artifact inspected:
Scope confirmed:
What remains unconfirmed:
Recommended status wording:
```

## Status Sync Template

```text
Status Sync

Subject:
Official source checked:
Current wording to record:
What is confirmed:
What is not confirmed:
Semantic limits:
Follow-up needed:
```

Regulă:

Status sync consemnează, nu promovează automat.

## Workflow Dispatch Template

```text
Workflow Dispatch

Workflow:
Reason:
Target branch / commit:
Expected evidence:
What success would confirm:
What success would not confirm:
Approval status:
```

## Local Operator Run Template

```text
Local Operator Run

Label: LOCAL INVESTIGATION ONLY — NOT OFFICIAL VALIDATION
Case:
Local environment:
Observed result:
Files or screenshots available:
What this suggests:
What this does not prove:
Recommended next official step:
```

## Connector Failure Fallback Template

```text
Connector Failure Fallback

Missing capability:
What is still confirmed:
What cannot be confirmed:
Minimum input needed:
Safe next action:
```

## Evidence Handoff Template

```text
Evidence Handoff

Context:
Repository / PR / main reference:
Workflow or artifact reference:
Files inspected:
Evidence summary:
Open gaps:
Next reviewer action:
```

## Final rule

Dacă un template pare să susțină o concluzie mai puternică decât dovada reală, concluzia trebuie redusă, nu forțată.
