# ARTIFACT-RETENTION-01 — Politică de păstrare și referențiere a artifactelor reale

## Scope

Acest document definește o politică docs-only pentru păstrarea și referențierea artifactelor reale produse în validări și pilot.

Scopul lui este să stabilească unde păstrăm artifactele reale și cum le referențiem fără a le include direct în repo.

Acest document nu schimbă aplicația.
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

Acest document nu reprezintă release claim.
Nu reprezintă product-stage DONE claim.

## 1. Scopul politicii

Politica definește:

- unde se păstrează artifactele reale produse în validări și pilot;
- cum sunt referențiate în documentație și evidențe interne;
- ce nu trebuie inclus direct în GitHub sau în repo;
- ce informații minime trebuie păstrate pentru trasabilitate.

## 2. Artifacte acoperite

Această politică acoperă cel puțin următoarele tipuri de artifacte:

- rapoarte DOCX generate;
- Diagnostic ZIP;
- `audit_checklist_ui.json`;
- `preflight.json`;
- `source_inventory.json`;
- `build_info.json`;
- PDF-uri scanate sau alte documente fizice;
- screenshot-uri UI, dacă sunt folosite ca dovezi;
- fișiere de măsurare a performanței UI, când vor exista.

## 3. Reguli generale

Regulile obligatorii sunt:

- nu se includ artifacte reale sensibile direct în repo;
- nu se includ ZIP-uri mari direct în repo;
- nu se includ fișiere cu date operaționale sensibile fără aprobare explicită;
- repo-ul păstrează doar documentație, politici, proceduri și referințe controlate;
- artifactele reale se păstrează într-un spațiu intern aprobat.

Acest spațiu intern poate fi un storage aprobat, un path intern controlat sau alt sistem intern acceptat de organizație.

## 4. Model minim de referențiere

Pentru fiecare artifact real păstrat în afara repo-ului trebuie consemnate cel puțin următoarele:

- nume artifact;
- data rulării;
- cod produs;
- lot;
- tester;
- commit sau build folosit;
- locație internă, path intern sau storage reference;
- checksum sau hash, dacă este disponibil;
- observații de sensibilitate.

## 5. Tabel model pentru inventarierea artifactelor

| Nume artifact | Data rulării | Cod produs | Lot | Tester | Commit / build | Locație internă / storage reference | Checksum / hash | Sensibilitate | Observații |
|---|---|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |  |  |

## 6. Caz local cunoscut — exemplu de referință

Pentru cazul local deja consemnat, artifactele cunoscute sunt:

- `TEST2000.docx`
- `TraceAI-Diagnostic-cod-lot-20260506T070322Z.zip`
- `SKM_36726050609130.pdf`
- `audit_checklist_ui.json`
- cod produs: `DS099903883`
- lot: `105.26`
- verdict: `PASS_WITH_OBSERVATIONS`
- `Data Quality: ERROR`

Aceste artifacte nu trebuie mutate automat în repo.

Ele trebuie doar referențiate controlat prin modelul de inventariere, într-un spațiu intern aprobat.

## 7. Reguli de securitate și sensibilitate

Artifactele reale pot conține date sensibile sau operaționale.

În special:

- Diagnostic ZIP poate conține date sensibile;
- PDF-urile scanate pot conține documente fizice operaționale;
- JSON-urile pot conține căi locale, coduri, loturi, warning-uri și informații de audit;
- screenshot-urile UI pot arăta date operaționale sau rezultate intermediare.

Distribuirea acestor artifacte se face doar prin canal intern aprobat.

## 8. Cine poate accesa

Accesul la artifactele reale trebuie limitat la rolurile interne care au nevoie legitimă de ele, de exemplu:

- testerul sau operatorul care a executat cazul;
- reviewer-ul intern desemnat;
- suportul tehnic intern;
- persoanele responsabile cu auditul intern sau cu validarea controlată.

Dacă organizația are reguli suplimentare de acces, ele au prioritate peste acest document.

## 9. Ce nu se pune în GitHub

Nu se pun în GitHub:

- artifacte reale sensibile;
- ZIP-uri de diagnostic reale;
- PDF-uri scanate reale;
- JSON-uri reale cu date operaționale;
- screenshot-uri reale sensibile;
- fișiere mari de evidență provenite din rulări reale;
- copii brute ale documentelor fizice sau ale surselor operaționale.

În GitHub se păstrează doar:

- politici;
- proceduri;
- planuri;
- execution records redactate controlat;
- referințe controlate către artifactele păstrate intern.

## 10. Reguli de păstrare

Pentru fiecare artifact real trebuie decis și consemnat:

- unde este păstrat;
- cine răspunde de păstrare;
- cât timp trebuie păstrat;
- dacă există cerință de checksum sau hash;
- dacă artifactul poate fi redistribuit intern sau doar consultat.

Dacă aceste reguli sunt stabilite separat de organizație, documentul de față trebuie folosit ca punct minim de control, nu ca înlocuitor al politicilor interne.

## 11. Limită explicită

Acest document nu validează artifactele.
Nu declară release readiness.
Nu declară `daily-use internal release`.
Nu marchează nicio etapă de produs ca `DONE`.

El definește doar politica de păstrare și referențiere a artifactelor reale.