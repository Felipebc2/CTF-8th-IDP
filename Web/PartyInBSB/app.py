#!/usr/bin/env python3
import hmac
import os
import posixpath
import secrets
import sqlite3
import stat
import tarfile
from datetime import datetime
from functools import wraps
from io import BytesIO
from pathlib import Path

from flask import Flask, abort, flash, redirect, render_template, request, send_file, session, url_for

APP_ROOT = Path("/app")
DATABASE = APP_ROOT / "data" / "party.db"
MAX_UPLOAD_SIZE = 10 * 1024 * 1024
MAX_ARCHIVE_FILES = 200
MAX_ARCHIVE_SIZE = 30 * 1024 * 1024


app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ["SESSION_KEY"],
    MAX_CONTENT_LENGTH=MAX_UPLOAD_SIZE,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)


def connect_database():
    connection = sqlite3.connect(f"file:{DATABASE}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def get_csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]


def has_valid_csrf_token():
    received_token = request.form.get("csrf", "")
    return hmac.compare_digest(session.get("csrf", ""), received_token)


def format_event_date(value):
    return datetime.fromisoformat(value).strftime("%d/%m/%Y · %H:%M")


@app.context_processor
def template_helpers():
    return {"csrf_token": get_csrf_token, "format_date": format_event_date}


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped_view


def app_path(value):
    if not isinstance(value, str) or "\x00" in value:
        abort(404)

    relative_path = value or "."
    filesystem_path = Path(os.path.abspath(APP_ROOT / relative_path))

    if filesystem_path != APP_ROOT and APP_ROOT not in filesystem_path.parents:
        abort(404)
    return str(filesystem_path), relative_path


@app.get("/")
def index():
    search_term = request.args.get("q", "").strip()
    category = request.args.get("category", "")
    month = request.args.get("month", "")
    price = request.args.get("price", "")
    order = request.args.get("order", "asc")
    page = max(request.args.get("page", 1, type=int), 1)

    clauses = ["1 = 1"]
    parameters = []
    if search_term:
        escaped_term = search_term.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        clauses.append("(title LIKE ? ESCAPE '\\' OR venue LIKE ? ESCAPE '\\' OR neighborhood LIKE ? ESCAPE '\\' OR description LIKE ? ESCAPE '\\')")
        parameters.extend([f"%{escaped_term}%"] * 4)
    if category:
        clauses.append("category = ?")
        parameters.append(category)
    if month in {f"{number:02d}" for number in range(1, 13)}:
        clauses.append("substr(starts_at, 6, 2) = ?")
        parameters.append(month)
    if price == "free":
        clauses.append("price_label = ?")
        parameters.append("Gratuito")
    elif price == "paid":
        clauses.append("price_label != ?")
        parameters.append("Gratuito")

    direction = "DESC" if order == "desc" else "ASC"
    filters = " AND ".join(clauses)
    offset = (page - 1) * 12
    connection = connect_database()
    categories = [row[0] for row in connection.execute("SELECT DISTINCT category FROM events ORDER BY category")]
    total = connection.execute(f"SELECT COUNT(*) FROM events WHERE {filters}", parameters).fetchone()[0]
    events = connection.execute(
        f"SELECT * FROM events WHERE {filters} ORDER BY starts_at {direction} LIMIT 12 OFFSET ?",
        parameters + [offset],
    ).fetchall()
    connection.close()

    return render_template("index.html", events=events, categories=categories, total=total, page=page, pages=max(1, (total + 11) // 12))


@app.get("/eventos/<int:event_id>")
def event(event_id):
    connection = connect_database()
    event_data = connection.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    connection.close()
    if event_data is None:
        abort(404)
    return render_template("event.html", event=event_data)


@app.route("/admin/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if not has_valid_csrf_token():
        abort(400)

    username = request.form.get("username", "")
    password = request.form.get("password", "")
    try:
        connection = connect_database()
        sql = "SELECT id, username, role FROM users WHERE username = '%s' AND password = '%s' LIMIT 1" % (username, password)
        user = connection.execute(sql).fetchone()
        connection.close()
    except sqlite3.Error:
        user = None

    if user is None:
        flash("Credenciais inválidas.", "error")
        return render_template("login.html")

    session.clear()
    session["csrf"] = secrets.token_urlsafe(24)
    session["admin_id"] = user["id"]
    return redirect(url_for("admin"))


@app.get("/admin/logout")
@admin_required
def logout():
    session.clear()
    return redirect(url_for("index"))


def list_directory(value):
    directory, relative_path = app_path(value)
    if not os.path.isdir(directory):
        abort(404)
    try:
        entries = []
        for item in os.scandir(directory):
            is_directory = item.is_dir(follow_symlinks=True)
            item_stat = item.stat(follow_symlinks=False)
            entries.append(
                {
                    "name": item.name,
                    "path": posixpath.join(relative_path if relative_path != "." else "", item.name),
                    "is_dir": is_directory,
                    "size": "—" if is_directory else item_stat.st_size,
                    "permissions": stat.filemode(item_stat.st_mode),
                }
            )
    except OSError:
        abort(404)
    entries.sort(key=lambda item: (not item["is_dir"], item["name"].lower()))
    parent = posixpath.dirname(relative_path) if relative_path != "." else None
    return entries, relative_path, parent


@app.get("/admin")
@admin_required
def admin():
    entries, current, parent = list_directory(request.args.get("path", "."))
    return render_template("admin.html", entries=entries, current=current, parent=parent)


@app.get("/admin/files")
@admin_required
def files():
    return redirect(url_for("admin", path=request.args.get("path", ".")))


@app.get("/admin/download")
@admin_required
def download():
    filename, relative_path = app_path(request.args.get("path", ""))
    if not os.path.isfile(filename):
        abort(404)
    return send_file(filename, as_attachment=True, download_name=Path(relative_path).name)


@app.get("/admin/export")
@admin_required
def export_app():
    archive_data = BytesIO()
    with tarfile.open(fileobj=archive_data, mode="w:gz", dereference=False) as archive:
        archive.add(APP_ROOT, arcname="app", recursive=True)
    archive_data.seek(0)
    return send_file(archive_data, as_attachment=True, download_name="party-in-bsb.tar.gz", mimetype="application/gzip")


@app.post("/admin/import")
@admin_required
def import_archive():
    if not has_valid_csrf_token():
        abort(400)
    uploaded_file = request.files.get("arquivo")
    if uploaded_file is None or not uploaded_file.filename.lower().endswith(".tar.gz"):
        flash("Envie um arquivo .tar.gz válido.", "error")
        return redirect(url_for("admin"))

    archive_data = uploaded_file.read(MAX_UPLOAD_SIZE + 1)
    if len(archive_data) > MAX_UPLOAD_SIZE or archive_data[:2] != b"\x1f\x8b":
        flash("Arquivo inválido.", "error")
        return redirect(url_for("admin"))

    try:
        extract_archive(archive_data)
    except (tarfile.TarError, OSError, ValueError):
        flash("Não foi possível importar o arquivo.", "error")
        return redirect(url_for("admin"))

    flash("Importação concluída.", "success")
    return redirect(url_for("admin"))


def extract_archive(archive_data):
    with tarfile.open(fileobj=BytesIO(archive_data), mode="r:gz") as archive:
        members = archive.getmembers()
        if len(members) > MAX_ARCHIVE_FILES:
            raise ValueError
        if sum(member.size for member in members if member.isreg()) > MAX_ARCHIVE_SIZE:
            raise ValueError

        archive.extractall(path=APP_ROOT)


@app.errorhandler(413)
def too_large(_error):
    return "Arquivo muito grande.", 413


