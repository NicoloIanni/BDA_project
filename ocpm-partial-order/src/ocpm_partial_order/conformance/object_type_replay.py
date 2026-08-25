from collections.abc import Collection, Mapping
from dataclasses import dataclass
from typing import Any

import pandas as pd
import pm4py


CASE_ID_COLUMN = "case:concept:name"
ACTIVITY_COLUMN = "concept:name"
TIMESTAMP_COLUMN = "time:timestamp"

DEFAULT_TOKEN_REPLAY_PARAMETERS = {
    "show_progress_bar": False,
}


@dataclass(frozen=True)
class ObjectTraceConformance:
    """
    Contiene il risultato del token-based replay
    relativo alla proiezione di un singolo oggetto.

    Il risultato riguarda una Petri net componente
    della OCPN e non rappresenta una fitness
    object-centric globale.
    """

    object_type: str
    object_id: str
    event_count: int
    activities: tuple[str, ...]
    trace_is_fit: bool
    trace_fitness: float
    missing_tokens: int
    consumed_tokens: int
    remaining_tokens: int
    produced_tokens: int


@dataclass(frozen=True)
class ObjectTypeConformanceSummary:
    """
    Riassume la conformità di tutte le proiezioni
    appartenenti a un singolo object type.
    """

    object_type: str
    trace_count: int
    fitting_trace_count: int
    non_fitting_trace_count: int
    fitting_percentage: float
    average_trace_fitness: float
    total_missing_tokens: int
    total_remaining_tokens: int
    trace_results: tuple[
        ObjectTraceConformance,
        ...,
    ]


@dataclass(frozen=True)
class ExecutionProjectionConformance:
    """
    Riassume il controllo delle proiezioni degli
    oggetti strutturali di una process execution.

    Non aggrega le Petri net componenti in una
    semantica object-centric sincronizzata.
    """

    trace_results: tuple[
        ObjectTraceConformance,
        ...,
    ]

    @property
    def all_projections_fit(self) -> bool:
        return bool(
            self.trace_results
        ) and all(
            result.trace_is_fit
            for result in self.trace_results
        )

    @property
    def minimum_trace_fitness(self) -> float:
        if not self.trace_results:
            return 0.0

        return min(
            result.trace_fitness
            for result in self.trace_results
        )

    @property
    def average_trace_fitness(self) -> float:
        if not self.trace_results:
            return 0.0

        return sum(
            result.trace_fitness
            for result in self.trace_results
        ) / len(self.trace_results)


def _require_non_empty_string(
    name: str,
    value: str,
) -> None:
    if (
        not isinstance(value, str)
        or not value.strip()
    ):
        raise ValueError(
            f"{name} deve essere una stringa "
            "non vuota"
        )


def _require_flattened_columns(
    flattened_log: pd.DataFrame,
) -> None:
    required_columns = {
        CASE_ID_COLUMN,
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


def _get_component_petri_net(
    ocpn: Mapping[str, Any],
    object_type: str,
) -> tuple[Any, Any, Any]:
    _require_non_empty_string(
        "object_type",
        object_type,
    )

    try:
        petri_nets = ocpn["petri_nets"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            "Struttura OCPN non valida: manca "
            "petri_nets"
        ) from error

    if not isinstance(
        petri_nets,
        Mapping,
    ):
        raise ValueError(
            "ocpn['petri_nets'] deve essere "
            "una mappa per object type"
        )

    if object_type not in petri_nets:
        raise ValueError(
            "Object type non presente nella OCPN: "
            f"{object_type!r}"
        )

    component = petri_nets[object_type]

    if (
        not isinstance(component, tuple)
        or len(component) != 3
    ):
        raise ValueError(
            "La componente OCPN deve contenere "
            "Petri net, initial marking e "
            "final marking"
        )

    return component


def _select_object_trace(
    flattened_log: pd.DataFrame,
    object_id: str,
) -> pd.DataFrame:
    _require_non_empty_string(
        "object_id",
        object_id,
    )
    _require_flattened_columns(
        flattened_log
    )

    trace = flattened_log[
        flattened_log[
            CASE_ID_COLUMN
        ].astype(str)
        == object_id
    ].copy()

    if trace.empty:
        raise ValueError(
            "Oggetto non trovato nel log "
            f"appiattito: {object_id!r}"
        )

    return trace


def _build_trace_result(
    object_type: str,
    object_id: str,
    activities: tuple[str, ...],
    diagnostic: Mapping[str, Any],
) -> ObjectTraceConformance:
    return ObjectTraceConformance(
        object_type=object_type,
        object_id=object_id,
        event_count=len(activities),
        activities=activities,
        trace_is_fit=bool(
            diagnostic.get(
                "trace_is_fit",
                False,
            )
        ),
        trace_fitness=float(
            diagnostic.get(
                "trace_fitness",
                0.0,
            )
        ),
        missing_tokens=int(
            diagnostic.get(
                "missing_tokens",
                0,
            )
        ),
        consumed_tokens=int(
            diagnostic.get(
                "consumed_tokens",
                0,
            )
        ),
        remaining_tokens=int(
            diagnostic.get(
                "remaining_tokens",
                0,
            )
        ),
        produced_tokens=int(
            diagnostic.get(
                "produced_tokens",
                0,
            )
        ),
    )


def replay_flattened_object_trace(
    flattened_trace: pd.DataFrame,
    component_petri_net: tuple[
        Any,
        Any,
        Any,
    ],
    object_type: str,
    object_id: str,
) -> ObjectTraceConformance:
    """
    Esegue il token-based replay di un log
    appiattito contenente un solo oggetto.

    Questa funzione consente anche di verificare
    tracce modificate in memoria nei test.
    """
    _require_non_empty_string(
        "object_type",
        object_type,
    )
    _require_non_empty_string(
        "object_id",
        object_id,
    )
    _require_flattened_columns(
        flattened_trace
    )

    case_ids = set(
        flattened_trace[
            CASE_ID_COLUMN
        ].astype(str)
    )

    if case_ids != {object_id}:
        raise ValueError(
            "Il log deve contenere una sola "
            "proiezione con identificatore "
            f"{object_id!r}; trovati "
            f"{sorted(case_ids)}"
        )

    if (
        not isinstance(
            component_petri_net,
            tuple,
        )
        or len(component_petri_net) != 3
    ):
        raise ValueError(
            "component_petri_net deve contenere "
            "Petri net, initial marking e "
            "final marking"
        )

    net, initial_marking, final_marking = (
        component_petri_net
    )

    diagnostics = (
        pm4py
        .conformance_diagnostics_token_based_replay(
            flattened_trace,
            net,
            initial_marking,
            final_marking,
            opt_parameters=(
                DEFAULT_TOKEN_REPLAY_PARAMETERS
            ),
        )
    )

    if len(diagnostics) != 1:
        raise RuntimeError(
            "Il token-based replay deve "
            "restituire un solo risultato; "
            f"ottenuti {len(diagnostics)}"
        )

    activities = tuple(
        flattened_trace[
            ACTIVITY_COLUMN
        ].astype(str)
    )

    return _build_trace_result(
        object_type=object_type,
        object_id=object_id,
        activities=activities,
        diagnostic=diagnostics[0],
    )


def check_object_projection(
    ocel,
    ocpn: Mapping[str, Any],
    object_type: str,
    object_id: str,
) -> ObjectTraceConformance:
    """
    Appiattisce l'OCEL per object type e controlla
    la proiezione di un singolo oggetto.
    """
    component = _get_component_petri_net(
        ocpn,
        object_type,
    )

    flattened_log = pm4py.ocel_flattening(
        ocel,
        object_type,
    )

    trace = _select_object_trace(
        flattened_log,
        object_id,
    )

    return replay_flattened_object_trace(
        flattened_trace=trace,
        component_petri_net=component,
        object_type=object_type,
        object_id=object_id,
    )


def check_execution_projections(
    ocel,
    ocpn: Mapping[str, Any],
    object_ids_by_type: Mapping[
        str,
        Collection[str],
    ],
) -> ExecutionProjectionConformance:
    """
    Controlla le proiezioni degli oggetti indicati.

    Ogni object type viene appiattito una sola volta.
    Il risultato non costituisce una fitness
    object-centric globale sincronizzata.
    """
    if not object_ids_by_type:
        raise ValueError(
            "È richiesto almeno un oggetto"
        )

    results = []

    for object_type in sorted(
        object_ids_by_type
    ):
        component = _get_component_petri_net(
            ocpn,
            object_type,
        )

        flattened_log = (
            pm4py.ocel_flattening(
                ocel,
                object_type,
            )
        )

        raw_object_ids = (
            object_ids_by_type[
                object_type
            ]
        )

        if isinstance(
            raw_object_ids,
            str,
        ):
            object_ids = {
                raw_object_ids
            }
        else:
            object_ids = {
                str(object_id)
                for object_id
                in raw_object_ids
            }

        if not object_ids:
            raise ValueError(
                "Nessun object ID fornito per "
                f"{object_type!r}"
            )

        for object_id in sorted(
            object_ids
        ):
            trace = _select_object_trace(
                flattened_log,
                object_id,
            )

            results.append(
                replay_flattened_object_trace(
                    flattened_trace=trace,
                    component_petri_net=component,
                    object_type=object_type,
                    object_id=object_id,
                )
            )

    return ExecutionProjectionConformance(
        trace_results=tuple(results),
    )


def replay_flattened_object_type(
    flattened_log: pd.DataFrame,
    component_petri_net: tuple[
        Any,
        Any,
        Any,
    ],
    object_type: str,
) -> ObjectTypeConformanceSummary:
    """
    Esegue il token-based replay di tutte le
    proiezioni contenute in un log appiattito.

    La funzione pu? essere usata sia sul log
    completo sia su partizioni di training,
    validation oppure test.
    """
    _require_non_empty_string(
        "object_type",
        object_type,
    )
    _require_flattened_columns(
        flattened_log
    )

    if (
        not isinstance(
            component_petri_net,
            tuple,
        )
        or len(component_petri_net) != 3
    ):
        raise ValueError(
            "component_petri_net deve contenere "
            "Petri net, initial marking e "
            "final marking"
        )

    traditional_log = (
        pm4py.convert_to_event_log(
            flattened_log
        )
    )

    net, initial_marking, final_marking = (
        component_petri_net
    )

    diagnostics = (
        pm4py
        .conformance_diagnostics_token_based_replay(
            traditional_log,
            net,
            initial_marking,
            final_marking,
            opt_parameters=(
                DEFAULT_TOKEN_REPLAY_PARAMETERS
            ),
        )
    )

    if len(traditional_log) != len(
        diagnostics
    ):
        raise RuntimeError(
            "Il numero di tracce e risultati "
            "di conformance non coincide"
        )

    trace_results = []

    for trace, diagnostic in zip(
        traditional_log,
        diagnostics,
    ):
        object_id = str(
            trace.attributes.get(
                "concept:name",
                "",
            )
        )

        if not object_id:
            raise ValueError(
                "Una traccia non contiene "
                "l'identificatore del caso"
            )

        activities = tuple(
            str(event[ACTIVITY_COLUMN])
            for event in trace
        )

        trace_results.append(
            _build_trace_result(
                object_type=object_type,
                object_id=object_id,
                activities=activities,
                diagnostic=diagnostic,
            )
        )

    ordered_results = tuple(
        sorted(
            trace_results,
            key=lambda result: (
                result.object_id
            ),
        )
    )

    trace_count = len(
        ordered_results
    )

    fitting_trace_count = sum(
        result.trace_is_fit
        for result in ordered_results
    )

    non_fitting_trace_count = (
        trace_count
        - fitting_trace_count
    )

    average_trace_fitness = (
        sum(
            result.trace_fitness
            for result in ordered_results
        )
        / trace_count
        if trace_count
        else 0.0
    )

    fitting_percentage = (
        100.0
        * fitting_trace_count
        / trace_count
        if trace_count
        else 0.0
    )

    return ObjectTypeConformanceSummary(
        object_type=object_type,
        trace_count=trace_count,
        fitting_trace_count=(
            fitting_trace_count
        ),
        non_fitting_trace_count=(
            non_fitting_trace_count
        ),
        fitting_percentage=(
            fitting_percentage
        ),
        average_trace_fitness=(
            average_trace_fitness
        ),
        total_missing_tokens=sum(
            result.missing_tokens
            for result in ordered_results
        ),
        total_remaining_tokens=sum(
            result.remaining_tokens
            for result in ordered_results
        ),
        trace_results=ordered_results,
    )


def check_object_type_conformance(
    ocel,
    ocpn: Mapping[str, Any],
    object_type: str,
) -> ObjectTypeConformanceSummary:
    """
    Esegue il token-based replay di tutte le
    proiezioni appartenenti a un object type.
    """
    component = _get_component_petri_net(
        ocpn,
        object_type,
    )

    flattened_log = pm4py.ocel_flattening(
        ocel,
        object_type,
    )

    return replay_flattened_object_type(
        flattened_log=flattened_log,
        component_petri_net=component,
        object_type=object_type,
    )
