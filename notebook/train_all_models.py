import os
import sys
import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

# Force UTF-8 stdout if needed
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("Starting training for all 5 Loan Risk ML Models...")

# 1. Load Dataset
dataset_path = os.path.join(os.path.dirname(__file__), "Dataset_XGBoost.csv")
if not os.path.exists(dataset_path):
    dataset_path = os.path.join(os.path.dirname(__file__), "Dataset.csv")

print(f"Using dataset: {os.path.basename(dataset_path)}")
df = pd.read_csv(dataset_path)

X = df.drop("loan_status", axis=1)
y = df["loan_status"]

# Define feature columns dynamically
num_cols = X.select_dtypes(include=["int64", "float64"]).columns.tolist()
cat_cols = X.select_dtypes(include=["object"]).columns.tolist()

print(f"Numerical Features ({len(num_cols)}): {num_cols}")
print(f"Categorical Features ({len(cat_cols)}): {cat_cols}")

# 2. Build Preprocessor Pipeline
preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
    ]
)

# 3. Define the 5 Models
models = {
    "random_forest": RandomForestClassifier(n_estimators=100, random_state=42),
    "xgboost": XGBClassifier(n_estimators=100, random_state=42, eval_metric="logloss"),
    "lightgbm": LGBMClassifier(n_estimators=100, random_state=42, verbose=-1),
    "logistic_regression": LogisticRegression(max_iter=1000, random_state=42),
    "gradient_boosting": GradientBoostingClassifier(n_estimators=100, random_state=42)
}

# 4. Train and Save Each Model
output_dir = os.path.dirname(__file__)

for model_name, classifier in models.items():
    print(f"\nTraining {model_name.replace('_', ' ').title()} Model...")
    
    pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", classifier)
    ])
    
    pipeline.fit(X, y)
    
    filename = f"loan_risk_model_{model_name}.pkl"
    file_path = os.path.join(output_dir, filename)
    joblib.dump(pipeline, file_path)
    
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"Saved: {filename} ({file_size_mb:.2f} MB)")

print("\nAll 5 Models Trained and Saved Successfully in .pkl format!")

