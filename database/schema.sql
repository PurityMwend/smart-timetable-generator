-- MySQL database schema for Smart Timetable Generator
-- Reference only — Django migrations are the source of truth.

CREATE DATABASE IF NOT EXISTS timetable_db;
USE timetable_db;

-- Departments
CREATE TABLE IF NOT EXISTS timetable_app_department (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL UNIQUE,
    code VARCHAR(10) NOT NULL UNIQUE
);

-- Courses
CREATE TABLE IF NOT EXISTS timetable_app_course (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    code VARCHAR(20) NOT NULL UNIQUE,
    department_id BIGINT NOT NULL,
    year_of_study SMALLINT UNSIGNED NOT NULL,
    study_mode VARCHAR(15) NOT NULL DEFAULT 'IN_PERSON',
    class_size INT UNSIGNED NOT NULL,
    hours_per_week DECIMAL(4,1) NOT NULL DEFAULT 3.0,
    FOREIGN KEY (department_id) REFERENCES timetable_app_department(id)
);

-- Lecturers
CREATE TABLE IF NOT EXISTS timetable_app_lecturer (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    employee_id VARCHAR(30) NOT NULL UNIQUE,
    email VARCHAR(254),
    department_id BIGINT NOT NULL,
    FOREIGN KEY (department_id) REFERENCES timetable_app_department(id)
);

-- Rooms
CREATE TABLE IF NOT EXISTS timetable_app_room (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    building VARCHAR(100),
    capacity INT UNSIGNED NOT NULL,
    room_type VARCHAR(20) NOT NULL DEFAULT 'CLASSROOM',
    UNIQUE (building, name)
);

-- Time Slots
CREATE TABLE IF NOT EXISTS timetable_app_timeslot (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    day VARCHAR(3) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    UNIQUE (day, start_time, end_time)
);

-- Lecturer Availability
CREATE TABLE IF NOT EXISTS timetable_app_lectureravailability (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    lecturer_id BIGINT NOT NULL,
    time_slot_id BIGINT NOT NULL,
    is_available BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (lecturer_id, time_slot_id),
    FOREIGN KEY (lecturer_id) REFERENCES timetable_app_lecturer(id),
    FOREIGN KEY (time_slot_id) REFERENCES timetable_app_timeslot(id)
);

-- Timetable Entries
CREATE TABLE IF NOT EXISTS timetable_app_timetableentry (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    course_id BIGINT NOT NULL,
    lecturer_id BIGINT NOT NULL,
    room_id BIGINT NOT NULL,
    time_slot_id BIGINT NOT NULL,
    is_locked BOOLEAN NOT NULL DEFAULT FALSE,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    UNIQUE (room_id, time_slot_id),
    UNIQUE (lecturer_id, time_slot_id),
    FOREIGN KEY (course_id) REFERENCES timetable_app_course(id),
    FOREIGN KEY (lecturer_id) REFERENCES timetable_app_lecturer(id),
    FOREIGN KEY (room_id) REFERENCES timetable_app_room(id),
    FOREIGN KEY (time_slot_id) REFERENCES timetable_app_timeslot(id)
);
