import requests
import csv
from datetime import datetime
import sqlite3
from pathlib import Path

CSV_API_TEMPLATE = (
    "https://api.agmarknet.gov.in/v1/dashboard-data/"
    "?dashboard=marketwise_price_arrival"
    "&date={date}"
    "&group=[100000]"
    "&commodity=[100001]"
    "&variety=100022"
    "&state=100006"
    "&district=[100007]"
    "&market=[100009]"
    "&grades=[4]"
    "&downloadreport=true"
    "&downloadformat=csv"
    "&page=0"
    "&limit=999999"
    "&format=json"
)

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Accept": "text/csv,application/json;q=0.9,*/*;q=0.8",
    "Referer": "https://agmarknet.gov.in/home",
    "Origin": "https://agmarknet.gov.in",
    "Connection": "keep-alive",
}

def download_and_parse_csv(date_str=None):
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d")
    url = CSV_API_TEMPLATE.format(date=date_str)
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    content = resp.content.decode("utf-8")
    lines = content.splitlines()
    data_start = 0
    for i, line in enumerate(lines):
        if "Commodity Group" in line:
            data_start = i
            break
    if data_start == 0:
        raise Exception("Header not found in CSV")
    reader = csv.DictReader(lines[data_start:])
    date_label = next((h for h in reader.fieldnames if "Price on" in h), None)
    arrival_label = next((h for h in reader.fieldnames if "Arrival on" in h), None)
    records = []
    for row in reader:
        if not row.get("Commodity"):
            continue
        records.append({
            "commodity_group": row.get("Commodity Group", "").strip(),
            "commodity": row.get("Commodity", "").strip(),
            "variety": row.get("Variety", "").strip(),
            "msp": row.get("MSP (Rs./Quintal) 2025-26", "").strip(),
            "price": row.get(date_label, "").strip() if date_label else "",
            "arrival": row.get(arrival_label, "").strip() if arrival_label else "",
            "date": date_str,
        })
    return records

def ensure_price_table(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS agmarknet_prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            commodity_group TEXT,
            commodity TEXT,
            variety TEXT,
            msp TEXT,
            price TEXT,
            arrival TEXT,
            date TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(commodity, variety, date)
        )
    ''')
    # Add variety column if needed
    try:
        cur.execute("ALTER TABLE agmarknet_prices ADD COLUMN variety TEXT")
    except sqlite3.OperationalError:
        pass
    conn.commit()
    conn.close()

def save_to_database(records, db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    inserted = 0
    for r in records:
        cur.execute('''
            INSERT OR REPLACE INTO agmarknet_prices
            (commodity_group, commodity, variety, msp, price, arrival, date)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (r['commodity_group'], r['commodity'], r['variety'], r['msp'], r['price'], r['arrival'], r['date']))
        if cur.rowcount > 0:
            inserted += 1
    conn.commit()
    conn.close()
    return inserted

def scrape_agmarknet_prices(date_str=None):
    db_path = Path("database/farmer_portal.db")
    ensure_price_table(db_path)
    records = download_and_parse_csv(date_str)
    inserted = save_to_database(records, db_path)
    print(f"Saved {inserted} records for {date_str or datetime.now()}")
    return inserted

if __name__ == "__main__":
    scrape_agmarknet_prices()
