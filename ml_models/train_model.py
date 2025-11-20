import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import pickle
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent))
from config import Config

def train_crop_model():
    """Train Random Forest model for crop recommendation"""
    
    print("="*60)
    print("CROP RECOMMENDATION MODEL TRAINING")
    print("="*60)
    
    # Load dataset
    print("\n1. Loading dataset...")
    if not Config.DATASET_PATH.exists():
        print(f"✗ Error: Dataset not found at {Config.DATASET_PATH}")
        print("  Please add Crop_recommendation.csv to project root")
        return
    
    df = pd.read_csv(Config.DATASET_PATH)
    print(f"✓ Dataset loaded: {df.shape[0]} rows, {df.shape[1]} columns")
    
    # Display dataset info
    print("\nDataset preview:")
    print(df.head())
    print("\nTarget distribution:")
    print(df['label'].value_counts())
    
    # Prepare features and target
    print("\n2. Preparing features and target...")
    X = df.drop('label', axis=1)
    y = df['label']
    
    feature_names = X.columns.tolist()
    print(f"✓ Features: {feature_names}")
    print(f"✓ Target classes: {y.nunique()}")
    
    # Split data
    print("\n3. Splitting data (80-20 train-test)...")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    print(f"✓ Training set: {X_train.shape[0]} samples")
    print(f"✓ Test set: {X_test.shape[0]} samples")
    
    # Feature scaling
    print("\n4. Scaling features...")
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    print("✓ Features scaled using StandardScaler")
    
    # Train Random Forest model
    print("\n5. Training Random Forest Classifier...")
    print("   (This may take a minute...)")
    
    rf_model = RandomForestClassifier(
        n_estimators=100,
        max_depth=15,
        min_samples_split=5,
        min_samples_leaf=2,
        random_state=42,
        n_jobs=-1
    )
    
    rf_model.fit(X_train_scaled, y_train)
    print("✓ Model training complete!")
    
    # Evaluate model
    print("\n6. Evaluating model performance...")
    
    # Training accuracy
    train_pred = rf_model.predict(X_train_scaled)
    train_accuracy = accuracy_score(y_train, train_pred)
    print(f"✓ Training Accuracy: {train_accuracy*100:.2f}%")
    
    # Test accuracy
    test_pred = rf_model.predict(X_test_scaled)
    test_accuracy = accuracy_score(y_test, test_pred)
    print(f"✓ Test Accuracy: {test_accuracy*100:.2f}%")
    
    # Feature importance
    print("\n7. Feature Importance:")
    feature_importance = pd.DataFrame({
        'feature': feature_names,
        'importance': rf_model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    for idx, row in feature_importance.iterrows():
        print(f"   {row['feature']:12s}: {row['importance']:.4f}")
    
    # Classification report
    print("\n8. Classification Report:")
    print(classification_report(y_test, test_pred))
    
    # Save model and scaler
    print("\n9. Saving model and scaler...")
    Config.MODEL_PATH.parent.mkdir(exist_ok=True)
    
    with open(Config.MODEL_PATH, 'wb') as f:
        pickle.dump(rf_model, f)
    print(f"✓ Model saved to {Config.MODEL_PATH}")
    
    with open(Config.SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    print(f"✓ Scaler saved to {Config.SCALER_PATH}")
    
    print("\n" + "="*60)
    print("MODEL TRAINING COMPLETE!")
    print("="*60)
    print(f"Final Test Accuracy: {test_accuracy*100:.2f}%")
    print("="*60)
    
    return rf_model, scaler

if __name__ == '__main__':
    train_crop_model()
