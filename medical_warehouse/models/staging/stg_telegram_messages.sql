-- dbt Transformation Layer — Staging Model
{{ config(materialized='view') }} -- If you have a config block

-- location: medical_warehouse/models/staging/stg_telegram_messages.sql
with source_data as (
    select * from {{ source('raw', 'telegram_messages') }}
)

select
    cast(message_id as int) as message_id,
    cast(channel_name as varchar(100)) as channel_name,
    cast(message_date as timestamp) as message_date,
    coalesce(message_text, '') as message_text,
    cast(has_media as boolean) as has_media,
    cast(image_path as varchar(500)) as image_path,
    cast(views as int) as view_count,
    cast(forwards as int) as forward_count,
    length(coalesce(message_text, '')) as message_length,
    case when image_path is not null then true else false end as has_image
from source_data
where message_id is not null
  and channel_name is not null