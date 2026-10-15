-- fct_sales.sql
-- Mart: Fact table for sales performance analytics
-- Grain: one row per deal (closed or open)

with sales as (
    select * from {{ ref('int_sales_enriched') }}
),

margins as (
    select
        client_code,
        sum(revenue)                                    as total_revenue,
        sum(total_cost)                                 as total_cost,
        sum(gross_margin)                               as total_margin,
        avg(margin_pct)                                 as avg_margin_pct,
        count(distinct item_code)                       as distinct_products
    from {{ ref('int_margins_calculated') }}
    group by client_code
),

final as (
    select
        s.deal_id                                       as sale_id,
        s.deal_name,
        s.deal_status,
        s.deal_stage,
        s.sales_rep_id,
        s.contact_name,
        s.company_name,
        s.country,

        -- Dates
        s.create_date,
        s.close_date,
        s.days_in_pipeline,

        -- Revenue metrics
        s.deal_amount                                   as deal_value,
        coalesce(m.total_revenue, s.deal_amount)        as actual_revenue,
        coalesce(m.total_cost, 0)                       as total_cost,
        coalesce(m.total_margin, s.deal_amount)         as gross_margin,
        coalesce(m.avg_margin_pct, 0)                   as avg_margin_pct,
        coalesce(m.distinct_products, 0)                as num_products,

        -- Pipeline metrics
        s.win_probability,
        s.deal_amount * s.win_probability               as weighted_pipeline,

        -- Time dimensions
        extract(year from s.close_date)                 as close_year,
        extract(month from s.close_date)                as close_month,
        extract(quarter from s.close_date)              as close_quarter,

        current_timestamp                               as dbt_updated_at

    from sales s
    left join margins m on s.deal_id = m.client_code
)

select * from final
