import sqlite3        #import sqlite3 module to interact with SQLite databases

conn = sqlite3.connect("database.db")   #connect to the database (or create it if it doesn't exist)
cursor = conn.cursor()                  #create a cursor object to execute SQL commands

#Create a table named 'semesters' with columns 'id' and 'name'. SQL command to create the table if it doesn't exist
cursor.execute("""
CREATE TABLE IF NOT EXISTS semesters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL
)
""")
#Create a table named 'courses' with columns 'id', 'name', and 'semester_id'
cursor.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    semester_id INTEGER NOT NULL,
    FOREIGN KEY (semester_id) REFERENCES semesters(id)
)
""")
# Create a table named 'tasks' with various columns related to tasks
cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    due_date TEXT,
    weight REAL,
    status TEXT,
    grade REAL,
    notes TEXT,
    FOREIGN KEY (course_id) REFERENCES courses(id)
)
""")


conn.commit()                    #commit the changes to the database
conn.close()                     #close the database connection
