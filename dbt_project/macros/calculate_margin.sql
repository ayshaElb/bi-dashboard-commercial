{% macro calculate_margin(revenue, cost) %}
    case
        when {{ revenue }} is not null and {{ revenue }} > 0
        then round(cast(({{ revenue }} - {{ cost }}) as numeric) / cast({{ revenue }} as numeric), 4)
        else 0
    end
{% endmacro %}
