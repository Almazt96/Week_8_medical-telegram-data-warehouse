-- dbt Transformation Layer — Dimensional Model Marts
with stage_data as (
    select * from {{ ref('stg_telegram_messages') }}
)

select
    md5(channel_name) as channel_key,
    channel_name,
    case 
        when channel_name ilike '%pharma%' then 'Pharmaceutical'
        when channel_name ilike '%cosmetics%' then 'Cosmetics'
        else 'Medical'
    end as channel_type,
    min(message_date) as first_post_date,
    max(message_date) as last_post_date,
    count(message_id) as total_posts,
    avg(view_count) as avg_views
from stage_data
group by channel_name