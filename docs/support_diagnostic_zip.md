# SUPPORT-DIAGNOSTIC-01 — Ghid pentru Diagnostic ZIP

Acest document explică pe scurt ce este Diagnostic ZIP, ce conține, ce poți trimite la suport și ce poate conține date sensibile.

Este un ghid pentru operator și pentru echipa care colectează informațiile de suport.

Acest document este doar ghid de utilizare.

Nu schimbă aplicația.
Nu schimbă logică de business.
Nu schimbă regulile de audit.

## Ce este Diagnostic ZIP

Diagnostic ZIP este un pachet local de investigație.

Scopul lui este să ajute suportul să înțeleagă ce a văzut aplicația în momentul rulării pentru un anumit folder, cod și lot.

Diagnostic ZIP este util mai ales când:

- aplicația afișează o eroare
- raportul DOCX nu se generează
- preview-ul nu arată cazul așteptat
- vrei să trimiți cazul la suport pentru analiză

Diagnostic ZIP nu înlocuiește raportul DOCX final.
Diagnostic ZIP nu înlocuiește validarea oficială GitHub folosită pentru închiderea etapelor de proiect.

## Ce conține în mod normal

Diagnostic ZIP este best-effort.

Asta înseamnă că încearcă să salveze cât mai multe informații utile chiar dacă o parte din flux a eșuat.

În mod normal, ZIP-ul poate conține:

- `build_info.json`
- `source_inventory.json`
- `preflight.json`
- `audit_checklist_ui.json`
- `manifest.json`
- `README.txt`
- opțional `reports/<nume raport>.docx`

Dacă o etapă nu poate fi generată, în locul fișierului normal poate apărea un fișier de eroare, de exemplu:

- `build_info_error.json`
- `source_inventory_error.json`
- `preflight_error.json`
- `audit_checklist_ui_error.json`
- `generated_report_copy_error.json`

## Ce înseamnă pe scurt fiecare fișier

### build_info.json

Conține informații despre build-ul aplicației.

Este util pentru suport când trebuie verificat ce versiune sau ce build a fost folosit.

### source_inventory.json

Descrie ce surse au fost găsite în folderul selectat.

Este util pentru suport ca să vadă dacă aplicația a observat fișierele așteptate.

### preflight.json

Conține rezultatul verificării preliminare pentru folder, cod și lot.

Aici pot apărea avertismente sau blocaje care explică de ce cazul nu poate merge mai departe normal.

### audit_checklist_ui.json

Conține payload-ul UI pentru checklist-ul de audit.

Este util pentru suport când trebuie analizat ce a reușit aplicația să pregătească pentru preview și pentru fluxul de raportare.

### manifest.json

Este lista internă a conținutului ZIP-ului.

Include și informații de context despre rulare, cum ar fi:

- folderul sursă folosit
- codul introdus
- lotul introdus
- lista fișierelor incluse
- warnings
- errors

### README.txt

Este un rezumat text simplu al pachetului de diagnostic.

Este util când cineva deschide ZIP-ul și vrea să vadă rapid ce fișiere există și ce probleme au fost detectate.

### reports/<nume raport>.docx

Poate exista dacă la rulare a fost disponibil și un raport DOCX generat care a fost copiat în pachet.

Acest fișier este opțional.

## Ce poți trimite la suport

Dacă suportul cere analiza cazului, poți trimite:

- întregul Diagnostic ZIP
- codul produsului
- lotul produsului
- o scurtă descriere a problemei observate
- momentul aproximativ când ai rulat aplicația

Cea mai simplă variantă este să trimiți ZIP-ul complet, fără să scoți manual fișiere din el.

Așa eviți să lipsească exact fișierul util pentru investigație.

## Ce poate conține date sensibile

Diagnostic ZIP poate conține informații operaționale sau sensibile.

În special, fii atent la:

- calea completă a folderului sursă din `manifest.json`
- codul și lotul folosite la rulare
- denumiri de fișiere și structură de surse observate de aplicație
- warnings și errors care pot cita nume de fișiere, foi sau probleme interne
- conținutul din `audit_checklist_ui.json`
- raportul DOCX copiat în `reports/` dacă există

În funcție de caz, aceste fișiere pot reflecta informații despre:

- produse
- loturi
- documente de lucru
- structura locală de directoare
- rezultate intermediare ale auditului

## Când nu trimiți ZIP-ul mai departe fără aprobare

Nu trimite Diagnostic ZIP în afara canalului intern aprobat dacă:

- nu știi cine are dreptul să vadă datele din caz
- ZIP-ul conține raport DOCX sau payload de audit pentru un caz sensibil
- politicile interne cer filtrare sau aprobare înainte de trimitere

Dacă ai dubii, cere confirmare internă înainte de a trimite pachetul.

## Ce faci înainte de trimitere

Înainte să trimiți ZIP-ul la suport, verifică rapid:

- ai generat ZIP-ul pentru cazul corect
- codul și lotul corespund problemei raportate
- descrierea scurtă a erorii este clară
- trimiți pachetul doar către canalul intern potrivit

## Ce nu trebuie făcut

- nu modifica manual fișierele din ZIP
- nu redenumi fișierele din interiorul ZIP-ului
- nu scoate selectiv fișiere dacă suportul nu a cerut asta explicit
- nu presupune că ZIP-ul este sigur pentru distribuție largă

## Limită importantă

Diagnostic ZIP este un instrument de suport și investigație locală.

Nu este dovadă oficială pentru promovarea unei etape la DONE.
Nu înlocuiește artifactele oficiale GitHub Actions / TraceAI Diagnostics.
Nu schimbă sursa unică de adevăr dintre audit, UI și DOCX.