SELECT matchday, COUNT(*) AS matches_per_matchday
FROM {{ref('stg_matches')}}
GROUP BY matchday
HAVING COUNT(*) != 18