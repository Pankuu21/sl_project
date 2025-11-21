import sqlite3
from datetime import datetime
import sys
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re

sys.path.append(str(Path(__file__).parent.parent))
from config import Config
from scraping.scraper_utils import clean_text

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/139.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-US, en;q=0.5'
}

KRISHI_JAGRAN_URL = "https://krishijagran.com/agriculture-world/"
MAX_ITEMS = 20

def _get_img_src(img_tag, base_url):
    """Extract actual image URL from <img> or from style in <a class='img'>."""
    if img_tag is None:
        return None
    # If it's a normal <img> element
    if img_tag.name == "img":
        for attr in ("src", "data-src", "data-lazy-src",
                     "data-original", "data-lazy", "data-srcset"):
            val = img_tag.get(attr)
            if val and val.strip():
                return urljoin(base_url, val.strip())
        # Handle srcset attribute
        srcset = img_tag.get("srcset")
        if srcset:
            parts = [p.strip().split(" ")[0] for p in srcset.split(",") if p.strip()]
            if parts:
                return urljoin(base_url, parts[0])
    # If <a class='img'> with style attribute
    if img_tag.name == "a":
        style = img_tag.get("style", "")
        m = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
        if m:
            return urljoin(base_url, m.group(1))
        # Try <img> as child
        inner_img = img_tag.find("img")
        if inner_img:
            return _get_img_src(inner_img, base_url)
    return None

def scrape_krishi_jagran():
    """
    Scrape Krishi Jagran Agriculture World page and return news dicts with images.
    Uses direct <img> tag (data-src or src), falling back to background/style image if needed.
    """
    from datetime import datetime
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin

    KRISHI_JAGRAN_URL = "https://krishijagran.com/agriculture-world/"
    MAX_ITEMS = 20
    HEADERS = {
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/139.0.0.0 Safari/537.36'
        ),
        'Accept-Language': 'en-US, en;q=0.5'
    }

    def clean_text(s):
        # Use your project clean_text or fallback
        return " ".join(s.split()) if s else ""

    def _get_img_src_fallback(a_img, base_url):
        # Old fallback for <a class='img'> with style or inner <img>
        import re
        image_url = None
        if a_img is None:
            return None
        style = a_img.get("style", "")
        m = re.search(r"url\(['\"]?(.*?)['\"]?\)", style)
        if m:
            image_url = urljoin(base_url, m.group(1))
        inner_img = a_img.find("img")
        if not image_url and inner_img:
            for attr in ("data-src", "src"):
                val = inner_img.get(attr)
                if val and val.strip():
                    image_url = urljoin(base_url, val.strip())
        return image_url

    print("\nScraping Krishi Jagran (Agriculture World page)")
    news_items = []

    try:
        resp = requests.get(KRISHI_JAGRAN_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Select all news cards
        candidates = soup.select("div.nc-item, div.nc-item.shadow-sm")
        if not candidates:
            candidates = soup.select("h2 > a")

        for node in candidates:
            if len(news_items) >= MAX_ITEMS:
                break

            headline, article_url, image_url = "", None, None

            if node.name == "div":
                # Headline and Article URL
                a_title = node.select_one("h2 > a") or node.select_one("a:not(.img)")
                headline = clean_text(a_title.get_text(strip=True)) if a_title else ""
                article_url = urljoin(KRISHI_JAGRAN_URL, a_title["href"]) if a_title and a_title.has_attr("href") else None

                # 📸 IMAGE: Try direct <img> tag
                img_tag = node.find("img")
                if img_tag:
                    image_url = img_tag.get("data-src") or img_tag.get("src")
                    if image_url:
                        image_url = urljoin(KRISHI_JAGRAN_URL, image_url)
                else:
                    # Fallback: <a class='img'>/style or child <img>
                    a_img = node.select_one("a.img")
                    image_url = _get_img_src_fallback(a_img, KRISHI_JAGRAN_URL)

            else:
                # For cases where node is a <a> (rare on this site)
                a_title = node
                headline = clean_text(a_title.get_text(strip=True))
                article_url = urljoin(KRISHI_JAGRAN_URL, a_title.get("href", ""))
                parent = node.parent
                img_tag = parent.find("img") if parent else None
                if img_tag:
                    image_url = img_tag.get("data-src") or img_tag.get("src")
                    if image_url:
                        image_url = urljoin(KRISHI_JAGRAN_URL, image_url)
                else:
                    a_img = parent.select_one("a.img") if parent else None
                    image_url = _get_img_src_fallback(a_img, KRISHI_JAGRAN_URL)

            # Only save if at least headline and article_url exist
            if headline and article_url:
                news_items.append({
                    "headline": headline,
                    "summary": "",
                    "source": "Krishi Jagran",
                    "url": article_url,
                    "image_url": image_url,
                    "published_date": datetime.now().strftime("%Y-%m-%d"),
                })
                print(f" ✓ {headline[:60]} | [Image: {'Yes' if image_url else 'No'}]")

        print(f" ✓ Found {len(news_items)} articles from Krishi Jagran")

    except Exception as e:
        print(f" ✗ Error scraping Krishi Jagran: {e}")

    return news_items


def scrape_farmer_news():
    """Main function to scrape Krishi Jagran for agri news and store in DB."""
    print("=" * 70)
    print("AGRICULTURAL NEWS SCRAPING")
    print("=" * 70)

    all_news = scrape_krishi_jagran()

    print(f"\n{'=' * 70}")
    print(f"Inserting {len(all_news)} news articles into database...")
    print("=" * 70)

    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()

    inserted = 0
    duplicates = 0

    for news in all_news:
        try:
            cursor.execute(
                """
                INSERT OR IGNORE INTO news_articles
                (headline, summary, source, url, image_url, published_date)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    news["headline"],
                    news["summary"],
                    news["source"],
                    news["url"],
                    news["image_url"],
                    news["published_date"],
                ),
            )

            if cursor.rowcount > 0:
                inserted += 1
            else:
                duplicates += 1

        except Exception as e:
            print(f"Error inserting news: {e}")

    conn.commit()
    conn.close()

    print(f"\n{'=' * 70}")
    print("SCRAPING SUMMARY")
    print("=" * 70)
    print(f"✓ Total articles found: {len(all_news)}")
    print(f"✓ New articles inserted: {inserted}")
    print(f"✓ Duplicates skipped: {duplicates}")
    print("=" * 70)

    return inserted

if __name__ == "__main__":
    scrape_farmer_news()