import os
import sys
import joblib
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, confusion_matrix

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("📊 Evaluating all 5 Trained Loan Risk Models...\n")

# Load Dataset
dataset_path = os.path.join(os.path.dirname(__file__), "Dataset_XGBoost.csv")
if not os.path.exists(dataset_path):
    dataset_path = os.path.join(os.path.dirname(__file__), "Dataset.csv")

df = pd.read_csv(dataset_path)

X = df.drop("loan_status", axis=1)
y = df["loan_status"]

# Same 80:20 train-test split across all models
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

models_info = [
    ("Random Forest", "loan_risk_model_random_forest.pkl"),
    ("XGBoost", "loan_risk_model_xgboost.pkl"),
    ("LightGBM", "loan_risk_model_lightgbm.pkl"),
    ("Logistic Regression", "loan_risk_model_logistic_regression.pkl"),
    ("Gradient Boosting", "loan_risk_model_gradient_boosting.pkl"),
]

results = []

for model_name, filename in models_info:
    file_path = os.path.join(os.path.dirname(__file__), filename)
    if not os.path.exists(file_path):
        print(f"⚠️ Model file not found: {filename}")
        continue
        
    pipeline = joblib.load(file_path)
    
    # Transform test set and predict
    X_transformed = pipeline.named_steps["preprocessor"].transform(X_test)
    preds = pipeline.named_steps["classifier"].predict(X_transformed)
    
    acc = accuracy_score(y_test, preds) * 100
    prec = precision_score(y_test, preds) * 100
    rec = recall_score(y_test, preds) * 100
    f1 = f1_score(y_test, preds) * 100
    cm = confusion_matrix(y_test, preds)
    
    results.append({
        "Model": model_name,
        "Accuracy (%)": round(acc, 2),
        "Precision (%)": round(prec, 2),
        "Recall (%)": round(rec, 2),
        "F1 Score (%)": round(f1, 2)
    })
    
    print(f"==================== {model_name.upper()} ====================")
    print(f"Accuracy  : {acc:.2f}%")
    print(f"Precision : {prec:.2f}%")
    print(f"Recall    : {rec:.2f}%")
    print(f"F1 Score  : {f1:.2f}%")
    print("Confusion Matrix:")
    print(cm)
    print()

results_df = pd.DataFrame(results)
print("==================== FINAL COMPARISON TABLE ====================")
print(results_df.to_string(index=False))