from __future__ import annotations

import os
import sqlite3
from datetime import date
from functools import wraps
from pathlib import Path

from flask import Flask, make_response, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE = Path(os.environ.get("PORTAL_DATABASE", BASE_DIR / "portal.db"))
app = Flask(__name__)
secret_key = os.environ.get("PORTAL_SECRET_KEY")
if not secret_key and os.environ.get("PORTAL_ENV") == "production":
    raise RuntimeError("PORTAL_SECRET_KEY must be set when PORTAL_ENV=production")
app.config["SECRET_KEY"] = secret_key or "local-development-key-change-me"
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

DOCUMENTS = [
    {"id":"experience-certificate","name":"Experience Certificate","category":"Employment","description":"Official confirmation of your employment history and role.","size":"1.2 MB","date":"15 Mar 2024","date_short":"15 Mar 2024","doc_id":"NS-EMP-MP-1234"},
    {"id":"relieving-letter","name":"Relieving Letter","category":"Employment","description":"Formal acknowledgement of completed responsibilities.","size":"860 KB","date":"15 Mar 2024","date_short":"15 Mar 2024","doc_id":"NS-EMP-MP-1235"},
    {"id":"form-16","name":"FY 2023–24 Form 16","category":"Tax","description":"Annual tax deduction certificate for your records.","size":"2.4 MB","date":"10 Jun 2024","date_short":"10 Jun 2024","doc_id":"NS-TAX-MP-1234"},
    {"id":"final-settlement","name":"Final Settlement Statement","category":"Payroll","description":"Detailed summary of your full and final settlement.","size":"940 KB","date":"22 Mar 2024","date_short":"22 Mar 2024","doc_id":"NS-PAY-MP-1234"},
    {"id":"provident-fund","name":"Provident Fund Guide","category":"Benefits","description":"Steps to view, transfer, or withdraw your PF balance.","size":"3.1 MB","date":"08 Apr 2024","date_short":"08 Apr 2024","doc_id":"NS-BEN-MP-1234"},
    {"id":"benefits-handbook","name":"Alumni Benefits Handbook","category":"Benefits","description":"Explore programs and benefits available to our alumni.","size":"4.8 MB","date":"01 May 2024","date_short":"01 May 2024","doc_id":"NS-BEN-MP-1235"},
]
CATEGORIES = ["Employment", "Tax", "Payroll", "Benefits"]


def db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with db() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT, first_name TEXT NOT NULL,
            last_name TEXT NOT NULL, employee_id TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE COLLATE NOCASE, password_hash TEXT NOT NULL
        )""")


def current_user():
    uid = session.get("user_id")
    if not uid:
        return None
    with db() as conn:
        row = conn.execute("SELECT * FROM users WHERE id=?", (uid,)).fetchone()
    return dict(row) if row else None


def login_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not current_user():
            return redirect(url_for("auth", mode="signin"))
        return fn(*args, **kwargs)
    return wrapped


def auth_page(mode="signin", errors=None, values=None):
    return render_template("auth.html", mode=mode, errors=errors or [], values=values or {})


@app.route("/")
def home():
    if current_user():
        return redirect(url_for("dashboard"))
    return redirect(url_for("auth", mode="signin"))


@app.route("/auth", methods=["GET", "POST"])
def auth():
    mode = request.args.get("mode", "signin")
    if request.method == "POST":
        action = request.form.get("action", "signin")
        mode = action
        if action == "register":
            values = {k: request.form.get(k, "").strip() for k in ("first_name", "last_name", "employee_id", "email")}
            password = request.form.get("password", "")
            confirm = request.form.get("confirm_password", "")
            errors = []
            if not values["first_name"] or not values["last_name"]: errors.append("Enter your first and last name.")
            if not values["employee_id"]: errors.append("Enter your former employee ID.")
            if "@" not in values["email"] or "." not in values["email"].rsplit("@", 1)[-1]: errors.append("Enter a valid personal email address.")
            if len(password) < 8: errors.append("Create a password with at least 8 characters.")
            if password != confirm: errors.append("Your passwords do not match.")
            if errors: return auth_page("register", errors, values)
            try:
                with db() as conn:
                    cursor = conn.execute("INSERT INTO users(first_name,last_name,employee_id,email,password_hash) VALUES(?,?,?,?,?)", (values["first_name"], values["last_name"], values["employee_id"].upper(), values["email"], generate_password_hash(password)))
                    session.clear()
                    session["user_id"] = cursor.lastrowid
                return redirect(url_for("dashboard"))
            except sqlite3.IntegrityError:
                return auth_page("register", ["An account already exists with that email or employee ID."], values)
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        with db() as conn:
            user = conn.execute("SELECT * FROM users WHERE email=?", (email,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear(); session["user_id"] = user["id"]
            return redirect(url_for("dashboard"))
        return auth_page("signin", ["Email or password is incorrect. Please try again."], {"email": email})
    return auth_page("register" if mode == "register" else "signin")


@app.route("/dashboard")
@login_required
def dashboard():
    user = current_user()
    category = request.args.get("category", "All documents")
    query = request.args.get("q", "").strip().lower()
    docs = [d for d in DOCUMENTS if (category == "All documents" or d["category"] == category) and (not query or query in (d["name"] + " " + d["description"] + " " + d["category"]).lower())]
    return render_template("dashboard.html", user=user, docs=docs, all_docs=DOCUMENTS, categories=CATEGORIES, category=category, query=query, counts={c:sum(d["category"] == c for d in DOCUMENTS) for c in CATEGORIES})


@app.route("/documents")
@login_required
def documents():
    return redirect(url_for("dashboard") + "#documents")


@app.route("/support")
@login_required
def support():
    return redirect(url_for("dashboard") + "#support")


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth", mode="signin"))


@app.route("/documents/<doc_id>/download")
@login_required
def download(doc_id):
    doc = next((d for d in DOCUMENTS if d["id"] == doc_id), None)
    if not doc: return "Document not found", 404
    user = current_user()
    lines = ["NORTHSTAR ALUMNI PORTAL", "OFFICIAL DOCUMENT", doc["name"], "", f"Issued to {user['first_name']} {user['last_name']}, Employee ID {user['employee_id']}.", doc["description"], f"Issued on {doc['date']}", f"Document ID: {doc['doc_id']}", "", "Sample preview only. Contact People Operations for an official copy."]
    def pdf_escape(value):
        value = value.encode("ascii", "replace").decode("ascii")
        return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    commands = ["BT", "/F1 16 Tf", "54 750 Td"]
    for index, line in enumerate(lines):
        if index:
            commands.append("0 -30 Td" if index < 3 else "0 -22 Td")
        commands.append(f"({pdf_escape(line)}) Tj")
        if index == 0:
            commands.append("/F1 11 Tf")
    commands.append("ET")
    stream = "\n".join(commands).encode("ascii")
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>", b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream"]
    pdf = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(pdf)); pdf.extend(f"{number} 0 obj\n".encode()); pdf.extend(obj); pdf.extend(b"\nendobj\n")
    xref = len(pdf); pdf.extend(f"xref\n0 {len(offsets)}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]: pdf.extend(f"{offset:010d} 00000 n \n".encode())
    pdf.extend(f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    response = make_response(bytes(pdf))
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"attachment; filename={doc['id']}.pdf"
    return response


@app.context_processor
def inject_user():
    return {"signed_in_user": current_user(), "now": date.today()}

init_db()

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False, host="127.0.0.1", port=int(os.environ.get("PORT", "5000")))
