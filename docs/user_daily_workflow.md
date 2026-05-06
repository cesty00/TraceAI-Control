# USER-DOCS-01 — Ghid zilnic de lucru pentru operator

Acest ghid este pentru folosirea zilnică a aplicației de către un operator non-tehnic.

Scopul este simplu:

- alegi folderul cu sursele oficiale;
- introduci codul și lotul;
- verifici dacă sursele sunt prezente;
- vezi un preview rapid;
- generezi raportul DOCX;
- generezi un Diagnostic ZIP dacă apare o problemă.

Acest document este doar ghid de utilizare.

Nu schimbă aplicația.
Nu schimbă logică de business.
Nu schimbă regulile de audit.

## Înainte să începi

Pregătește un folder care conține sursele oficiale pentru cazul pe care vrei să-l verifici.

Aplicația caută în mod normal aceste surse:

- `trasabilitate_wms.csv` sau `trasabilitate_wms.zip`
- `raport_productie.csv`, `rapoarte productie.csv` sau `rapoarte_productie.csv`
- `nomenclator.xlsx`
- `stoc_la_moment_original.xlsx` sau `stoc la moment original.xlsx`

Asigură-te că ai și:

- codul produsului
- lotul produsului

Dacă sursele sunt incomplete, lipsesc sau nu pot fi citite, aplicația poate opri generarea și îți va arăta un mesaj clar.

## Fluxul zilnic recomandat

Folosește mereu aceeași ordine.

1. alege folderul surselor
2. introdu codul și lotul
3. rulează verificarea surselor
4. deschide preview-ul
5. generează raportul DOCX
6. dacă apare o problemă, generează Diagnostic ZIP

## Pasul 1 — Alegerea folderului de surse

Deschide aplicația și selectează folderul în care ai pus fișierele pentru cazul curent.

Alege folderul cazului complet, nu fișiere individuale din mai multe locuri.

Bună practică:

- folosește un singur folder pentru un singur caz
- nu amesteca fișiere de la produse sau loturi diferite
- nu redenumi sursele decât dacă folosești unul dintre aliasurile acceptate de aplicație

## Pasul 2 — Introducerea codului și a lotului

Completează:

- codul produsului
- lotul produsului

Introdu valorile exact așa cum apar în sursele oficiale.

Dacă există diferențe de scriere între ce introduci și ce există în fișiere, aplicația poate să nu găsească înregistrări pentru cazul cerut.

## Pasul 3 — Verificarea surselor

Folosește opțiunea `Verifică surse` înainte să generezi raportul.

Ce urmărești la acest pas:

- toate sursele importante sunt prezente
- fișierele se pot citi
- nu lipsește un fișier obligatoriu
- nu apare un mesaj care indică date lipsă sau format corupt

Dacă verificarea arată o problemă, oprește fluxul normal și corectează întâi sursele.

Exemple de acțiuni corecte:

- adaugi fișierul lipsă în folder
- reexportezi sursa din sistemul oficial
- înlocuiești fișierul corupt sau ilizibil
- confirmi că ai ales folderul corect

## Pasul 4 — Preview înainte de generare

Folosește opțiunea `Previzualizează audit checklist`.

Preview-ul este util pentru o verificare rapidă înainte de generarea documentului final.

La acest pas verifici mai ales:

- ai selectat cazul corect
- structura raportului pare coerentă
- secțiunile principale apar în ordinea așteptată
- nu vezi din start o eroare care oprește cazul

Preview-ul nu înlocuiește raportul final DOCX, dar te ajută să prinzi repede un folder greșit, un cod greșit sau un lot greșit.

## Pasul 5 — Generarea raportului DOCX

Dacă verificarea surselor și preview-ul arată bine, folosește `Generează raport DOCX`.

Rezultatul așteptat este un raport audit checklist în format DOCX.

După generare, verifică imediat:

- fișierul a fost creat în locul ales
- documentul se deschide normal
- numele produsului, codul și lotul corespund cazului tău
- raportul este cel al cazului curent, nu al unui caz mai vechi

Dacă documentul s-a generat, dar conținutul nu corespunde cazului, nu îl trimite mai departe. Revino la folderul sursă, cod și lot și repetă pașii.

## Pasul 6 — Generarea Diagnostic ZIP

Folosește `Generează Diagnostic ZIP` în oricare dintre situațiile de mai jos:

- aplicația afișează o eroare
- raportul nu se generează
- preview-ul nu arată cazul așteptat
- vrei să trimiți cazul la suport pentru investigație

Diagnostic ZIP este pentru analiză și suport.

Nu înlocuiește raportul DOCX final.
Nu înlocuiește validarea oficială GitHub folosită pentru închiderea etapelor de proiect.

Păstrează ZIP-ul asociat aceluiași caz pentru care ai rulat aplicația.

## Ce faci când apare o eroare

Dacă apare o eroare, lucrează în ordinea de mai jos.

1. citește mesajul complet primit în aplicație
2. verifică dacă problema este despre folder greșit, fișier lipsă sau fișier corupt
3. corectează sursele și rulează din nou `Verifică surse`
4. dacă problema rămâne, generează `Diagnostic ZIP`
5. trimite mai departe codul, lotul și Diagnostic ZIP către persoana sau echipa care oferă suport

Nu încerca să modifici manual conținutul fișierelor oficiale doar pentru a forța generarea raportului.

## Checklist scurt pentru lucru zilnic

Înainte de finalizare, confirmă rapid:

- folderul selectat este cel corect
- codul este corect
- lotul este corect
- `Verifică surse` nu indică o problemă blocantă
- preview-ul corespunde cazului
- raportul DOCX s-a generat corect
- dacă a existat o eroare, Diagnostic ZIP a fost salvat

## Când te oprești și ceri ajutor

Oprește fluxul și cere ajutor dacă:

- lipsește o sursă oficială și nu o poți reexporta
- fișierul există, dar aplicația spune că nu poate fi citit
- nu există înregistrări pentru codul și lotul cerut, deși te aștepți să existe
- raportul generat nu corespunde cazului verificat
- aceeași eroare apare din nou după ce ai refăcut verificarea surselor

## Limită importantă

Acest ghid descrie fluxul zilnic de operare.

Nu schimbă regulile oficiale ale proiectului și nu mută logică în UI.
DOCX și UI rămân derivate din aceeași sursă de adevăr audit.