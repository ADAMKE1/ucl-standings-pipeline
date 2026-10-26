WITH home_side AS (

    SELECT
        fixture_id,
        matchday,
        home_team_id    AS team_id,
        home_team_name  AS team_name,
        home_goals      AS goals_for,
        away_goals      AS goals_against
    FROM {{ ref('stg_matches') }}

),

away_side AS (

    SELECT
        fixture_id,
        matchday,
        away_team_id    AS team_id,
        away_team_name  AS team_name,
        away_goals      AS goals_for,
        home_goals      AS goals_against
    FROM {{ ref('stg_matches') }}

),

both_sides AS (

    SELECT * FROM home_side
    UNION ALL
    SELECT * FROM away_side

)

SELECT
    fixture_id,
    matchday,
    team_id,
    team_name,
    goals_for,
    goals_against,
    goals_for - goals_against AS goal_diff,
    CASE
        WHEN goals_for > goals_against THEN 3
        WHEN goals_for = goals_against THEN 1
        ELSE 0
    END AS points
FROM both_sides