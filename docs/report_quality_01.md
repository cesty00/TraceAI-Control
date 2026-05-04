# REPORT-QUALITY-01 — Audit DOCX quality specification

Data: 2026-05-04

## Scop

Îmbunătățirea calității raportului DOCX fără schimbarea engine-ului, regulilor de trasabilitate sau datelor calculate.

Această etapă este strict despre prezentare, lizibilitate și utilitate pentru auditor.

## Reguli obligatorii

```text
1. Nu se schimbă TraceabilityCase.
2. Nu se schimbă regulile de clasificare amonte/aval.
3. Nu se schimbă bilanțurile sau cantitățile.
4. Nu se convertesc unități de măsură.
5. DOCX și UI rămân bazate pe aceeași sursă audit.
6. Dacă o informație lipsește, rămâne explicit FARA DATE IDENTIFICATE.
7. Build info rămâne prezent în raport.
8. Testele și comparatorul DS099903883 / 105.26 trebuie să rămână PASS.
```

## Probleme observate în raportul validat Windows

Raportul generat este corect funcțional și complet, dar poate fi îmbunătățit pentru audit:

```text
- auditorul are nevoie de un ghid scurt de citire imediat după titlu;
- tabelele lungi trebuie să fie ușor de urmărit;
- secțiunile critice trebuie să aibă o ordine și o descriere clară;
- observațiile trebuie să fie concise și orientate spre acțiune;
- registrul documentelor trebuie să fie ușor de folosit ca checklist fizic.
```

## Criterii de acceptare

Raportul DOCX trebuie să conțină:

```text
[ ] Titlu audit clar
[ ] Cod produs, lot și denumire produs în prima pagină
[ ] Ghid rapid pentru auditor
[ ] Rezumat de conformare checklist
[ ] Fișă exercițiu și bilanț produs finit
[ ] Tabel aval / livrări produs finit
[ ] Tabel amonte / materii prime, ambalaje, auxiliare/gaz
[ ] Verificare specială pentru materii prime livrate către terți
[ ] Detaliere producție/consum pe comenzi
[ ] Fluxuri loturi și documente
[ ] Registru documente fizice de pregătit pentru auditor
[ ] Concluzie audit intern
[ ] Informații build raport
```

## Ghid rapid pentru auditor — conținut propus

Se adaugă după titlu, înainte de rezumatul de conformare:

```text
Ghid rapid pentru auditor
- Verifică întâi Rezumatul de conformare checklist.
- Confirmă bilanțul PRD vs WMS în 01_EXERCITIU.
- Verifică avalul în 03_TABEL_II_AVAL și documentele de livrare.
- Verifică amontele în 02_TABEL_I_AMONTE și documentele de recepție.
- Folosește registrul documentelor pentru pregătirea dosarului fizic.
```

## Pași de implementare recomandați

### REPORT-QUALITY-01A — Ghid rapid pentru auditor

```text
- Adaugă secțiune scurtă după titlu.
- Test: XML-ul DOCX conține titlul secțiunii și cele 5 puncte.
- Nu se modifică datele raportului.
```

### REPORT-QUALITY-01B — Îmbunătățire registru documente

```text
- Păstrează coloanele existente.
- Asigură motiv scurt și status clar.
- Test: registrul conține documentele required și recommended.
```

### REPORT-QUALITY-01C — Finisare texte introductive

```text
- Texte scurte, orientate pe audit.
- Fără explicații tehnice inutile.
- Test: secțiunile critice rămân prezente.
```

## Validare obligatorie după fiecare subetapă

```text
python -m pytest -q
TraceAI Diagnostics pe main
reference_comparison.md = PASS
real_audit_checklist_ui.json = valid
```

## Stare curentă

```text
REPORT-QUALITY-01_SPEC_DEFINED
Next: REPORT-QUALITY-01A — add quick auditor guide to DOCX
```
