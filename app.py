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

# RADAR FUNCTION
def radar_generic(row, scores, names, dates):

    # Detect suffixes
    suffixes = sorted(
        set(int(m.group(1)) for c in row.index
            for m in [re.search(r'_(\d+)$', c)] if m)
    )
    last_suffix = max(suffixes)

    # Metrics present
    base_metrics = []
    for s in scores:
        for suf in suffixes:
            if f"{s}_{suf}" in row.index:
                base_metrics.append(s)
                break
    base_metrics = list(dict.fromkeys(base_metrics))

    # Collect values
    values_per_measurement = {}
    for suf in suffixes:
        values_per_measurement[suf] = [row[f"{m}_{suf}"] for m in base_metrics]

    seuil = [row[f"{m}_seuil"] for m in base_metrics]

    # Close loop
    def close(v): return v + v[:1]
    angles = np.linspace(0, 2*np.pi, len(base_metrics)+1)

    for suf in suffixes:
        values_per_measurement[suf] = close(values_per_measurement[suf])
    seuil = close(seuil)

    # Plot
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(polar=True))

    for suf, iter in zip(suffixes, range(len(suffixes))):
        lw = 3 if suf == last_suffix else 1.5
        ls = '-' if suf == last_suffix else ':'
        alpha = 0.25 if suf == last_suffix else 0.1
        ax.plot(angles, values_per_measurement[suf], 
                color=colorlist_warm70s[iter], lw=lw, ls = ls)
        ax.fill(angles, values_per_measurement[suf], 
                color=colorlist_warm70s[iter], alpha=alpha,  label="_nolegend_")

    # Remove default labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])

    # Curved rotated labels + threshold coloring
    rmax = ax.get_rmax()

    for angle, metric in zip(angles[:-1], base_metrics):

        final_val = row[f"{metric}_{last_suffix}"]
        seuil_val = row[f"{metric}_seuil"]
        color = "red" if final_val < seuil_val else "black"

        angle_deg = np.degrees(angle)
        rotation = angle_deg - 90
        if 180 < angle_deg < 327:
            rotation += 180

        ax.text(angle, rmax * 1.12, names[metric],
                color=color,
                fontweight="bold" if color=="red" else "normal",
                rotation=rotation,
                rotation_mode='anchor',
                ha='center', va='center')

    ax.legend(dates, bbox_to_anchor=(1.25,1.1))
    # ax.set_title(row["Prenom"])
    plt.tight_layout()

    return fig

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
    df = pd.read_csv(uploaded_file)
    st.success("✅ Fichier chargé")

    dates = df.loc[0, df.columns.str.contains("Date")].values
    students = df["Prenom"].tolist()

    student = st.selectbox("👩‍🎓 Choisir un élève", students)

    row = df[df["Prenom"] == student].iloc[0]
    fig = radar_generic(row, scores, names, dates)
    st.pyplot(fig)

    # ZIP DOWNLOAD
    if st.button("📥 Télécharger tous les radars (ZIP)"):
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w") as zf:
            for _, row in df.iterrows():
                fig = radar_generic(row, scores, names, dates)
                img_buffer = io.BytesIO()
                fig.savefig(img_buffer, format="png")
                zf.writestr(f"{row['Prenom']}.png", img_buffer.getvalue())
                plt.close(fig)

        st.download_button(
            "⬇ Télécharger ZIP",
            zip_buffer.getvalue(),
            "radars_eleves.zip",
            "application/zip"
        )
