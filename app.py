import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st

# Configuration page web
st.set_page_config(page_title="Analyse financière départementale", page_icon="📊")

# Chargement données et on les garde en mémoire vive
@st.cache_data
def load_data():
    return pd.read_csv("ofgl-base-departements.zip", sep=",", low_memory=False)

# Prévention d'erreurs
try:
    df_main = load_data()
except FileNotFoundError:
    st.error("Le fichier 'ofgl-base-departements.zip' est introuvable. Contactez l'administrateur du site.")
    st.stop()

# On stocke les variables min_annee et max_annee
min_annee = int(df_main["Exercice"].min())
max_annee = int(df_main["Exercice"].max())

# Fonction de génération des graphiques
def generer_graphiques(df_plot, titre):
    fig, axes = plt.subplots(2, 2, figsize=(10, 8))
    fig.suptitle(titre, fontsize=25, fontweight="bold", y=0.98)

    # Graphique 1 : épargne brute
    sns.lineplot(data=df_plot, x="Exercice", y="Epargne brute (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 0], linewidth=3)
    axes[0, 0].set_title("Épargne brute (M€)", fontsize=20, fontweight="semibold")
    axes[0, 0].set_xticks(df_plot["Exercice"].unique())
    
    # Graphique 2 : épargne nette
    sns.lineplot(data=df_plot, x="Exercice", y="Epargne nette (M€)", hue="Nom 2024 Département", marker="o", ax=axes[0, 1], linewidth=3)
    axes[0, 1].set_title("Épargne Nette (M€)")
    axes[0, 1].set_xticks(df_plot["Exercice"].unique())

    # Graphique 3 : capacité de désendettement (= encours de dette / épargne brute)
    sns.lineplot(data=df_plot, x="Exercice", y="Capacité de désendettement (années)", hue="Nom 2024 Département", marker="o", ax=axes[1, 0], linewidth=3)
    axes[1, 0].set_title("Capacité de désendettement (années)")
    axes[1, 0].axhline(12, color="darkred", linestyle="~", linewidth=0.5, label="Surendettement avéré (à réduire)")
    axes[1, 0].axhline(9, color="red", linestyle="--", linewidth=0.5, label="Surendettement trop élevé (à réduire)")
    axes[1, 0].axhline(6, color="darkorange", linestyle="--", linewidth=0.5, label="Surendettement élevé (à résorber)")
    axes[1, 0].axhline(3, color="green", linestyle="--", linewidth=0.5, label="Endettement maîtrisé (à maintenir)")
    axes[1, 0].set_xticks(df_plot["Exercice"].unique())
    axes[1, 0].legend(loc='upper right', fontsize='small')
        
    ajouter_etiquettes_desendettement(axes[1, 0], df_plot)

    # Graphique 4 : Poids des AIS
    sns.lineplot(data=df_plot, x="Exercice", y="Poids des AIS (%)", hue="Nom 2024 Département", marker="o", ax=axes[1, 1], linewidth=3)
    axes[1, 1].set_title("Poids des dépenses sociales (AIS) (%)")
    axes[1, 1].set_xticks(df_plot["Exercice"].unique())

    plt.tight_layout()
    return fig


def ajouter_etiquettes_desendettement(ax, df_donnees):
    """Ajoute les étiquettes avec les vraies valeurs pour la capacité de désendettement"""
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


# --- 4. FONCTIONS DE TRAITEMENT DES DONNÉES ---

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

def comparer_departements(df, code_dep1, code_dep2, intervalle_annees):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep1, code_dep2 = str(code_dep1), str(code_dep2)
    annee_min, annee_max = intervalle_annees
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   (df_temp["Code Insee 2024 Département"].isin([code_dep1, code_dep2])) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    pivot = df_temp[serie_filtre].pivot_table(index=["Exercice", "Nom 2024 Département"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot["Epargne brute"] / 1000000
    pivot["Epargne nette (M€)"] = pivot["Epargne nette"] / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot[["Allocations RSA", "Allocations APA", "Allocations PCH"]].sum(axis=1)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot["Dépenses totales"]) * 100

    fig = generer_graphiques(pivot, "Analyse Financière Comparative")

    colonnes = ["Exercice", "Nom 2024 Département", "Epargne brute (M€)", "Epargne nette (M€)", "Capacité de désendettement (années)", "Poids des AIS (%)"]
    df_final = pivot[[c for c in colonnes if c in pivot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    
    return fig, df_final

def comparer_departement_strate(df, code_dep, intervalle_annees):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min, annee_max = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   (df_temp["Strate population 2024"] == strate) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    pivot = df_temp[serie_filtre].pivot_table(index=["Exercice", "Code Insee 2024 Département", "Nom 2024 Département"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot["Epargne brute"] / 1000000
    pivot["Epargne nette (M€)"] = pivot["Epargne nette"] / 1000000
    pivot["Poids des AIS (%)"] = (pivot[["Allocations RSA", "Allocations APA", "Allocations PCH"]].sum(axis=1) / pivot["Dépenses totales"]) * 100

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    df_autres = pivot[pivot["Code Insee 2024 Département"] != code_dep].copy()
    
    df_moyenne = df_autres.groupby("Exercice")[["Epargne brute (M€)", "Epargne nette (M€)", "Capacité de désendettement (années)", "Capacité de désendettement (vraie)", "Poids des AIS (%)"]].mean().reset_index()
    df_moyenne["Nom 2024 Département"] = f"Moyenne Strate {strate} (hors {nom_dep})"
    df_plot = pd.concat([df_cible, df_moyenne], ignore_index=True)

    fig = generer_graphiques(df_plot, f"{nom_dep} VS Moyenne Strate {strate}")

    colonnes = ["Exercice", "Nom 2024 Département", "Epargne brute (M€)", "Epargne nette (M€)", "Capacité de désendettement (années)", "Poids des AIS (%)"]
    df_final = df_plot[[c for c in colonnes if c in df_plot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    
    return fig, df_final

def comparer_departement_strate_metro(df, code_dep, intervalle_annees):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min, annee_max = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   ((df_temp["Outre-mer"] == "Non") | (df_temp["Code Insee 2024 Département"] == code_dep)) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    pivot = df_temp[serie_filtre].pivot_table(index=["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Strate population 2024", "Outre-mer"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row["Encours de dette"] / row["Epargne brute"] if row["Epargne brute"] > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot["Epargne brute"] / 1000000
    pivot["Epargne nette (M€)"] = pivot["Epargne nette"] / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot[["Allocations RSA", "Allocations APA", "Allocations PCH"]].sum(axis=1)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot["Dépenses totales"]) * 100

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    
    df_strate = pivot[(pivot["Strate population 2024"] == strate) & (pivot["Code Insee 2024 Département"] != code_dep)].copy()
    df_moy_strate = df_strate.groupby("Exercice")[["Epargne brute (M€)", "Epargne nette (M€)", "Capacité de désendettement (années)", "Capacité de désendettement (vraie)", "Poids des AIS (%)"]].mean().reset_index()
    df_moy_strate["Nom 2024 Département"] = f"Moyenne Strate {strate}"

    df_metro = pivot[pivot["Outre-mer"] == "Non"].copy()
    df_moy_metro = df_metro.groupby("Exercice")[["Epargne brute (M€)", "Epargne nette (M€)", "Capacité de désendettement (années)", "Capacité de désendettement (vraie)", "Poids des AIS (%)"]].mean().reset_index()
    df_moy_metro["Nom 2024 Département"] = "Moyenne Métropole"
    
    df_plot = pd.concat([df_cible, df_moy_strate, df_moy_metro], ignore_index=True)

    fig = generer_graphiques(df_plot, f"{nom_dep} VS Strate {strate} VS Métropole")

    colonnes = ["Exercice", "Nom 2024 Département", "Epargne brute (M€)", "Epargne nette (M€)", "Capacité de désendettement (années)", "Poids des AIS (%)"]
    df_final = df_plot[[c for c in colonnes if c in df_plot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    
    return fig, df_final 


# --- 5. L'INTERFACE GRAPHIQUE UTILISATEUR (STREAMLIT) ---

st.title("📊 Outil d'analyse financière de départements")
st.markdown("Bienvenue dans l'interface d'analyse. Choisissez une fonctionnalité du magnifique menu situé à votre gauche.")

# Liste des départements pour les menus déroulants
liste_deps = sorted(df_main["Code Insee 2024 Département"].astype(str).unique())

# Ajout du style CSS pour espacer les options
st.markdown("""
    <style>
    div[role="radiogroup"] > label {
        margin-bottom: 20px !important; 
    }
    </style>
""", unsafe_allow_html=True)


# --- CRÉATION DU MENU ---

st.sidebar.markdown(
    "<h3 style='font-size: 22px; font-weight: bold; margin-bottom: 25px;'>Quelles sont les données qui vous intéressent ?</h3>", 
    unsafe_allow_html=True
)

menu = st.sidebar.radio(
    label="Menu caché",
    options=[
        "Recherche départements de même strate", 
        "Comparaison d'indicateurs financiers entre 2 départements", 
        "Comparaison d'indicateurs financiers entre un département et la moyenne de sa strate",
        "Comparaison d'indicateurs financiers entre un département, la moyenne de sa strate et la moyenne de la métropole"
    ],
    label_visibility="collapsed" 
)

st.write("---")

if menu == "Recherche départements de même strate":
    st.header("🔍 Départements de même strate")
    col1, col2 = st.columns(2)
    with col1:
        dep = st.selectbox("Sélectionnez le département ciblé :", liste_deps)
    with col2:
        meme_region = st.checkbox("Restreindre à la même région uniquement")
    
    if st.button("Chercher les correspondances"):
        resultat = departements_meme_strate(df_main, dep, meme_region)
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
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Lancer la comparaison"):
        fig, data = comparer_departements(df_main, dep1, dep2, annees_sel)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)

elif menu == "Comparaison d'indicateurs financiers entre un département et la moyenne de sa strate":
    st.header("📈 Comparaison d'un département à sa strate")
    dep = st.selectbox("Sélectionnez le département :", liste_deps)
    
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Générer l'analyse"):
        fig, data = comparer_departement_strate(df_main, dep, annees_sel)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)

elif menu == "Comparaison d'indicateurs financiers entre un département, la moyenne de sa strate et la moyenne de la métropole":
    st.header("🏢 Comparaison : Département VS Strate VS Métropole")
    dep = st.selectbox("Sélectionnez le département :", liste_deps)
    
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Générer l'analyse complète"):
        fig, data = comparer_departement_strate_metro(df_main, dep, annees_sel)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)
