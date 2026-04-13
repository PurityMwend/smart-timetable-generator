import { useState, useEffect } from 'react';
import api from '../services/api';
import './StudentInformation.css';

const StudentInformation = () => {
    const [activeTab, setActiveTab] = useState('schools');
    const [data, setData] = useState({
        schools: [],
        entries: []
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        fetchStudentData();
    }, []);

    const fetchStudentData = async () => {
        try {
            setLoading(true);
            setError(null);
            const [schoolsRes, entriesRes] = await Promise.all([
                api.get('/schools/'),
                api.get('/timetable-entries/')
            ]);

            setData({
                schools: schoolsRes.data || [],
                entries: entriesRes.data || []
            });
        } catch (error) {
            console.error('Error fetching student data:', error);
            console.error('Error response:', error.response);
            let errorMsg = 'Failed to load data. Please try refreshing the page.';

            if (error.response?.status === 403) {
                const detail = error.response.data?.detail;
                if (detail?.includes('Authentication credentials')) {
                    errorMsg = `❌ Not authenticated - ${detail}. Please log out and log back in.`;
                } else if (detail?.includes('permission')) {
                    errorMsg = `❌ Permission denied - ${detail}. Make sure you are logged in as a student.`;
                } else {
                    errorMsg = `❌ Access Denied (403) - ${detail || 'Check permissions'}`;
                }
            } else if (error.response?.status === 401) {
                errorMsg = `❌ Unauthorized (401) - Please log in first`;
            } else if (error.response?.data?.detail) {
                errorMsg = `❌ API Error: ${error.response.data.detail}`;
            } else if (error.message) {
                errorMsg = `❌ Error: ${error.message}`;
            }

            setError(errorMsg);
        } finally {
            setLoading(false);
        }
    };

    const tabs = [
        { key: 'schools', label: 'Schools & Departments' },
        { key: 'timetable', label: 'My Timetable' }
    ];

    if (loading) {
        return (
            <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
                <div className="spinner">Loading your course information...</div>
            </div>
        );
    }

    if (error) {
        return (
            <div className="container" style={{ padding: '2rem 1rem' }}>
                <div className="error-message">
                    <h2>⚠️ Error Loading Data</h2>
                    <p>{error}</p>
                    <button
                        onClick={fetchStudentData}
                        className="btn btn-primary"
                        style={{ marginTop: '1rem' }}
                    >
                        Try Again
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="student-info container">
            <div className="info-header">
                <h1>Course & Timetable Information</h1>
                <p>View your courses, class locations, departments, and schedule</p>
            </div>

            <div className="tabs">
                {tabs.map(tab => (
                    <button
                        key={tab.key}
                        className={`tab-button ${activeTab === tab.key ? 'active' : ''}`}
                        onClick={() => setActiveTab(tab.key)}
                    >
                        {tab.label}
                    </button>
                ))}
            </div>

            <div className="tab-content">
                {activeTab === 'schools' && <SchoolsList schools={data.schools} />}
                {activeTab === 'timetable' && <TimetableList entries={data.entries} />}
            </div>
        </div>
    );
};

const SchoolsList = ({ schools }) => (
    <div className="vital-info">
        <h2>Schools & Departments</h2>
        {schools.length === 0 ? (
            <p className="empty-message">No schools available yet</p>
        ) : (
            <div className="schools-container">
                {schools.map(school => (
                    <div key={school.id} className="school-card">
                        <div className="school-header">
                            <h3 className="school-name">{school.name}</h3>
                            <span className="school-code">{school.code}</span>
                        </div>
                        {school.description && (
                            <p className="school-description">{school.description}</p>
                        )}
                        <div className="departments-list">
                            <h4>Departments ({school.departments_count})</h4>
                            {school.departments && school.departments.length > 0 ? (
                                <ul>
                                    {school.departments.map(dept => (
                                        <li key={dept.id} className="department-item">
                                            <span className="dept-code">{dept.code}</span>
                                            <span className="dept-name">{dept.name}</span>
                                        </li>
                                    ))}
                                </ul>
                            ) : (
                                <p className="no-departments">No departments yet</p>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        )}
    </div>
);

const TimetableList = ({ entries }) => {
    const handleViewOnline = () => {
        // This can be extended to show the timetable in a modal or separate view
        console.log('View timetable online');
    };

    const handleDownloadPDF = () => {
        // Generate and download PDF
        if (entries.length === 0) {
            alert('No timetable data to download');
            return;
        }

        // Simple approach: generate HTML and convert to PDF
        const htmlContent = generateTimetableHTML(entries);
        const link = document.createElement('a');
        link.href = 'data:text/html;charset=utf-8,' + encodeURIComponent(htmlContent);
        link.download = 'timetable.html';
        link.click();
    };

    const handleDownloadExcel = () => {
        if (entries.length === 0) {
            alert('No timetable data to download');
            return;
        }

        // Create CSV format for Excel
        const csvContent = generateTimetableCSV(entries);
        const link = document.createElement('a');
        link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csvContent);
        link.download = 'timetable.csv';
        link.click();
    };

    return (
        <div className="vital-info">
            <div className="timetable-header">
                <h2>My Timetable</h2>
                <div className="timetable-actions">
                    <button onClick={handleViewOnline} className="btn btn-secondary">
                        👁️ View Online
                    </button>
                    <button onClick={handleDownloadPDF} className="btn btn-secondary">
                        📥 Download PDF
                    </button>
                    <button onClick={handleDownloadExcel} className="btn btn-secondary">
                        📊 Download Excel
                    </button>
                </div>
            </div>
            {entries.length === 0 ? (
                <p className="empty-message">No schedule available yet</p>
            ) : (
                <div className="timetable-view">
                    <table className="timetable-table">
                        <thead>
                            <tr>
                                <th>Course</th>
                                <th>Day & Time</th>
                                <th>Room</th>
                            </tr>
                        </thead>
                        <tbody>
                            {entries.map(entry => (
                                <tr key={entry.id}>
                                    <td>
                                        <strong>{entry.course_code}</strong>
                                        <br />
                                        <small>{entry.course_name}</small>
                                    </td>
                                    <td>
                                        <strong>{entry.day_display}</strong>
                                        <br />
                                        {entry.start_time} - {entry.end_time}
                                    </td>
                                    <td>{entry.room_name}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}
        </div>
    );
};

const generateTimetableHTML = (entries) => {
    let html = `<!DOCTYPE html>
<html>
<head>
    <title>My Timetable</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #1f4788; }
        table { width: 100%; border-collapse: collapse; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
        th { background-color: #1f4788; color: white; }
        tr:nth-child(even) { background-color: #f9f9f9; }
    </style>
</head>
<body>
    <h1>My Timetable</h1>
    <table>
        <thead>
            <tr>
                <th>Course</th>
                <th>Day & Time</th>
                <th>Room</th>
            </tr>
        </thead>
        <tbody>`;

    entries.forEach(entry => {
        html += `<tr>
            <td><strong>${entry.course_code}</strong><br><small>${entry.course_name}</small></td>
            <td><strong>${entry.day_display}</strong><br>${entry.start_time} - ${entry.end_time}</td>
            <td>${entry.room_name}</td>
        </tr>`;
    });

    html += `</tbody>
    </table>
</body>
</html>`;
    return html;
};

const generateTimetableCSV = (entries) => {
    let csv = 'Course Code,Course Name,Day,Start Time,End Time,Room\n';
    entries.forEach(entry => {
        csv += `"${entry.course_code}","${entry.course_name}","${entry.day_display}","${entry.start_time}","${entry.end_time}","${entry.room_name}"\n`;
    });
    return csv;
};

export default StudentInformation;
