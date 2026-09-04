import logging
import os
import sys

# Ajout des modules au chemin système
sys.path.append(os.path.abspath("01_web_scraping"))
sys.path.append(os.path.abspath("02_workflow_automation"))

from email_sender import send_client_report
from report_generator import generate_daily_report

# Configuration du journal d'exécution (logs)
logging.basicConfig(
    filename="app.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)


def run_pipeline():
    print("=== DÉMARRAGE DU PIPELINE MARKET INTELLIGENCE ===")
    logging.info("Lancement du pipeline.")

    # 1. Génération du rapport Excel depuis SQLite
    print("\n[1/2] Génération du rapport automatisé...")
    report_file = generate_daily_report()

    if not report_file:
        print("[-] Échec : Impossible de générer le rapport Excel.")
        logging.error("Échec de la génération du rapport Excel.")
        return False

    # 2. Envoi du rapport par e-mail au client
    print("\n[2/2] Expédition du rapport au client via Resend...")
    status = send_client_report(
        recipient_email="sossasilas219@gmail.com", report_path=report_file
    )

    if status:
        print("\n=== [✓] PIPELINE EXÉCUTÉ AVEC SUCCÈS ! ===")
        logging.info("Pipeline exécuté avec succès.")
    else:
        print("\n[-] Échec lors de la livraison du rapport.")
        logging.warning("Échec de l'envoi du rapport.")

    return status


if __name__ == "__main__":
    run_pipeline()