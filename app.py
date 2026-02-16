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
import textwrap

plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
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

colorlist_warm70s = ['#368F8B','#AF7AA1','#7FA26B', '#D4A72C', '#B6C649','#EDC948','#A0CBE8',  '#EC7C2D',]
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
    plt.rcParams.update({
    "text.usetex": False,
    "font.family": "serif",
    "font.serif": ["Times New Roman", "Times", "DejaVu Serif"],
    "font.size": 16
    })
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
    # Radial limits (optional)
    ax.set_ylim(0, 20)   # adjust to your grading scale

    # Only even ticks
    ticks = np.arange(0, 21, 5)
    ax.set_yticks(ticks)
    ax.set_yticklabels([str(t) for t in ticks])
    for label in ax.get_yticklabels():
        label.set_alpha(0.4)
        label.set_fontsize(12)

    # Make them subtle
    ax.yaxis.grid(True, color="gray", alpha=0.2)
    ax.xaxis.grid(True, color="gray", alpha=0.2)

    # Outer colored band (background)
    theta = np.linspace(0, 2*np.pi, 100)
    outer_radius = ax.get_ylim()[1]
    inner_radius = outer_radius * 0.92

    theta = np.linspace(0, 2*np.pi, 100)
    maxr = ax.get_ylim()[1]
    
    ax.fill_between(theta, 0, maxr*0.33, color="#E15759", alpha=0.08, label = '_nolegend_')  
    ax.fill_between(theta, maxr*0.33, maxr*0.66, color="#F1CE63", alpha=0.08, label = '_nolegend_')  
    ax.fill_between(theta, maxr*0.66, maxr, color="#59A14F", alpha=0.08, label = '_nolegend_')  

    ax.fill_between(theta, inner_radius, outer_radius,
                    color="#5FA8A5", alpha=0.25, label = '_nolegend_') 

    for i, suf in enumerate(suffixes):
        lw = 3 if suf == last_suffix else 2
        ls = '-' if suf == last_suffix else '-.'
        alpha = 0.3 if suf == last_suffix else 0.1
        color = colorlist_warm70s[i % len(colorlist_warm70s)]

        ax.plot(angles, values_per_measurement[suf], color=color, lw=lw, ls=ls)
        ax.fill(angles, values_per_measurement[suf], color=color, alpha=alpha, label="_nolegend_", ls=ls)

    # Threshold line
    # ax.plot(angles, seuil, linestyle="--", color="black", lw=2)
    ax.spines["polar"].set_color("#5FA8A5")
    ax.spines["polar"].set_linewidth(3)
    # Remove default xticks
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])

    # Labels with red threshold logic
    rmax = ax.get_rmax()

    for angle, metric in zip(angles[:-1], metrics):
        final_val = row.get(f"{metric}_{last_suffix}", np.nan)
        seuil_val = row.get(f"{metric}_seuil", np.nan)

        is_below = pd.notna(final_val) and pd.notna(seuil_val) and final_val < seuil_val
        color = "#E15759" if is_below else "black"
        weight = "bold" if is_below else "normal"

        angle_deg = np.degrees(angle)
        rotation = angle_deg - 90
        if 180 < angle_deg < 327:
            rotation += 180


        max_len = 16
        metric_wrapped = "\n".join(textwrap.wrap(metric, width=max_len))        
        ax.text(angle, rmax * 1.15, metric_wrapped,
                color=color,
                fontweight=weight,
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

with st.expander("ℹ️ Aide pour préparer le fichier CSV"):
    st.markdown("## 📘 Format du fichier d’entrée (CSV)")

    st.markdown("""
    ### 🧩 Règles générales

    Votre fichier CSV doit contenir :

    **1) Une colonne élève**
    - `Prenom`

    **2) Des scores avec suffixes**
    - Chaque compétence doit être répérée avec `_1`, `_2`, `_3`, … (mesures dans le temps)
    - Exemple :  
    - `Lire et comprendre une consigne_1`  
    - `Lire et comprendre une consigne_2`

    **3) Une colonne seuil pour chaque compétence**
    - Nom exact : `Nom compétence_seuil`

    **4) Colonnes dates (optionnel mais recommandé)**
    - `Date_1`, `Date_2`, etc.
                
    ➡️ Le radar affiche automatiquement la dernière mesure (_n) et compare au seuil. 
    """
    )

    sample_data = {
        "Prenom": ["Alice", "Brahim"],
        "Lire et comprendre une consigne_1": [8, 9],
        "Lire et comprendre une consigne_2": [13, 8],
        "Lire et comprendre une consigne_seuil": [10,10],
        "Comprendre un texte lu seul (13 lignes)_1": [6, 9],
        "Comprendre un texte lu seul (13 lignes)_2": [10, 13],
        "Comprendre un texte lu seul (13 lignes)_seuil": [10, 10],
        "Comprendre un texte lu seul (23 lignes)_1": [1, 2],
        "Comprendre un texte lu seul (23 lignes)_2": [8, 3],
        "Comprendre un texte lu seul (23 lignes)_seuil": [10,10],
        "Ecrire un texte (13 lignes)_1": [11, 12],
        "Ecrire un texte (13 lignes)_2": [8, 13],
        "Ecrire un texte (13 lignes)_seuil": [10,10],
        "Date_1": ["2024-09-01", "2024-09-01"],
        "Date_2": ["Juin 2024", "Juin 2024"]
    }

    df_sample = pd.DataFrame(sample_data)
    st.markdown("### 🧪 Exemple de fichier")
    st.dataframe(df_sample)


    # Download button
    sample_csv = df_sample.to_csv(index=False).encode("utf-8")
    st.download_button(
        "📥 Télécharger un exemple de fichier CSV",
        sample_csv,
        "exemple_notes_eleves.csv",
        "text/csv"
    )

st.write("Téléversez votre fichier CSV de notes.")

uploaded_file = st.file_uploader("📂 Importer CSV", type=["csv"])

if uploaded_file:
    df = pd.read_csv(uploaded_file, sep=None, engine="python")
    st.success("✅ Fichier chargé !")


    students = df["Prenom"].tolist()

    # Student selector
    student = st.selectbox("👩‍🎓 Choisir un élève", students)
    row = df[df["Prenom"] == student].iloc[0]
    fig = radar_generic(row, df)
    st.pyplot(fig)


    zip_buffer = BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for _, row in df.iterrows():
            fig = radar_generic(row, df)

            # Save figure to memory
            img_bytes = BytesIO()
            fig.savefig(img_bytes, format="png", dpi=300, bbox_inches="tight")
            plt.close(fig)  # VERY IMPORTANT to avoid memory leaks

            img_bytes.seek(0)
            filename = f"{row['Prenom']}.png"

            # Write to zip
            zf.writestr(filename, img_bytes.read())

    # Download button
    st.download_button(
        "📥 Télécharger tous les graphiques (ZIP)",
        data=zip_buffer.getvalue(),
        file_name="student_radar_plots.zip",
        mime="application/zip"
)


