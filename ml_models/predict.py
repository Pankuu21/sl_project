import pickle
import numpy as np
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import Config

def load_model():
    """Load trained model and scaler"""
    try:
        with open(Config.MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        with open(Config.SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        return model, scaler
    except FileNotFoundError:
        print("Model not found. Please train the model first.")
        return None, None

def predict_crop(N, P, K, temperature, humidity, ph, rainfall):
    """
    Predict crop based on input parameters
    
    Args:
        N: Nitrogen content
        P: Phosphorus content
        K: Potassium content
        temperature: Temperature in Celsius
        humidity: Humidity percentage
        ph: pH value
        rainfall: Rainfall in mm
    
    Returns:
        dict: Prediction result with crop name and confidence
    """
    
    model, scaler = load_model()
    
    if model is None or scaler is None:
        return {
            'success': False,
            'error': 'Model not loaded. Please train the model first.'
        }
    
    try:
        # Prepare input
        input_data = np.array([[N, P, K, temperature, humidity, ph, rainfall]])
        
        # Scale input
        input_scaled = scaler.transform(input_data)
        
        # Predict
        prediction = model.predict(input_scaled)[0]
        
        # Get prediction probabilities
        probabilities = model.predict_proba(input_scaled)[0]
        confidence = max(probabilities) * 100
        
        # Get crop info from config
        crop_info = Config.CROP_INFO.get(prediction.lower(), {
            'image': 'https://images.unsplash.com/photo-1625246333195-78d9c38ad449',
            'season': 'N/A',
            'duration': 'N/A',
            'tips': 'No additional information available'
        })
        
        return {
            'success': True,
            'crop': prediction,
            'confidence': round(confidence, 2),
            'image': crop_info.get('image'),
            'season': crop_info.get('season'),
            'duration': crop_info.get('duration'),
            'tips': crop_info.get('tips')
        }
    
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

if __name__ == '__main__':
    # Test prediction
    result = predict_crop(90, 42, 43, 20.8, 82.0, 6.5, 202.9)
    print(result)
