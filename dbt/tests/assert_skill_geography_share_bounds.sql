select *
from {{ ref('mart_skill_geography') }}
where share_of_ads < 0
   or share_of_ads > 1
