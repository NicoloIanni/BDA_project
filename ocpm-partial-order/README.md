# OCPM Partial Order — Order Management Prototype

Prototipo universitario per la costruzione di **Instance Graph object-centric a ordine parziale** a partire da una process execution e da relazioni causali note.

Il progetto è sviluppato da **Nicolò Ianni** e **Danilo La Palombara** nell'ambito di Big Data Analytics / Object-Centric Process Mining.

> **Stato del progetto:** l'esplorazione del dataset reale e la discovery preliminare della Object-Centric Petri Net sono state completate. L'algoritmo di costruzione dell'Instance Graph è stato validato su un toy example controllato. Non è ancora stato applicato automaticamente a una process execution reale e non è stato ancora eseguito conformance checking object-centric.

## 1. Obiettivo

Nel process mining tradizionale gli eventi sono spesso organizzati in tracce mediante un singolo case identifier. Questa rappresentazione è limitante nei processi object-centric, nei quali lo stesso evento può coinvolgere contemporaneamente oggetti differenti, per esempio un ordine, più articoli, un pacco e un dipendente.

Il progetto adatta il concetto di **Instance Graph** al contesto object-centric. Il risultato atteso è un grafo diretto aciclico (DAG) che rappresenti le dipendenze causali tra gli eventi senza imporre un ordine totale artificiale agli eventi che non risultano confrontabili.

La pipeline concettuale è:

```text
OCEL 2.0
    ↓
Object-Centric Petri Net
    ↓
process execution conforme + causal relations note
    ↓
algoritmo sviluppato nel progetto
    ↓
Instance Graph object-centric / ordine parziale
```

La prima iterazione adotta volutamente queste semplificazioni:

- la process execution è già disponibile ed è considerata conforme;
- le causal relations sono fornite in ingresso;
- non sono gestiti repairing, inserimenti o cancellazioni di eventi;
- non sono implementati object-centric alignment;
- l'algoritmo rimane separato dalla tecnica usata per estrarre la process execution.

## 2. Dataset

Il dataset reale ufficiale è **Order Management**, memorizzato localmente in formato OCEL 2.0 SQLite:

```text
data/raw/order_management.sqlite
```

Il file non è incluso nel repository. Deve essere copiato manualmente nella cartella indicata prima di eseguire i notebook che lavorano sul log reale.

L'esplorazione effettuata nel notebook `02_ocel_exploration.ipynb` ha prodotto i seguenti risultati:

| Misura | Valore |
| --- | ---: |
| Eventi | 21.008 |
| Oggetti | 10.825 |
| Relazioni evento-oggetto | 143.463 |
| Attività | 11 |
| Tipi di oggetto | 5 |

I tipi di oggetto rilevati sono:

- `orders`;
- `items`;
- `packages`;
- `products`;
- `employees`.

Tutti i 21.008 eventi sono associati a più oggetti e coinvolgono più tipi di oggetto; un evento può essere collegato fino a 37 oggetti. Il dataset contiene inoltre soltanto 20 prodotti e 18 dipendenti, riutilizzati trasversalmente. Per questo `products` ed `employees` possono agire da ponti tra ordini diversi e produrre una connected component molto grande o unica.

L'estrazione delle process execution dovrà quindi essere affrontata separatamente dall'algoritmo, confrontando criteri come connected components e leading object type senza vincolare il modello interno a una singola scelta.

## 3. Stato verificato

### Blocco 01 — Ambiente

L'ambiente è stato configurato e verificato su Windows con Python 3.12 e virtual environment locale.

Componenti principali verificati:

- PM4Py 2.7.23.3;
- pandas 3.0.5;
- NetworkX 3.6.1;
- Matplotlib 3.11.1;
- Graphviz Python package 0.21;
- pytest 9.1.1;
- Jupyter e ipykernel.

### Blocco 02 — Esplorazione OCEL

Il notebook `02_ocel_exploration.ipynb` carica il dataset reale, ne analizza eventi, oggetti e relazioni e documenta il rischio di ottenere un'unica process execution quando tipi di oggetto fortemente condivisi vengono usati indiscriminatamente nella costruzione delle connected components.

### Blocco 03 — Discovery OCPN

Il notebook `03_ocpn_discovery.ipynb` esegue una discovery preliminare della Object-Centric Petri Net con PM4Py. La struttura ottenuta comprende:

- 11 attività;
- 5 tipi di oggetto;
- una Petri net associata a ciascun tipo di oggetto.

Il notebook è stato eseguito integralmente con `nbconvert` ed è terminato senza errori. Le sue 14 celle possiedono ID presenti e univoci.

Questa fase dimostra la **discovery del modello**, non la conformità delle execution. In particolare, `tbr_results` è vuoto: non è stata calcolata né dimostrata una fitness uguale a 1 e non è stato eseguito object-centric conformance checking.

### Prototipo Instance Graph — toy example

È stata implementata e verificata una prima pipeline completa su una process execution sintetica del dominio Order Management:

- modello dati interno indipendente dalle classi di PM4Py/OCPA;
- caricamento della toy execution e delle causal relations da JSON;
- costruzione dell'Instance Graph;
- verifica che il grafo sia un DAG;
- transitive reduction;
- ricerca delle coppie di eventi incomparabili;
- visualizzazione Graphviz in PNG;
- confronto tra linearizzazioni temporali equivalenti;
- cinque test automatici superati.

## 4. Struttura del repository

```text
ocpm-partial-order/
├── data/
│   ├── raw/
│   │   └── order_management.sqlite          # locale, non versionato
│   └── samples/
│       ├── order_management_toy_execution.json
│       ├── order_management_toy_execution_reordered.json
│       └── order_management_toy_causal_relations.json
├── notebooks/
│   ├── 01_environment_check.ipynb
│   ├── 02_ocel_exploration.ipynb
│   └── 03_ocpn_discovery.ipynb
├── outputs/
│   ├── figures/
│   ├── graphs/
│   │   └── order_management_toy_instance_graph.png
│   ├── reports/
│   └── tables/
├── scripts/
│   ├── check_environment.py
│   ├── inspect_ocel.py
│   └── run_order_management_toy.py
├── src/ocpm_partial_order/
│   ├── config.py
│   ├── discovery/
│   │   └── ocpn_discovery.py
│   ├── domain/
│   │   ├── causal_relation.py
│   │   ├── event.py
│   │   └── process_execution.py
│   ├── extraction/
│   │   └── execution_adapter.py
│   ├── graphs/
│   │   ├── concurrency.py
│   │   ├── instance_graph.py
│   │   └── validation.py
│   ├── io/
│   │   ├── ocel_loader.py
│   │   └── sample_loader.py
│   └── visualization/
│       └── graph_visualizer.py
├── tests/
│   ├── fixtures/
│   ├── test_concurrency.py
│   ├── test_equivalent_linearizations.py
│   ├── test_instance_graph.py
│   └── test_sample_loader.py
├── .gitignore
├── pyproject.toml
├── requirements.txt
└── README.md
```

I notebook `04`, `05` e `06` non esistono ancora e non sono rappresentati come componenti completati.

## 5. Modello dati interno

L'algoritmo non usa direttamente le rappresentazioni interne di PM4Py o OCPA. Il package definisce un modello minimo e indipendente.

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

Contiene gli eventi di una singola execution e offre metodi per ottenere:

- gli ID degli eventi;
- gli oggetti coinvolti;
- gli eventi associati a uno specifico oggetto.

### `CausalRelation`

Descrive una relazione causale ammessa per uno specifico tipo di oggetto:

- `source_activity`;
- `target_activity`;
- `object_type`.

Questa separazione permette di cambiare dataset, libreria o metodo di estrazione senza riscrivere la logica del grafo.

## 6. Toy example Order Management

La process execution sintetica contiene sette eventi:

| ID | Attività |
| --- | --- |
| `e1` | place order |
| `e2` | confirm order |
| `e3` | pay order |
| `e4` | pick item |
| `e5` | create package |
| `e6` | send package |
| `e7` | package delivered |

Le causal relations manuali producono due rami dopo `place order`:

```text
                 confirm order → pay order
                /
place order ───
                \
                 pick item → create package → send package → package delivered
```

Le relazioni sono fornite nel file:

```text
data/samples/order_management_toy_causal_relations.json
```

La loro definizione manuale è una semplificazione esplicita della prima iterazione, non il risultato di un'estrazione automatica dalla OCPN.

## 7. Costruzione dell'Instance Graph

La funzione principale è:

```python
build_instance_graph(execution, causal_relations)
```

Il procedimento implementato:

1. valida la process execution;
2. crea un nodo per ogni evento;
3. raggruppa le causal relations per tipo di oggetto;
4. ricostruisce il ciclo di vita di ciascun oggetto;
5. ordina gli eventi dell'oggetto per timestamp;
6. aggiunge un arco quando la coppia di attività è ammessa dalle causal relations;
7. annota l'arco con `object_types` e `object_ids`;
8. verifica che il grafo sia un DAG;
9. applica la transitive reduction;
10. ricopia nel grafo ridotto gli attributi di nodi e archi.

La transitive reduction rimuove gli archi ridondanti preservando la raggiungibilità tra gli eventi. Nel caso di NetworkX, l'operazione richiede un DAG.

## 8. Incomparabilità e parallelismo

La funzione:

```python
find_incomparable_event_pairs(graph)
```

considera due eventi incomparabili quando non esiste un percorso diretto né indiretto dal primo al secondo e nemmeno dal secondo al primo.

Nel progetto viene usata la formulazione prudente:

```text
incomparabilità = candidato al parallelismo
```

L'incomparabilità non dimostra da sola che due eventi siano avvenuti simultaneamente; indica che il grafo causale non impone un ordine tra essi.

Nel toy example `confirm order` e `pick item` sono incomparabili perché appartengono a due rami causali distinti.

## 9. Risultato centrale

Sono state costruite due versioni della stessa toy execution. Nella seconda versione l'ordine temporale di `confirm order` e `pick item` è invertito:

| Execution | `confirm order` | `pick item` |
| --- | --- | --- |
| Originale | 09:15 | 09:20 |
| Riordinata | 09:25 | 09:10 |

I due grafi sono confrontati mediante isomorfismo, considerando:

- `activity` come attributo del nodo;
- `object_types` come attributo dell'arco.

Il test automatico dimostra che le due linearizzazioni producono lo stesso ordine parziale:

```text
ordine temporale diverso
          ↓
stesso grafo causale
```

Questo risultato è stato verificato esclusivamente sul toy example.

## 10. Installazione su Windows

### Prerequisiti

- Python 3.12;
- Git;
- Graphviz installato nel sistema e comando `dot` disponibile nel `PATH`.

Per verificare Graphviz:

```powershell
dot -V
```

### Creazione dell'ambiente

Da PowerShell, nella directory del progetto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

L'uso esplicito di `.\.venv\Scripts\python.exe` evita di eseguire accidentalmente il Python globale di Windows.

### Dataset reale

Copiare il file OCEL 2.0 SQLite in:

```text
data/raw/order_management.sqlite
```

## 11. Esecuzione

### Controllo ambiente

```powershell
.\.venv\Scripts\python.exe .\scripts\check_environment.py
```

### Toy Instance Graph

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_toy.py
```

Il PNG viene scritto in:

```text
outputs/graphs/order_management_toy_instance_graph.png
```

### Notebook

```powershell
.\.venv\Scripts\python.exe -m jupyter lab
```

Eseguire i notebook nell'ordine `01`, `02`, `03`.

## 12. Test automatici

Esecuzione completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

Risultato verificato:

```text
collected 5 items
5 passed
```

I test coprono:

| Test | Verifica |
| --- | --- |
| `test_order_management_toy_is_loaded` | caricamento della toy execution |
| `test_instance_graph_is_dag` | il grafo costruito è un DAG |
| `test_expected_edges_exist` | presenza degli archi causali attesi |
| `test_confirm_and_pick_are_incomparable` | incomparabilità dei due eventi selezionati |
| `test_reordered_parallel_events_produce_same_graph` | equivalenza di due linearizzazioni temporali |

## 13. Limiti attuali

Il prototipo non implementa ancora:

- estrazione automatica di una process execution reale;
- selezione automatica delle execution con fitness uguale a 1;
- estrazione automatica delle causal relations dalla OCPN;
- object-centric token-based replay o alignment;
- repairing delle execution non conformi;
- gestione robusta di loop e attività ripetute;
- applicazione sistematica dell'algoritmo al dataset completo.

La discovery della OCPN non elimina questi limiti: avere un modello scoperto non equivale ad avere dimostrato la conformità di una execution.

## 14. Prossimo blocco

Il prossimo obiettivo è applicare l'algoritmo a una **process execution reale piccola e controllabile**, mantenendo l'estrazione separata dalla costruzione del grafo:

1. selezionare una execution centrata inizialmente su un ordine;
2. includere i relativi item e package;
3. convertirla nel modello dati interno;
4. verificarne manualmente la conformità rispetto alla OCPN;
5. fornire le causal relations richieste dall'algoritmo;
6. costruire l'Instance Graph reale;
7. confrontarlo con il risultato del toy example.

`products` ed `employees` devono essere trattati con cautela perché possono collegare execution altrimenti distinte. La scelta tra connected components e leading type riguarda il modulo di estrazione e non deve propagarsi nella logica dell'Instance Graph.

## 15. Ripartizione del lavoro

Il progetto è sviluppato da due persone. Una possibile divisione del prossimo blocco è:

| Nicolò Ianni | Danilo La Palombara |
| --- | --- |
| selezione e ispezione della execution reale | analisi della OCPN e delle causal relations |
| adattamento dei dati al modello interno | preparazione dei casi di test reali |
| integrazione e documentazione | verifica indipendente dei risultati |

Entrambi revisionano algoritmo, test e conclusioni prima di considerare concluso ciascun blocco.

## 16. Riferimenti

- C. Diamantini, L. Genga, D. Potena, W. M. P. van der Aalst, *Building Instance Graphs for Highly Variable Processes*, Expert Systems with Applications, 59, 101–118, 2016. DOI: [10.1016/j.eswa.2016.04.021](https://doi.org/10.1016/j.eswa.2016.04.021).
- J. N. Adams et al., *Defining Cases and Variants for Object-Centric Event Data*, International Conference on Process Mining, 2022.
- [OCEL 2.0 — sito e specifica ufficiale](https://www.ocel-standard.org/).
- [PM4Py — documentazione ufficiale](https://processintelligence.solutions/pm4py/).
- [NetworkX — `transitive_reduction`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html).
- [Graphviz — documentazione ufficiale](https://graphviz.org/documentation/).

## Autori

- Nicolò Ianni
- Danilo La Palombara
