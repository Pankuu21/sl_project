import sqlite3
from pathlib import Path
import pandas as pd
from config import Config

def init_database():
    """Initialize SQLite database with required tables"""
    
    # Create database directory if not exists
    Path(Config.DATABASE_PATH).parent.mkdir(exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(Config.DATABASE_PATH)
    cursor = conn.cursor()
    
    print("Creating database tables...")
    
    # Table 1: Crops Data (from CSV)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS crops_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            N INTEGER NOT NULL,
            P INTEGER NOT NULL,
            K INTEGER NOT NULL,
            temperature REAL NOT NULL,
            humidity REAL NOT NULL,
            ph REAL NOT NULL,
            rainfall REAL NOT NULL,
            label TEXT NOT NULL
        )
    ''')
    
    # Table 2: News Articles
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS news_articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            headline TEXT NOT NULL,
            summary TEXT,
            source TEXT NOT NULL,
            url TEXT UNIQUE NOT NULL,
            image_url TEXT,
            published_date TEXT,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table 3: Pesticide Products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pesticide_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price TEXT,
            description TEXT,
            image_url TEXT,
            product_url TEXT UNIQUE,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table 4: Equipment Products
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT,
            price TEXT,
            description TEXT,
            image_url TEXT,
            product_url TEXT UNIQUE,
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Table 5: User Predictions
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            N INTEGER,
            P INTEGER,
            K INTEGER,
            temperature REAL,
            humidity REAL,
            ph REAL,
            rainfall REAL,
            predicted_crop TEXT,
            confidence REAL,
            prediction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
CREATE TABLE IF NOT EXISTS search_products (
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
)
''')

    cursor.execute('''
CREATE TABLE IF NOT EXISTS government_schemes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    scheme_name TEXT UNIQUE,
    publish_date TEXT,
    doc_links TEXT,
    apply_links TEXT,
    scraped_at TEXT
)
''')

    cursor.execute('''
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


    
    conn.commit()
    print("✓ Database tables created successfully!")
    
    # Load crop dataset into database
    if Config.DATASET_PATH.exists():
        print("\nLoading crop dataset into database...")
        try:
            df = pd.read_csv(Config.DATASET_PATH)
            df.to_sql('crops_data', conn, if_exists='replace', index=False)
            print(f"✓ Loaded {len(df)} crop records into database!")
        except Exception as e:
            print(f"✗ Error loading dataset: {e}")
    else:
        print(f"⚠ Dataset not found at {Config.DATASET_PATH}")
        print("  Please add Crop_recommendation.csv to the project root")
    
    # Display table stats
    cursor.execute("SELECT COUNT(*) FROM crops_data")
    crop_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM news_articles")
    news_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM pesticide_products")
    pesticide_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM equipment_products")
    equipment_count = cursor.fetchone()[0]
    
    print("\n" + "="*50)
    print("DATABASE STATISTICS")
    print("="*50)
    print(f"Crop Records: {crop_count}")
    print(f"News Articles: {news_count}")
    print(f"Pesticide Products: {pesticide_count}")
    print(f"Equipment Products: {equipment_count}")
    print("="*50)
    
    conn.close()
    print("\n✓ Database initialization complete!")

if __name__ == '__main__':
    init_database()
