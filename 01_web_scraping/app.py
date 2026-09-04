import plotly.express as px
import streamlit as st
from database import get_all_history
from hybrid_market_scraper import PortfolioScraper

st.set_page_config(page_title="Market Analyzer", layout="wide")

st.title("⚡ E-Commerce Market Intelligence Dashboard")
st.markdown(
    "Analyse de marge en temps réel, historique SQLite et alertes de"
    " rentabilité."
)

# Configuration de la barre latérale
st.sidebar.header("Lancer une Analyse")
keyword_input = st.sidebar.text_input("Produit à analyser", value="phone")

if st.sidebar.button("Exécuter le Scraping"):
  with st.spinner("Scraping en cours..."):
    scraper = PortfolioScraper(keyword_input)
    df_new = scraper.run()
    st.success(
        f"Analyse terminée pour '{keyword_input}' ! Données enregistrées dans"
        " SQLite."
    )

# Chargement de l'historique SQLite
df_hist = get_all_history()

if not df_hist.empty:
  st.subheader("📊 Historique des Relevés (SQLite)")

  col1, col2, col3 = st.columns(3)
  col1.metric("Total Relevés", len(df_hist))
  col2.metric(
      "Moyenne Prix Sourcing",
      f"${df_hist[df_hist['type'].str.contains('Fournisseur')]['price_usd'].mean():.2f}",
  )
  col3.metric(
      "Moyenne Prix Revente",
      f"${df_hist[df_hist['type'].str.contains('Revente')]['price_usd'].mean():.2f}",
  )

  fig = px.box(
      df_hist,
      x="keyword",
      y="price_usd",
      color="type",
      title="Distribution des Prix par Produit",
  )
  st.plotly_chart(fig, use_container_width=True)

  st.dataframe(df_hist)
else:
  st.info(
      "Aucune donnée disponible. Lancez une première analyse depuis le"
      " panneau latéral."
  )