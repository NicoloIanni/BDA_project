# OCPM Partial Order - Order Management Prototype

Prototipo universitario per la costruzione di **Instance Graph object-centric a ordine parziale** a partire da process execution estratte da un log OCEL 2.0 e da relazioni causali esplicite.

Il progetto è sviluppato da **Nicolò Ianni** e **Danilo La Palombara** nell'ambito di Big Data Analytics / Object-Centric Process Mining.

> **Stato verificato:** l'ambiente, l'esplorazione del dataset, la discovery preliminare della Object-Centric Petri Net, il toy example e una prima applicazione a una process execution reale sono completati. Per l'ordine reale `o-990424` è stato costruito un Instance Graph di 7 nodi e 6 archi, verificato come DAG e transitivamente ridotto. Le causal relations sono ancora definite manualmente; non è stato ancora eseguito conformance checking object-centric e non è stata dimostrata una fitness pari a 1.

## 1. Obiettivo

Nel process mining tradizionale gli eventi vengono normalmente raccolti in tracce usando un singolo `case_id`. Questa rappresentazione è limitante per processi nei quali uno stesso evento riguarda più entità: per esempio un ordine, uno o più articoli, un pacco e un dipendente.

L'Object-Centric Process Mining evita di scegliere in anticipo un unico case identifier e mantiene i collegamenti tra eventi e oggetti di tipi diversi. Questo progetto adatta a tale contesto il concetto di **Instance Graph**: un grafo diretto nel quale:

- ogni nodo rappresenta un evento della process execution;
- ogni arco rappresenta una dipendenza causale ammessa;
- eventi senza un ordine causale imposto restano incomparabili;
- la riduzione transitiva elimina gli archi ridondanti senza modificare la raggiungibilità.

L'obiettivo non è ricostruire una sequenza cronologica più elegante. L'obiettivo è evitare che il timestamp imponga un ordine totale artificiale a eventi che il modello causale consente di considerare indipendenti.

La pipeline concettuale è:

```text
OCEL 2.0 Order Management
        |
        +--> esplorazione del log
        |
        +--> discovery preliminare OCPN
        |
        +--> estrazione order-centred di una process execution
                    |
                    +--> adapter verso il modello interno
                    |
causal relations manuali
                    |
                    v
         Instance Graph object-centric
                    |
                    +--> controllo DAG
                    +--> riduzione transitiva
                    +--> eventi incomparabili
```

Le quattro attività seguenti devono rimanere distinte:

1. **discovery:** ricavare un modello dal log;
2. **estrazione:** delimitare una process execution nel log object-centric;
3. **costruzione dell'Instance Graph:** applicare relazioni causali agli eventi estratti;
4. **conformance checking:** verificare se l'execution è riproducibile dal modello.

Completare una fase non dimostra automaticamente le altre.

## 2. Semplificazioni metodologiche

La prima iterazione del progetto assume volutamente che:

- la process execution da analizzare sia già disponibile;
- le causal relations siano fornite in ingresso;
- non siano necessari repairing, inserimenti o cancellazioni di eventi;
- non vengano ancora calcolati object-centric alignment;
- l'algoritmo dell'Instance Graph resti indipendente dal metodo di estrazione;
- il modello interno non dipenda dalle classi private di PM4Py o OCPA.

Nel Blocco 04 l'estrazione della execution reale è stata automatizzata, ma le causal relations non sono state ricavate automaticamente dalla OCPN. La distinzione è sostanziale: il grafo usa dati reali, ma incorpora ancora un'ipotesi causale manuale.

## 3. Dataset Order Management

Il dataset ufficiale del progetto è **Order Management**, memorizzato localmente in formato OCEL 2.0 SQLite:

```text
data/raw/order_management.sqlite
```

Il file non è versionato e deve essere copiato manualmente nella cartella indicata.

L'esplorazione eseguita nel notebook `02_ocel_exploration.ipynb` ha prodotto:

| Misura | Valore |
| --- | ---: |
| Eventi | 21.008 |
| Oggetti | 10.825 |
| Relazioni evento-oggetto | 143.463 |
| Attività | 11 |
| Tipi di oggetto | 5 |

I tipi di oggetto sono:

- `orders`;
- `items`;
- `packages`;
- `products`;
- `employees`.

Tutti i 21.008 eventi sono collegati a più oggetti e coinvolgono più tipi di oggetto; un singolo evento può essere associato fino a 37 oggetti. Il log contiene soltanto 20 prodotti e 18 dipendenti, riutilizzati in molti ordini.

Questa struttura rende pericolosa un'espansione indiscriminata per connected components: `products` ed `employees` possono comportarsi come ponti e unire esecuzioni di ordini altrimenti distinti. Per il primo caso reale è stata quindi adottata un'estrazione **order-centred**, descritta nel Blocco 04.

## 4. Stato dei blocchi

### Blocco 01 - Ambiente

L'ambiente è stato configurato e verificato su Windows con Python 3.12 e virtual environment locale.

Versioni principali verificate:

- PM4Py 2.7.23.3;
- pandas 3.0.5;
- NetworkX 3.6.1;
- Matplotlib 3.11.1;
- Graphviz Python package 0.21;
- pytest 9.1.1;
- Jupyter e ipykernel.

### Blocco 02 - Esplorazione OCEL

Il notebook `02_ocel_exploration.ipynb`:

- carica il file SQLite OCEL 2.0;
- analizza eventi, oggetti e relazioni evento-oggetto;
- conta attività e tipi di oggetto;
- misura il numero di oggetti associati agli eventi;
- documenta il rischio di una connected component unica o molto grande.

Il risultato guida la scelta di estrazione ma non modifica la logica dell'Instance Graph.

### Blocco 03 - Discovery OCPN

Il notebook `03_ocpn_discovery.ipynb` usa PM4Py per effettuare una discovery preliminare della Object-Centric Petri Net. Il risultato comprende:

- 11 attività;
- 5 tipi di oggetto;
- una Petri net per ciascun tipo di oggetto;
- informazioni su archi, attività iniziali e finali, molteplicità e prestazioni.

Il notebook è stato eseguito integralmente senza errori.

Questa fase dimostra la **discovery del modello**, non la conformità delle execution. In particolare, `tbr_results` è vuoto: non è stata calcolata né dimostrata una fitness pari a 1.

### Prototipo preliminare - Toy example

Prima di usare il dataset reale è stata verificata la pipeline su una execution sintetica controllata:

- 7 eventi;
- 6 causal relations manuali;
- costruzione dell'Instance Graph;
- controllo DAG;
- riduzione transitiva;
- ricerca delle coppie incomparabili;
- generazione PNG con Graphviz;
- confronto tra due linearizzazioni temporali equivalenti.

Il test centrale dimostra che l'inversione temporale di due eventi appartenenti a rami indipendenti produce lo stesso grafo causale. Tale risultato vale per il toy example e non costituisce una dimostrazione generale su tutto il dataset.

### Blocco 04 - Instance Graph su execution reale

Il Blocco 04 applica la pipeline all'ordine reale `o-990424`.

#### 4.1 Selezione order-centred

L'estrazione segue questo criterio:

1. seleziona `o-990424` come leading object;
2. individua gli `items` collegati all'ordine;
3. individua i `packages` collegati agli item;
4. seleziona gli eventi appartenenti a questa porzione del processo;
5. conserva, per ogni evento, i riferimenti agli oggetti coinvolti.

`products` ed `employees` non vengono usati per espandere la execution perché sono oggetti condivisi trasversalmente e collegherebbero ordini differenti. Non vengono rimossi dal dataset: vengono esclusi soltanto dalla regola di espansione del caso.

La funzione pubblica usata dal notebook è:

```python
extract_order_centred_execution(
    ocel=ocel,
    order_id="o-990424",
)
```

L'adapter converte gli eventi OCEL selezionati nel modello interno `ProcessExecution`, lasciando separati il codice di estrazione e quello di costruzione del grafo.

#### 4.2 Causal relations

Le sei relazioni del prototipo reale sono caricate da:

```text
data/derived/order_management_o_990424_causal_relations.json
```

Ogni relazione specifica:

- attività sorgente;
- attività destinazione;
- tipo di oggetto che giustifica il collegamento.

Le relazioni sono manuali. Non sono state estratte dalla OCPN scoperta nel Blocco 03 e non costituiscono un risultato di conformance checking.

#### 4.3 Risultato verificato

Per l'ordine `o-990424` sono stati ottenuti:

| Proprietà | Risultato |
| --- | ---: |
| Eventi / nodi | 7 |
| Archi causali | 6 |
| Grafo diretto aciclico | sì |
| Grafo già transitivamente ridotto | sì |
| Coppie incomparabili | 8 |

Il grafo contiene due rami dopo `place order`:

```text
                 confirm order -> pay order
                /
place order ---
                \
                 pick item -> create package -> send package -> package delivered
```

Gli archi verificati sono:

| Sorgente | Destinazione | Tipo di oggetto |
| --- | --- | --- |
| `place order` | `confirm order` | `orders` |
| `confirm order` | `pay order` | `orders` |
| `place order` | `pick item` | `items` |
| `pick item` | `create package` | `items` |
| `create package` | `send package` | `packages` |
| `send package` | `package delivered` | `packages` |

I due eventi del ramo ordine sono incomparabili con i quattro eventi del ramo logistico: `2 x 4 = 8` coppie.

`pay order` possiede un timestamp successivo a `package delivered`, ma nel grafo non compare l'arco `package delivered -> pay order`. Il timestamp stabilisce una successione osservata; da solo non dimostra una dipendenza causale.

#### 4.4 Verifiche effettuate

Il notebook `04_real_instance_graph.ipynb` è stato eseguito interamente con `nbconvert`:

```text
Celle totali: 21
Celle di codice: 9
Celle eseguite: 9
Errori: 0
```

Le asserzioni del notebook verificano:

- l'insieme esatto dei 7 nodi;
- l'insieme esatto dei 6 archi;
- l'assenza di cicli;
- l'uguaglianza tra il grafo e la sua riduzione transitiva;
- la conservazione della chiusura transitiva;
- le 8 coppie incomparabili attese.

La figura viene generata in:

```text
outputs/graphs/order_management_o_990424_instance_graph.png
```

## 5. Struttura del repository

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
|-- notebooks/
|   |-- 01_environment_check.ipynb
|   |-- 02_ocel_exploration.ipynb
|   |-- 03_ocpn_discovery.ipynb
|   `-- 04_real_instance_graph.ipynb
|-- outputs/
|   |-- figures/
|   |-- graphs/
|   |   |-- order_management_toy_instance_graph.png
|   |   `-- order_management_o_990424_instance_graph.png
|   |-- reports/
|   `-- tables/
|-- scripts/
|   |-- check_environment.py
|   |-- inspect_ocel.py
|   |-- inspect_order_candidates.py
|   |-- run_order_management_toy.py
|   |-- run_order_management_real.py
|   `-- verify_real_execution.py
|-- src/ocpm_partial_order/
|   |-- config.py
|   |-- discovery/
|   |   `-- ocpn_discovery.py
|   |-- domain/
|   |   |-- causal_relation.py
|   |   |-- event.py
|   |   `-- process_execution.py
|   |-- extraction/
|   |   `-- execution_adapter.py
|   |-- graphs/
|   |   |-- concurrency.py
|   |   |-- instance_graph.py
|   |   `-- validation.py
|   |-- io/
|   |   |-- ocel_loader.py
|   |   `-- sample_loader.py
|   `-- visualization/
|       `-- graph_visualizer.py
|-- tests/
|   |-- fixtures/
|   |-- test_concurrency.py
|   |-- test_equivalent_linearizations.py
|   |-- test_execution_adapter.py
|   |-- test_instance_graph.py
|   |-- test_real_instance_graph.py
|   `-- test_sample_loader.py
|-- .gitignore
|-- pyproject.toml
|-- requirements.txt
`-- README.md
```

Gli artefatti in `outputs/` sono rigenerabili e possono essere esclusi dal versionamento. Il dataset in `data/raw/` resta locale. Il file in `data/derived/` è invece un input esplicito del prototipo reale e deve essere valutato come parte del codice riproducibile.

## 6. Modello dati interno

L'algoritmo non usa direttamente le rappresentazioni interne di PM4Py o OCPA.

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

Contiene gli eventi di una execution e offre metodi per ottenere:

- gli ID degli eventi;
- gli oggetti coinvolti;
- gli eventi associati a un oggetto specifico.

### `CausalRelation`

Descrive una relazione causale ammessa per uno specifico tipo di oggetto:

- `source_activity`;
- `target_activity`;
- `object_type`.

Questa separazione permette di cambiare dataset, libreria o tecnica di estrazione senza riscrivere la logica centrale del grafo.

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
6. aggiunge un arco quando la coppia di attività è ammessa e i due eventi condividono un oggetto del tipo richiesto;
7. annota l'arco con `object_types` e `object_ids`;
8. verifica che il grafo sia un DAG;
9. applica la riduzione transitiva;
10. ripristina nel grafo ridotto gli attributi di nodi e archi.

NetworkX definisce la riduzione transitiva per un DAG come il grafo che conserva la raggiungibilità eliminando gli archi per i quali esiste già un cammino alternativo più lungo.

## 8. Incomparabilità e parallelismo potenziale

La funzione:

```python
find_incomparable_event_pairs(graph)
```

considera due eventi incomparabili quando non esiste:

- né un cammino dal primo al secondo;
- né un cammino dal secondo al primo.

Nel progetto viene adottata la formulazione prudente:

```text
incomparabilità = candidato al parallelismo
```

L'incomparabilità non dimostra che due eventi siano avvenuti simultaneamente. Dimostra soltanto che il grafo costruito non impone un ordine causale tra loro. Anche le dispense del corso distinguono il parallelismo nel modello dalla coincidenza temporale nell'esecuzione.

## 9. Installazione su Windows

### Prerequisiti

- Python 3.12;
- Git;
- Graphviz installato nel sistema;
- comando `dot` disponibile nel `PATH`.

Verifica di Graphviz:

```powershell
dot -V
```

### Ambiente virtuale

Da PowerShell, nella root del progetto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install -e .
```

L'interprete della `.venv` viene richiamato esplicitamente per evitare di usare per errore il Python globale di Windows.

### Dataset reale

Copiare il file OCEL 2.0 SQLite in:

```text
data/raw/order_management.sqlite
```

## 10. Esecuzione

### Controllo ambiente

```powershell
.\.venv\Scripts\python.exe .\scripts\check_environment.py
```

### Toy Instance Graph

```powershell
.\.venv\Scripts\python.exe .\scripts\run_order_management_toy.py
```

### Execution reale

Gli script di supporto permettono di ispezionare i candidati, verificare l'estrazione e riprodurre il caso reale:

```powershell
.\.venv\Scripts\python.exe .\scripts\inspect_order_candidates.py
.\.venv\Scripts\python.exe .\scripts\verify_real_execution.py
.\.venv\Scripts\python.exe .\scripts\run_order_management_real.py
```

### Notebook

```powershell
.\.venv\Scripts\python.exe -m jupyter lab
```

Eseguire i notebook nell'ordine `01`, `02`, `03`, `04`.

Esecuzione non interattiva del Blocco 04:

```powershell
.\.venv\Scripts\python.exe -m jupyter nbconvert `
    --to notebook `
    --execute `
    --inplace `
    --ExecutePreprocessor.timeout=300 `
    .\notebooks\04_real_instance_graph.ipynb
```

## 11. Test automatici

Esecuzione completa:

```powershell
.\.venv\Scripts\python.exe -m pytest -q
```

Risultato verificato dopo il Blocco 04:

```text
............ [100%]
12 passed
```

La suite copre:

| Area | Verifica |
| --- | --- |
| caricamento | parsing della toy execution e delle causal relations |
| grafo | nodi, archi, DAG e riduzione transitiva |
| incomparabilità | eventi appartenenti a rami causali distinti |
| linearizzazioni | stesso grafo per ordini temporali equivalenti |
| adapter | conversione della execution OCEL nel modello interno |
| caso reale | eventi, archi e proprietà attese per `o-990424` |

Il comando `git diff --check` è stato eseguito senza errori. Gli avvisi `LF will be replaced by CRLF` dipendono dalla configurazione Git su Windows e non indicano errori di contenuto o whitespace.

## 12. Risultati dimostrati e non dimostrati

### Dimostrato

- caricamento ed esplorazione del dataset Order Management;
- discovery preliminare di una OCPN;
- algoritmo Instance Graph verificato sul toy example;
- equivalenza di due linearizzazioni temporali del toy example;
- estrazione riproducibile di una execution reale centrata su `o-990424`;
- conversione nel modello dati interno;
- grafo reale con 7 nodi e 6 archi;
- proprietà DAG;
- riduzione transitiva verificata;
- 8 coppie incomparabili;
- notebook 04 eseguito senza errori;
- 12 test automatici superati.

### Non dimostrato

- fitness pari a 1 della execution reale;
- conformance checking object-centric;
- derivazione automatica delle causal relations dalla OCPN;
- correttezza generale per loop e attività ripetute;
- repairing di execution non conformi;
- object-centric alignment;
- applicabilità sistematica a tutte le execution del dataset;
- scalabilità su grafi molto grandi.

La conclusione corretta è quindi: **il prototipo funziona su un caso reale piccolo e controllato sotto causal relations manuali**. Dire che il metodo object-centric completo è già risolto sarebbe falso.

## 13. Prossimo blocco

Il Blocco 05 dovrà ridurre la dipendenza dalle ipotesi manuali, studiando come ottenere o validare le causal relations usando la OCPN scoperta nel Blocco 03.

Obiettivi immediati:

1. ispezionare le Petri net per tipo di oggetto restituite da PM4Py;
2. chiarire come tradurre le relazioni del modello in dipendenze tra eventi;
3. gestire con prudenza loop e attività ripetute;
4. confrontare le relazioni derivate con le sei relazioni manuali del caso `o-990424`;
5. mantenere separati discovery, conformance ed estrazione.

Il conformance checking e la verifica della fitness restano previsti per un blocco successivo: anticiparli nominalmente senza implementarli non aggiungerebbe alcuna validità al progetto.

## 14. Ripartizione del lavoro

Il progetto è sviluppato da due persone. Per il Blocco 05 la divisione proposta è:

| Nicolò Ianni | Danilo La Palombara |
| --- | --- |
| ispezione della struttura OCPN restituita da PM4Py | studio delle causal relations nel paper e nella OCPN |
| prototipo di estrazione delle dipendenze | casi limite con loop e attività ripetute |
| integrazione con il caso `o-990424` | verifica indipendente degli archi ottenuti |

Entrambi revisionano algoritmo, test, notebook e conclusioni prima di considerare chiuso il blocco.

## 15. Riferimenti

- C. Diamantini, L. Genga, D. Potena, W. M. P. van der Aalst, *Building Instance Graphs for Highly Variable Processes*, Expert Systems with Applications, 59, 101-118, 2016. [DOI: 10.1016/j.eswa.2016.04.021](https://doi.org/10.1016/j.eswa.2016.04.021).
- J. N. Adams, D. Schuster, S. Schmitz, G. Schuh, W. M. P. van der Aalst, *Defining Cases and Variants for Object-Centric Event Data*, ICPM 2022, 128-135. [DOI: 10.1109/ICPM57379.2022.9980730](https://doi.org/10.1109/ICPM57379.2022.9980730).
- [OCEL 2.0 - specifica ufficiale](https://www.ocel-standard.org/specification/overview/).
- [PM4Py - funzionalità e supporto Object-Centric Process Mining](https://processintelligence.solutions/pm4py/features).
- [NetworkX - `transitive_reduction`](https://networkx.org/documentation/stable/reference/algorithms/generated/networkx.algorithms.dag.transitive_reduction.html).
- [Graphviz - documentazione ufficiale](https://graphviz.org/documentation/).

## Autori

- Nicolò Ianni
- Danilo La Palombara
