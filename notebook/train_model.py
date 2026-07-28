import pandas as pd
import joblib
import os
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

print("Loading Dataset.csv...")
dataset_path = os.path.join(os.path.dirname(__file__), "Dataset.csv")
df = pd.read_csv(dataset_path)

X = df.drop("loan_status", axis=1)
y = df["loan_status"]

num_cols = [
    "person_age", "person_income", "person_emp_exp", "loan_amnt", 
    "loan_int_rate", "loan_percent_income", "cb_person_cred_hist_length", "credit_score"
]
cat_cols = [
    "person_gender", "person_education", "person_home_ownership", 
    "loan_intent", "previous_loan_defaults_on_file"
]

preprocessor = ColumnTransformer(
    transformers=[
        ("num", StandardScaler(), num_cols),
        ("cat", OneHotEncoder(handle_unknown="ignore"), cat_cols)
    ]
)

pipeline = Pipeline(steps=[
    ("preprocessor", preprocessor),
    ("classifier", RandomForestClassifier(n_estimators=100, random_state=42))
])

print("Training Random Forest Model...")
pipeline.fit(X, y)

model_path = os.path.join(os.path.dirname(__file__), "loan_risk_model_random_forest.pkl")
joblib.dump(pipeline, model_path)
print(f"Model successfully trained and saved to: {model_path}")
