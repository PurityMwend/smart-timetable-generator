import { useState, useEffect } from 'react';
import api from '../services/api';
import './TimetableViewer.css';

const TimetableViewer = () => {
    const [activeTab, setActiveTab] = useState('full');
    const [timetable, setTimetable] = useState([]);
    const [courses, setCourses] = useState([]);
    const [lecturers, setLecturers] = useState([]);
    const [rooms, setRooms] = useState([]);
    const [selectedId, setSelectedId] = useState(null);
    const [summary, setSummary] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [timetableRes, coursesRes, lecturersRes, roomsRes] = await Promise.all([
                api.get('/timetable-entries/'),
                api.get('/courses/'),
                api.get('/lecturers/'),
                api.get('/rooms/')
            ]);
            setTimetable(timetableRes.data);
            setCourses(coursesRes.data);
            setLecturers(lecturersRes.data);
            setRooms(roomsRes.data);
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    const fetchSummary = async (type, id) => {
        try {
            let endpoint;
            if (type === 'course') endpoint = `/courses/${id}/timetable/`;
            else if (type === 'lecturer') endpoint = `/lecturers/${id}/timetable/`;
            else if (type === 'room') endpoint = `/rooms/${id}/timetable/`;
            const response = await api.get(endpoint);
            setSummary(response.data);
        } catch (error) {
            console.error('Error fetching summary:', error);
        }
    };

    const handleSelect = (type, id) => {
        setSelectedId(id);
        fetchSummary(type, id);
    };

    if (loading) {
        return <div className="container">Loading timetable...</div>;
    }

    return (
        <div className="timetable-viewer container">
            <h1>Timetable Viewer</h1>
            <div className="tabs">
                <button className={`tab-button ${activeTab === 'full' ? 'active' : ''}`} onClick={() => setActiveTab('full')}>
                    Full Timetable
                </button>
                <button className={`tab-button ${activeTab === 'courses' ? 'active' : ''}`} onClick={() => setActiveTab('courses')}>
                    Courses
                </button>
                <button className={`tab-button ${activeTab === 'lecturers' ? 'active' : ''}`} onClick={() => setActiveTab('lecturers')}>
                    Lecturers
                </button>
                <button className={`tab-button ${activeTab === 'rooms' ? 'active' : ''}`} onClick={() => setActiveTab('rooms')}>
                    Rooms
                </button>
            </div>
            <div className="tab-content">
                {activeTab === 'full' && <FullTimetable timetable={timetable} />}
                {activeTab === 'courses' && (
                    <SummaryView
                        items={courses}
                        onSelect={(id) => handleSelect('course', id)}
                        selectedId={selectedId}
                        summary={summary}
                        label="course"
                    />
                )}
                {activeTab === 'lecturers' && (
                    <SummaryView
                        items={lecturers}
                        onSelect={(id) => handleSelect('lecturer', id)}
                        selectedId={selectedId}
                        summary={summary}
                        label="lecturer"
                    />
                )}
                {activeTab === 'rooms' && (
                    <SummaryView
                        items={rooms}
                        onSelect={(id) => handleSelect('room', id)}
                        selectedId={selectedId}
                        summary={summary}
                        label="room"
                    />
                )}
            </div>
        </div>
    );
};

const FullTimetable = ({ timetable }) => {
    const days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const timeSlots = ['9:00-10:00', '10:00-11:00', '11:00-12:00', '14:00-15:00', '15:00-16:00', '16:00-17:00'];

    const getEntryForSlot = (day, time) => {
        return timetable.find(entry => entry.day === day && entry.time_slot === time);
    };

    return (
        <div className="timetable-grid">
            <div className="time-column">
                <div className="header-cell">Time</div>
                {timeSlots.map(time => (
                    <div key={time} className="time-cell">{time}</div>
                ))}
            </div>
            {days.map(day => (
                <div key={day} className="day-column">
                    <div className="header-cell">{day}</div>
                    {timeSlots.map(time => {
                        const entry = getEntryForSlot(day, time);
                        return (
                            <div key={time} className="entry-cell">
                                {entry ? (
                                    <div className="entry">
                                        <strong>{entry.course}</strong>
                                        <br />
                                        {entry.lecturer}
                                        <br />
                                        {entry.room}
                                    </div>
                                ) : (
                                    <div className="empty">Free</div>
                                )}
                            </div>
                        );
                    })}
                </div>
            ))}
        </div>
    );
};

const SummaryView = ({ items, onSelect, selectedId, summary, label }) => {
    return (
        <div className="summary-view">
            <div className="item-list">
                <h3>Select {label}</h3>
                <ul>
                    {items.map(item => (
                        <li key={item.id}>
                            <button
                                className={selectedId === item.id ? 'selected' : ''}
                                onClick={() => onSelect(item.id)}
                            >
                                {item.name || item.code}
                            </button>
                        </li>
                    ))}
                </ul>
            </div>
            <div className="summary">
                <h3>Timetable for Selected {label}</h3>
                {summary.length > 0 ? (
                    <ul>
                        {summary.map(entry => (
                            <li key={entry.id}>
                                {entry.time_slot} - {entry.course} - {entry.room}
                            </li>
                        ))}
                    </ul>
                ) : (
                    <p>No entries</p>
                )}
            </div>
        </div>
    );
};

export default TimetableViewer;