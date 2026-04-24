import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '../context/AuthContext';
import api from '../services/api';
import FileUpload from '../components/FileUpload';
import './DataManager.css';

// ─── Constants ────────────────────────────────────────────────────────────────
const DAYS = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT'];

// ─── Main component ───────────────────────────────────────────────────────────
const DataManager = () => {
    const { isTimetabler } = useAuth();

    // Hierarchy selection state
    const [schools, setSchools] = useState([]);
    const [selSchool, setSelSchool] = useState(null);  // { id, name, code }
    const [depts, setDepts] = useState([]);
    const [selDept, setSelDept] = useState(null);
    const [courses, setCourses] = useState([]);
    const [selCourse, setSelCourse] = useState(null);
    const [units, setUnits] = useState([]);      // units in selected course
    const [allUnits, setAllUnits] = useState([]);      // global unit catalogue

    const [loading, setLoading] = useState(false);
    const [modal, setModal] = useState(null);    // { type, item }
    const [formData, setFormData] = useState({});
    const [formError, setFormError] = useState('');
    const [savingLink, setSavingLink] = useState(null);    // unit_id being linked

    // ── Load helpers ──────────────────────────────────────────────────────────
    const loadSchools = useCallback(async () => {
        const res = await api.get('/schools/');
        setSchools(res.data || []);
    }, []);

    const loadDepts = useCallback(async (schoolId) => {
        const res = await api.get(`/schools/${schoolId}/departments/`);
        setDepts(res.data || []);
    }, []);

    const loadCourses = useCallback(async (deptId) => {
        const res = await api.get(`/departments/${deptId}/courses/`);
        setCourses(res.data || []);
    }, []);

    const loadUnits = useCallback(async (courseId) => {
        const res = await api.get(`/courses/${courseId}/units/`);
        setUnits(res.data || []);
    }, []);

    const loadAllUnits = useCallback(async () => {
        const res = await api.get('/units/');
        setAllUnits(res.data || []);
    }, []);

    useEffect(() => { loadSchools(); loadAllUnits(); }, []);
    useEffect(() => { if (selSchool) loadDepts(selSchool.id); else { setDepts([]); setSelDept(null); } }, [selSchool]);
    useEffect(() => { if (selDept) loadCourses(selDept.id); else { setCourses([]); setSelCourse(null); } }, [selDept]);
    useEffect(() => { if (selCourse) loadUnits(selCourse.id); else setUnits([]); }, [selCourse]);

    // ── Modal helpers ─────────────────────────────────────────────────────────
    const openModal = (type, item = null) => { setModal({ type, item }); setFormData(item ? { ...item } : {}); setFormError(''); };
    const closeModal = () => { setModal(null); setFormData({}); setFormError(''); };

    const onChange = e => setFormData(p => ({ ...p, [e.target.name]: e.target.value }));

    const saveEntity = async () => {
        try {
            setFormError('');
            const { type, item } = modal;
            const ep = { school: 'schools', department: 'departments', course: 'courses', unit: 'units' };

            if (item?.id) {
                await api.put(`/${ep[type]}/${item.id}/`, formData);
            } else {
                await api.post(`/${ep[type]}/`, formData);
            }

            closeModal();
            // Refresh the right level
            if (type === 'school') { loadSchools(); }
            if (type === 'department') { if (selSchool) loadDepts(selSchool.id); }
            if (type === 'course') { if (selDept) loadCourses(selDept.id); }
            if (type === 'unit') { loadAllUnits(); }
        } catch (err) {
            const data = err.response?.data;
            if (data && typeof data === 'object' && !data.error && !data.detail) {
                // It's likely a serializer error dict { field: [msg] }
                const msgs = Object.entries(data).map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(', ') : v}`);
                setFormError(msgs.join(' | '));
            } else {
                const mainErr = data?.error || data?.detail || err.message;
                const trace = data?.trace ? `\nTrace: ${data.trace.split('\n')[0]}...` : '';
                setFormError(mainErr + trace);
            }
        }
    };

    const deleteEntity = async (type, id) => {
        if (!window.confirm('Delete this item? This cannot be undone.')) return;
        const ep = { school: 'schools', department: 'departments', course: 'courses', unit: 'units' };
        await api.delete(`/${ep[type]}/${id}/`);
        if (type === 'school') { setSelSchool(null); loadSchools(); }
        if (type === 'department') { setSelDept(null); if (selSchool) loadDepts(selSchool.id); }
        if (type === 'course') { setSelCourse(null); if (selDept) loadCourses(selDept.id); }
        if (type === 'unit') { loadAllUnits(); }
    };

    // Link / unlink unit → course
    const linkUnit = async (unitId) => {
        if (!selCourse) return;
        setSavingLink(unitId);
        try {
            await api.post(`/courses/${selCourse.id}/units/${unitId}/`, {});
            await loadUnits(selCourse.id);
        } catch (err) {
            alert(err.response?.data?.detail || err.message);
        } finally {
            setSavingLink(null);
        }
    };

    const unlinkUnit = async (unitId) => {
        if (!selCourse || !window.confirm('Remove this unit from the course?')) return;
        await api.delete(`/courses/${selCourse.id}/units/${unitId}/unlink/`);
        loadUnits(selCourse.id);
    };

    const linkedUnitIds = new Set(units.map(u => u.unit_id));

    // ─────────────────────────────────────────────────────────────────────────
    return (
        <div className="data-manager">
            {/* ── Schools column ── */}
            <HierarchyColumn
                title="Schools"
                icon="🏛️"
                items={schools}
                selected={selSchool}
                onSelect={s => { setSelSchool(s); setSelDept(null); setSelCourse(null); }}
                onAdd={isTimetabler ? () => openModal('school') : null}
                onEdit={isTimetabler ? s => openModal('school', s) : null}
                onDelete={isTimetabler ? id => deleteEntity('school', id) : null}
                primaryKey="name"
                secondaryKey="code"
                emptyMsg="No schools yet"
            />

            {/* ── Departments column ── */}
            <HierarchyColumn
                title={selSchool ? `Departments — ${selSchool.code}` : 'Departments'}
                icon="🏢"
                items={depts}
                selected={selDept}
                onSelect={d => { setSelDept(d); setSelCourse(null); }}
                onAdd={isTimetabler && selSchool ? () => openModal('department', { school: selSchool.id }) : null}
                onEdit={isTimetabler ? d => openModal('department', d) : null}
                onDelete={isTimetabler ? id => deleteEntity('department', id) : null}
                primaryKey="name"
                secondaryKey="code"
                dimmed={!selSchool}
                emptyMsg={selSchool ? 'No departments in this school' : '← Select a school'}
            />

            {/* ── Courses column ── */}
            <HierarchyColumn
                title={selDept ? `Courses — ${selDept.code}` : 'Courses'}
                icon="📚"
                items={courses}
                selected={selCourse}
                onSelect={c => setSelCourse(c)}
                onAdd={isTimetabler && selDept ? () => openModal('course', { department: selDept.id }) : null}
                onEdit={isTimetabler ? c => openModal('course', c) : null}
                onDelete={isTimetabler ? id => deleteEntity('course', id) : null}
                primaryKey="name"
                secondaryKey="code"
                dimmed={!selDept}
                emptyMsg={selDept ? 'No courses in this department' : '← Select a department'}
            />

            {/* ── Units column (two halves: linked + global catalogue) ── */}
            <div className="hcol hcol-units">
                {/* Linked units */}
                <div className="hcol-top">
                    <div className="hcol-header">
                        <span>📋 Units in <em>{selCourse?.code || '…'}</em></span>
                        {isTimetabler && selCourse && (
                            <button className="hcol-add-btn" onClick={() => openModal('unit')}>+ New Unit</button>
                        )}
                    </div>
                    {!selCourse ? (
                        <p className="hcol-empty">← Select a course</p>
                    ) : units.length === 0 ? (
                        <p className="hcol-empty">No units linked yet. Link from the catalogue below.</p>
                    ) : (
                        <ul className="hcol-list">
                            {units.map(u => (
                                <li key={u.unit_id} className="hcol-item linked-unit">
                                    <div className="hcol-item-body">
                                        <span className="hcol-code">{u.code}</span>
                                        <span className="hcol-name">{u.name}</span>
                                        <span className="hcol-meta">Yr {u.year_of_study} · Sem {u.semester} · {u.credits} cr</span>
                                    </div>
                                    {isTimetabler && (
                                        <button className="hcol-unlink-btn" onClick={() => unlinkUnit(u.unit_id)} title="Unlink">×</button>
                                    )}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>

                {/* Global unit catalogue */}
                <div className="hcol-bottom">
                    <div className="hcol-header sub">
                        <span>🌐 Unit Catalogue</span>
                    </div>
                    {allUnits.length === 0 ? (
                        <p className="hcol-empty">No units yet. Create one above.</p>
                    ) : (
                        <ul className="hcol-list catalogue">
                            {allUnits.map(u => {
                                const isLinked = linkedUnitIds.has(u.id);
                                return (
                                    <li key={u.id} className={`hcol-item catalogue-unit ${isLinked ? 'is-linked' : ''}`}>
                                        <div className="hcol-item-body" onClick={() => isTimetabler && openModal('unit', u)}>
                                            <span className="hcol-code">{u.code}</span>
                                            <span className="hcol-name">{u.name}</span>
                                            <span className="hcol-meta">{u.credits} cr · {u.hours_per_week}h/wk</span>
                                        </div>
                                        <div className="catalogue-actions">
                                            {isTimetabler && selCourse && !isLinked && (
                                                <button
                                                    className="hcol-link-btn"
                                                    onClick={() => linkUnit(u.id)}
                                                    disabled={savingLink === u.id}
                                                    title="Link to selected course"
                                                >
                                                    {savingLink === u.id ? '…' : '＋'}
                                                </button>
                                            )}
                                            {isLinked && <span className="linked-badge">✓ linked</span>}
                                            {isTimetabler && (
                                                <button className="hcol-del-btn" onClick={() => deleteEntity('unit', u.id)}>🗑️</button>
                                            )}
                                        </div>
                                    </li>
                                );
                            })}
                        </ul>
                    )}
                </div>
            </div>

            {/* ── File upload strip ── */}
            {isTimetabler && (
                <div className="dm-upload-strip">
                    <FileUpload onUpload={() => { loadSchools(); loadAllUnits(); }} />
                </div>
            )}

            {/* ── Modal ── */}
            {modal && (
                <HierarchyModal
                    modal={modal}
                    formData={formData}
                    formError={formError}
                    onChange={onChange}
                    onSave={saveEntity}
                    onClose={closeModal}
                    schools={schools}
                    depts={depts}
                />
            )}
        </div>
    );
};

// ─── Reusable column component ────────────────────────────────────────────────
const HierarchyColumn = ({
    title, icon, items, selected, onSelect,
    onAdd, onEdit, onDelete, primaryKey, secondaryKey,
    dimmed, emptyMsg,
}) => (
    <div className={`hcol ${dimmed ? 'hcol-dimmed' : ''}`}>
        <div className="hcol-header">
            <span>{icon} {title} <em className="hcol-count">({items.length})</em></span>
            {onAdd && <button className="hcol-add-btn" onClick={onAdd}>＋</button>}
        </div>

        {items.length === 0 ? (
            <p className="hcol-empty">{emptyMsg}</p>
        ) : (
            <ul className="hcol-list">
                {items.map(item => (
                    <li
                        key={item.id}
                        className={`hcol-item ${selected?.id === item.id ? 'selected' : ''}`}
                        onClick={() => onSelect(item)}
                    >
                        <div className="hcol-item-body">
                            <span className="hcol-code">{item[secondaryKey]}</span>
                            <span className="hcol-name">{item[primaryKey]}</span>
                        </div>
                        {(onEdit || onDelete) && (
                            <div className="hcol-item-actions" onClick={e => e.stopPropagation()}>
                                {onEdit && <button onClick={() => onEdit(item)} className="hcol-edit-btn">✏️</button>}
                                {onDelete && <button onClick={() => onDelete(item.id)} className="hcol-del-btn">🗑️</button>}
                            </div>
                        )}
                    </li>
                ))}
            </ul>
        )}
    </div>
);

// ─── Modal ────────────────────────────────────────────────────────────────────
const HierarchyModal = ({ modal, formData, formError, onChange, onSave, onClose, schools, depts }) => {
    const { type, item } = modal;
    const isEdit = !!item?.id;

    const labels = {
        school: 'School', department: 'Department',
        course: 'Course', unit: 'Unit',
    };

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{isEdit ? '✏️ Edit' : '➕ Add'} {labels[type]}</h2>
                    <button className="modal-close" onClick={onClose}>✕</button>
                </div>

                {formError && <div className="error-message">{formError}</div>}

                <div className="modal-form">
                    {type === 'school' && (
                        <>
                            <F label="School Name"><input name="name" value={formData.name || ''} onChange={onChange} required placeholder="e.g. School of Computing" /></F>
                            <F label="Code"><input name="code" value={formData.code || ''} onChange={onChange} required placeholder="e.g. SCC" disabled={isEdit} /></F>
                            <F label="Description"><textarea name="description" value={formData.description || ''} onChange={onChange} rows={2} /></F>
                            <F label="Contact Email"><input type="email" name="contact_email" value={formData.contact_email || ''} onChange={onChange} /></F>
                        </>
                    )}

                    {type === 'department' && (
                        <>
                            <F label="School">
                                <select name="school" value={formData.school || ''} onChange={onChange} required>
                                    <option value="">Select School</option>
                                    {schools.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
                                </select>
                            </F>
                            <F label="Department Name"><input name="name" value={formData.name || ''} onChange={onChange} required placeholder="e.g. Computer Science" /></F>
                            <F label="Code"><input name="code" value={formData.code || ''} onChange={onChange} required placeholder="e.g. CS" disabled={isEdit} /></F>
                            <F label="Head of Department"><input name="head_of_department" value={formData.head_of_department || ''} onChange={onChange} /></F>
                            <F label="Email"><input type="email" name="email" value={formData.email || ''} onChange={onChange} /></F>
                        </>
                    )}

                    {type === 'course' && (
                        <>
                            <F label="Department">
                                <select name="department" value={formData.department || ''} onChange={onChange} required>
                                    <option value="">Select Department</option>
                                    {depts.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
                                </select>
                            </F>
                            <F label="Course Name"><input name="name" value={formData.name || ''} onChange={onChange} required placeholder="e.g. Bachelor of IT Year 2" /></F>
                            <F label="Code"><input name="code" value={formData.code || ''} onChange={onChange} required placeholder="e.g. BIT-Y2" disabled={isEdit} /></F>
                            <F label="Semester"><input type="number" name="semester" value={formData.semester || 1} onChange={onChange} min="1" max="8" /></F>
                            <F label="Credits"><input type="number" name="credits" value={formData.credits || 3} onChange={onChange} min="1" max="10" /></F>
                            <F label="Description"><textarea name="description" value={formData.description || ''} onChange={onChange} rows={2} /></F>
                        </>
                    )}

                    {type === 'unit' && (
                        <>
                            <F label="Unit Code"><input name="code" value={formData.code || ''} onChange={onChange} required placeholder="e.g. BCIT 1202" disabled={isEdit} /></F>
                            <F label="Unit Name"><input name="name" value={formData.name || ''} onChange={onChange} required placeholder="e.g. Data Communication" /></F>
                            <F label="Credits"><input type="number" name="credits" value={formData.credits || 3} onChange={onChange} min="1" max="10" /></F>
                            <F label="Hours / Week"><input type="number" name="hours_per_week" value={formData.hours_per_week || 3} onChange={onChange} min="1" /></F>
                            <F label="Description"><textarea name="description" value={formData.description || ''} onChange={onChange} rows={2} /></F>
                        </>
                    )}

                    <div className="form-actions">
                        <button className="btn btn-primary" onClick={onSave}>Save</button>
                        <button className="btn btn-secondary" onClick={onClose}>Cancel</button>
                    </div>
                </div>
            </div>
        </div>
    );
};

const F = ({ label, children }) => (
    <div className="form-field">
        <label>{label}</label>
        {children}
    </div>
);

export default DataManager;
