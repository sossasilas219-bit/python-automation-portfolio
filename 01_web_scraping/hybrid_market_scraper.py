import pandas as pd
import requests
from playwright.sync_api import sync_playwright


class PortfolioScraper:

  def __init__(self, query: str, sources: list = None):
    self.query = query
    self.sources = (
        sources
        if sources
        else [
            "DummyJSON Store",
            "Global Market B",
            "Site Web Cible (Playwright)",
        ]
    )

  def scrape_dummyjson(self) -> pd.DataFrame:
    url = f"https://dummyjson.com/products/search?q={self.query}&limit=50"
    try:
      response = requests.get(url, timeout=10)
      if response.status_code == 200:
        data = response.json().get("products", [])
        items = []
        for p in data:
          items.append({
              "title": p.get("title", "Inconnu"),
              "price": float(p.get("price", 0.0)),
              "rating": float(p.get("rating", 0.0)),
              "source": "DummyJSON Store",
          })
        return pd.DataFrame(items)
    except Exception as e:
      print(f"[!] Erreur sur DummyJSON : {e}")
    return pd.DataFrame()

  def scrape_alternative_source(self) -> pd.DataFrame:
    url = "https://fakestoreapi.com/products"
    try:
      response = requests.get(url, timeout=10)
      if response.status_code == 200:
        data = response.json()
        items = []
        for p in data:
          title = p.get("title", "")
          if self.query.lower() in title.lower() or self.query.lower() in p.get(
              "category", ""
          ).lower():
            items.append({
                "title": title,
                "price": float(p.get("price", 0.0)),
                "rating": float(p.get("rating", {}).get("rate", 0.0)),
                "source": "Global Market B",
            })
        return pd.DataFrame(items)
    except Exception as e:
      print(f"[!] Erreur sur la source alternative : {e}")
    return pd.DataFrame()

  def scrape_with_playwright(self) -> pd.DataFrame:
    """Simule un vrai navigateur pour contourner les protections JS et extraire le DOM."""
    items = []
    # Exemple d'URL de recherche (remplace par le site e-commerce de ton choix)
    target_url = f"https://quotes.toscrape.com/search.aspx"  # Site d'entraînement ou e-commerce cible

    with sync_playwright() as p:
      # Lancement d'un navigateur Chromium invisible (headless=True)
      browser = p.chromium.launch(headless=True)
      page = browser.new_page()
      try:
        page.goto(target_url, timeout=15000)

        # Exemple d'interaction dynamique (si le site nécessite de taper dans une barre de recherche)
        # page.fill("input#search", self.query)
        # page.press("input#search", "Enter")
        # page.wait_for_selector(".product-card", timeout=5000)

        # Extraction des éléments de la page
        # (Adapte les sélecteurs CSS '.product-title' et '.product-price' selon le site ciblé)
        products = page.query_selector_all(
            ".quote"
        )  # Remplacer par le sélecteur des articles
        for prod in products:
          title_element = prod.query_selector(".text")
          title = title_element.inner_text() if title_element else self.query

          # Simulation d'un prix pour l'exemple basé sur la longueur du texte
          items.append({
              "title": title[:50],
              "price": float(len(title) % 50 + 10),  # Prix fictif ou extrait du DOM
              "rating": 4.5,
              "source": "Site Web Cible (Playwright)",
          })
      except Exception as e:
        print(f"[!] Erreur Playwright : {e}")
      finally:
        browser.close()

    return pd.DataFrame(items)

  def run(self) -> pd.DataFrame:
    print(f"[*] Lancement de l'agrégation multi-sources pour : {self.query}")
    dfs = []

    if "DummyJSON Store" in self.sources:
      dfs.append(self.scrape_dummyjson())
    if "Global Market B" in self.sources:
      dfs.append(self.scrape_alternative_source())
    if "Site Web Cible (Playwright)" in self.sources:
      dfs.append(self.scrape_with_playwright())

    if dfs:
      combined_df = pd.concat(dfs, ignore_index=True)
      if not combined_df.empty:
        combined_df = combined_df.sort_values(by="price", ascending=True)
        combined_df = combined_df.reset_index(drop=True)
      return combined_df

    return pd.DataFrame()