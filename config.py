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

    # Weather API
    OPENWEATHER_API_KEY = "dcdee92ea032b014d62ed8abdb24415e"
    # ← Add your key
    OPENWEATHER_BASE_URL = "https://api.openweathermap.org/data/2.5"
    
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
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQFpDE03H4faCp45-nKSTsV67n-e9xlkYJ57Q&s',
            'season': 'Kharif/Rabi',
            'duration': '80-120 days',
            'tips': 'Moderate water requirement, fertile soil'
        },
        'cotton': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSW-zm4h_Y42XY5U8JVUzBj56CqhZn1TtNeGw&s',
            'season': 'Kharif',
            'duration': '150-180 days',
            'tips': 'Requires warm climate, black soil preferred'
        },
        'sugarcane': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcRZxUgdFKbf0LQXiiRmdmfd560osZKTWMCQ0w&s',
            'season': 'Year-round',
            'duration': '10-18 months',
            'tips': 'High water requirement, tropical climate'
        },
        'chickpea': {
        'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ_S-GsJNbQVpcAh586rKATFcdan0vWjZE6JA&s',
        'season': 'Rabi',
        'duration': '90-120 days',
        'tips': 'Prefers cool and dry climate; grows well in loamy soil with good drainage'
        },
        'kidneybeans': {
            'image': 'https://www.apnikheti.com/upload/crops/489idea99Red-kidney-beans-2.jpg',
            'season': 'Kharif',
            'duration': '90-110 days',
            'tips': 'Requires warm climate and moderately fertile soil'
        },
        'pigeonpeas': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR5iRqoogIXL1abhtF4FTiwfhGLJsT7iUUlMA&s',
            'season': 'Kharif',
            'duration': '150-180 days',
            'tips': 'Requires warm climate and well-drained soil'
        },
        'mothbeans': {
            'image': 'https://5.imimg.com/data5/SELLER/Default/2020/9/WB/TK/QU/106270270/turkish-gram-moth-bean.jpg',
            'season': 'Kharif',
            'duration': '60-70 days',
            'tips': 'Highly drought-tolerant; suitable for arid areas'
        },
        'mungbean': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQT-uLQSwX-vtL1DpU4aNlnat8iQxLR7u4uKw&s',
            'season': 'Kharif/Rabi/Summer',
            'duration': '60-70 days',
            'tips': 'Requires warm weather and well-drained sandy loam'
        },
        'blackgram': {
            'image': 'https://upload.wikimedia.org/wikipedia/commons/6/6f/Black_gram.jpg',
            'season': 'Kharif/Rabi',
            'duration': '70-120 days',
            'tips': 'Prefers warm climate and fertile soil'
        },
        'lentil': {
            'image': 'https://5.imimg.com/data5/VG/NB/MY-52019636/red-lentil-dal.jpg',
            'season': 'Rabi',
            'duration': '100-120 days',
            'tips': 'Requires cool climate and moderate moisture'
        },

        # Fruits
        'pomegranate': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSV9QZflIVbExc9ooR4fOxd2WtpREJClB4wgg&s',
            'season': 'Multiple seasons (Ambe, Mrig, Hasta)',
            'duration': '150-180 days from flowering',
            'tips': 'Thrives in hot, dry climate; avoid waterlogging'
        },
        'banana': {
            'image': 'https://im.pluckk.in/unsafe/1600x0/uploads/35122-akgpihz0y-vvxgprhblp2ur72zwazwxntgjawuaeztuee-rc-owvffgisyvdzxsyy-ms8xw25t0vo74rpqlekiotgobt9fqgqrdmaqs1600-rw-v1.webp',
            'season': 'Year-round',
            'duration': '10-12 months',
            'tips': 'High water need; prefers warm, humid climate'
        },
        'mango': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR4XO0BrRRPWPbuitdqGNfsoTwnZ4QnS_knyg&s',
            'season': 'Flowering Jan–Mar, harvest Apr–Jun',
            'duration': '5–6 months',
            'tips': 'Requires tropical climate and dry weather during flowering'
        },
        'grapes': {
            'image': 'https://www.apnikheti.com/upload/crops/1850idea99grapes.jpg',
            'season': 'Harvest Jan–Mar (India)',
            'duration': '120-150 days',
            'tips': 'Needs dry weather during ripening'
        },
        'watermelon': {
            'image': 'https://m.media-amazon.com/images/I/91job1aOASS.AC_UF1000,1000_QL80.jpg',
            'season': 'Zaid (Summer)',
            'duration': '70-90 days',
            'tips': 'Grows best in hot dry climate; sandy loam soil'
        },
        'muskmelon': {
            'image': 'https://goldenhillsfarm.in/media/ckeditor_uploads/2024/10/22/muskmelon-madhuras.jpg',
            'season': 'Zaid',
            'duration': '75-90 days',
            'tips': 'Warm climate and low humidity required'
        },
        'apple': {
            'image': 'https://cdn.britannica.com/22/187222-050-07B17FB6/apples-on-a-tree-branch.jpg',
            'season': 'Temperate (harvest Aug–Oct)',
            'duration': '150-180 days',
            'tips': 'Requires chilling period and temperate climate'
        },
        'orange': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQh09mUdNc9gzNDPKcBq-9Gcf_W25SB8pHcrRvH7sFafhh82yJo4NvEnoNOl7U3X8681OQ&usqp=CAU',
            'season': 'Varies by region (winter/summer crop)',
            'duration': '240-300 days',
            'tips': 'Thrives in subtropical climate with good drainage'
        },
        'papaya': {
            'image': 'https://cdn.wikifarmer.com/images/detailed/2023/10/Harvest-yield.png',
            'season': 'Year-round',
            'duration': '8-10 months',
            'tips': 'Needs warm climate and well-drained soil'
        },
        'coconut': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQ82_OoST1lP-lmi-j7XleRQz5YJIWUKXnF5w&s',
            'season': 'Year-round',
            'duration': '11-12 months for fruit maturity',
            'tips': 'Thrives in coastal tropical climate'
        },

        # Others
        'jute': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTNfT7tkHUzx8XxaY_hQ3fwHfB2X_7eMy61qw&s',
            'season': 'Kharif',
            'duration': '100-120 days',
            'tips': 'Requires warm humid climate and alluvial soil'
        },
        'coffee': {
            'image': 'https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcQn27o-ICLnOnOznHZ6Hf7KpB7PudzjlT81Cg&s',
            'season': 'Flowering Feb–Mar; harvest Nov–Jan',
            'duration': '6-8 months from flowering',
            'tips': 'Requires shade, rainfall, and cool tropical climate'
        }
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
