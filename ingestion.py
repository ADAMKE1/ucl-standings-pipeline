import json
import os
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://v3.football.api-sports.io"
LEAGUE_ID = 2   # Ligue des Champions
SEASON = 2024   # saison 2024-25


def fetch_fixtures(date_from: str, date_to: str) -> list[dict]:
    """Récupère les matchs de la LDC entre deux dates (format AAAA-MM-JJ)."""
    r = requests.get(
        f"{BASE_URL}/fixtures",
        headers={"x-apisports-key": os.environ["API_FOOTBALL_KEY"]},
        params={"league": LEAGUE_ID, "season": SEASON, "from": date_from, "to": date_to},
        timeout=30,
    )
    r.raise_for_status()
    payload = r.json()
    if payload["errors"]:
        raise RuntimeError(f"Erreur API-Football : {payload['errors']}")
    print("Quota restant aujourd'hui :", r.headers.get("x-ratelimit-requests-remaining"))
    return payload["response"]


def save_json(fixtures: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(fixtures, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    fixtures = fetch_fixtures("2024-09-16", "2024-09-22")
    print(f"{len(fixtures)} matchs récupérés")
    save_json(fixtures, Path("data/fixtures_2024-09-16_2024-09-22.json"))