from typing import Any

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance import (
    ObjectCentricGraphEvaluation,
    StructuralSetComparison,
    evaluate_object_centric_graph_holdout,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


SEPARATOR = "=" * 72


def _print_set_comparison(
    title: str,
    comparison: StructuralSetComparison,
) -> None:
    print(f"\n{title}")
    print(
        "- elementi nel training:",
        len(comparison.training_elements),
    )
    print(
        "- elementi nel test:",
        len(comparison.test_elements),
    )
    print(
        "- elementi condivisi:",
        len(comparison.shared_elements),
    )
    print(
        "- copertura del test:",
        round(comparison.test_coverage, 6),
    )
    print(
        "- copertura del training:",
        round(
            comparison.training_coverage,
            6,
        ),
    )
    print(
        "- indice di Jaccard:",
        round(comparison.jaccard, 6),
    )
    print(
        "- elementi nuovi nel test:",
        len(
            comparison.additional_test_elements
        ),
    )
    print(
        "- elementi del training "
        "assenti dal test:",
        len(
            comparison
            .training_elements_absent_from_test
        ),
    )

    if comparison.additional_test_elements:
        print("  Dettaglio elementi nuovi:")
        for element in sorted(
            comparison.additional_test_elements,
            key=repr,
        ):
            print(f"  - {element}")

    if (
        comparison
        .training_elements_absent_from_test
    ):
        print(
            "  Dettaglio elementi non "
            "riprodotti nel test:"
        )
        for element in sorted(
            comparison
            .training_elements_absent_from_test,
            key=repr,
        ):
            print(f"  - {element}")


def _count(
    diagnostics: dict[str, Any],
    key: str,
) -> int:
    value = diagnostics.get(key, ())
    return len(value)


def _print_native_diagnostics(
    evaluation: ObjectCentricGraphEvaluation,
) -> None:
    print("\n" + SEPARATOR)
    print("DIAGNOSTICA NATIVA PM4PY")
    print(SEPARATOR)

    ocdfg = (
        evaluation.ocdfg_default_diagnostics
    )
    ocdfg_structural = (
        evaluation
        .ocdfg_structural_diagnostics
    )

    print("\nOC-DFG")
    print(
        "- fitness predefinita:",
        evaluation.ocdfg_default_fitness,
    )
    print(
        "- fitness strutturale:",
        evaluation.ocdfg_structural_fitness,
    )
    print(
        "- attivita mancanti:",
        _count(
            ocdfg_structural,
            "missing_activities",
        ),
    )
    print(
        "- attivita aggiuntive:",
        _count(
            ocdfg_structural,
            "additional_activities",
        ),
    )
    print(
        "- flussi mancanti:",
        _count(
            ocdfg_structural,
            "missing_flows",
        ),
    )
    print(
        "- flussi aggiuntivi:",
        _count(
            ocdfg_structural,
            "additional_flows",
        ),
    )
    print(
        "- deviazioni frequenziali:",
        _count(
            ocdfg,
            (
                "non_conforming_"
                "activities_in_measure"
            ),
        )
        + _count(
            ocdfg,
            (
                "non_conforming_"
                "flows_in_measure"
            ),
        ),
    )

    otg = evaluation.otg_default_diagnostics
    otg_structural = (
        evaluation.otg_structural_diagnostics
    )

    print("\nOTG")
    print(
        "- fitness predefinita:",
        evaluation.otg_default_fitness,
    )
    print(
        "- fitness strutturale:",
        evaluation.otg_structural_fitness,
    )
    print(
        "- tipi mancanti:",
        _count(
            otg_structural,
            "missing_object_types",
        ),
    )
    print(
        "- tipi aggiuntivi:",
        _count(
            otg_structural,
            "additional_object_types",
        ),
    )
    print(
        "- archi mancanti:",
        _count(
            otg_structural,
            "missing_edges",
        ),
    )
    print(
        "- archi aggiuntivi:",
        _count(
            otg_structural,
            "additional_edges",
        ),
    )
    print(
        "- deviazioni frequenziali:",
        _count(
            otg,
            "non_conforming_edges",
        ),
    )

    etot = evaluation.etot_default_diagnostics
    etot_structural = (
        evaluation.etot_structural_diagnostics
    )
    etot_details = etot.get("details", {})
    structural_details = (
        etot_structural.get("details", {})
    )

    frequency_deviations = sum(
        1
        for difference in etot_details.get(
            "delta_rel",
            {},
        ).values()
        if difference > 0.10
    )

    print("\nET-OT")
    print(
        "- fitness predefinita:",
        evaluation.etot_default_fitness,
    )
    print(
        "- fitness strutturale:",
        evaluation.etot_structural_fitness,
    )
    print(
        "- attivita mancanti:",
        _count(
            structural_details,
            "A_missing",
        ),
    )
    print(
        "- attivita aggiuntive:",
        _count(
            structural_details,
            "A_additional",
        ),
    )
    print(
        "- tipi mancanti:",
        _count(
            structural_details,
            "OT_missing",
        ),
    )
    print(
        "- tipi aggiuntivi:",
        _count(
            structural_details,
            "OT_additional",
        ),
    )
    print(
        "- relazioni mancanti:",
        _count(
            structural_details,
            "R_missing",
        ),
    )
    print(
        "- relazioni aggiuntive:",
        _count(
            structural_details,
            "R_additional",
        ),
    )
    print(
        "- deviazioni frequenziali:",
        frequency_deviations,
    )


def main() -> None:
    print(SEPARATOR)
    print(
        "VALIDAZIONE HOLDOUT OBJECT-CENTRIC "
        "BASATA SU GRAFI"
    )
    print(SEPARATOR)

    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    evaluation = (
        evaluate_object_centric_graph_holdout(
            ocel=ocel,
        )
    )
    split = evaluation.split

    print(
        "Tipi strutturali:",
        list(split.object_types),
    )
    print(
        "Componenti totali:",
        split.component_count,
    )
    print(
        "Componenti di training:",
        split.training_component_count,
    )
    print(
        "Componenti di test:",
        split.test_component_count,
    )
    print(
        "Eventi di training:",
        split.training_event_count,
    )
    print(
        "Eventi di test:",
        split.test_event_count,
    )
    print(
        "Oggetti di training:",
        split.training_object_count,
    )
    print(
        "Oggetti di test:",
        split.test_object_count,
    )
    print(
        "Rapporto effettivo di training:",
        round(
            split.effective_training_ratio,
            4,
        ),
    )
    print(
        "Eventi condivisi:",
        split.shared_event_count,
    )
    print(
        "Oggetti condivisi:",
        split.shared_object_count,
    )

    _print_native_diagnostics(evaluation)

    print("\n" + SEPARATOR)
    print("CONFRONTO STRUTTURALE SIMMETRICO")
    print(SEPARATOR)

    _print_set_comparison(
        "OC-DFG: attivita",
        evaluation.ocdfg_activities,
    )
    _print_set_comparison(
        "OC-DFG: flussi tipizzati",
        evaluation.ocdfg_typed_flows,
    )
    _print_set_comparison(
        "OTG: tipi di oggetto",
        evaluation.otg_object_types,
    )
    _print_set_comparison(
        "OTG: archi",
        evaluation.otg_edges,
    )
    _print_set_comparison(
        "ET-OT: attivita",
        evaluation.etot_activities,
    )
    _print_set_comparison(
        "ET-OT: tipi di oggetto",
        evaluation.etot_object_types,
    )
    _print_set_comparison(
        "ET-OT: relazioni",
        evaluation.etot_relations,
    )

    print("\n" + SEPARATOR)
    print("INTERPRETAZIONE")
    print(SEPARATOR)
    print(
        "Le fitness predefinite includono le "
        "differenze di frequenza tra training "
        "e test di dimensioni diverse."
    )
    print(
        "Le fitness strutturali verificano "
        "attivita, flussi e relazioni ignorando "
        "tali differenze di volume."
    )
    print(
        "Questo esperimento costituisce una "
        "validazione object-centric basata su "
        "grafi, non un replay sincronizzato "
        "sulla OCPN."
    )

    print(
        "\nValidazione object-centric "
        "completata."
    )


if __name__ == "__main__":
    main()