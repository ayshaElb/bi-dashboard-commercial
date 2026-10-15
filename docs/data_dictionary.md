# Data Dictionary & Lignage des Données

Architecture dimensionnelle en étoile (Star Schema) pour la Business Intelligence Commerciale.

---

## 1. Vue d'ensemble du Lignage (Data Lineage)

```
[HubSpot CRM API]  --> stg_crm_deals ──┐
                   --> stg_crm_contacts ┼─> int_sales_enriched ──┐
[SAP B1 ERP API]   --> stg_erp_invoices ─┤                        ├──> fct_sales
                   --> stg_erp_products ─┴─> int_margins_calc ────┼──> dim_products
[Google Sheets]    --> stg_sales_targets                          ├──> dim_clients
                                                                  └──> dim_date
```

---

## 2. Tables de Faits & Dimensions

### `fct_sales` (Fait principal)
- Grain : 1 ligne par transaction commerciale / deal
- Clé primaire : `sale_id`
- Clés étrangères : `client_id`, `sales_rep_id`, `close_date` (date_id)
- Mesures : `deal_value`, `actual_revenue`, `total_cost`, `gross_margin`, `avg_margin_pct`, `weighted_pipeline`

### `dim_clients` (Dimension client)
- Grain : 1 ligne par entreprise / compte client
- Clé primaire : `client_id`
- Attributs : `company`, `email`, `lifecycle_stage`, `country`, `client_segment` (Enterprise, Mid-Market, SMB)

### `dim_products` (Dimension produit)
- Grain : 1 ligne par référence SKU
- Clé primaire : `product_code`
- Attributs : `product_name`, `product_group_id`, `standard_cost`, `abc_class` (A / B / C Pareto)

### `dim_date` (Dimension calendrier)
- Grain : 1 jour
- Clé primaire : `date_id` (YYYY-MM-DD)
- Attributs : `year`, `quarter`, `month`, `week_of_year`, `day_name`, `is_weekend`
