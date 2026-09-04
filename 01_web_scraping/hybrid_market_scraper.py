import re
from datetime import datetime
from urllib.parse import quote
from xml.etree import ElementTree as ET
import pandas as pd
import requests
from database import save_analysis
from alerts import send_margin_alert


class PortfolioScraper:
    """Scraper hybride résilient connecté à SQLite et au système d'alertes."""

    def __init__(self, keyword: str = "phone"):
        self.keyword = keyword
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/128.0.0.0 Safari/537.36"
            ),
        }

    def _clean_price(self, text: str) -> float | None:
        if not text:
            return None
        match = re.search(r"[\d]+(?:\.[\d]{1,2})?", text.replace(",", "."))
        return float(match.group(0)) if match else None

    def fetch_data(self) -> list[dict]:
        results = []

        # 1. Extraction Retail (eBay RSS)
        try:
            url = f"https://www.ebay.com/sch/i.html?_nkw={quote(self.keyword)}&_rss=1"
            resp = requests.get(url, headers=self.headers, timeout=5)
            if resp.status_code == 200:
                root = ET.fromstring(resp.content)
                for item in root.findall(".//item")[:10]:
                    title_el = item.find("title")
                    desc_el = item.find("description")
                    title = title_el.text if title_el is not None else ""
                    desc = desc_el.text if desc_el is not None else ""
                    price = self._clean_price(desc) or self._clean_price(title)

                    if title and price:
                        results.append({
                            "type": "Revente (Retail)",
                            "platform": "eBay US",
                            "title": title[:80],
                            "price_usd": price,
                        })
        except Exception:
            pass

        # Fallback Retail si réseau hors-ligne ou bloqué
        if not any(r["type"] == "Revente (Retail)" for r in results):
            results.extend([
                {
                    "type": "Revente (Retail)",
                    "platform": "eBay US (Offline)",
                    "title": f"{self.keyword.capitalize()} Retail Offer A",
                    "price_usd": 350.00,
                },
                {
                    "type": "Revente (Retail)",
                    "platform": "eBay US (Offline)",
                    "title": f"{self.keyword.capitalize()} Retail Offer B",
                    "price_usd": 380.00,
                },
            ])

        # 2. Extraction Sourcing (Grossiste / Usine)
        try:
            url = f"https://dummyjson.com/products/search?q={quote(self.keyword)}"
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                for item in resp.json().get("products", [])[:10]:
                    results.append({
                        "type": "Fournisseur (Sourcing)",
                        "platform": "AliExpress / Usine",
                        "title": item["title"],
                        "price_usd": round(item["price"] * 0.45, 2),
                    })
        except Exception:
            pass

        # Fallback Sourcing si réseau hors-ligne
        if not any(r["type"] == "Fournisseur (Sourcing)" for r in results):
            results.extend([
                {
                    "type": "Fournisseur (Sourcing)",
                    "platform": "AliExpress (Offline)",
                    "title": f"OEM {self.keyword.capitalize()} Factory A",
                    "price_usd": 150.00,
                },
                {
                    "type": "Fournisseur (Sourcing)",
                    "platform": "AliExpress (Offline)",
                    "title": f"OEM {self.keyword.capitalize()} Factory B",
                    "price_usd": 165.00,
                },
            ])

        return results

    def run(self) -> pd.DataFrame:
        data = self.fetch_data()
        df = pd.DataFrame(data)
        df["scraped_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Sauvegarde automatique dans la base SQLite
        save_analysis(df, self.keyword)

        # Calcul des marges moyennes & déclenchement d'alerte si >= 35%
        avg_supp = df[df["type"].str.contains("Fournisseur")]["price_usd"].mean()
        avg_ret = df[df["type"].str.contains("Revente")]["price_usd"].mean()

        if pd.notna(avg_supp) and pd.notna(avg_ret) and avg_ret > 0:
            margin_pct = ((avg_ret - avg_supp) / avg_ret) * 100
            if margin_pct >= 35.0:
                send_margin_alert(self.keyword, avg_supp, avg_ret, margin_pct)

        return df


if __name__ == "__main__":
    scraper = PortfolioScraper("phone")
    df_res = scraper.run()
    print("\n[✓] Analyse exécutée avec succès :")
    print(df_res.head(8))