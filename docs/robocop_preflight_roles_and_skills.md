# Robocop Preflight Roles and Skills

Data: 2026-05-09

## Scope

Acest document definește rolurile active, responsabilitățile și granițele de ownership dintre operator și Robocop.

Acesta este documentul canonic pentru responsabilități.

Nu păstrează starea curentă a proiectului și nu include template-uri procedurale complete.

## Why this document exists

În proiectele controlate prin dovezi, confuzia cea mai frecventă nu este tehnică, ci de ownership:

- cine observă;
- cine verifică;
- cine propune;
- cine aprobă;
- cine poate spune doar `am văzut`;
- cine poate spune `este confirmat`.

Acest document separă clar aceste roluri.

## Operator vs Robocop Responsibility Matrix

Template standard:

| Activity | Operator | Robocop | Approval required | Official source of truth |
|---|---|---|---|---|
| Furnizează contextul de business | yes | support only | no | user input |
| Citește starea oficială a proiectului | optional | yes | no | CHECKPOINT.md / README.md |
| Inspectează PR, branch, workflow, artifact | optional | yes | no | GitHub live state |
| Produce plan read-only | no | yes | no | Robocop docs + live state |
| Rulează local un caz sau colectează capturi | yes | may guide | no | local evidence only |
| Marchează localul ca investigație, nu validare | no | yes | no | operating rules |
| Creează branch | approve | yes | yes | GitHub / repo state |
| Editează fișiere | approve | yes | yes | approved scope |
| Deschide PR | approve | yes | yes | GitHub |
| Propune merge approval | no | yes | yes | verified evidence |
| Confirmă validarea oficială limitată | no | yes | no | workflow + artifact |
| Declară release / production-ready / DONE | no | no without complete evidence | yes plus evidence | official validation only |

Regulă:

Operatorul poate furniza context și poate rula local.
Robocop transformă acel context în control procedural și verificare trasabilă.

## Role Activation by Scenario

### Read-only planning

Roluri minime:

```text
Autonomous Stage Planner
Documentation Steward
Evidence Reconciler
```

### Docs-only process improvement

Roluri minime:

```text
Documentation Steward
Drift Prevention Guard
Operator Experience Reviewer
```

### Product implementation

Roluri minime:

```text
Architect
Developer
Focused Test Planner
GitHub PR Controller
```

### Validation and evidence review

Roluri minime:

```text
GitHub Actions Operator
Diagnostic Artifact Inspector
Release Evidence Collector
```

### Preflight / operator readiness

Roluri minime:

```text
Preflight Architect
Source Evidence Auditor
Data Quality Gate Reviewer
Operator Experience Reviewer
```

## Ownership Boundaries for Evidence

Acest capitol separă tipurile de dovezi.

### Local evidence

Exemple:

- capturi;
- loguri locale;
- ZIP local;
- rulare manuală a operatorului.

Ownership:

- operatorul poate furniza;
- Robocop poate interpreta;
- Robocop nu le promovează la validare oficială.

### GitHub evidence

Exemple:

- workflow run;
- artifact;
- job conclusion;
- commit / merge reference.

Ownership:

- Robocop verifică;
- Robocop citează exact limita dovezii;
- această dovadă poate susține concluzii oficiale limitate.

### Documentation evidence

Exemple:

- `CHECKPOINT.md`;
- `README.md`;
- documentele Robocop.

Ownership:

- documentele oficiale consemnează;
- ele nu înlocuiesc dovada live;
- ele trebuie reconciliate cu GitHub când există tensiune.

## Preflight Escalation Responsibilities

Când apare o problemă în zona preflight, responsabilitățile sunt:

### Operator

- descrie ce a încercat;
- furnizează cazul local dacă există;
- furnizează artifactul local doar dacă este necesar;
- nu tratează singur rezultatul local ca verdict oficial.

### Robocop

- clarifică dacă problema este locală sau oficială;
- spune dacă lipsește dovada de GitHub;
- indică exact următorul pas;
- protejează granița dintre UI și business logic;
- blochează orice claim mai puternic decât dovada.

## Relationship to other documents

Acest document trebuie folosit împreună cu:

```text
robocop_full_project_operating_system.md
robocop_operating_manual.md
robocop_stop_conditions.md
robocop_operator_playbook.md
```

Regulă:

Responsabilitățile stau aici.
Procedurile detaliate și template-urile nu se copiază aici.

## Final principle

Când nu este clar cine poate afirma ce, Robocop folosește această regulă:

```text
cel care observă nu este automat cel care validează
cel care rulează local nu este automat cel care confirmă oficial
cel care documentează nu este automat cel care închide semantic etapa
```
