import requests
import sqlite3
import os
import time

LIVE_URL = "https://loan-risk-prediction-z9jk.onrender.com/api/history"
DB_PATH = os.path.join(os.path.dirname(__file__), "loans.db")

def sync():
    print(f"Connecting to live server at {LIVE_URL}...")
    print("Note: If Render is waking up from sleep mode, this may take 20-40 seconds on first request...")
    
    max_retries = 3
    response = None
    
    for attempt in range(1, max_retries + 1):
        try:
            # 60s timeout to allow Render free tier to spin up from sleep
            response = requests.get(LIVE_URL, timeout=60)
            if response.status_code == 200:
                break
            else:
                print(f"Server returned status {response.status_code}. Retrying in 5s... (Attempt {attempt}/{max_retries})")
                time.sleep(5)
        except requests.exceptions.Timeout:
            print(f"Render server is still spinning up... (Attempt {attempt}/{max_retries})")
            time.sleep(3)
        except Exception as e:
            print(f"Connecting... (Attempt {attempt}/{max_retries})")
            time.sleep(3)
            
    if response is None or response.status_code != 200:
        print("Error: Could not connect to live Render server after retries.")
        return
    
    try:
        records = response.json()
        print(f"Retrieved {len(records)} records from live cloud server.")
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        for r in records:
            # Ensure defaults for any missing keys
            data = {
                "id": r.get("id"),
                "date": r.get("date"),
                "age": r.get("age"),
                "gender": r.get("gender"),
                "education": r.get("education"),
                "income": r.get("income"),
                "exp": r.get("exp"),
                "home": r.get("home"),
                "loan": r.get("loan"),
                "intent": r.get("intent"),
                "rate": r.get("rate"),
                "dti": r.get("dti"),
                "cred_len": r.get("cred_len"),
                "credit_score": r.get("credit_score"),
                "defaults": r.get("defaults"),
                "marital_status": r.get("marital_status", "Single"),
                "dependents": r.get("dependents", 0),
                "vehicle": r.get("vehicle", "No"),
                "bank_age": r.get("bank_age", 1),
                "savings": r.get("savings", 0.0),
                "risk": r.get("risk"),
                "decision": r.get("decision")
            }
            cursor.execute("""
                INSERT OR REPLACE INTO assessments (
                    id, date, age, gender, education, income, exp, home, 
                    loan, intent, rate, dti, cred_len, credit_score, defaults,
                    marital_status, dependents, vehicle, bank_age, savings,
                    risk, decision
                ) VALUES (
                    :id, :date, :age, :gender, :education, :income, :exp, :home,
                    :loan, :intent, :rate, :dti, :cred_len, :credit_score, :defaults,
                    :marital_status, :dependents, :vehicle, :bank_age, :savings,
                    :risk, :decision
                )
            """, data)
        
        conn.commit()
        conn.close()
        print("Success: Local loans.db updated with all live server records!")
    except Exception as e:
        print(f"Error updating database: {str(e)}")

if __name__ == "__main__":
    sync()

