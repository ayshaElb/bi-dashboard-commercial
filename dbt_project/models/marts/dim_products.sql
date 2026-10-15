-- dim_products.sql
-- Mart: Product dimension table with margin analysis

with products as (
    select * from {{ ref('stg_erp_products') }}
),

product_sales as (
    select
        item_code,
        count(*)                                        as times_sold,
        sum(quantity)                                   as total_qty_sold,
        sum(revenue)                                    as total_revenue,
        sum(gross_margin)                               as total_margin,
        avg(margin_pct)                                 as avg_margin_pct,
        min(invoice_date)                               as first_sale_date,
        max(invoice_date)                               as last_sale_date
    from {{ ref('int_margins_calculated') }}
    group by item_code
),

final as (
    select
        p.product_code,
        p.product_name,
        p.product_group_id,
        p.standard_cost,

        -- Sales metrics
        coalesce(ps.times_sold, 0)                      as times_sold,
        coalesce(ps.total_qty_sold, 0)                  as total_qty_sold,
        coalesce(ps.total_revenue, 0)                   as total_revenue,
        coalesce(ps.total_margin, 0)                    as total_margin,
        coalesce(ps.avg_margin_pct, 0)                  as avg_margin_pct,
        ps.first_sale_date,
        ps.last_sale_date,

        -- ABC classification (Pareto)
        case
            when coalesce(ps.total_revenue, 0) > 0
            then sum(coalesce(ps.total_revenue, 0)) over (
                order by coalesce(ps.total_revenue, 0) desc
            ) / nullif(sum(coalesce(ps.total_revenue, 0)) over (), 0)
            else 1
        end                                             as cumulative_revenue_pct,

        case
            when sum(coalesce(ps.total_revenue, 0)) over (
                order by coalesce(ps.total_revenue, 0) desc
            ) / nullif(sum(coalesce(ps.total_revenue, 0)) over (), 0) <= 0.80
                then 'A'
            when sum(coalesce(ps.total_revenue, 0)) over (
                order by coalesce(ps.total_revenue, 0) desc
            ) / nullif(sum(coalesce(ps.total_revenue, 0)) over (), 0) <= 0.95
                then 'B'
            else 'C'
        end                                             as abc_class,

        current_timestamp                               as dbt_updated_at

    from products p
    left join product_sales ps on p.product_code = ps.item_code
)

select * from final
