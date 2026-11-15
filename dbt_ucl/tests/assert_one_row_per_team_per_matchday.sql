SELECT team_id, matchday, COUNT(*) AS nb_lignes
FROM {{ ref('fct_standings_by_matchday') }}
GROUP BY team_id, matchday
HAVING COUNT(*) > 1