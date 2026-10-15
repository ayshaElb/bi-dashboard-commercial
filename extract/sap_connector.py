"""
SAP Business One ERP Connector
-------------------------------
Extracts invoices and product data from SAP B1 via Service Layer REST API.
Loads raw data into PostgreSQL staging tables.
"""

import os
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

SAP_BASE_URL = os.getenv('SAP_SERVICE_LAYER_URL', 'https://sap-server:50000/b1s/v1')
SAP_COMPANY_DB = os.getenv('SAP_COMPANY_DB')
SAP_USER = os.getenv('SAP_USER')
SAP_PASSWORD = os.getenv('SAP_PASSWORD')

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'bi_commercial'),
    'user': os.getenv('DB_USER', 'bi_user'),
    'password': os.getenv('DB_PASSWORD'),
}


class SAPSession:
    """Manages authenticated session with SAP B1 Service Layer."""

    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False  # SAP B1 often uses self-signed certs
        self._login()

    def _login(self):
        payload = {
            'CompanyDB': SAP_COMPANY_DB,
            'UserName': SAP_USER,
            'Password': SAP_PASSWORD,
        }
        response = self.session.post(f'{SAP_BASE_URL}/Login', json=payload)
        response.raise_for_status()
        logger.info('SAP B1 Service Layer login successful')

    def get(self, endpoint, params=None):
        response = self.session.get(f'{SAP_BASE_URL}/{endpoint}', params=params)
        response.raise_for_status()
        return response.json()

    def logout(self):
        self.session.post(f'{SAP_BASE_URL}/Logout')
        logger.info('SAP B1 Service Layer logout')


def fetch_invoices(sap_session, skip=0, top=100):
    """
    Fetch sales invoices from SAP B1 with pagination.
    Includes line items for product-level detail.
    """
    all_invoices = []
    has_next = True

    while has_next:
        params = {
            '$skip': skip,
            '$top': top,
            '$select': 'DocEntry,DocNum,DocDate,DocDueDate,CardCode,CardName,DocTotal,DocCurrency,DocumentLines',
            '$orderby': 'DocDate desc',
        }
        data = sap_session.get('Invoices', params=params)
        invoices = data.get('value', [])
        all_invoices.extend(invoices)
        logger.info(f'Fetched {len(invoices)} invoices (total: {len(all_invoices)})')

        if len(invoices) < top:
            has_next = False
        else:
            skip += top

    return all_invoices


def fetch_products(sap_session, skip=0, top=100):
    """Fetch product items from SAP B1 item master data."""
    all_products = []
    has_next = True

    while has_next:
        params = {
            '$skip': skip,
            '$top': top,
            '$select': 'ItemCode,ItemName,ItemsGroupCode,PurchaseItem,SalesItem,AvgStdPrice',
            '$filter': "SalesItem eq 'tYES'",
        }
        data = sap_session.get('Items', params=params)
        products = data.get('value', [])
        all_products.extend(products)
        logger.info(f'Fetched {len(products)} products (total: {len(all_products)})')

        if len(products) < top:
            has_next = False
        else:
            skip += top

    return all_products


def load_invoices_to_staging(invoices):
    """Load invoices and their line items into staging tables."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    # Invoice header table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS raw_erp_invoices (
            doc_entry           INTEGER PRIMARY KEY,
            doc_num             INTEGER,
            doc_date            DATE,
            doc_due_date        DATE,
            card_code           VARCHAR(50),
            card_name           TEXT,
            doc_total           DECIMAL(15, 2),
            doc_currency        VARCHAR(10),
            extracted_at        TIMESTAMP DEFAULT NOW()
        )
    ''')

    # Invoice lines table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS raw_erp_invoice_lines (
            doc_entry           INTEGER,
            line_num            INTEGER,
            item_code           VARCHAR(50),
            item_description    TEXT,
            quantity            DECIMAL(15, 4),
            unit_price          DECIMAL(15, 4),
            line_total          DECIMAL(15, 2),
            cost_price          DECIMAL(15, 4),
            gross_profit        DECIMAL(15, 2),
            extracted_at        TIMESTAMP DEFAULT NOW(),
            PRIMARY KEY (doc_entry, line_num)
        )
    ''')

    header_values = []
    line_values = []

    for inv in invoices:
        header_values.append((
            inv.get('DocEntry'),
            inv.get('DocNum'),
            inv.get('DocDate'),
            inv.get('DocDueDate'),
            inv.get('CardCode'),
            inv.get('CardName'),
            inv.get('DocTotal'),
            inv.get('DocCurrency', 'EUR'),
        ))

        for line in inv.get('DocumentLines', []):
            line_values.append((
                inv.get('DocEntry'),
                line.get('LineNum'),
                line.get('ItemCode'),
                line.get('ItemDescription'),
                line.get('Quantity'),
                line.get('UnitPrice'),
                line.get('LineTotal'),
                line.get('CostingCode'),
                line.get('GrossProfit'),
            ))

    execute_values(
        cur,
        '''INSERT INTO raw_erp_invoices
            (doc_entry, doc_num, doc_date, doc_due_date, card_code, card_name, doc_total, doc_currency)
        VALUES %s
        ON CONFLICT (doc_entry) DO UPDATE SET
            doc_total = EXCLUDED.doc_total,
            extracted_at = NOW()''',
        header_values,
    )

    if line_values:
        execute_values(
            cur,
            '''INSERT INTO raw_erp_invoice_lines
                (doc_entry, line_num, item_code, item_description, quantity, unit_price,
                 line_total, cost_price, gross_profit)
            VALUES %s
            ON CONFLICT (doc_entry, line_num) DO UPDATE SET
                line_total = EXCLUDED.line_total,
                cost_price = EXCLUDED.cost_price,
                gross_profit = EXCLUDED.gross_profit,
                extracted_at = NOW()''',
            line_values,
        )

    conn.commit()
    logger.info(f'Loaded {len(header_values)} invoices and {len(line_values)} lines')
    cur.close()
    conn.close()


def load_products_to_staging(products):
    """Load product master data into staging table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS raw_erp_products (
            item_code           VARCHAR(50) PRIMARY KEY,
            item_name           TEXT,
            item_group_code     INTEGER,
            avg_std_price       DECIMAL(15, 4),
            extracted_at        TIMESTAMP DEFAULT NOW()
        )
    ''')

    values = [(
        p.get('ItemCode'),
        p.get('ItemName'),
        p.get('ItemsGroupCode'),
        p.get('AvgStdPrice'),
    ) for p in products]

    execute_values(
        cur,
        '''INSERT INTO raw_erp_products (item_code, item_name, item_group_code, avg_std_price)
        VALUES %s
        ON CONFLICT (item_code) DO UPDATE SET
            item_name = EXCLUDED.item_name,
            avg_std_price = EXCLUDED.avg_std_price,
            extracted_at = NOW()''',
        values,
    )

    conn.commit()
    logger.info(f'Loaded {len(values)} products into raw_erp_products')
    cur.close()
    conn.close()


def run():
    """Main extraction pipeline for SAP B1 ERP data."""
    logger.info('Starting SAP B1 ERP extraction...')

    sap = SAPSession()

    try:
        logger.info('Extracting invoices...')
        invoices = fetch_invoices(sap)
        load_invoices_to_staging(invoices)

        logger.info('Extracting products...')
        products = fetch_products(sap)
        load_products_to_staging(products)
    finally:
        sap.logout()

    logger.info('SAP B1 ERP extraction complete.')


if __name__ == '__main__':
    run()
