# CHECKPOINT — TraceAI Control Modul Trasabilitate

Data checkpoint: 2026-04-29

## Status general

Proiectul este în repo-ul:

```text
cesty00/TraceAI-Control
```

Stadiul curent este:

```text
Faza 0 — Documentație și arhitectură inițială: finalizată
Faza 1 — Schelet repo: finalizată
Faza 2 — Core Engine: implementată tehnic v1
Faza 3 — Rules Engine: implementată tehnic v1
Faza 4 — TraceabilityCase: contract + report_tables + populare controlată + reguli clasificare + bilanț preliminar conservator implementate
Faza 5 — Report Engine DOCX: implementată tehnic v1 narativ + tabele Word reale + șablon profesional minimal + bilanț preliminar randat
Faza 5.1 — Flux E2E controlat DOCX: implementat tehnic
Faza 5.2 — Runner demonstrativ DOCX controlat: implementat tehnic + test automat dedicat + documentație de utilizare
Faza 5.3 — README principal sincronizat cu statusul curent și runnerul demonstrativ
Faza 6.0 — Contract minim UI -> engine: definit și documentat
Faza 6.1 — Funcție UI de orchestrare testabilă: implementată tehnic + documentată
Faza 6.2 — CLI/UI shell minimal peste orchestrator: implementat tehnic + testat + documentat
Faza 6.3 — UI vizual minimal peste orchestrator: implementat tehnic + testat + documentat
Faza 7.0 — Pregătire installer Windows: script PyInstaller + documentație integrate
Faza 7.1 — Script Windows build rafinat: entry point explicit + verificare înainte de build
Faza 7.2 — Verificare build Windows: script PowerShell + documentație integrate
Faza 7.3 — Pregătire installer Inno Setup: script .iss + build PowerShell + documentație integrate
Faza 7.4 — Checklist validare Windows: integrat
Faza 7.5 — Șablon rezultat validare Windows: integrat
Faza 7.6 — Issue GitHub validare Windows reală: #37 deschis și documentat
Faza 7.7 — GitHub Actions Windows installer artifact: workflow integrat
Installer Windows complet: pregătit tehnic, dar NEVALIDAT încă pe Windows real
```

## Decizie principală

UI-ul vizual există doar ca strat peste orchestrator. Installerul, verificarea buildului, workflow-ul GitHub Actions și documentele de validare nu introduc logică de business.

Ordinea proiectului este:

```text
Documentație
Core Engine
Rules Engine
TraceabilityCase
Teste automate
Report Engine DOCX
Flux E2E controlat
Runner demonstrativ DOCX
Documentație runner demonstrativ
README principal sincronizat
Contract UI -> engine
Funcție UI de orchestrare testabilă
CLI/UI shell minimal
UI vizual minimal
Pregătire installer Windows
Rafinare script Windows build
Verificare build Windows
Pregătire installer Inno Setup
Checklist validare Windows
Șablon rezultat validare Windows
Issue GitHub validare Windows reală
Workflow GitHub Actions pentru artifact installer
Validare reală Windows
Icon / semnare
```

## Reguli critice validate

1. Gazul ALISOL este auxiliar / consumabil tehnologic.
2. Gazul nu intră niciodată la materii prime alimentare.
3. Unitățile de măsură nu se convertesc automat.
4. Dacă o secțiune nu are date, raportul trebuie să spună explicit acest lucru.
5. Raportul DOCX trebuie să fie narativ și auditabil, nu un Excel copiat în Word.
6. DOCX-ul se generează din TraceabilityCase, nu direct din fișiere.
7. UI-ul nu conține logică de business.
8. Bilanțul preliminar este conservator și nu deduce fluxuri lipsă.
9. Fluxul E2E controlat folosește date sintetice de test, nu UI și nu fișiere operaționale reale.
10. Runnerul demonstrativ folosește dataset sintetic controlat și nu schimbă regulile de business.
11. Documentația runnerului explică explicit că demo-ul nu citește surse operaționale reale.
12. README.md principal reflectă statusul tehnic curent și nu mai conține status vechi de pre-cod.
13. Contractul UI -> engine limitează UI-ul la colectare input, apel engine și afișare succes/eroare.
14. Funcția UI de orchestrare nu citește direct sursele și nu conține logică de business.
15. Documentația UI explică explicit `UiGenerationRequest`, `UiGenerationResult` și `generate_report_from_ui_request()`.
16. CLI/UI shell-ul minimal apelează doar orchestratorul și nu conține logică de business.
17. UI-ul vizual minimal apelează doar orchestratorul și nu conține logică de business.
18. Scriptul Windows build pornește de la UI-ul vizual minimal și nu schimbă engine-ul.
19. Scriptul Windows build folosește entry point explicit `src\ui\visual.py` și verifică existența lui înainte de build.
20. Scriptul de verificare Windows build verifică doar artefactul rezultat și nu pornește automat UI-ul / engine-ul.
21. Scriptul Inno Setup împachetează executabilul PyInstaller existent și nu introduce logică de business.
22. Checklistul de validare Windows definește pașii reali de acceptare fără workaround-uri în UI sau installer.
23. Șablonul rezultatului de validare documentează verdictul ACCEPTED / REJECTED fără a marca validarea ca efectuată.
24. Issue-ul #37 urmărește validarea reală Windows fără a marca validarea ca finalizată.
25. Workflow-ul GitHub Actions construiește artifactul installer pe runner Windows și nu marchează validarea reală ca finalizată.

## Structura repo la checkpoint

```text
TraceAI-Control/
  README.md
  CHECKPOINT.md
  .github/
    workflows/
      windows-installer.yml
  docs/
    UI_ENGINE_CONTRACT.md
  installer/
    windows/
      README.md
      TraceAI-Control.iss
      VALIDATION_CHECKLIST.md
      VALIDATION_RESULT_TEMPLATE.md
      build_inno_setup.ps1
      build_windows.ps1
      verify_windows_build.ps1
  src/
    core/
    rules/
    report/
    ui/
      README.md
      __init__.py
      cli.py
      orchestrator.py
      visual.py
  tests/
    README.md
    test_source_inventory.py
    test_normalized_dataset.py
    test_dataset_validation.py
    test_record_selection.py
    test_run_pipeline.py
    test_case_type_detection.py
    test_run_rules_pipeline.py
    test_traceability_case.py
    test_run_traceability_case.py
    test_docx_minimal.py
    test_e2e_docx_controlled_flow.py
    test_demo_docx_runner.py
    test_ui_orchestrator.py
    test_ui_cli.py
    test_ui_visual.py
  samples/
    README.md
    demo_docx_runner.py
```

## Build, verificare, installer, workflow și validare Windows integrate

Implementare:

```text
installer/windows/build_windows.ps1
installer/windows/verify_windows_build.ps1
installer/windows/TraceAI-Control.iss
installer/windows/build_inno_setup.ps1
installer/windows/VALIDATION_CHECKLIST.md
installer/windows/VALIDATION_RESULT_TEMPLATE.md
.github/workflows/windows-installer.yml
```

Documentație:

```text
installer/windows/README.md
README.md
```

Issue tracking validare reală:

```text
#37 — Validate Windows build and installer on a real Windows machine
https://github.com/cesty00/TraceAI-Control/issues/37
```

Build installer prin GitHub Actions:

```text
Actions -> Build Windows Installer -> Run workflow
```

Artifact descărcabil după workflow:

```text
TraceAI-Control-Windows-Installer
```

Conține:

```text
TraceAI-Control-Setup.exe
```

Build executabil PyInstaller local:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_windows.ps1
```

Verificare build local:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\verify_windows_build.ps1
```

Build installer Inno Setup local:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\windows\build_inno_setup.ps1
```

Checklist validare Windows:

```text
installer/windows/VALIDATION_CHECKLIST.md
```

Șablon rezultat validare Windows:

```text
installer/windows/VALIDATION_RESULT_TEMPLATE.md
```

Entry point PyInstaller:

```text
src\ui\visual.py
```

Output executabil așteptat:

```text
dist\TraceAI-Control\TraceAI-Control.exe
```

Output installer local așteptat:

```text
installer\windows\output\TraceAI-Control-Setup.exe
```

Limitări installer curente:

```text
nu există încă semnare executabil
nu există icon final
nu există validare reală finalizată pe o mașină Windows
issue-ul #37 este deschis pentru validarea reală
```

## Testare curentă

Testele unitare și E2E controlate acoperă modulele Core, Rules, TraceabilityCase, bilanț preliminar conservator, Report Engine DOCX, fluxul controlat TraceabilityCase -> DOCX, runnerul demonstrativ, funcția UI de orchestrare, CLI/UI shell-ul minimal și UI-ul vizual minimal:

```text
python -m pytest -q
39 passed
```

## Limită curentă

Nu există încă:

```text
trasabilitate amonte/aval calculată
bilanțuri detaliate / reconciliere operațională completă
branding complet / logo / paginare avansată / cuprins automat
validare reală installer Windows
semnare executabil
icon final
```

## Următorul pas la reluare

Următorul pas corect este:

```text
rularea workflow-ului GitHub Actions Build Windows Installer, descărcarea artifactului TraceAI-Control-Windows-Installer și testarea lui pe mașina Windows reală
```

Primul cod permis după validare:

```text
installer/windows/VALIDATION_RESULT_TEMPLATE.md
installer/windows/README.md
README.md
CHECKPOINT.md
```

Regulă importantă:

```text
Nu se adaugă logică de business în installer.
Installerul trebuie să pornească UI-ul vizual minimal existent.
UI-ul vizual trebuie să apeleze același generate_report_from_ui_request().
DOCX rămâne generat din TraceabilityCase, nu direct din fișierele sursă.
Bilanțul preliminar rămâne conservator și nu convertește unități de măsură automat.
```

## Fraza de reluare recomandată

```text
Continuăm de la CHECKPOINT.md cu rularea workflow-ului Build Windows Installer, descărcarea artifactului și validarea pe Windows real.
```
