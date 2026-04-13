import { useState, useEffect } from 'react';
import api from '../services/api';
import './TrainingData.css';

const TrainingData = () => {
    const [activeTab, setActiveTab] = useState('datasets');
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState({
        datasets: [],
        commonUnits: [],
        recurrentUnits: [],
        courses: [],
        lecturers: [],
        departments: []
    });
    const [formData, setFormData] = useState({
        name: '',
        description: '',
        selectedCourses: [],
        selectedLecturers: [],
        selectedDepartments: [],
        selectedUnits: []
    });
    const [showForm, setShowForm] = useState(false);

    useEffect(() => {
        fetchAllData();
    }, []);

    const fetchAllData = async () => {
        try {
            setLoading(true);
            const [datasetsRes, unitsRes, recurrentRes, coursesRes, lecturersRes, deptRes] = await Promise.all([
                api.get('/training-data/'),
                api.get('/common-units/'),
                api.get('/recurrent-units/'),
                api.get('/courses/'),
                api.get('/lecturers/'),
                api.get('/departments/')
            ]);
            setData({
                datasets: datasetsRes.data,
                commonUnits: unitsRes.data,
                recurrentUnits: recurrentRes.data,
                courses: coursesRes.data,
                lecturers: lecturersRes.data,
                departments: deptRes.data
            });
        } catch (error) {
            console.error('Error fetching training data:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleCreateDataset = async (e) => {
        e.preventDefault();
        try {
            const payload = {
                name: formData.name,
                description: formData.description,
                course_ids: formData.selectedCourses,
                lecturer_ids: formData.selectedLecturers,
                department_ids: formData.selectedDepartments,
                common_unit_ids: formData.selectedUnits
            };
            await api.post('/training-data/', payload);
            setShowForm(false);
            setFormData({
                name: '',
                description: '',
                selectedCourses: [],
                selectedLecturers: [],
                selectedDepartments: [],
                selectedUnits: []
            });
            fetchAllData();
        } catch (error) {
            console.error('Error creating dataset:', error);
        }
    };

    const handleDeleteDataset = async (id) => {
        if (confirm('Are you sure you want to delete this dataset?')) {
            try {
                await api.delete(`/training-data/${id}/`);
                fetchAllData();
            } catch (error) {
                console.error('Error deleting dataset:', error);
            }
        }
    };

    const handleAddCommonUnit = async (e) => {
        e.preventDefault();
        const name = e.target.name.value;
        const code = e.target.code.value;
        try {
            await api.post('/common-units/', {
                name,
                code,
                hours_per_week: 3.0
            });
            e.target.reset();
            fetchAllData();
        } catch (error) {
            console.error('Error adding common unit:', error);
        }
    };

    const tabs = [
        { key: 'datasets', label: 'Training Datasets' },
        { key: 'commonUnits', label: 'Common Units' },
        { key: 'recurrentUnits', label: 'Recurrent Units' }
    ];

    if (loading) {
        return <div className="container">Loading training data...</div>;
    }

    return (
        <div className="training-data container">
            <h1>Training Data Management</h1>
            <p className="subtitle">For ML model training and scheduling optimization</p>

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
                {activeTab === 'datasets' && (
                    <div className="datasets-tab">
                        <button
                            className="btn btn-primary"
                            onClick={() => setShowForm(!showForm)}
                        >
                            {showForm ? 'Cancel' : 'Create New Dataset'}
                        </button>

                        {showForm && (
                            <form onSubmit={handleCreateDataset} className="dataset-form">
                                <h3>Create Training Dataset</h3>
                                <div className="form-group">
                                    <label>Dataset Name</label>
                                    <input
                                        type="text"
                                        placeholder="e.g., Fall 2024 Training"
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        required
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Description</label>
                                    <textarea
                                        placeholder="Describe the purpose of this training dataset"
                                        value={formData.description}
                                        onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                                        rows="3"
                                    />
                                </div>

                                <div className="form-group">
                                    <label>Select Courses</label>
                                    <div className="checkbox-group">
                                        {data.courses.map(course => (
                                            <label key={course.id}>
                                                <input
                                                    type="checkbox"
                                                    checked={formData.selectedCourses.includes(course.id)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setFormData({
                                                                ...formData,
                                                                selectedCourses: [...formData.selectedCourses, course.id]
                                                            });
                                                        } else {
                                                            setFormData({
                                                                ...formData,
                                                                selectedCourses: formData.selectedCourses.filter(id => id !== course.id)
                                                            });
                                                        }
                                                    }}
                                                />
                                                {course.code} - {course.name}
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Select Lecturers</label>
                                    <div className="checkbox-group">
                                        {data.lecturers.map(lecturer => (
                                            <label key={lecturer.id}>
                                                <input
                                                    type="checkbox"
                                                    checked={formData.selectedLecturers.includes(lecturer.id)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setFormData({
                                                                ...formData,
                                                                selectedLecturers: [...formData.selectedLecturers, lecturer.id]
                                                            });
                                                        } else {
                                                            setFormData({
                                                                ...formData,
                                                                selectedLecturers: formData.selectedLecturers.filter(id => id !== lecturer.id)
                                                            });
                                                        }
                                                    }}
                                                />
                                                {lecturer.name} ({lecturer.employee_id})
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <div className="form-group">
                                    <label>Select Departments</label>
                                    <div className="checkbox-group">
                                        {data.departments.map(dept => (
                                            <label key={dept.id}>
                                                <input
                                                    type="checkbox"
                                                    checked={formData.selectedDepartments.includes(dept.id)}
                                                    onChange={(e) => {
                                                        if (e.target.checked) {
                                                            setFormData({
                                                                ...formData,
                                                                selectedDepartments: [...formData.selectedDepartments, dept.id]
                                                            });
                                                        } else {
                                                            setFormData({
                                                                ...formData,
                                                                selectedDepartments: formData.selectedDepartments.filter(id => id !== dept.id)
                                                            });
                                                        }
                                                    }}
                                                />
                                                {dept.code} - {dept.name}
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                <button type="submit" className="btn btn-success">Create Dataset</button>
                            </form>
                        )}

                        <div className="datasets-list">
                            {data.datasets.length === 0 ? (
                                <p className="empty-message">No training datasets created yet</p>
                            ) : (
                                data.datasets.map(dataset => (
                                    <div key={dataset.id} className="dataset-card">
                                        <div className="dataset-header">
                                            <h3>{dataset.name}</h3>
                                            <span className={`status ${dataset.is_active ? 'active' : 'inactive'}`}>
                                                {dataset.is_active ? 'Active' : 'Inactive'}
                                            </span>
                                        </div>
                                        <p>{dataset.description}</p>
                                        <div className="dataset-stats">
                                            <span>{dataset.courses?.length || 0} courses</span>
                                            <span>{dataset.lecturers?.length || 0} lecturers</span>
                                            <span>{dataset.departments?.length || 0} departments</span>
                                        </div>
                                        <div className="dataset-actions">
                                            <button className="btn btn-secondary">Edit</button>
                                            <button
                                                className="btn btn-danger"
                                                onClick={() => handleDeleteDataset(dataset.id)}
                                            >
                                                Delete
                                            </button>
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'commonUnits' && (
                    <div className="common-units-tab">
                        <form onSubmit={handleAddCommonUnit} className="unit-form">
                            <h3>Add Common Unit</h3>
                            <input
                                type="text"
                                name="code"
                                placeholder="Unit Code (e.g., ISS401)"
                                required
                            />
                            <input
                                type="text"
                                name="name"
                                placeholder="Unit Name"
                                required
                            />
                            <button type="submit" className="btn btn-primary">Add Unit</button>
                        </form>

                        <div className="units-list">
                            <h3>Existing Common Units</h3>
                            {data.commonUnits.length === 0 ? (
                                <p>No common units exist</p>
                            ) : (
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Code</th>
                                            <th>Name</th>
                                            <th>Hours/Week</th>
                                            <th>Created</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.commonUnits.map(unit => (
                                            <tr key={unit.id}>
                                                <td>{unit.code}</td>
                                                <td>{unit.name}</td>
                                                <td>{unit.hours_per_week}</td>
                                                <td>{new Date(unit.created_at).toLocaleDateString()}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                    </div>
                )}

                {activeTab === 'recurrentUnits' && (
                    <div className="recurrent-units-tab">
                        <h3>Recurrent Units (Units in Specific Courses)</h3>
                        <div className="recurrent-units-list">
                            {data.recurrentUnits.length === 0 ? (
                                <p>No recurrent units configured</p>
                            ) : (
                                <table>
                                    <thead>
                                        <tr>
                                            <th>Unit Code</th>
                                            <th>Unit Name</th>
                                            <th>Course</th>
                                            <th>Year.Semester</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {data.recurrentUnits.map(unit => (
                                            <tr key={unit.id}>
                                                <td>{unit.unit_code}</td>
                                                <td>{unit.unit_name}</td>
                                                <td>{unit.course_code} - {unit.course_name}</td>
                                                <td>{unit.year_of_study}.{unit.semester}</td>
                                            </tr>
                                        ))}
                                    </tbody>
                                </table>
                            )}
                        </div>
                        <p className="info-text">
                            Recurrent units are common units that appear in specific courses and years.
                            For example: "Information Systems Security and Audit" (ISS401) is taught in
                            Software Engineering 4.2 by multiple lecturers but assigned to specific ones.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
};

export default TrainingData;
