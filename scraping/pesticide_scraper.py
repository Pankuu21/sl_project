"""
AgriBegri scraper - REFINED VERSION
Filters out navigation elements and improves price extraction
"""

import sqlite3
from datetime import datetime, timezone
import sys
from pathlib import Path
import time
import csv
import re
from urllib.parse import urljoin

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from scraping.scraper_utils import get_soup, clean_text, extract_price
except Exception:
    import requests
    from bs4 import BeautifulSoup
    
    def get_soup(url, headers=None, timeout=20):
        headers = headers or {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
        }
        try:
            r = requests.get(url, headers=headers, timeout=timeout)
            r.raise_for_status()
            return BeautifulSoup(r.text, "html.parser")
        except Exception as e:
            return None
    
    def clean_text(s):
        return " ".join(s.split()) if s else ""
    
    def extract_price(text):
        if not text: return None
        m = re.search(r'₹?\s*[\d,]+', text)
        if m:
            price = m.group(0).strip()
            if not price.startswith('₹'):
                price = '₹' + price
            return price
        return None

AGRIBEGRI_BASE = "https://www.agribegri.com"
AGRIBEGRI_PEST_PAGE = AGRIBEGRI_BASE + "/products/pesticides.html"

# Blacklist for filtering out non-product items
BLACKLIST_NAMES = [
    "new arrivals", "categories", "top brands", "featured", 
    "popular products", "best sellers", "shop now", "view all"
]

def normalize_url(url, base):
    if not url: return None
    url = url.strip()
    if url.startswith("//"): return "https:" + url
    if url.startswith("/"): return urljoin(base, url)
    return url

def extract_img_from_tag(img_tag, base):
    if not img_tag: return None
    for attr in ["data-src", "data-original", "src"]:
        url = img_tag.get(attr)
        if url and url.strip():
            return normalize_url(url, base)
    return None

def is_valid_product(name, price):
    """Filter out navigation elements and invalid products"""
    if not name or len(name) < 5:
        return False
    
    name_lower = name.lower()
    
    # Filter blacklisted terms
    if any(term in name_lower for term in BLACKLIST_NAMES):
        return False
    
    # Must have at least one word with 4+ characters (not just "New" or "Top")
    words = name.split()
    has_substantial_word = any(len(w) >= 4 for w in words)
    if not has_substantial_word:
        return False
    
    return True

def parse_product_card(card_div):
    """Parse product with better price extraction"""
    try:
        # Image
        img = card_div.find("img")
        image = extract_img_from_tag(img, AGRIBEGRI_BASE) if img else None
        
        # Product name
        name_tag = card_div.find("h4", class_=re.compile(r"title-pdt|product_name"))
        if not name_tag:
            name_tag = card_div.find("h4")
        
        if not name_tag:
            return None
        
        name = clean_text(name_tag.get_text())
        
        # Product link
        link = None
        a_tag = card_div.find("a", href=True)
        if a_tag:
            link = normalize_url(a_tag.get("href"), AGRIBEGRI_BASE)
        
        # Price extraction - IMPROVED
        price = None
        
        # Strategy 1: Look for qty-price div with strong tag
        qty_price = card_div.find("div", class_="qty-price")
        if qty_price:
            strong = qty_price.find("strong")
            if strong:
                price_text = clean_text(strong.get_text())
                price = extract_price(price_text)
        
        # Strategy 2: Look for p.price-pdt strong
        if not price:
            price_p = card_div.find("p", class_=re.compile(r"price-pdt|price"))
            if price_p:
                strong = price_p.find("strong")
                if strong:
                    price = extract_price(clean_text(strong.get_text()))
        
        # Strategy 3: Look for any element with "price" in class
        if not price:
            price_elem = card_div.find(class_=re.compile(r"price|amount"))
            if price_elem:
                # Try to find the main price (not strikethrough)
                strong = price_elem.find("strong")
                if strong:
                    price = extract_price(clean_text(strong.get_text()))
                else:
                    # Get text but exclude <s> tags (old prices)
                    for s_tag in price_elem.find_all("s"):
                        s_tag.decompose()
                    price = extract_price(clean_text(price_elem.get_text()))
        
        # Strategy 4: Search all text for price pattern (last resort)
        if not price:
            all_text = " ".join(card_div.stripped_strings)
            # Find all prices and take the first one
            matches = re.findall(r'₹\s*[\d,]+', all_text)
            if matches:
                price = matches[0].replace(" ", "")
        
        # Validate product
        if not is_valid_product(name, price):
            return None
        
        # Description
        description = ""
        desc_elem = card_div.find("p", class_=re.compile(r"desc|info|detail"))
        if desc_elem:
            description = clean_text(desc_elem.get_text())[:150]
        
        return {
            "name": name,
            "category": "Pesticide",
            "price": price or "Price on Request",
            "description": description,
            "image_url": image,
            "product_url": link
        }
    
    except Exception:
        return None

def scrape_agribegri_pesticides(max_pages=2, per_page_limit=None, delay=1.5):
    """Scrape pesticides with filtering"""
    print("\n" + "="*70)
    print("🌿 SCRAPING AGRIBEGRI PESTICIDES (FILTERED)")
    print("="*70)
    
    products = []
    page = 1
    
    while page <= max_pages:
        url = f"{AGRIBEGRI_PEST_PAGE}?page={page}"
        print(f"\n📄 Page {page}: {url}")
        
        soup = get_soup(url)
        if not soup:
            print("  ✗ Failed to fetch")
            break
        
        # Find product cards
        cards = soup.find_all("div", class_=re.compile(r"item-effect-item"))
        
        if not cards:
            all_divs = soup.find_all("div", recursive=True)
            cards = [
                d for d in all_divs 
                if d.find("img") and d.find("h4") and 
                len(d.find_all("div")) < 15
            ]
        
        print(f"  Found {len(cards)} candidate cards")
        
        if not cards:
            break
        
        parsed = 0
        skipped = 0
        
        for card in cards:
            item = parse_product_card(card)
            if item:
                products.append(item)
                parsed += 1
                print(f"  ✓ [{parsed}] {item['name'][:50]}")
                print(f"          {item['price']}")
                
                if per_page_limit and len(products) >= per_page_limit:
                    return products
            else:
                skipped += 1
        
        print(f"  → Parsed: {parsed}, Skipped: {skipped} (nav/duplicates)")
        
        page += 1
        if page <= max_pages:
            time.sleep(delay)
    
    print(f"\n{'='*70}")
    print(f"✓ Total valid products: {len(products)}")
    print("="*70)
    return products

# ============= Database Functions =============

def ensure_tables_exist(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute('''CREATE TABLE IF NOT EXISTS pesticide_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        category TEXT,
        price TEXT,
        description TEXT,
        image_url TEXT,
        product_url TEXT,
        scraped_at TEXT
    )''')
    cur.execute('''CREATE TABLE IF NOT EXISTS equipment_products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        category TEXT,
        price TEXT,
        description TEXT,
        image_url TEXT,
        product_url TEXT,
        scraped_at TEXT
    )''')
    conn.commit()
    conn.close()

def insert_products_into_db(products, db_path, table='pesticide_products'):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    inserted = 0
    duplicates = 0
    now = datetime.now(timezone.utc).isoformat()
    
    for p in products:
        try:
            cur.execute(f'''
                INSERT OR IGNORE INTO {table}
                (name, category, price, description, image_url, product_url, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (p['name'], p['category'], p['price'], p.get('description', ''),
                  p.get('image_url'), p.get('product_url'), now))
            
            if cur.rowcount > 0:
                inserted += 1
            else:
                duplicates += 1
        except Exception as e:
            print(f"  ✗ Insert error: {e}")
    
    conn.commit()
    conn.close()
    return inserted, duplicates

def export_csv(products, path="pesticide_products.csv"):
    if not products: return
    
    keys = ["name", "category", "price", "description", "image_url", "product_url"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=keys)
        writer.writeheader()
        writer.writerows({k: p.get(k, "") for k in keys} for p in products)
    print(f"✓ CSV saved: {path}")

# ============= Public API =============

def _get_db_path():
    try:
        from config import Config
        return Config.DATABASE_PATH
    except:
        return str(PROJECT_ROOT / "database" / "farmer_portal.db")

def _fallback_products():
    return [
        {'name': 'Bayer Confidor Insecticide (Imidacloprid)', 'category': 'Insecticide', 'price': '₹450',
         'description': 'Effective systemic insecticide', 'image_url': 'https://images.unsplash.com/photo-1464226184884-fa280b87c399',
         'product_url': AGRIBEGRI_BASE},
        {'name': 'Syngenta Actara 25 WG (Thiamethoxam)', 'category': 'Insecticide', 'price': '₹380',
         'description': 'Broad spectrum insecticide', 'image_url': 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8',
         'product_url': AGRIBEGRI_BASE},
        {'name': 'Tata Rallis Manik Fungicide (Mancozeb)', 'category': 'Fungicide', 'price': '₹520',
         'description': 'Protective fungicide for crops', 'image_url': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b',
         'product_url': AGRIBEGRI_BASE},
    ]

def scrape_pesticides(sample_limit=None, delay=1.5):
    """Main scraping function"""
    db_path = _get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    ensure_tables_exist(db_path)
    
    products = scrape_agribegri_pesticides(max_pages=3, per_page_limit=sample_limit, delay=delay)
    
    if len(products) < 3:
        print("\n⚠ Few products found, adding fallback...")
        products.extend(_fallback_products())
    
    print(f"\n📊 Inserting {len(products)} products...")
    inserted, duplicates = insert_products_into_db(products, db_path)
    print(f"✓ Inserted: {inserted}, Duplicates: {duplicates}")
    
    try:
        export_csv(products)
    except:
        pass
    
    return int(inserted)

def scrape_equipment(sample_limit=None, delay=1.0):
    """Equipment scraping"""
    db_path = _get_db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    ensure_tables_exist(db_path)
    
    equipment = [
        {'name': 'Mini Tiller Cultivator 5.5 HP', 'category': 'Tillage', 'price': '₹15,500',
         'description': 'Compact petrol tiller', 'image_url': 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449',
         'product_url': AGRIBEGRI_BASE},
        {'name': 'Battery Power Sprayer 16L', 'category': 'Spraying', 'price': '₹8,200',
         'description': 'High-pressure sprayer', 'image_url': 'https://images.unsplash.com/photo-1585408390579-e15d5dfcadf7',
         'product_url': AGRIBEGRI_BASE}
    ]
    
    inserted, _ = insert_products_into_db(equipment, db_path, 'equipment_products')
    return int(inserted)

if __name__ == "__main__":
    print("🚀 Testing Refined AgriBegri Scraper\n")
    count = scrape_pesticides(sample_limit=50, delay=1.0)
    print(f"\n{'='*70}")
    print(f"✅ COMPLETE! {count} products inserted")
    print("="*70)
