import logging
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv

# Force le rechargement du fichier .env
load_dotenv(override=True)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def send_client_report(recipient_email: str, report_path: str) -> bool:
    """Envoie le rapport Excel généré via Gmail SMTP."""
    sender_email = os.getenv("GMAIL_USER", "automationscraping4@gmail.com")
    app_password = os.getenv("GMAIL_APP_PASSWORD")

    if not app_password:
        logging.error("[!] Variable GMAIL_APP_PASSWORD introuvable dans le fichier .env.")
        return False

    if not os.path.exists(report_path):
        logging.error(f"[!] Fichier de rapport introuvable : {report_path}")
        return False

    msg = EmailMessage()
    msg["Subject"] = "Votre rapport d'extraction e-commerce"
    msg["From"] = f"Automation Bot <{sender_email}>"
    msg["To"] = recipient_email
    msg.set_content(
        "Bonjour,\n\nVeuillez trouver ci-joint votre rapport d'extraction e-commerce.\n\nCordialement,"
    )

    # Pièce jointe Excel
    with open(report_path, "rb") as f:
        file_data = f.read()
        file_name = os.path.basename(report_path)
        msg.add_attachment(
            file_data,
            maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=file_name,
        )

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(sender_email, app_password)
            smtp.send_message(msg)
        logging.info(f"[+] Email envoyé avec succès à {recipient_email} via {sender_email} !")
        return True
    except Exception as e:
        logging.error(f"[!] Échec de l'envoi SMTP : {e}")
        return False