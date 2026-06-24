with date_series as (
    select distinct cast(message_date as date) as full_date
    from {{ ref('stg_telegram_messages') }}
    where message_date is not null
)

select
    to_char(full_date, 'YYYYMMDD')::int as date_key,
    full_date,
    extract(isodow from full_date) as day_of_week,
    to_char(full_date, 'Day') as day_name,
    extract(week from full_date) as week_of_year,
    extract(month from full_date) as month,
    to_char(full_date, 'Month') as month_name,
    extract(quarter from full_date) as quarter,
    extract(year from full_date) as year,
    case when extract(isodow from full_date) in (6, 7) then true else false end as is_weekend
from date_series