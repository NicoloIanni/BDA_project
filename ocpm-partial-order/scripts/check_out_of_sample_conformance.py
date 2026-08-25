from pm4py.util import constants

from ocpm_partial_order.config import (
    MAIN_DATASET_DB,
)
from ocpm_partial_order.conformance import (
    DEFAULT_NOISE_THRESHOLD,
    DEFAULT_TRAIN_RATIO,
    evaluate_structural_holdout,
)
from ocpm_partial_order.io.ocel_loader import (
    load_ocel2_sqlite,
)


def print_evaluation(evaluation) -> None:
    split = evaluation.split
    train = evaluation.train_conformance
    test = evaluation.test_conformance

    print("\n" + "=" * 72)
    print(
        "OBJECT TYPE:",
        evaluation.object_type,
    )
    print("=" * 72)

    print("\nLeakage-free split")
    print(
        "- components:",
        split.component_count,
    )
    print(
        "- training components:",
        split.train_component_count,
    )
    print(
        "- test components:",
        split.test_component_count,
    )
    print(
        "- training cases:",
        split.train_case_count,
    )
    print(
        "- test cases:",
        split.test_case_count,
    )
    print(
        "- effective training ratio:",
        split.effective_train_ratio,
    )
    print(
        "- training events:",
        split.train_event_count,
    )
    print(
        "- test events:",
        split.test_event_count,
    )
    print(
        "- training variants:",
        split.train_variant_count,
    )
    print(
        "- test variants:",
        split.test_variant_count,
    )
    print(
        "- unseen test variants:",
        split.unseen_test_variant_count,
    )

    print("\nPetri net")
    print(
        "- places:",
        evaluation.place_count,
    )
    print(
        "- transitions:",
        evaluation.transition_count,
    )
    print(
        "- arcs:",
        evaluation.arc_count,
    )
    print(
        "- noise threshold:",
        evaluation.noise_threshold,
    )

    print("\nTraining conformance")
    print(
        "- traces:",
        train.trace_count,
    )
    print(
        "- fitting traces:",
        train.fitting_trace_count,
    )
    print(
        "- non-fitting traces:",
        train.non_fitting_trace_count,
    )
    print(
        "- average fitness:",
        train.average_trace_fitness,
    )
    print(
        "- missing tokens:",
        train.total_missing_tokens,
    )
    print(
        "- remaining tokens:",
        train.total_remaining_tokens,
    )
    print(
        "- precision:",
        evaluation.train_precision,
    )
    print(
        "- generalization:",
        evaluation.train_generalization,
    )

    print("\nOut-of-sample test")
    print(
        "- traces:",
        test.trace_count,
    )
    print(
        "- fitting traces:",
        test.fitting_trace_count,
    )
    print(
        "- non-fitting traces:",
        test.non_fitting_trace_count,
    )
    print(
        "- fitting percentage:",
        test.fitting_percentage,
    )
    print(
        "- average fitness:",
        test.average_trace_fitness,
    )
    print(
        "- missing tokens:",
        test.total_missing_tokens,
    )
    print(
        "- remaining tokens:",
        test.total_remaining_tokens,
    )
    print(
        "- precision:",
        evaluation.test_precision,
    )
    print(
        "- generalization:",
        evaluation.test_generalization,
    )
    print(
        "- model simplicity:",
        evaluation.model_simplicity,
    )


def main() -> None:
    constants.SHOW_PROGRESS_BAR = False

    print("=" * 72)
    print(
        "OUT-OF-SAMPLE COMPONENT VALIDATION"
    )
    print("=" * 72)
    print("Dataset:", MAIN_DATASET_DB)
    print(
        "Target training ratio:",
        DEFAULT_TRAIN_RATIO,
    )
    print(
        "Noise threshold:",
        DEFAULT_NOISE_THRESHOLD,
    )

    ocel = load_ocel2_sqlite(
        MAIN_DATASET_DB
    )

    print("OCEL loaded.")

    evaluations = (
        evaluate_structural_holdout(
            ocel=ocel,
            train_ratio=(
                DEFAULT_TRAIN_RATIO
            ),
            noise_threshold=(
                DEFAULT_NOISE_THRESHOLD
            ),
        )
    )

    for evaluation in evaluations:
        print_evaluation(
            evaluation
        )

    total_test_traces = sum(
        evaluation.test_conformance
        .trace_count
        for evaluation in evaluations
    )

    total_fitting_traces = sum(
        evaluation.test_conformance
        .fitting_trace_count
        for evaluation in evaluations
    )

    weighted_fitness = (
        sum(
            evaluation.test_conformance
            .average_trace_fitness
            * evaluation.test_conformance
            .trace_count
            for evaluation in evaluations
        )
        / total_test_traces
    )

    total_missing_tokens = sum(
        evaluation.test_conformance
        .total_missing_tokens
        for evaluation in evaluations
    )

    total_remaining_tokens = sum(
        evaluation.test_conformance
        .total_remaining_tokens
        for evaluation in evaluations
    )

    print("\n" + "=" * 72)
    print("OVERALL OUT-OF-SAMPLE TEST")
    print("=" * 72)
    print(
        "Test traces:",
        total_test_traces,
    )
    print(
        "Fitting traces:",
        total_fitting_traces,
    )
    print(
        "Non-fitting traces:",
        (
            total_test_traces
            - total_fitting_traces
        ),
    )
    print(
        "Weighted average fitness:",
        weighted_fitness,
    )
    print(
        "Missing tokens:",
        total_missing_tokens,
    )
    print(
        "Remaining tokens:",
        total_remaining_tokens,
    )

    print("\nMethodological note:")
    print(
        "Training and test do not share "
        "case IDs or event IDs."
    )
    print(
        "The items split is component-aware "
        "and is not a strict future-only split."
    )
    print(
        "Metrics concern separate object-type "
        "Petri net components."
    )
    print(
        "They do not constitute globally "
        "synchronized object-centric "
        "conformance."
    )


if __name__ == "__main__":
    main()
