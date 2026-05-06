# REAL-CASE-VALIDATION-01 — Plan de validare reală

## Scope

Acest document definește un plan docs-only pentru validare reală sau cu fixture-uri anonimizate înainte de o eventuală promovare către uz intern zilnic.

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

## 1. Scopul validării

Scopul validării este să confirme că `main` curent poate fi evaluat pe cazuri reale sau pe fixture-uri anonimizate reprezentative, fără a produce concluzii false pentru audit și fără a ascunde blocajele reale de date.

Această validare urmărește simultan:

- comportamentul din UI pentru operator;
- comportamentul din raportul DOCX generat;
- comportamentul din `audit_checklist_ui.json`;
- conținutul util al Diagnostic ZIP;
- verdictul final acceptabil pentru un release intern controlat.

## 2. Criterii de acceptare pentru release intern

Pentru un release intern controlat, planul de validare este considerat acoperit doar dacă:

- fiecare caz din matrice este rulat și documentat;
- rezultatul real este notat pentru UI, DOCX, `audit_checklist_ui.json` și Diagnostic ZIP;
- cazurile de succes nu ascund probleme de date;
- cazurile de eroare rămân explicite și acționabile pentru operator;
- cazurile incomplete păstrează marcajele de audit necesare;
- cazurile cu surse corupte sau ilizibile produc dovezi utile pentru suport;
- fiecare rezultat este clasificat ca `PASS`, `PASS_WITH_OBSERVATIONS` sau `FAIL`.

Release-ul intern nu trebuie propus pe baza unei singure rulări reușite. Acceptarea cere acoperire minimă pe toate scenariile din matrice.

## 3. Matricea de cazuri

### Caz 1 — FINISHED_PRODUCT complet

Inputuri necesare:

- folder cu surse oficiale complete pentru un produs finit;
- `trasabilitate_wms.csv` sau alias acceptat;
- `raport_productie.csv` sau alias acceptat;
- `nomenclator.xlsx`;
- `stoc la moment original.xlsx` sau alias acceptat;
- cod și lot valide pentru un caz complet.

Comportament așteptat în UI:

- `Verifică surse` nu raportează blocaj critic;
- preview-ul se poate deschide;
- `Generează raport DOCX` finalizează cu succes;
- `Generează Diagnostic ZIP` poate genera pachetul fără a bloca fluxul.

Comportament așteptat în DOCX:

- raportul se generează;
- produsul, codul și lotul corespund cazului;
- nu apare marcaj `INCOMPLETE` dacă dovezile esențiale sunt complete;
- secțiunile principale sunt coerente pentru audit.

Comportament așteptat în audit_checklist_ui.json:

- payload-ul se generează;
- secțiunile există și sunt coerente cu cazul;
- lipsurile, dacă există, rămân explicite și nu sunt mascate.

Diagnostic ZIP așteptat:

- `build_info.json`
- `source_inventory.json`
- `preflight.json`
- `audit_checklist_ui.json`
- `manifest.json`
- `README.txt`
- opțional raport DOCX în `reports/`

Verdict acceptat:

- `PASS`
- `PASS_WITH_OBSERVATIONS` doar dacă există warning-uri explicite care nu schimbă concluzia de audit.

Ce blochează release-ul:

- raportul nu se generează;
- cazul complet este marcat fals ca `INCOMPLETE`;
- payload-ul UI și DOCX se contrazic;
- Diagnostic ZIP nu poate fi generat pentru suport.

### Caz 2 — FINISHED_PRODUCT incomplet

Inputuri necesare:

- folder cu surse reale sau anonimizate pentru un produs finit cu dovezi esențiale lipsă;
- cod și lot valide pentru cazul incomplet.

Comportament așteptat în UI:

- operatorul poate ajunge la preview sau la generare dacă datele minime permit;
- cazul nu trebuie prezentat ca fiind complet dacă dovezile esențiale lipsesc.

Comportament așteptat în DOCX:

- raportul trebuie să marcheze explicit `INCOMPLETE` pentru cazul `FINISHED_PRODUCT` cu dovezi esențiale lipsă.

Comportament așteptat în audit_checklist_ui.json:

- lipsurile rămân explicite;
- nu apare o concluzie care să sugereze fals că setul este complet.

Diagnostic ZIP așteptat:

- fișierele standard disponibile;
- manifestul și preflight-ul reflectă lipsurile sau warning-urile observate.

Verdict acceptat:

- `PASS` dacă marcajul `INCOMPLETE` este corect și coerent;
- `PASS_WITH_OBSERVATIONS` dacă există warning-uri suplimentare explicite.

Ce blochează release-ul:

- caz incomplet prezentat ca și cum ar fi complet;
- lipsurile nu sunt vizibile în UI, DOCX sau payload-ul de audit.

### Caz 3 — WMS-only / PRD missing

Inputuri necesare:

- folder cu WMS disponibil;
- PRD lipsă sau indisponibil;
- cod și lot pentru care există urme în WMS.

Comportament așteptat în UI:

- operatorul primește un rezultat explicit despre date lipsă, nu un succes fals;
- dacă fluxul continuă până la preview, lipsurile trebuie să fie vizibile.

Comportament așteptat în DOCX:

- lipsurile rămân explicite;
- nu trebuie inventată dovadă upstream sau producție lipsă.

Comportament așteptat în audit_checklist_ui.json:

- câmpurile fără bază rămân explicite;
- `FARA DATE IDENTIFICATE` rămâne vizibil unde se aplică.

Diagnostic ZIP așteptat:

- inventarul surselor și preflight-ul trebuie să ajute suportul să vadă că PRD lipsește.

Verdict acceptat:

- `PASS_WITH_OBSERVATIONS` dacă lipsa este raportată clar și fără concluzii false;
- `FAIL` dacă lipsa este ascunsă sau compensată incorect.

Ce blochează release-ul:

- aplicația deduce fals date lipsă;
- UI sau DOCX sugerează trasabilitate completă fără bază în sursele oficiale.

### Caz 4 — no matching records

Inputuri necesare:

- folder valid cu surse lizibile;
- cod și lot care nu au înregistrări potrivite.

Comportament așteptat în UI:

- operatorul primește eroare explicită și acționabilă;
- cazul nu este tratat ca succes.

Comportament așteptat în DOCX:

- nu trebuie generat un raport care sugerează că există caz valid dacă nu există potriviri reale.

Comportament așteptat în audit_checklist_ui.json:

- dacă payload-ul nu poate fi generat, eroarea trebuie reflectată prin fluxul de diagnostic;
- dacă există fișier de eroare în diagnostic, acesta trebuie să fie util.

Diagnostic ZIP așteptat:

- inventar și preflight disponibile;
- fișier de eroare util dacă payload-ul audit nu poate fi generat.

Verdict acceptat:

- `PASS` dacă eroarea este explicită și acționabilă;
- `FAIL` dacă operatorul primește mesaj generic neclar sau un succes fals.

Ce blochează release-ul:

- eroare neacționabilă;
- lipsa dovezilor utile în Diagnostic ZIP;
- generare falsă de raport pentru caz fără potriviri.

### Caz 5 — corrupt/unreadable official source

Inputuri necesare:

- folder în care o sursă oficială există, dar este coruptă sau ilizibilă;
- restul surselor necesare sunt prezente dacă scenariul o cere;
- cod și lot pentru rulare.

Comportament așteptat în UI:

- operatorul primește mesaj de blocaj clar;
- eroarea indică faptul că sursa nu poate fi citită și cere reexport sau înlocuire.

Comportament așteptat în DOCX:

- nu trebuie generat un DOCX fals valid dacă sursa oficială blochează cazul.

Comportament așteptat în audit_checklist_ui.json:

- dacă payload-ul normal nu poate fi generat, diagnosticul trebuie să captureze eroarea într-un fișier relevant.

Diagnostic ZIP așteptat:

- `manifest.json` și fișierele disponibile trebuie să surprindă clar eroarea;
- poate apărea `audit_checklist_ui_error.json` sau alt fișier de eroare relevant.

Verdict acceptat:

- `PASS` dacă blocajul este explicit și util;
- `PASS_WITH_OBSERVATIONS` dacă există warning-uri suplimentare, dar eroarea principală rămâne clară;
- `FAIL` dacă problema cade într-un mesaj generic sau într-un rezultat ambiguu.

Ce blochează release-ul:

- lipsa clasificării clare pentru sursă coruptă sau ilizibilă;
- lipsa dovezii utile în Diagnostic ZIP.

### Caz 6 — caz local importat de utilizator: DS099903883 / lot 105.26

Inputuri necesare:

- folderul local furnizat de utilizator pentru codul `DS099903883` și lotul `105.26`;
- sursele oficiale sau fixture-urile anonimizate asociate.

Comportament așteptat în UI:

- aplicația trebuie evaluată exact pe cazul furnizat;
- rezultatul trebuie notat ca atare, fără a generaliza dintr-un alt caz.

Comportament așteptat în DOCX:

- dacă raportul se generează, trebuie verificat direct pe acest caz;
- dacă există limitări de date, ele trebuie consemnate explicit.

Comportament așteptat în audit_checklist_ui.json:

- payload-ul sau eroarea trebuie păstrate ca dovezi pentru acest caz specific.

Diagnostic ZIP așteptat:

- ZIP generat și atașat ca dovadă pentru acest caz;
- fișierele de inventar, preflight și payload/eroare trebuie păstrate pentru analiză.

Verdict acceptat:

- `PASS`, `PASS_WITH_OBSERVATIONS` sau `FAIL`, dar numai pe baza rezultatului real observat.

Ce blochează release-ul:

- cazul utilizatorului nu este testat deloc;
- rezultatul este rezumat fără dovezi concrete;
- există eroare neexplicată fără Diagnostic ZIP atașat.

## 4. Note explicite de interpretare

### Notă despre PDF-uri scanate

PDF-urile scanate pot apărea landscape, rotite sau orientate diferit din cauza scannerului sau a modului de captură.

Acest comportament nu reprezintă automat un bug TraceAI-Control și nu trebuie tratat ca defect al aplicației fără dovadă suplimentară.

### Notă despre PASS_WITH_OBSERVATIONS

`PASS_WITH_OBSERVATIONS` este acceptabil când Data Quality conține warning-uri sau issue-uri explicite, dar comportamentul general rămâne corect și auditabil.

Dacă Data Quality ajunge la nivel de eroare, problema trebuie explicată clar și trebuie atașat Diagnostic ZIP pentru investigație și suport.

## 5. Output final cerut pentru execuția validării

Execuția acestui plan trebuie să producă la final:

- un tabel de validare manuală completat pentru toate cazurile;
- numele testerului;
- semnătura sau confirmarea internă a testerului;
- data execuției;
- decizia finală pentru fiecare caz:
  - `PASS`
  - `PASS_WITH_OBSERVATIONS`
  - `FAIL`

## 6. Model de tabel pentru validare manuală

| Caz | Input verificat | UI | DOCX | audit_checklist_ui.json | Diagnostic ZIP | Verdict | Observații | Blocant release |
|---|---|---|---|---|---|---|---|---|
| FINISHED_PRODUCT complet |  |  |  |  |  |  |  |  |
| FINISHED_PRODUCT incomplet |  |  |  |  |  |  |  |  |
| WMS-only / PRD missing |  |  |  |  |  |  |  |  |
| no matching records |  |  |  |  |  |  |  |  |
| corrupt/unreadable official source |  |  |  |  |  |  |  |  |
| DS099903883 / lot 105.26 |  |  |  |  |  |  |  |  |

## 7. Semnătură și decizie finală

Tester:

Data:

Semnătură / confirmare:

Decizie finală:

- `PASS`
- `PASS_WITH_OBSERVATIONS`
- `FAIL`

## Limită importantă

Acest document este un plan de validare.

Nu reprezintă execuția validării.
Nu reprezintă un release claim.
Nu reprezintă promovarea unei etape de produs la DONE.
Nu înlocuiește validarea oficială GitHub Actions / TraceAI Diagnostics pentru etapele de produs relevante.