import { useState } from 'react';
import api from '../services/api';
import './FileUpload.css';

const FileUpload = ({ onUpload }) => {
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [message, setMessage] = useState('');

    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };

    const handleUpload = async () => {
        if (!file) return;
        setUploading(true);
        setMessage('');
        const formData = new FormData();
        formData.append('file', file);
        try {
            const response = await api.post('/upload-data/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            setMessage('Data uploaded successfully!');
            if (onUpload) onUpload();
        } catch (error) {
            setMessage('Error uploading file. Please try again.');
            console.error('Upload error:', error);
        } finally {
            setUploading(false);
        }
    };

    return (
        <div className="file-upload">
            <h3>Upload Data from Excel/PDF</h3>
            <input type="file" accept=".xlsx,.pdf" onChange={handleFileChange} />
            <button
                className="btn btn-primary"
                onClick={handleUpload}
                disabled={!file || uploading}
            >
                {uploading ? 'Uploading...' : 'Upload'}
            </button>
            {message && <p className="message">{message}</p>}
        </div>
    );
};

export default FileUpload;