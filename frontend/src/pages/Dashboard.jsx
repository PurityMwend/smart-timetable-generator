import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import './Dashboard.css'

function Dashboard() {
    const { isTimetabler, isLecturer, isStudent } = useAuth();
    const [stats, setStats] = useState([
        { label: 'Courses', value: '—', icon: '📚' },
        { label: 'Lecturers', value: '—', icon: '👨‍🏫' },
        { label: 'Rooms', value: '—', icon: '🏛️' },
        { label: 'Entries', value: '—', icon: '📅' },
    ]);

    useEffect(() => {
        fetchStats();
    }, []);

    const fetchStats = async () => {
        try {
            const [courses, lecturers, rooms, entries] = await Promise.all([
                api.get('/courses/'),
                api.get('/lecturers/'),
                api.get('/rooms/'),
                api.get('/timetable-entries/')
            ]);

            setStats([
                { label: 'Courses', value: courses.data.length || 0, icon: '📚' },
                { label: 'Lecturers', value: lecturers.data.length || 0, icon: '👨‍🏫' },
                { label: 'Rooms', value: rooms.data.length || 0, icon: '🏛️' },
                { label: 'Entries', value: entries.data.length || 0, icon: '📅' },
            ]);
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    };

    return (
        <div className="dashboard">
            {/* ---- Header ---- */}
            <header className="dashboard-header">
                <div className="container header-inner">
                    <div className="brand">
                        <span className="brand-icon">⏱️</span>
                        <h1 className="brand-title">Smart Timetable Generator</h1>
                    </div>
                    <p className="brand-subtitle">AI-Powered University Lecture Scheduling System</p>
                </div>
            </header>

            {/* ---- Main content ---- */}
            <main className="container dashboard-main">
                {/* Stats grid */}
                <section className="stats-grid" id="stats-section">
                    {stats.map((s) => (
                        <div className="card stat-card" key={s.label}>
                            <span className="stat-icon">{s.icon}</span>
                            <span className="stat-value">{s.value}</span>
                            <span className="stat-label">{s.label}</span>
                        </div>
                    ))}
                </section>

                {/* Welcome card - Timetabler only */}
                <section className="card welcome-card" id="welcome-section">
                    <h2>Welcome to AI-Powered Scheduling 👋</h2>
                    <p>
                        This intelligent system uses advanced AI algorithms to generate optimal, conflict-free weekly lecture
                        schedules for your university. Upload your constraints via PDF/Excel files,
                        let the AI learn from pre-trained models and your data, then generate efficient timetables automatically.
                    </p>
                    <div className="welcome-actions">
                        <Link to="/data" className="btn btn-primary">Data Manager</Link>
                        <Link to="/training-data" className="btn btn-secondary">Training Data</Link>
                        <Link to="/generate" className="btn btn-secondary">Generate Timetable</Link>
                        <Link to="/view" className="btn btn-secondary">View Timetable</Link>
                    </div>
                </section>

                {/* Quick-start steps */}
                <section className="steps-grid" id="steps-section">
                    {[
                        { step: 1, title: 'Manage Data', desc: 'Upload and manage courses, lecturers, rooms, and time slots.', link: '/data' },
                        { step: 2, title: 'Generate', desc: 'Run the AI algorithm to create an optimized conflict-free timetable.', link: '/generate' },
                        { step: 3, title: 'Publish', desc: 'Review, adjust, and publish the final timetable for students.', link: '/view' },
                    ].map((item) => (
                        <div className="card step-card" key={item.step}>
                            <span className="step-number">{item.step}</span>
                            <h3>{item.title}</h3>
                            <p>{item.desc}</p>
                            <Link to={item.link} className="btn btn-primary">Go</Link>
                        </div>
                    ))}
                </section>

            </main>
        </div>
    )
}

export default Dashboard
