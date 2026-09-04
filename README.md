# 📈 E-Commerce Market Intelligence & Automated Reporting Pipeline

Un pipeline Python autonome et de niveau professionnel conçu pour extraire des données e-commerce, les stocker dans une base de données relationnelle, générer des rapports Excel automatisés et les distribuer par e-mail aux décideurs.

---

## 🚀 Architecture du Projet

Le projet suit une architecture modulaire et évolutive :

```text
python-automation-portfolio/
├── 01_web_scraping/          # Extraction de données & web scraping
│   └── naver_scraper.py
├── 02_workflow_automation/    # Logique métier, génération de rapports & e-mails
│   ├── email_sender.py
│   ├── report_generator.py
│   └── reports/              # Stockage des rapports Excel générés
├── pipeline.py               # Orchestrateur principal du système
├── app.log                   # Journal d'exécution (Logging)
├── .gitignore                # Exclusion des fichiers sensibles et venv
└── README.md