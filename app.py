import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import streamlit as st
import io

# Configuration page web
st.set_page_config(page_title="Analyse financière départementale", layout="wide", page_icon="📊")

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
    
colonnes_necessaires = ["Exercice", "Nom 2024 Département", "Code Insee 2024 Département", "Population totale"]
colonnes_manquantes = [col for col in colonnes_necessaires if col not in df.columns]

if colonnes_manquantes:
    st.error(f"Erreur : il manque la ou les colonnes suivantes : {', '.join(colonnes_manquantes)}")
    st.stop()



# Indicateurs calculés (tous non-normalisables, le code devra être adapté si on calcule de nouveaux indicateurs qui seraient normalisables) en utilisant les données OFGL
indicateurs_calculés = [
    "Capacité de désendettement (années)", 
    "Poids des AIS (%)"
]

# Catégories et sous-catégories d'indicateurs
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
            "Allocations APA", "Allocations PCH", "Allocations RSA", "CNSA", "Frais d'hébergement"
        ]
    },
    "5️⃣ Dette & Trésorerie": {
        "Indicateurs": [
            "Annuité de la dette", "Charges financières", "Remboursements d'emprunts hors GAD", "Emprunts hors GAD",
            "Fonds de soutien aux emprunts à risque", "Flux net de dette", "Encours de dette",
            "Encours de dette - Dettes bancaires et assimilées", "Encours de dette - Dépôts et cautionnements reçus",
            "Crédits de trésorerie", "Dépôts au Trésor"
        ]
    },
    "6️⃣​ Autres": {
        "Indicateurs calculés via les données ofgl": [
             "Capacité de désendettement (années)", "Poids des AIS (%)"
        ]
    }    
}

# On stocke les variables annee_min et annee_max
annee_min = int(df["Exercice"].min())
annee_max = int(df["Exercice"].max())



# Fonction de génération des graphiques
def generer_graphiques(df_plot, titre, indicateurs, par_habitant=False, afficher_les_deux=False, superposer=False):
    # On prépare le nombre de graphiques à afficher => combien de lignes et colonnes
    if superposer:
        lignes, colonnes, n = (1, 2, 2) if afficher_les_deux else (1, 1, 1)
    else:
        n = len(indicateurs)
        colonnes = 2 if n >= 2 else 1
        lignes = n // colonnes if n % 2 == 0 else (n+1) // 2    # On aura un graphe vide "seul" en + en bas

    fig, axes = plt.subplots(lignes, colonnes, figsize=(4*2*colonnes, 3*2*lignes))    # Affichage des graphiques en 4:3 avec un coeff de taille en + pour qu'il aient toujours la même taille
    fig.suptitle(titre, fontsize=24, fontweight="bold", y=0.9925) 
    
    # On mets tous les graphiques dans une liste
    if lignes == 1 and colonnes == 1:
        axes_liste = [axes]
    else:
        axes_liste = axes.flatten()

    # On affiche tout ce qu'il faut pour chaque graphe
    for i, axe_indice_i in enumerate(axes_liste[:n]):    # On met un coup de slicing pour eviter de faire un tour en trop quand on a un nombre impairs d'indicateur (cf le graphique vide de fin)
        
        if superposer:
            # Ici, i=0 ou i=1
            if afficher_les_deux:
                axe_indice_i.set_title("Valeurs brutes" if i == 0 else "Valeurs normalisées (€/hab)", fontsize=15, fontweight="bold", alpha=0.85)
                indics_axe = [ind for ind in indicateurs if ("(€/hab)" in ind) == (i == 1)]
            else:
                axe_indice_i.set_title("Valeurs normalisées (€/hab)" if par_habitant else "Valeurs brutes", fontsize=15, fontweight="bold", alpha=0.85)
                indics_axe = indicateurs

            # On melt le tableau (c'est l'inverse du pivot) pour pouvoir superposer les indicateurs sur le graphique
            df_melt = df_plot.melt(id_vars=["Exercice"], value_vars=[ind for ind in indics_axe], var_name="Indicateur", value_name="Valeur")
            
            if df_melt["Valeur"].notna().any():
                sns.lineplot(data=df_melt, x="Exercice", y="Valeur", hue="Indicateur", style="Indicateur", markers=True, dashes=False, ax=axe_indice_i, linewidth=3)
            else:
                axe_indice_i.text(0.5, 0.5, "⚠️ Aucun indicateur disponible ⚠️", fontsize=12, fontweight="bold", va="center", ha="center")

        else:
            indic = indicateurs[i]
            if indic not in df_plot.columns or df_plot[indic].isna().all():
                label_txt = f"⚠️ {indic.replace(' (€/hab)', '')} non normalisable ⚠️" if "(€/hab)" in indic and (indic.replace(' (€/hab)', '') in indicateurs_calculés) else f"⚠️ {indic} introuvable ou vide ⚠️"
                axe_indice_i.set_title(indic, fontsize=15, fontweight="bold", color="grey")
                axe_indice_i.text(0.5, 0.5, label_txt, fontsize=12, fontweight="bold", va="center", ha="center")
                continue

            sns.lineplot(data=df_plot, x="Exercice", y=indic, hue="Nom 2024 Département", style="Nom 2024 Département", markers=True, dashes=False, ax=axe_indice_i, linewidth=3)
            axe_indice_i.set_title(f"{indic} (€/hab)" if (par_habitant and not afficher_les_deux and indic not in indicateurs_calculés) else indic, fontsize=15, fontweight="bold", alpha=0.85)

        # Mêmes abscisses pour tout les graphes
        axe_indice_i.set_xlim(df_plot["Exercice"].min() - 0.2, df_plot["Exercice"].max() + 0.2)
        axe_indice_i.set_xticks(df_plot["Exercice"].unique())
        
        # Gestion des seuils de désendettement (s'applique si l'indicateur est présent dans l'axe actuel)
        indics_presents = indics_axe if superposer else [indicateurs[i]]
        if "Capacité de désendettement (années)" in indics_presents:
            axe_indice_i.axhline(12, color="darkred", linestyle="--", linewidth=1, label="Surendettement avéré")
            axe_indice_i.axhline(9, color="red", linestyle="--", linewidth=1, label="Surendettement trop élevé")
            axe_indice_i.axhline(6, color="darkorange", linestyle="--", linewidth=1, label="Surendettement élevé")
            axe_indice_i.axhline(3, color="green", linestyle="--", linewidth=1, label="Endettement maîtrisé")
            ajouter_etiquettes_desendettement(axe_indice_i, df_plot)

        if axe_indice_i.get_legend() is not None:
            axe_indice_i.legend(loc="best", fontsize="small")

    if len(axes_liste) - n > 0:    # Si on est dans le cas ou le nombre d'indicateurs est pair, on supprime le dernier axe
        fig.delaxes(axes_liste[-1])

    plt.tight_layout()
    return fig

# Fonction auxilière rajoutée en cours de route
def ajouter_etiquettes_desendettement(axe, df_donnees):
    for index, ligne in df_donnees.iterrows():
        val_tracee = ligne.get("Capacité de désendettement (années)", np.nan)
        vraie_valeur = ligne.get("Capacité de désendettement (vraie)", np.nan)
        
        if pd.notna(val_tracee) and (val_tracee == 15 or val_tracee == -3):
            
            if pd.isna(vraie_valeur) or vraie_valeur == float('inf'):
                vraie_valeur_texte = "Infini\n(Épargne = 0)"
            else:
                vraie_valeur_texte = int(vraie_valeur)
            
            offset_y = -25 if val_tracee == 15 else 25
            va_align = "bottom" if val_tracee == 15 else "top"
            
            axe.annotate(
                vraie_valeur_texte, 
                xy=(ligne["Exercice"], val_tracee), 
                xytext=(0, offset_y),
                textcoords="offset points", 
                ha="center", 
                va=va_align,
                fontsize=10, 
                color="white", 
                fontweight="bold",
                bbox=dict(boxstyle="round,pad=0.5", fc="black", alpha=0.75, edgecolor="red", linewidth=3)
            )



##########
#####
# FONCTIONS "COEUR" DU CODE
#####
##########
def analyser_un_departement(df_arg, code_dep, intervalle_annees, indicateurs, par_habitant=False, afficher_les_deux=False):
    df_temp = df_arg.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min_temp, annee_max_temp = intervalle_annees
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & (df_temp["Code Insee 2024 Département"] == code_dep) & (annee_min_temp <= df_temp["Exercice"]) & (df_temp["Exercice"] <= annee_max_temp)
                    
    index_colonnes = ["Exercice", "Nom 2024 Département", "Population totale"]

    pivot = df_temp[serie_filtre].pivot_table(index=index_colonnes, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()    # aggfunc permet d'avoir la somme de toutes les lignes d'épargne nette par exemple
    if pivot.empty: # Sécurité
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée disponible", fontsize=12, fontweight="bold", ha='center', va='center')
        return fig, pd.DataFrame()
    
    nom_dep = pivot["Nom 2024 Département"].iloc[0]    # On récupère le nom du département pour plus tard l'afficher et pas avoir que les numéros de départements
    
    
    if "Capacité de désendettement (années)" in indicateurs:
        pivot["Capacité de désendettement (vraie)"] = pivot.apply(
            lambda ligne: ligne.get("Encours de dette", 0) / ligne["Epargne brute"] if ligne.get("Epargne brute", 0) != 0 else (float('inf') if ligne.get("Encours de dette", 0) > 0 else np.nan), 
            axis=1
        ) 
        def borner(val):
            if pd.isna(val):
                return np.nan
            if val == float('inf') or val > 15:
                return 15
            if val < -3:
                return -3
            return val       
        pivot["Capacité de désendettement (années)"] = pivot["Capacité de désendettement (vraie)"].apply(borner) 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    if "Poids des AIS (%)" in indicateurs:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
        pivot["Poids des AIS (%)"] = np.where(
            pivot.get("Dépenses de fonctionnement", 0) != 0, 
            ((pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)) / pivot.get("Dépenses de fonctionnement", 1)) * 100, 
            np.nan    # On ne trace pas le point du poids des AIS quand les dépenses de fctnmt sont nulles ou introuvables
        )
        
    indicateurs_a_tracer = indicateurs.copy()

    for indic in indicateurs_a_tracer:
         if indic not in pivot.columns:
            pivot[indic] = np.nan
      
    if par_habitant:
        if afficher_les_deux:
            liste_indic_temp = []    # On crée une nouvelle liste pour avoir les graphiques avec les données brutes et les données normalisées d'un même indic sur la même ligne
            for indic in indicateurs_a_tracer:
                liste_indic_temp.append(indic)
                indic_par_hab_temp = f"{indic} (€/hab)"
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic_par_hab_temp] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)
                else:
                    pivot[indic_par_hab_temp] = np.nan    # On crée une colonne vide pour quand même afficher un graphe vide dans lequel on ajoutera des infos pour l'utilisateurs
                liste_indic_temp.append(indic_par_hab_temp)
            indicateurs_a_tracer = liste_indic_temp
        else:
            for indic in indicateurs_a_tracer:
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)    # remarque : on pourrait mettre
                else:                                                                                                                                                           # un != (car NaN != 0 renvoit True et derrière ça marcherait)
                    pivot[indic] = np.nan # Pareil que précédemment                                                                                                          # au lieu de > mais ce ne serait pas "propre"
    
    if afficher_les_deux:                                                                                                                                                           
        titre_graphe = f"Analyse croisée du département : {nom_dep}"
    else:
        titre_graphe = f"Comparaison d'indicateurs du département : {nom_dep}"
        
    # On appelle proprement la fonction en activant l'interrupteur 'superposer=True'
    fig = generer_graphiques(pivot, titre_graphe, indicateurs_a_tracer, par_habitant, afficher_les_deux, superposer=True)

    colonnes_utiles = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = pivot[[colonne for colonne in colonnes_utiles if colonne in pivot.columns]].round(1).sort_values(by=["Exercice"])
   
    return fig, df_final



##########
#####
# FONCTIONS "COEUR" DE COMPARAISON ET RECHERCHE
#####
##########
def departements_meme_strate(df_arg, code_dep, mm_region=False):
    df_temp = df_arg.copy()
    code_dep = str(code_dep)
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    if df_dep_cible.empty: 
        return pd.DataFrame()

    strate = df_dep_cible["Strate population 2024"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0]
    
    serie_filtre = df_temp["Strate population 2024"] == strate
    if mm_region:
        serie_filtre = serie_filtre & (df_temp["Nom 2024 Région"] == region)

    df_resultat = df_temp.loc[serie_filtre, ["Code Insee 2024 Département", "Nom 2024 Département", "Nom 2024 Région"]].drop_duplicates()
    df_resultat = df_resultat[df_resultat["Code Insee 2024 Département"] != code_dep]
    
    return df_resultat.reset_index(drop=True)


def comparer_departements(df_arg, liste_codes_dep, intervalle_annees, indicateurs, par_habitant=False, afficher_les_deux=False):
    df_temp = df_arg.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    annee_min_temp, annee_max_temp = intervalle_annees
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & (df_temp["Code Insee 2024 Département"].isin(liste_codes_dep)) & (annee_min_temp <= df_temp["Exercice"]) & (df_temp["Exercice"] <= annee_max_temp)
                    
    index_colonnes = ["Exercice", "Nom 2024 Département", "Population totale"]

    pivot = df_temp[serie_filtre].pivot_table(index=index_colonnes, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()    # aggfunc permet d'avoir la somme de toutes les lignes d'épargne nette par exemple
    
    if pivot.empty: # Sécurité
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée disponible", fontsize=12, fontweight="bold", ha='center', va='center')
        return fig, pd.DataFrame()

    if "Capacité de désendettement (années)" in indicateurs:
        pivot["Capacité de désendettement (vraie)"] = pivot.apply(
            lambda ligne: ligne.get("Encours de dette", 0) / ligne["Epargne brute"] if ligne.get("Epargne brute", 0) != 0 else (float('inf') if ligne.get("Encours de dette", 0) > 0 else np.nan), 
            axis=1
        ) 
        def borner(val):
            if pd.isna(val):
                return np.nan
            if val == float('inf') or val > 15:
                return 15
            if val < -3:
                return -3
            return val        
        pivot["Capacité de désendettement (années)"] = pivot["Capacité de désendettement (vraie)"].apply(borner) 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    if "Poids des AIS (%)" in indicateurs:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        pivot["Poids des AIS (%)"] = np.where(
            pivot.get("Dépenses de fonctionnement", 0) != 0, 
            ((pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)) / pivot.get("Dépenses de fonctionnement", 1)) * 100, 
            np.nan    # On ne trace pas le point du poids des AIS quand les dépenses de fctnmt sont nulles ou introuvables
        )
        
    indicateurs_a_tracer = indicateurs.copy()

    for indic in indicateurs_a_tracer:
         if indic not in pivot.columns:
            pivot[indic] = np.nan
      
    if par_habitant:
        if afficher_les_deux:
            liste_indic_temp = []    # On crée une nouvelle liste pour avoir les graphiques avec les données brutes et les données normalisées d'un même indic sur la même ligne
            for indic in indicateurs_a_tracer:
                liste_indic_temp.append(indic)
                indic_par_hab_temp = f"{indic} (€/hab)"
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic_par_hab_temp] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)
                else:
                    pivot[indic_par_hab_temp] = np.nan    # On crée une colonne vide pour quand même afficher un graphe vide dans lequel on ajoutera des infos pour l'utilisateurs
                liste_indic_temp.append(indic_par_hab_temp)
            indicateurs_a_tracer = liste_indic_temp
        else:
            for indic in indicateurs_a_tracer:
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)    # remarque : on pourrait mettre
                else:                                                                                                                                                                                                                                                                                                                                   # un != (car NaN != 0 renvoit True et derrière ça marcherait)
                    pivot[indic] = np.nan # Pareil que précédemment                                                                                                                                                                                                                                                                                # au lieu de > mais ce ne serait pas "propre"

    fig = generer_graphiques(pivot, "Analyse Financière Comparative", indicateurs_a_tracer, par_habitant, afficher_les_deux)

    colonnes_utiles = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = pivot[[colonne for colonne in colonnes_utiles if colonne in pivot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    
    return fig, df_final


def comparer_departement_strate(df_arg, code_dep, intervalle_annees, indicateurs, afficher_france=True, afficher_region=False, par_habitant=False, afficher_les_deux=False):
    df_temp = df_arg.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min_temp, annee_max_temp = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    if df_dep_cible.empty: # Sécurité
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée disponible", fontsize=12, fontweight="bold", ha='center', va='center')
        return fig, pd.DataFrame()
        
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0]
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & (df_temp["Strate population 2024"] == strate) & (annee_min_temp <= df_temp["Exercice"]) & (df_temp["Exercice"] <= annee_max_temp)
                    
    index_colonnes = ["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Nom 2024 Région", "Population totale"]

    pivot = df_temp[serie_filtre].pivot_table(index=index_colonnes, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()    # aggfunc permet d'avoir la somme de toutes les lignes d'épargne nette par exemple
    
    if pivot.empty: # Sécurité
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée disponible", fontsize=12, fontweight="bold", ha='center', va='center')
        return fig, pd.DataFrame()

    if "Capacité de désendettement (années)" in indicateurs:
        pivot["Capacité de désendettement (vraie)"] = pivot.apply(
            lambda ligne: ligne.get("Encours de dette", 0) / ligne["Epargne brute"] if ligne.get("Epargne brute", 0) != 0 else (float('inf') if ligne.get("Encours de dette", 0) > 0 else np.nan), 
            axis=1
        ) 
        def borner(val):
            if pd.isna(val):
                return np.nan
            if val == float('inf') or val > 15:
                return 15
            if val < -3:
                return -3
            return val        
        pivot["Capacité de désendettement (années)"] = pivot["Capacité de désendettement (vraie)"].apply(borner) 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    if "Poids des AIS (%)" in indicateurs:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        pivot["Poids des AIS (%)"] = np.where(
            pivot.get("Dépenses de fonctionnement", 0) != 0, 
            ((pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)) / pivot.get("Dépenses de fonctionnement", 1)) * 100, 
            np.nan    # On ne trace pas le point du poids des AIS quand les dépenses de fctnmt sont nulles ou introuvables
        )
        
    indicateurs_a_tracer = indicateurs.copy()

    for indic in indicateurs_a_tracer:
         if indic not in pivot.columns:
            pivot[indic] = np.nan
      
    if par_habitant:
        if afficher_les_deux:
            liste_indic_temp = []    # On crée une nouvelle liste pour avoir les graphiques avec les données brutes et les données normalisées d'un même indic sur la même ligne
            for indic in indicateurs_a_tracer:
                liste_indic_temp.append(indic)
                indic_par_hab_temp = f"{indic} (€/hab)"
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic_par_hab_temp] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)
                else:
                    pivot[indic_par_hab_temp] = np.nan    # On crée une colonne vide pour quand même afficher un graphe vide dans lequel on ajoutera des infos pour l'utilisateurs
                liste_indic_temp.append(indic_par_hab_temp)
            indicateurs_a_tracer = liste_indic_temp
        else:
            for indic in indicateurs_a_tracer:
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)    # remarque : on pourrait mettre
                else:                                                                                                                                                                                                                                                                                                                                   # un != (car NaN != 0 renvoit True et derrière ça marcherait)
                    pivot[indic] = np.nan # Pareil que précédemment                                                                                                                                                                                                                                                                                # au lieu de > mais ce ne serait pas "propre"

    df_cible = pivot[pivot["Code Insee 2024 Département"] == code_dep].copy()
    df_autres = pivot[pivot["Code Insee 2024 Département"] != code_dep].copy()
    
    cols_mean = [c for c in indicateurs_a_tracer + ["Capacité de désendettement (vraie)"] if c in df_autres.columns]
    
    list_df_to_concat = [df_cible]
    if afficher_france and not df_autres.empty:
        df_moyenne_france = df_autres.groupby("Exercice")[cols_mean].mean().reset_index()
        df_moyenne_france["Nom 2024 Département"] = f"Moyenne Strate {strate} (France)"
        list_df_to_concat.append(df_moyenne_france)
        
    if afficher_region and not df_autres.empty:
        df_autres_region = df_autres[df_autres["Nom 2024 Région"] == region]
        if not df_autres_region.empty:
            df_moyenne_region = df_autres_region.groupby("Exercice")[cols_mean].mean().reset_index()
            df_moyenne_region["Nom 2024 Département"] = f"Moyenne Strate {strate} (même région)"
            list_df_to_concat.append(df_moyenne_region)
            
    df_plot = pd.concat(list_df_to_concat, ignore_index=True)

    fig = generer_graphiques(df_plot, f"{nom_dep} comparé à la moyenne de sa strate", indicateurs_a_tracer, par_habitant, afficher_les_deux)

    colonnes_utiles = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = df_plot[[colonne for colonne in colonnes_utiles if colonne in df_plot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    
    return fig, df_final


def comparer_departement_strate_metro(df_arg, code_dep, intervalle_annees, indicateurs, meme_region=False, par_habitant=False, afficher_les_deux=False):
    df_temp = df_arg.copy()
    df_temp["Code Insee 2024 Département"] = df_temp["Code Insee 2024 Département"].astype(str)
    code_dep = str(code_dep)
    annee_min_temp, annee_max_temp = intervalle_annees
    
    df_dep_cible = df_temp[df_temp["Code Insee 2024 Département"] == code_dep]
    if df_dep_cible.empty: # Sécurité
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée disponible", fontsize=12, fontweight="bold", ha='center', va='center')
        return fig, pd.DataFrame()
        
    strate = df_dep_cible["Strate population 2024"].iloc[0]
    nom_dep = df_dep_cible["Nom 2024 Département"].iloc[0]
    region = df_dep_cible["Nom 2024 Région"].iloc[0]
    
    serie_filtre = (df_temp["Type de budget"] == "Budget principal") & ((df_temp["Outre-mer"] == "Non") | (df_temp["Code Insee 2024 Département"] == code_dep)) & (annee_min_temp <= df_temp["Exercice"]) & (df_temp["Exercice"] <= annee_max_temp)
                    
    index_colonnes = ["Exercice", "Code Insee 2024 Département", "Nom 2024 Département", "Strate population 2024", "Outre-mer", "Nom 2024 Région", "Population totale"]

    pivot = df_temp[serie_filtre].pivot_table(index=index_colonnes, columns="Agrégat", values="Montant", aggfunc="sum").reset_index()    # aggfunc permet d'avoir la somme de toutes les lignes d'épargne nette par exemple
    
    if pivot.empty: # Sécurité
        fig, ax = plt.subplots()
        ax.text(0.5, 0.5, "Aucune donnée disponible", fontsize=12, fontweight="bold", ha='center', va='center')
        return fig, pd.DataFrame()

    if "Capacité de désendettement (années)" in indicateurs:
        pivot["Capacité de désendettement (vraie)"] = pivot.apply(
            lambda ligne: ligne.get("Encours de dette", 0) / ligne["Epargne brute"] if ligne.get("Epargne brute", 0) != 0 else (float('inf') if ligne.get("Encours de dette", 0) > 0 else np.nan), 
            axis=1
        ) 
        def borner(val):
            if pd.isna(val):
                return np.nan
            if val == float('inf') or val > 15:
                return 15
            if val < -3:
                return -3
            return val        
        pivot["Capacité de désendettement (années)"] = pivot["Capacité de désendettement (vraie)"].apply(borner) 
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                
    if "Poids des AIS (%)" in indicateurs:                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  
        pivot["Poids des AIS (%)"] = np.where(
            pivot.get("Dépenses de fonctionnement", 0) != 0, 
            ((pivot.get("Allocations RSA", 0) + pivot.get("Allocations APA", 0) + pivot.get("Allocations PCH", 0)) / pivot.get("Dépenses de fonctionnement", 1)) * 100, 
            np.nan    # On ne trace pas le point du poids des AIS quand les dépenses de fctnmt sont nulles ou introuvables
        )
        
    indicateurs_a_tracer = indicateurs.copy()

    for indic in indicateurs_a_tracer:
         if indic not in pivot.columns:
            pivot[indic] = np.nan
      
    if par_habitant:
        if afficher_les_deux:
            liste_indic_temp = []    # On crée une nouvelle liste pour avoir les graphiques avec les données brutes et les données normalisées d'un même indic sur la même ligne
            for indic in indicateurs_a_tracer:
                liste_indic_temp.append(indic)
                indic_par_hab_temp = f"{indic} (€/hab)"
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic_par_hab_temp] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)
                else:
                    pivot[indic_par_hab_temp] = np.nan    # On crée une colonne vide pour quand même afficher un graphe vide dans lequel on ajoutera des infos pour l'utilisateurs
                liste_indic_temp.append(indic_par_hab_temp)
            indicateurs_a_tracer = liste_indic_temp
        else:
            for indic in indicateurs_a_tracer:
                if indic not in ["Capacité de désendettement (années)", "Poids des AIS (%)", "Capacité de désendettement (vraie)"]:
                    pivot[indic] = pivot.apply(lambda ligne: ligne[indic] / ligne["Population totale"] if ligne.get("Population totale", 0) > 0 else np.nan, axis=1)    # remarque : on pourrait mettre
                else:                                                                                                                                                                                                                                                                                                                                   # un != (car NaN != 0 renvoit True et derrière ça marcherait)
                    pivot[indic] = np.nan # Pareil que précédemment                                                                                                                                                                                                                                                                                # au lieu de > mais ce ne serait pas "propre"

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

    fig = generer_graphiques(df_plot, f"{nom_dep} comparé à la moyenne de sa strate et à la moyenne de la métropole", indicateurs_a_tracer, par_habitant, afficher_les_deux)

    colonnes_utiles = ["Exercice", "Nom 2024 Département"] + indicateurs_a_tracer
    df_final = df_plot[[colonne for colonne in colonnes_utiles if colonne in df_plot.columns]].round(1).sort_values(by=["Exercice", "Nom 2024 Département"])
    
    return fig, df_final


##########
#####
# L'INTERFACE GRAPHIQUE UTILISATEUR (STREAMLIT)
#####
##########
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


st.sidebar.markdown(
    "<h3 style='font-size: 22px; font-weight: bold; margin-bottom: 10px;'>Paramètres Globaux</h3>", 
    unsafe_allow_html=True
)

st.sidebar.markdown("**📂 Choix des indicateurs par thème :**")

indicateurs_choisis = []

for main_cat, subcats in sorted(dico_indicateurs.items()):
    with st.sidebar.expander(main_cat, expanded=False):
        for subcat_name, indicators_list in subcats.items():
            
            if subcat_name != "Indicateurs":
                st.markdown(f"**{subcat_name}**")
            
            defauts_cat = [indic for indic in indicators_list if indic in indicateurs_calculés]
            
            choix = st.multiselect(
                label=subcat_name,
                options=indicators_list,
                default=defauts_cat,
                key=f"ms_{main_cat}_{subcat_name}",
                label_visibility="collapsed" if subcat_name != "Indicateurs" else "visible" 
            )
            indicateurs_choisis.extend(choix)

indicateurs_choisis = list(dict.fromkeys(indicateurs_choisis))

st.sidebar.markdown("<br>", unsafe_allow_html=True)

par_habitant = st.sidebar.checkbox("Normaliser les données (€/hab)")

afficher_les_deux = False
if par_habitant:
    afficher_les_deux = st.sidebar.checkbox("Afficher la donnée brute ET la normalisée")

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

if menu != "Recherche départements de même strate":
    facteur_graphes = 2 if (par_habitant and afficher_les_deux) else 1
    total_graphes = len(indicateurs_choisis) * facteur_graphes
    if total_graphes > 10:
        st.error(f"❌ **Limite de graphiques dépassée ({total_graphes}/10 max) :** Votre configuration actuelle demande {total_graphes} graphiques. Veuillez réduire le nombre d'indicateurs cochés ou décocher l'affichage côte à côte.")
        st.stop()


if menu == "Analyser un seul département":
    st.header("🎯 Analyse d'un seul département")
    dep = st.selectbox("Sélectionnez le département à analyser :", liste_deps)
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=annee_min, max_value=annee_max, value=(annee_min, annee_max))
        
    if st.button("Lancer l'analyse"):
        fig, data = analyser_un_departement(df, dep, annees_sel, indicateurs_choisis, par_habitant, afficher_les_deux)
        if fig:
            buf = io.BytesIO()
            fig.savefig(buf, format="pdf", bbox_inches="tight")
            st.download_button(
                label="📥 Télécharger le graphique en PDF",
                data=buf.getvalue(),
                file_name=f"Analyse_{dep}.pdf",
                mime="application/pdf"
            )
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
        st.write("") 
        st.write("")
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
                           min_value=annee_min, max_value=annee_max, value=(annee_min, annee_max))
        
    if st.button("Lancer la comparaison"):
        if len(deps_selectionnes) == 0:
            st.warning("⚠️ Veuillez sélectionner au moins un département pour lancer la comparaison.")
        else:
            fig, data = comparer_departements(df, deps_selectionnes, annees_sel, indicateurs_choisis, par_habitant, afficher_les_deux)
            if fig:
                buf = io.BytesIO()
                fig.savefig(buf, format="pdf", bbox_inches="tight")
                st.download_button(
                    label="📥 Télécharger le graphique en PDF",
                    data=buf.getvalue(),
                    file_name="Comparaison_departements.pdf",
                    mime="application/pdf"
                )
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
        afficher_france = st.checkbox("Afficher la moyenne de la strate (France)", value=True)
        afficher_region = st.checkbox("Afficher la moyenne de la strate (Même région)", value=False)
        
    annees_sel = st.slider("Sélectionnez l'intervalle des années (Exercices) :", 
                           min_value=annee_min, max_value=annee_max, value=(annee_min, annee_max))
        
    if st.button("Générer l'analyse"):
        if not afficher_france and not afficher_region:
            st.error("⚠️ Veuillez cocher au moins une moyenne à afficher (France et/ou Même région).")
        else:
            fig, data = comparer_departement_strate(df, dep, annees_sel, indicateurs_choisis, afficher_france, afficher_region, par_habitant, afficher_les_deux)
            if fig:    
                buf = io.BytesIO()
                fig.savefig(buf, format="pdf", bbox_inches="tight")
                st.download_button(
                    label="📥 Télécharger le graphique en PDF",
                    data=buf.getvalue(),
                    file_name=f"Comparaison_Strate_{dep}.pdf",
                    mime="application/pdf"
                )
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
                           min_value=annee_min, max_value=annee_max, value=(annee_min, annee_max))
        
    if st.button("Générer l'analyse complète"):
        fig, data = comparer_departement_strate_metro(df, dep, annees_sel, indicateurs_choisis, meme_region, par_habitant, afficher_les_deux)
        if fig:        
            buf = io.BytesIO()
            fig.savefig(buf, format="pdf", bbox_inches="tight")
            st.download_button(
                label="📥 Télécharger le graphique en PDF",
                data=buf.getvalue(),
                file_name=f"Comparaison_Strate_Metro_{dep}.pdf",
                mime="application/pdf"
            )
            st.pyplot(fig)
            st.subheader("📋 Données brutes")
            st.dataframe(data, use_container_width=True)
