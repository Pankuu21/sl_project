import sqlite3
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from config import Config
from scraping.scraper_utils import get_soup, clean_text, extract_price

def scrape_pesticides():
    """Scrape pesticide products"""
    
    print("Starting pesticide scraping...")
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    products = []
    
    # Add demo products (replace with actual scraping)
    print("Adding demo pesticide products...")
    
    demo_products = [
        {
            'name': 'Bayer Confidor Insecticide',
            'category': 'Insecticide',
            'price': '₹450',
            'description': 'Effective against sucking pests, thrips, and whiteflies',
            'image_url': 'https://images.unsplash.com/photo-1464226184884-fa280b87c399',
            'product_url': 'https://example.com/product1'
        },
        {
            'name': 'Syngenta Actara 25 WG',
            'category': 'Insecticide',
            'price': '₹380',
            'description': 'Broad spectrum insecticide for various crops',
            'image_url': 'https://images.unsplash.com/photo-1530836369250-ef72a3f5cda8',
            'product_url': 'https://example.com/product2'
        },
        {
            'name': 'Tata Rallis Manik Fungicide',
            'category': 'Fungicide',
            'price': '₹520',
            'description': 'Controls fungal diseases in paddy and vegetables',
            'image_url': 'https://images.unsplash.com/photo-1416879595882-3373a0480b5b',
            'product_url': 'https://example.com/product3'
        },
        {
            'name': 'UPL Saaf Fungicide',
            'category': 'Fungicide',
            'price': '₹290',
            'description': 'Preventive and curative fungicide',
            'image_url': 'https://images.unsplash.com/photo-1523348837708-15d4a09cfac2',
            'product_url': 'https://example.com/product4'
        },
        {
            'name': 'Coromandel Nuvan Pesticide',
            'category': 'Pesticide',
            'price': '₹340',
            'description': 'Effective pest control for cereals',
            'image_url': 'https://images.unsplash.com/photo-1592982537447-7440770cbfc9',
            'product_url': 'https://example.com/product5'
        },
        {
            'name': 'Dhanuka Targa Super Herbicide',
            'category': 'Herbicide',
            'price': '₹680',
            'description': 'Post-emergence herbicide for weed control',
            'image_url': 'https://images.unsplash.com/photo-1589923188900-85dae523342b',
            'product_url': 'https://example.com/product6'
        }
    ]
    
    products.extend(demo_products)
    
    # Insert into database
    print(f"\nInserting {len(products)} products into database...")
    inserted = 0
    
    for product in products:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO pesticide_products
                (name, category, price, description, image_url, product_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                product['name'],
                product['category'],
                product['price'],
                product['description'],
                product['image_url'],
                product['product_url']
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting product: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Successfully inserted {inserted} new products")
    print("Pesticide scraping complete!")
    
    return inserted

def scrape_equipment():
    """Scrape farming equipment"""
    
    print("\nStarting equipment scraping...")
    
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    equipment = []
    
    # Add demo equipment
    print("Adding demo equipment products...")
    
    demo_equipment = [
        {
            'name': 'Mini Tiller Cultivator',
            'category': 'Tillage Equipment',
            'price': '₹15,500',
            'description': 'Compact and efficient for small farms',
            'image_url': 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449',
            'product_url': 'https://example.com/equip1'
        },
        {
            'name': 'Power Sprayer 16L',
            'category': 'Spraying Equipment',
            'price': '₹8,200',
            'description': 'Battery operated, perfect for pesticide application',
            'image_url': 'https://images.unsplash.com/photo-1585408390579-e15d5dfcadf7',
            'product_url': 'https://example.com/equip2'
        },
        {
            'name': 'Seed Drill Machine',
            'category': 'Sowing Equipment',
            'price': '₹12,000',
            'description': 'Precision sowing for better yield',
            'image_url': 'https://images.unsplash.com/photo-1589923188900-85dae523342b',
            'product_url': 'https://example.com/equip3'
        },
        {
            'name': 'Chaff Cutter Machine',
            'category': 'Harvesting Equipment',
            'price': '₹18,500',
            'description': 'Heavy duty chaff cutting for fodder',
            'image_url': 'https://images.unsplash.com/photo-1523348837708-15d4a09cfac2',
            'product_url': 'https://example.com/equip4'
        }
    ]
    
    equipment.extend(demo_equipment)
    
    # Insert into database
    print(f"\nInserting {len(equipment)} equipment into database...")
    inserted = 0
    
    for item in equipment:
        try:
            cursor.execute('''
                INSERT OR IGNORE INTO equipment_products
                (name, category, price, description, image_url, product_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                item['name'],
                item['category'],
                item['price'],
                item['description'],
                item['image_url'],
                item['product_url']
            ))
            if cursor.rowcount > 0:
                inserted += 1
        except Exception as e:
            print(f"Error inserting equipment: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Successfully inserted {inserted} new equipment")
    print("Equipment scraping complete!")
    
    return inserted

if __name__ == '__main__':
    scrape_pesticides()
    scrape_equipment()
