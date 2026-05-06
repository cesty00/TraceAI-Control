# REAL-CASE-VALIDATION-02 — Execution Record

## 1. Scopul documentului

Acest document înregistrează execuția manuală a validării definite în [docs/real_case_validation_plan.md](docs/real_case_validation_plan.md).

Scopul lui este să păstreze într-un singur loc rezultatele observate pentru UI, DOCX, `audit_checklist_ui.json` și Diagnostic ZIP, astfel încât evaluarea de release readiness să se bazeze pe dovezi concrete.

Acest document este docs-only.

Nu schimbă aplicația.
Nu schimbă engine.
Nu schimbă UI.
Nu schimbă rendererul DOCX.
Nu schimbă tests.
Nu schimbă workflow-uri.
Nu schimbă DTO/JSON contracts.
Nu schimbă calculations.
Nu schimbă source mappings.
Nu schimbă verdict rules.
Nu schimbă extraction logic.
Nu schimbă unit handling.
Nu schimbă `CHECKPOINT.md` sau `README.md`.

## 2. Referință la planul de validare

Execuția consemnată aici trebuie interpretată împreună cu:

- [docs/real_case_validation_plan.md](docs/real_case_validation_plan.md)
- [docs/local_case_ds099903883_105_26_execution_procedure.md](docs/local_case_ds099903883_105_26_execution_procedure.md)

Dacă apar cazuri noi, ele trebuie adăugate în plan înainte să fie folosite pentru concluzii de release readiness.

## 3. Informații execuție

Data testului: 2026-05-06

Tester:

Versiune aplicație:

Commit build:

Canal build:

Sistem operare:

Surse folosite:

Note generale de mediu:

## 4. Tabel de execuție pentru cazuri validate

| Case ID | Scenariu | Cod produs | Lot | Inputuri | Rezultat UI | DOCX generat | audit_checklist_ui.json generat | Diagnostic ZIP generat | Verdict | Data Quality status | Timp execuție observat | Observații | Decizie |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| RCV-01 | FINISHED_PRODUCT complet |  |  |  |  |  |  |  |  |  |  |  | PASS / PASS_WITH_OBSERVATIONS / FAIL |
| RCV-02 | FINISHED_PRODUCT incomplet |  |  |  |  |  |  |  |  |  |  |  | PASS / PASS_WITH_OBSERVATIONS / FAIL |
| RCV-03 | WMS-only / PRD missing |  |  |  |  |  |  |  |  |  |  |  | PASS / PASS_WITH_OBSERVATIONS / FAIL |
| RCV-04 | no matching records |  |  |  |  |  |  |  |  |  |  |  | PASS / PASS_WITH_OBSERVATIONS / FAIL |
| RCV-05 | corrupt/unreadable official source |  |  |  |  |  |  |  |  |  |  |  | PASS / PASS_WITH_OBSERVATIONS / FAIL |
| RCV-06 | Caz local utilizator | DS099903883 | 105.26 | folder local utilizator; surse oficiale locale; PDF fizic scanat | preview și raport generate; rezultat controlat cu observații | Da, `TEST2000.docx` | Da | Da, `TraceAI-Diagnostic-cod-lot-20260506T070322Z.zip` | `PASS_WITH_OBSERVATIONS` | `ERROR` | UI timings: not measured in this execution | PDF scanat landscape/rotit; Data Quality explicit; rezultat păstrat pentru analiză | PASS_WITH_OBSERVATIONS |

## 5. Secțiune specială — Caz local utilizator

### Identificare caz

- Cod produs: `DS099903883`
- Lot: `105.26`
- Raport generat: `TEST2000.docx`
- Diagnostic ZIP: `TraceAI-Diagnostic-cod-lot-20260506T070322Z.zip`
- PDF fizic scanat: `SKM_36726050609130.pdf`

### Rezultat observat

- Verdict: `PASS_WITH_OBSERVATIONS`
- PRD produs: `734 Kilogram`
- WMS PRODUCTION-OUT: `734 Kilogram`
- WMS livrat: `-734 Kilogram`
- Aval: `3` livrări
- Amonte: `9` linii
- Consum pe comenzi: `21` rânduri
- Documente fizice: `15`
- Data Quality: `ERROR`
- Total constatări Data Quality:
  - `1` eroare
  - `7` warning-uri
  - `8` issue-uri

### Observații explicite

- PDF-ul fizic scanat este landscape/rotit din cauza orientării de scanare.
- Acest comportament nu este bug TraceAI-Control în lipsa unei dovezi că aplicația a modificat incorect orientarea.
- `PASS_WITH_OBSERVATIONS` rămâne acceptabil pentru acest caz deoarece rezultatul principal este coerent, iar problema de `Data Quality: ERROR` rămâne explicită și nu este ascunsă.
- Diagnostic ZIP este parte obligatorie a dovezii pentru acest caz, tocmai pentru că există `Data Quality: ERROR`.

### Verificări manuale consemnate

- cod produs și lot confirmate în rulare;
- verdictul confirmat ca `PASS_WITH_OBSERVATIONS`;
- bilanț PRD vs WMS verificat pe valorile observate;
- aval verificat: `3` livrări;
- amonte verificat: `9` linii;
- consum pe comenzi verificat: `21` rânduri;
- documente fizice verificate: `15`;
- secțiunea `Data Quality issues` prezentă și explicită.

### Dovezi atașate pentru acest caz

- rezultat UI observat
- `TEST2000.docx`
- `audit_checklist_ui.json`
- `TraceAI-Diagnostic-cod-lot-20260506T070322Z.zip`
- `SKM_36726050609130.pdf`

## 6. Semnătură / aprobare

Tester:

Reviewer:

Decizie:

Data:

## 7. Blocaje și observații

### Ce blochează release candidate

Se consemnează aici doar problemele care blochează efectiv un release candidate sau un pas înainte în release readiness, de exemplu:

- caz obligatoriu nerespectat față de plan;
- DOCX și UI JSON contradictorii pe un caz critic;
- lipsa Diagnostic ZIP pentru un caz cu eroare de date;
- eroare neacționabilă într-un scenariu care ar trebui să fie clar pentru operator;
- lipsa dovezilor minime pentru cazurile din matrice.

### Ce este doar observație

Se consemnează aici probleme sau particularități care nu schimbă verdictul principal al cazului, de exemplu:

- warning-uri explicite de Data Quality fără impact fals asupra concluziei;
- PDF scanat landscape/rotit din cauza scannerului;
- mici observații de prezentare care nu schimbă interpretarea auditului.

## 8. Release impact

`PASS_WITH_OBSERVATIONS` este acceptabil ca observație controlată pentru acest caz.

`Data Quality: ERROR` trebuie explicat explicit și trebuie însoțit de Diagnostic ZIP.

Acest rezultat nu declară `daily-use internal release`.

## 9. Timpi observați

UI timings: not measured in this execution.

## 10. Notă explicită

Acest document nu declară `daily-use internal release`.

Acest document nu marchează nicio etapă de produs ca `DONE`.

El doar înregistrează execuția manuală a validării și rezultatele observate, pentru a putea susține o evaluare ulterioară de release readiness.