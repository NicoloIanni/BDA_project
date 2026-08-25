from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance import (
    evaluate_instance_graph_holdout,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


def main() -> None:
    print("=" * 72)
    print(
        "VALIDAZIONE HOLDOUT END-TO-END "
        "DEGLI INSTANCE GRAPH"
    )
    print("=" * 72)

    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    evaluation = (
        evaluate_instance_graph_holdout(
            ocel
        )
    )

    split = evaluation.split

    print()
    print("SEPARAZIONE TRAINING E TEST")
    print(
        "- tipi strutturali:",
        list(split.object_types),
    )
    print(
        "- componenti totali:",
        split.component_count,
    )
    print(
        "- componenti training:",
        split.training_component_count,
    )
    print(
        "- componenti test:",
        split.test_component_count,
    )
    print(
        "- eventi training:",
        split.training_event_count,
    )
    print(
        "- eventi test:",
        split.test_event_count,
    )
    print(
        "- oggetti training:",
        split.training_object_count,
    )
    print(
        "- oggetti test:",
        split.test_object_count,
    )
    print(
        "- rapporto effettivo training:",
        round(
            split.effective_training_ratio,
            4,
        ),
    )
    print(
        "- eventi condivisi:",
        split.shared_event_count,
    )
    print(
        "- oggetti condivisi:",
        split.shared_object_count,
    )

    print()
    print("APPRENDIMENTO DELLE RELAZIONI")
    print(
        "- dependency threshold:",
        evaluation.dependency_threshold,
    )
    print(
        "- relative support threshold:",
        (
            evaluation
            .relative_support_threshold
        ),
    )
    print(
        "- self-loop threshold:",
        evaluation.self_loop_threshold,
    )
    print(
        "- relazioni training:",
        len(
            evaluation.training_relations
        ),
    )
    print(
        "- relazioni baseline full-log:",
        len(
            evaluation.reference_relations
        ),
    )
    print(
        "- relazioni mancanti:",
        len(
            evaluation
            .missing_training_relations
        ),
    )
    print(
        "- relazioni aggiuntive:",
        len(
            evaluation
            .additional_training_relations
        ),
    )
    print(
        "- set esattamente coincidente:",
        evaluation.exact_relation_set,
    )

    print()
    print("SELEZIONE DELLE EXECUTION")
    print(
        "- ordini presenti nel test:",
        evaluation.test_order_count,
    )
    print(
        "- ordini esclusi per "
        "contaminazione strutturale:",
        evaluation.excluded_order_count,
    )
    print(
        "- ordini valutabili:",
        evaluation.evaluated_order_count,
    )

    print()
    print("RISULTATI DEGLI INSTANCE GRAPH")
    print(
        "- grafi strutturalmente validi:",
        evaluation.valid_graph_count,
    )
    print(
        "- grafi con topologia esatta:",
        evaluation.exact_topology_count,
    )
    print(
        "- tutti i grafi validi:",
        (
            evaluation
            .all_evaluated_graphs_valid
        ),
    )
    print(
        "- tutte le topologie esatte:",
        evaluation.all_topologies_exact,
    )

    print()
    print("DETTAGLIO PER ORDINE")

    for result in evaluation.results:
        print(
            f"- {result.order_id}: "
            f"eventi={result.event_count}, "
            f"nodi={result.node_count}, "
            f"archi={result.edge_count}, "
            f"DAG={result.is_dag}, "
            "connesso="
            f"{result.is_weakly_connected}, "
            "copertura="
            f"{result.covers_all_events}, "
            "ridotto="
            f"{result.is_transitively_reduced}, "
            "topologia_esatta="
            f"{result.exact_topology}"
        )

    print()
    print("INTERPRETAZIONE")
    print(
        "Le causal relations usate sui casi "
        "di test sono apprese esclusivamente "
        "dal training."
    )
    print(
        "La baseline full-log e utilizzata "
        "soltanto dopo la costruzione dei "
        "grafi holdout per confrontarne "
        "la topologia."
    )
    print(
        "Gli ordini contaminati non sono "
        "errori del grafo: non rispettano "
        "la definizione order-centred "
        "adottata dal prototipo."
    )
    print(
        "Il controllo dimostra la "
        "generalizzazione sui casi "
        "ammissibili del test, non una "
        "fitness OCPN globalmente "
        "sincronizzata."
    )

    if split.shared_event_count:
        raise RuntimeError(
            "Training e test condividono eventi."
        )

    if split.shared_object_count:
        raise RuntimeError(
            "Training e test condividono oggetti."
        )

    if not evaluation.exact_relation_set:
        raise RuntimeError(
            "Le relazioni del training non "
            "coincidono con la baseline."
        )

    if not (
        evaluation
        .all_evaluated_graphs_valid
    ):
        raise RuntimeError(
            "Almeno un Instance Graph "
            "non e strutturalmente valido."
        )

    if not evaluation.all_topologies_exact:
        raise RuntimeError(
            "Almeno una topologia non "
            "coincide con la baseline."
        )

    print()
    print(
        "Validazione end-to-end completata."
    )


if __name__ == "__main__":
    main()