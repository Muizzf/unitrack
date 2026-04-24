# UniTrack – An Academic Progress Tracker

UniTrack is a full-stack web application built with **Flask** that helps students manage semesters, courses, and assignments while automatically tracking academic performance through real-time grade calculations. Track your academic progress easily with a clean, intuitive interface.

UniTrack is deployed and fully accessible online:

👉🔗 https://unitrack-tbu9.onrender.com  
⏱️ Note: The app may take **15 seconds** to load due to Render cold start
### 🧪 Demo Mode
A built-in demo login is available directly from the login page, allowing instant read-only access without registration.

## ✨ Features

- 🔐 **User Authentication System**
  - Secure login and registration
  - Session-based access control

- 🎓 **Academic Structure Management**
  - Create and manage semesters
  - Add/edit/delete courses
  - Organize assignments per course

- 📊 **Smart Grade Tracking**
  - Real-time course average calculations
  - Weighted grading system support
  - Semester-wide performance overview

- 📅 **Task Management System**
  - Full CRUD functionality for tasks
  - Sort by due date, course, or status
  - Status tracking (Not Started / In Progress / Completed)

- 📄 **Syllabus Parser**
  - Upload course syllabi (PDF)
  - Automatically extracts tasks, due dates, and weights using text parsing

- 🌙 **Dark Mode**
  - Toggleable theme with persistent localStorage support

- 🧪 **Demo Mode**
  - One-click demo login
  - No signup required
  - Read-only safe environment for exploration


## 🖥️ Technologies Used
- **Backend:** Python (Flaskk 3.0.0)  
- **Frontend:** HTML, CSS, JavaScript
- **Database:** PostgreSQL (production) / SQLite (development)
- **Libraries:**
  - Flask-Login
  - psycopg2
  - pdfplumber
  - regex


## 🌐 Live Deployment

The application is deployed on Render:

🔗 https://unitrack-tbu9.onrender.com

⚠️ Note:  
Because the app is hosted on a free Render instance, it may take **~15 seconds** to cold start when first opened.


## ▶️ How to Run Locally

```bash
# 1. Clone the repository
git clone https://github.com/your-username/your-repo.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables

# Create a .env file OR export variables manually:

SECRET_KEY=your_secret_key
DATABASE_URL=your_database_url

# 4. Run the app
python app.py

# 5. Open in browser
http://127.0.0.1:5000
```

## 📆 Future Improvemewnts
- Improve mobile responsiveness for better usability on smaller screens
- Improve PDF parsing accuracy for complex formats
- Add calendar view for deadlines and task scheduling
- Add drag-and-drop support for organizing semesters, courses, and tasks
- Add analytics dashboard (grade trends, performance over time)
- Add reminder/notification system for upcoming deadlines
- UI/UX improvements