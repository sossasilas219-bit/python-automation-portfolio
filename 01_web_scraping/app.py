import io
import os
import smtplib
import sys
from email.message import EmailMessage
from dotenv import load_dotenv

# Charger le fichier .env depuis la racine du projet
load_dotenv(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env")))

# Ajout du dossier parent pour les imports de la racine (database.py)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pandas as pd
import streamlit as st
from database import get_all_history, save_to_sqlite
from hybrid_market_scraper import PortfolioScraper

# Configuration de la page Streamlit
st.set_page_config(
    page_title="E-Commerce Market Intelligence Dashboard",
    page_icon="⚡",
    layout="wide",
)

st.title("⚡ E-Commerce Market Intelligence Dashboard")
st.markdown(
    "Analyse comparative multi-sources, historique SQLite, téléchargement Excel"
    " et alertes par e-mail."
)

# Panneau latéral pour les contrôles dynamiques
st.sidebar.header("Paramètres de Scraping & E-mail")
search_query = st.sidebar.text_input("Requête produit à rechercher", value="phone")

# Sélecteur dynamique des sources e-commerce incluant Playwright
selected_sources = st.sidebar.multiselect(
    "Sites marchands à comparer",
    ["DummyJSON Store", "Global Market B", "Site Web Cible (Playwright)"],
    default=["DummyJSON Store", "Global Market B", "Site Web Cible (Playwright)"],
)

recipient_email = st.sidebar.text_input(
    "E-mail destinataire", value=os.getenv("GMAIL_USER", "")
)

if st.sidebar.button("Lancer l'analyse"):
  with st.spinner("Scraping multi-sources en cours et sauvegarde..."):
    scraper = PortfolioScraper(query=search_query, sources=selected_sources)
    df_new = scraper.run()

    if not df_new.empty:
      save_to_sqlite(df_new)
      st.sidebar.success(
          f"Analyse terminée pour '{search_query}' ! Données enregistrées."
      )
      st.rerun()
    else:
      st.sidebar.warning("Aucune donnée retournée par les scrapers.")


# Fonction d'envoi d'e-mail avec pièce jointe Excel
def send_excel_email(df: pd.DataFrame, recipient: str):
  if df.empty:
    return False, "Le DataFrame est vide, aucun e-mail envoyé."

  sender_email = os.getenv("GMAIL_USER", "automationscraping4@gmail.com")
  sender_password = os.getenv("GMAIL_APP_PASSWORD", "")

  if not sender_password:
    return False, "Mot de passe e-mail (GMAIL_APP_PASSWORD) non trouvé dans .env."

  try:
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
      df.to_excel(writer, sheet_name="Market Data", index=False)
    excel_data = excel_buffer.getvalue()

    msg = EmailMessage()
    msg["Subject"] = "📊 Rapport Comparatif E-Commerce Market Intelligence"
    msg["From"] = sender_email
    msg["To"] = recipient
    msg.set_content(
        "Bonjour,\n\nVeuillez trouver ci-joint le rapport comparatif des"
        " prix généré depuis le tableau de bord.\n\nCordialement,\nVotre"
        " Pipeline Automatisé"
    )

    msg.add_attachment(
        excel_data,
        maintype="application",
        subtype=(
            "vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        filename="market_intelligence_report.xlsx",
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
      server.login(sender_email, sender_password)
      server.send_message(msg)

    return True, "E-mail envoyé avec succès !"
  except Exception as e:
    return False, f"Erreur lors de l'envoi de l'e-mail : {e}"


# Affichage des données de la base de données
st.subheader("📊 Comparatif des Prix & Historique (SQLite)")

df_history = get_all_history()

if not df_history.empty:
  st.dataframe(df_history, width="stretch")

  # Métriques clés
  col1, col2, col3 = st.columns(3)
  with col1:
    st.metric(label="Total Offres Répertoriées", value=len(df_history))
  with col2:
    if "price" in df_history.columns and not df_history["price"].empty:
      st.metric(label="Prix Moyen Global", value=f"${df_history['price'].mean():.2f}")
  with col3:
    if "price" in df_history.columns and not df_history["price"].empty:
      st.metric(label="Offre la Moins Chère", value=f"${df_history['price'].min():.2f}")

  st.markdown("---")

  # Section Actions : Téléchargement et Envoi e-mail
  col_dl, col_mail = st.columns(2)

  with col_dl:
    download_buffer = io.BytesIO()
    with pd.ExcelWriter(download_buffer, engine="openpyxl") as writer:
      df_history.to_excel(writer, sheet_name="Market Data", index=False)

    st.download_button(
        label="📥 Télécharger le rapport Excel",
        data=download_buffer.getvalue(),
        file_name="market_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        width="stretch",
    )

  with col_mail:
    if st.button("📧 Envoyer ce rapport par e-mail", width="stretch"):
      if recipient_email:
        with st.spinner("Envoi de l'e-mail en cours..."):
          success, message = send_excel_email(df_history, recipient_email)
          if success:
            st.success(message)
          else:
            st.error(message)
      else:
        st.warning(
            "Veuillez renseigner une adresse e-mail valide dans le panneau"
            " latéral."
        )
else:
  st.info("Aucune donnée disponible. Lancez une première analyse depuis le panneau latéral.")