import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import FileUpload from '../components/FileUpload';
import './DataManager.css';

const DataManager = () => {
    const { isTimetabler, isLecturer } = useAuth();
    const [activeTab, setActiveTab] = useState('courses');
    const [data, setData] = useState({
        courses: [],
        lecturers: [],
        rooms: [],
        departments: [],
        timeSlots: [],
        entries: []
    });
    const [loading, setLoading] = useState(true);
    const [showModal, setShowModal] = useState(false);
    const [modalType, setModalType] = useState(null); // 'course', 'lecturer', 'room', etc
    const [editingId, setEditingId] = useState(null);
    const [formError, setFormError] = useState('');

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            setLoading(true);
            const requests = [
                api.get('/courses/'),
                api.get('/lecturers/'),
                api.get('/rooms/'),
                api.get('/timetable-entries/'),
                api.get('/departments/'),
                api.get('/timeslots/')
            ];

            const responses = await Promise.all(requests);
            const newData = {
                courses: responses[0].data || [],
                lecturers: responses[1].data || [],
                rooms: responses[2].data || [],
                entries: responses[3].data || [],
                departments: responses[4].data || [],
                timeSlots: responses[5].data || []
            };
            setData(newData);

            // Set default tab based on role
            if (isLecturer && !isTimetabler) {
                setActiveTab('courses');
            }
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    // Define tabs based on user role
    const getTabs = () => {
        const baseTabs = [
            { key: 'courses', label: 'Courses' },
            { key: 'rooms', label: 'Rooms' },
            { key: 'departments', label: 'Departments' },
            { key: 'timeSlots', label: 'Time Slots' }
        ];

        // Lecturers and admins can see entries
        baseTabs.push({ key: 'entries', label: 'Entries' });

        // Only admins see lecturers
        if (isTimetabler) {
            baseTabs.splice(1, 0, { key: 'lecturers', label: 'Lecturers' });
        }

        return baseTabs;
    };

    const tabs = getTabs();

    if (loading) {
        return <div className="container">Loading...</div>;
    }

    const showTitle = isTimetabler ? 'Manage All Data' : 'My Data Management';

    const openModal = (type, id = null) => {
        setModalType(type);
        setEditingId(id);
        setFormError('');
        setShowModal(true);
    };

    const closeModal = () => {
        setShowModal(false);
        setModalType(null);
        setEditingId(null);
        setFormError('');
    };

    const handleSuccess = (message = 'Operation successful') => {
        closeModal();
        fetchData();
    };

    const handleDelete = async (type, id) => {
        if (!window.confirm('Are you sure you want to delete this?')) return;

        try {
            const endpoints = {
                course: 'courses',
                lecturer: 'lecturers',
                room: 'rooms',
                department: 'departments',
                timeSlot: 'timeslots',
                entry: 'timetable-entries'
            };

            await api.delete(`/${endpoints[type]}/${id}/`);
            fetchData();
        } catch (error) {
            alert(`Error deleting: ${error.response?.data?.detail || error.message}`);
        }
    };

    return (
        <div className="data-manager container">
            <h1>{showTitle}</h1>
            {isTimetabler && <FileUpload onUpload={fetchData} />}
            {isLecturer && !isTimetabler && (
                <div className="lecturer-notice">
                    <p>📚 You can manage courses, rooms, schedule entries, and view departments and time slots</p>
                </div>
            )}
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
                {activeTab === 'courses' && (
                    <CoursesList
                        courses={data.courses}
                        canEdit={isTimetabler}
                        onAdd={() => openModal('course')}
                        onEdit={(id) => openModal('course', id)}
                        onDelete={(id) => handleDelete('course', id)}
                        data={data}
                    />
                )}
                {activeTab === 'lecturers' && isTimetabler && (
                    <LecturersList
                        lecturers={data.lecturers}
                        onAdd={() => openModal('lecturer')}
                        onEdit={(id) => openModal('lecturer', id)}
                        onDelete={(id) => handleDelete('lecturer', id)}
                        data={data}
                    />
                )}
                {activeTab === 'rooms' && (
                    <RoomsList
                        rooms={data.rooms}
                        canEdit={isTimetabler}
                        onAdd={() => openModal('room')}
                        onEdit={(id) => openModal('room', id)}
                        onDelete={(id) => handleDelete('room', id)}
                    />
                )}
                {activeTab === 'departments' && (
                    <DepartmentsList
                        departments={data.departments}
                        canEdit={isTimetabler}
                        onAdd={() => openModal('department')}
                        onEdit={(id) => openModal('department', id)}
                        onDelete={(id) => handleDelete('department', id)}
                        data={data}
                    />
                )}
                {activeTab === 'timeSlots' && (
                    <TimeSlotsList
                        timeSlots={data.timeSlots}
                        canEdit={isTimetabler}
                        onAdd={() => openModal('timeSlot')}
                        onEdit={(id) => openModal('timeSlot', id)}
                        onDelete={(id) => handleDelete('timeSlot', id)}
                    />
                )}
                {activeTab === 'entries' && (isLecturer || isTimetabler) && (
                    <EntriesList
                        entries={data.entries}
                        canEdit={isTimetabler}
                        onAdd={() => openModal('entry')}
                        onEdit={(id) => openModal('entry', id)}
                        onDelete={(id) => handleDelete('entry', id)}
                        data={data}
                    />
                )}
            </div>

            {/* Modal for adding/editing */}
            {showModal && (
                <modal
                    type={modalType}
                    editingId={editingId}
                    data={data}
                    formError={formError}
                    onClose={closeModal}
                    onSuccess={handleSuccess}
                    setFormError={setFormError}
                />
            )}
        </div>
    );
};

// Modal Component for all forms
const EntityModal = ({ type, editingId, data, formError, onClose, onSuccess, setFormError }) => {
    const [formData, setFormData] = useState({});
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (editingId) {
            // Load existing data for editing
            const dataMap = {
                course: data.courses,
                lecturer: data.lecturers,
                room: data.rooms,
                department: data.departments,
                timeSlot: data.timeSlots,
                entry: data.entries
            };
            const item = dataMap[type]?.find(i => i.id === editingId);
            if (item) setFormData(item);
        }
    }, [editingId, type, data]);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setFormError('');

        try {
            const endpoints = {
                course: 'courses',
                lecturer: 'lecturers',
                room: 'rooms',
                department: 'departments',
                timeSlot: 'timeslots',
                entry: 'timetable-entries'
            };

            if (editingId) {
                await api.put(`/${endpoints[type]}/${editingId}/`, formData);
            } else {
                await api.post(`/${endpoints[type]}/`, formData);
            }
            onSuccess();
        } catch (error) {
            setFormError(error.response?.data?.detail || error.message);
        } finally {
            setLoading(false);
        }
    };

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{editingId ? `Edit ${type}` : `Add ${type}`}</h2>
                    <button className="modal-close" onClick={onClose}>✕</button>
                </div>

                {formError && <div className="error-message">{formError}</div>}

                <form onSubmit={handleSubmit}>
                    {type === 'course' && (
                        <>
                            <input
                                type="text"
                                name="code"
                                placeholder="Course Code"
                                value={formData.code || ''}
                                onChange={handleChange}
                                required
                                disabled={!!editingId}
                            />
                            <input
                                type="text"
                                name="name"
                                placeholder="Course Name"
                                value={formData.name || ''}
                                onChange={handleChange}
                                required
                            />
                            <select name="department" value={formData.department || ''} onChange={handleChange}>
                                <option value="">Select Department</option>
                                {data.departments?.map(d => (
                                    <option key={d.id} value={d.id}>{d.name}</option>
                                ))}
                            </select>
                            <input
                                type="number"
                                name="year_of_study"
                                placeholder="Year of Study"
                                value={formData.year_of_study || 1}
                                onChange={handleChange}
                                min="1"
                                max="6"
                            />
                            <input
                                type="number"
                                name="class_size"
                                placeholder="Class Size"
                                value={formData.class_size || 0}
                                onChange={handleChange}
                            />
                        </>
                    )}

                    {type === 'lecturer' && (
                        <>
                            <input
                                type="text"
                                name="name"
                                placeholder="Name"
                                value={formData.name || ''}
                                onChange={handleChange}
                                required
                            />
                            <input
                                type="text"
                                name="employee_id"
                                placeholder="Employee ID"
                                value={formData.employee_id || ''}
                                onChange={handleChange}
                                required
                                disabled={!!editingId}
                            />
                            <input
                                type="email"
                                name="email"
                                placeholder="Email"
                                value={formData.email || ''}
                                onChange={handleChange}
                            />
                            <select name="department" value={formData.department || ''} onChange={handleChange}>
                                <option value="">Select Department</option>
                                {data.departments?.map(d => (
                                    <option key={d.id} value={d.id}>{d.name}</option>
                                ))}
                            </select>
                        </>
                    )}

                    {type === 'room' && (
                        <>
                            <input
                                type="text"
                                name="name"
                                placeholder="Room Name"
                                value={formData.name || ''}
                                onChange={handleChange}
                                required
                            />
                            <input
                                type="text"
                                name="building"
                                placeholder="Building"
                                value={formData.building || ''}
                                onChange={handleChange}
                            />
                            <input
                                type="number"
                                name="capacity"
                                placeholder="Capacity"
                                value={formData.capacity || 30}
                                onChange={handleChange}
                            />
                            <select name="room_type" value={formData.room_type || 'Lecture_Hall'} onChange={handleChange}>
                                <option value="Lecture_Hall">Lecture Hall</option>
                                <option value="Lab">Lab</option>
                                <option value="Seminar">Seminar Room</option>
                                <option value="Tutorial">Tutorial Room</option>
                            </select>
                        </>
                    )}

                    {type === 'department' && (
                        <>
                            <input
                                type="text"
                                name="code"
                                placeholder="Department Code"
                                value={formData.code || ''}
                                onChange={handleChange}
                                required
                                disabled={!!editingId}
                            />
                            <input
                                type="text"
                                name="name"
                                placeholder="Department Name"
                                value={formData.name || ''}
                                onChange={handleChange}
                                required
                            />
                            <select name="school" value={formData.school || ''} onChange={handleChange}>
                                <option value="">Select School</option>
                                {/* Schools would be added here if we fetch them */}
                            </select>
                        </>
                    )}

                    {type === 'timeSlot' && (
                        <>
                            <select name="day" value={formData.day || ''} onChange={handleChange} required>
                                <option value="">Select Day</option>
                                <option value="Monday">Monday</option>
                                <option value="Tuesday">Tuesday</option>
                                <option value="Wednesday">Wednesday</option>
                                <option value="Thursday">Thursday</option>
                                <option value="Friday">Friday</option>
                                <option value="Saturday">Saturday</option>
                            </select>
                            <input
                                type="time"
                                name="start_time"
                                value={formData.start_time || ''}
                                onChange={handleChange}
                                required
                            />
                            <input
                                type="time"
                                name="end_time"
                                value={formData.end_time || ''}
                                onChange={handleChange}
                                required
                            />
                        </>
                    )}

                    {type === 'entry' && (
                        <>
                            <select name="course" value={formData.course || ''} onChange={handleChange} required>
                                <option value="">Select Course</option>
                                {data.courses?.map(c => (
                                    <option key={c.id} value={c.id}>{c.code} - {c.name}</option>
                                ))}
                            </select>
                            <select name="lecturer" value={formData.lecturer || ''} onChange={handleChange} required>
                                <option value="">Select Lecturer</option>
                                {data.lecturers?.map(l => (
                                    <option key={l.id} value={l.id}>{l.name}</option>
                                ))}
                            </select>
                            <select name="room" value={formData.room || ''} onChange={handleChange} required>
                                <option value="">Select Room</option>
                                {data.rooms?.map(r => (
                                    <option key={r.id} value={r.id}>{r.name}</option>
                                ))}
                            </select>
                            <select name="time_slot" value={formData.time_slot || ''} onChange={handleChange} required>
                                <option value="">Select Time Slot</option>
                                {data.timeSlots?.map(t => (
                                    <option key={t.id} value={t.id}>{t.day} {t.start_time}-{t.end_time}</option>
                                ))}
                            </select>
                        </>
                    )}

                    <div className="form-actions">
                        <button type="submit" className="btn btn-primary" disabled={loading}>
                            {loading ? 'Saving...' : 'Save'}
                        </button>
                        <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// Modal function reference (for usage in tabs)
const modal = EntityModal;

// List Components with functional buttons
const CoursesList = ({ courses, canEdit, onAdd, onEdit, onDelete, data }) => (
    <div>
        <div className="list-header">
            <h2>Courses</h2>
            {canEdit && <button className="btn btn-primary" onClick={onAdd}>+ Add Course</button>}
        </div>
        {courses.length === 0 ? (
            <p className="empty-message">No courses yet</p>
        ) : (
            <ul className="data-list">
                {courses.map(course => (
                    <li key={course.id} className="data-item">
                        <div className="data-info">
                            <span className="code">{course.code}</span>
                            <span className="name">{course.name}</span>
                            <span className="meta">Year {course.year_of_study} • {course.class_size} students</span>
                        </div>
                        {canEdit && (
                            <div className="item-actions">
                                <button className="btn btn-secondary" onClick={() => onEdit(course.id)}>Edit</button>
                                <button className="btn btn-danger" onClick={() => onDelete(course.id)}>Delete</button>
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        )}
    </div>
);

const LecturersList = ({ lecturers, onAdd, onEdit, onDelete, data }) => (
    <div>
        <div className="list-header">
            <h2>Lecturers</h2>
            <button className="btn btn-primary" onClick={onAdd}>+ Add Lecturer</button>
        </div>
        {lecturers.length === 0 ? (
            <p className="empty-message">No lecturers yet</p>
        ) : (
            <ul className="data-list">
                {lecturers.map(lecturer => (
                    <li key={lecturer.id} className="data-item">
                        <div className="data-info">
                            <span className="name">{lecturer.name}</span>
                            <span className="meta">{lecturer.employee_id}</span>
                            {lecturer.email && <span className="meta">{lecturer.email}</span>}
                        </div>
                        <div className="item-actions">
                            <button className="btn btn-secondary" onClick={() => onEdit(lecturer.id)}>Edit</button>
                            <button className="btn btn-danger" onClick={() => onDelete(lecturer.id)}>Delete</button>
                        </div>
                    </li>
                ))}
            </ul>
        )}
    </div>
);

const RoomsList = ({ rooms, canEdit, onAdd, onEdit, onDelete }) => (
    <div>
        <div className="list-header">
            <h2>Rooms</h2>
            {canEdit && <button className="btn btn-primary" onClick={onAdd}>+ Add Room</button>}
        </div>
        {rooms.length === 0 ? (
            <p className="empty-message">No rooms yet</p>
        ) : (
            <ul className="data-list">
                {rooms.map(room => (
                    <li key={room.id} className="data-item">
                        <div className="data-info">
                            <span className="name">{room.name}</span>
                            {room.building && <span className="meta">{room.building}</span>}
                            <span className="meta">Capacity: {room.capacity}</span>
                        </div>
                        {canEdit && (
                            <div className="item-actions">
                                <button className="btn btn-secondary" onClick={() => onEdit(room.id)}>Edit</button>
                                <button className="btn btn-danger" onClick={() => onDelete(room.id)}>Delete</button>
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        )}
    </div>
);

const DepartmentsList = ({ departments, canEdit, onAdd, onEdit, onDelete, data }) => (
    <div>
        <div className="list-header">
            <h2>Departments</h2>
            {canEdit && <button className="btn btn-primary" onClick={onAdd}>+ Add Department</button>}
        </div>
        {departments.length === 0 ? (
            <p className="empty-message">No departments yet</p>
        ) : (
            <ul className="data-list">
                {departments.map(dept => (
                    <li key={dept.id} className="data-item">
                        <div className="data-info">
                            <span className="code">{dept.code}</span>
                            <span className="name">{dept.name}</span>
                        </div>
                        {canEdit && (
                            <div className="item-actions">
                                <button className="btn btn-secondary" onClick={() => onEdit(dept.id)}>Edit</button>
                                <button className="btn btn-danger" onClick={() => onDelete(dept.id)}>Delete</button>
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        )}
    </div>
);

const TimeSlotsList = ({ timeSlots, canEdit, onAdd, onEdit, onDelete }) => (
    <div>
        <div className="list-header">
            <h2>Time Slots</h2>
            {canEdit && <button className="btn btn-primary" onClick={onAdd}>+ Add Time Slot</button>}
        </div>
        {timeSlots.length === 0 ? (
            <p className="empty-message">No time slots yet</p>
        ) : (
            <ul className="data-list">
                {timeSlots.map(slot => (
                    <li key={slot.id} className="data-item">
                        <div className="data-info">
                            <span className="name">{slot.day}</span>
                            <span className="meta">{slot.start_time} - {slot.end_time}</span>
                        </div>
                        {canEdit && (
                            <div className="item-actions">
                                <button className="btn btn-secondary" onClick={() => onEdit(slot.id)}>Edit</button>
                                <button className="btn btn-danger" onClick={() => onDelete(slot.id)}>Delete</button>
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        )}
    </div>
);

const EntriesList = ({ entries, canEdit, onAdd, onEdit, onDelete, data }) => (
    <div>
        <div className="list-header">
            <h2>Timetable Entries</h2>
            {canEdit && <button className="btn btn-primary" onClick={onAdd}>+ Add Entry</button>}
        </div>
        <div className="entries-info">
            <p>📋 Total scheduled entries: {entries.length}</p>
        </div>
        {entries.length === 0 ? (
            <p className="empty-message">No entries scheduled yet</p>
        ) : (
            <table className="entries-table">
                <thead>
                    <tr>
                        <th>Course</th>
                        <th>Lecturer</th>
                        <th>Room</th>
                        <th>Day & Time</th>
                        {canEdit && <th>Actions</th>}
                    </tr>
                </thead>
                <tbody>
                    {entries.map(entry => (
                        <tr key={entry.id}>
                            <td><strong>{entry.course_code}</strong><br />{entry.course_name}</td>
                            <td>{entry.lecturer_name}</td>
                            <td>{entry.room_name}</td>
                            <td>{entry.day_display} {entry.start_time} - {entry.end_time}</td>
                            {canEdit && (
                                <td>
                                    <button className="btn btn-sm btn-secondary" onClick={() => onEdit(entry.id)}>Edit</button>
                                    <button className="btn btn-sm btn-danger" onClick={() => onDelete(entry.id)}>Delete</button>
                                </td>
                            )}
                        </tr>
                    ))}
                </tbody>
            </table>
        )}
    </div>
);

export default DataManager;
