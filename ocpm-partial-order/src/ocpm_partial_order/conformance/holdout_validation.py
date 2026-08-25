from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

import pandas as pd
import pm4py

from ocpm_partial_order.conformance.object_type_replay import (
    ACTIVITY_COLUMN,
    CASE_ID_COLUMN,
    TIMESTAMP_COLUMN,
    ObjectTypeConformanceSummary,
    replay_flattened_object_type,
)


EVENT_ID_COLUMN = "ocel:eid"
DEFAULT_TRAIN_RATIO = 0.80
DEFAULT_NOISE_THRESHOLD = 0.0
DEFAULT_STRUCTURAL_OBJECT_TYPES = (
    "orders",
    "items",
    "packages",
)


@dataclass(frozen=True)
class ObjectTypeHoldoutSplit:
    """
    Contiene uno split per object type nel quale
    training e test non condividono casi o eventi.

    I DataFrame non partecipano al confronto e
    non vengono mostrati nella rappresentazione.
    """

    object_type: str
    train_log: pd.DataFrame = field(
        repr=False,
        compare=False,
    )
    test_log: pd.DataFrame = field(
        repr=False,
        compare=False,
    )
    component_count: int
    train_component_count: int
    test_component_count: int
    total_case_count: int
    train_case_count: int
    test_case_count: int
    train_event_count: int
    test_event_count: int
    train_variant_count: int
    test_variant_count: int
    unseen_test_variant_count: int

    @property
    def effective_train_ratio(self) -> float:
        if not self.total_case_count:
            return 0.0

        return (
            self.train_case_count
            / self.total_case_count
        )


@dataclass(frozen=True)
class ObjectTypeHoldoutEvaluation:
    """
    Contiene conformance e metriche di qualita
    per una Petri net scoperta dal solo training.
    """

    object_type: str
    split: ObjectTypeHoldoutSplit
    train_conformance: (
        ObjectTypeConformanceSummary
    )
    test_conformance: (
        ObjectTypeConformanceSummary
    )
    train_precision: float
    test_precision: float
    train_generalization: float
    test_generalization: float
    model_simplicity: float
    place_count: int
    transition_count: int
    arc_count: int
    noise_threshold: float


class _DisjointSet:
    def __init__(
        self,
        values: list[str],
    ) -> None:
        self.parent = {
            value: value
            for value in values
        }
        self.rank = {
            value: 0
            for value in values
        }

    def find(
        self,
        value: str,
    ) -> str:
        parent = self.parent[value]

        if parent != value:
            self.parent[value] = self.find(
                parent
            )

        return self.parent[value]

    def union(
        self,
        first: str,
        second: str,
    ) -> None:
        first_root = self.find(first)
        second_root = self.find(second)

        if first_root == second_root:
            return

        if (
            self.rank[first_root]
            < self.rank[second_root]
        ):
            first_root, second_root = (
                second_root,
                first_root,
            )

        self.parent[second_root] = first_root

        if (
            self.rank[first_root]
            == self.rank[second_root]
        ):
            self.rank[first_root] += 1


def _require_non_empty_string(
    name: str,
    value: str,
) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"{name} deve essere "
            "una stringa non vuota"
        )


def _require_ratio(
    name: str,
    value: float,
) -> None:
    if not 0.0 < value < 1.0:
        raise ValueError(
            f"{name} deve essere "
            "compreso tra 0 e 1, "
            "estremi esclusi"
        )


def _require_threshold(
    name: str,
    value: float,
) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} deve essere "
            "compreso tra 0 e 1"
        )


def _require_columns(
    flattened_log: pd.DataFrame,
) -> None:
    required_columns = {
        CASE_ID_COLUMN,
        EVENT_ID_COLUMN,
        ACTIVITY_COLUMN,
        TIMESTAMP_COLUMN,
    }

    missing_columns = (
        required_columns
        - set(flattened_log.columns)
    )

    if missing_columns:
        missing = ", ".join(
            sorted(missing_columns)
        )

        raise ValueError(
            "Il log appiattito non contiene "
            f"le colonne richieste: {missing}"
        )


def _trace_variants(
    flattened_log: pd.DataFrame,
) -> set[tuple[str, ...]]:
    ordered_log = (
        flattened_log.sort_values(
            [
                CASE_ID_COLUMN,
                TIMESTAMP_COLUMN,
                EVENT_ID_COLUMN,
            ],
            kind="stable",
        )
    )

    return {
        tuple(
            str(activity)
            for activity in group[
                ACTIVITY_COLUMN
            ]
        )
        for _, group in ordered_log.groupby(
            CASE_ID_COLUMN,
            sort=False,
        )
    }


def split_flattened_object_type_log(
    flattened_log: pd.DataFrame,
    object_type: str,
    train_ratio: float = (
        DEFAULT_TRAIN_RATIO
    ),
) -> ObjectTypeHoldoutSplit:
    """
    Divide un log appiattito in training e test.

    I casi collegati da almeno un evento comune
    vengono mantenuti nella stessa componente.
    Le componenti vengono ordinate rispetto al
    primo timestamp e assegnate interamente a
    training oppure test.
    """
    _require_non_empty_string(
        "object_type",
        object_type,
    )
    _require_ratio(
        "train_ratio",
        train_ratio,
    )
    _require_columns(
        flattened_log
    )

    normalized_log = (
        flattened_log.copy()
    )

    normalized_log[CASE_ID_COLUMN] = (
        normalized_log[
            CASE_ID_COLUMN
        ].astype(str)
    )
    normalized_log[EVENT_ID_COLUMN] = (
        normalized_log[
            EVENT_ID_COLUMN
        ].astype(str)
    )
    normalized_log[ACTIVITY_COLUMN] = (
        normalized_log[
            ACTIVITY_COLUMN
        ].astype(str)
    )
    normalized_log[TIMESTAMP_COLUMN] = (
        pd.to_datetime(
            normalized_log[
                TIMESTAMP_COLUMN
            ],
            utc=True,
        )
    )

    case_ids = sorted(
        set(
            normalized_log[
                CASE_ID_COLUMN
            ]
        )
    )

    if len(case_ids) < 2:
        raise ValueError(
            "Sono necessari almeno due casi "
            "per costruire uno split"
        )

    disjoint_set = _DisjointSet(
        case_ids
    )

    for _, event_group in (
        normalized_log.groupby(
            EVENT_ID_COLUMN,
            sort=False,
        )
    ):
        related_cases = sorted(
            set(
                event_group[
                    CASE_ID_COLUMN
                ]
            )
        )

        if len(related_cases) < 2:
            continue

        first_case = related_cases[0]

        for other_case in related_cases[1:]:
            disjoint_set.union(
                first_case,
                other_case,
            )

    components_by_root: dict[
        str,
        set[str],
    ] = defaultdict(set)

    for case_id in case_ids:
        components_by_root[
            disjoint_set.find(case_id)
        ].add(case_id)

    components = list(
        components_by_root.values()
    )

    if len(components) < 2:
        raise ValueError(
            "Tutti i casi appartengono "
            "alla stessa componente; non e "
            "possibile costruire uno split "
            "privo di leakage"
        )

    first_timestamp_by_case = (
        normalized_log.groupby(
            CASE_ID_COLUMN,
            sort=False,
        )[TIMESTAMP_COLUMN]
        .min()
        .to_dict()
    )

    ordered_components = sorted(
        components,
        key=lambda component: (
            min(
                first_timestamp_by_case[
                    case_id
                ]
                for case_id in component
            ),
            min(component),
        ),
    )

    cumulative_sizes = []
    cumulative_size = 0

    for component in ordered_components:
        cumulative_size += len(component)
        cumulative_sizes.append(
            cumulative_size
        )

    target_train_cases = (
        len(case_ids)
        * train_ratio
    )

    cut_index = min(
        range(
            1,
            len(ordered_components),
        ),
        key=lambda index: abs(
            cumulative_sizes[index - 1]
            - target_train_cases
        ),
    )

    train_components = (
        ordered_components[:cut_index]
    )
    test_components = (
        ordered_components[cut_index:]
    )

    train_case_ids = set().union(
        *train_components
    )
    test_case_ids = set().union(
        *test_components
    )

    sort_columns = [
        CASE_ID_COLUMN,
        TIMESTAMP_COLUMN,
        EVENT_ID_COLUMN,
    ]

    train_log = (
        normalized_log[
            normalized_log[
                CASE_ID_COLUMN
            ].isin(train_case_ids)
        ]
        .sort_values(
            sort_columns,
            kind="stable",
        )
        .copy()
    )

    test_log = (
        normalized_log[
            normalized_log[
                CASE_ID_COLUMN
            ].isin(test_case_ids)
        ]
        .sort_values(
            sort_columns,
            kind="stable",
        )
        .copy()
    )

    shared_cases = (
        set(
            train_log[CASE_ID_COLUMN]
        )
        & set(
            test_log[CASE_ID_COLUMN]
        )
    )
    shared_events = (
        set(
            train_log[EVENT_ID_COLUMN]
        )
        & set(
            test_log[EVENT_ID_COLUMN]
        )
    )

    if shared_cases or shared_events:
        raise RuntimeError(
            "Lo split contiene casi oppure "
            "eventi condivisi"
        )

    train_variants = _trace_variants(
        train_log
    )
    test_variants = _trace_variants(
        test_log
    )

    return ObjectTypeHoldoutSplit(
        object_type=object_type,
        train_log=train_log,
        test_log=test_log,
        component_count=len(
            ordered_components
        ),
        train_component_count=len(
            train_components
        ),
        test_component_count=len(
            test_components
        ),
        total_case_count=len(case_ids),
        train_case_count=len(
            train_case_ids
        ),
        test_case_count=len(
            test_case_ids
        ),
        train_event_count=(
            train_log[
                EVENT_ID_COLUMN
            ].nunique()
        ),
        test_event_count=(
            test_log[
                EVENT_ID_COLUMN
            ].nunique()
        ),
        train_variant_count=len(
            train_variants
        ),
        test_variant_count=len(
            test_variants
        ),
        unseen_test_variant_count=len(
            test_variants - train_variants
        ),
    )


def _quality_metrics(
    flattened_log: pd.DataFrame,
    component_petri_net: tuple[
        Any,
        Any,
        Any,
    ],
) -> tuple[float, float]:
    net, initial_marking, final_marking = (
        component_petri_net
    )

    precision = (
        pm4py.precision_token_based_replay(
            flattened_log,
            net,
            initial_marking,
            final_marking,
            activity_key=ACTIVITY_COLUMN,
            timestamp_key=TIMESTAMP_COLUMN,
            case_id_key=CASE_ID_COLUMN,
        )
    )

    generalization = pm4py.generalization_tbr(
        flattened_log,
        net,
        initial_marking,
        final_marking,
        activity_key=ACTIVITY_COLUMN,
        timestamp_key=TIMESTAMP_COLUMN,
        case_id_key=CASE_ID_COLUMN,
    )

    return (
        float(precision),
        float(generalization),
    )


def evaluate_object_type_holdout(
    ocel,
    object_type: str,
    train_ratio: float = (
        DEFAULT_TRAIN_RATIO
    ),
    noise_threshold: float = (
        DEFAULT_NOISE_THRESHOLD
    ),
) -> ObjectTypeHoldoutEvaluation:
    """
    Scopre una Petri net sul solo training e
    valuta separatamente training e test.
    """
    _require_non_empty_string(
        "object_type",
        object_type,
    )
    _require_ratio(
        "train_ratio",
        train_ratio,
    )
    _require_threshold(
        "noise_threshold",
        noise_threshold,
    )

    flattened_log = pm4py.ocel_flattening(
        ocel,
        object_type,
    )

    split = split_flattened_object_type_log(
        flattened_log=flattened_log,
        object_type=object_type,
        train_ratio=train_ratio,
    )

    component_petri_net = (
        pm4py.discover_petri_net_inductive(
            split.train_log,
            activity_key=ACTIVITY_COLUMN,
            timestamp_key=TIMESTAMP_COLUMN,
            case_id_key=CASE_ID_COLUMN,
            noise_threshold=noise_threshold,
        )
    )

    train_conformance = (
        replay_flattened_object_type(
            flattened_log=split.train_log,
            component_petri_net=(
                component_petri_net
            ),
            object_type=object_type,
        )
    )

    test_conformance = (
        replay_flattened_object_type(
            flattened_log=split.test_log,
            component_petri_net=(
                component_petri_net
            ),
            object_type=object_type,
        )
    )

    (
        train_precision,
        train_generalization,
    ) = _quality_metrics(
        split.train_log,
        component_petri_net,
    )

    (
        test_precision,
        test_generalization,
    ) = _quality_metrics(
        split.test_log,
        component_petri_net,
    )

    net, initial_marking, final_marking = (
        component_petri_net
    )

    model_simplicity = (
        pm4py.simplicity_petri_net(
            net,
            initial_marking,
            final_marking,
        )
    )

    return ObjectTypeHoldoutEvaluation(
        object_type=object_type,
        split=split,
        train_conformance=(
            train_conformance
        ),
        test_conformance=test_conformance,
        train_precision=train_precision,
        test_precision=test_precision,
        train_generalization=(
            train_generalization
        ),
        test_generalization=(
            test_generalization
        ),
        model_simplicity=float(
            model_simplicity
        ),
        place_count=len(net.places),
        transition_count=len(
            net.transitions
        ),
        arc_count=len(net.arcs),
        noise_threshold=noise_threshold,
    )


def evaluate_structural_holdout(
    ocel,
    object_types: tuple[str, ...] = (
        DEFAULT_STRUCTURAL_OBJECT_TYPES
    ),
    train_ratio: float = (
        DEFAULT_TRAIN_RATIO
    ),
    noise_threshold: float = (
        DEFAULT_NOISE_THRESHOLD
    ),
) -> tuple[
    ObjectTypeHoldoutEvaluation,
    ...,
]:
    """
    Valuta le componenti dei tipi strutturali.
    """
    return tuple(
        evaluate_object_type_holdout(
            ocel=ocel,
            object_type=object_type,
            train_ratio=train_ratio,
            noise_threshold=noise_threshold,
        )
        for object_type in object_types
    )
