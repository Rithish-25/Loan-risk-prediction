import os
import joblib
import sklearn.compose._column_transformer as _c
from sklearn.impute import SimpleImputer

# Backward compatibility patch for unpickling ColumnTransformer across scikit-learn versions
if not hasattr(_c, '_RemainderColsList'):
    class _RemainderColsList(list):
        pass
    _c._RemainderColsList = _RemainderColsList

def patch_model_imputers(obj):
    if hasattr(obj, '__dict__'):
        if isinstance(obj, SimpleImputer):
            if getattr(obj, 'strategy', '') in ['most_frequent', 'constant']:
                obj._fill_dtype = object
            else:
                obj._fill_dtype = float
        for k, v in list(obj.__dict__.items()):
            patch_model_imputers(v)
    elif isinstance(obj, (list, tuple)):
        for item in obj:
            patch_model_imputers(item)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            patch_model_imputers(v)

RF_MODEL = None
XGB_MODEL = None

RF_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "notebook", "loan_risk_model_random_forest.pkl")
XGB_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "notebook", "loan_risk_model_xgboost.pkl")

def load_model():
    global RF_MODEL, XGB_MODEL
    if os.path.exists(XGB_MODEL_PATH):
        try:
            XGB_MODEL = joblib.load(XGB_MODEL_PATH)
            patch_model_imputers(XGB_MODEL)
            print("XGBoost ML Model loaded successfully.")
        except Exception as e:
            print(f"Error loading XGBoost model: {str(e)}")
            
    if os.path.exists(RF_MODEL_PATH):
        try:
            RF_MODEL = joblib.load(RF_MODEL_PATH)
            patch_model_imputers(RF_MODEL)
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

