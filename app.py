import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st

# Chargement données et on les garde en mémoire vive pour pas que le site rame trop
@st.cache_data
def load_data():
    return pd.read_csv("ofgl-base-departements.zip", sep=",", low_memory=False)

# Prévention d'erreurs
try:
    df = load_data()
except FileNotFoundError:
    st.error("Le fichier 'ofgl-base-departements.zip' est introuvable. Contactez l'administrateur du site.")
    st.stop()

# Configuration page web
st.set_page_config(page_title="Analyse financière départementale", layout="wide", page_icon="📊")



# Indicateurs cochés par défaut à l'ouverture du site
indicateurs_fait_main = [
    "Capacité de désendettement (années)", 
    "Poids des AIS (%)"
]

# Catégories et sous-catégories d'indicateurs
# Mémo : dico_indicateurs est un dictionnaire dont les CLES sont les THEMES de nos indicateurs,
# les VALEURS sont des DICTIONNAIRES
# dont les CLES sont les SOUS PARTIES et
# les VALEURS sont nos INDICATEURS
dico_indicateurs = {
    "1️⃣ Épargne & Résultats": {
        "Indicateurs": [
            "Dépenses totales", "Dépenses d'investissement", "Dépenses de fonctionnement",
            "Recettes totales", "Recettes d'investissement", "Recettes de fonctionnement",
            "Epargne brute", "Epargne brute avant travaux en régie", "Epargne de gestion",
            "Epargne nette", "Capacité ou besoin de financement", "Fonds de roulement",
            "Variation du fonds de roulement"
        ]
    },
    "2️⃣ Recettes": {
        "Recettes de fonctionnement": [
            "Recettes de fonctionnement",
            "Attribution fonds de péreq. DMTO", "Autres dotations de fonctionnement",
            "Autres dotations et subventions", "Autres impôts et taxes", "CVAE", "Concours de l'Etat",
            "DMTO après péreq.", "DMTO avant péreq.", "Dotation globale de fonctionnement", "FMDI",
            "Fiscalité reversée", "Impôts et taxes", "Impôts locaux", "Produit des cessions d'immobilisations",
            "Prélèvement fonds de péreq. DMTO", "Péréquations et compensations fiscales", "TICPE", "TSCA",
            "TVA", "Ventes de biens et services", "Autres recettes de fonctionnement"
        ],
        "Recettes d'investissement": [
            "Recettes d'investissement",
            "Recettes d'investissement hors emprunts",
            "FCTVA", "Subventions reçues et participations", "DDEC", "Emprunts hors GAD", "Autres recettes d'investissement"
        ],
        "Totaux": [
            "Recettes totales",
            "Recettes totales hors emprunt"
        ]
    },
    "3️⃣ Dépenses": {
        "Dépenses de fonctionnement": [
            "Dépenses de fonctionnement",
            "Achats et charges externes", "Dépenses d'intervention", "Contributions aux SDIS",
            "Subventions aux personnes de droit privé", "Travaux en régie", "Frais de personnel",
            "Autres dépenses de fonctionnement"
        ],
        "Dépenses d'investissement": [
            "Dépenses d'investissement",
            "Dépenses d'investissement hors remb", "Dépenses d'équipement", "Subventions d'équipement versées",
            "Autres dépenses d'investissement"
        ],
        "Totaux": [
            "Dépenses totales", "Dépenses totales hors remb"
        ]
    },
    "4️⃣ Social & Solidarité": {
        "Indicateurs": [
            "Allocations APA", "Allocations PCH", "Allocations RSA", "Poids des AIS (%)", "CNSA", "Frais d'hébergement"
        ]
    },
    "5️⃣ Dette & Trésorerie": {
        "Indicateurs": [
            "Annuité de la dette", "Charges financières", "Remboursements d'emprunts hors GAD", "Emprunts hors GAD",
            "Fonds de soutien aux emprunts à risque", "Flux net de dette", "Encours de dette",
            "Encours de dette - Dettes bancaires et assimilées", "Encours de dette - Dépôts et cautionnements reçus",
            "Capacité de désendettement (années)", "Crédits de trésorerie", "Dépôts au Trésor"
        ]
    }
}


# On stocke les variables min_annee et max_annee
min_annee = int(df["Exercice"].min())
max_annee = int(df["Exercice"].max())



# Fonction de génération des graphiques dynamique
def generer_graphiques(df_plot, titre, indicateurs, par_habitant=False, afficher_les_deux=False):
    n = len(indicateurs)
    cols = 2 if n >= 2 else 1
    
    if n % 2 == 0:
        rows = n // cols
    else:
        rows = (n+1) // 2    # On aura un graphe "seul" en + en bas

    fig, axes = plt.subplots(rows, cols, figsize=(3*5, 5*5))
    fig.suptitle(titre, fontsize=25, fontweight="bold", y=1.02) 

    if rows == 1 and cols == 1:
        axes_flat = [axes]
    else:
        axes_flat = axes.flatten()

    for i, ind in enumerate(indicateurs):
        ax = axes_flat[i]
        
        if ind not in df_plot.columns:
            ax.set_title(f"{ind}\n(Données indisponibles)", fontsize=12, color="gray")
            continue
            
        sns.lineplot(data=df_plot, x="Exercice", y=ind, hue="Nom 2024 Département", marker="o", ax=ax, linewidth=3)
        
        titre_axe = f"{ind} (€/hab)" if par_habitant and not afficher_les_deux and ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)"] else ind
        ax.set_title(titre_axe, fontsize=15, fontweight="semibold")
        ax.set_xticks(df_plot["Exercice"].unique())
        
        if ind == "Capacité de désendettement (années)":
            ax.axhline(12, color="darkred", linestyle="--", linewidth=1, label="Surendettement avéré")
            ax.axhline(9, color="red", linestyle="--", linewidth=1, label="Surendettement trop élevé")
            ax.axhline(6, color="darkorange", linestyle="--", linewidth=1, label="Surendettement élevé")
            ax.axhline(3, color="green", linestyle="--", linewidth=1, label="Endettement maîtrisé")
            ajouter_etiquettes_desendettement(ax, df_plot)
            if ax.get_legend() is not None:
                ax.legend(loc="best", fontsize="small")

    for j in range(n, len(axes_flat)):
        fig.delaxes(axes_flat[j])

    plt.tight_layout()
    return fig


def ajouter_etiquettes_desendettement(ax, df_donnees):
    for index, row in df_donnees.iterrows():
        if row.get("Capacité de désendettement (années)", -1) == 0:
            vraie_valeur = row.get("Capacité de désendettement (vraie)", np.nan)
            if pd.isna(vraie_valeur) or np.isinf(vraie_valeur):
                vraie_valeur_texte = "inf"
            else:
                vraie_valeur_texte = f"{vraie_valeur:.1f}"
            
            ax.annotate(
                vraie_valeur_texte, xy=(row["Exercice"], 0), xytext=(0, 10),
                textcoords="offset points", ha="center", va="bottom",
                fontsize=10, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.5", fc="black", alpha=0.75, edgecolor="red", linewidth=3)
            )


# --- FONCTIONS DE TRAITEMENT ET ANALYSE ---

def analyser_un_departement(df, code_dep, intervalle_annees, indicateurs, par_habitant=False, afficher_les_deux=False):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min, annee_max = intervalle_annees
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   (df_temp["Code Insee 2024 Département"] == code_dep) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    idx_cols = ["Exercice", "Nom 2024 Département"]
    if "Population totale" in df_temp.columns: idx_cols.append("Population totale")

    pivot = df_temp[serie_filtre].pivot_table(index=idx_cols, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    if pivot.empty: return None, pd.DataFrame()
    
    nom_dep = pivot["Nom 2024 Département"].iloc[0]

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot.get("Epargne brute", 0) / 1000000
    pivot["Epargne nette (M€)"] = pivot.get("Epargne nette", 0) / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot.get("Dépenses de fonctionnement", 1)) * 100

    indicateurs_a_tracer = indicateurs.copy()
    
    if par_habitant and "Population totale" in pivot.columns:
        if afficher_les_deux:
            indicateurs_a_tracer = []
            for ind in indicateurs:
                indicateurs_a_tracer.append(ind)
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    nom_hab = f"{ind} (€/hab)"
                    pivot[nom_hab] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)
                    indicateurs_a_tracer.append(nom_hab)
        else:
            for ind in indicateurs:
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    pivot[ind] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)

    for ind in indicateurs_a_tracer:
        if ind not in pivot.columns:
            pivot[ind] = np.nan

    a_des_normalises = any("(€/hab)" in ind for ind in indicateurs_a_tracer)

    if afficher_les_deux and a_des_normalises:
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
        fig.suptitle(f"Analyse croisée de : {nom_dep}", fontsize=22, fontweight="bold", y=1.02)
        
        for ind in indicateurs_a_tracer:
            if ind in pivot.columns and pivot[ind].notna().any():
                if "(€/hab)" in ind:
                    sns.lineplot(data=pivot, x="Exercice", y=ind, marker="o", label=ind, ax=ax2, linewidth=3)
                else:
                    sns.lineplot(data=pivot, x="Exercice", y=ind, marker="o", label=ind, ax=ax1, linewidth=3)
                    
                    if ind == "Capacité de désendettement (années)":
                        ax1.axhline(12, color="darkred", linestyle="--", linewidth=1)
                        ax1.axhline(9, color="red", linestyle="--", linewidth=1)
                        ax1.axhline(6, color="darkorange", linestyle="--", linewidth=1)
                        ax1.axhline(3, color="green", linestyle="--", linewidth=1)

        ax1.set_title("Valeurs absolues", fontsize=15, fontweight="semibold")
        ax2.set_title("Valeurs normalisées (€/hab)", fontsize=15, fontweight="semibold")
        ax1.set_ylabel("Montant")
        ax2.set_ylabel("Montant (€/hab)")
        ax1.set_xlabel("Exercice")
        ax2.set_xlabel("Exercice")
        ax1.legend(loc='best', fontsize=10)
        ax2.legend(loc='best', fontsize=10)
        ax1.set_xticks(pivot["Exercice"].unique())
        ax2.set_xticks(pivot["Exercice"].unique())
        plt.tight_layout()
    else:
        fig, ax = plt.subplots(figsize=(14, 8))
        fig.suptitle(f"Comparaison d'indicateurs pour : {nom_dep}", fontsize=22, fontweight="bold", y=0.98)
        
        for ind in indicateurs_a_tracer:
            if ind in pivot.columns and pivot[ind].notna().any():
                sns.lineplot(data=pivot, x="Exercice", y=ind, marker="o", label=ind, ax=ax, linewidth=3)
                
                if ind == "Capacité de désendettement (années)":
                    ax.axhline(12, color="darkred", linestyle="--", linewidth=1)
                    ax.axhline(9, color="red", linestyle="--", linewidth=1)
                    ax.axhline(6, color="darkorange", linestyle="--", linewidth=1)
                    ax.axhline(3, color="green", linestyle="--", linewidth=1)

        ax.set_ylabel("Valeur")
        ax.set_xlabel("Exercice")
        ax.set_xticks(pivot["Exercice"].unique())
        ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=12)
        plt.tight_layout()

    colonnes = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = pivot[[c for c in colonnes if c in pivot.columns]].round(1).sort_values(by=["Exercice"])
    return fig, df_final


def departements_meme_strate(df, code_dep, mm_region=False):
    df_temp = df.copy()
    code_dep = str(code_dep)
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    
    if df_dep_cible.empty: return pd.DataFrame()

    strate = df_dep_cible["Strate population 2024"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0]
    
    serie_filtre = df_temp["Strate population 2024"] == strate
    if mm_region:
        serie_filtre = serie_filtre & (df_temp["Nom 2024 Région"] == region)

    df_resultat = df_temp.loc[serie_filtre, ["Code Insee 2024 Département", "Nom 2024 Département", "Nom 2024 Région"]].drop_duplicates()
    df_resultat = df_resultat[df_resultat["Code Insee 2024 Département"] != code_dep]
    return df_resultat.reset_index(drop=True)


def comparer_departements(df, liste_codes_dep, intervalle_annees, indicateurs, par_habitant=False, afficher_les_deux=False):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    annee_min, annee_max = intervalle_annees
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   (df_temp["Code Insee 2024 Département"].isin(liste_codes_dep)) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    idx_cols = ["Exercice", "Nom 2024 Département"]
    if "Population totale" in df_temp.columns: idx_cols.append("Population totale")

    pivot = df_temp[serie_filtre].pivot_table(index=idx_cols, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot.get("Epargne brute", 0) / 1000000
    pivot["Epargne nette (M€)"] = pivot.get("Epargne nette", 0) / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot.get("Dépenses de fonctionnement", 1)) * 100

    indicateurs_a_tracer = indicateurs.copy()
    
    if par_habitant and "Population totale" in pivot.columns:
        if afficher_les_deux:
            indicateurs_a_tracer = []
            for ind in indicateurs:
                indicateurs_a_tracer.append(ind)
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    nom_hab = f"{ind} (€/hab)"
                    pivot[nom_hab] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)
                    indicateurs_a_tracer.append(nom_hab)
        else:
            for ind in indicateurs:
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    pivot[ind] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)

    for ind in indicateurs_a_tracer:
        if ind not in pivot.columns:
            pivot[ind] = np.nan

    fig = generer_graphiques(pivot, "Analyse Financière Comparative", indicateurs_a_tracer, par_habitant and not afficher_les_deux, afficher_les_deux)

    colonnes = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = pivot[[c for c in colonnes if c in pivot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    return fig, df_final


def comparer_departement_strate(df, code_dep, intervalle_annees, indicateurs, meme_region=False, par_habitant=False, afficher_les_deux=False):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min, annee_max = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0]
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   (df_temp["Strate population 2024"] == strate) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                    
    idx_cols = ["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Nom 2024 Région"]
    if "Population totale" in df_temp.columns: idx_cols.append("Population totale")

    pivot = df_temp[serie_filtre].pivot_table(index=idx_cols, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot.get("Epargne brute", 0) / 1000000
    pivot["Epargne nette (M€)"] = pivot.get("Epargne nette", 0) / 1000000
    pivot["Poids des AIS (%)"] = ((pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)) / pivot.get("Dépenses de fonctionnement", 1)) * 100

    indicateurs_a_tracer = indicateurs.copy()
    
    if par_habitant and "Population totale" in pivot.columns:
        if afficher_les_deux:
            indicateurs_a_tracer = []
            for ind in indicateurs:
                indicateurs_a_tracer.append(ind)
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    nom_hab = f"{ind} (€/hab)"
                    pivot[nom_hab] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)
                    indicateurs_a_tracer.append(nom_hab)
        else:
            for ind in indicateurs:
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    pivot[ind] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)

    for ind in indicateurs_a_tracer:
        if ind not in pivot.columns:
            pivot[ind] = np.nan

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    df_autres = pivot[pivot["Code Insee 2024 Département"] != code_dep].copy()
    
    if meme_region:
        df_autres = df_autres[df_autres["Nom 2024 Région"] == region]

    cols_mean = [c for c in indicateurs_a_tracer + ["Capacité de désendettement (vraie)"] if c in df_autres.columns]
    df_moyenne = df_autres.groupby("Exercice")[cols_mean].mean().reset_index()
    
    label_moyenne = f"Moyenne Strate {strate}" + (" (même région)" if meme_region else " (France)")
    df_moyenne["Nom 2024 Département"] = label_moyenne
    
    df_plot = pd.concat([df_cible, df_moyenne], ignore_index=True)

    fig = generer_graphiques(df_plot, f"{nom_dep} comparé à la moyenne de sa strate", indicateurs_a_tracer, par_habitant and not afficher_les_deux, afficher_les_deux)

    colonnes = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = df_plot[[c for c in colonnes if c in df_plot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    return fig, df_final


def comparer_departement_strate_metro(df, code_dep, intervalle_annees, indicateurs, meme_region=False, par_habitant=False, afficher_les_deux=False):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min, annee_max = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0]
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   ((df_temp["Outre-mer"] == "Non") | (df_temp["Code Insee 2024 Département"] == code_dep)) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    idx_cols = ["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Strate population 2024", "Outre-mer", "Nom 2024 Région"]
    if "Population totale" in df_temp.columns: idx_cols.append("Population totale")

    pivot = df_temp[serie_filtre].pivot_table(index=idx_cols, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot.get("Epargne brute", 0) / 1000000
    pivot["Epargne nette (M€)"] = pivot.get("Epargne nette", 0) / 1000000
    pivot["Poids des AIS (%)"] = ((pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)) / pivot.get("Dépenses de fonctionnement", 1)) * 100

    indicateurs_a_tracer = indicateurs.copy()
    
    if par_habitant and "Population totale" in pivot.columns:
        if afficher_les_deux:
            indicateurs_a_tracer = []
            for ind in indicateurs:
                indicateurs_a_tracer.append(ind)
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    nom_hab = f"{ind} (€/hab)"
                    pivot[nom_hab] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)
                    indicateurs_a_tracer.append(nom_hab)
        else:
            for ind in indicateurs:
                if ind not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"] and ind in pivot.columns:
                    pivot[ind] = pivot.apply(lambda row: row[ind] / row["Population totale"] if pd.notnull(row.get("Population totale")) and row["Population totale"] > 0 else np.nan, axis=1)

    for ind in indicateurs_a_tracer:
        if ind not in pivot.columns:
            pivot[ind] = np.nan

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    cols_mean = [c for c in indicateurs_a_tracer + ["Capacité de désendettement (vraie)"] if c in pivot.columns]

    df_strate = pivot[(pivot["Strate population 2024"] == strate) & (pivot["Code Insee 2024 Département"] != code_dep)].copy()
    
    if meme_region:
        df_strate = df_strate[df_strate["Nom 2024 Région"] == region]

    df_moy_strate = df_strate.groupby("Exercice")[cols_mean].mean().reset_index()
    label_moyenne = f"Moyenne Strate {strate}" + (" (même région)" if meme_region else " (France)")
    df_moy_strate["Nom 2024 Département"] = label_moyenne

    df_metro = pivot[pivot["Outre-mer"] == "Non"].copy()
    df_moy_metro = df_metro.groupby("Exercice")[cols_mean].mean().reset_index()
    df_moy_metro["Nom 2024 Département"] = "Moyenne Métropole"
    
    df_plot = pd.concat([df_cible, df_moy_strate, df_moy_metro], ignore_index=True)

    fig = generer_graphiques(df_plot, f"{nom_dep} comparé à la moyenne de sa strate et à la moyenne de la métropole", indicateurs_a_tracer, par_habitant and not afficher_les_deux, afficher_les_deux)

    colonnes = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = df_plot[[c for c in colonnes if c in df_plot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    return fig, df_final 


# --- 5. L'INTERFACE GRAPHIQUE UTILISATEUR (STREAMLIT) ---

st.title("📊 Outil d'analyse financière de départements")
st.markdown("Bienvenue dans l'interface d'analyse. Choisissez une fonctionnalité du menu situé à votre gauche.")

liste_deps = sorted(df["Code Insee 2024 Département"].astype(str).unique())

st.markdown("""
    <style>
    div[role="radiogroup"] > label {
        margin-bottom: 20px !important; 
    }
    </style>
""", unsafe_allow_html=True)


# --- CRÉATION DU MENU ET SÉLECTION DES INDICATEURS ---

st.sidebar.markdown(
    "<h3 style='font-size: 22px; font-weight: bold; margin-bottom: 10px;'>Paramètres Globaux</h3>", 
    unsafe_allow_html=True
)

st.sidebar.markdown("**📂 Choix des indicateurs par thème :**")

indicateurs_choisis = []

# Création des menus déroulants (expanders) pour chaque grande catégorie
for main_cat, subcats in sorted(dico_indicateurs.items()):
    with st.sidebar.expander(main_cat, expanded=False):
        for subcat_name, indicators_list in subcats.items():
            
            if subcat_name != "Indicateurs":
                st.markdown(f"**{subcat_name}**")
            
            defauts_cat = [ind for ind in indicators_list if ind in indicateurs_fait_main]
            
            choix = st.multiselect(
                label=subcat_name,
                options=indicators_list,
                default=defauts_cat,
                key=f"ms_{main_cat}_{subcat_name}",
                label_visibility="collapsed" if subcat_name != "Indicateurs" else "visible" 
            )
            indicateurs_choisis.extend(choix)

# Nettoyage des doublons
indicateurs_choisis = list(dict.fromkeys(indicateurs_choisis))

st.sidebar.markdown("<br>", unsafe_allow_html=True)

par_habitant = st.sidebar.checkbox("Afficher les données en par habitant (€/hab)")

afficher_les_deux = False
if par_habitant:
    afficher_les_deux = st.sidebar.checkbox("Afficher côte à côte l'absolu ET le normalisé")

st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<h3 style='font-size: 22px; font-weight: bold; margin-bottom: 25px;'>Fonctionnalités</h3>", 
    unsafe_allow_html=True
)

menu = st.sidebar.radio(
    label="Menu caché",
    options=[
        "Analyser un seul département",
        "Recherche départements de même strate", 
        "Comparaison d'indicateurs financiers entre plusieurs départements", 
        "Département comparé à la moyenne de sa strate",
        "Département comparé à la moyenne de sa strate et à la moyenne de la métropole"
    ],
    label_visibility="collapsed" 
)

st.write("---")

if menu != "Recherche départements de même strate" and len(indicateurs_choisis) == 0:
    st.warning("⚠️ Veuillez sélectionner **au moins 1 indicateur** dans le panneau latéral de gauche pour générer les graphiques.")
    st.stop()


# --- CORPS DE LA PAGE SELON LE MENU ---

if menu == "Analyser un seul département":
    st.header("🎯 Analyse d'un seul département")
    dep = st.selectbox("Sélectionnez le département à analyser :", liste_deps)
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Lancer l'analyse"):
        fig, data = analyser_un_departement(df, dep, annees_sel, indicateurs_choisis, par_habitant, afficher_les_deux)
        if fig:
            st.pyplot(fig)
            st.subheader("📋 Données brutes")
            st.dataframe(data, use_container_width=True)
        else:
            st.warning("Aucune donnée trouvée pour ce département sur cet intervalle.")

elif menu == "Recherche départements de même strate":
    st.header("🔍 Départements de même strate")
    col1, col2 = st.columns(2)
    with col1:
        dep = st.selectbox("Sélectionnez le département ciblé :", liste_deps)
    with col2:
        meme_region = st.checkbox("Restreindre à la même région uniquement")
    
    if st.button("Chercher les correspondances"):
        resultat = departements_meme_strate(df, dep, meme_region)
        if not resultat.empty:
            st.success(f"Voici les départements trouvés ({len(resultat)}) :")
            st.dataframe(resultat, use_container_width=True)
        else:
            st.warning("Aucun résultat trouvé ou données manquantes.")

elif menu == "Comparaison d'indicateurs financiers entre plusieurs départements":
    st.header("⚖️ Comparaison entre plusieurs départements")
    
    deps_selectionnes = st.multiselect(
        "Sélectionnez les départements à comparer :", 
        liste_deps, 
        default=[liste_deps[0], liste_deps[1]] if len(liste_deps) >= 2 else liste_deps
    )
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Lancer la comparaison"):
        if len(deps_selectionnes) == 0:
            st.warning("⚠️ Veuillez sélectionner au moins un département pour lancer la comparaison.")
        else:
            fig, data = comparer_departements(df, deps_selectionnes, annees_sel, indicateurs_choisis, par_habitant, afficher_les_deux)
            st.pyplot(fig)
            st.subheader("📋 Données brutes")
            st.dataframe(data, use_container_width=True)

elif menu == "Département comparé à la moyenne de sa strate":
    st.header("📈 Département comparé à la moyenne de sa strate")
    col1, col2 = st.columns(2)
    with col1:
        dep = st.selectbox("Sélectionnez le département :", liste_deps)
    with col2:
        st.write("") 
        st.write("")
        meme_region = st.checkbox("Restreindre la moyenne de la strate à la même région")
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Générer l'analyse"):
        fig, data = comparer_departement_strate(df, dep, annees_sel, indicateurs_choisis, meme_region, par_habitant, afficher_les_deux)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)

elif menu == "Département comparé à la moyenne de sa strate et à la moyenne de la métropole":
    st.header("🏢 Département comparé à la moyenne de sa strate et à la moyenne de la métropole")
    col1, col2 = st.columns(2)
    with col1:
        dep = st.selectbox("Sélectionnez le département :", liste_deps)
    with col2:
        st.write("") 
        st.write("")
        meme_region = st.checkbox("Restreindre la moyenne de la strate à la même région")
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Générer l'analyse complète"):
        fig, data = comparer_departement_strate_metro(df, dep, annees_sel, indicateurs_choisis, meme_region, par_habitant, afficher_les_deux)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)
