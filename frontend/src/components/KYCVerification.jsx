import React, { useState, useRef } from 'react';

export default function KYCVerification({ onApplyToAssessment }) {
    // Uploaded Files
    const [incomeFile, setIncomeFile] = useState(null);
    const [aadhaarFile, setAadhaarFile] = useState(null);
    const [panFile, setPanFile] = useState(null);

    // File input refs
    const incomeInputRef = useRef(null);
    const aadhaarInputRef = useRef(null);
    const panInputRef = useRef(null);

    // Drag and drop states
    const [dragOverIncome, setDragOverIncome] = useState(false);
    const [dragOverAadhaar, setDragOverAadhaar] = useState(false);
    const [dragOverPan, setDragOverPan] = useState(false);

    // State
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [verificationResult, setVerificationResult] = useState(null);
    const [errorMessage, setErrorMessage] = useState('');
    const [notification, setNotification] = useState('');

    const showNotice = (msg) => {
        setNotification(msg);
        setTimeout(() => setNotification(''), 4500);
    };

    const handleReset = () => {
        setIncomeFile(null);
        setAadhaarFile(null);
        setPanFile(null);
        setDragOverIncome(false);
        setDragOverAadhaar(false);
        setDragOverPan(false);
        setVerificationResult(null);
        setErrorMessage('');
        if (incomeInputRef.current) incomeInputRef.current.value = '';
        if (aadhaarInputRef.current) aadhaarInputRef.current.value = '';
        if (panInputRef.current) panInputRef.current.value = '';
    };

    // Drag and drop handlers
    const handleDragEnter = (e, setDrag) => {
        e.preventDefault();
        e.stopPropagation();
        setDrag(true);
    };

    const handleDragOver = (e, setDrag) => {
        e.preventDefault();
        e.stopPropagation();
        setDrag(true);
    };

    const handleDragLeave = (e, setDrag) => {
        e.preventDefault();
        e.stopPropagation();
        if (!e.currentTarget.contains(e.relatedTarget)) {
            setDrag(false);
        }
    };

    const handleDrop = (e, setFile, setDrag) => {
        e.preventDefault();
        e.stopPropagation();
        setDrag(false);
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            const file = e.dataTransfer.files[0];
            setFile(file);
        }
    };

    const handleVerify = async (e) => {
        if (e) e.preventDefault();
        setErrorMessage('');

        if (!incomeFile || !aadhaarFile || !panFile) {
            setErrorMessage('All 3 proofs are compulsory! Please upload Income Certificate, Aadhaar Card, and PAN Card (PDF or Image).');
            return;
        }

        setIsAnalyzing(true);
        try {
            const formData = new FormData();
            formData.append('income_certificate', incomeFile);
            formData.append('aadhaar_card', aadhaarFile);
            formData.append('pan_card', panFile);

            const response = await fetch('/api/verify-documents', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Verification request failed');
            }

            const data = await response.json();
            setVerificationResult(data);
        } catch (err) {
            console.error('KYC Verification Error:', err);
            setErrorMessage(err.message || 'Error occurred during verification.');
        } finally {
            setIsAnalyzing(false);
        }
    };

    const handleApplyToAssessment = () => {
        if (!verificationResult) return;
        if (onApplyToAssessment) {
            onApplyToAssessment(verificationResult.autofill_data);
        }
    };

    return (
        <div className="kyc-container">
            {/* Page Header */}
            <div className="header">
                <div className="header-title">
                    <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                        <div className="kyc-header-icon">
                            <i className="fa-solid fa-id-card-clip"></i>
                        </div>
                        <div>
                            <h1>KYC Proof Authenticity Engine</h1>
                            <p>Verify Income Certificate, Aadhaar Card & PAN Card for original validity vs forgery</p>
                        </div>
                    </div>
                </div>
                <div className="header-actions">
                    <button type="button" className="btn btn-secondary" onClick={handleReset}>
                        <i className="fa-solid fa-arrow-rotate-left"></i> Reset
                    </button>
                </div>
            </div>

            {/* Notification Toast */}
            {notification && (
                <div className="kyc-toast">
                    {notification}
                </div>
            )}

            {/* Error Message */}
            {errorMessage && (
                <div className="kyc-alert kyc-alert-error">
                    <i className="fa-solid fa-circle-exclamation"></i>
                    <span>{errorMessage}</span>
                </div>
            )}

            <form onSubmit={handleVerify}>
                {/* 3 Compulsory Upload Proof Dropzones */}
                <div 
                    className="glass-panel kyc-section-panel"
                    onDragOver={(e) => { e.preventDefault(); e.stopPropagation(); }}
                    onDrop={(e) => { e.preventDefault(); e.stopPropagation(); }}
                >
                    <div className="kyc-section-header">
                        <div className="kyc-header-icon" style={{ width: '38px', height: '38px', fontSize: '1.1rem' }}>
                            <i className="fa-solid fa-cloud-arrow-up"></i>
                        </div>
                        <div>
                            <h3>Upload Proofs</h3>
                        </div>
                    </div>

                    <div className="kyc-upload-grid">
                        {/* Proof 1: Income Certificate */}
                        <div 
                            className={`kyc-upload-card ${incomeFile ? 'has-file' : ''} ${dragOverIncome ? 'drag-active' : ''}`}
                            onDragEnter={(e) => handleDragEnter(e, setDragOverIncome)}
                            onDragOver={(e) => handleDragOver(e, setDragOverIncome)}
                            onDragLeave={(e) => handleDragLeave(e, setDragOverIncome)}
                            onDrop={(e) => handleDrop(e, setIncomeFile, setDragOverIncome)}
                        >
                            <div className="kyc-card-top">
                                <div className="kyc-card-icon" style={{ background: 'rgba(16, 185, 129, 0.15)', color: '#10b981' }}>
                                    <i className="fa-solid fa-file-invoice-dollar"></i>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <h4>Income Certificate</h4>
                                    <span className="compulsory-badge">Compulsory</span>
                                </div>
                            </div>

                            <input 
                                type="file" 
                                ref={incomeInputRef} 
                                style={{ display: 'none' }}
                                accept=".pdf,image/png,image/jpeg,image/jpg,image/webp"
                                onChange={(e) => setIncomeFile(e.target.files[0] || null)}
                            />

                            {!incomeFile ? (
                                <div 
                                    className={`kyc-dropzone ${dragOverIncome ? 'drag-active' : ''}`}
                                    onClick={() => incomeInputRef.current && incomeInputRef.current.click()}
                                >
                                    <i className="fa-solid fa-cloud-arrow-up"></i>
                                    <span className="drop-title">Click to upload or drag & drop</span>
                                    <span className="drop-sub">PDF, PNG, JPG (Max 10MB)</span>
                                </div>
                            ) : (
                                <div className="kyc-file-preview">
                                    <div className="file-info">
                                        <i className={`fa-solid ${incomeFile.name.endsWith('.pdf') ? 'fa-file-pdf text-danger' : 'fa-file-image text-accent'}`}></i>
                                        <div className="file-text">
                                            <span className="file-name">{incomeFile.name}</span>
                                            <span className="file-size">{(incomeFile.size / 1024).toFixed(1)} KB</span>
                                        </div>
                                    </div>
                                    <button 
                                        type="button" 
                                        className="btn-icon-remove"
                                        onClick={() => {
                                             setIncomeFile(null);
                                             if (incomeInputRef.current) incomeInputRef.current.value = '';
                                        }}
                                        title="Remove File"
                                    >
                                        <i className="fa-solid fa-xmark"></i>
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Proof 2: Aadhaar Card */}
                        <div 
                            className={`kyc-upload-card ${aadhaarFile ? 'has-file' : ''} ${dragOverAadhaar ? 'drag-active' : ''}`}
                            onDragEnter={(e) => handleDragEnter(e, setDragOverAadhaar)}
                            onDragOver={(e) => handleDragOver(e, setDragOverAadhaar)}
                            onDragLeave={(e) => handleDragLeave(e, setDragOverAadhaar)}
                            onDrop={(e) => handleDrop(e, setAadhaarFile, setDragOverAadhaar)}
                        >
                            <div className="kyc-card-top">
                                <div className="kyc-card-icon" style={{ background: 'rgba(99, 102, 241, 0.15)', color: '#818cf8' }}>
                                    <i className="fa-solid fa-address-card"></i>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <h4>Aadhaar Card</h4>
                                    <span className="compulsory-badge">Compulsory</span>
                                </div>
                            </div>

                            <input 
                                type="file" 
                                ref={aadhaarInputRef} 
                                style={{ display: 'none' }}
                                accept=".pdf,image/png,image/jpeg,image/jpg,image/webp"
                                onChange={(e) => setAadhaarFile(e.target.files[0] || null)}
                            />

                            {!aadhaarFile ? (
                                <div 
                                    className={`kyc-dropzone ${dragOverAadhaar ? 'drag-active' : ''}`}
                                    onClick={() => aadhaarInputRef.current && aadhaarInputRef.current.click()}
                                >
                                    <i className="fa-solid fa-cloud-arrow-up"></i>
                                    <span className="drop-title">Click to upload or drag & drop</span>
                                    <span className="drop-sub">PDF, PNG, JPG (Max 10MB)</span>
                                </div>
                            ) : (
                                <div className="kyc-file-preview">
                                    <div className="file-info">
                                        <i className={`fa-solid ${aadhaarFile.name.endsWith('.pdf') ? 'fa-file-pdf text-danger' : 'fa-file-image text-accent'}`}></i>
                                        <div className="file-text">
                                            <span className="file-name">{aadhaarFile.name}</span>
                                            <span className="file-size">{(aadhaarFile.size / 1024).toFixed(1)} KB</span>
                                        </div>
                                    </div>
                                    <button 
                                        type="button" 
                                        className="btn-icon-remove"
                                        onClick={() => {
                                             setAadhaarFile(null);
                                             if (aadhaarInputRef.current) aadhaarInputRef.current.value = '';
                                        }}
                                        title="Remove File"
                                    >
                                        <i className="fa-solid fa-xmark"></i>
                                    </button>
                                </div>
                            )}
                        </div>

                        {/* Proof 3: PAN Card */}
                        <div 
                            className={`kyc-upload-card ${panFile ? 'has-file' : ''} ${dragOverPan ? 'drag-active' : ''}`}
                            onDragEnter={(e) => handleDragEnter(e, setDragOverPan)}
                            onDragOver={(e) => handleDragOver(e, setDragOverPan)}
                            onDragLeave={(e) => handleDragLeave(e, setDragOverPan)}
                            onDrop={(e) => handleDrop(e, setPanFile, setDragOverPan)}
                        >
                            <div className="kyc-card-top">
                                <div className="kyc-card-icon" style={{ background: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24' }}>
                                    <i className="fa-solid fa-credit-card"></i>
                                </div>
                                <div style={{ display: 'flex', alignItems: 'center' }}>
                                    <h4>PAN Card</h4>
                                    <span className="compulsory-badge">Compulsory</span>
                                </div>
                            </div>

                            <input 
                                type="file" 
                                ref={panInputRef} 
                                style={{ display: 'none' }}
                                accept=".pdf,image/png,image/jpeg,image/jpg,image/webp"
                                onChange={(e) => setPanFile(e.target.files[0] || null)}
                            />

                            {!panFile ? (
                                <div 
                                    className={`kyc-dropzone ${dragOverPan ? 'drag-active' : ''}`}
                                    onClick={() => panInputRef.current && panInputRef.current.click()}
                                >
                                    <i className="fa-solid fa-cloud-arrow-up"></i>
                                    <span className="drop-title">Click to upload or drag & drop</span>
                                    <span className="drop-sub">PDF, PNG, JPG (Max 10MB)</span>
                                </div>
                            ) : (
                                <div className="kyc-file-preview">
                                    <div className="file-info">
                                        <i className={`fa-solid ${panFile.name.endsWith('.pdf') ? 'fa-file-pdf text-danger' : 'fa-file-image text-accent'}`}></i>
                                        <div className="file-text">
                                            <span className="file-name">{panFile.name}</span>
                                            <span className="file-size">{(panFile.size / 1024).toFixed(1)} KB</span>
                                        </div>
                                    </div>
                                    <button 
                                        type="button" 
                                        className="btn-icon-remove"
                                        onClick={() => {
                                             setPanFile(null);
                                             if (panInputRef.current) panInputRef.current.value = '';
                                        }}
                                        title="Remove File"
                                    >
                                        <i className="fa-solid fa-xmark"></i>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Action Button */}
                    <div className="kyc-submit-bar" style={{ marginTop: '24px', textAlign: 'center' }}>
                        <button 
                            type="submit" 
                            className="btn btn-primary kyc-action-btn"
                            disabled={isAnalyzing}
                        >
                            {isAnalyzing ? (
                                <>
                                    <span className="spinner-border" style={{ marginRight: '8px' }}></span>
                                    Executing OCR & Forensic Authenticity Analysis...
                                </>
                            ) : (
                                <>
                                    <i className="fa-solid fa-shield-halved" style={{ marginRight: '8px' }}></i>
                                    Verify & Authenticate 3 Proofs
                                </>
                            )}
                        </button>
                    </div>
                </div>
            </form>

            {/* 3. Verification Results Display */}
            {verificationResult && (
                <div className="kyc-results-section" style={{ marginTop: '30px' }}>
                    {/* Overall Score Banner */}
                    <div className={`glass-panel kyc-summary-banner status-${verificationResult.overall_status.toLowerCase()}`}>
                        <div className="kyc-summary-score">
                            <div className="score-circle">
                                <span className="score-num">{verificationResult.trust_score}</span>
                                <span className="score-label">/ 100</span>
                            </div>
                            <div className="score-text">
                                <h2>{verificationResult.status_label}</h2>
                                <p className="risk-adjustment-text">
                                    <i className="fa-solid fa-shield-virus"></i> {verificationResult.risk_adjustment}
                                </p>
                            </div>
                        </div>
                        <div className="kyc-summary-actions">
                            <button 
                                type="button" 
                                className="btn btn-primary"
                                onClick={handleApplyToAssessment}
                                style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                            >
                                <i className="fa-solid fa-circle-arrow-right"></i> Apply to Loan Assessment
                            </button>
                        </div>
                    </div>

                    {/* 3 Deep Dive Cards */}
                    <div className="kyc-deepdive-grid" style={{ marginTop: '20px' }}>
                        {/* PAN Result */}
                        <div className="glass-panel kyc-detail-card">
                            <div className="card-header-bar">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <i className="fa-solid fa-credit-card text-warning"></i>
                                    <h4>PAN Card Analysis</h4>
                                </div>
                                <span className={`status-pill pill-${verificationResult.pan_verification.verdict.toLowerCase()}`}>
                                    {verificationResult.pan_verification.badge_label} ({verificationResult.pan_verification.authenticity_score}%)
                                </span>
                            </div>

                            <div className="doc-meta-row">
                                <span className="doc-meta-label">ID Evaluated:</span>
                                <span className="doc-meta-val code-font">{verificationResult.pan_verification.identified_id || 'Not Found'}</span>
                            </div>

                            <ul className="checks-list">
                                {verificationResult.pan_verification.checks.map((c, i) => (
                                    <li key={i} className={`check-item status-${c.status.toLowerCase()}`}>
                                        <i className={`fa-solid ${c.status === 'PASS' ? 'fa-circle-check' : c.status === 'FAIL' ? 'fa-circle-xmark' : 'fa-triangle-exclamation'}`}></i>
                                        <div>
                                            <strong>{c.name}</strong>
                                            <p>{c.detail}</p>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Aadhaar Result */}
                        <div className="glass-panel kyc-detail-card">
                            <div className="card-header-bar">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <i className="fa-solid fa-address-card text-accent"></i>
                                    <h4>Aadhaar Card Analysis</h4>
                                </div>
                                <span className={`status-pill pill-${verificationResult.aadhaar_verification.verdict.toLowerCase()}`}>
                                    {verificationResult.aadhaar_verification.badge_label} ({verificationResult.aadhaar_verification.authenticity_score}%)
                                </span>
                            </div>

                            <div className="doc-meta-row">
                                <span className="doc-meta-label">UID / Masked:</span>
                                <span className="doc-meta-val code-font">{verificationResult.aadhaar_verification.identified_id || 'Not Found'}</span>
                            </div>

                            <ul className="checks-list">
                                {verificationResult.aadhaar_verification.checks.map((c, i) => (
                                    <li key={i} className={`check-item status-${c.status.toLowerCase()}`}>
                                        <i className={`fa-solid ${c.status === 'PASS' ? 'fa-circle-check' : c.status === 'FAIL' ? 'fa-circle-xmark' : 'fa-triangle-exclamation'}`}></i>
                                        <div>
                                            <strong>{c.name}</strong>
                                            <p>{c.detail}</p>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>

                        {/* Income Certificate Result */}
                        <div className="glass-panel kyc-detail-card">
                            <div className="card-header-bar">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <i className="fa-solid fa-file-invoice-dollar text-success"></i>
                                    <h4>Income Certificate</h4>
                                </div>
                                <span className={`status-pill pill-${verificationResult.income_verification.verdict.toLowerCase()}`}>
                                    {verificationResult.income_verification.badge_label} ({verificationResult.income_verification.authenticity_score}%)
                                </span>
                            </div>

                            <div className="doc-meta-row">
                                <span className="doc-meta-label">Certified Amount:</span>
                                <span className="doc-meta-val" style={{ color: '#10b981', fontWeight: '700' }}>
                                    ₹ {verificationResult.income_verification.certified_income ? verificationResult.income_verification.certified_income.toLocaleString('en-IN') : '0'}
                                </span>
                            </div>

                            <ul className="checks-list">
                                {verificationResult.income_verification.checks.map((c, i) => (
                                    <li key={i} className={`check-item status-${c.status.toLowerCase()}`}>
                                        <i className={`fa-solid ${c.status === 'PASS' ? 'fa-circle-check' : c.status === 'FAIL' ? 'fa-circle-xmark' : 'fa-triangle-exclamation'}`}></i>
                                        <div>
                                            <strong>{c.name}</strong>
                                            <p>{c.detail}</p>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        </div>
                    </div>

                    {/* Cross-Proof Multi-Factor Audit Table */}
                    <div className="glass-panel kyc-section-panel" style={{ marginTop: '20px' }}>
                        <h4 style={{ marginBottom: '14px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                            <i className="fa-solid fa-network-wired text-accent"></i>
                            Cross-Proof Consistency & Statutory Audit
                        </h4>
                        <div className="cross-checks-container">
                            {verificationResult.cross_checks.map((chk, idx) => (
                                <div key={idx} className="cross-check-item">
                                    <div className="cross-check-title">
                                        <i className={`fa-solid ${chk.status === 'PASS' ? 'fa-circle-check text-success' : chk.status === 'WARNING' ? 'fa-triangle-exclamation text-warning' : 'fa-circle-info text-secondary'}`}></i>
                                        <span>{chk.title}</span>
                                    </div>
                                    <div className="cross-check-detail">{chk.detail}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
