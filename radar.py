import pandas as pd
import matplotlib.pyplot as plt
import matplotlib
import seaborn as sns
import numpy as np
import re

# %matplotlib inline
# %config InlineBackend.figure_format = 'svg'

# Configure Matplotlib fonts
plt.rcParams.update({
    "text.usetex": False,                # no LaTeX
    "font.family": "sans-serif",         # base font family
    "font.sans-serif": ["Helvetica"],    # prefer Helvetica
    "mathtext.fontset": "custom",        # custom math font
    "mathtext.rm": "Helvetica",          # math regular
    "mathtext.it": "Helvetica:italic",   # math italic
    "mathtext.bf": "Helvetica:bold",     # math bold
    "font.size": 15                       # global font size
})

matplotlib.rc('font', family='sans-serif') 
matplotlib.rc('font', serif='Helvetica Neue') 
matplotlib.rc('text', usetex='false') 


# define custom colormaps
norm = matplotlib.colors.Normalize(-1,1)

# Warm 70s color scheme
palette_20_warm70s_final = [
    '#368F8B', '#59A5A1', '#76B7B2', '#4E79A7', '#A0CBE8',
    '#EC7C2D', '#F28E2B', '#EDC948', '#D4A72C',
    '#E15759', '#C65D2E', '#B04A2F', '#9C755F',
    '#B6C649', '#C9B037', '#9AA14A', '#7FA26B', '#556B2F',
    '#7B4F6D', '#AF7AA1'
]



colors_warm70s = [[norm(-1.0), palette_20_warm70s_final[0]],
          [norm( 0.6), palette_20_warm70s_final[5]]]
cmap_warm70s = matplotlib.colors.LinearSegmentedColormap.from_list("", colors_warm70s)
colorlist_warm70s = ['#368F8B', '#EC7C2D', '#B6C649','#AF7AA1','#EDC948', '#D4A72C','#A0CBE8', '#7FA26B']

sns.set_palette(colorlist_warm70s)
sns.set_style('white')

# Visualize palette
# fig, ax = plt.subplots(figsize=(12, 2))
# for i, color in enumerate(palette_20_warm70s_final):
#     ax.add_patch(plt.Rectangle((i, 0), 1, 1, color=color))
#     ax.text(i + 0.5, -0.3, color, ha='center', va='top', fontsize=8, rotation=45)

# ax.set_xlim(0, len(palette_20_warm70s_final))
# ax.set_ylim(-0.5, 1)
# ax.axis('off')
# plt.show()


df = pd.read_csv("data.csv")

dates = df.loc[0,df.columns.str.contains('Date')].values

scores = [
    "Lire et comprendre une consigne",
    "Comprendre un texte lu seul (13 lignes)",
    "Ortographier correctement sous la dictee",
    "Copie un texte sans erreur de 4 phrases",
    "Rediger un texte de 4 phrases"
]

names = {
       "Lire et comprendre une consigne": "Lire et comprendre \nune consigne",
       "Comprendre un texte lu seul (13 lignes)": "Comprendre un texte \nlu seul (13 lignes)",
       "Ortographier correctement sous la dictee": "Ortographier correctement \nsous la dictee",
       "Copie un texte sans erreur de 4 phrases": "Copie un texte sans erreur \nde 4 phrases",
       "Rediger un texte de 4 phrases": "Rediger un texte \nde 4 phrases"
}
dates

plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman'] + plt.rcParams['font.serif']
plt.rcParams['mathtext.default'] = 'regular'
def radar_generic(row, scores, names, dates):

    # Detect available suffixes in dataframe
    suffixes = sorted(
        set(int(m.group(1)) for c in row.index
            for m in [re.search(r'_(\d+)$', c)] if m)
    )
    last_suffix = max(suffixes)

    # Build metric list that actually exists in data
    base_metrics = []
    for s in scores:
        for suf in suffixes:
            if f"{s}_{suf}" in row.index:
                base_metrics.append(s)
                break   # metric exists → keep it
    # Remove duplicates
    base_metrics = list(dict.fromkeys(base_metrics))

    # Collect values
    values_per_measurement = {}
    for suf in suffixes:
        values_per_measurement[suf] = [row[f"{m}_{suf}"] for m in base_metrics]

    seuil = [row[f"{m}_seuil"] for m in base_metrics]

    # Close radar loop
    def close(v): return v + v[:1]
    angles = np.linspace(0, 2*np.pi, len(base_metrics)+1)

    for suf in suffixes:
        values_per_measurement[suf] = close(values_per_measurement[suf])
    seuil = close(seuil)

    # Plot
    fig, ax = plt.subplots(figsize=(8,8), subplot_kw=dict(polar=True))

    for suf, iter in zip(suffixes, range(len(suffixes))):
        lw = 3 if suf == last_suffix else 1.5
        alpha = 0.25 if suf == last_suffix else 0.1
        ax.plot(angles, values_per_measurement[suf], 
                color=colorlist_warm70s[iter], lw=lw)
        ax.fill(angles, values_per_measurement[suf], 
                color=colorlist_warm70s[iter], alpha=alpha, label="_nolegend_")

    # Threshold
    # ax.plot(angles, seuil, linestyle="--", color=colors["seuil"], lw=2)

    # Axis labels
    # Remove default labels
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([])

    # Flip specific labels (top-left and bottom-right)
    # Identify indices by position in base_metrics
    # i_top_left = 1          # usually second label (adjust if needed)
    # i_bottom_right = 3       # usually fourth label (adjust if needed)

    # base_metrics[i_top_left], base_metrics[i_bottom_right] = \
    #     base_metrics[i_bottom_right], base_metrics[i_top_left]


    # Custom curved-style labels WITH red threshold coloring
    rmax = ax.get_rmax()

    for angle, metric in zip(angles[:-1], base_metrics):

        final_val = row[f"{metric}_{last_suffix}"]
        seuil_val = row[f"{metric}_seuil"]
        color = "red" if final_val < seuil_val else "black"

        angle_deg = np.degrees(angle)
        rotation = angle_deg - 90
        if 90 < angle_deg < 270:
            rotation += 180

        ax.text(angle, rmax * 1.12, names[metric],
                color=color,
                fontweight="bold" if color=="red" else "normal",
                rotation=rotation,
                rotation_mode='anchor',
                ha='center', va='center')

    # ax.set_title(row["Prenom"], fontsize=15)
    ax.legend(dates, bbox_to_anchor=(1.25,1.1))
    plt.tight_layout()
    plt.savefig(row["Prenom"] +'.png')

for _, row in df.iterrows():
    radar_generic(row, scores, names, dates)

