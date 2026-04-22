from flask import Flask, render_template, request, redirect 

import os

import psycopg2
from psycopg2.extras import RealDictCursor

from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)       #create the web server
app.secret_key = os.environ.get("SECRET_KEY", "dev")

def get_db():
    conn = psycopg2.connect(
        os.environ["DATABASE_URL"],
        sslmode="require"
    )
    return conn

login_manager = LoginManager() #initialize flask login
login_manager.init_app(app)
login_manager.login_view = "login"

app.config["UPLOAD_FOLDER"] = "uploads" #directory to store uploaded files

class User(UserMixin):
    pass

@login_manager.user_loader
def load_user(user_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, email FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if row:
        user = User()
        user.id = row[0]
        return user

    return None

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        hashed = generate_password_hash(password)

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO users (email, password_hash) VALUES (%s, %s)",
            (email, hashed)
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect("/login")

    return render_template("register.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()

        cur.execute("SELECT id, password_hash FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            u = User()
            u.id = user[0]
            login_user(u)
            return redirect("/")

        return "Invalid login"

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")



#routes
@app.route("/")             #define a route to homepage ("/") (index.html)
@login_required
def home():
    conn = get_db()         #opens database connection
    curr = conn.cursor(cursor_factory=RealDictCursor)
    curr.execute("SELECT * FROM semesters wHERE user_id = %s", (current_user.id,))
    semesters = curr.fetchall()

    curr.close()
    conn.close()

    return render_template("index.html", semesters=semesters) 

@app.route("/addSemester", methods=["POST"])
@login_required
def add_semester():
    name = request.form["semesterName"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("INSERT INTO semesters (name, user_id) VALUES (%s, %s)", (name, current_user.id))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/")

@app.route("/semester/<int:semester_id>")
@login_required
def semester_page(semester_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM semesters WHERE id = %s AND user_id = %s", (semester_id, current_user.id))
    semester = cur.fetchone()

    cur.execute("SELECT * FROM courses WHERE semester_id = %s AND user_id = %s", (semester_id, current_user.id))
    courses = cur.fetchall()

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
    cur.execute(f"""
        SELECT tasks.*, courses.name AS course_name
        FROM tasks
        JOIN courses ON tasks.course_id = courses.id
        WHERE courses.semester_id = %s AND courses.user_id = %s
        ORDER BY {order_by}
    """, (semester_id, current_user.id))
    tasks = cur.fetchall()

    cur.close()
    conn.close()

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
@login_required
def edit_semester_page(semester_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM semesters WHERE id = %s AND user_id = %s", (semester_id, current_user.id))
    semester = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("edit_semester.html", semester=semester)

@app.route("/updateSemester/<int:semester_id>", methods=["POST"])
@login_required
def update_semester(semester_id):
    new_name = request.form["semesterName"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE semesters SET name = %s WHERE id = %s AND user_id = %s",
        (new_name, semester_id, current_user.id)
    )
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/")

@app.route("/deleteSemester/<int:semester_id>", methods=["POST"])
@login_required
def delete_semester(semester_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM semesters WHERE id = %s AND user_id = %s", (semester_id, current_user.id))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/")



@app.route("/addTask/<int:semester_id>", methods=["POST"])
@login_required
def add_task(semester_id):
    course_id = request.form["course_id"]
    title = request.form["title"]
    due_date = request.form["due_date"]
    weight = request.form["weight"]
    status = request.form["status"]
    grade = request.form["grade"]
    notes = request.form["notes"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO tasks 
        (course_id, title, due_date, weight, status, grade, notes, user_id)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (course_id, title, due_date, weight, status, grade, notes, current_user.id))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(f"/semester/{semester_id}")


@app.route("/deleteTask/<int:task_id>", methods=["POST"])
@login_required
def delete_task(task_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM tasks WHERE id = %s AND user_id = %s", (task_id, current_user.id))
    conn.commit()

    cur.close()
    conn.close()

    return redirect(request.referrer)


@app.route("/addCourse/<int:semester_id>", methods=["POST"])
@login_required
def add_course(semester_id):
    name = request.form["courseName"]

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO courses (name, semester_id, user_id) VALUES (%s, %s, %s)",
        (name, semester_id, current_user.id)
    )
    conn.commit()

    cur.close()
    conn.close()

    return redirect(f"/semester/{semester_id}")


@app.route("/deleteCourse/<int:course_id>", methods=["POST"])
@login_required
def delete_course(course_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM tasks WHERE course_id = %s AND user_id = %s", (course_id, current_user.id))
    cur.execute("DELETE FROM courses WHERE id = %s AND user_id = %s", (course_id, current_user.id))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(request.referrer)

@app.route("/editCourse/<int:course_id>")
@login_required
def edit_course(course_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT * FROM courses WHERE id = %s AND user_id = %s", (course_id, current_user.id))
    course = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("edit_course.html", course=course)

@app.route("/updateCourse/<int:course_id>", methods=["POST"])
@login_required
def update_course(course_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT semester_id FROM courses WHERE id = %s AND user_id = %s", (course_id, current_user.id))
    course = cur.fetchone()
    semester_id = course["semester_id"]

    name = request.form["courseName"]

    cur.execute(
        "UPDATE courses SET name = %s WHERE id = %s AND user_id = %s",
        (name, course_id, current_user.id)
    )
    conn.commit()

    cur.close()
    conn.close()

    return redirect(f"/semester/{semester_id}")


@app.route("/editTask/<int:task_id>")
@login_required
def edit_task(task_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT tasks.*, courses.semester_id
        FROM tasks
        JOIN courses ON tasks.course_id = courses.id
        WHERE tasks.id = %s AND tasks.user_id = %s
    """, (task_id, current_user.id))
    task = cur.fetchone()

    cur.execute(
        "SELECT * FROM courses WHERE semester_id = %s AND user_id = %s",
        (task["semester_id"], current_user.id)
    )
    courses = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("edit_task.html", task=task, courses=courses)

@app.route("/updateTask/<int:task_id>", methods=["POST"])
@login_required
def update_task(task_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT courses.semester_id
        FROM tasks
        JOIN courses ON tasks.course_id = courses.id
        WHERE tasks.id = %s AND tasks.user_id = %s
    """, (task_id, current_user.id))
    row = cur.fetchone()

    semester_id = row["semester_id"]

    title = request.form["title"]
    due_date = request.form["due_date"]
    weight = request.form["weight"]
    status = request.form["status"]
    grade = request.form["grade"]
    notes = request.form["notes"]

    cur.execute("""
        UPDATE tasks
        SET title = %s, due_date = %s, weight = %s, status = %s, grade = %s, notes = %s
        WHERE id = %s AND user_id = %s
    """, (title, due_date, weight, status, grade, notes, task_id, current_user.id))

    conn.commit()

    cur.close()
    conn.close()

    return redirect(f"/semester/{semester_id}")


@app.route("/course/<int:course_id>")
@login_required
def course_page(course_id):
    conn = get_db()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get course info
    cur.execute(
        "SELECT * FROM courses WHERE id = %s AND user_id = %s",
        (course_id, current_user.id)
    )
    course = cur.fetchone()

    # Get all tasks for this course
    cur.execute("""
        SELECT * FROM tasks
        WHERE course_id = %s AND user_id = %s
        ORDER BY due_date ASC
    """, (course_id, current_user.id))
    tasks = cur.fetchall()

    cur.close()
    conn.close()

    # Initialize counters
    earned = 0
    lost = 0
    available = 0

    for t in tasks:
        weight = float(t["weight"]) if t["weight"] else 0
        grade = float(t["grade"]) if t["grade"] else None

        if grade is not None:
            earned += (grade / 100) * weight
            lost += ((100 - grade) / 100) * weight
        else:
            available += weight

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


from werkzeug.utils import secure_filename
from syllabus_parser import extract_tasks_from_pdf

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/uploadSyllabus", methods=["POST"])
@login_required
def upload_syllabus():
    course_id = request.form["course_id"]
    file = request.files["file"]

    if file.filename == "":
        return "No selected file"

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)

        os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
        file.save(filepath)

        tasks = extract_tasks_from_pdf(filepath)

        conn = get_db()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        for t in tasks:
            cur.execute("""
                INSERT INTO tasks
                (course_id, title, due_date, weight, status, grade, notes, user_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                course_id,
                t["title"],
                t["due_date"] if t["due_date"] != "Unknown" else "",
                t["weight"],
                "Not Started",
                None,
                "",
                current_user.id
            ))

        conn.commit()

        # Get semester_id for redirect
        cur.execute(
            "SELECT semester_id FROM courses WHERE id = %s AND user_id = %s",
            (course_id, current_user.id)
        )
        course = cur.fetchone()
        semester_id = course["semester_id"]

        cur.close()
        conn.close()

        return redirect(f"/semester/{semester_id}")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
