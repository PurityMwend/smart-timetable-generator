import { useState } from 'react';
import api from '../services/api';
import './TimetableGenerator.css';

const TimetableGenerator = () => {
    const [generating, setGenerating] = useState(false);
    const [progress, setProgress] = useState(0);
    const [currentStep, setCurrentStep] = useState('');
    const [message, setMessage] = useState('');

    const steps = [
        'Analyzing constraints and data...',
        'Training AI model on pre-existing patterns...',
        'Optimizing timetable with machine learning...',
        'Applying constraint satisfaction...',
        'Finalizing schedule...'
    ];

    const handleGenerate = async () => {
        setGenerating(true);
        setProgress(0);
        setMessage('');

        // Simulate progress steps
        for (let i = 0; i < steps.length; i++) {
            setCurrentStep(steps[i]);
            setProgress((i + 1) * 20);
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        try {
            const response = await api.post('/generate-timetable/');
            setMessage('Timetable generated successfully using AI optimization!');
            setProgress(100);
        } catch (error) {
            setMessage('Error generating timetable. Please try again.');
            console.error('Generation error:', error);
            setProgress(0);
        } finally {
            setGenerating(false);
            setCurrentStep('');
        }
    };

    return (
        <div className="timetable-generator container">
            <h1>AI-Powered Timetable Generator</h1>
            <div className="card">
                <p>Upload your constraints via the Data Manager, then click below to generate an optimized timetable using advanced AI algorithms.</p>
                <p>The system learns from pre-trained models and your specific data to create conflict-free, efficient schedules.</p>

                {generating && (
                    <div className="progress-container">
                        <div className="progress-bar">
                            <div
                                className="progress-fill"
                                style={{ width: `${progress}%` }}
                            ></div>
                        </div>
                        <p className="progress-text">{currentStep}</p>
                    </div>
                )}

                <button
                    className="btn btn-primary"
                    onClick={handleGenerate}
                    disabled={generating}
                >
                    {generating ? 'Generating with AI...' : 'Generate Timetable with AI'}
                </button>
                {message && <p className={`message ${message.includes('Error') ? 'error' : 'success'}`}>{message}</p>}
            </div>
        </div>
    );
};

export default TimetableGenerator;