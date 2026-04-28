# Specificație funcțională — TraceAI Control Modul Trasabilitate

## 1. Obiectiv

Aplicația generează un raport DOCX auditabil de trasabilitate pentru un articol și lot.

Input utilizator:

```text
Cod articol
Lot
```

Surse:

```text
trasabilitate_wms.csv
rapoarte productie.csv
nomenclator.xlsx
stoc la moment original.xlsx
```

Output principal:

```text
Raport DOCX de trasabilitate
```

## 2. Surse oficiale

### WMS

Sursă pentru:

- mișcări;
- recepții;
- livrări;
- parteneri;
- loturi;
- cantități;
- unități de măsură;
- Numar comanda;
- Document intrare;
- Document comanda.

### PRD / rapoarte producție

Sursă pentru:

- comenzi de producție;
- produs finit obținut;
- lot produs finit;
- consumuri componente;
- cantitate produsă;
- DDM.

### Nomenclator

Sursă suport pentru:

- denumiri;
- clasificare articol;
- categorie articol.

### Stoc la moment

Sursă pentru:

- stoc rămas;
- confirmare lipsă poziție;
- validare finală.

## 3. Surse excluse

Nu se folosesc:

```text
WME / fișă magazie
PP-03
OperatorView
patch-uri vechi
fișiere debug
```

Regulă obligatorie:

```text
Document intrare = WMS
Numar comanda = WMS
Document comanda = WMS
```

## 4. Tipuri de cazuri

Aplicația trebuie să detecteze automat:

```text
FINISHED_PRODUCT
RAW_MATERIAL
WMS_ONLY_PRODUCT
UNKNOWN
```

### FINISHED_PRODUCT

Caz în care codul și lotul apar în PRD ca produs finit rezultat.

Raportul include:

- producția lotului;
- AVAL produs finit;
- AMONTE materii prime;
- AMONTE ambalaje;
- AMONTE auxiliare / gaz;
- AVAL MP;
- stoc;
- concluzie.

### RAW_MATERIAL

Caz în care codul și lotul apar ca materie primă recepționată în WMS și consumată în PRD.

Raportul include:

- recepția materiei prime;
- mișcări WMS;
- consumuri în producție;
- produse finite rezultate;
- livrări directe către terți;
- stoc;
- concluzie.

### WMS_ONLY_PRODUCT

Caz în care codul și lotul apar în WMS, dar nu apar în PRD ca produs finit sau materie primă consumată.

Raportul include:

- recepție WMS;
- livrare WMS;
- bilanț recepționat-livrat-stoc;
- observație privind lipsa fluxului PRD;
- concluzie.

### UNKNOWN

Caz în care nu există date suficiente în surse.

Raportul trebuie să spună explicit că datele nu sunt suficiente.

## 5. Reguli business

### Bilanț produs finit

Se compară:

```text
cantitate produsă PRD
cantitate livrată WMS
stoc la moment
```

Verdicte:

```text
TRASABILITATE COERENTĂ
TRASABILITATE COERENTĂ CU OBSERVAȚII
TRASABILITATE INCOMPLETĂ
NECESITĂ VERIFICARE MANUALĂ
```

### Clasificare componente

Componentele se împart în:

```text
Materii prime alimentare
Ambalaje
Materiale auxiliare / consumabile tehnologice
```

Regulă obligatorie:

```text
GAZ ALIMENTAR ALISOL = material auxiliar / consumabil tehnologic
GAZ ALIMENTAR ALISOL != materie primă alimentară
```

### Unități de măsură

Unitățile nu se convertesc automat.

```text
kg rămâne kg
buc rămâne buc
m³ rămâne m³
```

Pentru produse cu gramaj fix:

```text
bilanțul se face în bucăți
greutatea se afișează separat ca echivalent
```

### AVAL MP

Pentru fiecare lot de materie primă alimentară folosit într-un produs finit, aplicația caută mișcările WMS ale acelui cod + lot.

Dacă există livrări către terți, acestea se afișează.

Dacă nu există, raportul spune explicit:

```text
Nu au fost identificate livrări către terți pentru loturile de materie primă folosite.
```

### Secțiuni fără date

Secțiunile fără date nu se lasă goale. Se afișează explicație explicită.

Exemple:

```text
Nu au fost identificate materiale auxiliare / gaz pentru acest lot.
Nu au fost identificate înregistrări PRD pentru acest articol și lot.
Articolul nu apare explicit în stocul la moment.
```

## 6. Livrabil DOCX

Raportul DOCX trebuie să fie:

- narativ;
- auditabil;
- clar;
- adaptat complexității cazului;
- cu tabele scurte și relevante;
- cu concluzie preliminară;
- cu recomandare operațională;
- cu secțiune de semnături.

Nu trebuie să fie un Excel copiat în Word.
