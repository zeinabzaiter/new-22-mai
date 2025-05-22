import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Surveillance RAM - Staph aureus", layout="wide")

@st.cache_data
def load_data():
    staph_data = pd.read_excel("staph aureus hebdomadaire excel.xlsx")
    staph_data.columns = staph_data.columns.str.strip()
    bacteries_list = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    tests_semaine = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    phenotypes = pd.read_excel("staph_aureus_pheno_final.xlsx")
    other_ab = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    return staph_data, bacteries_list, tests_semaine, phenotypes, other_ab

staph_data, bacteries_list, tests_semaine, phenotypes, other_ab = load_data()

st.title("Surveillance Dynamique de la Résistance aux Antimicrobiens")
st.markdown("Bienvenue dans le tableau de bord de suivi de la résistance bactérienne pour l'année 2024.")

# Harmonisation des colonnes
phenotypes = phenotypes[~phenotypes['week'].astype(str).str.contains("Total", na=False)]
phenotypes['week'] = pd.to_datetime(phenotypes['week'], errors='coerce')
other_ab = other_ab.rename(columns={"week": "Semaine", "Week": "Semaine"})

# Tabs
tabs = st.tabs([
    "Vue générale",
    "Staph aureus - Phénotypes",
    "Staph aureus - Antibiotiques",
    "Staph aureus - Autres AB",
    "Alertes par Service",
    "Fiche patient"
])

# Onglet 1: Vue générale
with tabs[0]:
    st.subheader("Bactéries suivies en 2024")
    st.dataframe(bacteries_list)

# Onglet 2: Phénotypes
with tabs[1]:
    st.subheader("Phénotypes - Staph aureus")
    pheno_columns = [col for col in phenotypes.columns if col.lower() not in ['week']]
    selected_pheno = st.selectbox("Choisir un phénotype", pheno_columns)

    try:
        col_values = pd.to_numeric(phenotypes[selected_pheno], errors='coerce').dropna()
        if selected_pheno.upper() in ['VRSA', 'VANCOMYCIN']:
            phenotypes['Alarme'] = phenotypes[selected_pheno] > 0
            seuil_info = "Alerte dès 1 cas"
        else:
            Q1 = col_values.quantile(0.25)
            Q3 = col_values.quantile(0.75)
            IQR = Q3 - Q1
            tukey_threshold = Q3 + 1.5 * IQR
            phenotypes['Alarme'] = phenotypes[selected_pheno] > tukey_threshold
            seuil_info = f"Seuil Tukey : {tukey_threshold:.2f}"

        fig = px.line(phenotypes, x='week', y=selected_pheno, title=f"% Résistance - {selected_pheno}", markers=True)
        alertes = phenotypes[phenotypes['Alarme']]
        fig.add_scatter(x=alertes['week'], y=alertes[selected_pheno], mode='markers', marker=dict(color='red', size=10), name='Alarme')
        st.plotly_chart(fig)
        st.markdown(f"Critère d’alerte pour {selected_pheno} : {seuil_info}")
    except Exception as e:
        st.error(f"Erreur : {e}")

# Onglet 3: Antibiotiques Staph aureus
with tabs[2]:
    st.subheader("Évolution des Résistances aux Antibiotiques - Staphylococcus aureus")
    ab_columns = [col for col in tests_semaine.columns if col.lower() not in ['semaine', 'week']]
    selected_ab = st.selectbox("Choisir un antibiotique", ab_columns)
    try:
        col_values = pd.to_numeric(tests_semaine[selected_ab], errors='coerce').dropna()
        Q1 = col_values.quantile(0.25)
        Q3 = col_values.quantile(0.75)
        IQR = Q3 - Q1
        tukey_threshold = Q3 + 1.5 * IQR
        if selected_ab.upper().startswith("VAN"):
            tests_semaine['Alarme'] = pd.to_numeric(tests_semaine[selected_ab], errors='coerce') > 0
        else:
            tests_semaine['Alarme'] = pd.to_numeric(tests_semaine[selected_ab], errors='coerce') > tukey_threshold

        fig_ab = px.line(tests_semaine, x='Semaine', y=selected_ab, title=f"% Résistance - {selected_ab}",
                         markers=True, labels={selected_ab: "% de résistance"},
                         hover_data={"Semaine": True, selected_ab: True})
        alertes_ab = tests_semaine[tests_semaine['Alarme'] == True]
        fig_ab.add_scatter(x=alertes_ab['Semaine'], y=alertes_ab[selected_ab], mode='markers',
                           marker=dict(color='red', size=10), name='Alarme')
        st.plotly_chart(fig_ab)
        seuil_info = "1 cas = alarme" if selected_ab.upper().startswith("VAN") else f"Seuil Tukey : **{tukey_threshold:.2f}%**"
        st.markdown(f"Critère d'alarme pour {selected_ab} : {seuil_info}")
    except Exception as e:
        st.error(f"Erreur lors du traitement de l'antibiotique {selected_ab} : {e}")

# Onglet 4: Autres Antibiotiques
with tabs[3]:
    st.subheader("Autres Antibiotiques")
    other_ab_columns = [col for col in other_ab.columns if col.lower() not in ['semaine', 'week']]
    selected_other_ab = st.selectbox("Choisir un autre AB", other_ab_columns)
    try:
        col_values = pd.to_numeric(other_ab[selected_other_ab], errors='coerce').dropna()
        Q1 = col_values.quantile(0.25)
        Q3 = col_values.quantile(0.75)
        IQR = Q3 - Q1
        tukey_threshold = Q3 + 1.5 * IQR
        other_ab['Alarme'] = pd.to_numeric(other_ab[selected_other_ab], errors='coerce') > tukey_threshold

        fig_other = px.line(other_ab, x='Semaine', y=selected_other_ab, title=f"% Résistance - {selected_other_ab}", markers=True)
        alertes = other_ab[other_ab['Alarme']]
        fig_other.add_scatter(x=alertes['Semaine'], y=alertes[selected_other_ab], mode='markers', marker=dict(color='red', size=10), name='Alarme')
        st.plotly_chart(fig_other)
    except Exception as e:
        st.error(f"Erreur : {e}")

# Onglet 5: Alertes par Service
with tabs[4]:
    st.subheader("Alertes par Service")
    staph_data['DATE_PRELEVEMENT'] = pd.to_datetime(staph_data['DATE_PRELEVEMENT'], errors='coerce')
    staph_data['Semaine'] = staph_data['DATE_PRELEVEMENT'].dt.isocalendar().week
    ab_columns_service = [col for col in staph_data.columns if col.lower() not in ['semaine', 'week', 'date_prelevement', 'libelle_demandeur']]
    selected_ab_service = st.selectbox("Choisir un AB à analyser par service", ab_columns_service)

    try:
        grouped = staph_data.groupby(['Semaine', 'LIBELLE_DEMANDEUR'])[selected_ab_service] \
            .apply(lambda x: (x == 'R').mean() * 100).reset_index()
        grouped.columns = ['Semaine', 'Service', 'Resistance (%)']
        Q1 = grouped['Resistance (%)'].quantile(0.25)
        Q3 = grouped['Resistance (%)'].quantile(0.75)
        IQR = Q3 - Q1
        tukey_threshold = Q3 + 1.5 * IQR
        grouped['Alarme'] = grouped['Resistance (%)'] > tukey_threshold

        fig_alertes = px.scatter(grouped, x='Semaine', y='Resistance (%)', color='Service', symbol='Alarme',
                                 size=grouped['Alarme'].apply(lambda x: 12 if x else 6),
                                 title=f"Alertes de résistance pour {selected_ab_service} par service")
        st.plotly_chart(fig_alertes)
        st.dataframe(grouped[grouped['Alarme']])
    except Exception as e:
        st.error(f"Erreur lors de l’analyse par service : {e}")
# Onglet 6 : Fiche patient
with tabs[5]:
    st.subheader("🧾 Fiche détaillée par patient (IPP_PASTEL)")

    # Sélection du service
    selected_service = st.selectbox("Filtrer par service :", staph_data["LIBELLE_DEMANDEUR"].dropna().unique())

    # Filtrer les patients de ce service
    patients = staph_data[staph_data["LIBELLE_DEMANDEUR"] == selected_service]["IPP_PASTEL"].dropna().unique()
    selected_patient = st.selectbox("Choisir un patient (IPP_PASTEL) :", patients)

    # Filtrage des données
    filtered_data = staph_data[staph_data["IPP_PASTEL"] == selected_patient]

    # Affichage des infos générales
    st.subheader("Informations générales")
    st.dataframe(filtered_data[["LIB_GERME", "DATE_PRELEVEMENT", "LIBELLE_DEMANDEUR"]])

    # 🔍 Sélection des colonnes d'antibiotiques uniquement
    ab_columns = [
        col for col in staph_data.columns
        if col not in ['IPP_PASTEL', 'DATE_PRELEVEMENT', 'LIBELLE_DEMANDEUR', 'LIB_GERME']
    ]

    # Résultats antibiotiques (remplir NaN avec un symbole)
    ab_results = filtered_data[ab_columns].fillna("–")

    st.subheader("Résultats des antibiotiques")
    st.dataframe(ab_results)
    # --- Onglet 5 : Alertes par Service ---
with tabs[4]:
    st.subheader("Alertes par Service")

    # Uniformiser la colonne "Semaine" si ce n'est pas déjà fait
    staph_data['Semaine'] = pd.to_datetime(staph_data['DATE_PRELEVEMENT'], errors='coerce').dt.isocalendar().week

    ab_columns = [col for col in tests_semaine.columns if col.lower() not in ['semaine', 'week']]
    selected_ab_service = st.selectbox("Choisir un AB à analyser par service", ab_columns)

    grouped = staph_data.groupby(['Semaine', 'LIBELLE_DEMANDEUR'])[selected_ab_service] \
        .apply(lambda x: (x == 'R').mean() * 100).reset_index()
    grouped.columns = ['Semaine', 'Service', 'Resistance (%)']

    # Seuil d'alarme
    Q1 = grouped['Resistance (%)'].quantile(0.25)
    Q3 = grouped['Resistance (%)'].quantile(0.75)
    IQR = Q3 - Q1
    tukey_threshold = Q3 + 1.5 * IQR

    grouped['Alarme'] = grouped['Resistance (%)'] > tukey_threshold

    # Graphique Plotly
    fig = px.scatter(
        grouped, x='Semaine', y='Resistance (%)', color='Service', symbol='Alarme',
        size=grouped['Alarme'].apply(lambda x: 12 if x else 6),
        title=f"% Résistance de {selected_ab_service} par service",
        custom_data=['Semaine']
    )

    st.plotly_chart(fig)

    # Interaction utilisateur - clic sur alarme
    from streamlit_plotly_events import plotly_events
    clicked = plotly_events(fig, select_event=True, key="alarme_click")

    if clicked:
        semaine_clic = int(clicked[0]['customdata'][0])
        st.markdown(f"### 🔍 Détails pour la semaine {semaine_clic}")

        filtered = staph_data[staph_data['Semaine'] == semaine_clic]
        if not filtered.empty:
            st.dataframe(filtered[['IPP_PASTEL', 'LIBELLE_DEMANDEUR', selected_ab_service, 'DATE_PRELEVEMENT']])
        else:
            st.info("Aucun enregistrement trouvé pour cette semaine.")

