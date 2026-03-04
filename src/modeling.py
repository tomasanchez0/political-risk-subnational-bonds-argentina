from linearmodels.panel import PanelOLS

def estimate_model(df):

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

    return res