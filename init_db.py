import os
import psycopg2

conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
cur = conn.cursor()

# Semesters table
cur.execute("""
CREATE TABLE IF NOT EXISTS semesters (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL
)
""")

# Courses table
cur.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    semester_id INTEGER NOT NULL,
    FOREIGN KEY (semester_id) REFERENCES semesters(id) ON DELETE CASCADE
)
""")

# Tasks table
cur.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    course_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    due_date TEXT,
    weight REAL,
    status TEXT,
    grade REAL,
    notes TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(id) ON DELETE CASCADE
)
""")

conn.commit()
cur.close()
conn.close()