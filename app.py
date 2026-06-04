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

liste_agregats = [elt for elt in df["Agrégat"]]

indiacteurs = sorted(list(set(indicateurs_fait_main + liste_agregats)))

# On stocke les variables min_annee et max_annee
min_annee = int(df["Exercice"].min())
max_annee = int(df["Exercice"].max())



# Fonction de génération des graphiques dynamique
def generer_graphiques(df_plot, titre, indicateurs):
    fig, axes = plt.subplots(2, 2, figsize=(16, 9))
    fig.suptitle(titre, fontsize=25, fontweight="bold", y=0.98)

    # On aplatit la matrice 2x2 en une liste de 4 cases pour boucler plus facilement
    axes_flat = axes.flatten()

    for i, ind in enumerate(indicateurs):
        ax = axes_flat[i]
        
        # Prévention d'erreurs (normalement le fichier ofgl n'a pas de "trous" mais on ne sait jamais dans les futurs documents ofgl)
        if ind not in df_plot.columns:
            ax.set_title(f"{ind}\n(Données indisponibles)", fontsize=12, color="gray")
            continue
            
        sns.lineplot(data=df_plot, x="Exercice", y=ind, hue="Nom 2024 Département", marker="o", ax=ax, linewidth=3)
        ax.set_title(ind, fontsize=15, fontweight="semibold")
        ax.set_xticks(df_plot["Exercice"].unique())
        
        # On avait rajouté un style spécifique pour la capacité d'endettement (avant de pouvoir choisir n'importe quelle donnée à afficher)
        if ind == "Capacité de désendettement (années)":
            ax.axhline(12, color="darkred", linestyle="--", linewidth=1, label="Surendettement avéré")
            ax.axhline(9, color="red", linestyle="--", linewidth=1, label="Surendettement trop élevé")
            ax.axhline(6, color="darkorange", linestyle="--", linewidth=1, label="Surendettement élevé")
            ax.axhline(3, color="green", linestyle="--", linewidth=1, label="Endettement maîtrisé")
            ajouter_etiquettes_desendettement(ax, df_plot)
            if ax.get_legend() is not None:
                ax.legend(loc="best", fontsize="small")

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
                bbox=dict(boxstyle="round,pad=0.5", fc="black", alpha=0.75, edgecolor="lightred", linewidth=5)
            )



# Nos fonctions correspondant aux différentes fonctionalités du site

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
def comparer_departements(df, code_dep1, code_dep2, intervalle_annees, indicateurs):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep1, code_dep2 = str(code_dep1), str(code_dep2)
    annee_min, annee_max = intervalle_annees
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   (df_temp["Code Insee 2024 Département"].isin([code_dep1, code_dep2])) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    pivot = df_temp[serie_filtre].pivot_table(index=["Exercice", "Nom 2024 Département"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    # Calcul des indicateurs customs (au cas où ils sont sélectionnés)
    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot.get("Epargne brute", 0) / 1000000
    pivot["Epargne nette (M€)"] = pivot.get("Epargne nette", 0) / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot.get("Dépenses totales", 1)) * 100

    for ind in indicateurs:
        if ind not in pivot.columns:
            pivot[ind] = np.nan

    fig = generer_graphiques(pivot, "Analyse Financière Comparative", indicateurs)

    colonnes = ["Exercice", "Nom 2024 Département"] + indicateurs
    df_final = pivot[[c for c in colonnes if c in pivot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    return fig, df_final


# La troisième
def comparer_departement_strate(df, code_dep, intervalle_annees, indicateurs, meme_region=False):
    df_temp = df.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min, annee_max = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0] # Récupération de la région
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & \
                   (df_temp["Strate population 2024"] == strate) & \
                   (df_temp["Exercice"] >= annee_min) & (df_temp["Exercice"] <= annee_max)
                   
    # On ajoute la région dans l'index du pivot_table pour pouvoir filtrer plus tard
    pivot = df_temp[serie_filtre].pivot_table(index=["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Nom 2024 Région"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot.get("Epargne brute", 0) / 1000000
    pivot["Epargne nette (M€)"] = pivot.get("Epargne nette", 0) / 1000000
    pivot["Poids des AIS (%)"] = ((pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)) / pivot.get("Dépenses totales", 1)) * 100

    for ind in indicateurs:
        if ind not in pivot.columns:
            pivot[ind] = np.nan

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    df_autres = pivot[pivot["Code Insee 2024 Département"] != code_dep].copy()
    
    # Filtre sur la région si la case a été cochée
    if meme_region:
        df_autres = df_autres[df_autres["Nom 2024 Région"] == region]

    cols_mean = [c for c in indicateurs + ["Capacité de désendettement (vraie)"] if c in df_autres.columns]
    df_moyenne = df_autres.groupby("Exercice")[cols_mean].mean().reset_index()
    
    # Label dynamique selon le filtre de région
    label_moyenne = f"Moyenne Strate {strate}" + (" (même région)" if meme_region else " (France)")
    df_moyenne["Nom 2024 Département"] = label_moyenne
    
    df_plot = pd.concat([df_cible, df_moyenne], ignore_index=True)

    fig = generer_graphiques(df_plot, f"{nom_dep} VS Moyenne Strate {strate}", indicateurs)

    colonnes = ["Exercice", "Nom 2024 Département"] + indicateurs
    df_final = df_plot[[c for c in colonnes if c in df_plot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    return fig, df_final


# La quatrième
def comparer_departement_strate_metro(df, code_dep, intervalle_annees, indicateurs, meme_region=False):
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
    pivot = df_temp[serie_filtre].pivot_table(index=["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Strate population 2024", "Outre-mer", "Nom 2024 Région"], columns="Agrégat", values="Montant", aggfunc="sum").reset_index()

    pivot["Capacité de désendettement (vraie)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) != 0 else np.nan, axis=1)
    pivot["Capacité de désendettement (années)"] = pivot.apply(lambda row: row.get("Encours de dette", 0) / row["Epargne brute"] if row.get("Epargne brute", 0) > 0 else 0, axis=1)
    pivot["Epargne brute (M€)"] = pivot.get("Epargne brute", 0) / 1000000
    pivot["Epargne nette (M€)"] = pivot.get("Epargne nette", 0) / 1000000
    pivot["Dépenses sociales (AIS)"] = pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)
    pivot["Poids des AIS (%)"] = (pivot["Dépenses sociales (AIS)"] / pivot.get("Dépenses totales", 1)) * 100

    for ind in indicateurs:
        if ind not in pivot.columns:
            pivot[ind] = np.nan

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    cols_mean = [c for c in indicateurs + ["Capacité de désendettement (vraie)"] if c in pivot.columns]

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

    fig = generer_graphiques(df_plot, f"{nom_dep} VS Strate {strate} VS Métropole", indicateurs)

    colonnes = ["Exercice", "Nom 2024 Département"] + indicateurs
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

# Ajout du multi-select pour choisir les graphiques
indicateurs_choisis = st.sidebar.multiselect(
    "Choisissez exactement 4 indicateurs à visualiser :",
    options=indiacteurs,
    default=indicateurs_fait_main,
    max_selections=4
)

st.sidebar.markdown("<hr>", unsafe_allow_html=True)
st.sidebar.markdown(
    "<h3 style='font-size: 22px; font-weight: bold; margin-bottom: 25px;'>Fonctionnalités</h3>", 
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

# Sécurité : vérifier que 4 indicateurs sont bien sélectionnés
if menu != "Recherche départements de même strate" and len(indicateurs_choisis) != 4:
    st.warning("⚠️ Veuillez sélectionner **exactement 4 indicateurs** dans le panneau latéral de gauche pour générer les graphiques.")
    st.stop()


# --- CORPS DE LA PAGE SELON LE MENU ---

if menu == "Recherche départements de même strate":
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
        fig, data = comparer_departements(df, dep1, dep2, annees_sel, indicateurs_choisis)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)

elif menu == "Comparaison d'indicateurs financiers entre un département et la moyenne de sa strate":
    st.header("📈 Comparaison d'un département à sa strate")
    col1, col2 = st.columns(2)
    with col1:
        dep = st.selectbox("Sélectionnez le département :", liste_deps)
    with col2:
        st.write("") # Espace vide pour aligner verticalement
        st.write("")
        meme_region = st.checkbox("Restreindre la moyenne de la strate à la même région")
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=min_annee, max_value=max_annee, value=(min_annee, max_annee))
        
    if st.button("Générer l'analyse"):
        fig, data = comparer_departement_strate(df, dep, annees_sel, indicateurs_choisis, meme_region)
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
        fig, data = comparer_departement_strate_metro(df, dep, annees_sel, indicateurs_choisis, meme_region)
        st.pyplot(fig)
        st.subheader("📋 Données brutes")
        st.dataframe(data, use_container_width=True)
