# REAL-TEST-PILOT-01 — Checklist operativ scurt pentru operator

Folosește acest checklist doar pentru cazul:

- cod produs: `DS099903883`
- lot: `105.26`

## Înainte de rulare

- aplicația pornește normal;
- build / versiune vizibilă, dacă există;
- folderul surselor este cel corect;
- sursele oficiale sunt prezente:
  - `trasabilitate_wms.csv` sau alias acceptat
  - `raport_productie.csv` sau alias acceptat
  - `nomenclator.xlsx`
  - `stoc_la_moment_original.xlsx` sau alias acceptat

## Pași

1. selectează folderul surselor;
2. introdu cod produs `DS099903883`;
3. introdu lot `105.26`;
4. rulează preflight / verificare surse;
5. generează preview / audit checklist;
6. generează raportul DOCX;
7. verifică reperele principale;
8. generează Diagnostic ZIP dacă este necesar;
9. păstrează artifactele.

## Repere principale de verificat

- verdictul rămâne `PASS_WITH_OBSERVATIONS`;
- PRD produs = `734 Kilogram`;
- WMS PRODUCTION-OUT = `734 Kilogram`;
- WMS livrat = `-734 Kilogram`;
- aval = `3` livrări;
- amonte = `9` linii;
- consum pe comenzi = `21` rânduri;
- documente fizice = `15`;
- `Data Quality: ERROR` este explicit, nu ascuns.

## Când generezi obligatoriu Diagnostic ZIP

- apare eroare sau blocaj;
- preview-ul nu arată cazul așteptat;
- DOCX-ul nu arată cazul așteptat;
- `Data Quality: ERROR` este prezent;
- cazul trebuie trimis la suport / analiză.

## Ce păstrezi

- DOCX-ul generat;
- Diagnostic ZIP complet, dacă a fost generat;
- `audit_checklist_ui.json`;
- `preflight.json`;
- `source_inventory.json`;
- `build_info.json`;
- observațiile operatorului.

## Verdict operativ

- `PASS`: cazul este coerent și artifactele minime există;
- `BLOCKED`: nu poți continua corect;
- `ISSUE FOUND`: rularea se termină, dar apare o problemă reală de investigat.

## Notă

Acest checklist nu declară:

- `production-ready`
- `daily-use internal release`
- `release finalized`
- etapă produs `DONE`
