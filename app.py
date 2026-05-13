from flask import Flask, render_template, request, redirect, send_from_directory
import os
import sqlite3
from docx import Document

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DB_NAME = "database.db"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# =========================
# Tạo database
# =========================
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    filepath TEXT,
    content TEXT
)
""")

conn.commit()
conn.close()


# =========================
# Đọc nội dung file Word
# =========================
def read_docx(file_path):
    doc = Document(file_path)

    text = []

    for para in doc.paragraphs:
        text.append(para.text)

    return "\n".join(text)


# =========================
# Trang chủ
# =========================
@app.route("/")
def index():
    query = request.args.get("query", "")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if query:
        cursor.execute("""
        SELECT * FROM files
        WHERE filename LIKE ?
        OR content LIKE ?
        """, (f"%{query}%", f"%{query}%"))
    else:
        cursor.execute("SELECT * FROM files")

    files = cursor.fetchall()

    conn.close()

    return render_template("index.html", files=files, query=query)


# =========================
# Upload file
# =========================
@app.route("/upload", methods=["POST"])
def upload():

    if "file" not in request.files:
        return redirect("/")

    file = request.files["file"]

    if file.filename == "":
        return redirect("/")

    if file:

        save_path = os.path.join(UPLOAD_FOLDER, file.filename)

        file.save(save_path)

        content = read_docx(save_path)

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO files (filename, filepath, content)
        VALUES (?, ?, ?)
        """, (file.filename, save_path, content))

        conn.commit()
        conn.close()

    return redirect("/")


# =========================
# Download file
# =========================
@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)


# =========================
# Chạy app
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)