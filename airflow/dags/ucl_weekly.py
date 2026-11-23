"""
DAG ucl_weekly : rejoue la phase de ligue de la Ligue des Champions 2024-25,
une exécution par semaine (du lundi au dimanche).

    charger_la_semaine  ──►  dbt_build

- charger_la_semaine : récupère les matchs de la semaine (API-Football)
  et écrase la table ucl_raw.fixtures_AAAAMMJJ (idempotent).
- dbt_build : reconstruit les modèles dbt et lance les tests.
"""
from datetime import datetime, timedelta

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task

AIRFLOW_HOME = "/usr/local/airflow"
DBT = f"{AIRFLOW_HOME}/dbt_venv/bin/dbt"


@dag(
    dag_id="ucl_weekly",
    schedule="0 0 * * 1",                 # chaque lundi à minuit
    start_date=datetime(2024, 9, 16),     # lundi de la journée 1
    end_date=datetime(2025, 1, 27),       # lundi de la journée 8
    catchup=False,                        # rien ne part tout seul : on lance un backfill
    max_active_runs=1,                    # une semaine à la fois
    default_args={"retries": 2, "retry_delay": timedelta(minutes=1)},
    tags=["ucl"],
)
def ucl_weekly():

    @task
    def charger_la_semaine(date_from: str) -> None:
        import sys
        sys.path.insert(0, f"{AIRFLOW_HOME}/ingestion")
        from fetch_fixtures import fetch_fixtures
        from load_to_bigquery import load_week

        date_to = (datetime.fromisoformat(date_from) + timedelta(days=6)).date().isoformat()
        print(f"Semaine du {date_from} au {date_to}")
        load_week(fetch_fixtures(date_from, date_to), date_from)

    dbt_build = BashOperator(
        task_id="dbt_build",
        bash_command=(
            f"{DBT} build"
            f" --project-dir {AIRFLOW_HOME}/dbt_ucl"
            f" --profiles-dir {AIRFLOW_HOME}/include/dbt"
            " --target-path /tmp/dbt_target"
            " --log-path /tmp/dbt_logs"
        ),
    )

    # {{ ds }} = la date logique de l'exécution (le lundi de la semaine), au format AAAA-MM-JJ
    charger_la_semaine(date_from="{{ ds }}") >> dbt_build


ucl_weekly()
