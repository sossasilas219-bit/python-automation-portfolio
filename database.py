import sqlite3
import pandas as pd

DB_NAME = "market_data.db"


def save_to_sqlite(df: pd.DataFrame):
  """Sauvegarde ou remplace les données dans la table SQLite market_data."""
  try:
    conn = sqlite3.connect(DB_NAME)
    df.to_sql("market_data", conn, if_exists="replace", index=False)
    conn.close()
  except Exception as e:
    print(f"[!] Erreur lors de l'enregistrement SQLite : {e}")


def get_all_history() -> pd.DataFrame:
  """Récupère l'historique sans planter si la table n'existe pas encore."""
  try:
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql("SELECT * FROM market_data", conn)
    conn.close()
    return df
  except Exception:
    # Retourne un DataFrame vide si la table n'est pas encore créée
    return pd.DataFrame()