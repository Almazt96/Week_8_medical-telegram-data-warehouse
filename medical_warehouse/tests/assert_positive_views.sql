-- Custom dbt Data Test Assertion
-- Custom invariant test: Returns records failing business rules. Must return 0 lines to pass.
select
    message_id,
    view_count
from {{ ref('stg_telegram_messages') }}
where view_count < 0