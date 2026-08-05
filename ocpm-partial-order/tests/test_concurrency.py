from pathlib import Path

from ocpm_partial_order.graphs.concurrency import (
    find_incomparable_event_pairs,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.sample_loader import (
    load_causal_relations,
    load_process_execution,
)


def test_confirm_and_pick_are_incomparable() -> None:
    execution = load_process_execution(
        Path(
            "data/samples/"
            "order_management_toy_execution.json"
        )
    )

    relations = load_causal_relations(
        Path(
            "data/samples/"
            "order_management_toy_causal_relations.json"
        )
    )

    graph = build_instance_graph(
        execution,
        relations,
    )

    pairs = find_incomparable_event_pairs(graph)

    assert (
        ("e2", "e4") in pairs
        or ("e4", "e2") in pairs
    )