import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Dashboard from './pages/Dashboard'
import DataManager from './pages/DataManager'
import TimetableGenerator from './pages/TimetableGenerator'
import TimetableViewer from './pages/TimetableViewer'
import './App.css'

function App() {
    return (
        <Router>
            <Navbar />
            <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/data" element={<DataManager />} />
                <Route path="/generate" element={<TimetableGenerator />} />
                <Route path="/view" element={<TimetableViewer />} />
            </Routes>
        </Router>
    )
}

export default App
