import os
import joblib

MODEL = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "notebook", "loan_risk_model_random_forest.pkl")

def load_model():
    global MODEL
    if not os.path.exists(MODEL_PATH):
        raise RuntimeError(f"Trained model not found at {MODEL_PATH}")
    
    try:
        MODEL = joblib.load(MODEL_PATH)
        print("Scikit-Learn ML Model loaded successfully.")
    except Exception as e:
        print(f"Error loading pickle model: {str(e)}")
        raise e

def get_model():
    return MODEL
