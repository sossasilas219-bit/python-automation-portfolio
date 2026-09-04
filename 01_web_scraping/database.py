import sqlite3
import pandas as pd

DB_FILE = "01_web_scraping/market_history.db"

def init_db():
    """Initialise la table dans la base de données SQLite."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS product_analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            type TEXT,
            platform TEXT,
            title TEXT,
            price_usd REAL,
            scraped_at TEXT
        )
    """)
    conn.commit()
    conn.close()

def save_analysis(df: pd.DataFrame, keyword: str):
    """Enregistre un jeu de données complet dans la base."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df_to_save = df.copy()
    df_to_save["keyword"] = keyword
    df_to_save.to_sql("product_analyses", conn, if_exists="append", index=False)
    conn.close()

def get_all_history() -> pd.DataFrame:
    """Récupère l'historique complet pour le Dashboard."""
    init_db()
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM product_analyses ORDER BY scraped_at DESC", conn)
    conn.close()
    return df