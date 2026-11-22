FROM astrocrpublic.azurecr.io/runtime:3.3-12

RUN python -m venv dbt_venv && \
    . dbt_venv/bin/activate && \
    pip install --no-cache-dir dbt-core==1.12.5 dbt-bigquery==1.12.1 && \
    deactivate