import { Link } from 'react-router-dom';
import './Dashboard.css'

const stats = [
    { label: 'Courses', value: '—', icon: '📚' },
    { label: 'Lecturers', value: '—', icon: '👨‍🏫' },
    { label: 'Rooms', value: '—', icon: '🏛️' },
    { label: 'Entries', value: '—', icon: '📅' },
]

function Dashboard() {
    return (
        <div className="dashboard">
            {/* ---- Header ---- */}
            <header className="dashboard-header">
                <div className="container header-inner">
                    <div className="brand">
                        <span className="brand-icon">⏱️</span>
                        <h1 className="brand-title">Smart Timetable Generator</h1>
                    </div>
                    <p className="brand-subtitle">University Lecture Scheduling System</p>
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

                {/* Welcome card */}
                <section className="card welcome-card" id="welcome-section">
                    <h2>Welcome 👋</h2>
                    <p>
                        This system automatically generates conflict-free weekly lecture
                        schedules for your university. Upload your data via Excel templates,
                        run the scheduler, and fine-tune the result with drag-and-drop.
                    </p>
                    <div className="welcome-actions">
                        <Link to="/data" className="btn btn-primary">Manage Data</Link>
                        <Link to="/generate" className="btn btn-secondary">Generate Timetable</Link>
                    </div>
                </section>

                {/* Quick-start steps */}
                <section className="steps-grid" id="steps-section">
                    {[
                        { step: 1, title: 'Upload Data', desc: 'Import courses, lecturers, rooms & time-slots from Excel templates.', link: '/data' },
                        { step: 2, title: 'Generate', desc: 'Run the constraint-satisfaction algorithm to create a conflict-free draft.', link: '/generate' },
                        { step: 3, title: 'Adjust & Publish', desc: 'Drag-and-drop to fine-tune, then publish the final timetable.', link: '/view' },
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
