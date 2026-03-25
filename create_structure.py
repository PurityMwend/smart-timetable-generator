import os

# Define the folder structure
folders = [
    "backend/timetable_project",
    "backend/timetable_app",
    "frontend/public",
    "frontend/src",
    "docs/proposal",
    "docs/requirements",
    "docs/design",
    "docs/user-manual",
    "database/sample_data",
    "tests/backend",
    "tests/frontend"
]

# Define files to create
files = [
    "backend/requirements.txt",
    "backend/manage.py",
    "frontend/package.json",
    "frontend/README.md",
    "database/schema.sql",
    ".gitignore",
    "README.md",
    "LICENSE",
    "docker-compose.yml"
]

# Get the current directory (should be your cloned repo)
current_dir = os.getcwd()
print(f"Working in directory: {current_dir}")

# Verify we're in the right place
if not os.path.basename(current_dir) == "smart-timetable-generator":
    response = input(f"Current directory is '{os.path.basename(current_dir)}'. Are you sure you want to create structure here? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Operation cancelled.")
        exit()

# Create folders
print("\n📁 Creating folders...")
for folder in folders:
    folder_path = os.path.join(current_dir, folder)
    os.makedirs(folder_path, exist_ok=True)
    print(f"  ✅ Created/Verified folder: {folder}")

# Create files (without overwriting existing ones)
print("\n📄 Creating files...")
for file in files:
    file_path = os.path.join(current_dir, file)
    
    # Check if file already exists
    if os.path.exists(file_path):
        print(f"  ⏭️  Skipped (already exists): {file}")
        continue
    
    # Create directory for file if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Create file with appropriate content
    with open(file_path, 'w') as f:
        if file == "README.md":
            f.write("# Smart Timetable Generator\n\nYour project description here.")
        elif file == ".gitignore":
            f.write("""# Python
__pycache__/
*.py[cod]
*.so
.Python

# Django
*.log
local_settings.py
db.sqlite3
media/

# React
node_modules/
build/
.env
.env.local
*.cache

# Environment
.env
.venv
venv/
ENV/
env/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Project specific
*.sqlite3
*.bak
*.pid
""")
        elif file == "docker-compose.yml":
            f.write("""version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - '8000:8000'
    volumes:
      - ./backend:/app
    environment:
      - DEBUG=1
    depends_on:
      - database

  frontend:
    build: ./frontend
    ports:
      - '3000:3000'
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000

  database:
    image: mysql:8.0
    ports:
      - '3306:3306'
    environment:
      - MYSQL_DATABASE=timetable_db
      - MYSQL_ROOT_PASSWORD=rootpassword
    volumes:
      - ./database:/docker-entrypoint-initdb.d
""")
        elif file == "LICENSE":
            f.write("""MIT License

Copyright (c) 2024 Smart Timetable Generator

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files...
""")
        elif file == "backend/requirements.txt":
            f.write("""Django==4.2.0
djangorestframework==3.14.0
mysqlclient==2.1.1
python-decouple==3.8
""")
        elif file == "backend/manage.py":
            f.write("""#!/usr/bin/env python
\"\"\"Django's command-line utility for administrative tasks.\"\"\"
import os
import sys


def main():
    \"\"\"Run administrative tasks.\"\"\"
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timetable_project.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
""")
        elif file == "frontend/package.json":
            f.write("""{
  "name": "smart-timetable-frontend",
  "version": "0.1.0",
  "private": true,
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "axios": "^1.4.0"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject"
  }
}
""")
        elif file == "database/schema.sql":
            f.write("""-- MySQL database schema for Smart Timetable Generator
CREATE DATABASE IF NOT EXISTS timetable_db;
USE timetable_db;

-- Add your table definitions here
-- This file will be automatically executed when the MySQL container starts
""")
        else:
            f.write("")  # Empty file for others
    
    print(f"  ✅ Created: {file}")

# Summary
print("\n" + "="*50)
print("✅ STRUCTURE CREATION COMPLETE!")
print("="*50)
print(f"\nLocation: {current_dir}")
print("\nFolders created/verified:")
for folder in folders:
    print(f"  • {folder}")

print("\nFiles created:")
for file in files:
    file_path = os.path.join(current_dir, file)
    if os.path.exists(file_path):
        print(f"  • {file}")

print("\n📝 Next steps:")
print("1. Review the created files")
print("2. Add your proposal PDFs to docs/proposal/")
print("3. Run 'git status' to see changes")
print("4. Commit the new structure: git add . && git commit -m 'Add project structure'")

