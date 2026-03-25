import { Link } from 'react-router-dom';
import './Navbar.css';

const Navbar = () => {
    return (
        <nav className="navbar">
            <div className="navbar-brand">
                <Link to="/" className="brand-link">
                    <span className="brand-icon">⏱️</span>
                    Smart Timetable Generator
                </Link>
            </div>
            <ul className="navbar-nav">
                <li><Link to="/" className="nav-link">Dashboard</Link></li>
                <li><Link to="/data" className="nav-link">Manage Data</Link></li>
                <li><Link to="/generate" className="nav-link">Generate Timetable</Link></li>
                <li><Link to="/view" className="nav-link">View Timetable</Link></li>
            </ul>
        </nav>
    );
};

export default Navbar;