# 📊 Dashboard BI — Performance Commerciale

> Pipeline SQL automatisé + modélisation dbt + tableau de bord Power BI temps réel

---

## 🔴 Le Défi

Une entreprise B2B faisait face à un **reporting fragmenté et chronophage** :

- **Données éparpillées** entre CRM (HubSpot), ERP (SAP Business One) et Google Sheets
- **10h/semaine** de reporting manuel (copier-coller, consolidation, mise en forme)
- **Vision KPIs à J+7** : les décisions stratégiques étaient prises sur des données obsolètes
- **Aucune visibilité** sur les marges réelles par produit/client/canal

## ⚡ La Solution

Architecture **data moderne end-to-end** :

```
Sources          Extraction         Transformation      Visualisation
┌──────────┐    ┌──────────────┐    ┌──────────────┐    ┌─────────────┐
│ CRM      │───▶│ Python API   │───▶│  dbt Cloud   │───▶│  Power BI   │
│ ERP      │    │ Connectors   │    │  Star Schema │    │  Dashboard  │
│ Sheets   │    │              │    │  Tests       │    │  Temps Réel │
└──────────┘    └──────────────┘    └──────────────┘    └─────────────┘
```

### Stack technique

| Composant | Technologie | Rôle |
|-----------|------------|------|
| **Extraction** | Python + API REST | Connecteurs CRM (HubSpot API v3) et ERP (SAP B1 Service Layer) |
| **Orchestration** | Apache Airflow | Scheduling quotidien + monitoring |
| **Staging** | PostgreSQL | Data warehouse intermédiaire |
| **Transformation** | dbt Core | Modélisation dimensionnelle (star schema) |
| **Visualisation** | Power BI | Dashboards interactifs temps réel |

## 📈 Les Résultats

| Métrique | Avant | Après | Impact |
|----------|-------|-------|--------|
| Fraîcheur des données | J+7 | **J+0 (temps réel)** | -7 jours |
| Temps de reporting | 10h/semaine | **0h (automatisé)** | -10h/semaine |
| Visibilité marges | Aucune | **Par produit/client/canal** | 100% |
| Décisions tarifaires | Intuition | **Basées sur marges réelles** | Data-driven |

---

## 🏗️ Architecture du projet

```
bi-dashboard-commercial/
├── README.md
├── extract/
│   ├── hubspot_connector.py       # Extraction CRM via API
│   ├── sap_connector.py           # Extraction ERP via Service Layer
│   └── sheets_connector.py        # Extraction Google Sheets
├── dbt_project/
│   ├── dbt_project.yml
│   ├── profiles.yml.example
│   ├── models/
│   │   ├── staging/
│   │   │   ├── stg_crm_deals.sql
│   │   │   ├── stg_crm_contacts.sql
│   │   │   ├── stg_erp_invoices.sql
│   │   │   ├── stg_erp_products.sql
│   │   │   └── schema.yml
│   │   ├── intermediate/
│   │   │   ├── int_sales_enriched.sql
│   │   │   └── int_margins_calculated.sql
│   │   └── marts/
│   │       ├── fct_sales.sql
│   │       ├── dim_clients.sql
│   │       ├── dim_products.sql
│   │       ├── dim_date.sql
│   │       └── schema.yml
│   ├── tests/
│   │   └── assert_positive_margins.sql
│   └── macros/
│       └── calculate_margin.sql
├── orchestration/
│   └── dag_daily_refresh.py
├── dashboards/
│   └── kpi_definitions.md
├── docs/
│   └── data_dictionary.md
└── requirements.txt
```

---

## 🔧 Installation & Configuration

### Prérequis

- Python 3.10+
- PostgreSQL 14+
- dbt Core 1.7+
- Power BI Desktop
- Accès API : HubSpot, SAP Business One

### Setup

```bash
# Cloner le repo
git clone https://github.com/ayshaElb/bi-dashboard-commercial.git
cd bi-dashboard-commercial

# Installer les dépendances
pip install -r requirements.txt

# Configurer dbt
cd dbt_project
cp profiles.yml.example profiles.yml
# Éditer profiles.yml avec vos credentials

# Tester la connexion
dbt debug

# Lancer les modèles
dbt run

# Lancer les tests
dbt test
```

## 📊 KPIs du Dashboard

### Vue d'ensemble commerciale
- **Chiffre d'affaires** : mensuel, trimestriel, annuel (avec comparaison N-1)
- **Nombre de deals** : pipeline, gagnés, perdus
- **Taux de conversion** : par étape du funnel commercial
- **Panier moyen** : évolution et segmentation

### Analyse des marges
- **Marge brute** par produit, client, canal de vente
- **Top/Flop produits** : classement par rentabilité
- **Évolution des marges** : tendances et alertes

### Performance équipe
- **CA par commercial** : objectifs vs réalisé
- **Cycle de vente moyen** : durée par segment
- **Activité CRM** : appels, emails, réunions

### Prévisions
- **Pipeline pondéré** : CA prévisionnel par probabilité
- **Forecast** : projection basée sur les tendances historiques

---

## 🛡️ Qualité des données

- **Tests dbt** : unicité, non-null, relations, valeurs acceptées
- **Tests custom** : marges positives, cohérence CA CRM vs ERP
- **Monitoring** : alertes automatiques en cas d'anomalie
- **Documentation** : data dictionary complet avec lignage

---

## 📄 Licence

Ce projet est un cas d'étude portfolio. Le code est partagé à des fins éducatives.

## 👤 Auteur

**AyshaE** — Data Analyst & Web Analytics
[ayshae-studio.com](https://ayshae-studio.com)
