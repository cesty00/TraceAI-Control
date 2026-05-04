# REPORT-QUALITY-01E — Audit content and table description specification

Data: 2026-05-04

## Decizie de siguranță

Nu se modifică rendererul principal `src/report/audit_checklist_docx.py` în această etapă dacă fișierul nu poate fi editat într-un mod complet și sigur.

Motiv: rendererul DOCX este mare și critic. O suprascriere parțială ar putea strica raportul validat până la `REPORT-QUALITY-01D-4_DONE`.

Această etapă mută focusul pe conținutul auditului: descrieri clare, semnificația tabelelor, sursa datelor și textul care ajută auditorul să înțeleagă rapid raportul.

PP-03 este în afara scope-ului.

## Obiectiv

Raportul exportat trebuie să explice mai clar datele extrase din fișierele sursă și rolul fiecărui tabel, fără să modifice:

```text
- TraceabilityCase;
- AuditTraceabilityReport;
- AuditChecklistReport;
- regulile de calcul;
- clasificarea amonte/aval;
- cantitățile;
- verdictul;
- JSON-ul UI;
- layout-ul validat până la 01D-4.
```

## Principiu

Fiecare tabel din raport trebuie să răspundă la trei întrebări:

```text
1. Ce verifică auditorul aici?
2. Din ce sursă provin datele?
3. Ce trebuie pregătit fizic sau confirmat manual?
```

## Surse și rolul lor în raport

### WMS trasabilitate

Rol:

```text
- mișcări produs finit;
- livrări aval;
- documente WMS;
- recepții pentru loturi sursă;
- stoc la moment dacă este disponibil în datele sursă;
- legături între cod, lot, document și comandă.
```

Text recomandat în raport:

```text
WMS este sursa principală pentru mișcările de gestiune, livrările către clienți și documentele operaționale identificate pentru produsul și lotul auditat.
```

### Raport producție PRD

Rol:

```text
- comenzi de producție;
- cantitate produsă;
- consumuri materii prime;
- consumuri ambalaje;
- consumuri auxiliare / gaz;
- legătura dintre lotul finit și loturile sursă.
```

Text recomandat în raport:

```text
PRD este sursa suport pentru producție și consumuri. Datele PRD explică din ce loturi și materiale s-a obținut lotul de produs finit analizat.
```

### Nomenclator

Rol:

```text
- denumiri articole;
- completare descrieri produs/material;
- clarificare coduri atunci când datele operaționale conțin coduri scurte.
```

Text recomandat în raport:

```text
Nomenclatorul completează denumirile produselor și materialelor, pentru ca raportul să fie ușor de citit în audit.
```

### Stoc la moment

Rol:

```text
- confirmă existența sau absența loturilor în stoc la momentul verificării;
- susține bilanțul produsului finit;
- susține verificarea loturilor sursă.
```

Text recomandat în raport:

```text
Stocul la moment este folosit ca informație de verificare. Absența unui lot din fișierul de stoc nu modifică automat istoricul trasabilității, dar devine punct de atenție pentru auditor.
```

## Texte recomandate pentru secțiuni

### Card verdict auditor

Scop:

```text
Oferă o citire rapidă a cazului: verdict, produs, lot, bilanț, aval, amonte și documente fizice.
```

Text recomandat:

```text
Cardul verdict sintetizează cazul de audit și indică zonele principale care trebuie citite înaintea verificării documentelor fizice.
```

### Ghid rapid pentru auditor

Scop:

```text
Stabilește ordinea practică de verificare a raportului.
```

Text recomandat:

```text
Ghidul rapid indică ordinea recomandată de citire: verdict, bilanț, aval, amonte, consumuri și registrul documentelor fizice.
```

### Rezumat conformare checklist

Scop:

```text
Arată dacă cerințele minime de audit sunt acoperite de datele identificate.
```

Text recomandat:

```text
Rezumatul de conformare arată dacă raportul conține informațiile necesare pentru verificarea trasabilității. Observațiile explică limitele datelor sau verificările care trebuie completate manual.
```

### 01_EXERCITIU — Fișa principală

Scop:

```text
Fixează produsul, lotul și bilanțul dintre PRD și WMS.
```

Text recomandat:

```text
Fișa principală identifică produsul și lotul auditat. Bilanțul compară cantitatea produsă în PRD cu mișcările WMS și stocul disponibil, fără conversii automate de unități.
```

### 03_TABEL_II_AVAL — Livrări produs finit

Scop:

```text
Arată traseul lotului finit către clienți.
```

Text recomandat:

```text
Tabelul aval prezintă livrările identificate pentru lotul auditat. Auditorul trebuie să compare aceste rânduri cu documentele fizice de livrare și cu documentele WMS indicate.
```

### 02_TABEL_I_AMONTE — Materii prime, ambalaje și auxiliare

Scop:

```text
Arată loturile sursă care au intrat în produsul finit.
```

Text recomandat:

```text
Tabelul amonte prezintă materialele și loturile care au contribuit la produsul finit: materii prime, ambalaje și materiale auxiliare. Auditorul verifică documentele de recepție, furnizorul, consumul și eventualele observații.
```

### Verificare specială — materii prime livrate către terți

Scop:

```text
Separă consumul intern de eventuale livrări directe din același lot sursă.
```

Text recomandat:

```text
Această verificare evidențiază dacă loturile de materie primă folosite în produsul auditat au avut și livrări directe către terți. Informația ajută la separarea consumului intern de alte ieșiri ale aceluiași lot.
```

### 04_PRODUCTIE_CONSUM — Detaliere pe comenzi de producție

Scop:

```text
Leagă comenzile de producție de cantitatea produsă și consumurile aferente.
```

Text recomandat:

```text
Această secțiune arată comenzile de producție și consumurile aferente fiecărei comenzi. Ea demonstrează legătura dintre lotul finit și loturile sursă consumate.
```

### 05_FLUX_LOTURI_SI_DOCUMENTE — Fluxuri loturi și documente

Scop:

```text
Oferă o privire de ansamblu asupra recepțiilor, consumului, livrărilor terți și stocului.
```

Text recomandat:

```text
Fluxurile de loturi reunesc informațiile esențiale despre recepții, consumul în lotul auditat, eventualele livrări către terți și stocul rămas.
```

### Registru documente fizice

Scop:

```text
Transformă raportul într-o listă de verificare imprimabilă.
```

Text recomandat:

```text
Registrul indică documentele care trebuie pregătite pentru dosarul de audit. Coloana Bifat permite folosirea tabelului ca listă de verificare tipărită.
```

### Concluzie audit intern

Scop:

```text
Rezumat final al trasabilității și al documentelor necesare.
```

Text recomandat:

```text
Concluzia sintetizează rezultatul verificării pe baza datelor WMS și PRD disponibile. Ea nu înlocuiește verificarea documentelor fizice, ci indică ce a fost identificat și ce trebuie atașat dosarului de audit.
```

## Zonă de excepții — variantă sigură pentru viitor

Implementarea vizuală a unei zone de excepții rămâne recomandată, dar trebuie făcută numai cu editare sigură a rendererului.

Reguli pentru acea zonă:

```text
- folosește doar date deja existente în AuditChecklistReport;
- nu schimbă verdictul;
- nu schimbă calculele;
- nu schimbă sursele;
- nu introduce reguli noi de business;
- afișează explicit dacă nu sunt excepții majore;
- afișează maximum 8 puncte de atenție ca să nu încarce prima pagină.
```

Categoriile permise:

```text
- bilanț PRD vs WMS;
- conformare checklist diferită de DA;
- observații amonte diferite de OK / Nu se aplică;
- documente fizice care trebuie pregătite;
- absențe explicite FARA DATE IDENTIFICATE.
```

## Criterii de acceptare pentru această etapă

```text
[x] Nu se modifică rendererul principal fără editare sigură.
[x] Nu se modifică logica de extragere.
[x] Nu se modifică DTO-uri sau calcule.
[x] Se documentează textele recomandate pentru tabele.
[x] Se păstrează REPORT-QUALITY-01D-4 ca ultimă implementare validată.
[ ] Textele se implementează ulterior în pași mici, cu test dedicat.
```

## Stare

```text
REPORT-QUALITY-01E_SPEC_DEFINED
Next safe implementation: apply one text block at a time in audit_checklist_docx.py with focused tests.
```
