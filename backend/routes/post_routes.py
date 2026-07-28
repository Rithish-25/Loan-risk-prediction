from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import pandas as pd
import random
import datetime
import database
import model_loader

router = APIRouter()

# Pydantic schema for validation
class PredictRequest(BaseModel):
    person_age: float = Field(..., ge=18, le=100)
    person_gender: str
    person_education: str
    person_income: float = Field(..., gt=0)
    person_emp_exp: int = Field(..., ge=0)
    person_home_ownership: str
    loan_amnt: float = Field(..., gt=0)
    loan_intent: str
    loan_int_rate: float = Field(..., gt=0)
    loan_percent_income: float = Field(..., ge=0, le=1)
    cb_person_cred_hist_length: float = Field(..., ge=0)
    credit_score: int = Field(..., ge=300, le=850)
    previous_loan_defaults_on_file: str

@router.post("/api/predict")
async def predict_loan_risk(req: PredictRequest):
    model = model_loader.get_model()
    if model is None:
        raise HTTPException(status_code=503, detail="Machine Learning Model is currently unavailable.")
    
    try:
        # 1. Transform raw request to Pandas DataFrame matching model features
        data_dict = {
            "person_age": [req.person_age],
            "person_gender": [req.person_gender],
            "person_education": [req.person_education],
            "person_income": [req.person_income],
            "person_emp_exp": [req.person_emp_exp],
            "person_home_ownership": [req.person_home_ownership],
            "loan_amnt": [req.loan_amnt],
            "loan_intent": [req.loan_intent],
            "loan_int_rate": [req.loan_int_rate],
            "loan_percent_income": [req.loan_percent_income],
            "cb_person_cred_hist_length": [req.cb_person_cred_hist_length],
            "credit_score": [req.credit_score],
            "previous_loan_defaults_on_file": [req.previous_loan_defaults_on_file]
        }
        df = pd.DataFrame(data_dict)
        
        # 2. Run Inference (preprocessing + classification)
        X_transformed = model.named_steps["preprocessor"].transform(df)
        probability = model.named_steps["classifier"].predict_proba(X_transformed)
        
        # Extracted probability of default (class 1)
        risk_prob = float(probability[0][1]) * 100.0
        
        # 3. Dynamic financial recommendations
        # Determine approval decision
        decision = "Approved"
        if risk_prob >= 50.0:
            decision = "Rejected"
        elif risk_prob >= 30.0:
            decision = "Conditional"
            
        # Determine loan capping factor based on applicant history & FICO
        cap_factor = 0.35
        if req.previous_loan_defaults_on_file == "Yes":
            cap_factor = 0.10
        elif req.credit_score < 560:
            cap_factor = 0.15
        elif req.credit_score < 650:
            cap_factor = 0.25
            
        recommended_cap = int(round(req.person_income * cap_factor))
        
        # Monthly affordable EMI (30% of monthly income)
        monthly_income = req.person_income / 12.0
        affordable_emi = int(round(monthly_income * 0.30))

        # 4. Generate unique ID & date
        tx_id = f"TX-{random.randint(1000, 9999)}"
        timestamp = datetime.datetime.utcnow().isoformat() + "Z"

        # 5. Extract specific risk drivers for frontend rendering
        drivers = []
        if req.previous_loan_defaults_on_file == "Yes":
            drivers.append({"text": "Prior defaults on record (+35%)", "positive": False})
        
        if req.credit_score < 560:
            drivers.append({"text": "Critical Credit score (<560) (+32%)", "positive": False})
        elif req.credit_score < 650:
            drivers.append({"text": "Subprime Credit score (<650) (+15%)", "positive": False})
        elif req.credit_score >= 720:
            drivers.append({"text": "Prime Credit profile (Excellent) (-12%)", "positive": True})

        dti_pct = req.loan_percent_income * 100.0
        if dti_pct > 45.0:
            drivers.append({"text": "Extreme Debt-to-Income (>45%) (+22%)", "positive": False})
        elif dti_pct > 25.0:
            drivers.append({"text": "Moderate Debt-to-Income (>25%) (+8%)", "positive": False})
        else:
            drivers.append({"text": "Low Debt-to-Income ratio (-5%)", "positive": True})

        if req.person_home_ownership == "RENT":
            drivers.append({"text": "Housing status Rented (+6%)", "positive": False})
        elif req.person_home_ownership == "OWN":
            drivers.append({"text": "Outright Home ownership (-4%)", "positive": True})

        if req.person_emp_exp < 2:
            drivers.append({"text": "Short tenure employment history (+5%)", "positive": False})
        
        if req.person_age < 23:
            drivers.append({"text": "Young borrower demographic risk (+3%)", "positive": False})

        if req.loan_int_rate > 15.0:
            drivers.append({"text": "Premium high-interest terms (>15%) (+8%)", "positive": False})

        # Save record to database
        db_record = {
            "id": tx_id,
            "date": timestamp,
            "age": int(req.person_age),
            "gender": req.person_gender,
            "education": req.person_education,
            "income": req.person_income,
            "exp": req.person_emp_exp,
            "home": req.person_home_ownership,
            "loan": req.loan_amnt,
            "intent": req.loan_intent,
            "rate": req.loan_int_rate,
            "dti": round(dti_pct, 2),
            "cred_len": int(req.cb_person_cred_hist_length),
            "credit_score": req.credit_score,
            "defaults": req.previous_loan_defaults_on_file,
            "risk": round(risk_prob, 2),
            "decision": "Approved" if decision == "Conditional" else decision
        }
        database.insert_assessment(db_record)

        return {
            "id": tx_id,
            "risk": round(risk_prob, 2),
            "decision": decision,
            "recommended_cap": recommended_cap,
            "affordable_emi": affordable_emi,
            "drivers": drivers
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Model execution error: {str(e)}")
