import React, { useState, useEffect, useCallback } from 'react';
import Dashboard from './components/Dashboard';
import NewAssessment from './components/NewAssessment';
import AssessmentLogs from './components/AssessmentLogs';

export default function App() {
    const [activeTab, setActiveTab] = useState('dashboard');
    const [assessments, setAssessments] = useState([]);

    const fetchLogs = useCallback(async () => {
        try {
            const response = await fetch('/api/history');
            if (response.ok) {
                const data = await response.json();
                setAssessments(data);
            } else {
                console.error('Failed to fetch historical logs from server');
            }
        } catch (err) {
            console.error('Network error loading history:', err);
        }
    }, []);

    useEffect(() => {
        fetchLogs();
    }, [fetchLogs]);

    const handleClearLogs = async () => {
        try {
            const response = await fetch('/api/history', { method: 'DELETE' });
            if (response.ok) {
                setAssessments([]);
            } else {
                alert('Error clearing historical logs on backend.');
            }
        } catch (err) {
            console.error(err);
            alert('Network error connecting to API.');
        }
    };

    return (
        <div className="app-container">
            {/* Sidebar Navigation */}
            <aside className="sidebar">
                <div className="sidebar-logo">
                    <i className="fa-solid fa-shield-halved"></i>
                    <span>CreditGuard AI</span>
                </div>
                <ul className="sidebar-menu">
                    <li>
                        <a 
                            className={`menu-item ${activeTab === 'dashboard' ? 'active' : ''}`}
                            onClick={() => {
                                setActiveTab('dashboard');
                                fetchLogs();
                            }}
                        >
                            <i className="fa-solid fa-chart-pie"></i>
                            <span>Dashboard</span>
                        </a>
                    </li>
                    <li>
                        <a 
                            className={`menu-item ${activeTab === 'assessment' ? 'active' : ''}`}
                            onClick={() => setActiveTab('assessment')}
                        >
                            <i className="fa-solid fa-clipboard-check"></i>
                            <span>New Assessment</span>
                        </a>
                    </li>
                    <li>
                        <a 
                            className={`menu-item ${activeTab === 'logs' ? 'active' : ''}`}
                            onClick={() => {
                                setActiveTab('logs');
                                fetchLogs();
                            }}
                        >
                            <i className="fa-solid fa-list-ul"></i>
                            <span>Assessment Logs</span>
                        </a>
                    </li>
                </ul>
                <div className="sidebar-footer">
                    <div className="user-avatar">RA</div>
                    <div className="user-info">
                        <span className="user-name">Risk Analyst</span>
                        <span className="user-role">Risk Operations</span>
                    </div>
                </div>
            </aside>

            {/* Main Workspace - Feature Components */}
            <main className="main-content">
                {activeTab === 'dashboard' && (
                    <Dashboard 
                        assessments={assessments} 
                        onNavigateToLogs={() => {
                            setActiveTab('logs');
                            fetchLogs();
                        }}
                    />
                )}

                {activeTab === 'assessment' && (
                    <NewAssessment 
                        onAssessmentAdded={fetchLogs}
                    />
                )}

                {activeTab === 'logs' && (
                    <AssessmentLogs 
                        assessments={assessments} 
                        onClearLogs={handleClearLogs}
                    />
                )}
            </main>
        </div>
    );
}
