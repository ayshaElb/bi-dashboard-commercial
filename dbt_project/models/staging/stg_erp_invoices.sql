-- stg_erp_invoices.sql
-- Staging model: Clean and join ERP invoice headers with line items

with headers as (
    select * from {{ source('raw', 'raw_erp_invoices') }}
),

lines as (
    select * from {{ source('raw', 'raw_erp_invoice_lines') }}
),

joined as (
    select
        h.doc_entry,
        h.doc_num                                       as invoice_number,
        h.doc_date                                      as invoice_date,
        h.doc_due_date                                  as due_date,
        h.card_code                                     as client_code,
        h.card_name                                     as client_name,
        h.doc_total                                     as invoice_total,
        h.doc_currency                                  as currency,

        l.line_num,
        l.item_code,
        l.item_description,
        l.quantity,
        l.unit_price,
        l.line_total,
        l.cost_price,
        l.gross_profit,

        -- Calculate margin at line level
        case
            when l.line_total > 0
            then (l.line_total - coalesce(l.cost_price * l.quantity, 0)) / l.line_total
            else 0
        end                                             as margin_pct

    from headers h
    left join lines l on h.doc_entry = l.doc_entry
    where h.doc_entry is not null
)

select * from joined
