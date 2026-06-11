import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st



# Chargement données et on les garde en mémoire vive
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



# Indicateurs que l'on code
indicateurs_fait_main = [
    "Capacité de désendettement (années)", 
    "Poids des AIS (%)"
]

# --- Fonction de catégorisation ---
def categoriser_indicateur(ind):
    ind_l = ind.lower()
    
    # 1. Épargne (Très spécifique)
    if any(x in ind_l for x in ["épargne", "epargne", "désendettement", "fonds de roulement", "financement", "besoin"]):
        return "1️⃣ Épargne & Résultats"
        
    # 4. Social (Placé en haut pour capter "frais d'hébergement" avant le mot "frais")
    elif any(x in ind_l for x in ["allocation", "ais", "cnsa", "hébergement", "social"]):
        return "4️⃣ Social & Solidarité"
        
    # 5. Dette & Trésorerie (Placé avant dépenses pour capter "charges financières" ou "dépôts")
    elif any(x in ind_l for x in ["dette", "emprunt", "trésorerie", "financière", "financier", "gad", "annuité", "dépôt", "trésor"]):
        return "5️⃣ Dette & Trésorerie"
        
    # 2. Recettes (Ajout de "concours" et "subventions reçues")
    elif any(x in ind_l for x in ["recette", "dotation", "impôt", "taxe", "tva", "dmto", "cvae", "ticpe", "tsca", "fiscal", "fctva", "fmdi", "péreq", "compensation", "vente", "produit", "concours", "subventions reçues"]):
        return "2️⃣ Recettes & Fiscalité"
        
    # 3. Dépenses (Prend tout le reste des charges, dont les "subventions" classiques versées)
    elif any(x in ind_l for x in ["dépense", "achat", "frais", "subvention", "personnel", "sdis", "ddec", "travaux", "charge", "intervention"]):
        return "3️⃣ Dépenses"
        
    # Sécurité au cas où l'OFGL ajoute un nouveau mot inconnu l'année prochaine
    else:
        return "6️⃣ Autres"

liste_agregats = [elt for elt in df["Agrégat"]]

# Tri personnalisé par catégorie puis alphabétique
indiacteurs = sorted(list(set(indicateurs_fait_main + liste_agregats)), key=lambda x: (categoriser_indicateur(x), x))

# On stocke les variables min_annee et max_annee
min_annee = int(df["Exercice"].min())
max_annee = int(df["Exercice"].max())



# Fonction de génération des graphiques dynamique
def generer_graphiques(df_plot, titre, indicateurs, par_habitant=False, afficher_les_deux=False):
    # Calcul dynamique des lignes et colonnes en fonction du nombre d'indicateurs
    n = len(indicateurs)
    
    # On force l'affichage à 2 colonnes maximum par ligne pour garder un beau dashboard
    cols = 2 if n >= 2 else 1
    rows = (n + cols - 1) // cols
    
    # La hauteur de la figure s'adapte au nombre de lignes (5 par ligne)
    fig, axes = plt.subplots(rows, cols, figsize=(16, 5 * rows))
    fig.suptitle(titre, fontsize=25, fontweight="bold", y=1.02) 

    # On sécurise l'aplatissement (gère le fait qu'il y ait 1, 2 ou 10 graphiques)
    if rows == 1 and cols == 1:
        axes_flat = [axes]
    else:
        axes_flat = axes.flatten()

    for i, ind in enumerate(indicateurs):
        ax = axes_flat[i]
        
        # Prévention d'erreurs
        if ind not in df_plot.columns:
            ax.set_title(f"{ind}\n(Données indisponibles)", fontsize=12, color="gray")
            continue
            
        sns.lineplot(data=df_plot, x="Exercice", y=ind, hue="Nom 2024 Département", marker="o", ax=ax, linewidth=3)
        
        # Adaptation du titre si par_habitant est coché et qu'on ne les affiche pas en double (sinon le nom contient déjà la mention)
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

    # Nettoyage des cases vides (ex: 3 indicateurs sur une grille 2x2 ou 5 sur une grille 3x2)
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



# Nos fonctions correspondant aux différentes fonctionalités du site

def analyser_un_departement(df, code_dep, intervalle_annees, indicateurs, par_habitant=False, afficher_les_deux=False):
    """Nouvelle fonction pour tracer TOUS les indicateurs d'un seul département SUR LE MÊME GRAPHIQUE"""
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

    # --- CRÉATION DU GRAPHIQUE UNIQUE SUPERPOSÉ (MISE À JOUR) ---
    a_des_normalises = any("(€/hab)" in ind for ind in indicateurs_a_tracer)

    if afficher_les_deux and a_des_normalises:
        # On coupe en deux (haut pour absolu, bas pour habitant) en partageant l'axe X
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)
        fig.suptitle(f"Analyse croisée de : {nom_dep}", fontsize=22, fontweight="bold", y=0.98)
        
        for ind in indicateurs_a_tracer:
            if ind in pivot.columns and pivot[ind].notna().any():
                if "(€/hab)" in ind:
                    sns.lineplot(data=pivot, x="Exercice", y=ind, marker="o", label=ind, ax=ax2, linewidth=3)
                else:
                    sns.lineplot(data=pivot, x="Exercice", y=ind, marker="o", label=ind, ax=ax1, linewidth=3)
                    
                    # On garde les lignes de repères pour la dette sur l'axe des valeurs absolues
                    if ind == "Capacité de désendettement (années)":
                        ax1.axhline(12, color="darkred", linestyle="--", linewidth=1)
                        ax1.axhline(9, color="red", linestyle="--", linewidth=1)
                        ax1.axhline(6, color="darkorange", linestyle="--", linewidth=1)
                        ax1.axhline(3, color="green", linestyle="--", linewidth=1)

        ax1.set_ylabel("Valeurs absolues")
        ax2.set_ylabel("Valeurs normalisées (€/hab)")
        ax2.set_xlabel("Exercice")
        
        # On sort les légendes pour la propreté
        ax1.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=12)
        ax2.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=12)
        
        ax1.set_xticks(pivot["Exercice"].unique())
        ax2.set_xticks(pivot["Exercice"].unique())
        
        plt.tight_layout()

    else:
        # Le code normal pour tracer sur un seul axe
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


# La première
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


# La deuxième
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


# La troisième
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


# La quatrième
def comparer_departement_strate_metro(df, code_dep, intervalle_annees, indicateurs, meme_region=False, par_habitant=False, afficher_les_deux=False):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min, annee_max = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0] # Récupération de la région
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   ((df_temp["Outre-mer"] == "Non") | (df_temp["Code Insee 2024 Département"] == code_dep)) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    # On ajoute la région dans l'index du pivot_table
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
    
    # Filtre sur la région pour la moyenne de la strate si la case a été cochée
    if meme_region:
        df_strate = df_strate[df_strate["Nom 2024 Région"] == region]

    df_moy_strate = df_strate.groupby("Exercice")[cols_mean].mean().reset_index()
    label_moyenne = f"Moyenne Strate {strate}" + (" (même région)" if meme_region else " (France)")
    df_moy_strate["Nom 2024 Département"] = label_moyenne

    # La moyenne métropole reste globale (elle ne se restreint pas à la région)
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
st.markdown("Bienvenue dans l'interface d'analyse. Choisissez une fonctionnalité du magnifique menu situé à votre gauche.")

# Liste des départements pour les menus déroulants
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

# On regroupe les indicateurs par catégorie pour créer les sous-menus visuels
dict_categories = {}
for ind in indiacteurs:
    cat = categoriser_indicateur(ind)
    if cat not in dict_categories:
        dict_categories[cat] = []
    dict_categories[cat].append(ind)

indicateurs_choisis = []

# Création du volet déroulant pour la sélection des indicateurs
with st.sidebar.expander("📂 Choix des indicateurs par thème", expanded=True):
    for cat in sorted(dict_categories.keys()):
        # On définit les valeurs cochées par défaut pour cette catégorie
        defauts_cat = [ind for ind in dict_categories[cat] if ind in indicateurs_fait_main]
        
        choix = st.multiselect(
            label=cat,
            options=dict_categories[cat],
            default=defauts_cat
        )
        indicateurs_choisis.extend(choix)

par_habitant = st.sidebar.checkbox("Afficher les données en par habitant (€/hab)")

# La mini-option conditionnelle
afficher_les_deux = False
if par_habitant:
    afficher_les_deux = st.sidebar.checkbox("Afficher et superposer l'absolu ET le normalisé")

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
        "Comparaison d'indicateurs financiers entre un département et la moyenne de sa strate",
        "Comparaison d'indicateurs financiers entre un département, la moyenne de sa strate et la moyenne de la métropole"
    ],
    label_visibility="collapsed" 
)

st.write("---")

# Sécurité : vérifier qu'au moins 1 indicateur est sélectionné
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
    
    # Remplacement des 2 selectbox par un multiselect pour choisir N départements
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

elif menu == "Comparaison d'indicateurs financiers entre un département et la moyenne de sa strate":
    st.header("📈 Comparaison d'un département à sa strate")
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

elif menu == "Comparaison d'indicateurs financiers entre un département, la moyenne de sa strate et la moyenne de la métropole":
    st.header("🏢 Comparaison : Département VS Strate VS Métropole")
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
