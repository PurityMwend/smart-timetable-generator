import { useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../services/api';
import './TimetableGenerator.css';

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const DAY_LABELS = { MON: 'Mon', TUE: 'Tue', WED: 'Wed', THU: 'Thu', FRI: 'Fri', SAT: 'Sat' };

const TimetableGenerator = () => {
    const [state, setState] = useState('idle');  // idle | generating | done | error
    const [message, setMessage] = useState('');
    const [entries, setEntries] = useState([]);
    const [timetableId, setTimetableId] = useState(null);
    const [exporting, setExporting] = useState(null); // 'excel' | 'pdf' | null

    // ------------------------------------------------------------------ generate
    const handleGenerate = async () => {
        setState('generating');
        setMessage('');
        setEntries([]);
        setTimetableId(null);

        try {
            const res = await api.post('/generate-timetable/');
            setState('done');
            setMessage(res.data.message);
            setEntries(res.data.entries || []);
            setTimetableId(res.data.timetable_id);
        } catch (err) {
            const errMsg = err.response?.data?.error || 'Generation failed. Please try again.';
            setState('error');
            setMessage(errMsg);
        }
    };

    // ------------------------------------------------------------------ export
    const handleExport = async (format) => {
        if (!timetableId) return;
        setExporting(format);
        try {
            const res = await api.get(`/timetables/${timetableId}/export/?format=${format}`, {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const a = document.createElement('a');
            a.href = url;
            a.download = `timetable_${timetableId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Export error:', err);
        } finally {
            setExporting(null);
        }
    };

    // ------------------------------------------------------------------ timetable grid
    const buildGrid = () => {
        const timeLabels = [...new Set(
            entries.map(e => `${e.start_time?.slice(0, 5) || ''}–${e.end_time?.slice(0, 5) || ''}`)
        )].sort();
        const lookup = {};
        entries.forEach(e => {
            const key = `${e.day}||${e.start_time?.slice(0, 5)}–${e.end_time?.slice(0, 5)}`;
            lookup[key] = e;
        });
        return { timeLabels, lookup };
    };

    const { timeLabels, lookup } = state === 'done' ? buildGrid() : { timeLabels: [], lookup: {} };

    // ------------------------------------------------------------------ render
    return (
        <div className="timetable-generator container">

            {/* Page header */}
            <div className="gen-header">
                <div className="gen-header-icon">🗓️</div>
                <div>
                    <h1>AI-Powered Timetable Generator</h1>
                    <p className="subtitle">
                        Uses OR-Tools constraint programming and an ML optimizer trained on
                        your historical scheduling data to create conflict-free timetables.
                    </p>
                </div>
            </div>

            {/* Upload hint */}
            {state !== 'done' && (
                <div className="gen-hint">
                    <span>💡 Need to import data first?</span>
                    <Link to="/upload" className="btn-link"> Upload Sample Data →</Link>
                </div>
            )}

            {/* Card */}
            <div className="gen-card card">
                {/* Idle state */}
                {state === 'idle' && (
                    <div className="gen-idle">
                        <div className="gen-steps">
                            {[
                                ['🧠', 'ML Optimizer', 'Trains on past timetable patterns'],
                                ['🔍', 'Constraint Loader', 'Reads rooms, lecturers, time slots'],
                                ['⚙️', 'OR-Tools CP-SAT', 'Solves scheduling constraints'],
                                ['📋', 'Entry Creator', 'Persists results to SQLite DB'],
                            ].map(([icon, title, desc]) => (
                                <div key={title} className="gen-step">
                                    <span className="step-icon">{icon}</span>
                                    <div>
                                        <strong>{title}</strong>
                                        <p>{desc}</p>
                                    </div>
                                </div>
                            ))}
                        </div>
                        <button id="generate-btn" className="btn btn-primary gen-btn" onClick={handleGenerate}>
                            Generate Timetable with AI
                        </button>
                    </div>
                )}

                {/* Generating state */}
                {state === 'generating' && (
                    <div className="gen-loading">
                        <div className="gen-spinner" />
                        <h2>Generating…</h2>
                        <p>Running OR-Tools + ML optimizer. This may take a moment.</p>
                    </div>
                )}

                {/* Error state */}
                {state === 'error' && (
                    <div className="gen-error">
                        <span className="error-icon">⚠️</span>
                        <div>
                            <strong>Generation Failed</strong>
                            <p>{message}</p>
                            {message.includes('upload') && (
                                <Link to="/upload" className="btn btn-secondary" style={{ marginTop: '0.75rem', display: 'inline-block' }}>
                                    Upload Data Now
                                </Link>
                            )}
                        </div>
                        <button className="btn btn-outline gen-retry" onClick={handleGenerate}>Retry</button>
                    </div>
                )}

                {/* Done state */}
                {state === 'done' && (
                    <div className="gen-done">
                        <div className="gen-success-bar">
                            <span>✅ {message}</span>
                            <div className="export-actions">
                                <button
                                    className="btn btn-outline export-btn"
                                    onClick={() => handleExport('excel')}
                                    disabled={exporting === 'excel'}
                                >
                                    {exporting === 'excel' ? '…' : '📊'} Excel
                                </button>
                                <button
                                    className="btn btn-outline export-btn"
                                    onClick={() => handleExport('pdf')}
                                    disabled={exporting === 'pdf'}
                                >
                                    {exporting === 'pdf' ? '…' : '📄'} PDF
                                </button>
                                <button className="btn btn-secondary regen-btn" onClick={handleGenerate}>
                                    🔄 Regenerate
                                </button>
                            </div>
                        </div>

                        {/* Timetable grid */}
                        {entries.length > 0 ? (
                            <div className="timetable-grid-wrapper">
                                <table className="timetable-grid">
                                    <thead>
                                        <tr>
                                            <th className="corner-cell">Time</th>
                                            {DAYS.map(d => <th key={d}>{DAY_LABELS[d]}</th>)}
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {timeLabels.map(tl => (
                                            <tr key={tl}>
                                                <td className="time-cell">{tl}</td>
                                                {DAYS.map(day => {
                                                    const e = lookup[`${day}||${tl}`];
                                                    return (
                                                        <td key={day} className={e ? 'entry-cell' : 'empty-cell'}>
                                                            {e && (
                                                                <div className="entry-block">
                                                                    <span className="entry-code">{e.course_code || e.course}</span>
                                                                    <span className="entry-name">{e.course_name || ''}</span>
                                                                    <span className="entry-meta">
                                                                        {e.lecturer_name || e.lecturer} · {e.room_name || e.room}
                                                                    </span>
                                                                </div>
                                                            )}
                                                        </td>
                                                    );
                                                })}
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            </div>
                        ) : (
                            <p className="no-entries">No entries were generated. Check your data and try again.</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

export default TimetableGenerator;