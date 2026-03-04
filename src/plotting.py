import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def _prepare_compare(df):

    df_plot = df.reset_index(drop=True)

    gd30_daily = (
        df_plot[df_plot["ticker"].str.strip() == "GD30"]
        .groupby("fecha", as_index=False)["Vol Anual"]
        .mean()
        .rename(columns={"Vol Anual": "GD30_mean"})
    )

    prov_daily = (
        df_plot[df_plot["Prov"] == 1]
        .groupby("fecha", as_index=False)["Vol Anual"]
        .mean()
        .rename(columns={"Vol Anual": "Prov_mean"})
    )

    compare = (
        gd30_daily.merge(prov_daily, on="fecha", how="inner")
        .sort_values("fecha")
    )

    compare["GD30_smooth"] = compare["GD30_mean"].rolling(30, min_periods=15).mean()
    compare["Prov_smooth"] = compare["Prov_mean"].rolling(30, min_periods=15).mean()

    compare["Ratio_Prov_GD30"] = (
        compare["Prov_smooth"] / compare["GD30_smooth"]
    )

    return compare


def plot_volatility_compare(df):

    compare = _prepare_compare(df)

    fig, ax = plt.subplots(figsize=(14,7))

    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0f172a")

    ax.axhline(0.35, color="#d1d5db", linestyle="--", linewidth=1.5, alpha=0.8)

    color_gd30 = "#00FFFF"
    color_prov = "#FF8C00"

    ax.plot(compare["fecha"],
            compare["GD30_smooth"],
            color=color_gd30,
            linewidth=2.8,
            label="GD30")

    ax.plot(compare["fecha"],
            compare["Prov_smooth"],
            color=color_prov,
            linewidth=2.8,
            label="Promedio Provincial")

    ax.set_title("Volatilidad Anualizada Suavizada (MA 30)",
                 color="white", fontsize=16, fontweight="bold")

    ax.set_xlabel("Fecha", color="white")
    ax.set_ylabel("Volatilidad Anual", color="white")

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    ax.tick_params(axis='y', colors='white')
    ax.tick_params(axis='x', colors='white')

    for spine in ax.spines.values():
        spine.set_color("#334155")
        spine.set_linewidth(1.2)

    ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35, color="white")

    ax.legend(facecolor="black", edgecolor="white", labelcolor="white")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_ratio(df):

    compare = _prepare_compare(df)

    fig, ax = plt.subplots(figsize=(14,7))

    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("dimgray")

    ax.axhline(1, color="#FF8C00", linestyle="--", linewidth=1.5, alpha=0.8)

    color_ratio = "#00FFFF"

    ax.plot(compare["fecha"],
            compare["Ratio_Prov_GD30"],
            color=color_ratio,
            linewidth=2.8,
            label="Ratio Promedio Provincial / GD30 (MA30)")

    ax.set_title("Ratio de Volatilidad Suavizada (MA 30)", color="white")
    ax.set_xlabel("Fecha", color="white")
    ax.set_ylabel("Ratio", color="white")

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    ax.tick_params(axis='y', colors='white')
    ax.tick_params(axis='x', colors='white')

    for spine in ax.spines.values():
        spine.set_color("#334155")
        spine.set_linewidth(1.2)

    ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35, color="white")

    ax.legend(facecolor="black", edgecolor="white", labelcolor="white")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def plot_all_bonds(df):

    df_plot = df.sort_values(["ticker", "fecha"]).copy()

    # Suavizado por bono
    df_plot["Vol_smooth"] = (
        df_plot
        .groupby("ticker")["Vol Anual"]
        .transform(lambda x: x.rolling(30, min_periods=15).mean())
    )

    # Promedio provincial suavizado
    prov_daily = (
        df_plot[df_plot["Prov"] == 1]
        .groupby("fecha", as_index=False)["Vol Anual"]
        .mean()
        .rename(columns={"Vol Anual": "Prov_mean"})
    )

    prov_daily["Prov_smooth"] = (
        prov_daily["Prov_mean"]
        .rolling(30, min_periods=15)
        .mean()
    )

    fig, ax = plt.subplots(figsize=(14,7))

    fig.patch.set_facecolor("#0b0f19")
    ax.set_facecolor("#0f172a")

    tickers = df_plot["ticker"].unique()

    # Graficar cada bono
    for t in tickers:
        sub = df_plot[df_plot["ticker"] == t]
        ax.plot(sub["fecha"],
                sub["Vol_smooth"],
                linewidth=1.8,
                alpha=0.55)

    #  Línea blanca del promedio
    ax.plot(prov_daily["fecha"],
            prov_daily["Prov_smooth"],
            color="white",
            linewidth=3.2,
            label="Promedio Provincial")

    ax.set_title("Volatilidad Anualizada Suavizada (MA 30) - Todos los Bonos",
                 color="white", fontsize=16, fontweight="bold")

    ax.set_xlabel("Fecha", color="white")
    ax.set_ylabel("Volatilidad Anual", color="white")

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))

    ax.tick_params(axis='y', colors='white')
    ax.tick_params(axis='x', colors='white')

    for spine in ax.spines.values():
        spine.set_color("#334155")
        spine.set_linewidth(1.2)

    ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35, color="white")

    ax.legend(facecolor="black",
              edgecolor="white",
              labelcolor="white")

    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()