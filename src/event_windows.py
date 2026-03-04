import pandas as pd

def add_event_windows(df):

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

    return df