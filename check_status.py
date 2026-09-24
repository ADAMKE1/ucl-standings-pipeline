import os
import requests
from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

# 1. API-Football : /status ne consomme pas de quota
r = requests.get(
    "https://v3.football.api-sports.io/status",
    headers={"x-apisports-key": os.environ["API_FOOTBALL_KEY"]},
)
print("API-Football :", r.json()["response"]["requests"])

# 2. BigQuery : lister les datasets du projet
client = bigquery.Client(project=os.environ["GCP_PROJECT_ID"])
print("BigQuery :", [d.dataset_id for d in client.list_datasets()])