SELECT 
    fixture_id,
    JSON_VALUE(payload, '$.teams.home.name') AS home_team_name,
    JSON_VALUE(payload, '$.teams.away.name') AS away_team_name
FROM {{source('ucl_raw', 'fixtures')}}