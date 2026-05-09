# Robocop Full Project Operating System — TraceAI-Control

Data: 2026-05-09

## Scop

Acest document definește modelul canonic de operare pentru Robocop în `TraceAI-Control`.

El stabilește:

- cum se citește starea proiectului;
- cum se interpretează dovezile;
- ce înseamnă validare oficială;
- cum se evită drift-ul dintre documente;
- care document este sursa canonică pentru fiecare categorie de reguli.

Acest document este docs-only.

Nu schimbă aplicația, testele, workflow-urile, UI-ul, rendererul DOCX, engine-ul, regulile Data Quality, source mappings, DTO-urile, JSON contractele, calculele sau verdicturile.

Nu declară release, production-ready, daily-use sau `DONE`.

## Surse oficiale de adevăr

Starea oficială a proiectului se citește din:

```text
CHECKPOINT.md
README.md
AGENTS.md
```

Documentele Robocop completează controlul operațional, dar nu înlocuiesc checkpoint-ul produsului.

Dacă există contradicții:

```text
1. CHECKPOINT.md
2. README.md
3. AGENTS.md
4. documentele Robocop
```

## Bucla de control

Robocop operează în această buclă:

```text
1. Citește starea oficială.
2. Verifică live GitHub: branch, PR, workflow, artifact, commit.
3. Reconcilează starea live cu documentele oficiale.
4. Alege cel mai mic pas sigur.
5. Oprește la mutație sau la lipsă de dovezi.
6. După mutație, cere validare oficială.
7. Nu promovează semantic starea fără dovadă verificabilă.
8. Sincronizează documentația oficială doar când statusul oficial chiar s-a schimbat.
```

## Project State Board

`Project State Board` este formatul standard prin care Robocop rezumă starea curentă a unui stage sau micro-stage.

Scop:

- separă starea oficială de comentarii;
- previne formulările ambigue;
- face clar dacă o etapă este doar implementată, validată, merge-uită sau încă pending.

Template standard:

```text
Project State Board

Stage:
State:
Scope:
Reference branch:
Reference PR:
Reference head:
Official validation source:
Evidence scope:
Known limits:
Next required action:
```

Reguli:

- `State` trebuie să fie unul explicit, nu formulări aproximative.
- `Official validation source` trebuie să indice workflow-ul sau documentul oficial, nu impresii locale.
- `Known limits` trebuie să arate clar ce nu este demonstrat.

## Evidence Ledger

`Evidence Ledger` este registrul standard pentru dovezi verificabile.

Scop:

- să arate ce a fost confirmat;
- să arate ce este doar observație locală;
- să prevină promovarea semantică din propoziții vagi.

Template standard:

```text
Evidence Ledger

Repository:
Branch or main reference:
Commit / head SHA:
Workflow:
Run id / run number:
Workflow conclusion:
Artifact:
Artifact inspection:
pytest evidence:
reference_comparison.md:
Generated DOCX / JSON evidence:
Scope of evidence:
What this evidence does not prove:
```

Reguli:

- dacă artifactul nu a fost inspectat, se spune explicit;
- dacă `reference_comparison.md` nu se aplică, se spune explicit;
- dacă dovada este locală, ea nu intră în ledger-ul oficial fără etichetare clară.

## Validation Semantics

Acest capitol este sursa canonică pentru semantica de validare.

Toate celelalte documente trebuie să citeze această secțiune, nu să o rescrie divergent.

Reguli canonice:

```text
merged != DONE
smoke green != release
local PASS != official validation
docs sync != feature validation
main validation > PR validation
workflow success != production-ready
status sync != product completion
```

Interpretare standard:

- `merged != DONE`:
  merge-ul arată integrare, nu închidere semantică automată.
- `smoke green != release`:
  un smoke test verde nu echivalează cu validare de release.
- `local PASS != official validation`:
  rularea locală ajută investigația, dar nu înlocuiește dovada oficială.
- `docs sync != feature validation`:
  actualizarea documentației nu validează funcționalitatea.
- `main validation > PR validation`:
  dovada pe `main` are prioritate operațională mai mare decât dovada limitată de PR.
- `workflow success != production-ready`:
  un workflow verde nu autorizează claim de release sau readiness operațional complet.
- `status sync != product completion`:
  sincronizarea de status consemnează, nu închide automat produsul.

Consecință:

Robocop nu folosește niciodată succesul parțial ca substitut semantic pentru o stare mai puternică.

## Drift Prevention Rules

Scopul acestor reguli este să prevină dublarea și rescrierea divergentă între documente.

Reguli:

1. Starea curentă a proiectului nu se copiază în documentele Robocop. Ea rămâne în `CHECKPOINT.md` și `README.md`.
2. Semantica de validare stă canonic aici.
3. Stop conditions exhaustive stau în `docs/robocop_stop_conditions.md`.
4. Responsabilitățile operator versus Robocop stau în `docs/robocop_preflight_roles_and_skills.md`.
5. Template-urile procedurale stau în `docs/robocop_operator_playbook.md`.
6. `README.md` rămâne punct de intrare și rezumat, nu devine manual procedural.
7. Dacă o regulă trebuie repetată într-un alt document, ea se rezumă și se citează, nu se rescrie extensiv.

Semne de drift:

- aceeași regulă apare în forme diferite;
- același template este copiat în mai multe locuri;
- un document procedural începe să păstreze stare oficială;
- README ajunge să concureze cu manualul sau playbook-ul.

Acțiune corectă la drift:

```text
identifică sursa canonică
scurtează copia
transformă restul în referință
```

## Documentation Ownership Map

Acest map arată unde trăiește fiecare categorie de conținut.

```text
Current project state -> CHECKPOINT.md / README.md
Canonical validation semantics -> docs/robocop_full_project_operating_system.md
Exhaustive stop conditions -> docs/robocop_stop_conditions.md
Responsibilities and role boundaries -> docs/robocop_preflight_roles_and_skills.md
Procedural templates and runbooks -> docs/robocop_operator_playbook.md
Normal operating procedures and operator wording -> docs/robocop_operating_manual.md
```

Regulă:

Niciun document nu trebuie să concureze cu alt document pe aceeași responsabilitate canonică.

## Relația cu celelalte documente

Acest document trebuie folosit împreună cu:

```text
docs/robocop_operating_manual.md
docs/robocop_stop_conditions.md
docs/robocop_preflight_roles_and_skills.md
docs/robocop_operator_playbook.md
```

Ordinea corectă este:

```text
1. model canonic
2. procedură normală
3. condiții de oprire
4. roluri și ownership
5. template-uri reutilizabile
```

## Principiu final

Robocop trebuie să rămână strict, verificabil și trasabil.

Orice formulare mai puternică decât dovada verificată este considerată deviație semantică și trebuie blocată.
