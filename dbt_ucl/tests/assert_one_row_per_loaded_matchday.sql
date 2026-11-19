SELECT team_id, team_name, COUNT(*) AS nb_lignes
FROM {{ ref('fct_standings_by_matchday') }}
GROUP BY team_id, team_name
HAVING COUNT(*) <> (SELECT MAX(matchday) FROM {{ref('stg_matches')}})