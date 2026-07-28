import React, { useState } from 'react';

export default function AssessmentLogs({ assessments = [], onClearLogs }) {
    const [searchQuery, setSearchQuery] = useState('');
    const [statusFilter, setStatusFilter] = useState('all');

    const handleClear = async () => {
        if (window.confirm('Are you sure you want to clear all database logs? This cannot be undone.')) {
            if (onClearLogs) {
                await onClearLogs();
            }
        }
    };

    // Filter logic
    const filtered = assessments.filter(item => {
        if (statusFilter !== 'all') {
            if (statusFilter === 'Approved' && item.decision !== 'Approved') return false;
            if (statusFilter === 'Rejected' && item.decision !== 'Rejected') return false;
        }

        if (searchQuery.trim()) {
            const query = searchQuery.toLowerCase();
            const matchIntent = (item.intent || '').toLowerCase().includes(query);
            const matchEdu = (item.education || '').toLowerCase().includes(query);
            return matchIntent || matchEdu;
        }

        return true;
    });

    // Sort descending by date
    const sorted = [...filtered].sort((a, b) => new Date(b.date) - new Date(a.date));

    return (
        <section id="logs" className="view-panel active">
            <div className="header">
                <div className="header-title">
                    <h1>Historical Assessments Log</h1>
                    <p>Search, filter, and review historical prediction records</p>
                </div>
                <button className="btn btn-secondary" id="btn-clear-logs" onClick={handleClear}>
                    <i className="fa-solid fa-trash-can"></i> Clear All Logs
                </button>
            </div>

            <div className="glass-panel" style={{ padding: '24px' }}>
                {/* Filter and Search controls */}
                <div style={{ display: 'flex', justifyContent: 'space-between', gap: '16px', marginBottom: '20px', flexWrap: 'wrap' }}>
                    <input 
                        type="text" 
                        id="log-search" 
                        placeholder="Search logs by Intent or Education..." 
                        style={{ width: '320px' }}
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                    />
                    
                    <div style={{ display: 'flex', gap: '12px' }}>
                        <select 
                            id="log-filter-status" 
                            style={{ width: '160px' }}
                            value={statusFilter}
                            onChange={(e) => setStatusFilter(e.target.value)}
                        >
                            <option value="all">All Statuses</option>
                            <option value="Approved">Approved</option>
                            <option value="Rejected">Rejected</option>
                        </select>
                    </div>
                </div>

                {/* Logs Table */}
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Date/Time</th>
                                <th>Demographics</th>
                                <th>Employment</th>
                                <th>Loan Amount</th>
                                <th>Intent</th>
                                <th>Credit Score</th>
                                <th>Risk Prob</th>
                                <th>Decision</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sorted.length === 0 ? (
                                <tr>
                                    <td colSpan="8" style={{ textAlign: 'center', color: 'var(--text-secondary)' }}>
                                        No assessment records found.
                                    </td>
                                </tr>
                            ) : (
                                sorted.map(item => {
                                    const dateStr = item.date ? new Date(item.date).toLocaleString(undefined, { 
                                        month: 'short', 
                                        day: 'numeric', 
                                        hour: '2-digit', 
                                        minute: '2-digit' 
                                    }) : 'N/A';

                                    let statusBadge = <span className="badge info">Conditional</span>;
                                    if (item.decision === 'Approved') {
                                        statusBadge = <span className="badge success">Approved</span>;
                                    } else if (item.decision === 'Rejected') {
                                        statusBadge = <span className="badge danger">Rejected</span>;
                                    }

                                    const riskColor = item.risk >= 50 ? 'text-danger' : (item.risk >= 30 ? 'text-warning' : 'text-success');

                                    return (
                                        <tr key={item.id || Math.random()}>
                                            <td>{dateStr}</td>
                                            <td>
                                                <div style={{ fontWeight: 500 }}>
                                                    {(item.gender || '').toUpperCase()}, {item.age}y
                                                </div>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                    {item.education} / {item.home}
                                                </div>
                                            </td>
                                            <td>
                                                <div>${Number(item.income).toLocaleString()}/yr</div>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                    {item.exp} yrs exp
                                                </div>
                                            </td>
                                            <td style={{ fontWeight: 600 }}>${Number(item.loan).toLocaleString()}</td>
                                            <td><span style={{ fontSize: '0.8125rem', fontWeight: 500 }}>{item.intent}</span></td>
                                            <td>
                                                <div style={{ fontWeight: 600 }}>{item.credit_score}</div>
                                                <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                                                    {item.cred_len}y cred hist
                                                </div>
                                            </td>
                                            <td className={`${riskColor} font-bold`}>{Number(item.risk).toFixed(1)}%</td>
                                            <td>{statusBadge}</td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>
        </section>
    );
}
