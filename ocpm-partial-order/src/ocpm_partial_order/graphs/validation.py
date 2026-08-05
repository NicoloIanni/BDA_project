import networkx as nx

from ocpm_partial_order.domain.process_execution import (
    ProcessExecution,
)


class InvalidExecutionError(ValueError):
    pass


def validate_execution(
    execution: ProcessExecution,
) -> None:
    if not execution.events:
        raise InvalidExecutionError(
            "La process execution non contiene eventi."
        )

    event_ids = [
        event.event_id
        for event in execution.events
    ]

    if len(event_ids) != len(set(event_ids)):
        raise InvalidExecutionError(
            "Sono presenti event_id duplicati."
        )

    for event in execution.events:
        if not event.activity.strip():
            raise InvalidExecutionError(
                f"L'evento {event.event_id} "
                "non ha un'attività."
            )

        if not event.objects:
            raise InvalidExecutionError(
                f"L'evento {event.event_id} "
                "non ha oggetti associati."
            )


def validate_instance_graph(
    graph: nx.DiGraph,
) -> None:
    if not nx.is_directed_acyclic_graph(graph):
        raise InvalidExecutionError(
            "L'Instance Graph contiene un ciclo."
        )