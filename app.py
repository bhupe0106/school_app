import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DATABASE = "students.db"
COURSES = ["Computer Science", "Information Technology", "Electronics", "Mechanical", "Civil"]



def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS student (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT NOT NULL,
            email    TEXT NOT NULL UNIQUE,
            age      INTEGER NOT NULL,
            gender   TEXT NOT NULL,
            course   TEXT NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


class Student:
    """Student model: id, name, email, age, gender, course, password"""

    @staticmethod
    def create(name, email, age, gender, course, password):
        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO student (name, email, age, gender, course, password) VALUES (?, ?, ?, ?, ?, ?)",
                (name, email, age, gender, course, generate_password_hash(password)),
            )
            conn.commit()
        finally:
            conn.close()

    @staticmethod
    def get_by_email(email):
        conn = get_db()
        row = conn.execute("SELECT * FROM student WHERE email = ?", (email,)).fetchone()
        conn.close()
        return row

    @staticmethod
    def get_by_id(student_id):
        conn = get_db()
        row = conn.execute("SELECT * FROM student WHERE id = ?", (student_id,)).fetchone()
        conn.close()
        return row

    @staticmethod
    def update_course(student_id, course):
        conn = get_db()
        conn.execute("UPDATE student SET course = ? WHERE id = ?", (course, student_id))
        conn.commit()
        conn.close()



@app.route("/", methods=["GET", "POST"])
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        age = request.form.get("age", "").strip()
        gender = request.form.get("gender", "").strip()
        course = request.form.get("course", "").strip()
        password = request.form.get("password", "")

        # Server-side checks
        if not (name and email and age.isdigit() and gender and course and len(password) >= 6):
            return render_template("register.html", courses=COURSES, error="Please fill all fields correctly.")

        try:
            Student.create(name, email, int(age), gender, course, password)
        except sqlite3.IntegrityError:
            return render_template("register.html", courses=COURSES, error="This email is already registered.")
        except Exception as e:
            return render_template("register.html", courses=COURSES, error=f"Database error: {e}")

        return redirect(url_for("success", name=name))

    return render_template("register.html", courses=COURSES, error=None)


@app.route("/success")
def success():
    return render_template("success.html", name=request.args.get("name", "Student"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        student = Student.get_by_email(email)
        if student and check_password_hash(student["password"], password):
            session["student_id"] = student["id"]
            return redirect(url_for("profile"))
        error = "Invalid email or password."
    return render_template("login.html", error=error)


@app.route("/profile")
def profile():
    student_id = session.get("student_id")
    if not student_id:
        return redirect(url_for("login"))
    student = Student.get_by_id(student_id)
    if not student:
        session.clear()
        return redirect(url_for("login"))
    return render_template("profile.html", student=student, courses=COURSES)


@app.route("/update-course", methods=["POST"])
def update_course():
    student_id = session.get("student_id")
    if not student_id:
        return jsonify(success=False, message="Not logged in"), 401
    course = request.form.get("course", "")
    if course not in COURSES:
        return jsonify(success=False, message="Invalid course"), 400
    try:
        Student.update_course(student_id, course)
    except Exception as e:
        return jsonify(success=False, message=str(e)), 500
    return jsonify(success=True, message=f"Course updated to: {course}")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
