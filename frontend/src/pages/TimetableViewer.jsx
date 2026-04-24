import { useState, useEffect } from 'react';
import api from '../services/api';
import './TimetableViewer.css';

const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];
const DAY_LABELS = { MON: 'Monday', TUE: 'Tuesday', WED: 'Wednesday', THU: 'Thursday', FRI: 'Friday', SAT: 'Saturday' };

const TimetableViewer = () => {
    const [timetables, setTimetables] = useState([]);
    const [selectedTimetableId, setSelectedTimetableId] = useState(null);
    const [entries, setEntries] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [exporting, setExporting] = useState(null);

    useEffect(() => {
        fetchTimetables();
    }, []);

    useEffect(() => {
        if (selectedTimetableId) {
            fetchEntries(selectedTimetableId);
        }
    }, [selectedTimetableId]);

    const fetchTimetables = async () => {
        try {
            const res = await api.get('/timetables/');
            setTimetables(res.data);
            if (res.data.length > 0) {
                // Default to the most recent one (assuming higher ID is newer)
                const latest = [...res.data].sort((a, b) => b.id - a.id)[0];
                setSelectedTimetableId(latest.id);
            } else {
                setLoading(false);
            }
        } catch (err) {
            setError('Failed to fetch timetables list.');
            setLoading(false);
        }
    };

    const fetchEntries = async (id) => {
        setLoading(true);
        try {
            const res = await api.get(`/timetable-entries/?timetable=${id}`);
            setEntries(res.data);
            setError(null);
        } catch (err) {
            setError('Failed to load timetable entries.');
        } finally {
            setLoading(false);
        }
    };

    const handleExport = async (format) => {
        if (!selectedTimetableId) return;
        setExporting(format);
        try {
            const res = await api.get(`/timetables/${selectedTimetableId}/export/?format=${format}`, {
                responseType: 'blob',
            });
            const url = window.URL.createObjectURL(new Blob([res.data]));
            const a = document.createElement('a');
            a.href = url;
            a.download = `timetable_${selectedTimetableId}.${format === 'pdf' ? 'pdf' : 'xlsx'}`;
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (err) {
            console.error('Export error:', err);
        } finally {
            setExporting(null);
        }
    };

    // ------------------------------------------------------------------ Grid logic
    const buildGrid = () => {
        // Collect unique time slots
        const slots = [...new Set(
            entries.map(e => `${e.start_time.slice(0, 5)}–${e.end_time.slice(0, 5)}`)
        )].sort();

        const lookup = {};
        entries.forEach(e => {
            const key = `${e.day}||${e.start_time.slice(0, 5)}–${e.end_time.slice(0, 5)}`;
            lookup[key] = e;
        });

        return { slots, lookup };
    };

    const { slots, lookup } = buildGrid();

    if (loading && timetables.length === 0) {
        return <div className="viewer-loading">Loading Timetables...</div>;
    }

    const selectedTimetable = timetables.find(t => t.id === selectedTimetableId);

    return (
        <div className="timetable-viewer container">
            <div className="viewer-header">
                <div className="header-icon">📅</div>
                <div>
                    <h1>Timetable Browser</h1>
                    <p className="subtitle">View and export generated schedules for your school.</p>
                </div>
            </div>

            <div className="viewer-controls">
                <div className="timetable-selector">
                    <label>Select Timetable:</label>
                    <select
                        value={selectedTimetableId || ''}
                        onChange={(e) => setSelectedTimetableId(Number(e.target.value))}
                        disabled={loading}
                    >
                        {timetables.length === 0 && <option value="">No timetables found</option>}
                        {timetables.map(t => (
                            <option key={t.id} value={t.id}>
                                {t.name} ({t.academic_year})
                            </option>
                        ))}
                    </select>
                </div>

                {selectedTimetableId && (
                    <div className="viewer-actions">
                        <button className="btn btn-outline" onClick={() => handleExport('excel')} disabled={exporting}>
                            {exporting === 'excel' ? '...' : 'Excel (.xlsx)'}
                        </button>
                        <button className="btn btn-outline" onClick={() => handleExport('pdf')} disabled={exporting}>
                            {exporting === 'pdf' ? '...' : 'PDF (.pdf)'}
                        </button>
                    </div>
                )}
            </div>

            {error && <div className="viewer-error">⚠️ {error}</div>}

            {loading ? (
                <div className="viewer-loading-inline">
                    <div className="spinner" /> Loading entries...
                </div>
            ) : (
                <div className="viewer-content">
                    {selectedTimetable && (
                        <div className="timetable-info">
                            <span className="badge">{selectedTimetable.status}</span>
                            <span className="meta">
                                {selectedTimetable.program_name} · Semester {selectedTimetable.semester}
                            </span>
                        </div>
                    )}

                    {entries.length > 0 ? (
                        <div className="viewer-grid-wrapper">
                            <table className="viewer-grid">
                                <thead>
                                    <tr>
                                        <th className="corner">Time</th>
                                        {DAYS.map(day => <th key={day}>{DAY_LABELS[day]}</th>)}
                                    </tr>
                                </thead>
                                <tbody>
                                    {slots.map(slot => (
                                        <tr key={slot}>
                                            <td className="time-label">{slot}</td>
                                            {DAYS.map(day => {
                                                const entry = lookup[`${day}||${slot}`];
                                                return (
                                                    <td key={day} className={entry ? 'entry-cell' : 'empty-cell'}>
                                                        {entry && (
                                                            <div className="entry-card">
                                                                <div className="course-code">{entry.course_code || entry.course}</div>
                                                                <div className="course-name">{entry.course_name}</div>
                                                                <div className="entry-footer">
                                                                    <span>👤 {entry.lecturer_name || entry.lecturer}</span>
                                                                    <span>🏫 {entry.room_name || entry.room}</span>
                                                                </div>
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
                        <div className="viewer-empty">
                            <div className="empty-icon">📭</div>
                            <p>No entries found for this timetable.</p>
                            <button className="btn btn-primary" onClick={() => window.location.href = '/generate'}>
                                Generate One Now
                            </button>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default TimetableViewer;