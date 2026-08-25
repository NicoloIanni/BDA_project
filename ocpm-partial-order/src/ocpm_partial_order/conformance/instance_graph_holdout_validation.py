from dataclasses import dataclass
from typing import Collection

import networkx as nx
import pm4py
from pm4py.objects.ocel.obj import OCEL

from ocpm_partial_order.conformance.object_centric_graph_validation import (
    DEFAULT_GRAPH_OBJECT_TYPES,
    DEFAULT_GRAPH_TRAIN_RATIO,
    ObjectCentricComponentSplit,
    split_object_centric_components,
)
from ocpm_partial_order.discovery.causal_relations import (
    derive_causal_relations,
)
from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)
from ocpm_partial_order.extraction.execution_adapter import (
    StructuralContaminationError,
    extract_order_centred_execution,
)
from ocpm_partial_order.graphs.instance_graph import (
    build_instance_graph,
)
from ocpm_partial_order.graphs.validation import (
    validate_execution,
    validate_instance_graph,
)


DEFAULT_DEPENDENCY_THRESHOLD = 0.90
DEFAULT_RELATIVE_SUPPORT_THRESHOLD = 0.05
DEFAULT_SELF_LOOP_THRESHOLD = 0.90
DEFAULT_ORDER_OBJECT_TYPE = "orders"


Edge = tuple[str, str]


@dataclass(frozen=True)
class InstanceGraphHoldoutResult:
    """
    Risultato end-to-end per una singola
    process execution del test.

    Il grafo holdout usa esclusivamente le
    causal relations apprese dal training.

    Il grafo di riferimento usa le relazioni
    derivate dall'intero log ed e impiegato
    soltanto per il confronto valutativo.
    """

    order_id: str
    event_count: int
    node_count: int
    edge_count: int
    reference_edge_count: int
    is_dag: bool
    is_weakly_connected: bool
    covers_all_events: bool
    is_transitively_reduced: bool
    training_edges: frozenset[Edge]
    reference_edges: frozenset[Edge]

    @property
    def missing_reference_edges(
        self,
    ) -> frozenset[Edge]:
        return (
            self.reference_edges
            - self.training_edges
        )

    @property
    def additional_training_edges(
        self,
    ) -> frozenset[Edge]:
        return (
            self.training_edges
            - self.reference_edges
        )

    @property
    def exact_topology(self) -> bool:
        return (
            self.training_edges
            == self.reference_edges
        )

    @property
    def is_structurally_valid(self) -> bool:
        return (
            self.is_dag
            and self.is_weakly_connected
            and self.covers_all_events
            and self.is_transitively_reduced
        )


@dataclass(frozen=True)
class InstanceGraphHoldoutEvaluation:
    """
    Valutazione end-to-end della pipeline:

        training OCEL
        -> training OC-DFG
        -> causal relations
        -> test process executions
        -> Instance Graph

    Gli ordini strutturalmente contaminati
    sono esclusi perche non rispettano la
    definizione order-centred del prototipo.
    """

    split: ObjectCentricComponentSplit
    dependency_threshold: float
    relative_support_threshold: float
    self_loop_threshold: float
    training_relations: frozenset[
        CausalRelation
    ]
    reference_relations: frozenset[
        CausalRelation
    ]
    test_order_ids: tuple[str, ...]
    excluded_order_ids: tuple[str, ...]
    results: tuple[
        InstanceGraphHoldoutResult,
        ...,
    ]

    @property
    def test_order_count(self) -> int:
        return len(self.test_order_ids)

    @property
    def excluded_order_count(self) -> int:
        return len(self.excluded_order_ids)

    @property
    def evaluated_order_count(self) -> int:
        return len(self.results)

    @property
    def valid_graph_count(self) -> int:
        return sum(
            result.is_structurally_valid
            for result in self.results
        )

    @property
    def exact_topology_count(self) -> int:
        return sum(
            result.exact_topology
            for result in self.results
        )

    @property
    def missing_training_relations(
        self,
    ) -> frozenset[CausalRelation]:
        return (
            self.reference_relations
            - self.training_relations
        )

    @property
    def additional_training_relations(
        self,
    ) -> frozenset[CausalRelation]:
        return (
            self.training_relations
            - self.reference_relations
        )

    @property
    def exact_relation_set(self) -> bool:
        return (
            self.training_relations
            == self.reference_relations
        )

    @property
    def all_evaluated_graphs_valid(
        self,
    ) -> bool:
        return (
            bool(self.results)
            and self.valid_graph_count
            == self.evaluated_order_count
        )

    @property
    def all_topologies_exact(self) -> bool:
        return (
            bool(self.results)
            and self.exact_topology_count
            == self.evaluated_order_count
        )


def _edge_set(
    graph: nx.DiGraph,
) -> frozenset[Edge]:
    return frozenset(
        (
            str(source),
            str(target),
        )
        for source, target in graph.edges()
    )


def _is_transitively_reduced(
    graph: nx.DiGraph,
) -> bool:
    if not nx.is_directed_acyclic_graph(
        graph
    ):
        return False

    reduced = nx.transitive_reduction(graph)

    return (
        set(graph.edges())
        == set(reduced.edges())
    )


def _test_order_ids(
    test_ocel: OCEL,
    order_object_type: str,
) -> tuple[str, ...]:
    objects = test_ocel.objects

    order_ids = objects.loc[
        objects["ocel:type"]
        == order_object_type,
        "ocel:oid",
    ].astype(str)

    return tuple(
        sorted(set(order_ids))
    )


def evaluate_instance_graph_holdout(
    ocel: OCEL,
    object_types: Collection[str] = (
        DEFAULT_GRAPH_OBJECT_TYPES
    ),
    train_ratio: float = (
        DEFAULT_GRAPH_TRAIN_RATIO
    ),
    dependency_threshold: float = (
        DEFAULT_DEPENDENCY_THRESHOLD
    ),
    relative_support_threshold: float = (
        DEFAULT_RELATIVE_SUPPORT_THRESHOLD
    ),
    self_loop_threshold: float = (
        DEFAULT_SELF_LOOP_THRESHOLD
    ),
    order_object_type: str = (
        DEFAULT_ORDER_OBJECT_TYPE
    ),
) -> InstanceGraphHoldoutEvaluation:
    """
    Esegue la validazione end-to-end degli
    Instance Graph su process execution non
    utilizzate per apprendere le relazioni.

    La baseline full-log viene calcolata solo
    dopo la costruzione del modello di training
    ed e usata esclusivamente per misurare la
    corrispondenza della topologia.
    """

    split = split_object_centric_components(
        ocel,
        object_types=object_types,
        train_ratio=train_ratio,
    )

    thresholds = {
        "dependency_threshold": (
            dependency_threshold
        ),
        "relative_support_threshold": (
            relative_support_threshold
        ),
        "self_loop_threshold": (
            self_loop_threshold
        ),
        "object_types": split.object_types,
    }

    training_relations = frozenset(
        derive_causal_relations(
            pm4py.discover_ocdfg(
                split.training_ocel
            ),
            **thresholds,
        )
    )

    reference_relations = frozenset(
        derive_causal_relations(
            pm4py.discover_ocdfg(ocel),
            **thresholds,
        )
    )

    test_order_ids = _test_order_ids(
        split.test_ocel,
        order_object_type,
    )

    excluded_order_ids = []
    results = []

    for order_id in test_order_ids:
        try:
            execution = (
                extract_order_centred_execution(
                    split.test_ocel,
                    order_id,
                )
            )
        except StructuralContaminationError:
            excluded_order_ids.append(
                order_id
            )
            continue

        validate_execution(execution)

        training_graph = build_instance_graph(
            execution,
            set(training_relations),
        )
        validate_instance_graph(
            training_graph
        )

        reference_graph = build_instance_graph(
            execution,
            set(reference_relations),
        )
        validate_instance_graph(
            reference_graph
        )

        event_ids = frozenset(
            event.event_id
            for event in execution.events
        )
        graph_node_ids = frozenset(
            str(node)
            for node in training_graph.nodes()
        )

        training_edges = _edge_set(
            training_graph
        )
        reference_edges = _edge_set(
            reference_graph
        )

        results.append(
            InstanceGraphHoldoutResult(
                order_id=order_id,
                event_count=len(
                    execution.events
                ),
                node_count=(
                    training_graph
                    .number_of_nodes()
                ),
                edge_count=len(
                    training_edges
                ),
                reference_edge_count=len(
                    reference_edges
                ),
                is_dag=(
                    nx.is_directed_acyclic_graph(
                        training_graph
                    )
                ),
                is_weakly_connected=(
                    nx.is_weakly_connected(
                        training_graph
                    )
                ),
                covers_all_events=(
                    graph_node_ids
                    == event_ids
                ),
                is_transitively_reduced=(
                    _is_transitively_reduced(
                        training_graph
                    )
                ),
                training_edges=(
                    training_edges
                ),
                reference_edges=(
                    reference_edges
                ),
            )
        )

    return InstanceGraphHoldoutEvaluation(
        split=split,
        dependency_threshold=(
            dependency_threshold
        ),
        relative_support_threshold=(
            relative_support_threshold
        ),
        self_loop_threshold=(
            self_loop_threshold
        ),
        training_relations=(
            training_relations
        ),
        reference_relations=(
            reference_relations
        ),
        test_order_ids=(
            test_order_ids
        ),
        excluded_order_ids=tuple(
            excluded_order_ids
        ),
        results=tuple(results),
    )