import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './context/AuthContext'
import Navbar from './components/Navbar'
import PrivateRoute from './components/PrivateRoute'
import Login from './pages/Login'
import Register from './pages/Register'
import ApiDebug from './pages/ApiDebug'
import Dashboard from './pages/Dashboard'
import DataManager from './pages/DataManager'
import TrainingData from './pages/TrainingData'
import TimetableGenerator from './pages/TimetableGenerator'
import TimetableViewer from './pages/TimetableViewer'
import UploadSampleData from './pages/UploadSampleData'
import './App.css'

function App() {
    return (
        <Router>
            <AuthProvider>
                <Navbar />
                <Routes>
                    {/* Public Routes */}
                    <Route path="/login" element={<Login />} />
                    <Route path="/register" element={<Register />} />
                    <Route path="/debug" element={<ApiDebug />} />

                    {/* Protected Routes */}
                    <Route
                        path="/"
                        element={
                            <PrivateRoute>
                                <Dashboard />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/data"
                        element={
                            <PrivateRoute>
                                <DataManager />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/training-data"
                        element={
                            <PrivateRoute>
                                <TrainingData />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/generate"
                        element={
                            <PrivateRoute>
                                <TimetableGenerator />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/view"
                        element={
                            <PrivateRoute>
                                <TimetableViewer />
                            </PrivateRoute>
                        }
                    />
                    <Route
                        path="/upload"
                        element={
                            <PrivateRoute>
                                <UploadSampleData />
                            </PrivateRoute>
                        }
                    />
                </Routes>
            </AuthProvider>
        </Router>
    )
}

export default App
