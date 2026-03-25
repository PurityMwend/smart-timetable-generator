import { useState } from 'react';
import api from '../services/api';
import './TimetableGenerator.css';

const TimetableGenerator = () => {
    const [generating, setGenerating] = useState(false);
    const [message, setMessage] = useState('');

    const handleGenerate = async () => {
        setGenerating(true);
        setMessage('Generating timetable...');
        try {
            const response = await api.post('/generate-timetable/');
            setMessage('Timetable generated successfully!');
        } catch (error) {
            setMessage('Error generating timetable. Please try again.');
            console.error('Generation error:', error);
        } finally {
            setGenerating(false);
        }
    };

    return (
        <div className="timetable-generator container">
            <h1>Generate Timetable</h1>
            <div className="card">
                <p>Click the button below to generate a conflict-free timetable based on your data.</p>
                <button
                    className="btn btn-primary"
                    onClick={handleGenerate}
                    disabled={generating}
                >
                    {generating ? 'Generating...' : 'Generate Timetable'}
                </button>
                {message && <p className="message">{message}</p>}
            </div>
        </div>
    );
};

export default TimetableGenerator;