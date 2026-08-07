from pathlib import Path

import networkx as nx
import pytest

from ocpm_partial_order.config import MAIN_DATASET_DB
from ocpm_partial_order.extraction import (
    extract_order_centred_execution,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)
from ocpm_partial_order.io.sample_loader import (
    load_causal_relations,
)


ORDER_ID = "o-990424"

RELATIONS_PATH = Path(
    "data/derived/"
    "order_management_o_990424_causal_relations.json"
)

EXPECTED_NODES = {
    "place_o-990424",
    "confirm_o-990424",
    "pay_o-990424",
    "pick_i-881734",
    "create_p-660247",
    "send_p-660247",
    "deliver_p-660247",
}

EXPECTED_EDGE_OBJECTS = {
    (
        "place_o-990424",
        "confirm_o-990424",
    ): (
        {"orders"},
        {"o-990424"},
    ),
    (
        "confirm_o-990424",
        "pay_o-990424",
    ): (
        {"orders"},
        {"o-990424"},
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
        {"packages"},
        {"p-660247"},
    ),
    (
        "send_p-660247",
        "deliver_p-660247",
    ): (
        {"packages"},
        {"p-660247"},
    ),
}


@pytest.fixture(scope="module")
def real_graph() -> nx.DiGraph:
    dataset_path = Path(MAIN_DATASET_DB)

    if not dataset_path.is_file():
        pytest.skip(
            "Dataset reale non disponibile: "
            f"{dataset_path}"
        )

    if not RELATIONS_PATH.is_file():
        pytest.fail(
            "File delle causal relations non trovato: "
            f"{RELATIONS_PATH}"
        )

    ocel = load_ocel2_sqlite(dataset_path)

    execution = extract_order_centred_execution(
        ocel=ocel,
        order_id=ORDER_ID,
    )

    causal_relations = load_causal_relations(
        RELATIONS_PATH
    )

    return build_instance_graph(
        execution=execution,
        causal_relations=causal_relations,
    )


def test_real_graph_has_expected_nodes_and_edges(
    real_graph: nx.DiGraph,
) -> None:
    assert set(real_graph.nodes) == EXPECTED_NODES
    assert set(real_graph.edges) == set(
        EXPECTED_EDGE_OBJECTS
    )

    for edge, expected_attributes in (
        EXPECTED_EDGE_OBJECTS.items()
    ):
        expected_types, expected_ids = (
            expected_attributes
        )
        actual_attributes = real_graph.edges[edge]

        assert (
            actual_attributes["object_types"]
            == expected_types
        )
        assert (
            actual_attributes["object_ids"]
            == expected_ids
        )


def test_real_graph_is_a_transitively_reduced_dag(
    real_graph: nx.DiGraph,
) -> None:
    assert nx.is_directed_acyclic_graph(real_graph)

    reduced_again = nx.transitive_reduction(
        real_graph
    )

    assert set(reduced_again.nodes) == set(
        real_graph.nodes
    )
    assert set(reduced_again.edges) == set(
        real_graph.edges
    )

    original_closure = nx.transitive_closure_dag(
        real_graph
    )
    reduced_closure = nx.transitive_closure_dag(
        reduced_again
    )

    assert set(original_closure.edges) == set(
        reduced_closure.edges
    )


def test_payment_and_logistics_are_incomparable(
    real_graph: nx.DiGraph,
) -> None:
    payment = "pay_o-990424"
    delivery = "deliver_p-660247"

    assert not nx.has_path(
        real_graph,
        payment,
        delivery,
    )
    assert not nx.has_path(
        real_graph,
        delivery,
        payment,
    )

    confirmation = "confirm_o-990424"
    picking = "pick_i-881734"

    assert not nx.has_path(
        real_graph,
        confirmation,
        picking,
    )
    assert not nx.has_path(
        real_graph,
        picking,
        confirmation,
    )
