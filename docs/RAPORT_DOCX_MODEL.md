# Model raport DOCX — TraceAI Control Modul Trasabilitate

Raportul DOCX este livrabilul principal al aplicației.

Stilul urmărit este un proces-verbal auditabil: narativ, clar, cu tabele scurte, concluzie și semnături.

## Principii

Raportul trebuie să spună:

```text
ce s-a verificat
ce surse au fost folosite
ce s-a găsit
ce nu s-a găsit
ce înseamnă operațional
ce trebuie verificat manual, dacă este cazul
```

Raportul nu trebuie să fie:

```text
un Excel copiat în Word
un dump de date brute
un tabel imens greu de citit
```

## Antet raport

```text
RAPORT DE TRASABILITATE
Articol verificat: [cod]
Lot verificat: [lot]
Produs: [denumire]
Data generării: [data]
Caracter document: Preliminar / uz intern / audit
Surse utilizate: WMS, PRD, nomenclator, stoc la moment
```

## Structură FINISHED_PRODUCT

```text
1. Obiectul verificării
2. Situația centralizată a lotului
3. Situația numerică utilizată în verificare
4. Producția lotului
5. AVAL produs finit
6. AMONTE — materii prime alimentare
7. AMONTE — ambalaje
8. AMONTE — materiale auxiliare / gaz
9. AVAL MP — mișcări ale loturilor de materie primă folosite
10. Observații tehnice
11. Stoc la moment
12. Concluzie preliminară
13. Recomandare operațională
14. Documente de pregătit pentru audit
15. Semnături
```

## Structură RAW_MATERIAL

```text
1. Obiectul verificării
2. Recepția lotului
3. Situația numerică a lotului
4. Mișcări WMS relevante
5. Consumuri în producție
6. Produse finite rezultate
7. Livrări directe către terți
8. Stoc la moment
9. Observații tehnice
10. Concluzie preliminară
11. Recomandare operațională
12. Documente de pregătit pentru audit
13. Semnături
```

## Structură WMS_ONLY_PRODUCT

```text
1. Obiectul verificării
2. Recepția lotului
3. Livrarea lotului
4. Bilanț recepționat-livrat-stoc
5. Observație privind lipsa fluxului PRD
6. Stoc la moment
7. Concluzie preliminară
8. Recomandare operațională
9. Documente de pregătit pentru audit
10. Semnături
```

## Reguli de text

Raportul trebuie să conțină concluzii formulate natural.

Exemplu pentru produs finit:

```text
Pentru articolul [cod], lot [lot], trasabilitatea tehnică este coerentă. Lotul a fost produs în cantitate totală de [cantitate] prin comenzile [comenzi] și a fost livrat integral prin documentele WMS [documente].
```

Exemplu pentru materie primă:

```text
Pentru articolul [cod], lot [lot], trasabilitatea tehnică este coerentă. Lotul a fost recepționat în WMS prin documentul de intrare [document] și a fost consumat în producție în cantitate de [cantitate], fiind regăsit în produsele finite rezultate.
```

Exemplu pentru produs fără producție:

```text
Pentru articolul [cod], lot [lot], nu au fost identificate înregistrări de producție sau consum în PRD. Trasabilitatea este de tip WMS-only și se bazează pe recepțiile și livrările din WMS.
```

## Tabele obligatorii

În funcție de tipul cazului, raportul trebuie să includă tabele pentru:

- producție;
- livrări PF;
- materii prime;
- ambalaje;
- auxiliare / gaz;
- livrări MP către terți;
- recepții WMS;
- consumuri PRD;
- stoc.

## Documente WMS obligatorii

Când există, se afișează:

```text
Numar comanda
Document intrare
Document comanda
```

Recepții:

```text
Numar comanda
Document intrare
Document comanda
Furnizor
Cantitate
UM
```

Livrări:

```text
Numar comanda
Document comanda
Client
Cantitate
UM
```

## Secțiuni fără date

Nu se lasă secțiuni goale.

Exemple:

```text
Nu au fost identificate materiale auxiliare / gaz pentru acest lot.
Nu au fost identificate livrări către terți pentru loturile de materie primă folosite.
Nu au fost identificate înregistrări PRD pentru acest articol și lot.
Articolul nu apare explicit în stocul la moment.
```

## AVAL MP

Dacă un lot MP are până la 5 livrări către terți, acestea se afișează în corpul raportului.

Dacă un lot MP are peste 5 livrări către terți:

```text
corp raport = sumar
anexă = detaliu complet
```

## Semnături

Raportul se încheie cu:

```text
Întocmit de
Verificat de
Luare la cunoștință
```
