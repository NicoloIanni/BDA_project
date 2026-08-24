from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from numbers import Number
from typing import Any

from ocpm_partial_order.domain.causal_relation import (
    CausalRelation,
)


DEFAULT_DEPENDENCY_THRESHOLD = 0.90
DEFAULT_RELATIVE_SUPPORT_THRESHOLD = 0.05
DEFAULT_SELF_LOOP_THRESHOLD = 0.90


@dataclass(frozen=True)
class CausalRelationEvidence:
    """
    Contiene una causal relation candidata e le misure
    utilizzate per valutarla.

    Per una relazione tra attività differenti viene
    calcolata la dependency measure.

    Per una relazione nella quale sorgente e destinazione
    coincidono viene invece calcolato il self-loop score.
    """

    relation: CausalRelation
    forward_frequency: int
    backward_frequency: int
    dependency: float
    relative_support: float
    self_loop_score: float | None = None


def _measure_frequency(value: Any) -> int:
    """
    Converte una misura dell'OC-DFG in una frequenza.

    PM4Py può rappresentare gli event couples mediante
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
    Calcola le misure degli archi osservati nell'OC-DFG.

    Per attività differenti viene usata la dependency:

        (forward - backward)
        / (forward + backward + 1)

    Per un'attività seguita dalla stessa attività viene
    usato il punteggio dei loop di lunghezza 1:

        frequency / (frequency + 1)

    Il supporto relativo confronta sempre la frequenza
    dell'arco con la massima frequenza uscente dalla
    stessa attività sorgente.
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
            forward = frequencies[
                (source, target)
            ]

            if source == target:
                backward = 0
                dependency = 0.0
                self_loop_score = (
                    forward / (forward + 1)
                )
            else:
                backward = frequencies.get(
                    (target, source),
                    0,
                )

                dependency = (
                    (forward - backward)
                    / (forward + backward + 1)
                )

                self_loop_score = None

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
                    self_loop_score=self_loop_score,
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
    self_loop_threshold: float = (
        DEFAULT_SELF_LOOP_THRESHOLD
    ),
    object_types: Iterable[str] | None = None,
) -> set[CausalRelation]:
    """
    Deriva le causal relations candidate dall'OC-DFG.

    Le relazioni tra attività differenti devono superare
    la dependency threshold.

    Le auto-relazioni devono superare la self-loop
    threshold.

    Entrambe devono inoltre superare la soglia di
    supporto relativo.
    """
    _validate_threshold(
        "dependency_threshold",
        dependency_threshold,
    )
    _validate_threshold(
        "relative_support_threshold",
        relative_support_threshold,
    )
    _validate_threshold(
        "self_loop_threshold",
        self_loop_threshold,
    )

    evidence = score_causal_relations(
        ocdfg=ocdfg,
        object_types=object_types,
    )

    accepted_relations = set()

    for item in evidence:
        relation = item.relation

        is_self_loop = (
            relation.source_activity
            == relation.target_activity
        )

        if is_self_loop:
            score_is_sufficient = (
                item.self_loop_score is not None
                and item.self_loop_score
                >= self_loop_threshold
            )
        else:
            score_is_sufficient = (
                item.dependency
                >= dependency_threshold
            )

        support_is_sufficient = (
            item.relative_support
            >= relative_support_threshold
        )

        if (
            score_is_sufficient
            and support_is_sufficient
        ):
            accepted_relations.add(relation)

    return accepted_relations