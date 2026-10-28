WITH cumulative AS (

    SELECT
        matchday,
        team_id,
        team_name,
        COUNT(*)       OVER (PARTITION BY team_id ORDER BY matchday) AS matches_played,
        SUM(points)    OVER (PARTITION BY team_id ORDER BY matchday) AS points_cumul,
        SUM(goal_diff) OVER (PARTITION BY team_id ORDER BY matchday) AS goal_diff_cumul,
        SUM(goals_for) OVER (PARTITION BY team_id ORDER BY matchday) AS goals_for_cumul
    FROM {{ ref('int_match_results') }}

)

SELECT
    matchday,
    team_id,
    team_name,
    matches_played,
    points_cumul,
    goal_diff_cumul,
    goals_for_cumul,
    RANK() OVER (
        PARTITION BY matchday
        ORDER BY points_cumul DESC, goal_diff_cumul DESC, goals_for_cumul DESC
    ) AS rank
FROM cumulative