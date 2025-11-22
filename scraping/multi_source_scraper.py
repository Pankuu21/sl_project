

import sqlite3
from datetime import datetime, timezone
import sys
from pathlib import Path
import time
import re
from urllib.parse import urljoin, quote_plus
import requests
from bs4 import BeautifulSoup

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scraping.scraper_utils import clean_text
except:
    def clean_text(s):
        return " ".join(s.split()) if s else ""

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9"
}

BLACKLIST = ["new arrivals", "categories", "top brands", "featured", "popular products", "best sellers", "shop now", "view all"]

def normalize_url(url, base):
    if not url: return None
    url = url.strip()
    if url.startswith("//"): return "https:" + url
    if url.startswith("/"): return urljoin(base, url)
    return url

def extract_price(text):
    if not text: return None
    m = re.search(r'₹?\s*[\d,]+(?:\.\d+)?', text)
    if m:
        price = m.group(0).strip()
        if not price.startswith('₹'):
            price = '₹' + price
        return price
    return None

def get_img_src(tag, base):
    if not tag: return None
    if tag.name == "img":
        for attr in ["data-src", "src", "data-original", "data-lazy-src", "data-srcset"]:
            url = tag.get(attr)
            if url and url.strip():
                if attr in ["data-srcset", "srcset"] and "," in url:
                    url = url.split(",")[0].strip().split()[0]
                return normalize_url(url, base)
    style = tag.get("style", "")
    m = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
    if m:
        return normalize_url(m.group(1), base)
    return None

def is_valid_product(name):
    if not name or len(name) < 5:
        return False
    name_lower = name.lower()
    if any(term in name_lower for term in BLACKLIST):
        return False
    words = name.split()
    return any(len(w) >= 4 for w in words)

def print_product_details(products, source_name):
    """Print detailed product information"""
    if not products:
        return
    
    print(f"\n{'='*100}")
    print(f"{source_name} - Detailed Results ({len(products)} products)")
    print("="*100)
    
    for idx, p in enumerate(products, 1):
        print(f"\n[{idx}] {p['name'][:80]}")
        print(f"Price: {p['price']}")
        print(f"Image: {p['image_url'][:80] if p['image_url'] else 'No image'}...")
        print(f"Link:  {p['product_url'][:80] if p['product_url'] else 'No link'}...")
    
    print(f"\n{'='*100}\n")

def clear_search_products_table(db_path):
    """Delete ALL entries from search_products table"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM search_products")
        count = cursor.fetchone()[0]
        
        if count > 0:
            cursor.execute("DELETE FROM search_products")
            conn.commit()
            print(f"\n🧹 Cleared table: Deleted all {count} existing entries")
        else:
            print(f"\n✓ Table already empty")
    
    except Exception as e:
        print(f"Cleanup error: {e}")
    
    finally:
        conn.close()

def scrape_agriplex(keyword, max_items=30):
    """Scrape Agriplex India search results"""
    BASE = "https://agriplexindia.com"
    products = []
    
    print(f"\nScraping Agriplex for '{keyword}'...")
    
    try:
        search_url = f"{BASE}/search?q={quote_plus(keyword)}"
        soup = BeautifulSoup(requests.get(search_url, headers=HEADERS, timeout=15).text, "html.parser")
        
        candidates = soup.select("ul#collection li.square, li.product, div.product-item")
        
        for node in candidates[:max_items]:
            a = node.select_one("h3 a") or node.select_one("a")
            if not a:
                continue
            
            name = clean_text(a.get_text())
            if not is_valid_product(name):
                continue
            
            link = normalize_url(a.get("href"), BASE)
            
            img_tag = node.select_one("img")
            image = get_img_src(img_tag, BASE) if img_tag else None
            
            price_node = node.select_one(".price, .money")
            price = extract_price(clean_text(price_node.get_text())) if price_node else None
            if not price:
                m = re.search(r"(?:Rs\.?|₹)\s?[0-9,]+", node.get_text())
                price = m.group(0) if m else "Price on Request"
            
            products.append({
                "name": name,
                "price": price,
                "image_url": image,
                "product_url": link,
                "source": "Agriplex India",
                "category": "Agricultural Product"
            })
        
        print(f"Found {len(products)} products from Agriplex")
        print_product_details(products, "Agriplex India")
        
    except Exception as e:
        print(f"Agriplex error: {e}")
    
    return products

def scrape_kisanshop(keyword, max_items=30):
    """Scrape KisanShop search results"""
    BASE = "https://www.kisanshop.in"
    products = []
    
    print(f"\nScraping KisanShop for '{keyword}'...")
    
    try:
        search_url = f"{BASE}/search?query={quote_plus(keyword)}"
        session = requests.Session()
        session.get(BASE, headers=HEADERS, timeout=10)
        time.sleep(0.5)
        
        soup = BeautifulSoup(session.get(search_url, headers=HEADERS, timeout=15).text, "html.parser")
        
        cards = soup.select("div.product-card, li.square, li.product")
        
        for card in cards[:max_items]:
            title_a = card.select_one("span.product-title a, h3 a, a.product-title")
            if not title_a:
                continue
            
            name = clean_text(title_a.get_text())
            if not is_valid_product(name):
                continue
            
            link = normalize_url(title_a.get("href"), BASE)
            
            img_tag = card.select_one("img")
            image = get_img_src(img_tag, BASE) if img_tag else None
            
            price_node = card.select_one(".price-row i, .current, .money")
            price = extract_price(clean_text(price_node.get_text())) if price_node else None
            if not price:
                m = re.search(r"(?:₹|Rs\.?)\s?[0-9,]+", card.get_text())
                price = m.group(0) if m else "Price on Request"
            
            products.append({
                "name": name,
                "price": price,
                "image_url": image,
                "product_url": link,
                "source": "KisanShop",
                "category": "Agricultural Product"
            })
        
        print(f"Found {len(products)} products from KisanShop")
        print_product_details(products, "KisanShop")
        
    except Exception as e:
        print(f"KisanShop error: {e}")
    
    return products

def search_all_sources(keyword, max_per_source=30):
    """Search all sources and combine results"""
    print("="*100)
    print(f"SEARCHING ALL SOURCES FOR: '{keyword}'")
    print("="*100)
    
    all_products = []
    
    all_products.extend(scrape_agriplex(keyword, max_items=max_per_source))
    all_products.extend(scrape_kisanshop(keyword, max_items=max_per_source))
    
    print(f"\n{'='*100}")
    print(f"TOTAL: {len(all_products)} products from all sources")
    print("="*100)
    
    return all_products

def ensure_table_exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS search_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        category TEXT,
        price TEXT,
        image_url TEXT,
        product_url TEXT,
        source TEXT,
        keyword TEXT,
        scraped_at TEXT,
        UNIQUE(name, source)
    )''')
    conn.commit()
    conn.close()

def save_to_db(products, keyword, db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    inserted = 0
    now = datetime.now(timezone.utc).isoformat()
    
    for p in products:
        try:
            cur.execute('''
                INSERT OR IGNORE INTO search_products
                (name, category, price, image_url, product_url, source, keyword, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (p['name'], p['category'], p['price'], p.get('image_url'),
                  p.get('product_url'), p['source'], keyword, now))
            if cur.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"  ✗ Insert error: {e}")
    
    conn.commit()
    conn.close()
    return inserted

def _get_db_path():
    try:
        from config import Config
        return Config.DATABASE_PATH
    except:
        return str(PROJECT_ROOT / "database" / "farmer_portal.db")

def scrape_by_keyword(keyword, max_per_source=30):
    """
    Main function: scrape all sources by keyword and save to DB
    ALWAYS clears the search_products table before scraping
    
    Args:
        keyword: Search keyword
        max_per_source: Max items per source (default: 30)
    """
    db_path = _get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    ensure_table_exists(db_path)
    
    print("\nClearing search_products table...")
    clear_search_products_table(db_path)
    
    products = search_all_sources(keyword, max_per_source)
    
    print(f"\nSaving {len(products)} products to database...")
    inserted = save_to_db(products, keyword, db_path)
    print(f"Inserted: {inserted} new products")
    
    return inserted

if __name__ == "__main__":
    keyword = input("Enter search keyword: ").strip() or "seeds"
    scrape_by_keyword(keyword, max_per_source=15)
