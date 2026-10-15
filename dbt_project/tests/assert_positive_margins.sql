-- assert_positive_margins.sql
-- Custom test: Ensure no won sale has an abnormal negative margin > -10% (loss leader limit)
select
    sale_id,
    deal_name,
    actual_revenue,
    gross_margin,
    avg_margin_pct
from {{ ref('fct_sales') }}
where deal_status = 'won'
  and actual_revenue > 0
  and avg_margin_pct < -0.10
