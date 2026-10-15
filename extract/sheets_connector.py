"""
Google Sheets Connector
-----------------------
Extracts supplementary commercial data from Google Sheets
(targets, manual KPIs, budget allocations).
Uses Google Sheets API v4 with service account.
"""

import os
import logging
import psycopg2
from psycopg2.extras import execute_values
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SCOPES = ['https://www.googleapis.com/auth/spreadsheets.readonly']
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SA_KEY_PATH', 'credentials/service_account.json')

# Spreadsheet configuration
SPREADSHEET_ID = os.getenv('SHEETS_SPREADSHEET_ID')
TARGETS_RANGE = 'Objectifs!A2:F'
BUDGET_RANGE = 'Budget!A2:E'

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'bi_commercial'),
    'user': os.getenv('DB_USER', 'bi_user'),
    'password': os.getenv('DB_PASSWORD'),
}


def get_sheets_service():
    """Authenticate and return Google Sheets API service."""
    credentials = Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    service = build('sheets', 'v4', credentials=credentials)
    return service.spreadsheets()


def fetch_sales_targets(sheets_service):
    """
    Fetch monthly sales targets per sales rep.
    Expected columns: Month, SalesRep, TargetRevenue, TargetDeals, Region, Notes
    """
    result = sheets_service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=TARGETS_RANGE,
    ).execute()

    rows = result.get('values', [])
    logger.info(f'Fetched {len(rows)} sales target rows from Google Sheets')
    return rows


def fetch_budget_allocations(sheets_service):
    """
    Fetch quarterly budget allocations by channel.
    Expected columns: Quarter, Channel, Budget, Spent, Notes
    """
    result = sheets_service.values().get(
        spreadsheetId=SPREADSHEET_ID,
        range=BUDGET_RANGE,
    ).execute()

    rows = result.get('values', [])
    logger.info(f'Fetched {len(rows)} budget allocation rows from Google Sheets')
    return rows


def load_targets_to_staging(targets):
    """Load sales targets into staging table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS raw_sheets_targets (
            month               VARCHAR(20),
            sales_rep           TEXT,
            target_revenue      DECIMAL(15, 2),
            target_deals        INTEGER,
            region              VARCHAR(100),
            notes               TEXT,
            extracted_at        TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Truncate and reload (full refresh)
    cur.execute('TRUNCATE TABLE raw_sheets_targets')

    values = []
    for row in targets:
        # Pad row to 6 columns if incomplete
        padded = row + [''] * (6 - len(row))
        values.append((
            padded[0],  # month
            padded[1],  # sales_rep
            padded[2] or None,  # target_revenue
            padded[3] or None,  # target_deals
            padded[4],  # region
            padded[5],  # notes
        ))

    if values:
        execute_values(
            cur,
            '''INSERT INTO raw_sheets_targets
                (month, sales_rep, target_revenue, target_deals, region, notes)
            VALUES %s''',
            values,
        )

    conn.commit()
    logger.info(f'Loaded {len(values)} target rows into raw_sheets_targets')
    cur.close()
    conn.close()


def load_budget_to_staging(budgets):
    """Load budget allocations into staging table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS raw_sheets_budget (
            quarter             VARCHAR(10),
            channel             VARCHAR(100),
            budget              DECIMAL(15, 2),
            spent               DECIMAL(15, 2),
            notes               TEXT,
            extracted_at        TIMESTAMP DEFAULT NOW()
        )
    ''')

    cur.execute('TRUNCATE TABLE raw_sheets_budget')

    values = []
    for row in budgets:
        padded = row + [''] * (5 - len(row))
        values.append((
            padded[0],  # quarter
            padded[1],  # channel
            padded[2] or None,  # budget
            padded[3] or None,  # spent
            padded[4],  # notes
        ))

    if values:
        execute_values(
            cur,
            '''INSERT INTO raw_sheets_budget
                (quarter, channel, budget, spent, notes)
            VALUES %s''',
            values,
        )

    conn.commit()
    logger.info(f'Loaded {len(values)} budget rows into raw_sheets_budget')
    cur.close()
    conn.close()


def run():
    """Main extraction pipeline for Google Sheets data."""
    logger.info('Starting Google Sheets extraction...')

    sheets = get_sheets_service()

    logger.info('Extracting sales targets...')
    targets = fetch_sales_targets(sheets)
    load_targets_to_staging(targets)

    logger.info('Extracting budget allocations...')
    budgets = fetch_budget_allocations(sheets)
    load_budget_to_staging(budgets)

    logger.info('Google Sheets extraction complete.')


if __name__ == '__main__':
    run()
