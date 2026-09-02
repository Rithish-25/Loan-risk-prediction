import React, { useState } from 'react';

export default function NewAssessment({ onAssessmentAdded }) {
    const [formData, setFormData] = useState({
        person_age: '',
        person_gender: '',
        person_education: '',
        person_home_ownership: '',
        person_income: '',
        person_emp_exp: '',
        credit_score: '',
        cb_person_cred_hist_length: '',
        previous_loan_defaults_on_file: '',
        loan_amnt: '',
        loan_intent: '',
        loan_int_rate: '',
        marital_status: '',
        number_of_dependents: '',
        vehicle_ownership: '',
        bank_account_age: '',
        savings_balance: ''
    });

    const [predictionResult, setPredictionResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);

    // Calculate live DTI string
    const incomeNum = parseFloat(formData.person_income) || 0;
    const loanNum = parseFloat(formData.loan_amnt) || 0;
    const dtiDisplay = (incomeNum > 0 && loanNum > 0) 
        ? ((loanNum / incomeNum) * 100).toFixed(2) + '%' 
        : '';

    const handleChange = (e) => {
        const { id, value } = e.target;
        setFormData(prev => ({ ...prev, [id]: value }));
    };

    const handleReset = () => {
        setFormData({
            person_age: '',
            person_gender: '',
            person_education: '',
            person_home_ownership: '',
            person_income: '',
            person_emp_exp: '',
            credit_score: '',
            cb_person_cred_hist_length: '',
            previous_loan_defaults_on_file: '',
            loan_amnt: '',
            loan_intent: '',
            loan_int_rate: '',
            marital_status: '',
            number_of_dependents: '',
            vehicle_ownership: '',
            bank_account_age: '',
            savings_balance: ''
        });
        setPredictionResult(null);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        const age = parseInt(formData.person_age, 10);
        const exp = parseInt(formData.person_emp_exp, 10);
        const credLen = parseInt(formData.cb_person_cred_hist_length, 10);
        const income = parseFloat(formData.person_income);
        const loan = parseFloat(formData.loan_amnt);
        const creditScore = parseInt(formData.credit_score, 10);
        const rate = parseFloat(formData.loan_int_rate);
        const dependents = parseInt(formData.number_of_dependents, 10) || 0;
        const bankAge = parseInt(formData.bank_account_age, 10) || 0;
        const savings = parseFloat(formData.savings_balance) || 0;

        // Validation limits
        if (exp >= age) {
            alert("Employment experience years cannot exceed applicant age.");
            return;
        }
        if (credLen >= age) {
            alert("Credit history length cannot exceed applicant age.");
            return;
        }
        if (bankAge >= age) {
            alert("Bank account age cannot exceed applicant age.");
            return;
        }

        const payload = {
            person_age: age,
            person_gender: formData.person_gender,
            person_education: formData.person_education,
            person_income: income,
            person_emp_exp: exp,
            person_home_ownership: formData.person_home_ownership,
            loan_amnt: loan,
            loan_intent: formData.loan_intent,
            loan_int_rate: rate,
            loan_percent_income: loan / income,
            cb_person_cred_hist_length: credLen,
            credit_score: creditScore,
            previous_loan_defaults_on_file: formData.previous_loan_defaults_on_file,
            marital_status: formData.marital_status || 'Single',
            number_of_dependents: dependents,
            vehicle_ownership: formData.vehicle_ownership || 'No',
            bank_account_age: bankAge,
            savings_balance: savings
        };

        setIsLoading(true);
        try {
            const response = await fetch('/api/predict', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                let errorMsg = 'Server encountered an issue.';
                if (errData.detail) {
                    if (Array.isArray(errData.detail)) {
                        errorMsg = errData.detail.map(d => `${d.loc ? d.loc[d.loc.length - 1] + ': ' : ''}${d.msg}`).join(', ');
                    } else if (typeof errData.detail === 'string') {
                        errorMsg = errData.detail;
                    } else {
                        errorMsg = JSON.stringify(errData.detail);
                    }
                }
                alert('Prediction Error: ' + errorMsg);
                setIsLoading(false);
                return;
            }

            const result = await response.json();
            setPredictionResult(result);
            setIsLoading(false);

            if (onAssessmentAdded) {
                await onAssessmentAdded();
            }

        } catch (err) {
            console.error(err);
            alert('Network error connecting to FastAPI credit evaluation server.');
            setIsLoading(false);
        }
    };

    // Calculate gauge parameters
    const riskProb = predictionResult ? predictionResult.risk : 0;
    const offset = 220 - ((riskProb / 100) * 110);

    let gaugeColor = 'var(--color-success)';
    let statusClass = 'safe';
    if (riskProb >= 50.0) {
        gaugeColor = 'var(--color-danger)';
        statusClass = 'danger';
    } else if (riskProb >= 30.0) {
        gaugeColor = 'var(--color-warning)';
        statusClass = 'warning';
    }

    return (
        <section id="assessment" className="view-panel active">
            <div className="header">
                <div className="header-title">
                    <h1>New Credit Risk Assessment</h1>
                    <p>Analyze applicant profile to calculate default risk & recommended terms</p>
                </div>
            </div>

            <div className="assessment-layout">
                {/* Input Form Panel */}
                <form id="assessment-form" className="glass-panel" style={{ padding: '28px' }} onSubmit={handleSubmit}>
                    
                    {/* Section 1: Personal Profile */}
                    <div className="form-section-title">1. Personal Profile</div>
                    <div className="form-grid">
                        <div className="form-group">
                            <label htmlFor="person_age">Age (Years)</label>
                            <input 
                                type="number" 
                                id="person_age" 
                                required 
                                min="18" 
                                max="100" 
                                placeholder="e.g. 28" 
                                value={formData.person_age}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="person_gender">Gender</label>
                            <select 
                                id="person_gender" 
                                required 
                                value={formData.person_gender} 
                                onChange={handleChange}
                            >
                                <option value="" disabled>Select</option>
                                <option value="male">Male</option>
                                <option value="female">Female</option>
                                <option value="other">Other</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="person_education">Education Level</label>
                            <select 
                                id="person_education" 
                                required 
                                value={formData.person_education} 
                                onChange={handleChange}
                            >
                                <option value="" disabled>Select</option>
                                <option value="High School">High School</option>
                                <option value="Associate">Associate Degree</option>
                                <option value="Bachelor">Bachelor Degree</option>
                                <option value="Master">Master Degree</option>
                                <option value="Doctorate">Doctorate</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="person_home_ownership">Home Ownership</label>
                            <select 
                                id="person_home_ownership" 
                                required 
                                value={formData.person_home_ownership} 
                                onChange={handleChange}
                            >
                                <option value="" disabled>Select</option>
                                <option value="RENT">Rent</option>
                                <option value="MORTGAGE">Mortgage</option>
                                <option value="OWN">Own</option>
                                <option value="OTHER">Other</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="marital_status">Marital Status</label>
                            <select 
                                id="marital_status" 
                                required 
                                value={formData.marital_status} 
                                onChange={handleChange}
                            >
                                <option value="" disabled>Select</option>
                                <option value="Single">Single</option>
                                <option value="Married">Married</option>
                                <option value="Divorced">Divorced</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="number_of_dependents">Number of Dependents</label>
                            <input 
                                type="number" 
                                id="number_of_dependents" 
                                required 
                                min="0" 
                                max="15" 
                                placeholder="e.g. 2" 
                                value={formData.number_of_dependents}
                                onChange={handleChange}
                            />
                        </div>
                    </div>

                    {/* Section 2: Finances & Credit */}
                    <div className="form-section-title">2. Financial & Credit History</div>
                    <div className="form-grid">
                        <div className="form-group">
                            <label htmlFor="person_income">Annual Income ($)</label>
                            <input 
                                type="number" 
                                id="person_income" 
                                required 
                                min="1000" 
                                max="10000000" 
                                placeholder="e.g. 60000"
                                value={formData.person_income}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="savings_balance">Savings Balance ($)</label>
                            <input 
                                type="number" 
                                id="savings_balance" 
                                required 
                                min="0" 
                                max="50000000" 
                                placeholder="e.g. 150000"
                                value={formData.savings_balance}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="person_emp_exp">Employment Experience (Years)</label>
                            <input 
                                type="number" 
                                id="person_emp_exp" 
                                required 
                                min="0" 
                                max="60" 
                                placeholder="e.g. 5"
                                value={formData.person_emp_exp}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="bank_account_age">Bank Account Age (Years)</label>
                            <input 
                                type="number" 
                                id="bank_account_age" 
                                required 
                                min="0" 
                                max="60" 
                                placeholder="e.g. 6"
                                value={formData.bank_account_age}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="credit_score">Credit Score (FICO)</label>
                            <input 
                                type="number" 
                                id="credit_score" 
                                required 
                                min="300" 
                                max="850" 
                                placeholder="e.g. 680"
                                value={formData.credit_score}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="cb_person_cred_hist_length">Credit History Length (Years)</label>
                            <input 
                                type="number" 
                                id="cb_person_cred_hist_length" 
                                required 
                                min="0" 
                                max="60" 
                                placeholder="e.g. 6"
                                value={formData.cb_person_cred_hist_length}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="vehicle_ownership">Vehicle Ownership</label>
                            <select 
                                id="vehicle_ownership" 
                                required 
                                value={formData.vehicle_ownership} 
                                onChange={handleChange}
                            >
                                <option value="" disabled>Select</option>
                                <option value="Yes">Yes (Vehicle Owned)</option>
                                <option value="No">No</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="previous_loan_defaults_on_file">Has Previous Loan Defaults?</label>
                            <select 
                                id="previous_loan_defaults_on_file" 
                                required 
                                value={formData.previous_loan_defaults_on_file} 
                                onChange={handleChange}
                            >
                                <option value="" disabled>Select</option>
                                <option value="No">No (Clean Record)</option>
                                <option value="Yes">Yes (Prior Default)</option>
                            </select>
                        </div>
                    </div>

                    {/* Section 3: Loan Proposal */}
                    <div className="form-section-title">3. Loan Proposal</div>
                    <div className="form-grid">
                        <div className="form-group">
                            <label htmlFor="loan_amnt">Requested Loan Amount ($)</label>
                            <input 
                                type="number" 
                                id="loan_amnt" 
                                required 
                                min="500" 
                                max="1000000" 
                                placeholder="e.g. 15000"
                                value={formData.loan_amnt}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="loan_intent">Loan Purpose</label>
                            <select 
                                id="loan_intent" 
                                required 
                                value={formData.loan_intent} 
                                onChange={handleChange}
                            >
                                <option value="" disabled>Select</option>
                                <option value="PERSONAL">Personal</option>
                                <option value="EDUCATION">Education</option>
                                <option value="MEDICAL">Medical</option>
                                <option value="VENTURE">Venture / Business</option>
                                <option value="HOMEIMPROVEMENT">Home Improvement</option>
                                <option value="DEBTCONSOLIDATION">Debt Consolidation</option>
                            </select>
                        </div>
                        <div className="form-group">
                            <label htmlFor="loan_int_rate">Interest Rate (%)</label>
                            <input 
                                type="number" 
                                id="loan_int_rate" 
                                step="0.01" 
                                required 
                                min="1" 
                                max="40" 
                                placeholder="e.g. 10.5"
                                value={formData.loan_int_rate}
                                onChange={handleChange}
                            />
                        </div>
                        <div className="form-group">
                            <label htmlFor="loan_percent_income">Debt-to-Income Ratio (%)</label>
                            <input 
                                type="text" 
                                id="loan_percent_income" 
                                readOnly 
                                placeholder="Auto-calculated" 
                                style={{ opacity: 0.7 }}
                                value={dtiDisplay}
                            />
                        </div>
                    </div>

                    <div style={{ display: 'flex', gap: '16px', marginTop: '8px' }}>
                        <button type="submit" className="btn" style={{ flexGrow: 1 }} disabled={isLoading}>
                            <i className="fa-solid fa-bolt"></i> {isLoading ? 'Analyzing...' : 'Run Risk Analysis'}
                        </button>
                        <button type="button" className="btn btn-secondary" id="btn-reset" onClick={handleReset}>
                            Reset
                        </button>
                    </div>
                </form>

                {/* Real-Time Evaluation Result Box */}
                <div className="glass-panel results-card">
                    <div className="details-header" style={{ width: '100%', borderBottom: '1px solid rgba(255, 255, 255, 0.05)', paddingBottom: '12px' }}>
                        <h2 className="details-title">Analysis Result</h2>
                    </div>

                    {!predictionResult ? (
                        <div id="results-placeholder" className="results-placeholder">
                            <i className="fa-solid fa-chart-line"></i>
                            <p>Complete the assessment form and trigger analysis to review predictive flags.</p>
                        </div>
                    ) : (
                        <div id="results-active" className="results-active">
                            {/* Arc Gauge */}
                            <div className="gauge-container">
                                <svg className="gauge-svg" viewBox="0 0 100 60">
                                    <path className="gauge-track" d="M15 50 A 35 35 0 0 1 85 50"></path>
                                    <path 
                                        id="gauge-fill" 
                                        className="gauge-fill" 
                                        d="M15 50 A 35 35 0 0 1 85 50"
                                        style={{ strokeDashoffset: offset, stroke: gaugeColor }}
                                    ></path>
                                </svg>
                                <div className="gauge-text">
                                    <div className="gauge-val" id="res-prob" style={{ color: gaugeColor }}>
                                        {predictionResult.risk.toFixed(1)}%
                                    </div>
                                    <div className="gauge-lbl">Probable Risk</div>
                                </div>
                            </div>

                            <span className={`result-badge ${statusClass}`} id="res-badge">
                                {predictionResult.decision}
                            </span>

                            {/* Recommendation Panel */}
                            <div className="analysis-panel">
                                <div className="analysis-title">
                                    <i className="fa-solid fa-coins"></i> Loan Recommendation
                                </div>
                                <div className="analysis-row">
                                    <span>Recommended Cap:</span>
                                    <span className="analysis-val" id="rec-cap">
                                        ${predictionResult.recommended_cap.toLocaleString()}
                                    </span>
                                </div>
                                <div className="analysis-row">
                                    <span>Affordable EMI:</span>
                                    <span className="analysis-val text-success" id="rec-emi">
                                        ${predictionResult.affordable_emi.toLocaleString()}/mo
                                    </span>
                                </div>
                                <div className="analysis-row">
                                    <span>Approval Decision:</span>
                                    <span className="analysis-val" id="rec-decision">
                                        {predictionResult.decision === 'Approved' && <span className="text-success">Approved (Low Risk)</span>}
                                        {predictionResult.decision === 'Rejected' && <span className="text-danger">Declined (High Risk)</span>}
                                        {predictionResult.decision !== 'Approved' && predictionResult.decision !== 'Rejected' && <span className="text-warning">Review Needed (Medium Risk)</span>}
                                    </span>
                                </div>
                            </div>

                            {/* Risk Drivers */}
                            <div className="analysis-panel" style={{ marginBottom: 0 }}>
                                <div className="analysis-title">
                                    <i className="fa-solid fa-circle-info"></i> Highlighted Risk Drivers
                                </div>
                                <div className="factor-list" id="res-drivers">
                                    {predictionResult.drivers.length === 0 ? (
                                        <div className="factor-item">
                                            <i className="fa-solid fa-circle-check text-success"></i> No critical triggers recorded.
                                        </div>
                                    ) : (
                                        predictionResult.drivers.map((item, index) => (
                                            <div key={index} className={`factor-item ${item.positive ? 'positive' : 'negative'}`}>
                                                <i className={`fa-solid ${item.positive ? 'fa-circle-check' : 'fa-circle-exclamation'}`}></i>
                                                <span>{item.text}</span>
                                            </div>
                                        ))
                                    )}
                                </div>
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </section>
    );
}
