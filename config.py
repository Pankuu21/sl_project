import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent

class Config:
    """Application configuration"""
    
    # Flask
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    DEBUG = True
    
    # Database
    DATABASE_PATH = BASE_DIR / 'database' / 'farmer_portal.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DATABASE_PATH}'
    
    # ML Model
    MODEL_PATH = BASE_DIR / 'ml_models' / 'crop_model.pkl'
    SCALER_PATH = BASE_DIR / 'ml_models' / 'scaler.pkl'
    DATASET_PATH = BASE_DIR / 'Crop_recommendation.csv'
    
    # Scraping
    SCRAPING_DELAY = 2  # seconds between requests
    MAX_RETRIES = 3
    CACHE_TIMEOUT = 3600  # 1 hour
    
    # Pagination
    NEWS_PER_PAGE = 12
    PRODUCTS_PER_PAGE = 16
    
    # Scheduler (for auto-scraping)
    SCRAPING_INTERVAL_HOURS = 6
    
    # Crop information
    CROP_INFO = {
        'rice': {
            'image': 'https://images.unsplash.com/photo-1586201375761-83865001e31c',
            'season': 'Kharif',
            'duration': '120-150 days',
            'tips': 'Requires standing water, high humidity'
        },
        'wheat': {
            'image': 'https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b',
            'season': 'Rabi',
            'duration': '120-150 days',
            'tips': 'Requires well-drained soil, cool climate'
        },
        'maize': {
            'image': 'https://images.unsplash.com/photo-1603052418422-596c7e0f1e6f',
            'season': 'Kharif/Rabi',
            'duration': '80-120 days',
            'tips': 'Moderate water requirement, fertile soil'
        },
        'cotton': {
            'image': 'https://images.unsplash.com/photo-1607081692251-5e7aae7e2c9a',
            'season': 'Kharif',
            'duration': '150-180 days',
            'tips': 'Requires warm climate, black soil preferred'
        },
        'sugarcane': {
            'image': 'https://images.unsplash.com/photo-1563729784364-42c9d81e0eb4',
            'season': 'Year-round',
            'duration': '10-18 months',
            'tips': 'High water requirement, tropical climate'
        }
        # Add more crops as needed
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
