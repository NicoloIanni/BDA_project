from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
SAMPLE_DATA_DIR = DATA_DIR / "samples"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
GRAPHS_DIR = OUTPUT_DIR / "graphs"
TABLES_DIR = OUTPUT_DIR / "tables"
REPORTS_DIR = OUTPUT_DIR / "reports"

# Dataset principale del progetto
ORDER_MANAGEMENT_DB = RAW_DATA_DIR / "order_management.sqlite"

# Alias comodo per indicare il dataset attualmente usato
MAIN_DATASET_DB = ORDER_MANAGEMENT_DB