select *
from {{ ref('mart_dashboard_skill_trends') }}
where share_of_ads < 0
   or share_of_ads > 1
