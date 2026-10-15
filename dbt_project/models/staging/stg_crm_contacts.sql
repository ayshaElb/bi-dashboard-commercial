-- stg_crm_contacts.sql
-- Staging model: Clean and standardize CRM contact data from HubSpot

with source as (
    select * from {{ source('raw', 'raw_crm_contacts') }}
),

cleaned as (
    select
        contact_id,
        coalesce(first_name, '')                        as first_name,
        coalesce(last_name, '')                         as last_name,
        trim(coalesce(first_name, '') || ' ' || coalesce(last_name, ''))
                                                        as full_name,
        lower(trim(email))                              as email,
        company,
        phone,
        lifecycle_stage,
        lead_status,
        city,
        country,
        create_date::date                               as create_date,
        extracted_at
    from source
    where contact_id is not null
)

select * from cleaned
