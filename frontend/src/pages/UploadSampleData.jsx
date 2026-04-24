import { useState, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';
import './UploadSampleData.css';

const UploadSampleData = () => {
    const navigate = useNavigate();
    const fileInputRef = useRef(null);
    const [dragOver, setDragOver] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState(null);  // { message, summary }
    const [error, setError] = useState(null);
    const [selectedFile, setSelectedFile] = useState(null);

    const ACCEPTED = '.xlsx,.xls,.pdf';

    // ------------------------------------------------------------------ drag & drop
    const handleDragOver = useCallback((e) => {
        e.preventDefault();
        setDragOver(true);
    }, []);
    const handleDragLeave = useCallback(() => setDragOver(false), []);
    const handleDrop = useCallback((e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files[0];
        if (file) handleFileSelected(file);
    }, []);

    const handleFileSelected = (file) => {
        const name = file.name.toLowerCase();
        if (!name.endsWith('.xlsx') && !name.endsWith('.xls') && !name.endsWith('.pdf')) {
            setError('Only .xlsx, .xls, or .pdf files are supported.');
            return;
        }
        setSelectedFile(file);
        setError(null);
        setResult(null);
    };

    // ------------------------------------------------------------------ upload
    const handleUpload = async () => {
        if (!selectedFile) return;
        setUploading(true);
        setError(null);
        setResult(null);

        const formData = new FormData();
        formData.append('file', selectedFile);

        try {
            const res = await api.post('/upload-sample-data/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setResult(res.data);
        } catch (err) {
            const data = err.response?.data;
            setError(data?.error || 'Upload failed. Please check your file format.');
            if (data?.summary) setResult(data);   // still show partial summary
        } finally {
            setUploading(false);
        }
    };

    // ------------------------------------------------------------------ template download
    const handleDownloadTemplate = () => {
        // Open the static template served by backend
        window.open('/api/sample-template/', '_blank');
    };

    // ------------------------------------------------------------------ render helpers
    const SummaryCard = ({ label, count, color }) => (
        <div className="summary-card" style={{ '--card-color': color }}>
            <span className="summary-count">{count}</span>
            <span className="summary-label">{label}</span>
        </div>
    );

    const summary = result?.summary;

    return (
        <div className="upload-page container">
            {/* Header */}
            <div className="upload-header">
                <div className="upload-header-icon">📂</div>
                <div>
                    <h1>Upload Sample Data</h1>
                    <p className="subtitle">
                        Import your school data (departments, lecturers, rooms, courses) from an
                        Excel or PDF file to seed the database for timetable generation.
                    </p>
                </div>
            </div>

            {/* Template hint */}
            <div className="template-hint">
                <span>📋 Don't have a file yet?</span>
                <button className="btn-link" onClick={handleDownloadTemplate}>
                    Download sample template ↓
                </button>
                <span className="hint-note">
                    (Sheets: Schools · Departments · Programs · Lecturers · Rooms · TimeSlots · Courses)
                </span>
            </div>

            {/* Drop zone */}
            <div
                id="drop-zone"
                className={`drop-zone ${dragOver ? 'drag-over' : ''} ${selectedFile ? 'has-file' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept={ACCEPTED}
                    style={{ display: 'none' }}
                    onChange={(e) => e.target.files[0] && handleFileSelected(e.target.files[0])}
                />
                {selectedFile ? (
                    <div className="file-selected">
                        <span className="file-icon">
                            {selectedFile.name.endsWith('.pdf') ? '📄' : '📊'}
                        </span>
                        <div>
                            <p className="file-name">{selectedFile.name}</p>
                            <p className="file-size">{(selectedFile.size / 1024).toFixed(1)} KB</p>
                        </div>
                        <button
                            className="change-file"
                            onClick={(e) => { e.stopPropagation(); setSelectedFile(null); setResult(null); setError(null); }}
                        >✕</button>
                    </div>
                ) : (
                    <>
                        <div className="drop-icon">⬆️</div>
                        <p className="drop-title">Drag & drop your file here</p>
                        <p className="drop-sub">or <strong>click to browse</strong> — .xlsx, .xls, .pdf accepted</p>
                    </>
                )}
            </div>

            {/* Error */}
            {error && (
                <div className="upload-error">
                    <span>⚠️</span> {error}
                </div>
            )}

            {/* Actions */}
            <div className="upload-actions">
                <button
                    id="upload-btn"
                    className="btn btn-primary upload-btn"
                    disabled={!selectedFile || uploading}
                    onClick={handleUpload}
                >
                    {uploading ? (
                        <><span className="spinner" />  Parsing & Importing...</>
                    ) : 'Upload & Import Data'}
                </button>
            </div>

            {/* Parse result summary */}
            {summary && (
                <div className="parse-result">
                    <div className="parse-result-header">
                        <span className="parse-icon">✅</span>
                        <h2>Import Summary</h2>
                    </div>
                    <p className="parse-message">{result.message || result.error}</p>

                    <div className="summary-cards">
                        <SummaryCard label="Schools" count={summary.created?.schools || 0} color="#1a73e8" />
                        <SummaryCard label="Departments" count={summary.created?.departments || 0} color="#34a853" />
                        <SummaryCard label="Programs" count={summary.created?.programs || 0} color="#fbbc04" />
                        <SummaryCard label="Lecturers" count={summary.created?.lecturers || 0} color="#ea4335" />
                        <SummaryCard label="Rooms" count={summary.created?.rooms || 0} color="#9334e8" />
                        <SummaryCard label="Time Slots" count={summary.created?.time_slots || 0} color="#00bfa5" />
                        <SummaryCard label="Courses" count={summary.created?.courses || 0} color="#ff6d00" />
                    </div>

                    {/* Errors table */}
                    {summary.errors?.length > 0 && (
                        <div className="parse-errors">
                            <h3>⚠️ {summary.error_count} rows had issues</h3>
                            <table>
                                <thead>
                                    <tr><th>#</th><th>Row</th><th>Error</th></tr>
                                </thead>
                                <tbody>
                                    {summary.errors.map((err, i) => (
                                        <tr key={i}>
                                            <td>{i + 1}</td>
                                            <td className="err-row">{err.row}</td>
                                            <td className="err-msg">{err.error}</td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}

                    {/* CTA */}
                    <div className="parse-cta">
                        <button className="btn btn-primary" onClick={() => navigate('/generate')}>
                            Proceed to Generate Timetable →
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
};

export default UploadSampleData;
