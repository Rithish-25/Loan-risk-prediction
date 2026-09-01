import React from 'react';

export default function Dashboard({ assessments = [], onNavigateToLogs }) {
    const total = assessments.length;

    const approvalsCount = assessments.filter(x => x.risk < 30).length;
    const approvalRate = total > 0 ? ((approvalsCount / total) * 100).toFixed(0) + '%' : '0%';

    const highRisks = assessments.filter(x => x.risk >= 50).length;

    const avgCredit = total > 0 
        ? (assessments.reduce((sum, item) => sum + item.credit_score, 0) / total).toFixed(0) 
        : 'N/A';

    // Recent 5 rows
    const sorted = [...assessments].sort((a, b) => new Date(b.date) - new Date(a.date));
    const recent = sorted.slice(0, 5);

    // Intent counts breakdown
    const intentCounts = {};
    assessments.forEach(item => {
        if (item.intent) {
            intentCounts[item.intent] = (intentCounts[item.intent] || 0) + 1;
        }
    });

    return (
        <section id="dashboard" className="view-panel active">
            <div className="header">
                <div className="header-title">
                    <h1>Credit Risk Dashboard</h1>
                    <p>Real-time analytics and defaults oversight system</p>
                </div>
            </div>

            {/* KPI Widgets Grid */}
            <div className="stats-grid">
                <div className="glass-panel stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Total Applications</span>
                        <div className="stat-icon accent">
                            <i className="fa-solid fa-folder-open"></i>
                        </div>
                    </div>
                    <div className="stat-value">{total}</div>
                    <div className="stat-sub">Across all loan portfolios</div>
                </div>

                <div className="glass-panel stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Approval Recommend</span>
                        <div className="stat-icon success">
                            <i className="fa-solid fa-check-circle"></i>
                        </div>
                    </div>
                    <div className="stat-value">{approvalRate}</div>
                    <div className="stat-sub">Risk criteria met (&lt; 30% prob)</div>
                </div>

                <div className="glass-panel stat-card">
                    <div className="stat-header">
                        <span className="stat-title">High Risk Flagged</span>
                        <div className="stat-icon danger">
                            <i className="fa-solid fa-triangle-exclamation"></i>
                        </div>
                    </div>
                    <div className="stat-value">{highRisks}</div>
                    <div className="stat-sub">Default risk &gt; 50% flagged</div>
                </div>

                <div className="glass-panel stat-card">
                    <div className="stat-header">
                        <span className="stat-title">Avg Credit Score</span>
                        <div className="stat-icon warning">
                            <i className="fa-solid fa-gauge"></i>
                        </div>
                    </div>
                    <div className="stat-value">{avgCredit}</div>
                    <div className="stat-sub">Average of assessed applicants</div>
                </div>
            </div>

            {/* Detailed Widgets */}
            <div className="dashboard-details-grid">
                <div className="glass-panel details-card">
                    <div className="details-header">
                        <h2 className="details-title">Recent Assessed Applications</h2>
                        <button className="btn btn-secondary" onClick={onNavigateToLogs}>View All</button>
                    </div>
                    <div className="table-container">
                        <table>
                            <thead>
                                <tr>
                                    <th>Applicant</th>
                                    <th>Loan Details</th>
                                    <th>Income</th>
                                    <th style={{ textAlign: 'center' }}>Risk %</th>
                                    <th style={{ textAlign: 'right' }}>Status</th>
                                </tr>
                            </thead>
                            <tbody>
                                {recent.length === 0 ? (
                                    <tr>
                                        <td colSpan="5" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                                            No applications processed yet.
                                        </td>
                                    </tr>
                                ) : (
                                    recent.map(app => {
                                        const riskColor = app.risk >= 50 ? 'text-danger' : (app.risk >= 30 ? 'text-warning' : 'text-success');
                                        let statusBadge = <span className="badge info">Conditional</span>;
                                        if (app.decision === 'Approved') {
                                            statusBadge = <span className="badge success">Approved</span>;
                                        } else if (app.decision === 'Rejected') {
                                            statusBadge = <span className="badge danger">Rejected</span>;
                                        }

                                        return (
                                            <tr key={app.id || Math.random()}>
                                                <td>
                                                    <div style={{ fontWeight: 600 }}>Applicant ({app.age}y)</div>
                                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{app.education}</div>
                                                </td>
                                                <td>
                                                    <div style={{ fontWeight: 500 }}>${Number(app.loan).toLocaleString()}</div>
                                                    <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{app.intent}</div>
                                                </td>
                                                <td style={{ fontWeight: 500 }}>${Number(app.income).toLocaleString()}</td>
                                                <td style={{ textAlign: 'center' }} className={`${riskColor} font-bold`}>{app.risk.toFixed(1)}%</td>
                                                <td style={{ textAlign: 'right' }}>{statusBadge}</td>
                                            </tr>
                                        );
                                    })
                                )}
                            </tbody>
                        </table>
                    </div>
                </div>

                <div className="glass-panel details-card">
                    <div className="details-header">
                        <h2 className="details-title">Loan Intent Share</h2>
                    </div>
                    <div style={{ flexGrow: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: '14px' }}>
                        {Object.keys(intentCounts).length === 0 ? (
                            <div style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>No intents loaded yet.</div>
                        ) : (
                            Object.keys(intentCounts).map(intent => {
                                const count = intentCounts[intent];
                                const percent = ((count / total) * 100).toFixed(0);
                                return (
                                    <div key={intent}>
                                        <div className="flex-between" style={{ fontSize: '0.8125rem', marginBottom: '6px' }}>
                                            <span>{intent}</span>
                                            <span style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>
                                                {count} ({percent}%)
                                            </span>
                                        </div>
                                        <div style={{ height: '6px', background: 'rgba(255,255,255,0.05)', borderRadius: '999px', overflow: 'hidden' }}>
                                            <div style={{ width: `${percent}%`, height: '100%', background: 'var(--color-accent)', borderRadius: '999px' }}></div>
                                        </div>
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>
        </section>
    );
}
