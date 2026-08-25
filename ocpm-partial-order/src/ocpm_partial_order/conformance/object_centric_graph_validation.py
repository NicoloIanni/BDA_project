from dataclasses import dataclass, field
from math import inf
from typing import Any, Collection

import pm4py
from pm4py.algo.discovery.ocel.etot import (
    algorithm as etot_discovery,
)
from pm4py.algo.discovery.ocel.ocdfg import (
    algorithm as ocdfg_discovery,
)
from pm4py.algo.discovery.ocel.otg import (
    algorithm as otg_discovery,
)
from pm4py.algo.transformation.ocel.split_ocel import (
    algorithm as split_ocel,
)
from pm4py.objects.ocel.obj import OCEL


DEFAULT_GRAPH_TRAIN_RATIO = 0.80
DEFAULT_GRAPH_OBJECT_TYPES = (
    "orders",
    "items",
    "packages",
)

OTG_RELATIONSHIP_TYPES = (
    "object_interaction",
    "object_descendants",
    "object_inheritance",
    "object_cobirth",
    "object_codeath",
)


@dataclass(frozen=True)
class StructuralSetComparison:
    """
    Confronto simmetrico tra gli elementi
    strutturali di training e test.

    La copertura del test indica quale quota
    del comportamento osservato nel test era
    gia presente nel training.
    """

    training_elements: frozenset[Any]
    test_elements: frozenset[Any]
    shared_elements: frozenset[Any]
    additional_test_elements: frozenset[Any]
    training_elements_absent_from_test: (
        frozenset[Any]
    )

    @property
    def test_coverage(self) -> float:
        if not self.test_elements:
            return 1.0

        return (
            len(self.shared_elements)
            / len(self.test_elements)
        )

    @property
    def training_coverage(self) -> float:
        if not self.training_elements:
            return 1.0

        return (
            len(self.shared_elements)
            / len(self.training_elements)
        )

    @property
    def jaccard(self) -> float:
        union = (
            self.training_elements
            | self.test_elements
        )

        if not union:
            return 1.0

        return (
            len(self.shared_elements)
            / len(union)
        )


@dataclass(frozen=True)
class ObjectCentricComponentSplit:
    """
    Split dell'OCEL basato sulle componenti
    connesse del grafo di interazione.

    Training e test non condividono eventi
    oppure oggetti.
    """

    object_types: tuple[str, ...]
    training_ocel: OCEL = field(
        repr=False,
        compare=False,
    )
    test_ocel: OCEL = field(
        repr=False,
        compare=False,
    )
    component_count: int
    training_component_count: int
    test_component_count: int
    training_event_count: int
    test_event_count: int
    training_object_count: int
    test_object_count: int
    shared_event_count: int
    shared_object_count: int

    @property
    def total_event_count(self) -> int:
        return (
            self.training_event_count
            + self.test_event_count
        )

    @property
    def effective_training_ratio(self) -> float:
        if not self.total_event_count:
            return 0.0

        return (
            self.training_event_count
            / self.total_event_count
        )


@dataclass(frozen=True)
class ObjectCentricGraphEvaluation:
    """
    Risultati della validazione holdout nativa
    basata su OC-DFG, OTG ed ET-OT.

    Le fitness strutturali ignorano le differenze
    di frequenza dovute alla diversa dimensione
    di training e test.
    """

    split: ObjectCentricComponentSplit

    ocdfg_default_diagnostics: dict[str, Any] = field(
        repr=False,
        compare=False,
    )
    ocdfg_structural_diagnostics: dict[
        str,
        Any,
    ] = field(
        repr=False,
        compare=False,
    )
    otg_default_diagnostics: dict[str, Any] = field(
        repr=False,
        compare=False,
    )
    otg_structural_diagnostics: dict[
        str,
        Any,
    ] = field(
        repr=False,
        compare=False,
    )
    etot_default_diagnostics: dict[str, Any] = field(
        repr=False,
        compare=False,
    )
    etot_structural_diagnostics: dict[
        str,
        Any,
    ] = field(
        repr=False,
        compare=False,
    )

    ocdfg_activities: StructuralSetComparison
    ocdfg_typed_flows: StructuralSetComparison
    otg_object_types: StructuralSetComparison
    otg_edges: StructuralSetComparison
    etot_activities: StructuralSetComparison
    etot_object_types: StructuralSetComparison
    etot_relations: StructuralSetComparison

    @property
    def ocdfg_default_fitness(self) -> float:
        return float(
            self.ocdfg_default_diagnostics[
                "fitness"
            ]
        )

    @property
    def ocdfg_structural_fitness(self) -> float:
        return float(
            self.ocdfg_structural_diagnostics[
                "fitness"
            ]
        )

    @property
    def otg_default_fitness(self) -> float:
        return float(
            self.otg_default_diagnostics[
                "fitness"
            ]
        )

    @property
    def otg_structural_fitness(self) -> float:
        return float(
            self.otg_structural_diagnostics[
                "fitness"
            ]
        )

    @property
    def etot_default_fitness(self) -> float:
        return float(
            self.etot_default_diagnostics[
                "fitness"
            ]
        )

    @property
    def etot_structural_fitness(self) -> float:
        return float(
            self.etot_structural_diagnostics[
                "fitness"
            ]
        )


def _require_ratio(
    name: str,
    value: float,
) -> None:
    if not 0.0 < value < 1.0:
        raise ValueError(
            f"{name} deve essere compreso "
            "tra 0 e 1, estremi esclusi"
        )


def _normalise_object_types(
    object_types: Collection[str],
) -> tuple[str, ...]:
    normalised = tuple(
        sorted(
            {
                value.strip()
                for value in object_types
                if (
                    isinstance(value, str)
                    and value.strip()
                )
            }
        )
    )

    if not normalised:
        raise ValueError(
            "object_types deve contenere "
            "almeno un tipo non vuoto"
        )

    return normalised


def _build_subocel(
    source_ocel: OCEL,
    object_ids: Collection[str],
) -> OCEL:
    selected_object_ids = set(object_ids)

    relations = source_ocel.relations[
        source_ocel.relations[
            source_ocel.object_id_column
        ].isin(selected_object_ids)
    ].copy()

    retained_event_ids = set(
        relations[source_ocel.event_id_column]
    )
    retained_object_ids = set(
        relations[source_ocel.object_id_column]
    )

    events = source_ocel.events[
        source_ocel.events[
            source_ocel.event_id_column
        ].isin(retained_event_ids)
    ].copy()

    objects = source_ocel.objects[
        source_ocel.objects[
            source_ocel.object_id_column
        ].isin(retained_object_ids)
    ].copy()

    return OCEL(
        events=events,
        objects=objects,
        relations=relations,
    )


def filter_structural_ocel(
    ocel: OCEL,
    object_types: Collection[str] = (
        DEFAULT_GRAPH_OBJECT_TYPES
    ),
) -> OCEL:
    """
    Mantiene nell'OCEL soltanto i tipi di
    oggetto considerati strutturali.
    """
    selected_types = _normalise_object_types(
        object_types
    )

    available_types = set(
        ocel.objects[ocel.object_type_column]
    )
    missing_types = (
        set(selected_types)
        - available_types
    )

    if missing_types:
        missing = ", ".join(
            sorted(missing_types)
        )
        raise ValueError(
            "Tipi di oggetto assenti "
            f"dall'OCEL: {missing}"
        )

    selected_object_ids = set(
        ocel.objects.loc[
            ocel.objects[
                ocel.object_type_column
            ].isin(selected_types),
            ocel.object_id_column,
        ]
    )

    structural_ocel = _build_subocel(
        ocel,
        selected_object_ids,
    )

    retained_types = set(
        structural_ocel.objects[
            structural_ocel.object_type_column
        ]
    )

    if retained_types != set(selected_types):
        raise ValueError(
            "Il filtro strutturale non ha "
            "mantenuto tutti i tipi richiesti"
        )

    return structural_ocel


def _component_sort_key(
    component: OCEL,
) -> tuple[Any, int, str]:
    first_timestamp = component.events[
        component.event_timestamp
    ].min()

    first_object_id = min(
        str(value)
        for value in component.objects[
            component.object_id_column
        ]
    )

    return (
        first_timestamp,
        len(component.events),
        first_object_id,
    )


def split_object_centric_components(
    ocel: OCEL,
    object_types: Collection[str] = (
        DEFAULT_GRAPH_OBJECT_TYPES
    ),
    train_ratio: float = (
        DEFAULT_GRAPH_TRAIN_RATIO
    ),
) -> ObjectCentricComponentSplit:
    """
    Divide l'OCEL strutturale usando le
    componenti connesse ufficiali di PM4Py.

    Il punto di separazione minimizza la
    distanza dal rapporto di eventi richiesto.
    """
    _require_ratio(
        "train_ratio",
        train_ratio,
    )

    selected_types = _normalise_object_types(
        object_types
    )
    structural_ocel = filter_structural_ocel(
        ocel=ocel,
        object_types=selected_types,
    )

    components = sorted(
        split_ocel.apply(structural_ocel),
        key=_component_sort_key,
    )

    if len(components) < 2:
        raise ValueError(
            "L'OCEL strutturale forma una "
            "sola componente e non puo essere "
            "diviso senza leakage"
        )

    event_counts = [
        len(component.events)
        for component in components
    ]
    total_events = sum(event_counts)

    training_component_count = min(
        range(1, len(components)),
        key=lambda cut: (
            abs(
                sum(event_counts[:cut])
                / total_events
                - train_ratio
            ),
            cut,
        ),
    )

    training_components = components[
        :training_component_count
    ]
    test_components = components[
        training_component_count:
    ]

    training_object_ids = {
        str(object_id)
        for component in training_components
        for object_id in component.objects[
            component.object_id_column
        ]
    }
    test_object_ids = {
        str(object_id)
        for component in test_components
        for object_id in component.objects[
            component.object_id_column
        ]
    }

    training_ocel = _build_subocel(
        structural_ocel,
        training_object_ids,
    )
    test_ocel = _build_subocel(
        structural_ocel,
        test_object_ids,
    )

    training_event_ids = set(
        training_ocel.events[
            training_ocel.event_id_column
        ]
    )
    test_event_ids = set(
        test_ocel.events[
            test_ocel.event_id_column
        ]
    )

    retained_training_object_ids = set(
        training_ocel.objects[
            training_ocel.object_id_column
        ]
    )
    retained_test_object_ids = set(
        test_ocel.objects[
            test_ocel.object_id_column
        ]
    )

    shared_event_ids = (
        training_event_ids
        & test_event_ids
    )
    shared_object_ids = (
        retained_training_object_ids
        & retained_test_object_ids
    )

    if shared_event_ids or shared_object_ids:
        raise RuntimeError(
            "Lo split object-centric contiene "
            "eventi oppure oggetti condivisi"
        )

    return ObjectCentricComponentSplit(
        object_types=selected_types,
        training_ocel=training_ocel,
        test_ocel=test_ocel,
        component_count=len(components),
        training_component_count=(
            len(training_components)
        ),
        test_component_count=(
            len(test_components)
        ),
        training_event_count=(
            len(training_ocel.events)
        ),
        test_event_count=len(test_ocel.events),
        training_object_count=(
            len(training_ocel.objects)
        ),
        test_object_count=len(test_ocel.objects),
        shared_event_count=len(
            shared_event_ids
        ),
        shared_object_count=len(
            shared_object_ids
        ),
    )


def compare_structural_sets(
    training_elements: Collection[Any],
    test_elements: Collection[Any],
) -> StructuralSetComparison:
    """
    Confronta simmetricamente due insiemi.
    """
    training = frozenset(training_elements)
    test = frozenset(test_elements)
    shared = training & test

    return StructuralSetComparison(
        training_elements=training,
        test_elements=test,
        shared_elements=shared,
        additional_test_elements=(
            test - training
        ),
        training_elements_absent_from_test=(
            training - test
        ),
    )


def typed_ocdfg_flows(
    model: dict[str, Any],
) -> frozenset[tuple[str, str, str]]:
    """
    Estrae i flussi OC-DFG conservando il
    tipo di oggetto.

    La fitness nativa di PM4Py unisce invece
    i flussi dei diversi tipi di oggetto.
    """
    result: set[
        tuple[str, str, str]
    ] = set()

    event_couples = (
        model.get("edges", {})
        .get("event_couples", {})
    )

    for object_type, flows in (
        event_couples.items()
    ):
        for source, target in flows:
            result.add(
                (
                    str(object_type),
                    str(source),
                    str(target),
                )
            )

    return frozenset(result)


def evaluate_object_centric_graph_holdout(
    ocel: OCEL,
    object_types: Collection[str] = (
        DEFAULT_GRAPH_OBJECT_TYPES
    ),
    train_ratio: float = (
        DEFAULT_GRAPH_TRAIN_RATIO
    ),
) -> ObjectCentricGraphEvaluation:
    """
    Valuta il test rispetto ai modelli scoperti
    esclusivamente dal training.

    Produce sia le fitness native, sensibili
    alle frequenze, sia fitness strutturali e
    confronti simmetrici degli elementi.
    """
    split = split_object_centric_components(
        ocel=ocel,
        object_types=object_types,
        train_ratio=train_ratio,
    )

    training_ocdfg = ocdfg_discovery.apply(
        split.training_ocel
    )
    test_ocdfg = ocdfg_discovery.apply(
        split.test_ocel
    )

    training_otg = otg_discovery.apply(
        split.training_ocel
    )
    test_otg = otg_discovery.apply(
        split.test_ocel
    )

    training_etot = etot_discovery.apply(
        split.training_ocel
    )
    test_etot = etot_discovery.apply(
        split.test_ocel
    )

    ocdfg_default = pm4py.conformance_ocdfg(
        test_ocdfg,
        training_ocdfg,
    )
    ocdfg_structural = (
        pm4py.conformance_ocdfg(
            test_ocdfg,
            training_ocdfg,
            parameters={
                "theta_act": inf,
                "theta_flow": inf,
            },
        )
    )

    otg_default = pm4py.conformance_otg(
        test_otg,
        training_otg,
    )
    otg_structural = pm4py.conformance_otg(
        test_otg,
        training_otg,
        parameters={
            "theta": {
                relationship_type: inf
                for relationship_type
                in OTG_RELATIONSHIP_TYPES
            },
        },
    )

    etot_default = pm4py.conformance_etot(
        test_etot,
        training_etot,
    )
    etot_structural = (
        pm4py.conformance_etot(
            test_etot,
            training_etot,
            parameters={
                "theta_real": inf,
            },
        )
    )

    return ObjectCentricGraphEvaluation(
        split=split,
        ocdfg_default_diagnostics=(
            ocdfg_default
        ),
        ocdfg_structural_diagnostics=(
            ocdfg_structural
        ),
        otg_default_diagnostics=otg_default,
        otg_structural_diagnostics=(
            otg_structural
        ),
        etot_default_diagnostics=etot_default,
        etot_structural_diagnostics=(
            etot_structural
        ),
        ocdfg_activities=(
            compare_structural_sets(
                training_ocdfg["activities"],
                test_ocdfg["activities"],
            )
        ),
        ocdfg_typed_flows=(
            compare_structural_sets(
                typed_ocdfg_flows(
                    training_ocdfg
                ),
                typed_ocdfg_flows(
                    test_ocdfg
                ),
            )
        ),
        otg_object_types=(
            compare_structural_sets(
                training_otg[0],
                test_otg[0],
            )
        ),
        otg_edges=compare_structural_sets(
            training_otg[1].keys(),
            test_otg[1].keys(),
        ),
        etot_activities=(
            compare_structural_sets(
                training_etot[0],
                test_etot[0],
            )
        ),
        etot_object_types=(
            compare_structural_sets(
                training_etot[1],
                test_etot[1],
            )
        ),
        etot_relations=(
            compare_structural_sets(
                training_etot[2],
                test_etot[2],
            )
        ),
    )