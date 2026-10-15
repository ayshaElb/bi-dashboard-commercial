"""
dag_daily_refresh.py
Apache Airflow DAG orchestrating end-to-end data pipeline:
1. Extract from CRM (HubSpot), ERP (SAP), and Google Sheets
2. Stage and transform via dbt Core (staging -> intermediate -> marts)
3. Run dbt tests (singular + generic schema tests)
4. Trigger Power BI dataset refresh via Power BI REST API
"""

from datetime import datetime, timedelta
import logging
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'email_on_failure': True,
    'email': ['data-alerts@ayshae-studio.com'],
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
}

def extract_crm_deals(**context):
    logging.info("Starting HubSpot CRM extraction...")
    from extract.hubspot_connector import HubSpotConnector
    connector = HubSpotConnector()
    count = connector.sync_deals_to_postgres()
    logging.info(f"HubSpot sync finished. {count} records extracted.")

def extract_erp_invoices(**context):
    logging.info("Starting SAP ERP extraction...")
    from extract.sap_connector import SAPConnector
    connector = SAPConnector()
    count = connector.sync_invoices_to_postgres()
    logging.info(f"SAP sync finished. {count} records extracted.")

def extract_sheets_targets(**context):
    logging.info("Starting Google Sheets targets extraction...")
    from extract.sheets_connector import SheetsConnector
    connector = SheetsConnector()
    count = connector.sync_targets_to_postgres()
    logging.info(f"Sheets sync finished. {count} records extracted.")

def trigger_powerbi_refresh(**context):
    """Trigger Power BI Semantic Model refresh via Power BI REST API."""
    import os
    tenant_id = os.getenv("PBI_TENANT_ID")
    client_id = os.getenv("PBI_CLIENT_ID")
    client_secret = os.getenv("PBI_CLIENT_SECRET")
    group_id = os.getenv("PBI_WORKSPACE_ID")
    dataset_id = os.getenv("PBI_DATASET_ID")

    # Get Azure AD Token
    token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/powerbi/api/.default'
    }
    r = requests.post(token_url, data=token_data)
    r.raise_for_status()
    access_token = r.json()['access_token']

    # Trigger Dataset Refresh
    refresh_url = f"https://api.powerbi.com/v1.0/myorg/groups/{group_id}/datasets/{dataset_id}/refreshes"
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    res = requests.post(refresh_url, headers=headers)
    res.raise_for_status()
    logging.info("Power BI refresh triggered successfully (HTTP 202 Accepted).")

with DAG(
    dag_id='commercial_bi_daily_pipeline',
    default_args=default_args,
    description='Automated commercial pipeline: API Extract -> dbt transform -> Power BI Refresh',
    schedule_interval='0 4 * * *',  # Every day at 04:00 AM UTC (Ready before business hours at J+0)
    start_date=datetime(2026, 1, 1),
    catchup=False,
    tags=['bi', 'commercial', 'dbt', 'powerbi'],
) as dag:

    t_crm = PythonOperator(
        task_id='extract_hubspot_crm',
        python_callable=extract_crm_deals
    )

    t_erp = PythonOperator(
        task_id='extract_sap_erp',
        python_callable=extract_erp_invoices
    )

    t_sheets = PythonOperator(
        task_id='extract_google_sheets',
        python_callable=extract_sheets_targets
    )

    t_dbt_run = BashOperator(
        task_id='dbt_run_models',
        bash_command='cd /opt/airflow/dbt_project && dbt run --profiles-dir . --target prod'
    )

    t_dbt_test = BashOperator(
        task_id='dbt_test_models',
        bash_command='cd /opt/airflow/dbt_project && dbt test --profiles-dir . --target prod'
    )

    t_powerbi = PythonOperator(
        task_id='refresh_powerbi_dataset',
        python_callable=trigger_powerbi_refresh
    )

    # Dependency graph
    [t_crm, t_erp, t_sheets] >> t_dbt_run >> t_dbt_test >> t_powerbi
