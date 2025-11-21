from flask import Flask, render_template, request, jsonify ,flash ,redirect ,url_for
from flask_cors import CORS
import sqlite3
from datetime import datetime
import sys
from pathlib import Path
from config import Config
from ml_models.predict import predict_crop
from scraping.news_scraper import scrape_farmer_news
from scraping.pesticide_scraper import scrape_pesticides, scrape_equipment

app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Database helper
def get_db_connection():
    """Create database connection"""
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ============= ROUTES =============

@app.route('/')
def index():
    """Homepage"""
    return render_template('index.html')

@app.route('/crop-recommendation')
def crop_recommendation():
    """Crop recommendation page"""
    return render_template('crop_recommend.html')

@app.route('/news')
def news():
    """News aggregator page"""
    page = request.args.get('page', 1, type=int)
    per_page = Config.NEWS_PER_PAGE
    
    conn = get_db_connection()
    
    # Get total count
    total = conn.execute('SELECT COUNT(*) FROM news_articles').fetchone()[0]
    
    # Get paginated news
    offset = (page - 1) * per_page
    news_articles = conn.execute('''
        SELECT * FROM news_articles 
        ORDER BY scraped_at DESC 
        LIMIT ? OFFSET ?
    ''', (per_page, offset)).fetchall()
    
    conn.close()
    
    total_pages = (total + per_page - 1) // per_page
    
    return render_template('news.html', 
                         news=news_articles, 
                         page=page, 
                         total_pages=total_pages)

# app.py - MODIFIED /products route with search

# ============= NEW: DYNAMIC SEARCH ROUTE =============
@app.route('/search-products', methods=['GET', 'POST'])
def search_products():
    """Dynamic product search across all sources"""
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        if keyword:
            try:
                from scraping.multi_source_scraper import scrape_by_keyword
                count = scrape_by_keyword(keyword, max_per_source=15)
                flash(f'Successfully scraped {count} products for "{keyword}"', 'success')
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('search_products', keyword=keyword))
    
    # GET request - display results
    keyword = request.args.get('keyword', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = 12
    
    conn = get_db_connection()
    
    if keyword:
        query = "SELECT * FROM search_products WHERE keyword = ?"
        count_query = "SELECT COUNT(*) FROM search_products WHERE keyword = ?"
        params = [keyword]
    else:
        query = "SELECT * FROM search_products"
        count_query = "SELECT COUNT(*) FROM search_products"
        params = []
    
    total = conn.execute(count_query, params).fetchone()[0]
    total_pages = (total + per_page - 1) // per_page
    
    query += " ORDER BY scraped_at DESC LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    products_list = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template(
        'search_products.html',
        products=products_list,
        keyword=keyword,
        page=page,
        total_pages=total_pages
    )


@app.route('/analytics')
def analytics():
    """Analytics dashboard page"""
    conn = get_db_connection()
    
    # Get crop distribution from predictions
    crop_dist = conn.execute('''
        SELECT predicted_crop, COUNT(*) as count 
        FROM user_predictions 
        GROUP BY predicted_crop
    ''').fetchall()
    
    # Get recent predictions
    recent_predictions = conn.execute('''
        SELECT * FROM user_predictions 
        ORDER BY prediction_date DESC 
        LIMIT 10
    ''').fetchall()
    
    # Get average nutrient values by crop from dataset
    avg_nutrients = conn.execute('''
        SELECT label, 
               AVG(N) as avg_n, 
               AVG(P) as avg_p, 
               AVG(K) as avg_k,
               AVG(temperature) as avg_temp,
               AVG(humidity) as avg_humidity,
               AVG(ph) as avg_ph,
               AVG(rainfall) as avg_rainfall
        FROM crops_data 
        GROUP BY label
    ''').fetchall()
    
    conn.close()
    
    return render_template('analytics.html',
                         crop_dist=crop_dist,
                         recent_predictions=recent_predictions,
                         avg_nutrients=avg_nutrients)

# ============= API ROUTES =============

@app.route('/api/predict', methods=['POST'])
def api_predict():
    """Crop prediction API endpoint"""
    try:
        data = request.get_json()
        
        # Extract parameters
        N = float(data.get('N'))
        P = float(data.get('P'))
        K = float(data.get('K'))
        temperature = float(data.get('temperature'))
        humidity = float(data.get('humidity'))
        ph = float(data.get('ph'))
        rainfall = float(data.get('rainfall'))
        
        # Validate inputs
        if not all([N >= 0, P >= 0, K >= 0, temperature >= -10, 
                   humidity >= 0, humidity <= 100, ph >= 0, ph <= 14, rainfall >= 0]):
            return jsonify({
                'success': False,
                'error': 'Invalid input values'
            }), 400
        
        # Get prediction
        result = predict_crop(N, P, K, temperature, humidity, ph, rainfall)
        
        if result['success']:
            # Save to database
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO user_predictions 
                (N, P, K, temperature, humidity, ph, rainfall, predicted_crop, confidence)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (N, P, K, temperature, humidity, ph, rainfall, 
                  result['crop'], result['confidence']))
            conn.commit()
            conn.close()
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/news')
def api_news():
    """Get news articles API"""
    limit = request.args.get('limit', 10, type=int)
    search = request.args.get('search', '')
    
    conn = get_db_connection()
    
    if search:
        news_articles = conn.execute('''
            SELECT * FROM news_articles 
            WHERE headline LIKE ? OR summary LIKE ?
            ORDER BY scraped_at DESC 
            LIMIT ?
        ''', (f'%{search}%', f'%{search}%', limit)).fetchall()
    else:
        news_articles = conn.execute('''
            SELECT * FROM news_articles 
            ORDER BY scraped_at DESC 
            LIMIT ?
        ''', (limit,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(row) for row in news_articles])

@app.route('/api/products/<product_type>')
def api_products(product_type):
    """Get products API"""
    limit = request.args.get('limit', 20, type=int)
    
    conn = get_db_connection()
    
    if product_type == 'pesticides':
        table = 'pesticide_products'
    elif product_type == 'equipment':
        table = 'equipment_products'
    else:
        return jsonify({'error': 'Invalid product type'}), 400
    
    products_list = conn.execute(f'''
        SELECT * FROM {table} 
        ORDER BY scraped_at DESC 
        LIMIT ?
    ''', (limit,)).fetchall()
    
    conn.close()
    
    return jsonify([dict(row) for row in products_list])

@app.route('/api/analytics/crop-distribution')
def api_crop_distribution():
    """Get crop prediction distribution"""
    conn = get_db_connection()
    
    crop_dist = conn.execute('''
        SELECT predicted_crop as crop, COUNT(*) as count 
        FROM user_predictions 
        GROUP BY predicted_crop
        ORDER BY count DESC
    ''').fetchall()
    
    conn.close()
    
    return jsonify([dict(row) for row in crop_dist])

@app.route('/api/analytics/nutrient-stats')
def api_nutrient_stats():
    """Get nutrient statistics by crop"""
    conn = get_db_connection()
    
    stats = conn.execute('''
        SELECT label as crop,
               AVG(N) as avg_n, 
               AVG(P) as avg_p, 
               AVG(K) as avg_k,
               AVG(temperature) as avg_temp,
               AVG(humidity) as avg_humidity,
               AVG(ph) as avg_ph,
               AVG(rainfall) as avg_rainfall,
               COUNT(*) as sample_count
        FROM crops_data 
        GROUP BY label
        ORDER BY label
    ''').fetchall()
    
    conn.close()
    
    return jsonify([dict(row) for row in stats])

@app.route('/api/scrape/news', methods=['POST'])
def api_scrape_news():
    """Trigger news scraping"""
    try:
        count = scrape_farmer_news()
        return jsonify({
            'success': True,
            'message': f'Successfully scraped {count} news articles'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/scrape/products', methods=['POST'])
def api_scrape_products():
    """Trigger product scraping"""
    try:
        pesticide_count = scrape_pesticides()
        equipment_count = scrape_equipment()
        return jsonify({
            'success': True,
            'message': f'Successfully scraped {pesticide_count} pesticides and {equipment_count} equipment'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(e):
    return render_template('index.html'), 404

@app.errorhandler(500)
def server_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Ensure database exists
    if not Config.DATABASE_PATH.exists():
        print("Database not found. Please run 'python init_db.py' first.")
        sys.exit(1)
    
    # Ensure model exists
    if not Config.MODEL_PATH.exists():
        print("Model not found. Please run 'python ml_models/train_model.py' first.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("🌾 FARMER'S PORTAL - Starting Server")
    print("="*60)
    print(f"📊 Database: {Config.DATABASE_PATH}")
    print(f"🤖 Model: {Config.MODEL_PATH}")
    print(f"🌐 Server: http://localhost:5000")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
