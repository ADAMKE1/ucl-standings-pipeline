import sys
from datetime import date, timedelta

from fetch_fixtures import fetch_fixtures
from load_to_bigquery import load_week

date_from = sys.argv[1]
date_to = (date.fromisoformat(date_from) + timedelta(days=6)).isoformat()
load_week(fetch_fixtures(date_from, date_to), date_from)