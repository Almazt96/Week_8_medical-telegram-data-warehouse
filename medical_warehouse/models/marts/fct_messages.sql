with stage_data as (
    select * from {{ ref('stg_telegram_messages') }}
)

select
    s.message_id,
    md5(s.channel_name) as channel_key,
    to_char(s.message_date, 'YYYYMMDD')::int as date_key,
    s.message_text,
    s.message_length,
    s.view_count,
    s.forward_count,
    s.has_image
from stage_data s