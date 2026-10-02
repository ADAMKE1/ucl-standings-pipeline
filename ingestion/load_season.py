import time
from datetime import date, timedelta

from fetch_fixtures import fetch_fixtures
from load_to_bigquery import load_week

SEASON_START = date(2024, 9, 16)   # lundi de la journée 1
SEASON_END = date(2025, 1, 27)     # lundi de la journée 8

week = SEASON_START
while week <= SEASON_END:
    date_from = week.isoformat()
    date_to = (week + timedelta(days=6)).isoformat()
    print(f"--- Semaine du {date_from} ---")
    load_week(fetch_fixtures(date_from, date_to), date_from)
    week += timedelta(weeks=1)
    time.sleep(7)