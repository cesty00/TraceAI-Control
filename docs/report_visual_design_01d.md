# REPORT-QUALITY-01D — Full DOCX visual design specification

Data: 2026-05-04

## Decizie produs

Raportul DOCX exportat din aplicație trebuie să arate și să se comporte ca un dosar de audit tipărit, nu ca un export brut de date.

Designul urmărește lizibilitate, scanare rapidă, imprimare alb-negru și utilizare practică în audit.

## Referință vizuală

Referința vizuală este raportul scanat furnizat pentru vizualizare:

```text
SKM_36726050412330.pdf
```

Observații din referință:

```text
- raport landscape;
- secțiuni numerotate;
- tabele compacte;
- header de tabel evidențiat;
- registru documente fizice cu checkbox;
- concluzie și build info la final;
- conținut orientat către audit și imprimare.
```

## Principiu de design

```text
Raportul principal trebuie să răspundă rapid la întrebările auditorului:
1. Ce produs și lot se verifică?
2. Care este verdictul?
3. Care este bilanțul?
4. Ce s-a livrat în aval?
5. Ce a intrat în amonte?
6. Ce documente trebuie pregătite fizic?
7. Cu ce versiune a aplicației a fost generat raportul?
```

## Reguli care nu se schimbă

```text
- Nu se schimbă TraceabilityCase.
- Nu se schimbă regulile de clasificare amonte/aval.
- Nu se schimbă bilanțurile sau cantitățile.
- Nu se convertesc unități de măsură.
- DOCX și UI rămân bazate pe aceeași sursă audit.
- JSON-ul UI rămâne compatibil.
- Valorile lipsă rămân explicite: FARA DATE IDENTIFICATE.
```

## Layout țintă

### Prima pagină

```text
TEST DE TRASABILITATE PENTRU AUDIT
Cod / lot / denumire produs
Rezultat audit
Data generării
Build commit
Ghid rapid pentru auditor
Verdict scurt / card de conformare
```

### Secțiuni principale

```text
00. Exercițiu și bilanț
01. Rezumat conformare checklist
02. Amonte — materii prime, ambalaje, auxiliare
03. Aval — livrări produs finit
04. Producție și consum
05. Flux loturi și documente
06. Registru documente fizice
07. Concluzie audit
08. Build info
```

### Tabele

```text
- landscape păstrat;
- tabele 100% lățime pagină;
- header repetabil pe pagini;
- rânduri care nu se rup între pagini;
- conținut aliniat sus în celule;
- margini mici în celule;
- header gri deschis;
- font compact;
- informațiile lungi comprimate în observații standardizate.
```

### Registru documente

```text
- coloană Bifat cu simbolul ☐;
- required înainte de recommended;
- documentele fizice ușor de pregătit;
- tabel utilizabil direct tipărit.
```

### Header/footer

```text
Header:
TraceAI Control — Test de trasabilitate | cod | lot

Footer:
Build commit / canal build / generat la / pagină
```

## Implementare în pași mici

### REPORT-QUALITY-01D-1 — Apply layout helpers to all audit checklist tables

```text
- tabel 100% width;
- tblLook firstRow;
- tblHeader pentru header;
- cantSplit pentru rânduri normale;
- vAlign top pentru celule;
- teste pe WordprocessingML.
```

### REPORT-QUALITY-01D-2 — Compact table typography

```text
- font compact pentru tabele mari;
- margini celule reduse;
- spațiere verticală redusă;
- fără modificare date.
```

### REPORT-QUALITY-01D-3 — Auditor verdict card

```text
- card scurt pe prima pagină;
- rezultat, bilanț, aval, amonte, documente;
- fără modificarea calculului verdictului.
```

### REPORT-QUALITY-01D-4 — Better header/footer metadata

```text
- cod și lot în header;
- build commit în footer;
- păstrează landscape.
```

### REPORT-QUALITY-01D-5 — Final visual validation on Windows artifact

```text
- build Windows;
- generare raport real;
- verificare manuală vizuală;
- Diagnostic ZIP verde.
```

## Criterii de acceptare

```text
[ ] pytest PASS
[ ] TraceAI Diagnostics PASS
[ ] reference_comparison.md PASS
[ ] real_audit_checklist_ui.json valid
[ ] DOCX se deschide în Word / LibreOffice
[ ] raportul este lizibil în landscape
[ ] registrul documentelor este utilizabil ca checklist tipărit
[ ] build info rămâne prezent
```

## Stare

```text
REPORT-QUALITY-01D_SPEC_DEFINED
Next: REPORT-QUALITY-01D-1 — apply layout helpers to all audit checklist tables
```
