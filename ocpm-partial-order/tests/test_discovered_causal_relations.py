from pathlib import Path

import networkx as nx
import pm4py
import pytest

from ocpm_partial_order.config import MAIN_DATASET_DB
from ocpm_partial_order.discovery import (
    derive_causal_relations,
)
from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)
from ocpm_partial_order.extraction import (
    extract_order_centred_execution,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


ORDER_ID = "o-990424"

STRUCTURAL_TYPES = {
    "orders",
    "items",
    "packages",
}

EXPECTED_RELEVANT_RELATIONS = {
    CausalRelation(
        source_activity="place order",
        target_activity="confirm order",
        object_type="orders",
    ),
    CausalRelation(
        source_activity="place order",
        target_activity="confirm order",
        object_type="items",
    ),
    CausalRelation(
        source_activity="confirm order",
        target_activity="pay order",
        object_type="orders",
    ),
    CausalRelation(
        source_activity="confirm order",
        target_activity="pay order",
        object_type="items",
    ),
    CausalRelation(
        source_activity="place order",
        target_activity="pick item",
        object_type="items",
    ),
    CausalRelation(
        source_activity="pick item",
        target_activity="create package",
        object_type="items",
    ),
    CausalRelation(
        source_activity="create package",
        target_activity="send package",
        object_type="items",
    ),
    CausalRelation(
        source_activity="create package",
        target_activity="send package",
        object_type="packages",
    ),
    CausalRelation(
        source_activity="send package",
        target_activity="package delivered",
        object_type="items",
    ),
    CausalRelation(
        source_activity="send package",
        target_activity="package delivered",
        object_type="packages",
    ),
}

EXPECTED_EDGE_OBJECTS = {
    (
        "place_o-990424",
        "confirm_o-990424",
    ): (
        {"items", "orders"},
        {"i-881734", "o-990424"},
    ),
    (
        "confirm_o-990424",
        "pay_o-990424",
    ): (
        {"items", "orders"},
        {"i-881734", "o-990424"},
    ),
    (
        "place_o-990424",
        "pick_i-881734",
    ): (
        {"items"},
        {"i-881734"},
    ),
    (
        "pick_i-881734",
        "create_p-660247",
    ): (
        {"items"},
        {"i-881734"},
    ),
    (
        "create_p-660247",
        "send_p-660247",
    ): (
        {"items", "packages"},
        {"i-881734", "p-660247"},
    ),
    (
        "send_p-660247",
        "deliver_p-660247",
    ): (
        {"items", "packages"},
        {"i-881734", "p-660247"},
    ),
}


@pytest.fixture(scope="module")
def discovered_result() -> tuple[
    set[CausalRelation],
    nx.DiGraph,
]:
    dataset_path = Path(MAIN_DATASET_DB)

    if not dataset_path.is_file():
        pytest.skip(
            "Dataset reale non disponibile: "
            f"{dataset_path}"
        )

    ocel = load_ocel2_sqlite(dataset_path)
    ocdfg = pm4py.discover_ocdfg(ocel)

    causal_relations = derive_causal_relations(
        ocdfg=ocdfg,
        object_types=STRUCTURAL_TYPES,
    )

    execution = extract_order_centred_execution(
        ocel=ocel,
        order_id=ORDER_ID,
    )

    graph = build_instance_graph(
        execution=execution,
        causal_relations=causal_relations,
    )

    execution_activities = {
        event.activity
        for event in execution.events
    }

    relevant_relations = {
        relation
        for relation in causal_relations
        if relation.source_activity
        in execution_activities
        and relation.target_activity
        in execution_activities
    }

    return relevant_relations, graph


def test_expected_relations_are_discovered(
    discovered_result: tuple[
        set[CausalRelation],
        nx.DiGraph,
    ],
) -> None:
    relevant_relations, _ = discovered_result

    assert (
        relevant_relations
        == EXPECTED_RELEVANT_RELATIONS
    )


def test_discovered_relations_build_expected_graph(
    discovered_result: tuple[
        set[CausalRelation],
        nx.DiGraph,
    ],
) -> None:
    _, graph = discovered_result

    assert graph.number_of_nodes() == 7
    assert set(graph.edges) == set(
        EXPECTED_EDGE_OBJECTS
    )

    for edge, expected_attributes in (
        EXPECTED_EDGE_OBJECTS.items()
    ):
        expected_types, expected_ids = (
            expected_attributes
        )
        actual_attributes = graph.edges[edge]

        assert (
            actual_attributes["object_types"]
            == expected_types
        )
        assert (
            actual_attributes["object_ids"]
            == expected_ids
        )


def test_discovered_graph_preserves_partial_order(
    discovered_result: tuple[
        set[CausalRelation],
        nx.DiGraph,
    ],
) -> None:
    _, graph = discovered_result

    assert nx.is_directed_acyclic_graph(graph)

    reduced_again = nx.transitive_reduction(
        graph
    )

    assert set(reduced_again.edges) == set(
        graph.edges
    )

    assert not nx.has_path(
        graph,
        "confirm_o-990424",
        "pick_i-881734",
    )
    assert not nx.has_path(
        graph,
        "pick_i-881734",
        "confirm_o-990424",
    )
    assert not nx.has_path(
        graph,
        "pay_o-990424",
        "deliver_p-660247",
    )
    assert not nx.has_path(
        graph,
        "deliver_p-660247",
        "pay_o-990424",
    )