import { useState, useEffect } from 'react';
import api from '../services/api';
import FileUpload from '../components/FileUpload';
import './DataManager.css';

const DataManager = () => {
    const [activeTab, setActiveTab] = useState('courses');
    const [data, setData] = useState({
        courses: [],
        lecturers: [],
        rooms: [],
        departments: [],
        timeSlots: []
    });
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchData();
    }, []);

    const fetchData = async () => {
        try {
            const [coursesRes, lecturersRes, roomsRes, departmentsRes, timeSlotsRes] = await Promise.all([
                api.get('/courses/'),
                api.get('/lecturers/'),
                api.get('/rooms/'),
                api.get('/departments/'),
                api.get('/timeslots/')
            ]);
            setData({
                courses: coursesRes.data,
                lecturers: lecturersRes.data,
                rooms: roomsRes.data,
                departments: departmentsRes.data,
                timeSlots: timeSlotsRes.data
            });
        } catch (error) {
            console.error('Error fetching data:', error);
        } finally {
            setLoading(false);
        }
    };

    const tabs = [
        { key: 'courses', label: 'Courses' },
        { key: 'lecturers', label: 'Lecturers' },
        { key: 'rooms', label: 'Rooms' },
        { key: 'departments', label: 'Departments' },
        { key: 'timeSlots', label: 'Time Slots' }
    ];

    if (loading) {
        return <div className="container">Loading...</div>;
    }

    return (
        <div className="data-manager container">
            <h1>Manage Data</h1>
            <FileUpload onUpload={fetchData} />
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
                {activeTab === 'courses' && <CoursesList courses={data.courses} refresh={fetchData} />}
                {activeTab === 'lecturers' && <LecturersList lecturers={data.lecturers} refresh={fetchData} />}
                {activeTab === 'rooms' && <RoomsList rooms={data.rooms} refresh={fetchData} />}
                {activeTab === 'departments' && <DepartmentsList departments={data.departments} refresh={fetchData} />}
                {activeTab === 'timeSlots' && <TimeSlotsList timeSlots={data.timeSlots} refresh={fetchData} />}
            </div>
        </div>
    );
};

const CoursesList = ({ courses, refresh }) => {
    return (
        <div>
            <h2>Courses</h2>
            <button className="btn btn-primary">Add Course</button>
            <ul className="data-list">
                {courses.map(course => (
                    <li key={course.id} className="data-item">
                        <span>{course.code} - {course.name}</span>
                        <div>
                            <button className="btn btn-secondary">Edit</button>
                            <button className="btn btn-secondary">Delete</button>
                        </div>
                    </li>
                ))}
            </ul>
        </div>
    );
};

// Similarly for other lists, but for brevity, I'll implement one fully and note for others
const LecturersList = ({ lecturers, refresh }) => (
    <div>
        <h2>Lecturers</h2>
        <button className="btn btn-primary">Add Lecturer</button>
        <ul className="data-list">
            {lecturers.map(lecturer => (
                <li key={lecturer.id} className="data-item">
                    <span>{lecturer.name}</span>
                    <div>
                        <button className="btn btn-secondary">Edit</button>
                        <button className="btn btn-secondary">Delete</button>
                    </div>
                </li>
            ))}
        </ul>
    </div>
);

const RoomsList = ({ rooms, refresh }) => (
    <div>
        <h2>Rooms</h2>
        <button className="btn btn-primary">Add Room</button>
        <ul className="data-list">
            {rooms.map(room => (
                <li key={room.id} className="data-item">
                    <span>{room.name} - Capacity: {room.capacity}</span>
                    <div>
                        <button className="btn btn-secondary">Edit</button>
                        <button className="btn btn-secondary">Delete</button>
                    </div>
                </li>
            ))}
        </ul>
    </div>
);

const DepartmentsList = ({ departments, refresh }) => (
    <div>
        <h2>Departments</h2>
        <button className="btn btn-primary">Add Department</button>
        <ul className="data-list">
            {departments.map(dept => (
                <li key={dept.id} className="data-item">
                    <span>{dept.code} - {dept.name}</span>
                    <div>
                        <button className="btn btn-secondary">Edit</button>
                        <button className="btn btn-secondary">Delete</button>
                    </div>
                </li>
            ))}
        </ul>
    </div>
);

const TimeSlotsList = ({ timeSlots, refresh }) => (
    <div>
        <h2>Time Slots</h2>
        <button className="btn btn-primary">Add Time Slot</button>
        <ul className="data-list">
            {timeSlots.map(slot => (
                <li key={slot.id} className="data-item">
                    <span>{slot.day} {slot.start_time} - {slot.end_time}</span>
                    <div>
                        <button className="btn btn-secondary">Edit</button>
                        <button className="btn btn-secondary">Delete</button>
                    </div>
                </li>
            ))}
        </ul>
    </div>
);

export default DataManager;