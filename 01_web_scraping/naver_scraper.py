import json
from datetime import datetime
import pandas as pd
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


class NaverShoppingScraper:
    """Scraper e-commerce Naver Shopping (bypass anti-bot 418 via Playwright)."""

    def __init__(self, keyword: str = "마스크팩"):
        self.keyword = keyword
        self.url = f"https://search.shopping.naver.com/search/all?query={self.keyword}"

    def fetch_page(self) -> str | None:
        """Ouvre un navigateur Chromium réel pour simuler une visite humaine."""
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                        " AppleWebKit/537.36 (KHTML, like Gecko)"
                        " Chrome/128.0.0.0 Safari/537.36"
                    ),
                    locale="ko-KR",
                )
                print(f"[+] Connexion à Naver pour : '{self.keyword}'...")
                page.goto(self.url, wait_until="networkidle", timeout=30000)
                content = page.content()
                browser.close()
                print("[+] Page Naver récupérée avec succès !")
                return content
        except Exception as e:
            print(f"[-] Erreur Playwright : {e}")
            return None

    def parse_products(self, html_content: str) -> list[dict]:
        soup = BeautifulSoup(html_content, "html.parser")
        products = []
        script_tag = soup.find("script", id="__NEXT_DATA__")
        if script_tag and script_tag.string:
            try:
                data = json.loads(script_tag.string)
                items = (
                    data.get("props", {})
                    .get("pageProps", {})
                    .get("initialResult", {})
                    .get("searchResult", {})
                    .get("products", [])
                )
                for item in items:
                    products.append(
                        {
                            "id": item.get("id"),
                            "title": item.get("productTitle"),
                            "price_krw": item.get("price"),
                            "brand": item.get("brand", "N/A"),
                            "mall_name": item.get("mallName"),
                            "review_count": item.get("reviewCount", 0),
                            "rating": item.get("scoreInfo", "N/A"),
                            "link": item.get("crUrl"),
                            "scraped_at": datetime.now().strftime(
                                "%Y-%m-%d %H:%M:%S"
                            ),
                        }
                    )
            except Exception as e:
                print(f"[-] Erreur JSON : {e}")

        print(f"[+] {len(products)} produits extraits.")
        return products

    def export_to_excel(
        self,
        products: list[dict],
        filename: str = "naver_kbeauty_trends.xlsx",
    ):
        if not products:
            print("[-] Aucune donnée à exporter.")
            return

        df = pd.DataFrame(products)
        df["price_krw"] = pd.to_numeric(df["price_krw"], errors="coerce")
        df["est_price_usd"] = (df["price_krw"] / 1330).round(2)

        filepath = f"01_web_scraping/{filename}"
        df.to_excel(filepath, index=False, engine="openpyxl")
        print(f"[✓] Rapport Excel généré avec succès : {filepath}")


if __name__ == "__main__":
    scraper = NaverShoppingScraper(keyword="마스크팩")
    html = scraper.fetch_page()
    if html:
        data = scraper.parse_products(html)
        scraper.export_to_excel(data)