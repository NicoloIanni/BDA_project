from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from numbers import Number
from typing import Any

from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)


DEFAULT_DEPENDENCY_THRESHOLD = 0.90
DEFAULT_RELATIVE_SUPPORT_THRESHOLD = 0.05


@dataclass(frozen=True)
class CausalRelationEvidence:
    """
    Contiene una causal relation candidata e le misure
    utilizzate per valutarla.
    """

    relation: CausalRelation
    forward_frequency: int
    backward_frequency: int
    dependency: float
    relative_support: float


def _measure_frequency(value: Any) -> int:
    """
    Converte una misura dell'OC-DFG in una frequenza.

    PM4Py puo rappresentare gli event couples mediante
    collezioni oppure mediante valori numerici.
    """
    if isinstance(value, Number):
        return int(value)

    try:
        return len(value)
    except TypeError as error:
        raise TypeError(
            "Misura OC-DFG non supportata: "
            f"{type(value).__name__}"
        ) from error


def _validate_threshold(
    name: str,
    value: float,
) -> None:
    if not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{name} deve essere compresa tra 0 e 1"
        )


def score_causal_relations(
    ocdfg: Mapping[str, Any],
    object_types: Iterable[str] | None = None,
) -> tuple[CausalRelationEvidence, ...]:
    """
    Calcola dependency e supporto relativo degli archi
    direttamente osservati nell'OC-DFG.

    Le relazioni tra un'attivita e se stessa vengono
    escluse in questa prima versione, coerentemente con
    le assunzioni dell'attuale Instance Graph.
    """
    try:
        edges_by_type = ocdfg[
            "edges"
        ]["event_couples"]
    except (KeyError, TypeError) as error:
        raise ValueError(
            "Struttura OC-DFG non valida: manca "
            "edges.event_couples"
        ) from error

    if not isinstance(edges_by_type, Mapping):
        raise ValueError(
            "edges.event_couples deve essere "
            "una mappa per object type"
        )

    available_types = set(edges_by_type)

    if object_types is None:
        selected_types = available_types
    else:
        selected_types = set(object_types)

    unknown_types = (
        selected_types - available_types
    )

    if unknown_types:
        raise ValueError(
            "Object type non presenti nell'OC-DFG: "
            f"{sorted(unknown_types)}"
        )

    evidence = []

    for object_type in sorted(selected_types):
        raw_edges = edges_by_type[object_type]

        if not isinstance(raw_edges, Mapping):
            raise ValueError(
                "Gli archi dell'object type "
                f"{object_type!r} non sono una mappa"
            )

        frequencies = {
            edge: _measure_frequency(value)
            for edge, value in raw_edges.items()
        }

        maximum_by_source: dict[str, int] = {}

        for edge, frequency in frequencies.items():
            if (
                not isinstance(edge, tuple)
                or len(edge) != 2
            ):
                raise ValueError(
                    "Arco OC-DFG non valido: "
                    f"{edge!r}"
                )

            source, _ = edge

            maximum_by_source[source] = max(
                maximum_by_source.get(source, 0),
                frequency,
            )

        for source, target in sorted(frequencies):
            if source == target:
                continue

            forward = frequencies[
                (source, target)
            ]
            backward = frequencies.get(
                (target, source),
                0,
            )

            dependency = (
                (forward - backward)
                / (forward + backward + 1)
            )

            source_maximum = maximum_by_source[
                source
            ]

            relative_support = (
                forward / source_maximum
                if source_maximum
                else 0.0
            )

            evidence.append(
                CausalRelationEvidence(
                    relation=CausalRelation(
                        source_activity=source,
                        target_activity=target,
                        object_type=object_type,
                    ),
                    forward_frequency=forward,
                    backward_frequency=backward,
                    dependency=dependency,
                    relative_support=relative_support,
                )
            )

    return tuple(evidence)


def derive_causal_relations(
    ocdfg: Mapping[str, Any],
    dependency_threshold: float = (
        DEFAULT_DEPENDENCY_THRESHOLD
    ),
    relative_support_threshold: float = (
        DEFAULT_RELATIVE_SUPPORT_THRESHOLD
    ),
    object_types: Iterable[str] | None = None,
) -> set[CausalRelation]:
    """
    Deriva le causal relations candidate dall'OC-DFG.

    Una relazione viene mantenuta se supera sia la
    dependency threshold sia la soglia di supporto
    relativo rispetto alla massima uscita della sorgente.
    """
    _validate_threshold(
        "dependency_threshold",
        dependency_threshold,
    )
    _validate_threshold(
        "relative_support_threshold",
        relative_support_threshold,
    )

    evidence = score_causal_relations(
        ocdfg=ocdfg,
        object_types=object_types,
    )

    return {
        item.relation
        for item in evidence
        if item.dependency
        >= dependency_threshold
        and item.relative_support
        >= relative_support_threshold
    }