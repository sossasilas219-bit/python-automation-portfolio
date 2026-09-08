import re
from datetime import datetime
from urllib.parse import quote_plus
import pandas as pd
import requests


class PortfolioScraper:
    """Scraper hybride résilient pour e-commerce."""

    def __init__(self, keyword: str = None):
        if not keyword:
            keyword = input("Que souhaitez-vous scraper aujourd'hui ? : ").strip()

        while not keyword:
            keyword = input("Veuillez saisir un mot-clé valide : ").strip()

        self.keyword = keyword
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }
        print(f"\n[+] Recherche lancée pour : '{self.keyword}'\n")

    def _clean_price(self, text: str) -> float | None:
        """Extrait la valeur numérique d'un prix."""
        if not text:
            return None
        clean = text.replace("$", "").replace(",", "").strip()
        match = re.search(r"\d+\.?\d*", clean)
        if match:
            try:
                return float(match.group())
            except ValueError:
                return None
        return None

    def fetch_data(self) -> list[dict]:
        """Récupère les données d'eBay HTML ou bascule sur l'API e-commerce de secours."""
        results = []
        encoded_query = quote_plus(self.keyword)

        # 1. Tentative sur eBay HTML
        ebay_url = f"https://www.ebay.com/sch/i.html?_nkw={encoded_query}"
        try:
            response = requests.get(ebay_url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                items = re.findall(
                    r'class="s-item__title"[^>]*>(?:<span[^>]*>)?(.*?)(?:</span>)?</[^>]+>.*?class="s-item__price"[^>]*>(.*?)</span>',
                    response.text,
                    re.DOTALL,
                )

                for title_raw, price_raw in items:
                    title = re.sub(r"<[^>]+>", "", title_raw).strip()
                    if "Shop on eBay" in title or not title:
                        continue

                    price = self._clean_price(price_raw)
                    if title and price:
                        results.append(
                            {
                                "type": "Revente (Retail)",
                                "platform": "eBay US",
                                "search_term": self.keyword,
                                "title": title[:80],
                                "price_usd": price,
                                "timestamp": datetime.now().strftime(
                                    "%Y-%m-%d %H:%M:%S"
                                ),
                            }
                        )
        except Exception as e:
            print(f"[!] Erreur sur la source principale : {e}")

        # 2. Source de secours (API E-Commerce publique) si 0 résultat
        if not results:
            print("[i] Basculement automatique sur l'API e-commerce de secours...")
            try:
                fallback_url = f"https://dummyjson.com/products/search?q={encoded_query}"
                res = requests.get(fallback_url, timeout=10).json()
                for prod in res.get("products", []):
                    results.append(
                        {
                            "type": "Revente (Retail)",
                            "platform": "Global Market API",
                            "search_term": self.keyword,
                            "title": prod.get("title", ""),
                            "price_usd": float(prod.get("price", 0)),
                            "timestamp": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    )
            except Exception as e:
                print(f"[!] Erreur sur la source de secours : {e}")

        return results


if __name__ == "__main__":
    scraper = PortfolioScraper()
    data = scraper.fetch_data()

    if data:
        df = pd.DataFrame(data)
        print("\n--- RÉSULTATS DU SCRAPING ---")
        print(df.to_string(index=False))
    else:
        print("[!] Aucun résultat trouvé pour cette recherche.")