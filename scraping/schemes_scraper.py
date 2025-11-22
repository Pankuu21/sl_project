import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import sqlite3
from datetime import datetime, timezone
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

BASE = "https://agriwelfare.gov.in"
PAGE = "https://agriwelfare.gov.in/en/Major"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
}

def fetch_page():
    print(f"Fetching schemes from {PAGE}...")
    r = requests.get(PAGE, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text

def parse_schemes(html):
    soup = BeautifulSoup(html, "html.parser")
    
    table = soup.find("table", class_="testdatatable") or soup.find("table")
    schemes = []
    
    if not table:
        print("No table found on page. Page may be blocked or structure changed.")
        return schemes
    
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if not tds or len(tds) < 4:
            continue
        
        title = tds[1].get_text(strip=True)
        publish_date = tds[2].get_text(strip=True)
        
        doc_links = []
        apply_links = []
        
        for a in tds[3].find_all("a", href=True):
            href = a["href"].strip()
            full = urljoin(BASE, href)
            text = a.get_text(strip=True).lower()
            
            if href.lower().endswith(".pdf") or "download" in text or "guideline" in text:
                doc_links.append(full)
            else:
                apply_links.append(full)
        
        schemes.append({
            "scheme": title,
            "publish_date": publish_date,
            "doc_links": list(dict.fromkeys(doc_links)),
            "apply_links": list(dict.fromkeys(apply_links)),
        })
    
    return schemes

def ensure_schemes_table(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS government_schemes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            scheme_name TEXT UNIQUE,
            publish_date TEXT,
            doc_links TEXT,
            apply_links TEXT,
            scraped_at TEXT
        )
    ''')
    conn.commit()
    conn.close()

def save_schemes_to_db(schemes, db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc).isoformat()
    
    for s in schemes:
        doc_links_str = "|".join(s['doc_links']) if s['doc_links'] else ""
        apply_links_str = "|".join(s['apply_links']) if s['apply_links'] else ""
        
        try:
            cur.execute('''
                INSERT INTO government_schemes 
                (scheme_name, publish_date, doc_links, apply_links, scraped_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(scheme_name) DO UPDATE SET
                    publish_date = excluded.publish_date,
                    doc_links = excluded.doc_links,
                    apply_links = excluded.apply_links,
                    scraped_at = excluded.scraped_at
            ''', (s['scheme'], s['publish_date'], doc_links_str, apply_links_str, now))
            
            if cur.rowcount > 0:
                inserted += 1
            else:
                updated += 1
        except Exception as e:
            print(f"Error saving scheme: {e}")
    
    conn.commit()
    conn.close()
    return inserted

def _get_db_path():
    try:
        from config import Config
        return Config.DATABASE_PATH
    except:
        return str(PROJECT_ROOT / "database" / "farmer_portal.db")

def scrape_government_schemes():
    """Main function to scrape and save government schemes"""
    print("="*80)
    print("SCRAPING GOVERNMENT AGRICULTURAL SCHEMES")
    print("="*80)
    
    db_path = _get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    ensure_schemes_table(db_path)
    
    try:
        html = fetch_page()
        schemes = parse_schemes(html)
        
        if not schemes:
            print("No schemes found. Try running again or check website structure.")
            return 0
        
        print(f"\n✓ Parsed {len(schemes)} schemes")
        
        print("\nSample schemes:")
        for i, s in enumerate(schemes[:3], 1):
            print(f"\n  [{i}] {s['scheme']}")
            print(f"Published: {s['publish_date']}")
            print(f"Documents: {len(s['doc_links'])}")
            print(f"Apply links: {len(s['apply_links'])}")
        
        inserted = save_schemes_to_db(schemes, db_path)
        print(f"\nSaved {inserted} schemes to database")
        
        return len(schemes)
        
    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 0

if __name__ == "__main__":
    scrape_government_schemes()
