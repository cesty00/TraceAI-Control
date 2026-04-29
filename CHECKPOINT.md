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
Faza 7.8 — Installer Windows rulat de utilizator și raport real generat pentru DS099903883 / 105.26
Faza 5.4 — Randare DOCX tabele cu lookup normalizat pentru coloane: integrată parțial
Installer Windows complet: funcțional pentru generare raport, dar validarea formală #37 rămâne de completat
```

## Decizie principală

UI-ul vizual există doar ca strat peste orchestrator. Installerul, verificarea buildului, workflow-ul GitHub Actions și documentele de validare nu introduc logică de business.

Raportul real pentru `DS099903883 / 105.26` confirmă că aplicația instalată poate genera DOCX, iar bilanțul preliminar este prezent în raport.

## Rezultat test real utilizator — DS099903883 / 105.26

Utilizatorul a rulat aplicația instalată pe o mașină Windows reală și a generat raport DOCX pentru:

```text
Cod articol: DS099903883
Lot: 105.26
```

Raportul generat conține:

```text
Tip caz: WMS_ONLY_PRODUCT
Status validare Core: INVALID
Număr înregistrări selectate: 29
Surse utilizate: WMS
Bilanț preliminar prezent
```

Bilanțul preliminar vizibil în raport:

```text
Livrări produs finit: -734 Kilogram
Ambalaje: 1017 Kilogram
Recepții WMS: 1919 Kilogram
```

După corecția `src/report/docx_minimal.py`, tabelele DOCX au început să afișeze valori reale din WMS:

```text
Livrări produs finit:
WME111147 / 38748 / -33 Kilogram
WME111147 / 38748 / -176 Kilogram
WME111146 / 38760 / -74 Kilogram
WME111148 / 38770 / -109 Kilogram

Recepții WMS:
M31__F619CF60 / 168 Kilogram
M31__F619CF60 / 74 Kilogram
M9__28FD80CE / 209 Kilogram
M9__212C98D2 / 242 Kilogram
```

Mapping WMS este îmbunătățit parțial, dar nu este complet.

Câmpuri încă incomplete în raport:

```text
Client
Furnizor
Document intrare
unele coduri / denumiri pentru ambalaje
```

## Ordinea proiectului

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
Test real utilizator pe Windows
Îmbunătățire mapping WMS în DOCX
Validare formală #37
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
19. Scriptul Windows build folosește entry point explicit `src\\ui\\visual.py` și verifică existența lui înainte de build.
20. Scriptul de verificare Windows build verifică doar artefactul rezultat și nu pornește automat UI-ul / engine-ul.
21. Scriptul Inno Setup împachetează executabilul PyInstaller existent și nu introduce logică de business.
22. Checklistul de validare Windows definește pașii reali de acceptare fără workaround-uri în UI sau installer.
23. Șablonul rezultatului de validare documentează verdictul ACCEPTED / REJECTED fără a marca validarea ca efectuată.
24. Issue-ul #37 urmărește validarea reală Windows fără a marca validarea formală ca finalizată.
25. Workflow-ul GitHub Actions construiește artifactul installer pe runner Windows și nu marchează validarea reală ca finalizată.
26. Report Engine citește în continuare doar din TraceabilityCase; lookup-ul normalizat al coloanelor este randare, nu business logic.

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
      docx_minimal.py
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

## Build, installer și test Windows

Implementare:

```text
installer/windows/build_windows.ps1
installer/windows/verify_windows_build.ps1
installer/windows/TraceAI-Control.iss
installer/windows/build_inno_setup.ps1
.github/workflows/windows-installer.yml
```

Workflow GitHub Actions:

```text
Actions -> Build Windows Installer -> Run workflow
```

Artifact descărcabil:

```text
TraceAI-Control-Windows-Installer
```

Conține:

```text
TraceAI-Control-Setup.exe
```

Issue tracking validare formală:

```text
#37 — Validate Windows build and installer on a real Windows machine
https://github.com/cesty00/TraceAI-Control/issues/37
```

Status practic:

```text
Utilizatorul a rulat installerul și a generat raport real.
Validarea formală #37 trebuie încă completată în șablonul de rezultat.
```

## Testare curentă

Pe GitHub Actions Windows, testele au raportat anterior:

```text
42 passed, 4 failed
```

Cele 4 eșecuri observate sunt cross-platform / randare și trebuie tratate separat:

```text
test_demo_docx_runner_generates_valid_demo_report
test_e2e_controlled_traceability_case_to_docx
test_normalized_dataset_preserves_values_and_builds_hints
test_generate_report_from_ui_request_orchestrates_existing_engine
```

Workflow-ul de installer rulează testele ca diagnostic non-blocking pentru a permite generarea artifactului Windows.

## Limită curentă

Nu există încă:

```text
trasabilitate amonte/aval calculată
bilanțuri detaliate / reconciliere operațională completă
mapping WMS complet pentru Client / Furnizor / Document intrare
branding complet / logo / paginare avansată / cuprins automat
validare formală #37 completată
semnare executabil
icon final
```

## Următorul pas la reluare

Următorul pas corect este:

```text
continuarea mapping-ului WMS pentru raportul DS099903883 / 105.26: Client, Furnizor, Document intrare și coduri / denumiri ambalaje
```

Primul cod permis la reluare:

```text
src/rules/traceability_case.py
src/report/docx_minimal.py
tests/
README.md
CHECKPOINT.md
```

Regulă importantă:

```text
Nu se adaugă logică de business în UI sau installer.
Installerul trebuie să pornească UI-ul vizual minimal existent.
UI-ul vizual trebuie să apeleze același generate_report_from_ui_request().
DOCX rămâne generat din TraceabilityCase, nu direct din fișierele sursă.
Bilanțul preliminar rămâne conservator și nu convertește unități de măsură automat.
Mapping-ul WMS trebuie testat controlat și documentat.
```

## Fraza de reluare recomandată

```text
Continuăm de la CHECKPOINT.md cu raportul DS099903883 / 105.26: mapping WMS parțial reparat, urmează Client, Furnizor, Document intrare și coduri / denumiri ambalaje.
```
