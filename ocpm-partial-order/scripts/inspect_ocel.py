from ocpm_partial_order.config import MAIN_DATASET_DB
from ocpm_partial_order.io.ocel_loader import load_ocel2_sqlite


def main() -> None:
    ocel = load_ocel2_sqlite(MAIN_DATASET_DB)

    print("OCEL Order Management caricato correttamente")
    print(ocel)

    print("\nColonne tabella eventi:")
    print(ocel.events.columns.tolist())

    print("\nColonne tabella oggetti:")
    print(ocel.objects.columns.tolist())

    print("\nColonne tabella relazioni:")
    print(ocel.relations.columns.tolist())

    print("\nPrimi eventi:")
    print(ocel.events.head())

    print("\nPrimi oggetti:")
    print(ocel.objects.head())

    print("\nPrime relazioni evento-oggetto:")
    print(ocel.relations.head())

    print("\nStatistiche generali")
    print("Numero eventi:", len(ocel.events))
    print("Numero oggetti:", len(ocel.objects))
    print("Numero relazioni evento-oggetto:", len(ocel.relations))

    if "ocel:activity" in ocel.events.columns:
        print(
            "Numero tipi di evento:",
            ocel.events["ocel:activity"].nunique(),
        )

    if "ocel:type" in ocel.objects.columns:
        print(
            "Numero tipi di oggetto:",
            ocel.objects["ocel:type"].nunique(),
        )


if __name__ == "__main__":
    main()