import pandas as pd
import numpy as np

def build_panel():

    df = pd.read_excel("data/raw/BonosP.xlsx")

    df["fecha"] = pd.to_datetime(df["fecha"])
    df["cierre"] = pd.to_numeric(df["cierre"], errors="coerce")

    # Evitar duplicados panel
    df = df.drop_duplicates(subset=["ticker", "fecha"])
    df = df.sort_values(["ticker", "fecha"]).reset_index(drop=True)

    # Tipo de cambio
    tc = pd.read_excel("data/raw/TC.xlsx")

    tc["fecha"] = pd.to_datetime(tc["fecha"])
    tc["tc"] = pd.to_numeric(tc["tc"], errors="coerce")
    tc = tc.sort_values("fecha")

    tc = tc.set_index("fecha").reindex(
        pd.date_range(tc["fecha"].min(), tc["fecha"].max(), freq="D")
    )

    tc["tc"] = tc["tc"].ffill()
    tc["d_tc"] = np.log(tc["tc"]).diff()
    tc["vol_tc_20"] = tc["d_tc"].rolling(20).std() * np.sqrt(252)

    tc = tc.reset_index().rename(columns={"index": "fecha"})

    df = df.merge(tc[["fecha", "tc", "vol_tc_20"]], on="fecha", how="left")

    # Conversión a USD
    df["close_usd"] = df["cierre"] / df["tc"]
    df = df.sort_values(["ticker", "fecha"])

    df["ret_ln"] = df.groupby("ticker")["close_usd"].transform(
        lambda x: np.log(x / x.shift(1))
    )

    window = 20

    df["vol_diaria_ret"] = df.groupby("ticker")["ret_ln"].transform(
        lambda x: x.rolling(window).std()
    )

    df["Vol Anual"] = df["vol_diaria_ret"] * np.sqrt(252)

    # Dummy provincial
    bonos_prov = ["PMM29D", "NDT25D", "CO26D", "BA37D"]
    df["Prov"] = df["ticker"].isin(bonos_prov).astype(int)

    # Riesgo país
    rp = pd.read_excel("data/raw/RiesgoP.xlsx")

    rp.columns = rp.columns.str.strip().str.lower()
    rp["fecha"] = pd.to_datetime(rp["fecha"], format="mixed")
    rp["pb"] = pd.to_numeric(rp["pb"], errors="coerce")
    rp = rp.sort_values("fecha")

    df = df.merge(rp[["fecha", "pb"]], on="fecha", how="left")
    df["pb"] = df["pb"].ffill()

    # Limpieza final
    df = df[
        df["Vol Anual"].notna() &
        df["vol_tc_20"].notna() &
        df["pb"].notna()
    ].copy()

    return df