# Smart Timetable Generator

> Automated, conflict-free university lecture scheduling — built with Django, React, and MySQL.

## Overview

A web-based application that helps university administrators generate weekly lecture timetables. The system uses a constraint-satisfaction algorithm to automatically schedule lectures while preventing room and lecturer conflicts, with a human-in-the-loop interface for manual adjustments.

## Tech Stack

| Layer      | Technology                     |
|------------|--------------------------------|
| Backend    | Python 3.11 · Django 4.2 · DRF |
| Frontend   | React 18 · Vite · Axios       |
| Database   | MySQL 8.0 (SQLite for dev)     |
| Containers | Docker · Docker Compose        |

## Quick Start (Local Development)

### Backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Linux/macOS
pip install -r requirements.txt

# Uses SQLite by default — no MySQL needed for local dev
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open [http://localhost:8000/admin/](http://localhost:8000/admin/) to access the Django admin.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173/](http://localhost:5173/) to view the app.

### Docker (Full Stack)

```bash
docker-compose up --build
```

## Project Structure

```
smart-timetable-generator/
├── backend/
│   ├── timetable_project/   # Django project settings
│   ├── timetable_app/       # Models, views, serializers, URLs
│   ├── manage.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Reusable UI components
│   │   ├── pages/           # Page-level components
│   │   ├── services/        # API layer (Axios)
│   │   ├── context/         # React context providers
│   │   └── utils/           # Helpers
│   ├── vite.config.js
│   └── package.json
├── database/
│   └── schema.sql
├── docs/                    # Project documentation
├── tests/                   # Backend & frontend tests
├── docker-compose.yml
└── .env.example
```

## API Endpoints

All endpoints are prefixed with `/api/`:

| Resource                | URL                          |
|-------------------------|------------------------------|
| Departments             | `/api/departments/`          |
| Courses                 | `/api/courses/`              |
| Lecturers               | `/api/lecturers/`            |
| Rooms                   | `/api/rooms/`                |
| Time Slots              | `/api/timeslots/`            |
| Lecturer Availability   | `/api/lecturer-availability/`|
| Timetable Entries       | `/api/timetable-entries/`    |

## License

MIT
