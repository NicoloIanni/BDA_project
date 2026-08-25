from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance import (
    check_execution_projections,
    check_object_type_conformance,
)
from ocpm_partial_order.discovery import (
    discover_ocpn,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


REFERENCE_ORDER = "o-990424"

REFERENCE_OBJECTS = {
    "orders": {
        "o-990424",
    },
    "items": {
        "i-881734",
    },
    "packages": {
        "p-660247",
    },
}

STRUCTURAL_OBJECT_TYPES = (
    "orders",
    "items",
    "packages",
)


def print_execution_report(
    report,
) -> None:
    print("\n" + "=" * 72)
    print(
        "REFERENCE PROCESS EXECUTION:",
        REFERENCE_ORDER,
    )
    print("=" * 72)

    for result in report.trace_results:
        print(
            "\nObject type:",
            result.object_type,
        )
        print(
            "Object ID:",
            result.object_id,
        )
        print(
            "Events:",
            result.event_count,
        )
        print(
            "Activities:",
            " -> ".join(
                result.activities
            ),
        )
        print(
            "Trace is fit:",
            result.trace_is_fit,
        )
        print(
            "Trace fitness:",
            result.trace_fitness,
        )
        print(
            "Missing tokens:",
            result.missing_tokens,
        )
        print(
            "Remaining tokens:",
            result.remaining_tokens,
        )

    print(
        "\nAll projections fit:",
        report.all_projections_fit,
    )
    print(
        "Minimum projection fitness:",
        report.minimum_trace_fitness,
    )
    print(
        "Average projection fitness:",
        report.average_trace_fitness,
    )


def print_object_type_summary(
    summary,
) -> None:
    print("\n" + "-" * 72)
    print(
        "Object type:",
        summary.object_type,
    )
    print(
        "Traces:",
        summary.trace_count,
    )
    print(
        "Fitting traces:",
        summary.fitting_trace_count,
    )
    print(
        "Non-fitting traces:",
        summary.non_fitting_trace_count,
    )
    print(
        "Fitting percentage:",
        summary.fitting_percentage,
    )
    print(
        "Average trace fitness:",
        summary.average_trace_fitness,
    )
    print(
        "Missing tokens:",
        summary.total_missing_tokens,
    )
    print(
        "Remaining tokens:",
        summary.total_remaining_tokens,
    )


def main() -> None:
    print("=" * 72)
    print("OBJECT-TYPE CONFORMANCE CHECKING")
    print("=" * 72)

    print(
        "Dataset:",
        MAIN_DATASET_DB,
    )

    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    print("OCEL loaded.")

    ocpn = discover_ocpn(
        ocel
    )

    print("OCPN discovered.")

    execution_report = (
        check_execution_projections(
            ocel=ocel,
            ocpn=ocpn,
            object_ids_by_type=(
                REFERENCE_OBJECTS
            ),
        )
    )

    print_execution_report(
        execution_report
    )

    print("\n" + "=" * 72)
    print("FULL OBJECT-TYPE SUMMARIES")
    print("=" * 72)

    summaries = []

    for object_type in (
        STRUCTURAL_OBJECT_TYPES
    ):
        summary = (
            check_object_type_conformance(
                ocel=ocel,
                ocpn=ocpn,
                object_type=object_type,
            )
        )

        summaries.append(
            summary
        )

        print_object_type_summary(
            summary
        )

    total_traces = sum(
        summary.trace_count
        for summary in summaries
    )

    total_fitting = sum(
        summary.fitting_trace_count
        for summary in summaries
    )

    total_non_fitting = sum(
        summary.non_fitting_trace_count
        for summary in summaries
    )

    total_missing = sum(
        summary.total_missing_tokens
        for summary in summaries
    )

    total_remaining = sum(
        summary.total_remaining_tokens
        for summary in summaries
    )

    print("\n" + "=" * 72)
    print("OVERALL PROJECTION SUMMARY")
    print("=" * 72)

    print(
        "Structural projections:",
        total_traces,
    )
    print(
        "Fitting projections:",
        total_fitting,
    )
    print(
        "Non-fitting projections:",
        total_non_fitting,
    )
    print(
        "Missing tokens:",
        total_missing,
    )
    print(
        "Remaining tokens:",
        total_remaining,
    )

    print("\nMethodological note:")
    print(
        "These results concern the separate "
        "object-type projections."
    )
    print(
        "They do not constitute a globally "
        "synchronized object-centric fitness."
    )
    print(
        "The OCPN was discovered from the same "
        "OCEL used for this in-sample check."
    )


if __name__ == "__main__":
    main()
