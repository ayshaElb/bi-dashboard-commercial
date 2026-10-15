-- dim_clients.sql
-- Mart: Client dimension table

with contacts as (
    select * from {{ ref('stg_crm_contacts') }}
),

sales_summary as (
    select
        company_name,
        count(*)                                        as total_deals,
        sum(case when deal_status = 'won' then 1 else 0 end) as won_deals,
        sum(actual_revenue)                             as lifetime_revenue,
        avg(avg_margin_pct)                             as avg_margin,
        min(create_date)                                as first_deal_date,
        max(close_date)                                 as last_deal_date
    from {{ ref('fct_sales') }}
    group by company_name
),

final as (
    select
        c.contact_id                                    as client_id,
        c.full_name,
        c.email,
        c.company,
        c.phone,
        c.lifecycle_stage,
        c.lead_status,
        c.city,
        c.country,
        c.create_date                                   as client_since,

        -- Aggregated metrics
        coalesce(s.total_deals, 0)                      as total_deals,
        coalesce(s.won_deals, 0)                        as won_deals,
        coalesce(s.lifetime_revenue, 0)                 as lifetime_revenue,
        coalesce(s.avg_margin, 0)                       as avg_margin,
        s.first_deal_date,
        s.last_deal_date,

        -- Client segmentation
        case
            when coalesce(s.lifetime_revenue, 0) >= 100000 then 'Enterprise'
            when coalesce(s.lifetime_revenue, 0) >= 25000  then 'Mid-Market'
            when coalesce(s.lifetime_revenue, 0) > 0       then 'SMB'
            else 'Prospect'
        end                                             as client_segment,

        current_timestamp                               as dbt_updated_at

    from contacts c
    left join sales_summary s on c.company = s.company_name
)

select * from final
