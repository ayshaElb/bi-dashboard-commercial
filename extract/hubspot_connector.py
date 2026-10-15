"""
HubSpot CRM Connector
---------------------
Extracts deals, contacts, and pipeline data from HubSpot CRM via API v3.
Loads raw data into PostgreSQL staging tables.
"""

import os
import logging
import requests
import psycopg2
from psycopg2.extras import execute_values
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

HUBSPOT_API_KEY = os.getenv('HUBSPOT_API_KEY')
HUBSPOT_BASE_URL = 'https://api.hubapi.com/crm/v3'

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'dbname': os.getenv('DB_NAME', 'bi_commercial'),
    'user': os.getenv('DB_USER', 'bi_user'),
    'password': os.getenv('DB_PASSWORD'),
}

HEADERS = {
    'Authorization': f'Bearer {HUBSPOT_API_KEY}',
    'Content-Type': 'application/json',
}


def fetch_deals(after=None, limit=100):
    """
    Fetch deals from HubSpot CRM with pagination.
    Returns a list of deal records with properties.
    """
    url = f'{HUBSPOT_BASE_URL}/objects/deals'
    params = {
        'limit': limit,
        'properties': [
            'dealname', 'amount', 'dealstage', 'pipeline',
            'closedate', 'createdate', 'hubspot_owner_id',
            'hs_deal_stage_probability', 'deal_currency_code',
        ],
    }
    if after:
        params['after'] = after

    all_deals = []
    has_next = True

    while has_next:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        deals = data.get('results', [])
        all_deals.extend(deals)
        logger.info(f'Fetched {len(deals)} deals (total: {len(all_deals)})')

        paging = data.get('paging', {}).get('next', {})
        if paging.get('after'):
            params['after'] = paging['after']
        else:
            has_next = False

    return all_deals


def fetch_contacts(after=None, limit=100):
    """
    Fetch contacts from HubSpot CRM with pagination.
    Returns a list of contact records with properties.
    """
    url = f'{HUBSPOT_BASE_URL}/objects/contacts'
    params = {
        'limit': limit,
        'properties': [
            'firstname', 'lastname', 'email', 'company',
            'phone', 'lifecyclestage', 'createdate',
            'hs_lead_status', 'city', 'country',
        ],
    }
    if after:
        params['after'] = after

    all_contacts = []
    has_next = True

    while has_next:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()
        data = response.json()

        contacts = data.get('results', [])
        all_contacts.extend(contacts)
        logger.info(f'Fetched {len(contacts)} contacts (total: {len(all_contacts)})')

        paging = data.get('paging', {}).get('next', {})
        if paging.get('after'):
            params['after'] = paging['after']
        else:
            has_next = False

    return all_contacts


def load_deals_to_staging(deals):
    """Load extracted deals into raw_crm_deals staging table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS raw_crm_deals (
            deal_id             VARCHAR(50) PRIMARY KEY,
            deal_name           TEXT,
            amount              DECIMAL(15, 2),
            deal_stage          VARCHAR(100),
            pipeline            VARCHAR(100),
            close_date          TIMESTAMP,
            create_date         TIMESTAMP,
            owner_id            VARCHAR(50),
            stage_probability   DECIMAL(5, 2),
            currency_code       VARCHAR(10),
            extracted_at        TIMESTAMP DEFAULT NOW()
        )
    ''')

    values = []
    for deal in deals:
        props = deal.get('properties', {})
        values.append((
            deal.get('id'),
            props.get('dealname'),
            props.get('amount'),
            props.get('dealstage'),
            props.get('pipeline'),
            props.get('closedate'),
            props.get('createdate'),
            props.get('hubspot_owner_id'),
            props.get('hs_deal_stage_probability'),
            props.get('deal_currency_code', 'EUR'),
        ))

    execute_values(
        cur,
        '''
        INSERT INTO raw_crm_deals
            (deal_id, deal_name, amount, deal_stage, pipeline,
             close_date, create_date, owner_id, stage_probability, currency_code)
        VALUES %s
        ON CONFLICT (deal_id) DO UPDATE SET
            deal_name = EXCLUDED.deal_name,
            amount = EXCLUDED.amount,
            deal_stage = EXCLUDED.deal_stage,
            pipeline = EXCLUDED.pipeline,
            close_date = EXCLUDED.close_date,
            owner_id = EXCLUDED.owner_id,
            stage_probability = EXCLUDED.stage_probability,
            currency_code = EXCLUDED.currency_code,
            extracted_at = NOW()
        ''',
        values,
    )

    conn.commit()
    logger.info(f'Loaded {len(values)} deals into raw_crm_deals')
    cur.close()
    conn.close()


def load_contacts_to_staging(contacts):
    """Load extracted contacts into raw_crm_contacts staging table."""
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()

    cur.execute('''
        CREATE TABLE IF NOT EXISTS raw_crm_contacts (
            contact_id          VARCHAR(50) PRIMARY KEY,
            first_name          TEXT,
            last_name           TEXT,
            email               TEXT,
            company             TEXT,
            phone               TEXT,
            lifecycle_stage     VARCHAR(100),
            create_date         TIMESTAMP,
            lead_status         VARCHAR(100),
            city                VARCHAR(200),
            country             VARCHAR(100),
            extracted_at        TIMESTAMP DEFAULT NOW()
        )
    ''')

    values = []
    for contact in contacts:
        props = contact.get('properties', {})
        values.append((
            contact.get('id'),
            props.get('firstname'),
            props.get('lastname'),
            props.get('email'),
            props.get('company'),
            props.get('phone'),
            props.get('lifecyclestage'),
            props.get('createdate'),
            props.get('hs_lead_status'),
            props.get('city'),
            props.get('country'),
        ))

    execute_values(
        cur,
        '''
        INSERT INTO raw_crm_contacts
            (contact_id, first_name, last_name, email, company, phone,
             lifecycle_stage, create_date, lead_status, city, country)
        VALUES %s
        ON CONFLICT (contact_id) DO UPDATE SET
            first_name = EXCLUDED.first_name,
            last_name = EXCLUDED.last_name,
            email = EXCLUDED.email,
            company = EXCLUDED.company,
            phone = EXCLUDED.phone,
            lifecycle_stage = EXCLUDED.lifecycle_stage,
            lead_status = EXCLUDED.lead_status,
            city = EXCLUDED.city,
            country = EXCLUDED.country,
            extracted_at = NOW()
        ''',
        values,
    )

    conn.commit()
    logger.info(f'Loaded {len(values)} contacts into raw_crm_contacts')
    cur.close()
    conn.close()


def run():
    """Main extraction pipeline for HubSpot CRM data."""
    logger.info('Starting HubSpot CRM extraction...')

    logger.info('Extracting deals...')
    deals = fetch_deals()
    load_deals_to_staging(deals)

    logger.info('Extracting contacts...')
    contacts = fetch_contacts()
    load_contacts_to_staging(contacts)

    logger.info('HubSpot CRM extraction complete.')


if __name__ == '__main__':
    run()
