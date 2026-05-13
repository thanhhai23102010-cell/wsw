from flask import Flask, render_template, request, redirect
import sqlite3
from docx import Document
import cloudinary
import cloudinary.uploader

app = Flask(__name__)

DB_NAME = "database.db"

# =========================
# Cloudinary Config
# =========================
cloudinary.config(
    cloud_name="YOUR_CLOUD_NAME",
    api_key="YOUR_API_KEY",
    api_secret="YOUR_API_SECRET",
    secure=True
)


# =========================
# Tạo database
# =========================
conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filename TEXT,
    fileurl TEXT,
    content TEXT
)
""")

conn.commit()
conn.close()


# =========================
# Trang chủ
# =========================
@app.route("/")
# =========================
# Upload nhiều file
# =========================
@app.route("/upload", methods=["POST"])
def upload():

    files = request.files.getlist("file")

    for file in files:

        if file.filename == "":
            continue

        # Upload lên Cloudinary
        result = cloudinary.uploader.upload(
            file,
            resource_type="raw"
        )

        file_url = result["secure_url"]

        # Đọc nội dung Word
        file.seek(0)

        doc = Document(file)

        text = []

        for para in doc.paragraphs:
            text.append(para.text)

        content = "\n".join(text)

        # Lưu database
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute(
            """
            INSERT INTO files (filename, fileurl, content)
            VALUES (?, ?, ?)
            """,
            (file.filename, file_url, content)
        )

        conn.commit()
        conn.close()

    return redirect("/")


# =========================
# Xóa file
# =========================
@app.route("/delete/<int:file_id>")
def delete(file_id):

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM files WHERE id=?",
        (file_id,)
    )
    conn.commit()
    conn.close()

    return redirect("/")


# =========================
# Xem trước file Word
# =========================
@app.route("/preview/<int:file_id>")
def preview(file_id):

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


# =========================
# Chạy app
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)