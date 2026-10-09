import os
import sys
import joblib
import pandas as pd

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

print("📊 Comparing Predictions Across All 5 Trained ML Models...\n")

model_files = {
    "Random Forest": "loan_risk_model_random_forest.pkl",
    "XGBoost": "loan_risk_model_xgboost.pkl",
    "LightGBM": "loan_risk_model_lightgbm.pkl",
    "Logistic Regression": "loan_risk_model_logistic_regression.pkl",
    "Gradient Boosting": "loan_risk_model_gradient_boosting.pkl"
}

# Full 18-feature sample input
sample_input = pd.DataFrame([{
    "person_age": 28.0,
    "person_gender": "male",
    "person_education": "Bachelor",
    "person_income": 65000.0,
    "person_emp_exp": 4,
    "person_home_ownership": "RENT",
    "loan_amnt": 12000.0,
    "loan_intent": "PERSONAL",
    "loan_int_rate": 11.49,
    "loan_percent_income": 0.18,
    "cb_person_cred_hist_length": 5.0,
    "credit_score": 710,
    "previous_loan_defaults_on_file": "No",
    "marital_status": "Single",
    "number_of_dependents": 1,
    "vehicle_ownership": "Yes",
    "bank_account_age": 4,
    "savings_balance": 25000.0
}])

base_dir = os.path.dirname(__file__)

print("Sample Applicant Input:")
print(f"Income: ${sample_input['person_income'].iloc[0]:,.0f} | Loan: ${sample_input['loan_amnt'].iloc[0]:,.0f} | Credit Score: {sample_input['credit_score'].iloc[0]}\n")

for name, filename in model_files.items():
    file_path = os.path.join(base_dir, filename)
    if os.path.exists(file_path):
        model = joblib.load(file_path)
        X_trans = model.named_steps["preprocessor"].transform(sample_input)
        pred = model.named_steps["classifier"].predict(X_trans)[0]
        prob = model.named_steps["classifier"].predict_proba(X_trans)[0][1] * 100.0
        
        status = "REJECTED (High Risk)" if pred == 1 else "APPROVED (Safe)"
        print(f"[{name:19}] Prediction: {pred} | Risk Probability: {prob:6.2f}% -> {status}")
    else:
        print(f"[{name:19}] Model file not found.")