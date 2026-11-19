SELECT
    COUNT(DISTINCT matchday) AS nb_journees,
    MAX(matchday)            AS derniere_journee
FROM {{ ref('stg_matches') }}
HAVING COUNT(DISTINCT matchday) <> MAX(matchday)