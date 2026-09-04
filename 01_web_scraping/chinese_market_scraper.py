import json
import re
from datetime import datetime
from urllib.parse import quote
import pandas as pd
from playwright.sync_api import sync_playwright


class ChineseMarketScraper:
    """Scraper e-commerce pour le marché chinois (JD.com & AliExpress)."""

    def __init__(self, keyword: str = "notebook", headless: bool = True):
        self.keyword = keyword
        self.headless = headless

    def scrape_jd(self, context) -> list[dict]:
        """Extraction JD.com (Marché intérieur chinois - CNY)."""
        results = []
        print(f"[+] [JD.com China] Recherche domestique pour : '{self.keyword}'...")
        page = context.new_page()

        try:
            url = f"https://search.jd.com/Search?keyword={quote(self.keyword)}"
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(2000)

            # Scroll pour déclencher le lazy loading de JD
            for _ in range(3):
                page.mouse.wheel(0, 1200)
                page.wait_for_timeout(800)

            # Extraction par sélecteurs DOM
            items = page.query_selector_all(".gl-item")
            for item in items[:20]:
                title_el = item.query_selector(".p-name em")
                price_el = item.query_selector(".p-price i")

                if title_el and price_el:
                    title = title_el.inner_text().strip().replace("\n", " ")
                    price_str = price_el.inner_text().strip()
                    try:
                        price_cny = float(price_str)
                        if price_cny > 0:
                            results.append({
                                "region": "Chine Domestique (JD.com)",
                                "title": title,
                                "price_local": price_cny,
                                "currency": "CNY (¥)",
                                "est_price_usd": round(price_cny / 7.15, 2),
                                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            })
                    except ValueError:
                        continue

            print(f"[✓] JD.com : {len(results)} produits récupérés.")
        except Exception as e:
            print(f"[-] Erreur JD.com : {e}")
        finally:
            page.close()

        return results

    def scrape_aliexpress(self, context) -> list[dict]:
        """Extraction AliExpress (Exportation directe usines chinoises - USD)."""
        results = []
        print(f"[+] [AliExpress China Export] Recherche pour : '{self.keyword}'...")
        page = context.new_page()

        try:
            formatted_kw = quote(self.keyword.replace(" ", "-"))
            url = f"https://www.aliexpress.com/w/wholesale-{formatted_kw}.html"
            page.goto(url, wait_until="domcontentloaded", timeout=25000)
            page.wait_for_timeout(2500)

            page.mouse.wheel(0, 1500)
            page.wait_for_timeout(1000)

            # Extraction du JSON d'état global d'AliExpress
            raw_data = page.evaluate("""() => {
                const scripts = Array.from(document.querySelectorAll('script'));
                for (const s of scripts) {
                    if (s.textContent.includes('_page__data_')) {
                        return s.textContent;
                    }
                }
                return null;
            }""")

            if raw_data:
                # Capture des paires titre/prix dans le script JSON
                titles = re.findall(r'"title"\s*:\s*\{\s*"displayTitle"\s*:\s*"([^"]+)"', raw_data)
                prices = re.findall(r'"minPrice"\s*:\s*([\d\.]+)', raw_data)

                for title, price_str in zip(titles, prices):
                    try:
                        price_usd = float(price_str)
                        results.append({
                            "region": "Chine Export (AliExpress)",
                            "title": title,
                            "price_local": price_usd,
                            "currency": "USD ($)",
                            "est_price_usd": price_usd,
                            "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        })
                        if len(results) >= 20:
                            break
                    except ValueError:
                        continue

            print(f"[✓] AliExpress : {len(results)} produits récupérés.")
        except Exception as e:
            print(f"[-] Erreur AliExpress : {e}")
        finally:
            page.close()

        return results

    def run(self) -> list[dict]:
        all_results = []
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
                viewport={"width": 1440, "height": 900},
                locale="en-US",
            )

            context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            """)

            all_results.extend(self.scrape_jd(context))
            all_results.extend(self.scrape_aliexpress(context))

            browser.close()

        return all_results


if __name__ == "__main__":
    query = "notebook"
    scraper = ChineseMarketScraper(keyword=query, headless=True)

    print(f"[+] Démarrage de la recherche Marché Chinois pour : '{query}'\n")
    data = scraper.run()

    if data:
        df = pd.DataFrame(data)
        output_file = "01_web_scraping/chinese_market_trends.xlsx"
        df.to_excel(output_file, index=False, engine="openpyxl")
        print(f"\n[✓] SUCCÈS : Fichier Excel généré -> {output_file}")
        print("\nAperçu des données :")
        print(df[["region", "title", "price_local", "currency", "est_price_usd"]].head(10))
    else:
        print("\n[-] Échec : Aucune donnée collectée.")