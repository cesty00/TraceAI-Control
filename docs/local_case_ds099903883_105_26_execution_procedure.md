# Procedură de execuție — caz local DS099903883 / lot 105.26

## 1. Scopul procedurii

Acest document definește procedura manuală repetabilă pentru executarea cazului local cu:

- cod produs: `DS099903883`
- lot: `105.26`

Scopul procedurii este să ofere un mod stabil de rulare a aceluiași caz, astfel încât rezultatele observate să poată fi comparate între rulări fără a modifica aplicația sau regulile de business.

Acest document este docs-only.

Nu schimbă aplicația.
Nu schimbă tests.
Nu schimbă workflow-uri.
Nu schimbă UI.
Nu schimbă rendererul DOCX.
Nu schimbă DTO/JSON contracts.
Nu schimbă calculations.
Nu schimbă source mappings.
Nu schimbă verdict rules.
Nu schimbă extraction logic.
Nu schimbă unit handling.
Nu schimbă `CHECKPOINT.md` sau `README.md`.

## 2. Referință la planul de validare

Această procedură trebuie folosită împreună cu:

- [docs/real_case_validation_plan.md](docs/real_case_validation_plan.md)

Dacă apar variații ale cazului local, ele trebuie documentate separat, nu amestecate în această procedură de bază.

## 3. Identificare caz

- Cod produs: `DS099903883`
- Lot: `105.26`
- Raport local anterior: `TEST2000.docx`
- Diagnostic local anterior: `TraceAI-Diagnostic-cod-lot-20260506T070322Z.zip`
- PDF fizic scanat: `SKM_36726050609130.pdf`

## 4. Clarificare despre PDF-ul scanat

PDF-ul poate apărea landscape sau rotit pentru că așa a fost scanat.

Orientarea PDF-ului scanat nu este bug TraceAI-Control în lipsa unei dovezi că aplicația a modificat incorect orientarea sau a introdus rotația.

## 5. Precondiții

Înainte de rulare, trebuie consemnate:

- versiune aplicație;
- commit/build folosit;
- sistem operare;
- folderul surselor;
- fișierele sursă necesare prezente în folder.

### Fișiere sursă necesare

Folderul folosit pentru caz trebuie verificat să conțină sursele oficiale relevante, folosind denumirile acceptate de aplicație, de tipul:

- `trasabilitate_wms.csv` sau alias acceptat;
- `raport_productie.csv` sau alias acceptat;
- `nomenclator.xlsx`;
- `stoc la moment original.xlsx` sau alias acceptat.

Dacă structura folderului sau numele fișierelor diferă, procedura trebuie oprită și cazul trebuie revalidat pe baza surselor reale disponibile.

## 6. Pași de execuție în UI

1. pornește aplicația;
2. selectează folderul surselor pentru cazul local;
3. introdu cod produs `DS099903883`;
4. introdu lot `105.26`;
5. rulează verificarea surselor / preflight;
6. generează preview / audit checklist;
7. generează raportul DOCX;
8. generează Diagnostic ZIP.

La fiecare pas, trebuie notat dacă aplicația:

- răspunde normal;
- afișează warning-uri explicite;
- afișează eroare clară și acționabilă;
- generează artefactul așteptat.

## 7. Rezultate așteptate

Pentru acest caz, rezultatele așteptate sunt:

- verdict: `PASS_WITH_OBSERVATIONS`;
- PRD produs: `734 Kilogram`;
- WMS PRODUCTION-OUT: `734 Kilogram`;
- WMS livrat: `-734 Kilogram`;
- Data Quality: `ERROR`;
- total constatări de date:
  - `1` eroare
  - `7` warning-uri
  - `8` issue-uri;
- PDF landscape nu se tratează ca defect TraceAI.

Dacă una dintre aceste așteptări se schimbă, schimbarea trebuie investigată și explicată înainte de a compara verdictul cu rulările anterioare.

## 8. Ce se verifică manual în DOCX

După generarea raportului, se verifică manual în DOCX:

- codul produsului și lotul;
- verdictul;
- secțiunea bilanț PRD vs WMS;
- aval: `3` livrări;
- amonte: `9` linii;
- consum pe comenzi: `21` rânduri;
- documente fizice: `15`;
- secțiunea `Data Quality issues`.

Dacă documentul nu conține aceste repere sau acestea nu sunt lizibile, cazul trebuie marcat pentru investigație înainte de orice concluzie de release readiness.

## 9. Ce se verifică în Diagnostic ZIP

După generarea Diagnostic ZIP, se verifică prezența elementelor de bază:

- `build_info.json`;
- `source_inventory.json`;
- `preflight.json`;
- `audit_checklist_ui.json`;
- `reports/TEST2000.docx` sau raportul generat la rularea curentă;
- `manifest.json`;
- `README.txt`.

Dacă una dintre aceste piese lipsește, trebuie notat dacă lipsa este explicabilă printr-un fișier de eroare sau dacă reprezintă o problemă de generare a diagnosticului.

## 10. Timpi observați

Dacă utilizatorul îi măsoară, se consemnează separat:

- timp pentru preflight;
- timp pentru preview;
- timp pentru DOCX;
- timp pentru Diagnostic ZIP;
- timp total.

Dacă timpii nu sunt măsurați, câmpurile pot rămâne necompletate fără a invalida procedura.

## 11. Criteriu de acceptare

Procedura este considerată acceptabilă dacă:

- este reproductibilă;
- raportul este generat;
- Diagnostic ZIP este generat;
- verdictul rămâne `PASS_WITH_OBSERVATIONS`;
- `Data Quality ERROR` este explicat, nu ascuns.

## 12. Criterii de fail

Procedura este considerată eșuată dacă:

- aplicația se blochează;
- nu generează DOCX;
- nu generează Diagnostic ZIP;
- verdictul devine `PASS` simplu fără justificare;
- PDF landscape este tratat ca bug TraceAI.

## 13. Notă explicită

Acest document nu consemnează încă execuția finală a cazului.

El doar definește procedura de execuție manuală pentru cazul local, astfel încât rularea să poată fi repetată și evaluată consecvent.