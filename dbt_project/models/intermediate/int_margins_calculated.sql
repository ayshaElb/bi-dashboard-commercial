-- int_margins_calculated.sql
-- Intermediate: Calculate detailed margins by product and client

with invoices as (
    select * from {{ ref('stg_erp_invoices') }}
),

products as (
    select * from {{ ref('stg_erp_products') }}
),

margins as (
    select
        i.invoice_number,
        i.invoice_date,
        i.client_code,
        i.client_name,
        i.item_code,
        coalesce(p.product_name, i.item_description)    as product_name,
        p.product_group_id,
        i.quantity,
        i.unit_price,
        i.line_total                                    as revenue,
        p.standard_cost,
        i.quantity * coalesce(p.standard_cost, i.cost_price, 0)
                                                        as total_cost,
        i.line_total - (i.quantity * coalesce(p.standard_cost, i.cost_price, 0))
                                                        as gross_margin,
        {{ calculate_margin('i.line_total', 'i.quantity * coalesce(p.standard_cost, i.cost_price, 0)') }}
                                                        as margin_pct,

        -- Margin classification
        case
            when {{ calculate_margin('i.line_total', 'i.quantity * coalesce(p.standard_cost, i.cost_price, 0)') }} >= 0.30
                then 'High Margin'
            when {{ calculate_margin('i.line_total', 'i.quantity * coalesce(p.standard_cost, i.cost_price, 0)') }} >= 0.15
                then 'Medium Margin'
            else 'Low Margin'
        end                                             as margin_tier

    from invoices i
    left join products p on i.item_code = p.product_code
    where i.item_code is not null
)

select * from margins
