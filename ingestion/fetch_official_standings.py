import csv
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

r = requests.get(
    "https://v3.football.api-sports.io/standings",
    headers={"x-apisports-key": os.environ["API_FOOTBALL_KEY"]},
    params={"league": 2, "season": 2024},
    timeout=30,
)
r.raise_for_status()
payload = r.json()
if payload["errors"]:
    raise RuntimeError(f"Erreur API-Football : {payload['errors']}")

teams = payload["response"][0]["league"]["standings"][0]

path = Path("dbt_ucl/seeds/official_standings_md8.csv")
path.parent.mkdir(parents=True, exist_ok=True)

with path.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f)
    writer.writerow(["team_id", "team_name", "official_rank", "official_points", "official_goal_diff"])
    for t in teams:
        writer.writerow([t["team"]["id"], t["team"]["name"], t["rank"], t["points"], t["goalsDiff"]])

print(f"{len(teams)} équipes écrites dans {path}")