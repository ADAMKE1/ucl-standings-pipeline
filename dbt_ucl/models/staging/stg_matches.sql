WITH extracted AS (

    SELECT
        fixture_id,
        TIMESTAMP(JSON_VALUE(payload, '$.fixture.date'))      AS kickoff_at,
        JSON_VALUE(payload, '$.fixture.status.short')         AS status,
        JSON_VALUE(payload, '$.league.round')                 AS round,
        CAST(JSON_VALUE(payload, '$.teams.home.id') AS INT64) AS home_team_id,
        JSON_VALUE(payload, '$.teams.home.name')              AS home_team_name,
        CAST(JSON_VALUE(payload, '$.teams.away.id') AS INT64) AS away_team_id,
        JSON_VALUE(payload, '$.teams.away.name')              AS away_team_name,
        CAST(JSON_VALUE(payload, '$.goals.home') AS INT64)    AS home_goals,
        CAST(JSON_VALUE(payload, '$.goals.away') AS INT64)    AS away_goals
    FROM {{ source('ucl_raw', 'fixtures') }}

)

SELECT
    fixture_id,
    kickoff_at,
    CAST(REPLACE(round, 'League Stage - ', '') AS INT64) AS matchday,
    status,
    home_team_id,
    home_team_name,
    away_team_id,
    away_team_name,
    home_goals,
    away_goals
FROM extracted
WHERE round LIKE 'League Stage%'
  AND status = 'FT'