from importlib.metadata import version

from ocpm_partial_order.config import MAIN_DATASET_DB

PACKAGES = [
    "pm4py",
    "pandas",
    "networkx",
    "matplotlib",
    "graphviz",
    "pytest",
]


def main() -> None:
    print("Controllo ambiente\n")

    for package in PACKAGES:
        try:
            installed_version = version(package)
            print(f"[OK] {package}: {installed_version}")
        except Exception as exc:
            print(f"[ERRORE] {package}: {exc}")

    print("\nControllo dataset")

    if MAIN_DATASET_DB.exists():
        print(f"[OK] Order Management: {MAIN_DATASET_DB}")
    else:
        print(f"[ERRORE] Dataset non trovato: {MAIN_DATASET_DB}")


if __name__ == "__main__":
    main()