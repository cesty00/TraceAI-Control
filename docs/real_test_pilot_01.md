# REAL-TEST-PILOT-01 — Pilot real controlat

## 1. Scop

Acest document definește `REAL-TEST-PILOT-01` ca pasul oficial următor după sync-ul de status pentru `PREFLIGHT-UI-01A`.

Scopul pilotului este să execute un caz real controlat cap-coadă în UI, cu sursele oficiale reale, și să păstreze dovezile necesare pentru evaluarea controlată a comportamentului aplicației.

Acest document este docs-only.

Nu schimbă aplicația.
Nu schimbă logică de business.
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

## 2. Cazul real testat

`REAL-TEST-PILOT-01` se execută pe cazul real controlat deja documentat în repo:

- cod produs: `DS099903883`
- lot: `105.26`

Acest pilot folosește exact cazul local deja referențiat în:

- `docs/local_case_ds099903883_105_26_execution_procedure.md`
- `docs/real_case_validation_execution_record.md`

Nu se amestecă în același pilot alte produse, alte loturi sau alte scenarii.

## 3. Surse oficiale folosite

Pilotul folosește doar sursele oficiale relevante pentru caz, din folderul real ales de operator:

- `trasabilitate_wms.csv` sau alias acceptat;
- `raport_productie.csv` sau alias acceptat;
- `nomenclator.xlsx`;
- `stoc_la_moment_original.xlsx` sau alias acceptat.

Sursele auxiliare, scanările și documentele fizice pot fi folosite pentru comparație manuală sau suport, dar sursa oficială de adevăr pentru rularea aplicației rămâne setul oficial de mai sus.

Dacă una dintre sursele oficiale lipsește, este coruptă sau ilizibilă, pilotul nu inventează completări și nu schimbă sursele. Cazul intră în `BLOCKED` sau `ISSUE FOUND`, după regulile din acest document.

## 4. Operatorul și pașii exacți

Operatorul rulează pilotul manual, pas cu pas, fără improvizații și fără a schimba structura surselor în timpul aceleiași execuții.

Pașii sunt:

1. pornește aplicația care urmează să fie evaluată;
2. notează versiunea, commitul build și canalul build dacă sunt vizibile;
3. selectează folderul real al surselor pentru cazul `DS099903883 / 105.26`;
4. verifică vizual că folderul conține sursele oficiale așteptate;
5. introduce cod produs `DS099903883`;
6. introduce lot `105.26`;
7. rulează verificarea surselor / preflight;
8. notează dacă preflight-ul arată stări operator-facing coerente;
9. generează preview / audit checklist;
10. generează raportul DOCX;
11. inspectează rezultatul UI și rezultatul DOCX la nivel de repere principale;
12. generează Diagnostic ZIP dacă se aplică regulile de mai jos;
13. păstrează artifactele definite în acest document;
14. completează rezultatul în execution record.

Operatorul nu modifică manual fișiere din ZIP și nu redenumește artifactele interne.

## 5. Artifacte care se păstrează

Artifactele minime de păstrat pentru `REAL-TEST-PILOT-01` sunt:

- raportul DOCX generat la rularea curentă;
- `audit_checklist_ui.json`, direct sau prin Diagnostic ZIP;
- `preflight.json`, direct sau prin Diagnostic ZIP;
- `source_inventory.json`, direct sau prin Diagnostic ZIP;
- `build_info.json`, direct sau prin Diagnostic ZIP;
- `manifest.json`, prin Diagnostic ZIP;
- `README.txt`, prin Diagnostic ZIP;
- execution record actualizat pentru pilot;
- opțional PDF-ul fizic scanat, dacă este folosit în comparația manuală.

Dacă Diagnostic ZIP este generat, ZIP-ul complet se păstrează integral. Nu se extrag selectiv doar câteva fișiere ca dovadă principală.

## 6. Rezultatul pilotului: PASS / BLOCKED / ISSUE FOUND

### PASS

Pilotul este `PASS` dacă toate condițiile de mai jos sunt simultan adevărate:

- aplicația rămâne utilizabilă pe tot parcursul rulării;
- preflight-ul oferă un rezultat coerent pentru sursele reale observate;
- preview / audit checklist se generează;
- DOCX-ul se generează;
- reperele principale ale cazului sunt coerente cu rezultatul deja documentat pentru acest caz;
- eventualele probleme de `Data Quality` sunt explicite, nu ascunse;
- artifactele minime definite mai sus sunt păstrate.

### BLOCKED

Pilotul este `BLOCKED` dacă execuția nu poate continua corect din cauza unui blocaj care împiedică evaluarea cazului, de exemplu:

- sursă oficială obligatorie lipsă;
- sursă oficială coruptă / ilizibilă;
- aplicația nu pornește;
- aplicația nu poate rula preflight-ul pentru caz;
- aplicația nu poate genera preview sau DOCX;
- operatorul nu poate păstra artifactele minime cerute.

`BLOCKED` înseamnă că pilotul nu poate produce o concluzie de comportament acceptabil pentru caz, nu că etapa produs este automat respinsă definitiv.

### ISSUE FOUND

Pilotul este `ISSUE FOUND` dacă execuția se termină, dar scoate la iveală o problemă reală care cere investigație, de exemplu:

- preflight-ul afișează informații înșelătoare sau incoerente față de sursele reale;
- preview-ul și DOCX-ul se contrazic;
- datele principale ale cazului se abat neexplicat de la rezultatul deja documentat;
- apare un mesaj neacționabil pentru operator;
- Diagnostic ZIP sau artifactele rezultate arată o problemă de trasabilitate, de prezentare sau de consistență care nu blochează rularea, dar este totuși defect.

## 7. Când se generează Diagnostic ZIP

Diagnostic ZIP se generează obligatoriu în oricare dintre situațiile de mai jos:

- apare un `BLOCKED`;
- apare un `ISSUE FOUND`;
- `Data Quality` este marcat `ERROR` sau există constatări care trebuie investigate;
- preview-ul sau DOCX-ul nu arată cazul așteptat;
- operatorul trebuie să trimită cazul mai departe pentru suport sau analiză.

Diagnostic ZIP poate fi generat și pe un rezultat `PASS` dacă proiectul vrea o arhivă completă a rulării pilot, dar nu este obligatoriu dacă nu există semne de problemă și dacă execution record-ul este complet.

## 8. Repere minime pentru comparația pe acest caz

Pentru cazul `DS099903883 / 105.26`, pilotul trebuie comparat cu reperele deja documentate în repo:

- verdict observat: `PASS_WITH_OBSERVATIONS`;
- PRD produs: `734 Kilogram`;
- WMS PRODUCTION-OUT: `734 Kilogram`;
- WMS livrat: `-734 Kilogram`;
- aval: `3` livrări;
- amonte: `9` linii;
- consum pe comenzi: `21` rânduri;
- documente fizice: `15`;
- `Data Quality: ERROR` explicit.

Aceste repere nu transformă pilotul într-o validare automată. Ele sunt baza de comparație pentru a vedea dacă rularea curentă rămâne coerentă cu cazul real deja documentat.

## 9. Ce se completează după execuție

După rulare, operatorul sau reviewerul actualizează execution record cu:

- data execuției;
- mediul folosit;
- artifactele păstrate;
- rezultatul final `PASS`, `BLOCKED` sau `ISSUE FOUND`;
- observațiile explicite;
- motivul pentru generarea sau negenerarea Diagnostic ZIP.

## 10. Limită explicită

`REAL-TEST-PILOT-01` nu declară:

- `production-ready`;
- `daily-use internal release`;
- `release finalized`;
- promovarea automată a unei etape produs la `DONE`.

Acest pilot definește doar execuția controlată a unui caz real și dovada minimă care trebuie păstrată pentru evaluarea lui.