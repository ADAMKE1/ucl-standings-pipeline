import json
import os
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import bigquery

load_dotenv()

DATASET = "ucl_raw"

SCHEMA = [
    bigquery.SchemaField("fixture_id", "INT64"),
    bigquery.SchemaField("payload", "STRING"),
    bigquery.SchemaField("window_start", "DATE"),
    bigquery.SchemaField("ingested_at", "TIMESTAMP"),
]


def load_week(fixtures: list[dict], date_from: str) -> None:
    """Charge les matchs d'une semaine dans sa propre table, en l'écrasant."""
    if not fixtures:
        print(f"Aucun match pour la semaine du {date_from}, rien à charger.")
        return

    client = bigquery.Client(project=os.environ["GCP_PROJECT_ID"])
    table_id = f"{client.project}.{DATASET}.fixtures_{date_from.replace('-', '')}"
    now = datetime.now(timezone.utc).isoformat()

    rows = [
        {
            "fixture_id": f["fixture"]["id"],
            "payload": json.dumps(f, ensure_ascii=False),
            "window_start": date_from,
            "ingested_at": now,
        }
        for f in fixtures
    ]

    job_config = bigquery.LoadJobConfig(schema=SCHEMA, write_disposition="WRITE_TRUNCATE")
    job = client.load_table_from_json(rows, table_id, job_config=job_config)
    job.result()
    print(f"{job.output_rows} lignes chargées dans {table_id}")


if __name__ == "__main__":
    path = Path("data/fixtures_2024-09-16_2024-09-22.json")
    fixtures = json.loads(path.read_text(encoding="utf-8"))
    load_week(fixtures, "2024-09-16")