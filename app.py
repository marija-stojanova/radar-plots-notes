import matplotlib
matplotlib.use("Agg")

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import re
import io
import zipfile
from io import BytesIO

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans"],   # Helvetica not on Linux
    "font.size": 14
})

# COLORS
norm = matplotlib.colors.Normalize(-1,1)

palette_20_warm70s_final = [
    '#368F8B', '#59A5A1', '#76B7B2', '#4E79A7', '#A0CBE8',
    '#EC7C2D', '#F28E2B', '#EDC948', '#D4A72C',
    '#E15759', '#C65D2E', '#B04A2F', '#9C755F',
    '#B6C649', '#C9B037', '#9AA14A', '#7FA26B', '#556B2F',
    '#7B4F6D', '#AF7AA1'
]

colorlist_warm70s = ['#368F8B', '#EC7C2D', '#B6C649','#AF7AA1','#EDC948', '#D4A72C','#A0CBE8', '#7FA26B']
sns.set_palette(colorlist_warm70s)
sns.set_style('white')

def detect_suffixes(df):
    return sorted(set(
        int(m.group(1))
        for c in df.columns
        for m in [re.search(r'_(\d+)$', c)]
        if m
    ))

def detect_metrics(df):
    metrics = sorted(set(
        re.sub(r'_\d+$', '', c)
        for c in df.columns if re.search(r'_\d+$', c)
    ))
    # Keep only metrics with thresholds
    return [m for m in metrics if f"{m}_seuil" in df.columns]

# RADAR FUNCTION
def radar_generic(row, df):
    suffixes = detect_suffixes(df)
    metrics  = detect_metrics(df)
    last_suffix = max(suffixes)

    # Collect values (handle missing metrics gracefully)
    values_per_measurement = {}
    for suf in suffixes:
        vals = []
        for m in metrics:
            col = f"{m}_{suf}"
            vals.append(row[col] if col in row and pd.notna(row[col]) else np.nan)
        values_per_measurement[suf] = vals

    # Thresholds
    seuil = [row[f"{m}_seuil"] for m in metrics]

    # Close radar loop
    def close(v): return v + v[:1]
    angles = np.linspace(0, 2*np.pi, len(metrics)+1)

    for suf in suffixes:
        values_per_measurement[suf] = close(values_per_measurement[suf])
    seuil = close(seuil)

    # Plot
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(polar=True))

    for i, suf in enumerate(suffixes):
        lw = 3 if suf == last_suffix else 2
        ls = '-' if suf == last_suffix else '-.'
        alpha = 0.3 if suf == last_suffix else 0.1
        color = colorlist_warm70s[i % len(colorlist_warm70s)]

        ax.plot(angles, values_per_measurement[suf], color=color, lw=lw, ls=ls)
        ax.fill(angles, values_per_measurement[suf], color=color, alpha=alpha, label="_nolegend_", ls=ls)

    # Threshold line
    # ax.plot(angles, seuil, linestyle="--", color="black", lw=2)

    # Remove default xticks
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])

    # Labels with red threshold logic
    rmax = ax.get_rmax()

    for angle, metric in zip(angles[:-1], metrics):
        final_val = row.get(f"{metric}_{last_suffix}", np.nan)
        seuil_val = row.get(f"{metric}_seuil", np.nan)
        color = "red" if pd.notna(final_val) and pd.notna(seuil_val) and final_val < seuil_val else "black"

        angle_deg = np.degrees(angle)
        rotation = angle_deg - 90
        if 180 < angle_deg < 327:
            rotation += 180

        ax.text(angle, rmax * 1.15, metric,
                color=color,
                fontweight="bold" if color=="red" else "normal",
                rotation=rotation,
                rotation_mode='anchor',
                ha='center', va='center')

    # Legend (dates)
    dates = df.loc[0, df.columns.str.contains("Date")].values
    ax.legend(dates, bbox_to_anchor=(1.25,1.1))

    plt.tight_layout()
    # plt.savefig(f"{row['Prenom']}.png")

    return(fig)    


# STREAMLIT UI
st.title("📊 Radar d’évaluation des élèves")
st.write("Téléversez votre fichier CSV de notes.")

uploaded_file = st.file_uploader("📂 Importer CSV", type=["csv"])

scores = [
    "Lire et comprendre une consigne",
    "Comprendre un texte lu seul (13 lignes)",
    "Ortographier correctement sous la dictee",
    "Copie un texte sans erreur de 4 phrases",
    "Rediger un texte de 4 phrases"
]

names = {
    "Lire et comprendre une consigne": "Lire et comprendre\nune consigne",
    "Comprendre un texte lu seul (13 lignes)": "Comprendre un texte\nlu seul (13 lignes)",
    "Ortographier correctement sous la dictee": "Orthographier\nsous la dictée",
    "Copie un texte sans erreur de 4 phrases": "Copie sans erreur\nde 4 phrases",
    "Rediger un texte de 4 phrases": "Rédiger un texte\nde 4 phrases"
}

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=None, engine="python")
    st.success("✅ Fichier chargé !")

    # for _, row in df.iterrows():
    #     radar_generic(row, df)
    #     st.image(f"{row['Prenom']}.png")

    students = df["Prenom"].tolist()

    # Student selector
    student = st.selectbox("👩‍🎓 Choisir un élève", students)
    # student = st.selectbox("👩‍🎓 Choisir un élève", students)
    row = df[df["Prenom"] == student].iloc[0]
    fig = radar_generic(row, df)
    st.pyplot(fig)


    # row = df[df["Prenom"] == student].iloc[0]
    # fig = radar_generic(row, scores, names, dates)
    # st.pyplot(fig)


    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        for _, row in df.iterrows():
            radar_generic(row, df)
            fname = f"{row['Prenom']}.png"
            zf.write(fname)

    st.download_button(
        "📥 Télécharger tous les graphiques (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="student_radar_plots.zip",
        mime="application/zip"
    )

