
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Surveillance RAM - Staph aureus", layout="wide")

@st.cache_data
def load_data():
    staph_data = pd.read_excel("staph aureus hebdomadaire excel.xlsx")
    bacteries_list = pd.read_excel("TOUS les bacteries a etudier.xlsx")
    tests_semaine = pd.read_csv("tests_par_semaine_antibiotiques_2024.csv")
    phenotypes = pd.read_excel("staph_aureus_pheno_final.xlsx")
    other_ab = pd.read_excel("other Antibiotiques staph aureus.xlsx")
    return staph_data, bacteries_list, tests_semaine, phenotypes, other_ab

staph_data, bacteries_list, tests_semaine, phenotypes, other_ab = load_data()

st.title("Surveillance Dynamique de la Résistance aux Antimicrobiens")
st.markdown("Bienvenue dans le tableau de bord de suivi de la résistance bactérienne pour l'année 2024.")

# ✅ Tabs défini AVANT toute utilisation
tabs = st.tabs([
    "Vue générale",
    "Staph aureus - Phénotypes",
    "Staph aureus - Antibiotiques",
    "Staph aureus - Autres AB",
    "Alertes par Service"
])

# --- Onglet 1 ---
with tabs[0]:
    st.subheader("Bactéries suivies en 2024")
    st.dataframe(bacteries_list)

# --- Onglet 2 ---
with tabs[1]:
    st.subheader("Phénotypes - Staph aureus")
    pheno_columns = [col for col in phenotypes.columns if col.lower() not in ['semaine', 'week']]
    selected_pheno = st.selectbox("Choisir un phénotype", pheno_columns)
    col_values = pd.to_numeric(phenotypes[selected_pheno], errors='coerce').dropna()
    Q1 = col_values.quantile(0.25)
    Q3 = col_values.quantile(0.75)
    IQR = Q3 - Q1
    tukey_threshold = Q3 + 1.5 * IQR
    phenotypes['Alarme'] = pd.to_numeric(phenotypes[selected_pheno], errors='coerce') > tukey_threshold
    fig = px.line(phenotypes, x='Semaine', y=selected_pheno, title=f"% Résistance - {selected_pheno}", markers=True)
    alertes = phenotypes[phenotypes['Alarme']]
    fig.add_scatter(x=alertes['Semaine'], y=alertes[selected_pheno], mode='markers', marker=dict(color='red', size=10), name='Alarme')
    st.plotly_chart(fig)

# --- Onglet 3 ---
with tabs[2]:
    st.subheader("Tests de sensibilité - Antibiotiques")
    ab_columns = [col for col in tests_semaine.columns if col.lower() not in ['semaine', 'week']]
    selected_ab = st.selectbox("Choisir un antibiotique", ab_columns)
    col_values = pd.to_numeric(tests_semaine[selected_ab], errors='coerce').dropna()
    Q1 = col_values.quantile(0.25)
    Q3 = col_values.quantile(0.75)
    IQR = Q3 - Q1
    tukey_threshold = Q3 + 1.5 * IQR
    if selected_ab.upper().startswith("VAN"):
        tests_semaine['Alarme'] = pd.to_numeric(tests_semaine[selected_ab], errors='coerce') > 0
    else:
        tests_semaine['Alarme'] = pd.to_numeric(tests_semaine[selected_ab], errors='coerce') > tukey_threshold
    fig = px.line(tests_semaine, x='Semaine', y=selected_ab, title=f"% Résistance - {selected_ab}", markers=True)
    alertes = tests_semaine[tests_semaine['Alarme']]
    fig.add_scatter(x=alertes['Semaine'], y=alertes[selected_ab], mode='markers', marker=dict(color='red', size=10), name='Alarme')
    st.plotly_chart(fig)

# --- Onglet 4 ---
with tabs[3]:
    st.subheader("Autres Antibiotiques")
    other_ab_columns = [col for col in other_ab.columns if col.lower() not in ['semaine', 'week']]
    selected_other_ab = st.selectbox("Choisir un autre AB", other_ab_columns)
    col_values = pd.to_numeric(other_ab[selected_other_ab], errors='coerce').dropna()
    Q1 = col_values.quantile(0.25)
    Q3 = col_values.quantile(0.75)
    IQR = Q3 - Q1
    tukey_threshold = Q3 + 1.5 * IQR
    other_ab['Alarme'] = pd.to_numeric(other_ab[selected_other_ab], errors='coerce') > tukey_threshold
    fig = px.line(other_ab, x='Semaine', y=selected_other_ab, title=f"% Résistance - {selected_other_ab}", markers=True)
    alertes = other_ab[other_ab['Alarme']]
    fig.add_scatter(x=alertes['Semaine'], y=alertes[selected_other_ab], mode='markers', marker=dict(color='red', size=10), name='Alarme')
    st.plotly_chart(fig)

# --- Onglet 5 ---
with tabs[4]:
    st.subheader("Alertes par Service")
    staph_data['DATE_PRELEVEMENT'] = pd.to_datetime(staph_data['DATE_PRELEVEMENT'], errors='coerce')
    staph_data['Semaine'] = staph_data['DATE_PRELEVEMENT'].dt.isocalendar().week
    ab_columns = [col for col in tests_semaine.columns if col.lower() not in ['semaine', 'week']]
    selected_ab_service = st.selectbox("Choisir un AB à analyser par service", ab_columns)
    grouped = staph_data.groupby(['Semaine', 'DEMANDEUR'])[selected_ab_service] \
        .apply(lambda x: (x == 'R').mean() * 100).reset_index()
    grouped.columns = ['Semaine', 'Service', 'Resistance (%)']
    Q1 = grouped['Resistance (%)'].quantile(0.25)
    Q3 = grouped['Resistance (%)'].quantile(0.75)
    IQR = Q3 - Q1
    tukey_threshold = Q3 + 1.5 * IQR
    grouped['Alarme'] = grouped['Resistance (%)'] > tukey_threshold
    fig = px.scatter(grouped, x='Semaine', y='Resistance (%)', color='Service', symbol='Alarme',
                     size=grouped['Alarme'].apply(lambda x: 12 if x else 6),
                     title=f"% Résistance de {selected_ab_service} par service")
    st.plotly_chart(fig)
    st.dataframe(grouped[grouped['Alarme']])
