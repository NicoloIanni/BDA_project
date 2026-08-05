import networkx as nx

from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)
from ocpm_partial_order.domain.process_execution import (
    ProcessExecution,
)
from ocpm_partial_order.graphs.validation import (
    validate_execution,
    validate_instance_graph,
)


def build_instance_graph(
    execution: ProcessExecution,
    causal_relations: set[CausalRelation],
) -> nx.DiGraph:
    """
    Costruisce il primo prototipo di Instance Graph
    object-centric.

    Assunzioni:
    - execution perfettamente conforme;
    - causal relations già note;
    - nessun repairing;
    - nessuna attività ripetuta problematicamente
      nello stesso ciclo di vita dell'oggetto.
    """
    validate_execution(execution)

    graph = nx.DiGraph()

    # Un nodo per ogni evento.
    for event in execution.events:
        graph.add_node(
            event.event_id,
            activity=event.activity,
            timestamp=event.timestamp,
            objects={
                (
                    obj.object_type,
                    obj.object_id,
                )
                for obj in event.objects
            },
        )

    # Indicizzazione delle causal relations per tipo.
    relations_by_type: dict[
        str,
        set[tuple[str, str]],
    ] = {}

    for relation in causal_relations:
        relations_by_type.setdefault(
            relation.object_type,
            set(),
        ).add(
            (
                relation.source_activity,
                relation.target_activity,
            )
        )

    # Analisi separata del ciclo di vita
    # di ogni oggetto.
    for object_type, object_id in execution.objects():
        object_events = execution.events_for_object(
            object_type=object_type,
            object_id=object_id,
        )

        valid_relations = relations_by_type.get(
            object_type,
            set(),
        )

        for source_index, source_event in enumerate(
            object_events
        ):
            later_events = object_events[
                source_index + 1 :
            ]

            for target_event in later_events:
                activity_pair = (
                    source_event.activity,
                    target_event.activity,
                )

                if activity_pair not in valid_relations:
                    continue

                if graph.has_edge(
                    source_event.event_id,
                    target_event.event_id,
                ):
                    edge = graph.edges[
                        source_event.event_id,
                        target_event.event_id,
                    ]

                    edge["object_types"].add(
                        object_type
                    )
                    edge["object_ids"].add(
                        object_id
                    )
                else:
                    graph.add_edge(
                        source_event.event_id,
                        target_event.event_id,
                        object_types={object_type},
                        object_ids={object_id},
                    )

    validate_instance_graph(graph)

    # Eliminazione degli archi transitivi ridondanti.
    reduced_graph = nx.transitive_reduction(graph)

    # NetworkX non conserva automaticamente
    # tutti gli attributi durante la riduzione.
    for node, attributes in graph.nodes(data=True):
        reduced_graph.nodes[node].update(attributes)

    for source, target in reduced_graph.edges:
        reduced_graph.edges[source, target].update(
            graph.edges[source, target]
        )

    validate_instance_graph(reduced_graph)

    return reduced_graph