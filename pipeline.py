import os
import importlib
import pandas as pd
from datetime import datetime

# 1. Import sécurisé du scraper
try:
    scraper_module = importlib.import_module("01_web_scraping.hybrid_market_scraper")
    PortfolioScraper = scraper_module.PortfolioScraper
except Exception:
    from hybrid_market_scraper import PortfolioScraper

# 2. Import sécurisé de la base de données (SQLite)
save_to_db = None
try:
    from database import save_to_db
except ImportError:
    try:
        db_module = importlib.import_module("02_database.database")
        save_to_db = getattr(db_module, "save_to_db", None)
    except ImportError:
        pass

# 3. Import sécurisé du module d'email
send_client_report = None
try:
    from email_sender import send_client_report
except ImportError:
    pass


def run_pipeline():
    print("=" * 50)
    print("  DÉMARRAGE DU PIPELINE D'AUTOMATISATION")
    print("=" * 50)

    # ÉTAPE 1 : Scraping dynamique
    scraper = PortfolioScraper()
    raw_data = scraper.fetch_data()

    if not raw_data:
        print("[!] Aucun résultat extrait. Fin du programme.")
        return

    # ÉTAPE 2 : Sauvegarde en Base de données (si le module existe)
    if save_to_db:
        try:
            save_to_db(raw_data)
            print("[+] Étape 2/4 : Données enregistrées dans SQLite.")
        except Exception as e:
            print(f"[!] Erreur SQLite : {e}")
    else:
        print("[i] Étape 2/4 : Ignorée (module SQLite introuvable).")

    # ÉTAPE 3 : Génération du fichier Excel
    df = pd.DataFrame(raw_data)
    date_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_filename = f"rapport_{scraper.keyword}_{date_str}.xlsx"
    excel_path = os.path.join(os.getcwd(), excel_filename)

    df.to_excel(excel_path, index=False)
    print(f"[+] Étape 3/4 : Rapport Excel créé -> {excel_filename}")

    # ÉTAPE 4 : Notification Email
    if send_client_report:
        recipient = "adamgik48@gmail.com"
        send_client_report(recipient, excel_path)
        print("[+] Étape 4/4 : Traitement de l'envoi d'email terminé.")
    else:
        print("[i] Étape 4/4 : Ignorée (module email introuvable).")

    print("\n[✔] PIPELINE EXÉCUTÉ AVEC SUCCÈS !")


if __name__ == "__main__":
    run_pipeline()