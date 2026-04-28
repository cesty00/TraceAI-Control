# Teste validate — TraceAI Control Modul Trasabilitate

Acest document conține cazurile virtuale validate înainte de dezvoltarea aplicației.

## Test matrix v1

| Test | Cod / Lot | Tip caz | Scop test | Verdict |
|---|---|---|---|---|
| 1 | DS099903883 / 105.26 | FINISHED_PRODUCT | păstrăv PENNY, gaz, AVAL MP punctual | Acceptat |
| 2 | DS099904006 / 091.26 | FINISHED_PRODUCT | păstrăv LIDL, flux complex, MP multiple, UM diferite | Acceptat |
| 3 | DS099904181 / 092.26 | FINISHED_PRODUCT | somon LIDL, AVAL MP complex, fără gaz | Acceptat |
| 4 | DS099904127 / 098.26 | FINISHED_PRODUCT | somon 200G PENNY, produs în bucăți | Acceptat |
| 5 | DS099904015 / 105.26 | FINISHED_PRODUCT | doradă LIDL, flux simplu, o comandă | Acceptat |
| 6 | DS099904130 / 90994-082 | RAW_MATERIAL | materie primă ca subiect principal | Acceptat |
| 7 | DS099903913 / 896 | WMS_ONLY_PRODUCT | produs fără producție | Acceptat |

## Test 1 — DS099903883 / 105.26

Tip caz:

```text
FINISHED_PRODUCT
```

Rezumat:

```text
Produs: PF-REFRIGERAT-P PASTRAV EVISCERAT GREUTATE VARIABILA ATM PENNY
Cantitate produsă PRD: 734 kg
Cantitate livrată WMS: 734 kg
Stoc operațional: 0 kg
```

Reguli validate:

- gazul ALISOL este auxiliar, nu materie primă alimentară;
- materiile prime alimentare sunt separate de ambalaje și auxiliare;
- există livrări către terți pentru lotul MP DS099903892 / 547803;
- Document intrare, Numar comanda și Document comanda se iau din WMS.

## Test 2 — DS099904006 / 091.26

Tip caz:

```text
FINISHED_PRODUCT
```

Rezumat:

```text
Produs: PF-REFRIGERAT-P PASTRAV CURCUBEU EVISCERAT GREUTATE VARIABILA ATM LIDL
Cantitate produsă PRD: 7.524 kg
Cantitate livrată WMS: 7.524 kg
Stoc operațional: 0 kg
```

Reguli validate:

- raportul suportă materii prime multiple;
- raportul suportă UM diferite;
- AVAL MP poate fi extins;
- unele recepții WMS pot lipsi pentru anumite ambalaje și trebuie marcate ca observații.

## Test 3 — DS099904181 / 092.26

Tip caz:

```text
FINISHED_PRODUCT
```

Rezumat:

```text
Produs: PF-REFRIGERAT-P FILE DE SOMON NORVEGIAN CU PIELE GREUTATE VARIABILA VID LIDL
Cantitate produsă PRD: 5.363 kg
Cantitate livrată WMS: 5.363 kg
Stoc operațional: 0 kg
```

Reguli validate:

- raportul funcționează și pentru familia somon;
- raportul suportă multe loturi MP;
- AVAL MP poate necesita anexă;
- secțiunea gaz/auxiliare poate fi goală, dar trebuie explicată.

## Test 4 — DS099904127 / 098.26

Tip caz:

```text
FINISHED_PRODUCT
```

Rezumat:

```text
Produs: PF-REFRIGERAT-P FILE SOMON 200G ATM PENNY
Cantitate produsă PRD: 4.840 bucăți
Greutate echivalentă: 968 kg
Cantitate livrată WMS: 4.840 bucăți
Stoc operațional: 0 bucăți
```

Reguli validate:

- produsul finit poate fi în bucăți;
- reconcilierea se face în unitatea produsului finit;
- greutatea se afișează separat ca echivalent;
- MP rămâne în kg;
- gazul rămâne în m³.

## Test 5 — DS099904015 / 105.26

Tip caz:

```text
FINISHED_PRODUCT
```

Rezumat:

```text
Produs: PF-REFRIGERAT-P DORADA PROASPATA EVISCERATA GREUTATE VARIABILA ATM LIDL
Cantitate produsă PRD: 2.972 kg
Cantitate livrată WMS: 2.972 kg
Stoc operațional: 0 kg
```

Reguli validate:

- raportul trebuie să fie scurt pentru fluxuri simple;
- o singură comandă de producție este suficientă pentru raport;
- o singură livrare poate închide bilanțul;
- diferența MP consumată vs PF rezultat este randament, nu eroare automată.

## Test 6 — DS099904130 / 90994-082

Tip caz:

```text
RAW_MATERIAL
```

Rezumat:

```text
Articol: CREVETI INTREGI PREFIERTI 40-60 BAX 5 KG ASC
Recepționat WMS: 6.400 kg
Consumat PRD: 4.320 kg
Stoc la moment: 891,20 kg
```

Reguli validate:

- aplicația suportă materia primă ca subiect principal;
- raportul trebuie să afișeze recepția MP;
- raportul trebuie să afișeze consumurile în producție;
- raportul trebuie să afișeze produsele finite rezultate;
- raportul trebuie să afișeze stocul rămas.

## Test 7 — DS099903913 / 896

Tip caz:

```text
WMS_ONLY_PRODUCT
```

Rezumat:

```text
Articol: REFRIGERAT-P SOMON EVISCERAT 3-4
Recepționat WMS: 580,60 kg
Livrat WMS: 580,60 kg
Stoc operațional: 0 kg
```

Reguli validate:

- aplicația nu eșuează dacă articolul nu apare în PRD;
- raportul devine WMS-only;
- raportul include recepție, livrare, bilanț și concluzie;
- lipsa fluxului PRD este menționată explicit.

## Concluzie

Cele 7 teste acoperă baza minimă pentru dezvoltarea aplicației instalabile:

- produs finit simplu;
- produs finit complex;
- produs finit în bucăți;
- materie primă ca subiect;
- produs fără producție;
- AVAL MP simplu și complex;
- gaz ca auxiliar;
- lipsă gaz;
- UM diferite;
- randament tehnologic.
