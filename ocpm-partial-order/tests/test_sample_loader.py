from pathlib import Path

from ocpm_partial_order.io.sample_loader import (
    load_process_execution,
)


def test_order_management_toy_is_loaded() -> None:
    execution = load_process_execution(
        Path(
            "data/samples/"
            "order_management_toy_execution.json"
        )
    )

    assert (
        execution.execution_id
        == "order-management-toy-001"
    )

    assert len(execution.events) == 7
    assert "e1" in execution.event_ids()