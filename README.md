# UniTrack – An Academic Progress Tracker

UniTrack is a full-stack web application built with **Flask** and **SQLite** that helps students manage semesters, courses, tasks, and grades. Track your academic progress easily with a clean, intuitive interface.



## Features

- Manage **semesters**, **courses**, and **tasks** (full CRUD functionality)
- Real-time **grade calculations** (earned, remaining, course average)
- Sort tasks by **due date**, **course**, or **status**
- REST-style routes with proper **GET/POST** HTTP methods
- Dark mode toggle using localStorage for improved user experience
- Upload a course syllabus (PDF) to automatically extract tasks, due dates, and weights using text parsing and pattern recognition



## Technologies Used
- **Python** (Flask 3.0.0)  
- **HTML / CSS / JavaScript**  
- **SQLite**  
- **pdfplumber & regex (PDF parsing)**



## How to Run

```bash
# 1. Install Python 3.x

# 2. Install dependencies
pip install -r requirements.txt

# 3. Initialize the database
python init_db.py

# 4. Start the application
python app.py

# 5. Open a browser and go to: `http://127.0.0.1:5000`
```