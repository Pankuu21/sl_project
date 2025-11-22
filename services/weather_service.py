"""
Weather Service - OpenWeatherMap API Integration
"""

import requests
from datetime import datetime
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.resolve()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from config import Config
    API_KEY = Config.OPENWEATHER_API_KEY
    BASE_URL = Config.OPENWEATHER_BASE_URL
except:
    API_KEY = ""
    BASE_URL = "https://api.openweathermap.org/data/2.5"

def get_current_weather(city):
    """
    Get current weather for a city
    Returns: dict with weather data or error
    """
    try:
        url = f"{BASE_URL}/weather"
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric"  # Celsius
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        return {
            "success": True,
            "city": data["name"],
            "country": data["sys"]["country"],
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "temp_min": round(data["main"]["temp_min"], 1),
            "temp_max": round(data["main"]["temp_max"], 1),
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "description": data["weather"][0]["description"].title(),
            "icon": data["weather"][0]["icon"],
            "wind_speed": data["wind"]["speed"],
            "visibility": data.get("visibility", 0) / 1000,  # Convert to km
            "sunrise": datetime.fromtimestamp(data["sys"]["sunrise"]).strftime("%I:%M %p"),
            "sunset": datetime.fromtimestamp(data["sys"]["sunset"]).strftime("%I:%M %p"),
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": "City not found"}
        return {"success": False, "error": f"API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_forecast(city, days=7):
    """
    Get weather forecast for next N days
    Returns: dict with forecast data or error
    """
    try:
        url = f"{BASE_URL}/forecast"
        params = {
            "q": city,
            "appid": API_KEY,
            "units": "metric",
            "cnt": days * 8  # 8 readings per day (3-hour intervals)
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Group by day
        daily_forecast = {}
        for item in data["list"]:
            date = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            day_name = datetime.fromtimestamp(item["dt"]).strftime("%A")
            
            if date not in daily_forecast:
                daily_forecast[date] = {
                    "date": date,
                    "day": day_name,
                    "temps": [],
                    "humidity": [],
                    "rainfall": 0,
                    "description": item["weather"][0]["description"].title(),
                    "icon": item["weather"][0]["icon"]
                }
            
            daily_forecast[date]["temps"].append(item["main"]["temp"])
            daily_forecast[date]["humidity"].append(item["main"]["humidity"])
            
            # Accumulate rainfall
            if "rain" in item:
                daily_forecast[date]["rainfall"] += item["rain"].get("3h", 0)
        
        # Calculate averages
        forecast_list = []
        for date, day_data in list(daily_forecast.items())[:days]:
            forecast_list.append({
                "date": date,
                "day": day_data["day"],
                "temp_avg": round(sum(day_data["temps"]) / len(day_data["temps"]), 1),
                "temp_min": round(min(day_data["temps"]), 1),
                "temp_max": round(max(day_data["temps"]), 1),
                "humidity_avg": round(sum(day_data["humidity"]) / len(day_data["humidity"])),
                "rainfall": round(day_data["rainfall"], 1),
                "description": day_data["description"],
                "icon": day_data["icon"]
            })
        
        return {
            "success": True,
            "city": data["city"]["name"],
            "country": data["city"]["country"],
            "forecast": forecast_list
        }
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return {"success": False, "error": "City not found"}
        return {"success": False, "error": f"API error: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_weather_alerts(current_weather, forecast):
    """
    Generate farming alerts based on weather data
    """
    alerts = []
    
    if not current_weather.get("success") or not forecast.get("success"):
        return alerts
    
    # Temperature alerts
    temp = current_weather["temperature"]
    if temp > 35:
        alerts.append({
            "type": "warning",
            "icon": "fa-temperature-high",
            "title": "High Temperature Alert",
            "message": f"Temperature is {temp}°C. Ensure adequate irrigation for crops."
        })
    elif temp < 10:
        alerts.append({
            "type": "danger",
            "icon": "fa-snowflake",
            "title": "Cold Weather Alert",
            "message": f"Temperature is {temp}°C. Protect sensitive crops from frost."
        })
    
    # Humidity alerts
    humidity = current_weather["humidity"]
    if humidity > 80:
        alerts.append({
            "type": "warning",
            "icon": "fa-tint",
            "title": "High Humidity",
            "message": "Risk of fungal diseases. Monitor crops closely."
        })
    elif humidity < 30:
        alerts.append({
            "type": "info",
            "icon": "fa-wind",
            "title": "Low Humidity",
            "message": "Dry conditions. Increase irrigation frequency."
        })
    
    # Rainfall alerts
    total_rainfall = sum([day["rainfall"] for day in forecast["forecast"]])
    if total_rainfall > 50:
        alerts.append({
            "type": "info",
            "icon": "fa-cloud-rain",
            "title": "Heavy Rainfall Expected",
            "message": f"Expected rainfall: {round(total_rainfall, 1)}mm in next 7 days. Plan drainage."
        })
    elif total_rainfall < 5:
        alerts.append({
            "type": "warning",
            "icon": "fa-sun",
            "title": "Dry Week Ahead",
            "message": "Minimal rainfall expected. Ensure adequate irrigation."
        })
    
    return alerts

if __name__ == "__main__":
    # Test
    city = input("Enter city name: ").strip() or "Mumbai"
    
    print("\n🌤️  CURRENT WEATHER")
    print("="*50)
    current = get_current_weather(city)
    if current["success"]:
        print(f"City: {current['city']}, {current['country']}")
        print(f"Temperature: {current['temperature']}°C (Feels like {current['feels_like']}°C)")
        print(f"Condition: {current['description']}")
        print(f"Humidity: {current['humidity']}%")
    else:
        print(f"Error: {current['error']}")
    
    print("\n📅 7-DAY FORECAST")
    print("="*50)
    forecast = get_forecast(city, days=7)
    if forecast["success"]:
        for day in forecast["forecast"]:
            print(f"{day['day']:10} {day['date']:12} | {day['temp_min']}°C - {day['temp_max']}°C | {day['description']}")
    else:
        print(f"Error: {forecast['error']}")
