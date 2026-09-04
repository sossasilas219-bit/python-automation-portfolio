import requests

def send_margin_alert(keyword: str, supplier_price: float, retail_price: float, margin_pct: float, bot_token: str = None, chat_id: str = None):
    """Déclenche une alerte si la marge cible (> 35%) est atteinte."""
    message = (
        f"🚨 *OPPORTUNITÉ DÉTECTÉE !*\n\n"
        f"📦 *Produit* : {keyword.upper()}\n"
        f"🏭 *Prix Sourcing* : ${supplier_price:.2f}\n"
        f"🏷️ *Prix Revente* : ${retail_price:.2f}\n"
        f"💰 *Marge Brute* : {margin_pct:.1f}%\n"
    )
    
    # Affichage terminal
    print("\n" + "="*40)
    print(message)
    print("="*40 + "\n")

    # Envoi Telegram optionnel
    if bot_token and chat_id:
        try:
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}, timeout=5)
        except Exception as e:
            print(f"[!] Échec envoi Telegram : {e}")