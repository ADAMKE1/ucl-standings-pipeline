WITH ours AS (

    SELECT team_id, team_name, points_cumul, goal_diff_cumul
    FROM {{ ref('fct_standings_by_matchday') }}
    WHERE matchday = 8

),

official AS (

    SELECT team_id, team_name, official_points, official_goal_diff
    FROM {{ ref('official_standings_md8') }}

)

SELECT
    COALESCE(ours.team_id, official.team_id)     AS team_id,
    COALESCE(ours.team_name, official.team_name) AS team_name,
    CASE
        WHEN ours.team_id IS NULL     THEN 'absente de notre classement'
        WHEN official.team_id IS NULL THEN 'absente du classement officiel'
        WHEN ours.points_cumul <> official.official_points THEN 'points différents'
        ELSE 'différence de buts différente'
    END AS probleme,
    ours.points_cumul,
    official.official_points,
    ours.goal_diff_cumul,
    official.official_goal_diff
FROM ours
FULL OUTER JOIN official
    ON ours.team_id = official.team_id
WHERE (SELECT MAX(matchday) FROM {{ ref('stg_matches') }}) = 8
  AND (
        ours.team_id IS NULL
     OR official.team_id IS NULL
     OR ours.points_cumul <> official.official_points
     OR ours.goal_diff_cumul <> official.official_goal_diff
  )