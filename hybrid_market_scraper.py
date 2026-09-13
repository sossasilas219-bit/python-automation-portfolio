import requests
import pandas as pd
import time


class PortfolioScraper:

  def __init__(self, query: str):
    self.query = query

  def scrape_dummyjson(self) -> pd.DataFrame:
    """Source 1 : Interroge l'API DummyJSON avec pagination/limite élargie."""
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
    """Source 2 : Seconde source ou API alternative (ex: FakeStoreAPI ou mock enrichi)"""
    # Ici, on peut cibler une autre API publique ou adapter un parseur requests/BeautifulSoup
    url = f"https://fakestoreapi.com/products"
    try:
      response = requests.get(url, timeout=10)
      if response.status_code == 200:
        data = response.json()
        items = []
        # Filtrage simple basé sur la requête utilisateur
        for p in data:
          title = p.get("title", "")
          if self.query.lower() in title.lower() or self.query.lower() in p.get(
              "category", ""
          ).lower():
            items.append({
                "title": title,
                "price": float(p.get("price", 0.0)),
                # FakeStoreAPI utilise un système de 'rate' dans 'rating'
                "rating": float(p.get("rating", {}).get("rate", 0.0)),
                "source": "Global Market B",
            })
        return pd.DataFrame(items)
    except Exception as e:
      print(f"[!] Erreur sur la source alternative : {e}")
    return pd.DataFrame()

  def run(self) -> pd.DataFrame:
    """Exécute les scrapers en parallèle/séquentiel, fusionne et trie par prix croissant."""
    print(f"[*] Lancement de la comparaison multi-sources pour : {self.query}")

    df_source1 = self.scrape_dummyjson()
    df_source2 = self.scrape_alternative_source()

    # Fusion des DataFrames de toutes les sources
    combined_df = pd.concat([df_source1, df_source2], ignore_index=True)

    if not combined_df.empty:
      # Nettoyage et tri par prix croissant (le moins cher en premier)
      combined_df = combined_df.sort_values(by="price", ascending=True)
      combined_df = combined_df.reset_index(drop=True)

    return combined_df