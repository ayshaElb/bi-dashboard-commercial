-- int_sales_enriched.sql
-- Intermediate: Enrich sales data by joining CRM deals with ERP invoices

with deals as (
    select * from {{ ref('stg_crm_deals') }}
),

invoices as (
    select * from {{ ref('stg_erp_invoices') }}
),

contacts as (
    select * from {{ ref('stg_crm_contacts') }}
),

enriched as (
    select
        d.deal_id,
        d.deal_name,
        d.deal_amount,
        d.deal_stage,
        d.deal_status,
        d.close_date,
        d.create_date,
        d.sales_rep_id,
        d.win_probability,
        d.days_in_pipeline,

        -- Invoice data (aggregated by client)
        coalesce(inv.total_invoiced, 0)                 as total_invoiced,
        coalesce(inv.total_cost, 0)                     as total_cost,
        coalesce(inv.total_invoiced, 0) - coalesce(inv.total_cost, 0)
                                                        as gross_margin,
        case
            when coalesce(inv.total_invoiced, 0) > 0
            then (coalesce(inv.total_invoiced, 0) - coalesce(inv.total_cost, 0))
                 / coalesce(inv.total_invoiced, 0)
            else 0
        end                                             as margin_pct,

        -- Contact info
        c.full_name                                     as contact_name,
        c.company                                       as company_name,
        c.country

    from deals d
    left join (
        select
            client_code,
            sum(line_total)                             as total_invoiced,
            sum(cost_price * quantity)                   as total_cost
        from {{ ref('stg_erp_invoices') }}
        group by client_code
    ) inv on d.deal_id = inv.client_code
    left join contacts c on d.deal_id = c.contact_id
)

select * from enriched
