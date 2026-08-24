from itertools import combinations

import networkx as nx
import pm4py

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.discovery import (
    DEFAULT_DEPENDENCY_THRESHOLD,
    DEFAULT_RELATIVE_SUPPORT_THRESHOLD,
    DEFAULT_SELF_LOOP_THRESHOLD,
    derive_causal_relations,
)
from ocpm_partial_order.extraction import (
    extract_order_centred_execution,
)
from ocpm_partial_order.graphs.concurrency import (
    find_incomparable_event_pairs,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


ORDER_IDS = (
    "o-990424",
    "o-991749",
    "o-990878",
    "o-991284",
    "o-990387",
    "o-990916",
    "o-991630",
    "o-991982",
    "o-990077",
    "o-991686",
    "o-991144",
    "o-991324",
    "o-991520",
    "o-991925",
    "o-990241",
    "o-990566",
    "o-990006",
    "o-990046",
    "o-990013",
    "o-990254",
    "o-990004",
    "o-990042",
)

STRUCTURAL_TYPES = {
    "orders",
    "items",
    "packages",
}

EXCEPTION_ACTIVITIES = {
    "item out of stock",
    "reorder item",
    "payment reminder",
    "failed delivery",
}


def structural_objects(event) -> set[
    tuple[str, str]
]:
    """
    Restituisce soltanto gli oggetti che definiscono
    la struttura della process execution.

    Products ed employees vengono conservati negli
    eventi, ma non vengono usati per imporre un ordine.
    """
    return {
        (
            reference.object_type,
            reference.object_id,
        )
        for reference in event.objects
        if reference.object_type
        in STRUCTURAL_TYPES
    }


def find_suspicious_repetitions(
    execution,
    graph: nx.DiGraph,
) -> list[
    tuple[
        str,
        str,
        str,
        set[tuple[str, str]],
    ]
]:
    """
    Cerca coppie di eventi con la stessa attività e
    almeno un oggetto strutturale condiviso che siano
    rimaste incomparabili nel grafo.

    Dopo l'introduzione dei self-loop, una situazione
    del genere richiede un controllo manuale.
    """
    suspicious = []

    for first, second in combinations(
        execution.events,
        2,
    ):
        if first.activity != second.activity:
            continue

        shared_objects = (
            structural_objects(first)
            & structural_objects(second)
        )

        if not shared_objects:
            continue

        first_before_second = nx.has_path(
            graph,
            first.event_id,
            second.event_id,
        )
        second_before_first = nx.has_path(
            graph,
            second.event_id,
            first.event_id,
        )

        if (
            not first_before_second
            and not second_before_first
        ):
            suspicious.append(
                (
                    first.activity,
                    first.event_id,
                    second.event_id,
                    shared_objects,
                )
            )

    return suspicious


def failed_delivery_chain(
    graph: nx.DiGraph,
) -> list[str]:
    """
    Restituisce gli eventi failed delivery ordinati
    temporalmente.
    """
    return sorted(
        (
            node
            for node, attributes
            in graph.nodes(data=True)
            if attributes["activity"]
            == "failed delivery"
        ),
        key=lambda node: (
            graph.nodes[node]["timestamp"],
            node,
        ),
    )


def main() -> None:
    print("Caricamento OCEL")
    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    print("Discovery OC-DFG")
    ocdfg = pm4py.discover_ocdfg(ocel)

    print("Derivazione causal relations")
    causal_relations = derive_causal_relations(
        ocdfg=ocdfg,
        dependency_threshold=(
            DEFAULT_DEPENDENCY_THRESHOLD
        ),
        relative_support_threshold=(
            DEFAULT_RELATIVE_SUPPORT_THRESHOLD
        ),
        self_loop_threshold=(
            DEFAULT_SELF_LOOP_THRESHOLD
        ),
        object_types=STRUCTURAL_TYPES,
    )

    self_relations = {
        relation
        for relation in causal_relations
        if relation.source_activity
        == relation.target_activity
    }

    print(
        "Causal relations:",
        len(causal_relations),
    )
    print(
        "Auto-relazioni:",
        len(self_relations),
    )
    print(
        "Dependency threshold:",
        DEFAULT_DEPENDENCY_THRESHOLD,
    )
    print(
        "Relative support threshold:",
        DEFAULT_RELATIVE_SUPPORT_THRESHOLD,
    )
    print(
        "Self-loop threshold:",
        DEFAULT_SELF_LOOP_THRESHOLD,
    )

    print("\n" + "=" * 72)
    print("SCREENING DELLE PROCESS EXECUTION")
    print("=" * 72)

    successful = 0
    failures = []
    suspicious_total = []
    graphs = {}

    for order_id in ORDER_IDS:
        try:
            execution = (
                extract_order_centred_execution(
                    ocel=ocel,
                    order_id=order_id,
                )
            )

            graph = build_instance_graph(
                execution=execution,
                causal_relations=(
                    causal_relations
                ),
            )

            graphs[order_id] = graph

            is_dag = (
                nx.is_directed_acyclic_graph(
                    graph
                )
            )

            weakly_connected = (
                graph.number_of_nodes() > 0
                and nx.is_weakly_connected(
                    graph
                )
            )

            covered_nodes = {
                node
                for node in graph.nodes
                if (
                    graph.in_degree(node)
                    + graph.out_degree(node)
                ) > 0
            }

            isolated_nodes = (
                set(graph.nodes)
                - covered_nodes
            )

            sources = [
                node
                for node in graph.nodes
                if graph.in_degree(node) == 0
            ]

            sinks = [
                node
                for node in graph.nodes
                if graph.out_degree(node) == 0
            ]

            incomparable_pairs = (
                find_incomparable_event_pairs(
                    graph
                )
            )

            repetitions = (
                find_suspicious_repetitions(
                    execution,
                    graph,
                )
            )

            suspicious_total.extend(
                (
                    order_id,
                    *repetition,
                )
                for repetition in repetitions
            )

            reduced = (
                nx.transitive_reduction(graph)
                if is_dag
                else None
            )

            transitively_reduced = (
                reduced is not None
                and set(reduced.edges)
                == set(graph.edges)
            )

            checks = {
                "DAG": is_dag,
                "connesso": weakly_connected,
                "copertura": (
                    len(covered_nodes)
                    == graph.number_of_nodes()
                ),
                "ridotto": (
                    transitively_reduced
                ),
                "ripetizioni": (
                    not repetitions
                ),
            }

            passed = all(checks.values())

            if passed:
                successful += 1
            else:
                failures.append(
                    (
                        order_id,
                        checks,
                    )
                )

            activities = {
                event.activity
                for event in execution.events
            }

            exceptions = sorted(
                activities
                & EXCEPTION_ACTIVITIES
            )

            print("\n" + "-" * 72)
            print("Ordine:", order_id)
            print(
                "Eventi:",
                graph.number_of_nodes(),
            )
            print(
                "Archi:",
                graph.number_of_edges(),
            )
            print("DAG:", is_dag)
            print(
                "Connesso debolmente:",
                weakly_connected,
            )
            print(
                "Copertura:",
                f"{len(covered_nodes)}/"
                f"{graph.number_of_nodes()}",
            )
            print(
                "Transitivamente ridotto:",
                transitively_reduced,
            )
            print(
                "Coppie incomparabili:",
                len(incomparable_pairs),
            )
            print("Sorgenti:", len(sources))
            print("Pozzi:", len(sinks))
            print(
                "Eventi isolati:",
                (
                    sorted(isolated_nodes)
                    if isolated_nodes
                    else "nessuno"
                ),
            )
            print(
                "Eccezioni:",
                (
                    exceptions
                    if exceptions
                    else "nessuna"
                ),
            )
            print(
                "Ripetizioni sospette:",
                (
                    len(repetitions)
                    if repetitions
                    else "nessuna"
                ),
            )
            print(
                "Esito:",
                (
                    "SUPERATO"
                    if passed
                    else "DA CONTROLLARE"
                ),
            )

        except Exception as error:
            failures.append(
                (
                    order_id,
                    {
                        "errore": (
                            f"{type(error).__name__}: "
                            f"{error}"
                        )
                    },
                )
            )

            print("\n" + "-" * 72)
            print("Ordine:", order_id)
            print(
                "ERRORE:",
                type(error).__name__,
                "-",
                error,
            )

    print("\n" + "=" * 72)
    print("CONTROLLO DEI LOOP PRINCIPALI")
    print("=" * 72)

    for order_id in (
        "o-990254",
        "o-990042",
    ):
        graph = graphs.get(order_id)

        if graph is None:
            continue

        failed_nodes = (
            failed_delivery_chain(graph)
        )

        expected_edges = set(
            zip(
                failed_nodes,
                failed_nodes[1:],
            )
        )

        actual_edges = {
            (source, target)
            for source, target in graph.edges
            if source in failed_nodes
            and target in failed_nodes
        }

        print("\nOrdine:", order_id)
        print(
            "Failed delivery:",
            len(failed_nodes),
        )
        print(
            "Archi consecutivi attesi:",
            len(expected_edges),
        )
        print(
            "Archi consecutivi trovati:",
            len(
                expected_edges
                & actual_edges
            ),
        )
        print(
            "Catena completa:",
            actual_edges
            == expected_edges,
        )

        for source, target in sorted(
            actual_edges,
            key=lambda edge: (
                graph.nodes[
                    edge[0]
                ]["timestamp"],
                graph.nodes[
                    edge[1]
                ]["timestamp"],
            ),
        ):
            print(
                f"- {source} -> {target}"
            )

    print("\n" + "=" * 72)
    print("RIEPILOGO")
    print("=" * 72)
    print(
        "Execution previste:",
        len(ORDER_IDS),
    )
    print(
        "Execution superate:",
        successful,
    )
    print(
        "Execution fallite:",
        len(failures),
    )
    print(
        "Ripetizioni sospette:",
        len(suspicious_total),
    )

    if failures:
        print("\nDETTAGLIO PROBLEMI")

        for order_id, details in failures:
            print(
                f"- {order_id}: {details}"
            )

        raise AssertionError(
            "Almeno una process execution "
            "non ha superato lo screening"
        )

    if suspicious_total:
        print("\nRIPETIZIONI SOSPETTE")

        for item in suspicious_total:
            print("-", item)

        raise AssertionError(
            "Sono presenti attività ripetute "
            "incomparabili sullo stesso oggetto"
        )

    assert len(causal_relations) == 26
    assert len(self_relations) == 4
    assert successful == len(ORDER_IDS)

    print(
        "\nSCREENING COMPLETO SUPERATO"
    )


if __name__ == "__main__":
    main()