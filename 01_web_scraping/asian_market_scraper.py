import json
import re
from datetime import datetime
from urllib.parse import quote
import pandas as pd
from playwright.sync_api import sync_playwright


class RobustAsianScraper:
    """Scraper pan-asiatique corrigé (gestion des prix texte + API directe Shopee)."""

    TITLE_KEYS = {"productTitle", "title", "name", "productName", "itemName"}
    PRICE_KEYS = {"price", "lowPrice", "salePrice", "discountedSalePrice", "priceMin"}

    def __init__(self, keyword: str = "mask pack", headless: bool = True):
        self.keyword = keyword
        self.headless = headless

    def _clean_price(self, val) -> float | None:
        """Convertit un prix entier, flottant ou texte en float valide."""
        if isinstance(val, (int, float)) and val > 0:
            return float(val)
        if isinstance(val, str):
            digits = re.sub(r"[^\d]", "", val)
            if digits:
                return float(digits)
        return None

    def _extract_products_from_json(self, obj, found=None):
        """Extraction récursive compatible avec les prix sous forme de chaînes."""
        if found is None:
            found = []
        if isinstance(obj, dict):
            title = next(
                (obj[k] for k in self.TITLE_KEYS if isinstance(obj.get(k), str) and len(obj[k].strip()) > 2),
                None,
            )
            raw_price = next(
                (obj[k] for k in self.PRICE_KEYS if obj.get(k) is not None),
                None,
            )
            price = self._clean_price(raw_price) if raw_price else None

            if title and price and price > 0:
                # Évite les doublons exacts
                if not any(f["title"] == title for f in found):
                    found.append({"title": title, "price": price})

            for v in obj.values():
                self._extract_products_from_json(v, found)
        elif isinstance(obj, list):
            for v in obj:
                self._extract_products_from_json(v, found)
        return found

    # ---------- Shopee SG ----------

    def _scrape_shopee(self, context, results):
        print(f"[+] [Shopee SG] Requête API directe pour : '{self.keyword}'...")
        api_url = (
            f"https://shopee.sg/api/v4/search/search_items?"
            f"by=relevance&keyword={quote(self.keyword)}&limit=30&newest=0&order=desc&page_type=search&version=2"
        )
        
        try:
            # Appel API direct pour contourner le challenge Cloudflare navigateur
            response = context.request.get(
                api_url,
                headers={
                    "Referer": f"https://shopee.sg/search?keyword={quote(self.keyword)}",
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/128.0.0.0 Safari/537.36"
                    ),
                    "x-shopee-language": "en",
                },
                timeout=15000,
            )
            
            if response.status == 200:
                data = response.json()
                items = data.get("items", []) or []
                for entry in items:
                    basic = entry.get("item_basic", {})
                    name = basic.get("name")
                    raw_p = basic.get("price", 0)
                    if name and raw_p:
                        price = raw_p / 100000
                        results.append({
                            "region": "Asie du Sud-Est (Shopee SG)",
                            "title": name,
                            "price_local": round(price, 2),
                            "currency": "SGD",
                            "est_price_usd": round(price * 0.76, 2),
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        })

            shopee_count = len([r for r in results if "Shopee" in r["region"]])
            print(f"[✓] Shopee SG : {shopee_count} produits récupérés.")
        except Exception as e:
            print(f"[-] Erreur Shopee : {e}")

    # ---------- Naver KR ----------

    def _scrape_naver(self, context, results):
        print(f"[+] [Naver KR] Extraction pour : '{self.keyword}'...")
        page = context.new_page()

        try:
            page.goto(
                f"https://search.shopping.naver.com/search/all?query={quote(self.keyword)}",
                wait_until="domcontentloaded",
                timeout=25000,
            )
            page.wait_for_timeout(2000)
            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1500)

            # Récupération du JSON embarqué dans le DOM
            raw_json = page.evaluate("""() => {
                const el = document.querySelector('script#__NEXT_DATA__');
                if (el) return el.textContent;
                return JSON.stringify(window.__PRELOADED_STATE__ || null);
            }""")

            naver_count_before = len([r for r in results if "Naver" in r["region"]])

            if raw_json:
                try:
                    parsed = json.loads(raw_json)
                    extracted = self._extract_products_from_json(parsed)
                    for item in extracted[:25]:
                        results.append({
                            "region": "Corée du Sud (Naver)",
                            "title": item["title"],
                            "price_local": item["price"],
                            "currency": "KRW",
                            "est_price_usd": round(item["price"] / 1330, 2),
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        })
                except json.JSONDecodeError:
                    pass

            naver_count = len([r for r in results if "Naver" in r["region"]]) - naver_count_before
            print(f"[✓] Naver KR : {naver_count} produits récupérés.")
        except Exception as e:
            print(f"[-] Erreur Naver : {e}")
        finally:
            page.close()

    # ---------- Orchestration ----------

    def run(self) -> list[dict]:
        results = []
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=self.headless,
                args=["--disable-blink-features=AutomationControlled"],
            )
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/128.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1366, "height": 768},
                locale="en-US",
            )

            # Stealth injection
            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)

            self._scrape_shopee(context, results)
            self._scrape_naver(context, results)

            browser.close()

        return results


if __name__ == "__main__":
    query = "notebook"
    scraper = RobustAsianScraper(keyword=query, headless=True)

    print(f"[+] Démarrage du traitement pan-asiatique pour : '{query}'\n")
    data = scraper.run()

    if data:
        df = pd.DataFrame(data)
        output_file = "01_web_scraping/asian_market_trends.xlsx"
        df.to_excel(output_file, index=False, engine="openpyxl")
        print(f"\n[✓] SUCCÈS : Fichier Excel généré -> {output_file}")
        print("\nAperçu des données obtenues :")
        print(df[["region", "title", "price_local", "est_price_usd"]].head(10))
    else:
        print("\n[-] Échec : Aucune donnée collectée.")