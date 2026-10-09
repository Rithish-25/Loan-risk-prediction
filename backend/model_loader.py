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

MODELS = {}

MODEL_FILES = {
    "random_forest": "loan_risk_model_random_forest.pkl",
    "xgboost": "loan_risk_model_xgboost.pkl",
    "lightgbm": "loan_risk_model_lightgbm.pkl",
    "logistic_regression": "loan_risk_model_logistic_regression.pkl",
    "gradient_boosting": "loan_risk_model_gradient_boosting.pkl",
}

def load_model():
    global MODELS
    notebook_dir = os.path.join(os.path.dirname(__file__), "..", "notebook")
    
    for key, filename in MODEL_FILES.items():
        file_path = os.path.join(notebook_dir, filename)
        if os.path.exists(file_path):
            try:
                loaded_m = joblib.load(file_path)
                patch_model_imputers(loaded_m)
                MODELS[key] = loaded_m
                print(f"Loaded ML Model: {key}")
            except Exception as e:
                print(f"Error loading model {key}: {str(e)}")

def get_model():
    # Returns XGBoost as primary default, or first available model
    if "xgboost" in MODELS:
        return MODELS["xgboost"]
    elif "random_forest" in MODELS:
        return MODELS["random_forest"]
    elif len(MODELS) > 0:
        return list(MODELS.values())[0]
    return None

def get_model_by_name(name: str):
    return MODELS.get(name.lower().replace(" ", "_"), get_model())

def get_all_models():
    return MODELS
