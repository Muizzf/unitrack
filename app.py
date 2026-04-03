from flask import Flask, render_template, request, redirect 

import sqlite3             #import to interact with SQLite databases

app = Flask(__name__)       #create the web server

def get_db():
    conn = sqlite3.connect("database.db")       #opens file database.db (or creates it if it doesn't exist)
    conn.row_factory = sqlite3.Row
    return conn 


#routes
@app.route("/")             #define a route to homepage ("/") (index.html)
def home():
    conn = get_db()         #opens database connection
    semesters = conn.execute("SELECT * FROM semesters").fetchall()
    return render_template("index.html", semesters=semesters) 

@app.route("/addSemester", methods=["POST"])
def add_semester():
    name = request.form["semesterName"]

    conn = get_db()
    conn.execute("INSERT INTO semesters (name) VALUES (?)", (name,))
    conn.commit()

    return redirect("/")

@app.route("/semester/<int:semester_id>")
def semester_page(semester_id):
    conn = get_db()

    semester = conn.execute(
        "SELECT * FROM semesters WHERE id = ?",
        (semester_id,)
    ).fetchone()

    courses = conn.execute(
        "SELECT * FROM courses WHERE semester_id = ?",
        (semester_id,)
    ).fetchall()

    sort = request.args.get("sort", "due")   # Default to due date
    # Map sort option to SQL
    order_by = {
        "due": "due_date",
        "course": "courses.name",
        "status": """
            CASE tasks.status
                WHEN 'Completed' THEN 1
                WHEN 'In Progress' THEN 2
                WHEN 'Not Started' THEN 3
            END
        """
    }.get(sort, "due_date")

    # Get all tasks in this semester, sorted
    tasks = conn.execute(f"""
        SELECT tasks.*, courses.name AS course_name
        FROM tasks
        JOIN courses ON tasks.course_id = courses.id
        WHERE courses.semester_id = ?
        ORDER BY {order_by}
    """, (semester_id,)).fetchall()

    course_totals = {}
    for t in tasks:
        course_id = t["course_id"]
        
        # Convert weight safely
        weight = float(t["weight"]) if t["weight"] not in (None, '') else 0
        
        # Convert grade safely
        grade = float(t["grade"]) if t["grade"] not in (None, '') else None

        if grade is not None:
            if course_id not in course_totals:
                course_totals[course_id] = {"earned": 0, "weight": 0}
            course_totals[course_id]["earned"] += (grade / 100) * weight
            course_totals[course_id]["weight"] += weight

    course_averages = []
    for totals in course_totals.values():
        if totals["weight"] > 0:
            course_averages.append(totals["earned"] / totals["weight"] * 100)

    semester_average = round(sum(course_averages) / len(course_averages), 2) if course_averages else 0

    return render_template(
        "semester.html",
        semester=semester,
        courses=courses,
        tasks=tasks,
        semester_average=semester_average
    )


@app.route("/editSemester/<int:semester_id>")
def edit_semester_page(semester_id):
    conn = get_db()
    semester = conn.execute(
        "SELECT * FROM semesters WHERE id = ?",
        (semester_id,)
    ).fetchone()

    return render_template("edit_semester.html", semester=semester)
@app.route("/updateSemester/<int:semester_id>", methods=["POST"])
def update_semester(semester_id):
    new_name = request.form["semesterName"]

    conn = get_db()
    conn.execute(
        "UPDATE semesters SET name = ? WHERE id = ?",
        (new_name, semester_id)
    )
    conn.commit()

    return redirect("/")

@app.route("/deleteSemester/<int:semester_id>", methods=["POST"])
def delete_semester(semester_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM semesters WHERE id = ?",
        (semester_id,)
    )
    conn.commit()

    return redirect("/")



@app.route("/addTask/<int:semester_id>", methods=["POST"])
def add_task(semester_id):
    course_id = request.form["course_id"]
    title = request.form["title"]
    due_date = request.form["due_date"]
    weight = request.form["weight"]
    status = request.form["status"]
    grade = request.form["grade"]
    notes = request.form["notes"]

    conn = get_db()
    conn.execute("""
        INSERT INTO tasks 
        (course_id, title, due_date, weight, status, grade, notes)
        VALUES (    , ?, ?, ?, ?, ?, ?)
    """, (course_id, title, due_date, weight, status, grade, notes))

    conn.commit()

    return redirect(f"/semester/{semester_id}")


@app.route("/deleteTask/<int:task_id>", methods=["POST"])
def delete_task(task_id):
    conn = get_db()
    conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    return redirect(request.referrer)


@app.route("/addCourse/<int:semester_id>", methods=["POST"])    #route to add a course via POST method (not GET) (user GETS info or user POST info)
def add_course(semester_id):
    name = request.form["courseName"]

    conn = get_db()
    conn.execute(
        "INSERT INTO courses (name, semester_id) VALUES (?, ?)",
        (name, semester_id)
    )
    conn.commit()

    return redirect(f"/semester/{semester_id}")


@app.route("/deleteCourse/<int:course_id>", methods=["POST"])
def delete_course(course_id):
    conn = get_db()

    # delete tasks first
    conn.execute(
        "DELETE FROM tasks WHERE course_id = ?",
        (course_id,)
    )

    # delete course
    conn.execute(
        "DELETE FROM courses WHERE id = ?",
        (course_id,)
    )

    conn.commit()

    return redirect(request.referrer)

@app.route("/editCourse/<int:course_id>")
def edit_course(course_id):
    conn = get_db()

    course = conn.execute(
        "SELECT * FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()

    return render_template("edit_course.html", course=course)

@app.route("/updateCourse/<int:course_id>", methods=["POST"])
def update_course(course_id):
    conn = get_db()

    # Get semester_id first
    course = conn.execute(
        "SELECT semester_id FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()

    semester_id = course["semester_id"]

    # Update the course
    name = request.form["courseName"]
    conn.execute(
        "UPDATE courses SET name = ? WHERE id = ?",
        (name, course_id)
    )
    conn.commit()

    return redirect(f"/semester/{semester_id}")


@app.route("/editTask/<int:task_id>")   #route to edit a task
def edit_task(task_id):
    conn = get_db()

    task = conn.execute("""
        SELECT tasks.*, courses.semester_id
        FROM tasks
        JOIN courses ON tasks.course_id = courses.id
        WHERE tasks.id = ?
    """, (task_id,)).fetchone()

    courses = conn.execute(
        "SELECT * FROM courses WHERE semester_id = ?",
        (task["semester_id"],)
    ).fetchall()

    return render_template(
        "edit_task.html",
        task=task,
        courses=courses
    )

@app.route("/updateTask/<int:task_id>", methods=["POST"])   #route to update a task
def update_task(task_id):
    conn = get_db()

    # Get semester_id for redirect
    row = conn.execute("""
        SELECT courses.semester_id
        FROM tasks
        JOIN courses ON tasks.course_id = courses.id
        WHERE tasks.id = ?
    """, (task_id,)).fetchone()

    semester_id = row["semester_id"]

    # Get updated values
    title = request.form["title"]
    due_date = request.form["due_date"]
    weight = request.form["weight"]
    status = request.form["status"]
    grade = request.form["grade"]
    notes = request.form["notes"]

    conn.execute("""
        UPDATE tasks
        SET title = ?, due_date = ?, weight = ?, status = ?, grade = ?, notes = ?
        WHERE id = ?
    """, (title, due_date, weight, status, grade, notes, task_id))

    conn.commit()

    return redirect(f"/semester/{semester_id}")


@app.route("/course/<int:course_id>")
def course_page(course_id):
    conn = get_db()

    # Get course info
    course = conn.execute(
        "SELECT * FROM courses WHERE id = ?",
        (course_id,)
    ).fetchone()

    # Get all tasks for this course
    tasks = conn.execute("""
        SELECT * FROM tasks
        WHERE course_id = ?
        ORDER BY due_date ASC
    """, (course_id,)).fetchall()

    # Initialize counters
    earned = 0
    lost = 0
    available = 0  # ungraded weight

    for t in tasks:
        weight = float(t["weight"]) if t["weight"] else 0
        grade = float(t["grade"]) if t["grade"] else None

        if grade is not None:   # task has a grade
            earned += (grade / 100) * weight
            lost += ((100 - grade) / 100) * weight
        else:                   # task not yet graded
            available += weight

    # Calculate percentages
    percentage_earned = earned
    percentage_lost = lost
    percentage_available = available
    course_average = earned / (earned + lost) * 100 if (earned + lost) > 0 else 0



    return render_template(
        "course.html",
        course=course,
        tasks=tasks,
        percentage_earned=percentage_earned,
        percentage_lost=percentage_lost,
        percentage_available=percentage_available,
        course_average=course_average
    )





if __name__ == "__main__":
    app.run(debug=True)     #Start running the server in debug mode


