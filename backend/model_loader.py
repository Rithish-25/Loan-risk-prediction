import os
import joblib

RF_MODEL = None
XGB_MODEL = None

RF_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "notebook", "loan_risk_model_random_forest.pkl")
XGB_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "notebook", "loan_risk_model_xgboost.pkl")

def load_model():
    global RF_MODEL, XGB_MODEL
    if os.path.exists(XGB_MODEL_PATH):
        try:
            XGB_MODEL = joblib.load(XGB_MODEL_PATH)
            print("XGBoost ML Model loaded successfully.")
        except Exception as e:
            print(f"Error loading XGBoost model: {str(e)}")
            
    if os.path.exists(RF_MODEL_PATH):
        try:
            RF_MODEL = joblib.load(RF_MODEL_PATH)
            print("Random Forest ML Model loaded successfully.")
        except Exception as e:
            print(f"Error loading Random Forest model: {str(e)}")

def get_model():
    # Returns XGBoost model as primary for 2nd Review, falls back to RF if needed
    return XGB_MODEL if XGB_MODEL is not None else RF_MODEL

def get_xgb_model():
    return XGB_MODEL

def get_rf_model():
    return RF_MODEL

