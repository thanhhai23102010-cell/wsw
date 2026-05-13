from flask import (
    Flask,
    render_template,
    request,
    redirect,
    session,
    url_for,
    send_from_directory
)

import os
import sqlite3
from docx import Document

app = Flask(__name__)

app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
DB_NAME = "database.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =====================
# DATABASE
# =====================

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

# Users
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT

)
""")

# Files
cursor.execute("""
CREATE TABLE IF NOT EXISTS files (

    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    content TEXT

)
""")

conn.commit()
conn.close()


# =====================
# READ WORD
# =====================

def read_docx(path):

    doc = Document(path)

    text = []

    for para in doc.paragraphs:
        text.append(para.text)

    return "\n".join(text)


# =====================
# LOGIN CHECK
# =====================

def logged_in():

    return "user" in session


# =====================
# HOME
# =====================

@app.route("/")
def home():

    if not logged_in():
        return redirect("/login")

    query = request.args.get("query", "")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if query:

        cursor.execute(
            """
            SELECT * FROM files
            WHERE filename LIKE ?
            OR content LIKE ?
            """,
            (f"%{query}%", f"%{query}%")
        )

    else:

        cursor.execute(
            "SELECT * FROM files ORDER BY id DESC"
        )

    files = cursor.fetchall()

    conn.close()

    return render_template(
        "index.html",
        files=files,
        query=query,
        username=session["user"]
    )


# =====================
# REGISTER
# =====================

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        try:

            cursor.execute(
                """
                INSERT INTO users (username, password)
                VALUES (?, ?)
                """,
                (username, password)
            )

            conn.commit()

        except:
            return "Tài khoản đã tồn tại"

        conn.close()

        return redirect("/login")

    return render_template("register.html")


# =====================
# LOGIN
# =====================

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT * FROM users
            WHERE username=?
            AND password=?
            """,
            (username, password)
        )

        user = cursor.fetchone()

        conn.close()

        if user:

            session["user"] = username

            return redirect("/")

        else:

            return "Sai tài khoản hoặc mật khẩu"

    return render_template("login.html")


# =====================
# LOGOUT
# =====================

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# =====================
# UPLOAD
# =====================

@app.route("/upload", methods=["POST"])
def upload():

    if not logged_in():
        return redirect("/login")

    files = request.files.getlist("file")

    for file in files:

        if file.filename != "":

            save_path = os.path.join(
                UPLOAD_FOLDER,
                file.filename
            )

            file.save(save_path)

            content = read_docx(save_path)

            conn = sqlite3.connect(DB_NAME)
            cursor = conn.cursor()

            cursor.execute(
                """
                INSERT INTO files (filename, content)
                VALUES (?, ?)
                """,
                (file.filename, content)
            )

            conn.commit()
            conn.close()

    return redirect("/")


# =====================
# DOWNLOAD
# =====================

@app.route("/download/<filename>")
def download(filename):

    if not logged_in():
        return redirect("/login")

    return send_from_directory(
        UPLOAD_FOLDER,
        filename,
        as_attachment=True
    )


# =====================
# DELETE
# =====================

@app.route("/delete/<int:file_id>")
def delete(file_id):

    if not logged_in():
        return redirect("/login")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT filename FROM files WHERE id=?",
        (file_id,)
    )

    file = cursor.fetchone()

    if file:

        filename = file[0]

        path = os.path.join(
            UPLOAD_FOLDER,
            filename
        )

        if os.path.exists(path):
            os.remove(path)

        cursor.execute(
            "DELETE FROM files WHERE id=?",
            (file_id,)
        )

        conn.commit()

    conn.close()

    return redirect("/")


# =====================
# PREVIEW
# =====================

@app.route("/preview/<int:file_id>")
def preview(file_id):

    if not logged_in():
        return redirect("/login")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM files WHERE id=?",
        (file_id,)
    )

    file = cursor.fetchone()

    conn.close()

    return render_template(
        "preview.html",
        file=file
    )


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)