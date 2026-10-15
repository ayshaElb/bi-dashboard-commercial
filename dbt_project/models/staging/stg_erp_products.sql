-- stg_erp_products.sql
-- Staging model: Clean product master data from SAP B1

with source as (
    select * from {{ source('raw', 'raw_erp_products') }}
),

cleaned as (
    select
        item_code                                       as product_code,
        item_name                                       as product_name,
        item_group_code                                 as product_group_id,
        coalesce(avg_std_price, 0)                      as standard_cost,
        extracted_at
    from source
    where item_code is not null
)

select * from cleaned
