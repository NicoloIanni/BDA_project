# OCPM Partial Order — Order Management Prototype

Prototipo universitario per la costruzione di **Instance Graph object-centric a ordine parziale** a partire da process execution estratte da un log OCEL 2.0.

Il progetto è sviluppato da **Nicolò Ianni** e **Danilo La Palombara** nell’ambito di Big Data Analytics e Object-Centric Process Mining.

> **Stato attuale:** sono state completate l’esplorazione del dataset, la discovery preliminare della Object-Centric Petri Net, la costruzione dell’Instance Graph su un esempio sintetico e su una process execution reale e la derivazione automatica di causal relations mediante filtraggio dell’Object-Centric Directly-Follows Graph.
>
> Per l’ordine reale `o-990424` è stato costruito automaticamente un Instance Graph con 7 nodi e 6 archi. Il grafo è un DAG, è transitivamente ridotto e conserva due rami causali incomparabili.
>
> Le causal relations automatiche non sono ricavate direttamente dagli archi della OCPN: vengono inferite dalle frequenze dell’OC-DFG mediante dependency measure e supporto relativo. Non è stato ancora eseguito un conformance checking object-centric formale e non è stata dimostrata una fitness pari a 1.

---

## 1. Obiettivo

Nel process mining tradizionale gli eventi vengono normalmente organizzati in tracce utilizzando un singolo `case_id`. Questa rappresentazione è limitante per processi nei quali uno stesso evento può coinvolgere contemporaneamente entità differenti, come:

- un ordine;
- uno o più articoli;
- un pacco;
- un prodotto;
- un dipendente.

L’Object-Centric Process Mining evita di scegliere in anticipo un unico identificatore di caso e mantiene i collegamenti tra eventi e oggetti di tipi differenti.

Questo progetto adatta a tale contesto il concetto di **Instance Graph**, rappresentando una process execution mediante un grafo diretto nel quale:

- ogni nodo rappresenta un evento;
- ogni arco rappresenta una dipendenza causale ammessa;
- ogni arco conserva i tipi e gli identificatori degli oggetti che giustificano la relazione;
- gli eventi senza un ordine causale imposto restano incomparabili;
- la riduzione transitiva elimina gli archi ridondanti senza modificare la raggiungibilità.

L’obiettivo non è trasformare la process execution in una sequenza cronologica totale. Il timestamp descrive l’ordine osservato degli eventi, ma non è sufficiente da solo a dimostrare una dipendenza causale.

L’obiettivo è quindi evitare che l’ordinamento temporale imponga artificialmente un ordine tra eventi che il modello causale permette di considerare indipendenti.

---

## 2. Pipeline del progetto

La pipeline attualmente implementata è:

```text
OCEL 2.0 Order Management
        |
        +--> esplorazione del log
        |
        +--> discovery preliminare della OCPN
        |        |
        |        +--> analisi diagnostica della struttura
        |
        +--> discovery dell'OC-DFG
        |        |
        |        +--> dependency measure
        |        +--> supporto relativo
        |        +--> filtraggio delle relazioni
        |        |
        |        v
        |   causal relations automatiche
        |
        +--> estrazione order-centred
                 |
                 v
          ProcessExecution interna
                 |
                 v
        costruzione Instance Graph
                 |
                 +--> controllo DAG
                 +--> riduzione transitiva
                 +--> annotazione degli archi
                 +--> eventi incomparabili
                 +--> visualizzazione
```

La pipeline automatica viene confrontata con una baseline precedente basata su causal relations definite manualmente:

```text
ProcessExecution reale
        +
causal relations manuali
        |
        v
Instance Graph di riferimento
```

Il file manuale rimane nel repository come baseline controllata, ma non viene caricato dallo script automatico del Blocco 05.

---

## 3. Distinzione tra le fasi

Nel progetto devono rimanere distinte almeno cinque attività:

1. **Model discovery**
   Ricavare un modello di processo dal log.

2. **Estrazione della process execution**
   Delimitare gli eventi e gli oggetti che costituiscono una specifica esecuzione.

3. **Inferenza delle causal relations**
   Stabilire quali coppie di attività rappresentano dipendenze causali candidate.

4. **Costruzione dell’Instance Graph**
   Applicare le causal relations agli eventi della process execution.

5. **Conformance checking**
   Verificare formalmente se la process execution può essere riprodotta dal modello.

Il completamento di una fase non dimostra automaticamente il completamento delle altre.

In particolare:

- la discovery della OCPN non dimostra che una execution sia conforme;
- la presenza di un percorso nella OCPN non implica necessariamente una relazione causale diretta utile per l’Instance Graph;
- la costruzione corretta di un DAG non dimostra una fitness pari a 1;
- la corrispondenza con il caso di studio non dimostra che le soglie scelte siano universalmente valide.

---

## 4. Semplificazioni e limiti metodologici

La prima iterazione del progetto assume volutamente che:

- la process execution da analizzare possa essere estratta dal log;
- non siano necessari repairing della execution;
- non siano necessari inserimenti o cancellazioni di eventi;
- non vengano ancora calcolati object-centric alignment;
- l’algoritmo dell’Instance Graph resti indipendente dalla tecnica di estrazione;
- il modello dati interno non dipenda dalle classi private di PM4Py o OCPA;
- le causal relations siano rappresentate a livello di attività e tipo di oggetto;
- non siano ancora risolti in modo generale tutti i casi con loop, attività ripetute o transizioni diverse aventi la stessa etichetta.

Nel Blocco 04 le causal relations erano fornite manualmente.

Nel Blocco 05 è stata aggiunta una derivazione automatica basata sull’OC-DFG. Questa costituisce un avanzamento rispetto alla baseline manuale, ma non equivale a una derivazione formale delle relazioni direttamente dalla semantica di esecuzione della OCPN.

---

## 5. Dataset Order Management

Il dataset ufficiale del progetto è **Order Management**, memorizzato localmente in formato OCEL 2.0 SQLite:

```text
data/raw/order_management.sqlite
```

Il dataset non viene incluso nel repository e deve essere copiato manualmente nella cartella indicata.

L’esplorazione eseguita nel notebook `02_ocel_exploration.ipynb` ha prodotto i seguenti risultati:

| Misura | Valore |
| --- | ---: |
| Eventi | 21.008 |
| Oggetti | 10.825 |
| Relazioni evento-oggetto | 143.463 |
| Attività | 11 |
| Tipi di oggetto | 5 |

I tipi di oggetto presenti sono:

- `orders`;
- `items`;
- `packages`;
- `products`;
- `employees`.

Il log contiene solamente 20 prodotti e 18 dipendenti, condivisi trasversalmente tra numerosi ordini.

Questa struttura rende pericolosa un’espansione indiscriminata basata sulle connected components: gli oggetti `products` ed `employees` possono comportarsi come ponti e collegare process execution appartenenti a ordini differenti.

Per il primo caso reale è stata quindi adottata un’estrazione **order-centred**.

---

## 6. Stato dei blocchi

### Blocco 01 — Configurazione dell’ambiente

L’ambiente è stato configurato e verificato su Windows con:

- Python 3.12.0;
- ambiente virtuale `.venv`;
- PM4Py 2.7.23.3;
- pandas 3.0.5;
- NetworkX 3.6.1;
- Matplotlib 3.11.1;
- Graphviz Python package 0.21;
- pytest 9.1.1;
- Jupyter;
- ipykernel.

L’interprete della virtual environment viene richiamato esplicitamente:

```powershell
.\.venv\Scripts\python.exe
```

Questo evita di eseguire accidentalmente gli script con l’installazione globale di Python.

---

### Blocco 02 — Esplorazione dell’OCEL

Il notebook `02_ocel_exploration.ipynb`:

- carica il file SQLite OCEL 2.0;
- analizza eventi, oggetti e relazioni evento-oggetto;
- conta le attività e i tipi di oggetto;
- misura quanti oggetti sono associati agli eventi;
- analizza la condivisione degli oggetti;
- documenta il rischio di un’espansione eccessiva attraverso `products` ed `employees`.

Questa fase guida la scelta della strategia di estrazione, ma non modifica la logica centrale dell’Instance Graph.

---

### Blocco 03 — Discovery preliminare della OCPN

Il notebook `03_ocpn_discovery.ipynb` usa PM4Py per effettuare la discovery preliminare di una Object-Centric Petri Net.

La funzione utilizzata è:

```python
pm4py.discover_oc_petri_net(ocel)
```

La versione di PM4Py usata nel progetto espone i seguenti parametri principali:

- `inductive_miner_variant`;
- `noise_threshold`;
- `multi_processing`;
- `disable_fallthroughs`;
- `disable_strict_sequence_cut`;
- `diagnostics_with_tbr`.

Il risultato della discovery comprende:

- 11 attività;
- 5 tipi di oggetto;
- una Petri net per ogni tipo di oggetto;
- attività iniziali e finali;
- informazioni sugli archi;
- informazioni sulle molteplicità;
- dati prestazionali.

Il notebook è stato eseguito integralmente senza errori.

Questa fase dimostra la discovery del modello, non la conformità delle process execution.

In particolare, i risultati di token-based replay non sono stati utilizzati per dimostrare una fitness pari a 1.

---

### Prototipo preliminare — Toy example

Prima di usare il dataset reale è stata verificata la pipeline su una process execution sintetica controllata del dominio Order Management.

Il toy example comprende:

- 7 eventi;
- 6 causal relations manuali;
- costruzione dell’Instance Graph;
- controllo che il grafo sia un DAG;
- riduzione transitiva;
- ricerca delle coppie incomparabili;
- generazione di una figura PNG mediante Graphviz;
- confronto tra due linearizzazioni temporali equivalenti.

Il test sulle linearizzazioni verifica che l’inversione temporale di due eventi appartenenti a rami causali indipendenti produca lo stesso Instance Graph.

Questo risultato vale per il toy example e non costituisce una dimostrazione generale su tutte le process execution del dataset.

---

### Blocco 04 — Instance Graph su una execution reale

Il Blocco 04 applica la pipeline all’ordine reale:

```text
o-990424
```

#### Estrazione order-centred

L’estrazione segue questo criterio:

1. seleziona `o-990424` come leading object;
2. individua gli `items` collegati all’ordine;
3. individua i `packages` collegati agli item;
4. seleziona gli eventi appartenenti alla porzione individuata;
5. conserva, per ogni evento, i riferimenti agli oggetti coinvolti;
6. impedisce l’espansione verso oggetti strutturali appartenenti ad altri ordini.

`products` ed `employees` non vengono usati per espandere la process execution perché sono oggetti informativi condivisi tra numerosi ordini.

Non vengono rimossi dal dataset: vengono esclusi solamente dalla regola di espansione.

La funzione pubblica utilizzata è:

```python
extract_order_centred_execution(
    ocel=ocel,
    order_id="o-990424",
)
```

L’adapter converte gli eventi OCEL selezionati nel modello interno `ProcessExecution`, mantenendo separati:

- il codice di caricamento;
- la strategia di estrazione;
- la rappresentazione interna;
- la costruzione del grafo.

#### Baseline con causal relations manuali

Le sei causal relations della baseline sono caricate da:

```text
data/derived/order_management_o_990424_causal_relations.json
```

Ogni relazione specifica:

- attività sorgente;
- attività destinazione;
- tipo di oggetto che giustifica il collegamento.

Le relazioni contenute in questo file sono state definite manualmente.

Il file rimane utile come:

- baseline controllata;
- riferimento per i test;
- confronto con la derivazione automatica;
- documentazione esplicita dell’ipotesi causale iniziale.

#### Risultato della baseline

Per l’ordine `o-990424` sono stati ottenuti:

| Proprietà | Risultato |
| --- | ---: |
| Eventi/nodi | 7 |
| Archi causali | 6 |
| Grafo diretto aciclico | sì |
| Grafo transitivamente ridotto | sì |
| Coppie incomparabili | 8 |

La topologia ottenuta è:

```text
                 confirm order -> pay order
                /
place order ---
                \
                 pick item -> create package -> send package
                                              -> package delivered
```

Rappresentata senza la disposizione grafica:

```text
place order -> confirm order -> pay order
place order -> pick item -> create package
create package -> send package -> package delivered
```

Gli archi della baseline manuale sono:

| Sorgente | Destinazione | Tipo di oggetto |
| --- | --- | --- |
| `place order` | `confirm order` | `orders` |
| `confirm order` | `pay order` | `orders` |
| `place order` | `pick item` | `items` |
| `pick item` | `create package` | `items` |
| `create package` | `send package` | `packages` |
| `send package` | `package delivered` | `packages` |

Dopo `place order` emergono due rami distinti:

- ramo amministrativo: `confirm order -> pay order`;
- ramo logistico: `pick item -> create package -> send package -> package delivered`.

I due eventi del ramo amministrativo sono incomparabili con i quattro eventi del ramo logistico:

```text
2 × 4 = 8 coppie incomparabili
```

`pay order` possiede un timestamp successivo a `package delivered`, ma il grafo non contiene l’arco:

```text
package delivered -> pay order
```

Il timestamp stabilisce una successione osservata, ma da solo non dimostra una dipendenza causale.

---

### Blocco 05 — Derivazione automatica delle causal relations

Il Blocco 05 sostituisce, nella nuova pipeline, il file di causal relations manuali con una procedura automatica.

Il lavoro è stato diviso in due analisi:

1. tentativo di estrazione delle relazioni dalla struttura delle Petri net per tipo di oggetto;
2. inferenza statistica delle relazioni a partire dall’OC-DFG.

#### Analisi della struttura della OCPN

Sono state analizzate le Petri net scoperte da PM4Py per i tipi:

- `orders`;
- `items`;
- `packages`.

Per `orders` e `packages`, la raggiungibilità tra transizioni visibili ha prodotto relazioni coerenti con il caso di studio.

Per `items`, invece, la net scoperta presenta una struttura fortemente ciclica e generalizzante. Numerose transizioni visibili condividono le stesse regioni della rete e risultano reciprocamente raggiungibili.

Il risultato della raggiungibilità visibile è stato:

| Tipo | Relazioni totali | Relazioni rilevanti | Attese presenti | Aggiuntive |
| --- | ---: | ---: | ---: | ---: |
| `orders` | 5 | 2 | 2/2 | 0 |
| `items` | 110 | 42 | 2/2 | 40 |
| `packages` | 5 | 2 | 2/2 | 0 |

Nel caso `items`, la sola raggiungibilità strutturale accetta quasi tutte le direzioni tra le attività del caso reale, comprese relazioni reciproche e auto-relazioni.

Per questo motivo non viene utilizzata come sorgente finale delle causal relations.

Questa analisi rimane comunque utile perché documenta un limite concreto dell’estrazione ingenua dalla OCPN scoperta.

#### Verifica dei parametri dell’Inductive Miner

Sono state confrontate diverse configurazioni della discovery:

- `im` con soglia di rumore `0.0`;
- `imf` con soglie `0.05`, `0.10`, `0.20` e `0.30`.

Le configurazioni `imf` fino a `0.20` non modificano la struttura problematica della net `items`.

Con soglia `0.30`, la struttura cambia sensibilmente, ma viene persa la relazione attesa:

```text
pick item -> create package
```

Il semplice aumento della soglia di rumore non risolve quindi il problema in modo soddisfacente.

#### Utilizzo dell’OC-DFG

La soluzione adottata usa l’Object-Centric Directly-Follows Graph scoperto dal log.

Per ogni tipo di oggetto e per ogni coppia di attività `(a, b)` vengono considerate:

- la frequenza `f(a,b)` della relazione diretta `a -> b`;
- la frequenza opposta `f(b,a)`;
- la dependency measure;
- il supporto relativo rispetto alle relazioni uscenti da `a`.

La dependency measure utilizzata è:

```text
dependency(a,b) =
    (f(a,b) - f(b,a))
    /
    (f(a,b) + f(b,a) + 1)
```

Il supporto relativo è:

```text
relative_support(a,b) =
    f(a,b)
    /
    max_y f(a,y)
```

dove il denominatore rappresenta la massima frequenza di un arco uscente dall’attività `a`, per lo stesso tipo di oggetto.

Una relazione viene selezionata quando soddisfa entrambe le condizioni:

```text
dependency(a,b) >= dependency_threshold
```

e:

```text
relative_support(a,b) >= relative_support_threshold
```

Le auto-relazioni vengono escluse dalla selezione.

#### Soglie adottate

I valori predefiniti scelti sono:

```text
dependency_threshold = 0.90
relative_support_threshold = 0.05
```

Questi valori sono stati verificati mediante un’analisi di sensibilità.

Le soglie considerate sono state:

```text
dependency:
0.80, 0.85, 0.90, 0.95, 0.97, 0.98

relative support:
0.01, 0.05, 0.10, 0.20
```

La topologia esatta del caso di riferimento è stata ottenuta per tutte le combinazioni con:

```text
dependency compresa tra 0.80 e 0.97
relative support compreso tra 0.05 e 0.20
```

Si tratta di 15 configurazioni esatte.

Con supporto relativo `0.01` viene aggiunta la relazione:

```text
pick item -> send package
```

Con dependency `0.98` viene invece eliminata la relazione:

```text
pick item -> create package
```

La configurazione `0.90 / 0.05` non rappresenta quindi un singolo punto isolato che funziona per caso, ma appartiene a una regione stabile rispetto al caso di studio.

Questa stabilità è stata verificata esclusivamente rispetto a `o-990424` e non dimostra la validità universale delle soglie.

#### Evidenze principali

Alcune delle relazioni più rilevanti osservate nell’OC-DFG sono:

| Tipo | Relazione | Forward | Backward | Dependency | Supporto relativo |
| --- | --- | ---: | ---: | ---: | ---: |
| `orders` | `place order -> confirm order` | 2000 | 0 | 1.000 | 1.000 |
| `orders` | `confirm order -> pay order` | 1557 | 0 | 0.999 | 1.000 |
| `items` | `place order -> pick item` | 1915 | 0 | 0.999 | 1.000 |
| `items` | `pick item -> create package` | 5290 | 66 | 0.975 | 1.000 |
| `items` | `create package -> send package` | 1122 | 0 | 0.999 | 1.000 |
| `items` | `send package -> package delivered` | 913 | 0 | 0.999 | 1.000 |
| `packages` | `create package -> send package` | 1128 | 0 | 0.999 | 1.000 |
| `packages` | `send package -> package delivered` | 914 | 0 | 0.999 | 1.000 |

La relazione `pick item -> create package` è il caso più vicino alla soglia:

```text
forward = 5290
backward = 66
dependency = 0.975
```

Per questo motivo una dependency threshold pari a `0.98` la elimina.

#### Risultato della derivazione automatica

La procedura automatica seleziona:

```text
22 causal relations complessive
```

considerando tutte le attività e i tipi di oggetto rilevanti dell’OC-DFG.

Tra queste, 10 sono applicabili alle attività e agli oggetti presenti nella process execution di `o-990424`:

| Sorgente | Destinazione | Tipo |
| --- | --- | --- |
| `confirm order` | `pay order` | `items` |
| `confirm order` | `pay order` | `orders` |
| `create package` | `send package` | `items` |
| `create package` | `send package` | `packages` |
| `pick item` | `create package` | `items` |
| `place order` | `confirm order` | `items` |
| `place order` | `confirm order` | `orders` |
| `place order` | `pick item` | `items` |
| `send package` | `package delivered` | `items` |
| `send package` | `package delivered` | `packages` |

Più causal relations riferite a tipi di oggetto differenti possono produrre lo stesso arco tra due eventi.

Per questo motivo le 10 relazioni rilevanti producono comunque esattamente 6 archi nel grafo.

#### Instance Graph automatico

Il grafo costruito con le relazioni derivate automaticamente possiede:

| Proprietà | Risultato |
| --- | ---: |
| Nodi | 7 |
| Archi | 6 |
| DAG | sì |
| Transitivamente ridotto | sì |
| Coppie incomparabili | 8 |
| Archi attesi mancanti | 0 |
| Archi aggiuntivi | 0 |

Gli archi e le relative annotazioni sono:

| Sorgente | Destinazione | Tipi di oggetto | Identificatori |
| --- | --- | --- | --- |
| `place order` | `confirm order` | `items`, `orders` | `i-881734`, `o-990424` |
| `confirm order` | `pay order` | `items`, `orders` | `i-881734`, `o-990424` |
| `place order` | `pick item` | `items` | `i-881734` |
| `pick item` | `create package` | `items` | `i-881734` |
| `create package` | `send package` | `items`, `packages` | `i-881734`, `p-660247` |
| `send package` | `package delivered` | `items`, `packages` | `i-881734`, `p-660247` |

La topologia coincide esattamente con quella della baseline manuale:

```text
place order -> confirm order -> pay order
place order -> pick item -> create package
create package -> send package -> package delivered
```

Le annotazioni automatiche sono più ricche rispetto alla baseline manuale perché una stessa relazione può essere supportata da più tipi di oggetto.

La figura viene salvata in:

```text
outputs/graphs/order_management_o_990424_discovered_instance_graph.png
```

#### Interpretazione metodologica

Il risultato corretto deve essere descritto nel modo seguente:

> Le causal relations sono inferite automaticamente dall’OC-DFG mediante dependency measure e supporto relativo e vengono successivamente applicate alla process execution estratta.

Non deve essere descritto come:

> Le causal relations sono lette direttamente dagli archi della OCPN.

La OCPN viene scoperta e analizzata, ma la sorgente operativa delle relazioni automatiche del Blocco 05 è l’OC-DFG filtrato.

---

## 7. Struttura del repository

```text
ocpm-partial-order/
|-- data/
|   |-- raw/
|   |   `-- order_management.sqlite
|   |-- samples/
|   |   |-- order_management_toy_execution.json
|   |   |-- order_management_toy_execution_reordered.json
|   |   `-- order_management_toy_causal_relations.json
|   `-- derived/
|       `-- order_management_o_990424_causal_relations.json
|
|-- notebooks/
|   |-- 01_environment_check.ipynb
|   |-- 02_ocel_exploration.ipynb
|   |-- 03_ocpn_discovery.ipynb
|   |-- 03_ocpn_discovery.executed.ipynb
|   |-- 04_real_instance_graph.ipynb
|   |-- 05_instance_graph.ipynb
|   `-- 06_real_execution.ipynb
|
|-- outputs/
|   |-- figures/
|   |-- graphs/
|   |   |-- order_management_toy_instance_graph.png
|   |   |-- order_management_o_990424_instance_graph.png
|   |   `-- order_management_o_990424_discovered_instance_graph.png
|   |-- reports/
|   `-- tables/
|
|-- scripts/
|   |-- check_environment.py
|   |-- inspect_ocel.py
|   |-- inspect_order_candidates.py
|   |-- run_order_management_toy.py
|   |-- run_order_management_real.py
|   |-- run_order_management_discovered.py
|   |-- run_toy_example.py
|   `-- verify_real_execution.py
|
|-- src/
|   `-- ocpm_partial_order/
|       |-- __init__.py
|       |-- config.py
|       |
|       |-- discovery/
|       |   |-- __init__.py
|       |   |-- causal_relations.py
|       |   `-- ocpn_discovery.py
|       |
|       |-- domain/
|       |   |-- __init__.py
|       |   |-- causal_relation.py
|       |   |-- event.py
|       |   `-- process_execution.py
|       |
|       |-- extraction/
|       |   |-- __init__.py
|       |   `-- execution_adapter.py
|       |
|       |-- graphs/
|       |   |-- __init__.py
|       |   |-- concurrency.py
|       |   |-- instance_graph.py
|       |   `-- validation.py
|       |
|       |-- io/
|       |   |-- __init__.py
|       |   |-- ocel_loader.py
|       |   `-- sample_loader.py
|       |
|       `-- visualization/
|           |-- __init__.py
|           `-- graph_visualizer.py
|
|-- tests/
|   |-- fixtures/
|   |-- test_causal_relations.py
|   |-- test_concurrency.py
|   |-- test_discovered_causal_relations.py
|   |-- test_equivalent_linearizations.py
|   |-- test_execution_adapter.py
|   |-- test_instance_graph.py
|   |-- test_real_instance_graph.py
|   `-- test_sample_loader.py
|
|-- .gitignore
|-- pyproject.toml
|-- requirements.txt
`-- README.md
```

Alcuni notebook futuri possono essere presenti come file vuoti o segnaposto. La loro presenza nel repository non implica che il relativo blocco sia già stato completato.

Gli artefatti contenuti in `outputs/` sono rigenerabili.

Il dataset contenuto in `data/raw/` resta locale e non deve essere versionato.

Il file in `data/derived/` rappresenta invece la baseline manuale del caso reale ed è un input riproducibile dei test precedenti.

---

## 8. Modello dati interno

L’algoritmo non usa direttamente le rappresentazioni interne di PM4Py o OCPA.

### `ObjectReference`

Rappresenta un oggetto coinvolto in un evento:

- `object_id`;
- `object_type`.

### `ExecutionEvent`

Rappresenta un evento della process execution:

- `event_id`;
- `activity`;
- `timestamp`;
- insieme di `ObjectReference`.

### `ProcessExecution`

Contiene gli eventi di una process execution e offre metodi per ottenere:

- gli ID degli eventi;
- gli oggetti coinvolti;
- gli eventi associati a un oggetto specifico.

### `CausalRelation`

Descrive una relazione causale ammessa per uno specifico tipo di oggetto:

- `source_activity`;
- `target_activity`;
- `object_type`.

La classe è immutabile e può essere usata all’interno di insiemi.

### `CausalRelationEvidence`

Rappresenta le evidenze statistiche associate a una causal relation candidata.

Contiene le informazioni necessarie per documentare e verificare la selezione, tra cui:

- attività sorgente;
- attività destinazione;
- tipo di oggetto;
- frequenza forward;
- frequenza backward;
- dependency measure;
- supporto relativo.

Questa separazione permette di cambiare:

- dataset;
- libreria;
- tecnica di estrazione;
- tecnica di discovery;
- strategia di filtraggio;

senza riscrivere la logica centrale dell’Instance Graph.

---

## 9. Derivazione delle causal relations

Il modulo:

```text
src/ocpm_partial_order/discovery/causal_relations.py
```

espone due operazioni principali:

```python
score_causal_relations(...)
derive_causal_relations(...)
```

### `score_causal_relations`

Calcola le evidenze per le relazioni candidate presenti nell’OC-DFG.

Il risultato può essere usato per:

- ispezionare le frequenze;
- confrontare le direzioni opposte;
- analizzare la dependency measure;
- analizzare il supporto relativo;
- effettuare sensitivity analysis;
- spiegare perché una relazione è stata inclusa o esclusa.

### `derive_causal_relations`

Filtra le relazioni candidate e restituisce le `CausalRelation` che superano le soglie configurate.

Le soglie predefinite sono:

```python
dependency_threshold = 0.90
relative_support_threshold = 0.05
```

La funzione:

- valida che le soglie appartengano all’intervallo `[0, 1]`;
- rifiuta tipi di oggetto sconosciuti;
- esclude le auto-relazioni;
- confronta la frequenza forward con quella backward;
- filtra il rumore mediante supporto relativo;
- restituisce relazioni indipendenti dalla rappresentazione interna del grafo finale.

Le soglie sono parametri espliciti e possono essere modificate senza cambiare l’algoritmo di costruzione dell’Instance Graph.

---

## 10. Costruzione dell’Instance Graph

La funzione principale è:

```python
build_instance_graph(
    execution,
    causal_relations,
)
```

Il procedimento implementato:

1. valida la process execution;
2. crea un nodo per ogni evento;
3. salva nei nodi attività, timestamp e oggetti;
4. raggruppa le causal relations per tipo di oggetto;
5. ricostruisce il ciclo di vita di ogni oggetto;
6. ordina gli eventi dell’oggetto;
7. esamina le coppie di eventi nello stesso ciclo di vita;
8. aggiunge un arco quando la coppia di attività è ammessa per quel tipo di oggetto;
9. unisce le evidenze quando lo stesso arco è giustificato da più oggetti;
10. annota gli archi con `object_types` e `object_ids`;
11. verifica che il grafo sia un DAG;
12. applica la riduzione transitiva;
13. ripristina gli attributi non conservati automaticamente da NetworkX;
14. valida nuovamente il grafo ridotto.

NetworkX definisce la riduzione transitiva di un DAG come il grafo che conserva la stessa raggiungibilità eliminando gli archi per i quali esiste già un cammino alternativo.

L’algoritmo riceve un insieme di `CausalRelation` e non dipende dal modo in cui queste sono state ottenute.

Può quindi essere usato sia con:

- causal relations manuali;
- causal relations inferite automaticamente;
- eventuali tecniche di discovery future.

---

## 11. Incomparabilità e parallelismo potenziale

La funzione:

```python
find_incomparable_event_pairs(graph)
```

considera due eventi incomparabili quando non esiste:

- un cammino dal primo evento al secondo;
- né un cammino dal secondo evento al primo.

Nel progetto viene adottata la formulazione prudente:

```text
incomparabilità = candidato al parallelismo
```

L’incomparabilità non dimostra che due eventi siano avvenuti simultaneamente.

Dimostra solamente che l’Instance Graph costruito non impone un ordine causale tra i due eventi.

Nel caso reale, le coppie incomparabili sono:

```text
confirm order || pick item
confirm order || create package
confirm order || send package
confirm order || package delivered

pay order || pick item
pay order || create package
pay order || send package
pay order || package delivered
```

Sono quindi presenti 8 coppie incomparabili.

---

## 12. Installazione su Windows

### Prerequisiti

Sono necessari:

- Python 3.12;
- Git;
- Graphviz installato nel sistema;
- comando `dot` disponibile nel `PATH`.

Verifica di Graphviz:

```powershell
dot -V
```

### Creazione dell’ambiente virtuale

Dalla root del progetto:

```powershell
py -3.12 -m venv .venv
```

Aggiornamento di `pip`:

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
```

Installazione delle dipendenze:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Installazione del progetto in modalità editable:

```powershell
.\.venv\Scripts\python.exe -m pip install -e .
```

Installazione delle dipendenze di sviluppo, se necessaria:

```powershell
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

### Dataset reale

Copiare il file OCEL 2.0 SQLite in:

```text
data/raw/order_management.sqlite
```

Il dataset non deve essere aggiunto al repository Git.

---

## 13. Esecuzione

Tutti i comandi seguenti devono essere eseguiti dalla root del repository.

### Controllo dell’ambiente

```powershell
.\.venv\Scripts\python.exe .\scripts\check_environment.py
```

### Ispezione dell’OCEL

```powershell
.\.venv\Scripts\python.exe .\scripts\inspect_ocel.py
```

### Selezione dei candidati reali

```powershell
.\.venv\Scripts\python.exe .\scripts\inspect_order_candidates.py
```

### Toy example

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_toy.py
```

### Verifica dell’estrazione reale

```powershell
.\.venv\Scripts\python.exe .\scripts\verify_real_execution.py
```

### Caso reale con causal relations manuali

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_real.py
```

Questo script usa:

```text
data/derived/order_management_o_990424_causal_relations.json
```

### Caso reale con causal relations automatiche

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_discovered.py
```

Questo script esegue:

```text
OCEL
  -> OC-DFG
  -> scoring delle relazioni
  -> filtraggio automatico
  -> estrazione della execution
  -> Instance Graph
  -> validazione
  -> visualizzazione
```

Lo script non carica il file di causal relations manuali.

Il risultato atteso è:

```text
Causal relations totali: 22
Causal relations rilevanti: 10

Instance Graph:
Nodi: 7
Archi: 6
DAG: True

VERIFICA CON RELAZIONI DERIVATE SUPERATA
```

---

## 14. Notebook

Avvio di Jupyter Lab:

```powershell
.\.venv\Scripts\python.exe -m jupyter lab
```

L’ordine consigliato dei notebook è:

1. `01_environment_check.ipynb`;
2. `02_ocel_exploration.ipynb`;
3. `03_ocpn_discovery.ipynb`;
4. `04_real_instance_graph.ipynb`;
5. `05_instance_graph.ipynb`.

### Notebook 04

Documenta:

- estrazione order-centred;
- baseline manuale;
- costruzione del grafo reale;
- riduzione transitiva;
- coppie incomparabili;
- visualizzazione.

### Notebook 05

Documenta:

- analisi della struttura della OCPN;
- limite della raggiungibilità ingenua sulla net `items`;
- discovery dell’OC-DFG;
- dependency measure;
- supporto relativo;
- sensitivity analysis;
- causal relations derivate;
- costruzione automatica dell’Instance Graph;
- confronto con la topologia attesa;
- limiti metodologici.

Il notebook è stato verificato con:

```text
Celle totali: 24
Celle di codice: 9
Celle di codice eseguite: 9
Celle Markdown: 15
Errori: 0
Validazione notebook: superata
```

### Esecuzione non interattiva del Notebook 05

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    .\notebooks\05_instance_graph.ipynb `
    --ExecutePreprocessor.timeout=300
```

Su Windows possono comparire avvisi relativi a:

- `Proactor event loop`;
- comunicazione locale del kernel Jupyter tramite TCP non cifrata.

Nel contesto dell’esecuzione locale questi avvisi non indicano un errore del notebook. La verifica rilevante è l’assenza di output con `output_type = error`.

---

## 15. Test automatici

Esecuzione completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Risultato verificato dopo il Blocco 05:

```text
22 passed
```

La suite comprende:

| Area | Verifica |
| --- | --- |
| caricamento | parsing della toy execution e delle causal relations |
| modello dati | rappresentazione degli eventi e degli oggetti |
| grafo | nodi, archi, DAG e riduzione transitiva |
| incomparabilità | eventi appartenenti a rami causali distinti |
| linearizzazioni | stesso grafo per ordini temporali equivalenti |
| adapter | conversione della execution OCEL nel modello interno |
| estrazione | delimitazione order-centred e controllo degli oggetti esterni |
| baseline reale | nodi, archi e proprietà attese per `o-990424` |
| scoring | frequenze forward e backward, dependency e supporto |
| validazione | soglie non valide e tipi di oggetto sconosciuti |
| filtraggio | eliminazione delle relazioni rumorose |
| discovery reale | presenza delle causal relations attese |
| integrazione | costruzione del grafo usando relazioni automatiche |
| ordine parziale | conservazione delle coppie incomparabili |

I test specifici del Blocco 05 sono contenuti in:

```text
tests/test_causal_relations.py
tests/test_discovered_causal_relations.py
```

Il primo contiene 7 test unitari.

Il secondo contiene 3 test di integrazione sul dataset reale:

```text
test_expected_relations_are_discovered
test_discovered_relations_build_expected_graph
test_discovered_graph_preserves_partial_order
```

---

## 16. Risultati dimostrati

Il progetto dimostra attualmente:

- caricamento del dataset Order Management in formato OCEL 2.0;
- esplorazione di eventi, oggetti e relazioni;
- identificazione del rischio introdotto dagli oggetti condivisi;
- discovery preliminare di una OCPN con PM4Py;
- implementazione di un modello dati interno indipendente da PM4Py;
- costruzione dell’Instance Graph sul toy example;
- equivalenza di due linearizzazioni temporali del toy example;
- estrazione riproducibile di una execution reale centrata su `o-990424`;
- conversione della execution nel modello interno;
- costruzione del grafo reale con causal relations manuali;
- costruzione del grafo reale con causal relations automatiche;
- scoring delle relazioni dell’OC-DFG;
- filtraggio mediante dependency e supporto relativo;
- sensitivity analysis delle soglie;
- selezione di 22 causal relations complessive;
- applicazione di 10 relazioni al caso reale;
- ottenimento della topologia esatta di 6 archi;
- assenza di archi attesi mancanti;
- assenza di archi aggiuntivi;
- proprietà DAG;
- riduzione transitiva verificata;
- conservazione della raggiungibilità;
- identificazione di 8 coppie incomparabili;
- annotazione degli archi con tipi e identificatori degli oggetti;
- generazione automatica della figura;
- esecuzione completa del notebook 05 senza errori;
- superamento di 22 test automatici.

---

## 17. Risultati non ancora dimostrati

Il progetto non dimostra ancora:

- fitness pari a 1 della process execution reale;
- conformance checking object-centric formale;
- object-centric token-based replay completo;
- object-centric alignment;
- repairing della process execution;
- gestione generale di eventi mancanti o aggiuntivi;
- correttezza delle soglie su tutte le execution del dataset;
- correttezza su dataset differenti;
- gestione generale di attività ripetute nella stessa execution;
- disambiguazione generale di transizioni diverse con la stessa etichetta;
- derivazione delle causal relations direttamente dalla semantica della OCPN;
- equivalenza generale tra OC-DFG filtrato e causalità del modello;
- identificazione certa del parallelismo reale a partire dalla sola incomparabilità;
- robustezza generale rispetto a loop complessi;
- scalabilità su tutte le process execution del log.

La corrispondenza esatta ottenuta su `o-990424` costituisce una verifica sperimentale sul caso di studio, non una dimostrazione universale.

---

## 18. Prossimi passi

Il prossimo blocco dovrebbe concentrarsi sulla generalizzazione e sulla verifica formale.

### 18.1 Analisi di più process execution

Selezionare ulteriori ordini con caratteristiche differenti:

- execution lineari;
- più item;
- più package;
- `failed delivery`;
- `payment reminder`;
- `item out of stock`;
- `reorder item`;
- attività ripetute;
- loop;
- durate differenti.

Per ogni execution sarà necessario verificare:

- numero di eventi;
- numero di oggetti;
- relazioni automatiche applicabili;
- proprietà DAG;
- archi transitivi;
- coppie incomparabili;
- stabilità rispetto alle soglie;
- eventuali archi aggiuntivi o mancanti.

### 18.2 Separazione tra calibrazione e valutazione

Le soglie `0.90 / 0.05` sono state verificate rispetto a `o-990424`.

Per evitare una validazione circolare, le prossime execution dovrebbero essere utilizzate come casi di valutazione separati.

Una possibile procedura è:

1. mantenere fisse le soglie scelte;
2. applicarle a nuove execution;
3. analizzare gli errori senza modificare immediatamente le soglie;
4. documentare precisione, copertura e stabilità;
5. modificare la configurazione solo dopo avere raccolto più evidenze.

### 18.3 Conformance checking

Dovrà essere studiata la disponibilità in PM4Py o in altri strumenti di:

- token-based replay object-centric;
- fitness per tipo di oggetto;
- diagnostics della OCPN;
- alignment object-centric;
- verifica della riproducibilità della execution.

Solo dopo questa fase sarà possibile sostenere formalmente che la process execution analizzata è conforme al modello.

### 18.4 Loop e attività ripetute

L’attuale algoritmo applica una relazione tra attività agli eventi successivi appartenenti allo stesso ciclo di vita dell’oggetto.

In presenza di attività ripetute sarà necessario distinguere:

- dipendenza tra etichette di attività;
- dipendenza tra specifiche occorrenze degli eventi;
- archi dovuti a loop;
- archi transitivi;
- relazioni reciproche osservate;
- concorrenza reale;
- rumore statistico.

### 18.5 Confronto tra sorgenti causali

Un’estensione utile sarà confrontare:

- causal relations manuali;
- relazioni inferite dall’OC-DFG;
- relazioni estratte dalla struttura della OCPN;
- relazioni ottenute tramite replay o alignment.

Il confronto dovrà chiarire quali relazioni descrivono:

- comportamento osservato nel log;
- comportamento consentito dal modello;
- causalità locale;
- raggiungibilità;
- ordine diretto;
- ordine transitivo.

---

## 19. Riproducibilità

Prima di effettuare un commit è consigliato eseguire:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_discovered.py
```

```powershell
git status --short
```

```powershell
git diff --check
```

Su Windows può comparire un avviso simile a:

```text
LF will be replaced by CRLF
```

Questo avviso dipende dalla configurazione delle terminazioni di riga di Git e non indica necessariamente un errore nel contenuto.

È comunque opportuno controllare che `git diff --check` non segnali:

- trailing whitespace;
- spazi prima delle tabulazioni;
- conflict marker;
- errori reali di formattazione.

---

## 20. Riferimenti

- W. M. P. van der Aalst e A. Berti,
  *Discovering Object-Centric Petri Nets*,
  Fundamenta Informaticae, 175(1–4), 2020.

- J. T. S. Ribeiro, J. Carmona, M. La Rosa e W. M. P. van der Aalst,
  riferimenti generali su process mining, modelli di processo e conformance checking.

- A. J. M. M. Weijters, W. M. P. van der Aalst e A. K. Alves de Medeiros,
  *Process Mining with the HeuristicsMiner Algorithm*,
  Eindhoven University of Technology, 2006.

- PM4Py — Process Mining for Python:
  https://processintelligence.solutions/pm4py

- PM4Py source code, DFG filtering e dependency threshold:
  https://github.com/process-intelligence-solutions/pm4py/blob/release/pm4py/algo/filtering/dfg/dfg_filtering.py

- NetworkX documentation, directed acyclic graphs e transitive reduction:
  https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html


---

## Autori

**Nicolò Ianni**
**Danilo La Palombara**