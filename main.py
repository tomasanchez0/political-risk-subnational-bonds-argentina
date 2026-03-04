from src.data_processing import build_panel
from src.event_windows import add_event_windows
from src.modeling import estimate_model
from src.plotting import plot_volatility_compare, plot_ratio, plot_all_bonds


def main():

    # 1. Construcción del panel
    df = build_panel()

    # 2. Agregar ventanas electorales
    df = add_event_windows(df)

    # 3. Estimación econométrica
    res = estimate_model(df)
    print(res)

    # 4. Gráficos
    plot_volatility_compare(df)
    plot_ratio(df)
    plot_all_bonds(df)


if __name__ == "__main__":
    main()