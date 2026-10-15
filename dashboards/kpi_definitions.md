# Dictionnaire des Métriques & Formules DAX — Tableau de Bord Commercial

Ce document détaille les règles de calcul et les formules DAX implémentées dans le modèle sémantique Power BI.

---

## 1. Métriques de Performance Commerciale

### Chiffre d'Affaires Réalisé (Total Revenue)
```dax
Total Revenue = SUM(fct_sales[actual_revenue])
```

### Chiffre d'Affaires N-1 (YoY Revenue)
```dax
Revenue LY = 
CALCULATE(
    [Total Revenue],
    SAMEPERIODLASTYEAR(dim_date[date_id])
)
```

### Croissance YoY %
```dax
YoY Growth % = 
DIVIDE([Total Revenue] - [Revenue LY], [Revenue LY], 0)
```

### Taux de Conversion Funnel (Win Rate %)
```dax
Won Deals Count = CALCULATE(COUNTROWS(fct_sales), fct_sales[deal_status] = "won")
Total Closed Deals = CALCULATE(COUNTROWS(fct_sales), fct_sales[deal_status] IN {"won", "lost"})

Win Rate % = 
DIVIDE([Won Deals Count], [Total Closed Deals], 0)
```

---

## 2. Analyse de la Rentabilité & Marges

### Coût des Ventes (COGS)
```dax
Total COGS = SUM(fct_sales[total_cost])
```

### Marge Brute (€)
```dax
Gross Margin € = [Total Revenue] - [Total COGS]
```

### Taux de Marge Brute (%)
```dax
Gross Margin % = 
DIVIDE([Gross Margin €], [Total Revenue], 0)
```

### Marge Brute vs Budget (%)
```dax
Margin vs Target % = 
DIVIDE([Gross Margin €] - [Budgeted Margin €], [Budgeted Margin €], 0)
```

---

## 3. Prévisions & Pipeline

### Pipeline Pondéré (Weighted Pipeline)
```dax
Weighted Pipeline = 
CALCULATE(
    SUMX(fct_sales, fct_sales[deal_value] * fct_sales[win_probability]),
    fct_sales[deal_status] = "open"
)
```

### Cycle Moyen de Vente (Sales Cycle Days)
```dax
Avg Sales Cycle = 
AVERAGEX(
    FILTER(fct_sales, fct_sales[deal_status] = "won"),
    fct_sales[days_in_pipeline]
)
```
