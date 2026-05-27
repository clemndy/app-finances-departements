# -*- coding: utf-8 -*-
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st

# --- 1. CONFIGURATION DE LA PAGE WEB ---
st.set_page_config(page_title="Analyse Financière Départementale", layout="wide", page_icon="📊")

# --- 2. CHARGEMENT DES DONNÉES ---
@st.cache_data
def load_data():
    return pd.read_zip("ofgl-base-departements.zip", sep=",", low_memory=False)

try:
    df = load_data()
except FileNotFoundError:
    st.error("Le fichier 'ofgl-base-departements.zip' est introuvable. Placez-le dans le même dossier que ce script (avec le même nom affiché ici).")
    st.stop()


# --- 3. VOS FONCTIONS ADAPTÉES POUR STREAMLIT ---

def ajouter_etiquettes_desendettement(ax, df_donnees):
    for index, row in df_donnees.iterrows():
        if row["Capacité de désendettement (années)"] == 0:
            vraie_valeur = row["Capacité de désendettement (vraie)"]
            if pd.isna(vraie_valeur) or np.isinf(vraie_valeur):
                texte = "inf"
            else:
                texte = f"{vraie_valeur:.1f}"
            ax.annotate(
                texte, xy=(row["Exercice"], 0), xytext=(0, 10),
                textcoords="offset points", ha="center", va="bottom",
                fontsize=9, color="white", fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.3", fc="black", ec="none", alpha=0.7)
            )

def departements_meme_strate(code_dep, mm_region=False):
    code_dep = str(code_dep)
    df["Code Insee 2024 Département"] = df["Code Insee 2024 Département"].astype(str)
    df_dep_cible = df[df["Code Insee 2024 Département"] == code_dep]
    
    if df_dep_cible.empty: return pd.DataFrame()

    strate = df_dep_cible["Strate population 2024"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0]
    
    serie_filtre = df["Strate population 2024"] == strate
    if mm_region:
        serie_filtre = serie_filtre & (df["Nom 2024 Région"] == region)

    df_resultat = df.loc[serie_filtre, ["Code Insee 2024 Département", "Nom 2024 Département", "Nom 2024 Région"]].drop_duplicates()
    df_resultat = df_resultat[df_resultat["Code Insee 2024 Département"] != code_dep]
    return df_resultat.reset_index(drop=True)

def comparer_departements(code_dep1, code_dep2):
    df["Code Insee 2024 Département"] = df["Code Insee 2024 Département"].astype(str)
    code_dep1, code_dep2 = str(code_dep1), str(code_dep2)
    
    serie_filtre = (df["Type de budget"] == "Budget principal") & (df["Code Insee 2024 Département"].isin([code_dep1, code_dep2]))
    pivot = df[serie_filtre].pivot_table(index=["Exercice", "Nom 2024 Département"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] > 0 else 0, axis=1)
    pivot["Capacité d'autofinancement"] = pivot["Epargne brute"] - pivot["Annuité de la dette"]
    pivot["Epargne brute (M€)"] = pivot["Epargne brute"] / 1000000
    pivot["Capacité d'autofinancement (M€)"] = pivot["Capacité d'autofinancement"] / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot[["Allocations RSA", "Allocations APA", "Allocations PCH"]].sum(axis=1)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot["Dépenses totales"]) * 100

    fig, axes = plt.subplots(2, 2, figsize=(14,8))
    fig.suptitle("Analyse Financière Comparative", fontsize=25, fontweight="bold", y=0.98)

    sns.lineplot(data=pivot, x="Exercice", y="Epargne brute (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 0], linewidth=3)
    axes[0, 0].set_title("Épargne Brute (M€)")
    axes[0, 0].set_xticks(pivot["Exercice"].unique())
    
    sns.lineplot(data=pivot, x="Exercice", y="Capacité d'autofinancement (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 1], linewidth=3)
    axes[0, 1].set_title("Capacité d'autofinancement (M€)")
    axes[0, 1].set_xticks(pivot["Exercice"].unique())

    sns.lineplot(data=pivot, x="Exercice", y="Capacité de désendettement (années)", hue="Nom 2024 Département", marker="o", ax=axes[1, 0], linewidth=3)
    axes[1, 0].set_title("Capacité de désendettement (années)")
    axes[1, 0].axhline(12, color="darkred", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(9, color="red", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(6, color="darkorange", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(3, color="green", linestyle="--", linewidth=1.5)
    axes[1, 0].set_xticks(pivot["Exercice"].unique())
    ajouter_etiquettes_desendettement(axes[1, 0], pivot)

    sns.lineplot(data=pivot, x="Exercice", y="Poids des AIS (%)", hue="Nom 2024 Département", marker="o", ax=axes[1, 1], linewidth=3)
    axes[1, 1].set_title("Poids des dépenses sociales (%)")
    axes[1, 1].set_xticks(pivot["Exercice"].unique())

    plt.tight_layout()

    colonnes = ["Exercice", "Nom 2024 Département", "Epargne brute (M€)", "Capacité d'autofinancement (M€)", "Capacité de désendettement (années)", "Poids des AIS (%)"]
    df_final = pivot[[c for c in colonnes if c in pivot.columns]].round(1)
    return fig, df_final

def comparer_departement_strate(code_dep):
    df["Code Insee 2024 Département"] = df["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    df_dep_cible = df[df["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    
    serie_filtre = (df["Type de budget"] == "Budget principal") & (df["Strate population 2024"] == strate)
    pivot = df[serie_filtre].pivot_table(index=["Exercice", "Code Insee 2024 Département", "Nom 2024 Département"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] > 0 else 0, axis=1)
    pivot["Capacité d'autofinancement"] = pivot["Epargne brute"] - pivot["Annuité de la dette"]
    pivot["Epargne brute (M€)"] = pivot["Epargne brute"] / 1000000
    pivot["Capacité d'autofinancement (M€)"] = pivot["Capacité d'autofinancement"] / 1000000
    pivot["Poids des AIS (%)"] = (pivot[["Allocations RSA", "Allocations APA", "Allocations PCH"]].sum(axis=1) / pivot["Dépenses totales"]) * 100

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    df_autres = pivot[pivot["Code Insee 2024 Département"] != code_dep].copy()
    
    df_moyenne = df_autres.groupby("Exercice")[["Epargne brute (M€)", "Capacité d'autofinancement (M€)", "Capacité de désendettement (années)", "Capacité de désendettement (vraie)", "Poids des AIS (%)"]].mean().reset_index()
    df_moyenne["Nom 2024 Département"] = f"Moyenne Strate {strate} (hors {nom_dep})"
    df_plot = pd.concat([df_cible, df_moyenne], ignore_index=True)

    fig, axes = plt.subplots(2, 2, figsize=(14,8))
    fig.suptitle(f"{nom_dep} VS Moyenne Strate {strate}", fontsize=25, fontweight="bold", y=0.98)

    sns.lineplot(data=df_plot, x="Exercice", y="Epargne brute (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 0], linewidth=3)
    axes[0, 0].set_xticks(df_plot["Exercice"].unique())
    
    sns.lineplot(data=df_plot, x="Exercice", y="Capacité d'autofinancement (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 1], linewidth=3)
    axes[0, 1].set_xticks(df_plot["Exercice"].unique())

    sns.lineplot(data=df_plot, x="Exercice", y="Capacité de désendettement (années)", hue="Nom 2024 Département", marker="o", ax=axes[1, 0], linewidth=3)
    axes[1, 0].axhline(12, color="darkred", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(9, color="red", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(6, color="darkorange", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(3, color="green", linestyle="--", linewidth=1.5)
    axes[1, 0].set_xticks(df_plot["Exercice"].unique())
    ajouter_etiquettes_desendettement(axes[1, 0], df_plot)

    sns.lineplot(data=df_plot, x="Exercice", y="Poids des AIS (%)", hue="Nom 2024 Département", marker="o", ax=axes[1, 1], linewidth=3)
    axes[1, 1].set_xticks(df_plot["Exercice"].unique())

    plt.tight_layout()
    colonnes = ["Exercice", "Nom 2024 Département", "Epargne brute (M€)", "Capacité d'autofinancement (M€)", "Capacité de désendettement (années)", "Poids des AIS (%)"]
    df_final = df_plot[[c for c in colonnes if c in df_plot.columns]].round(1)
    return fig, df_final

def comparer_departement_strate_metro(code_dep):
    df["Code Insee 2024 Département"] = df["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    
    df_dep_cible = df[df["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    
    serie_filtre = (df["Type de budget"] == "Budget principal") & ((df["Outre-mer"] == "Non") | (df["Code Insee 2024 Département"] == code_dep))
    pivot = df[serie_filtre].pivot_table(index=["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Strate population 2024", "Outre-mer"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] > 0 else 0, axis=1)
    pivot["Capacité d'autofinancement"] = pivot["Epargne brute"] - pivot["Annuité de la dette"]
    pivot["Epargne brute (M€)"] = pivot["Epargne brute"] / 1000000
    pivot["Capacité d'autofinancement (M€)"] = pivot["Capacité d'autofinancement"] / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot[["Allocations RSA", "Allocations APA", "Allocations PCH"]].sum(axis=1)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot["Dépenses totales"]) * 100

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    
    df_strate = pivot[(pivot["Strate population 2024"] == strate) & (pivot["Code Insee 2024 Département"] != code_dep)].copy()
    df_moy_strate = df_strate.groupby("Exercice")[["Epargne brute (M€)", "Capacité d'autofinancement (M€)", "Capacité de désendettement (années)", "Capacité de désendettement (vraie)", "Poids des AIS (%)"]].mean().reset_index()
    df_moy_strate["Nom 2024 Département"] = f"Moyenne Strate {strate}"

    df_metro = pivot[pivot["Outre-mer"] == "Non"].copy()
    df_moy_metro = df_metro.groupby("Exercice")[["Epargne brute (M€)", "Capacité d'autofinancement (M€)", "Capacité de désendettement (années)", "Capacité de désendettement (vraie)", "Poids des AIS (%)"]].mean().reset_index()
    df_moy_metro["Nom 2024 Département"] = "Moyenne Métropole"
    
    df_plot = pd.concat([df_cible, df_moy_strate, df_moy_metro], ignore_index=True)

    fig, axes = plt.subplots(2, 2, figsize=(14,8))
    fig.suptitle(f"{nom_dep} VS Strate {strate} VS Métropole", fontsize=25, fontweight="bold", y=0.98)

    sns.lineplot(data=df_plot, x="Exercice", y="Epargne brute (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 0], linewidth=3)
    axes[0, 0].set_xticks(df_plot["Exercice"].unique())
    
    sns.lineplot(data=df_plot, x="Exercice", y="Capacité d'autofinancement (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 1], linewidth=3)
    axes[0, 1].set_xticks(df_plot["Exercice"].unique())

    sns.lineplot(data=df_plot, x="Exercice", y="Capacité de désendettement (années)", hue="Nom 2024 Département", marker="o", ax=axes[1, 0], linewidth=3)
    axes[1, 0].axhline(12, color="darkred", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(9, color="red", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(6, color="darkorange", linestyle="--", linewidth=1.5)
    axes[1, 0].axhline(3, color="green", linestyle="--", linewidth=1.5)
    axes[1, 0].set_xticks(df_plot["Exercice"].unique())
    ajouter_etiquettes_desendettement(axes[1, 0], df_plot)

    sns.lineplot(data=df_plot, x="Exercice", y="Poids des AIS (%)", hue="Nom 2024 Département", marker="o", ax=axes[1, 1], linewidth=3)
    axes[1, 1].set_xticks(df_plot["Exercice"].unique())

    plt.tight_layout()
    colonnes = ["Exercice", "Nom 2024 Département", "Epargne brute (M€)", "Capacité d'autofinancement (M€)", "Capacité de désendettement (années)", "Poids des AIS (%)"]
    df_final = df_plot[[c for c in colonnes if c in df_plot.columns]].round(1)
    
    return fig, df_final  # Correction ici : votre code original retournait un vide !


# --- 4. L'INTERFACE GRAPHIQUE UTILISATEUR ---

st.title("📊 Outil d'analyse financière de départements")
st.markdown("Bienvenue dans l'interface d'analyse. Choisissez une fonctionnalité du magnifique menu situé à votre gauche.")

# Liste des départements pour les menus déroulants
liste_deps = sorted(df["Code Insee 2024 Département"].astype(str).unique())

# --- AJOUT DU STYLE CSS POUR ESPACER LES OPTIONS ---
st.markdown("""
    <style>
    /* Cette ligne cible les options du bouton radio et ajoute 20 pixels d'espace en dessous de chacune */
    div[role="radiogroup"] > label {
        margin-bottom: 20px !important; 
    }
    </style>
""", unsafe_allow_html=True)


# --- CRÉATION DU NOUVEAU MENU VISUELLEMENT AMÉLIORÉ ---

# 1. On crée un grand titre personnalisé dans la barre latérale
st.sidebar.markdown(
    "<h3 style='font-size: 22px; font-weight: bold; margin-bottom: 25px;'>Quelles sont les données qui vous intéressent ?</h3>", 
    unsafe_allow_html=True
)

# 2. On crée le menu radio, mais on cache son titre d'origine avec label_visibility="collapsed"
menu = st.sidebar.radio(
    label="Menu caché", # Obligatoire pour Streamlit, mais il ne sera pas affiché
    options=[
        "Recherche départements de même strate", 
        "Comparaison d'indicateurs financiers entre 2 départements", 
        "Comparaison d'indicateurs financiers entre un département et la moyenne de sa strate",
        "Comparaison d'indicateurs financiers entre un département, la moyenne de sa strate et la moyenne de la métropole"
    ],
    label_visibility="collapsed" # <-- L'astuce pour cacher le petit titre est ici !
)

st.write("---")

st.write("---")

if menu == "Recherche départements de même strate":
    st.header("🔍 Départements de même strate")
    col1, col2 = st.columns(2)
    with col1:
        dep = st.selectbox("Sélectionnez le département ciblé :", liste_deps)
    with col2:
        meme_region = st.checkbox("Restreindre à la même région uniquement")
    
    if st.button("Chercher les correspondances"):
        resultat = departements_meme_strate(dep, meme_region)
        if not resultat.empty:
            st.success(f"Voici les départements trouvés ({len(resultat)}) :")
            st.dataframe(resultat, use_container_width=True)
        else:
            st.warning("Aucun résultat trouvé ou données manquantes.")

elif menu == "Comparaison d'indicateurs financiers entre 2 départements":
    st.header("⚖️ Comparaison entre deux départements")
    col1, col2 = st.columns(2)
    with col1:
        dep1 = st.selectbox("Premier département :", liste_deps, index=0)
    with col2:
        dep2 = st.selectbox("Second département :", liste_deps, index=1)
        
    if st.button("Lancer la comparaison"):
        fig, data = comparer_departements(dep1, dep2)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)

elif menu == "Comparaison d'indicateurs financiers entre un département et la moyenne de sa strate":
    st.header("📈 Comparaison d'un département à sa strate")
    dep = st.selectbox("Sélectionnez le département :", liste_deps)
        
    if st.button("Générer l'analyse"):
        fig, data = comparer_departement_strate(dep)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)

elif menu == "Comparaison d'indicateurs financiers entre un département, la moyenne de sa strate et la moyenne de la métropole":
    st.header("🏢 Comparaison : Département VS Strate VS Métropole")
    dep = st.selectbox("Sélectionnez le département :", liste_deps)
        
    if st.button("Générer l'analyse complète"):
        fig, data = comparer_departement_strate_metro(dep)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)