

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from linearmodels.panel import PanelOLS
import matplotlib.ticker as mtick

#Se carga el panel principal

df = pd.read_excel("data/raw/BonosP.xlsx")

df["fecha"] = pd.to_datetime(df["fecha"])
df["cierre"] = pd.to_numeric(df["cierre"], errors="coerce")

# Evitar duplicados panel
df = df.drop_duplicates(subset=["ticker", "fecha"])
df = df.sort_values(["ticker", "fecha"]).reset_index(drop=True)


#Se agrega la variable de tipo de cambio.

tc = pd.read_excel("data/raw/TC.xlsx")

tc["fecha"] = pd.to_datetime(tc["fecha"])
tc["tc"] = pd.to_numeric(tc["tc"], errors="coerce")

tc = tc.sort_values("fecha")

#Serie diaria continua del tipo de cambio
tc = tc.set_index("fecha").reindex(
    pd.date_range(tc["fecha"].min(), tc["fecha"].max(), freq="D")
)

tc["tc"] = tc["tc"].ffill()

#Retorno log TC
tc["d_tc"] = np.log(tc["tc"]).diff()

#Volatilidad rolling TC (20 días)
tc["vol_tc_20"] = tc["d_tc"].rolling(20).std() * np.sqrt(252)

tc = tc.reset_index().rename(columns={"index": "fecha"})

# Merge con la base inicial
df = df.merge(tc[["fecha", "tc", "vol_tc_20"]], on="fecha", how="left")


#se transforman los bonos de pesos a dólares

df["close_usd"] = df["cierre"] / df["tc"]

df = df.sort_values(["ticker", "fecha"])

#Retorno log en USD
df["ret_ln"] = df.groupby("ticker")["close_usd"].transform(
    lambda x: np.log(x / x.shift(1))
)

#Volatilidad rolling 20 días en USD
window = 20

df["vol_diaria_ret"] = df.groupby("ticker")["ret_ln"].transform(
    lambda x: x.rolling(window).std()
)

df["Vol Anual"] = df["vol_diaria_ret"] * np.sqrt(252)


#Dummy provincial
bonos_prov = ["PMM29D", "NDT25D", "CO26D", "BA37D"]

df["Prov"] = df["ticker"].isin(bonos_prov).astype(int)

#ahora se trabaja sobre la variable de riesgo país y se agrega al panel.

rp = pd.read_excel("data/raw/RiesgoP.xlsx")

rp.columns = rp.columns.str.strip().str.lower()
rp["fecha"] = pd.to_datetime(rp["fecha"], format="mixed")
rp["pb"] = pd.to_numeric(rp["pb"], errors="coerce")

rp = rp.sort_values("fecha")

df = df.merge(rp[["fecha", "pb"]], on="fecha", how="left")

df["pb"] = df["pb"].ffill()


#Limpieza final del panel.

df = df[
    df["Vol Anual"].notna() &
    df["vol_tc_20"].notna() &
    df["pb"].notna()
].copy()

# dato extra para ver rápidamente en que medida los provinciales siguen a los soberanos.
pivot_ret = df.pivot(index="fecha", columns="ticker", values="ret_ln")

pivot_ret.corr()

#A partir de acá se construye el ratio provincial/soberano.

df["Tipo"] = df["Prov"].map({0: "Soberano", 1: "Provincial"})

df.groupby("Tipo")[["ret_ln", "Vol Anual"]].mean()

#Resumen estadístico.
stats_bonos = df.groupby("ticker").agg(
    obs=("ret_ln", "count"),
    ret_medio=("ret_ln", "mean"),
    ret_std=("ret_ln", "std"),
    ret_min=("ret_ln", "min"),
    ret_max=("ret_ln", "max"),
    vol_promedio=("Vol Anual", "mean"),
    vol_min=("Vol Anual", "min"),      # ← agregado
    vol_max=("Vol Anual", "max"),
    precio_prom_usd=("close_usd", "mean")
)

stats_bonos.sort_values("vol_promedio", ascending=False)

#se ajustan las dummys por ventanas electorales específicas.

eventos = {
    "PASO23_win": ("2023-08-13", 20, 15),
    "GEN23_win":  ("2023-10-22", 20, 40),
    "BAL23_win":  ("2023-11-19", 20, 50),
    "LEG25_win":  ("2025-10-26", 30, 30),
}

for name in eventos:
    df[name] = 0

for name, (fecha, back, forward) in eventos.items():
    fecha = pd.Timestamp(fecha)
    inicio = fecha - pd.Timedelta(days=back)
    fin = fecha + pd.Timedelta(days=forward)

    mask = (df["fecha"] >= inicio) & (df["fecha"] <= fin)

    for prev in eventos:
        if prev == name:
            break
        mask &= (df[prev] == 0)

    df.loc[mask, name] = 1

#Se estima por OLS con FE

df_panel = df.set_index(["ticker", "fecha"]).sort_index()

model = PanelOLS.from_formula(
    "Q('Vol Anual') ~ \
     PASO23_win + PASO23_win:Prov + \
     GEN23_win + GEN23_win:Prov + \
     BAL23_win + BAL23_win:Prov + \
     LEG25_win + LEG25_win:Prov + \
      pb + EntityEffects",
    data=df_panel
)

res = model.fit(cov_type="driscoll-kraay", bandwidth=30)
print(res)

df_plot = df.reset_index(drop=True)

# GD30 separado
gd30_daily = (
    df_plot[df_plot["ticker"].str.strip() == "GD30"]
    .groupby("fecha", as_index=False)["Vol Anual"]
    .mean()
    .rename(columns={"Vol Anual": "GD30_mean"})
)

#Promedio provincial para el gráfico
prov_daily = (
    df_plot[df_plot["Prov"] == 1]
    .groupby("fecha", as_index=False)["Vol Anual"]
    .mean()
    .rename(columns={"Vol Anual": "Prov_mean"})
)

#Merge solo en fechas coincidentes para generar los gráficos.
compare = (
    pd.merge(gd30_daily, prov_daily, on="fecha", how="inner")
      .sort_values("fecha")
)

#Rolling 30 días.
compare["GD30_smooth"] = compare["GD30_mean"].rolling(30, min_periods=15).mean()
compare["Prov_smooth"] = compare["Prov_mean"].rolling(30, min_periods=15).mean()

# Ratio
compare["Ratio_Prov_GD30"] = (
    compare["Prov_smooth"] / compare["GD30_smooth"]
)

compare = compare.dropna(subset=["Ratio_Prov_GD30"])

#Gráfico de la evolución vol anual provincial y soberana.

fig, ax = plt.subplots(figsize=(14,7))

# Fondo
fig.patch.set_facecolor("#0b0f19")
ax.set_facecolor("#0f172a")

# Línea base (podés cambiar el nivel si querés)
ax.axhline(0.35, color="#d1d5db", linestyle="--", linewidth=1.5, alpha=0.8)

# Colores
color_gd30 = "#00FFFF"
color_prov = "#FF8C00"

# Series suavizadas MA30
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

# Títulos
ax.set_title("Volatilidad Anualizada Suavizada (MA 30)",
             color="white", fontsize=16, fontweight="bold")
ax.set_xlabel("Fecha", color="white")
ax.set_ylabel("Volatilidad Anual", color="white")

# Fechas
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.xticks(rotation=45, color="white")

# Ejes
ax.tick_params(axis='y', colors='white')
ax.tick_params(axis='x', colors='white')

for spine in ax.spines.values():
    spine.set_color("#334155")
    spine.set_linewidth(1.2)

# Grid
ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35, color="white")

plt.yticks(color="white")

# Leyenda
ax.legend(facecolor="black", edgecolor="white", labelcolor="white")

plt.tight_layout()
plt.show()

#Gráfico del Ratio
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
plt.xticks(rotation=45, color="white")

ax.tick_params(axis='y', colors='white')
ax.tick_params(axis='x', colors='white')

for spine in ax.spines.values():
    spine.set_color("#334155")
    spine.set_linewidth(1.2)

ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35, color="white")

plt.yticks(color="white")
plt.legend(facecolor="black", edgecolor="white", labelcolor="white")

plt.tight_layout()
plt.show()

#Media móvil por bono
df_plot = df_plot.sort_values(["ticker", "fecha"])

df_plot["Vol_smooth"] = (
    df_plot
    .groupby("ticker")["Vol Anual"]
    .transform(lambda x: x.rolling(30, min_periods=15).mean())
)

#Media total diaria (entre bonos)
mean_daily = (
    df_plot
    .groupby("fecha", as_index=False)["Vol_smooth"]
    .mean()
    .rename(columns={"Vol_smooth": "Vol_mean_total"})
)

#Volatilidad anual de cada bono por separado en un gráfico.

fig, ax = plt.subplots(figsize=(14,7))

# Fondo
fig.patch.set_facecolor("#0b0f19")
ax.set_facecolor("#0f172a")

# Colormap automático para diferenciar bonos
tickers = df_plot["ticker"].unique()

for t in tickers:
    sub = df_plot[df_plot["ticker"] == t]
    ax.plot(sub["fecha"],
            sub["Vol_smooth"],
            linewidth=2.0,
            alpha=0.6,
            label=t)

# Línea media total destacada
ax.plot(mean_daily["fecha"],
        mean_daily["Vol_mean_total"],
        color="#FFFFFF",
        linewidth=3,
        label="Media Total Bonos")

# Títulos
ax.set_title("Volatilidad Anualizada Suavizada (MA 30) - Todos los Bonos",
             color="white", fontsize=16, fontweight="bold")
ax.set_xlabel("Fecha", color="white")
ax.set_ylabel("Volatilidad Anual", color="white")

# Fechas
ax.xaxis.set_major_locator(mdates.AutoDateLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
plt.xticks(rotation=45, color="white")

# Ejes
ax.tick_params(axis='y', colors='white')
ax.tick_params(axis='x', colors='white')

for spine in ax.spines.values():
    spine.set_color("#334155")
    spine.set_linewidth(1.2)

# Grid
ax.grid(True, linestyle="--", linewidth=0.7, alpha=0.35, color="white")

plt.yticks(color="white")

# Leyenda más compacta
ax.legend(facecolor="black",
          edgecolor="white",
          labelcolor="white",
          fontsize=9,
          ncol=2)

plt.tight_layout()
plt.show()