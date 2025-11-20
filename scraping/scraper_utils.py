import requests
from bs4 import BeautifulSoup
import time
from config import Config

def get_soup(url, delay=Config.SCRAPING_DELAY):
    """
    Get BeautifulSoup object from URL with error handling
    
    Args:
        url: URL to scrape
        delay: Delay between requests (seconds)
    
    Returns:
        BeautifulSoup object or None
    """
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    retries = 0
    while retries < Config.MAX_RETRIES:
        try:
            time.sleep(delay)
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        
        except requests.exceptions.RequestException as e:
            retries += 1
            print(f"Error fetching {url}: {e}")
            if retries < Config.MAX_RETRIES:
                print(f"Retrying... ({retries}/{Config.MAX_RETRIES})")
                time.sleep(delay * 2)
            else:
                print(f"Failed after {Config.MAX_RETRIES} retries")
                return None

def clean_text(text):
    """Clean and normalize text"""
    if not text:
        return ""
    return ' '.join(text.strip().split())

def extract_price(price_text):
    """Extract price from text"""
    if not price_text:
        return "N/A"
    # Remove currency symbols and extra spaces
    import re
    price = re.sub(r'[^\d.,]', '', price_text)
    return price if price else "N/A"
