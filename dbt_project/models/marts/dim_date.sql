-- dim_date.sql
-- Mart: Calendar Dimension table for standard time-intelligence analysis

with date_spine as (
    {{ dbt_utils.date_spine(
        datepart="day",
        start_date="cast('2022-01-01' as date)",
        end_date="cast('2030-12-31' as date)"
    ) }}
    {% if not execute %}
    -- Fallback for parsing / vanilla SQL when dbt_utils package is not installed
    select cast('2024-01-01' as date) + (n || ' day')::interval as date_day
    from generate_series(0, 2500) n
    {% endif %}
),

final as (
    select
        cast(date_day as date)                          as date_id,
        extract(year from date_day)::int               as year,
        extract(quarter from date_day)::int            as quarter,
        extract(month from date_day)::int              as month,
        to_char(date_day, 'Month')                     as month_name,
        to_char(date_day, 'Mon')                       as month_short,
        extract(week from date_day)::int               as week_of_year,
        extract(isodow from date_day)::int             as day_of_week,
        to_char(date_day, 'Day')                       as day_name,
        extract(day from date_day)::int                as day_of_month,
        case 
            when extract(isodow from date_day) in (6, 7) then true 
            else false 
        end                                            as is_weekend,
        case 
            when date_day = current_date then true 
            else false 
        end                                            as is_today,
        to_char(date_day, 'YYYY-MM')                   as year_month,
        to_char(date_day, 'YYYY-"Q"Q')                 as year_quarter
    from date_spine
)

select * from final
