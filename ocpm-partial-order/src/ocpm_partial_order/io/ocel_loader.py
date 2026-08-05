# src/ocpm_partial_order/io/ocel_loader.py

from pathlib import Path

import pm4py


def load_ocel2_sqlite(path: str | Path):
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(
            f"Dataset non trovato: {path.resolve()}"
        )

    if path.suffix.lower() != ".sqlite":
        raise ValueError(
            f"Formato non supportato: {path.suffix}. "
            "È richiesto un file .sqlite."
        )

    return pm4py.read_ocel2_sqlite(str(path))