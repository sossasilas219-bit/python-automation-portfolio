import os
import base64
import logging
import resend

# Récupération sécurisée de la clé API
# La clé réelle sera lue depuis les variables d'environnement
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "re_123456789_placeholder_for_github")
resend.api_key = RESEND_API_KEY

def send_client_report(recipient_email, report_path):
    """
    Envoie le rapport Excel généré au destinataire via l'API Resend.
    """
    if not os.path.exists(report_path):
        logging.error(f"Fichier de rapport introuvable : {report_path}")
        return False

    try:
        # Encodage du fichier Excel en Base64 pour la pièce jointe
        with open(report_path, "rb") as f:
            file_data = f.read()
            encoded_file = base64.b64encode(file_data).decode("utf-8")

        filename = os.path.basename(report_path)

        # Structure du message
        email_parameters = {
            "from": "Market Intelligence <onboarding@resend.dev>",
            "to": [recipient_email],
            "subject": "📊 Rapport d'Intelligence Marché E-Commerce",
            "html": """
                <h2>Rapport d'analyse e-commerce</h2>
                <p>Bonjour,</p>
                <p>Veuillez trouver en pièce jointe le rapport quotidien généré automatiquement par le pipeline.</p>
                <br>
                <p><i>Message envoyé automatiquement par Python Automation Pipeline.</i></p>
            """,
            "attachments": [
                {
                    "filename": filename,
                    "content": encoded_file
                }
            ]
        }

        # Expédition via Resend
        response = resend.Emails.send(email_parameters)
        logging.info(f"E-mail envoyé à {recipient_email} (ID: {response.get('id')})")
        return True

    except Exception as e:
        logging.error(f"Erreur d'envoi de l'e-mail : {e}")
        raise e