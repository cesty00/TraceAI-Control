# REPORT-QUALITY-01E — Audit content and table description specification

Data: 2026-05-04

## Scope

Această etapă definește conținutul recomandat pentru îmbunătățirea calității textului din raportul audit checklist DOCX, fără schimbări în logica de business.

Nu schimbă:

```text
TraceabilityCase
AuditTraceabilityReport
AuditChecklistReport
regulile de calcul
clasificarea amonte / aval
cantitățile
verdictul
JSON-ul UI
sursele de intrare
```

PP-03 rămâne în afara scope-ului.

## Objective

Raportul DOCX trebuie să explice mai clar:

```text
ce verifică auditorul
ce sursă alimentează fiecare secțiune
ce trebuie confirmat manual sau pregătit fizic
```

## Safety decision

Implementarea în rendererul mare `src/report/audit_checklist_docx.py` se face doar incremental, în pași mici, pe deasupra versiunii curente din `main`, cu test dedicat pentru fiecare bloc de text introdus.

Această etapă este de tip specificație de conținut, nu schimbare de renderer.

## Source roles

### WMS trasabilitate

Rol:

```text
mișcări produs finit
livrări aval
documente WMS
recepții pentru loturi sursă
legături între cod, lot, document și comandă
```

Text recomandat:

```text
WMS este sursa principală pentru mișcările de gestiune, livrările către clienți și documentele operaționale identificate pentru produsul și lotul auditat.
```

### Raport producție PRD

Rol:

```text
comenzi de producție
cantitate produsă
consumuri materii prime
consumuri ambalaje
consumuri auxiliare / gaz
legătura dintre lotul finit și loturile sursă
```

Text recomandat:

```text
PRD este sursa suport pentru producție și consumuri. Datele PRD explică din ce loturi și materiale s-a obținut lotul de produs finit analizat.
```

### Nomenclator

Rol:

```text
denumiri articole și materiale
clarificare coduri scurte
suport de lizibilitate pentru audit
```

Text recomandat:

```text
Nomenclatorul completează denumirile produselor și materialelor, pentru ca raportul să fie ușor de citit în audit.
```

### Stoc la moment

Rol:

```text
confirmă existența sau absența loturilor în stoc la momentul verificării
susține bilanțul produsului finit
susține verificarea loturilor sursă
```

Text recomandat:

```text
Stocul la moment este folosit ca informație de verificare. Absența unui lot din fișierul de stoc nu modifică automat istoricul trasabilității, dar devine punct de atenție pentru auditor.
```

## Recommended text blocks by section

### Card verdict auditor

Scop:

```text
citire rapidă a cazului: verdict, produs, lot, bilanț, aval, amonte și documente fizice
```

Text recomandat:

```text
Cardul verdict sintetizează cazul de audit și indică zonele principale care trebuie citite înaintea verificării documentelor fizice.
```

### Ghid rapid pentru auditor

Text recomandat:

```text
Ghidul rapid indică ordinea recomandată de citire: verdict, bilanț, aval, amonte, consumuri și registrul documentelor fizice.
```

### Rezumat conformare checklist

Text recomandat:

```text
Rezumatul de conformare arată dacă raportul conține informațiile necesare pentru verificarea trasabilității. Observațiile explică limitele datelor sau verificările care trebuie completate manual.
```

### 01_EXERCITIU — Fișa principală

Text recomandat:

```text
Fișa principală identifică produsul și lotul auditat. Bilanțul compară cantitatea produsă în PRD cu mișcările WMS și stocul disponibil, fără conversii automate de unități.
```

### 02_TABEL_I_AMONTE

Text recomandat:

```text
Tabelul amonte prezintă materialele și loturile care au contribuit la produsul finit: materii prime, ambalaje și materiale auxiliare. Auditorul verifică documentele de recepție, furnizorul, consumul și eventualele observații.
```

### 03_TABEL_II_AVAL

Text recomandat:

```text
Tabelul aval prezintă livrările identificate pentru lotul auditat. Auditorul trebuie să compare aceste rânduri cu documentele fizice de livrare și cu documentele WMS indicate.
```

### 04_PRODUCTIE_CONSUM

Text recomandat:

```text
Această secțiune arată comenzile de producție și consumurile aferente fiecărei comenzi. Ea demonstrează legătura dintre lotul finit și loturile sursă consumate.
```

### 05_FLUX_LOTURI_SI_DOCUMENTE

Text recomandat:

```text
Fluxurile de loturi reunesc informațiile esențiale despre recepții, consumul în lotul auditat, eventualele livrări către terți și stocul rămas.
```

### Registru documente fizice

Text recomandat:

```text
Registrul indică documentele care trebuie pregătite pentru dosarul de audit. Coloana Bifat permite folosirea tabelului ca listă de verificare tipărită.
```

### Concluzie audit intern

Text recomandat:

```text
Concluzia sintetizează rezultatul verificării pe baza datelor WMS și PRD disponibile. Ea nu înlocuiește verificarea documentelor fizice, ci indică ce a fost identificat și ce trebuie atașat dosarului de audit.
```

## Future exception zone rules

O zonă vizuală de excepții rămâne utilă, dar trebuie construită numai din date deja existente în `AuditChecklistReport`.

Reguli:

```text
nu schimbă verdictul
nu schimbă calculele
nu introduce reguli noi de business
nu schimbă sursele
afișează explicit dacă nu există excepții majore
limitează punctele de atenție afișate pe prima pagină
```

Categorii permise:

```text
bilanț PRD vs WMS
conformare checklist diferită de DA
observații amonte diferite de OK / Nu se aplică
documente fizice care trebuie pregătite
absențe explicite FARA DATE IDENTIFICATE
```

## Acceptance criteria for this spec stage

```text
[x] Nu se schimbă logica de business
[x] Nu se schimbă DTO-uri sau calcule
[x] Se documentează texte recomandate pentru secțiuni și tabele
[x] Se păstrează rendererul curent drept ultim comportament validat
[ ] Implementarea se face ulterior în pași mici, cu test dedicat
```

## Status

```text
REPORT-QUALITY-01E_SPEC_DEFINED
Next safe implementation: REPORT-QUALITY-01E-1, one approved text block at a time, on top of current main.
```
