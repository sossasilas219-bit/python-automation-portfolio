import os
import sqlite3
from datetime import datetime
import pandas as pd


def get_db_path():
    """Détecte dynamiquement l'emplacement exact de market_history.db."""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)

    possible_paths = [
        os.path.join(project_root, "01_web_scraping", "market_history.db"),
        os.path.join(current_dir, "market_history.db"),
        os.path.join(project_root, "market_history.db"),
    ]

    for path in possible_paths:
        if os.path.exists(path) and os.path.getsize(path) > 0:
            return path
    return None


def generate_daily_report():
    db_path = get_db_path()

    if not db_path:
        print(
            "[-] Fichier 'market_history.db' introuvable. Lance d'abord une recherche dans le Module 1."
        )
        return None

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Détection automatique du nom de la table présente dans la BDD
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [t[0] for t in cursor.fetchall()]

    if not tables:
        print("[-] La base de données ne contient aucune table.")
        conn.close()
        return None

    target_table = "search_history" if "search_history" in tables else tables[0]

    query = f"SELECT * FROM {target_table}"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("[-] Aucune donnée enregistrée dans la base.")
        return None

    # Création du dossier de rapports et export Excel
    reports_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "reports"
    )
    os.makedirs(reports_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = os.path.join(
        reports_dir, f"rapport_opportunites_{timestamp}.xlsx"
    )

    with pd.ExcelWriter(report_path, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Historique Complet", index=False)
        if "type" in df.columns:
            df_supp = df[df["type"].str.contains("Fournisseur", na=False)]
            df_ret = df[df["type"].str.contains("Revente", na=False)]
            if not df_supp.empty:
                df_supp.to_excel(
                    writer, sheet_name="Offres Sourcing", index=False
                )
            if not df_ret.empty:
                df_ret.to_excel(
                    writer, sheet_name="Offres Retail", index=False
                )

    print(f"[✓] Rapport généré avec succès : {report_path}")
    return report_path


if __name__ == "__main__":
    generate_daily_report()