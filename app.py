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
    """Dynamic product search with sorting"""
    if request.method == 'POST':
        keyword = request.form.get('keyword', '').strip()
        if keyword:
            try:
                from scraping.multi_source_scraper import scrape_by_keyword
                count = scrape_by_keyword(keyword, max_per_source=15)
                flash(f'✅ Found {count} products for "{keyword}"', 'success')
            except Exception as e:
                flash(f'Error: {str(e)}', 'error')
        return redirect(url_for('search_products', keyword=keyword))
    
    # GET request - display results
    keyword = request.args.get('keyword', '').strip()
    sort_by = request.args.get('sort', 'newest')  # 'newest', 'low_to_high', 'high_to_low'
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
    
    # Get total count
    total = conn.execute(count_query, params).fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    # Add sorting logic
    if sort_by == 'low_to_high':
        # Sort by price ascending (extract numeric price)
        query += " ORDER BY CAST(REPLACE(REPLACE(price, '₹', ''), ',', '') AS INTEGER) ASC"
    elif sort_by == 'high_to_low':
        # Sort by price descending
        query += " ORDER BY CAST(REPLACE(REPLACE(price, '₹', ''), ',', '') AS INTEGER) DESC"
    else:
        # Default: newest first
        query += " ORDER BY scraped_at DESC"
    
    # Add pagination
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    
    products_list = conn.execute(query, params).fetchall()
    conn.close()
    
    return render_template(
        'search_products.html',
        products=products_list,
        keyword=keyword,
        sort_by=sort_by,
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

@app.route('/schemes')
def schemes():
    """Government schemes page"""
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    conn = get_db_connection()
    
    total = conn.execute("SELECT COUNT(*) FROM government_schemes").fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)
    
    schemes_list = conn.execute(
        "SELECT * FROM government_schemes ORDER BY scraped_at DESC LIMIT ? OFFSET ?",
        (per_page, (page - 1) * per_page)
    ).fetchall()
    
    conn.close()
    
    return render_template(
        'schemes.html',
        schemes=schemes_list,
        page=page,
        total_pages=total_pages
    )

@app.route('/api/scrape/schemes', methods=['POST'])
def scrape_schemes_api():
    """Trigger schemes scraping"""
    try:
        from scraping.schemes_scraper import scrape_government_schemes
        count = scrape_government_schemes()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/weather')
def weather():
    """Weather page"""
    city = request.args.get('city', 'Mumbai')
    
    from services.weather_service import get_current_weather, get_forecast, get_weather_alerts
    
    current = get_current_weather(city)
    forecast = get_forecast(city, days=7)
    alerts = get_weather_alerts(current, forecast)
    
    return render_template(
        'weather.html',
        current=current,
        forecast=forecast,
        alerts=alerts,
        city=city
    )

@app.route('/api/weather/<city>')
def weather_api(city):
    """Weather API endpoint"""
    from services.weather_service import get_current_weather, get_forecast
    
    current = get_current_weather(city)
    forecast = get_forecast(city, days=7)
    
    return jsonify({
        "current": current,
        "forecast": forecast
    })
@app.route('/prices')
def crop_prices():
    """Crop prices page"""
    from services.agmarknet_prices import get_crop_prices, CROPS, MANDIS
    
    crop = request.args.get('crop', 'Tomato')
    mandi = request.args.get('mandi', 'Delhi')
    days = request.args.get('days', 7, type=int)
    
    if crop in CROPS and mandi in MANDIS:
        prices = get_crop_prices(crop, mandi, days=days)
    else:
        prices = {"success": False, "error": "Invalid crop or mandi"}
    
    return render_template(
        'prices.html',
        prices=prices,
        crops=list(CROPS.keys()),
        mandis=list(MANDIS.keys()),
        selected_crop=crop,
        selected_mandi=mandi
    )

@app.route('/market-prices')
def market_prices():
    search = request.args.get('search', '').strip()
    category = request.args.get('category', '').strip()
    commodity = request.args.get('commodity', '').strip()
    variety = request.args.get('variety', '').strip()
    per_page = request.args.get('per_page', 100, type=int)
    page = request.args.get('page', 1, type=int)

    conn = get_db_connection()
    conds, params = [], []
    if search:
        conds.append("commodity LIKE ?")
        params.append('%' + search + '%')
    if category:
        conds.append("commodity_group = ?")
        params.append(category)
    if commodity:
        conds.append("commodity = ?")
        params.append(commodity)
    if variety:
        conds.append("variety = ?")
        params.append(variety)

    where = " WHERE " + " AND ".join(conds) if conds else ""
    total = conn.execute(f"SELECT COUNT(*) FROM agmarknet_prices{where}", params).fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)

    query = f"SELECT * FROM agmarknet_prices{where} ORDER BY date DESC, commodity ASC LIMIT ? OFFSET ?"
    results = conn.execute(query, params + [per_page, (page - 1) * per_page]).fetchall()

    categories = [r[0] for r in conn.execute("SELECT DISTINCT commodity_group FROM agmarknet_prices").fetchall()]
    commodities = [r[0] for r in conn.execute("SELECT DISTINCT commodity FROM agmarknet_prices ORDER BY commodity ASC").fetchall()]
    varieties = [r[0] for r in conn.execute("SELECT DISTINCT variety FROM agmarknet_prices ORDER BY variety ASC").fetchall()]
    conn.close()

    return render_template(
        'market_prices.html',
        prices=results,
        search=search,
        category=category,
        categories=categories,
        commodity=commodity,
        commodities=commodities,
        variety=variety,
        varieties=varieties,
        per_page=per_page,
        page=page,
        total_pages=total_pages
    )



@app.route('/api/scrape/prices', methods=['POST'])
def scrape_prices_api():
    try:
        from services.agmarknet_csv_scraper import scrape_agmarknet_prices
        count = scrape_agmarknet_prices()
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500





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
