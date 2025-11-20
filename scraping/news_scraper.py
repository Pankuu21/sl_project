import sqlite3
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import Config
from scraping.scraper_utils import get_soup, clean_text

def scrape_farmer_news():
    """Scrape agricultural news from multiple sources"""
    
    print("Starting news scraping...")
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    news_items = []
    
    # Source 1: Down To Earth (Agriculture section)
    print("\n1. Scraping Down To Earth...")
    try:
        soup = get_soup('https://www.downtoearth.org.in/agriculture')
        if soup:
            articles = soup.find_all('div', class_='card-story')[:10]
            
            for article in articles:
                try:
                    headline_tag = article.find('h3') or article.find('h2')
                    headline = clean_text(headline_tag.get_text()) if headline_tag else None
                    
                    link_tag = article.find('a', href=True)
                    url = 'https://www.downtoearth.org.in' + link_tag['href'] if link_tag else None
                    
                    summary_tag = article.find('p')
                    summary = clean_text(summary_tag.get_text()) if summary_tag else ""
                    
                    img_tag = article.find('img', src=True)
                    image_url = img_tag['src'] if img_tag else None
                    
                    if headline and url:
                        news_items.append({
                            'headline': headline,
                            'summary': summary,
                            'source': 'Down To Earth',
                            'url': url,
                            'image_url': image_url,
                            'published_date': datetime.now().strftime('%Y-%m-%d')
                        })
                except Exception as e:
                    print(f"Error parsing article: {e}")
                    continue
            
            print(f"✓ Found {len(news_items)} articles from Down To Earth")
    
    except Exception as e:
        print(f"✗ Error scraping Down To Earth: {e}")
    
    # Source 2: Add sample/demo news if scraping fails
    if len(news_items) < 5:
        print("\nAdding demo news articles...")
        demo_news = [
            {
                'headline': 'Government Announces New Minimum Support Price for Crops',
                'summary': 'The government has increased MSP for major crops to support farmers.',
                'source': 'PIB India',
                'url': 'https://pib.gov.in',
                'image_url': 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449',
                'published_date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'headline': 'Organic Farming Techniques Gain Popularity Among Indian Farmers',
                'summary': 'More farmers are adopting organic methods to improve soil health.',
                'source': 'Agriculture News',
                'url': 'https://agriculturenews.in',
                'image_url': 'https://images.unsplash.com/photo-1574943320219-553eb213f72d',
                'published_date': datetime.now().strftime('%Y-%m-%d')
            },
            {
                'headline': 'New Mobile App Helps Farmers Get Real-Time Weather Updates',
                'summary': 'Technology is empowering farmers with accurate weather predictions.',
                'source': 'Tech in Agriculture',
                'url': 'https://example.com',
                'image_url': 'https://images.unsplash.com/photo-1560493676-04071c5f467b',
                'published_date': datetime.now().strftime('%Y-%m-%d')
            }
        ]
        news_items.extend(demo_news)
    
    # Insert into database
    print(f"\nInserting {len(news_items)} news articles into database...")
    inserted = 0
    
    for news in news_items:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO news_articles 
                (headline, summary, source, url, image_url, published_date)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                news['headline'],
                news['summary'],
                news['source'],
                news['url'],
                news['image_url'],
                news['published_date']
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting news: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Successfully inserted {inserted} new articles")
    print("News scraping complete!")
    
    return inserted

if __name__ == '__main__':
    scrape_farmer_news()
