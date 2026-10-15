-- stg_crm_deals.sql
-- Staging model: Clean and standardize CRM deal data from HubSpot

with source as (
    select * from {{ source('raw', 'raw_crm_deals') }}
),

cleaned as (
    select
        deal_id,
        deal_name,
        coalesce(amount, 0)                             as deal_amount,
        deal_stage,
        pipeline,
        close_date::date                                as close_date,
        create_date::date                               as create_date,
        owner_id                                        as sales_rep_id,
        coalesce(stage_probability, 0) / 100.0          as win_probability,
        coalesce(currency_code, 'EUR')                  as currency,
        extracted_at,

        -- Derived fields
        case
            when deal_stage in ('closedwon')            then 'won'
            when deal_stage in ('closedlost')           then 'lost'
            else 'open'
        end                                             as deal_status,

        close_date::date - create_date::date            as days_in_pipeline

    from source
    where deal_id is not null
)

select * from cleaned
