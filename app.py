import os
import uuid
import json
from datetime import datetime
from functools import wraps

from flask import (Flask, render_template, request, redirect,
                   url_for, flash, session, jsonify, abort,
                   send_from_directory, Response)
from supabase import create_client, Client
from dotenv import load_dotenv
import bleach

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-me-in-production")

# ── Supabase ──────────────────────────────────────────────────────────────────
SUPABASE_URL    = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY    = os.environ.get("SUPABASE_KEY", "")   # service-role key (server-side only)
SUPABASE_BUCKET = os.environ.get("SUPABASE_BUCKET", "layosam-projects")
ADMIN_PASSWORD  = os.environ.get("ADMIN_PASSWORD", "layosam2026")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL else None

ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
MAX_FILE_BYTES = 8 * 1024 * 1024   # 8 MB

# ── Helpers ───────────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_IMAGE_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated

def get_projects(limit: int = 50, offset: int = 0):
    """Fetch projects from Supabase ordered by newest first."""
    if not supabase:
        return []
    try:
        res = (supabase.table("projects")
               .select("*")
               .order("created_at", desc=True)
               .range(offset, offset + limit - 1)
               .execute())
        return res.data or []
    except Exception as e:
        app.logger.error(f"Supabase fetch error: {e}")
        return []

def upload_image_to_supabase(file_obj, original_filename: str) -> str | None:
    """Upload image bytes to Supabase Storage, return public URL."""
    if not supabase:
        return None
    ext = original_filename.rsplit(".", 1)[1].lower()
    unique_name = f"{uuid.uuid4().hex}.{ext}"
    path = f"projects/{unique_name}"
    try:
        file_bytes = file_obj.read()
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path,
            file_bytes,
            {"content-type": f"image/{ext}", "upsert": "false"}
        )
        public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(path)
        return public_url
    except Exception as e:
        app.logger.error(f"Supabase upload error: {e}")
        return None

def delete_image_from_supabase(image_url: str):
    """Remove an image from Supabase Storage."""
    if not supabase or not image_url:
        return
    try:
        # Extract path after bucket name
        marker = f"{SUPABASE_BUCKET}/"
        idx = image_url.find(marker)
        if idx != -1:
            path = image_url[idx + len(marker):]
            supabase.storage.from_(SUPABASE_BUCKET).remove([path])
    except Exception as e:
        app.logger.error(f"Supabase delete error: {e}")

# ── Public routes ─────────────────────────────────────────────────────────────
@app.route("/")
def index():
    projects = get_projects(limit=6)
    return render_template(
        "index.html",
        projects=projects,
        seo_title="Layosam | Solar Installation & Electrical Services in Ibadan",
        seo_description="Expert solar installation, inverter setup, house wiring and electrical engineering in Ibadan. Free inspection. Call 08106690594.",
        canonical_url="https://layosamtech.onrender.com/"
    )

@app.route("/about")
def about():
    return render_template(
        "about.html",
        seo_title="About Us | Layosam Solar & Electrical – Ibadan",
        seo_description="Learn about Layosam, Ibadan's trusted solar installation and electrical engineering company. Certified engineers, hundreds of completed projects.",
        canonical_url="https://layosamtech.onrender.com/about"
    )

@app.route("/services")
def services():
    return render_template(
        "services.html",
        seo_title="Services | Solar, Inverter & Electrical Wiring – Layosam Ibadan",
        seo_description="Solar panel installation, inverter & battery setup, house wiring, electrical repairs and more. Serving Ibadan and Oyo State.",
        canonical_url="https://layosamtech.onrender.com/services"
    )

@app.route("/projects")
def projects_page():
    page  = request.args.get("page", 1, type=int)
    limit = 12
    offset = (page - 1) * limit
    projects = get_projects(limit=limit + 1, offset=offset)
    has_next = len(projects) > limit
    projects = projects[:limit]
    return render_template(
        "projects.html",
        projects=projects,
        page=page,
        has_next=has_next,
        seo_title="Completed Projects | Solar & Electrical Work – Layosam Ibadan",
        seo_description="Browse completed solar installation and electrical projects by Layosam across Ibadan and Oyo State, Nigeria.",
        canonical_url="https://layosamtech.onrender.com/projects"
    )

@app.route("/contact")
def contact():
    return render_template(
        "contact.html",
        seo_title="Contact Layosam | Solar & Electrical Services Ibadan",
        seo_description="Get in touch with Layosam for solar installation, inverter setup and electrical services in Ibadan. Call 08106690594 or WhatsApp us.",
        canonical_url="https://layosamtech.onrender.com/contact"
    )

# ── API: latest projects (used by index.html JS) ──────────────────────────────
@app.route("/api/projects")
def api_projects():
    limit  = request.args.get("limit", 6, type=int)
    offset = request.args.get("offset", 0, type=int)
    return jsonify(get_projects(limit=limit, offset=offset))

# ── Admin auth ────────────────────────────────────────────────────────────────
@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    error = None
    if request.method == "POST":
        pw = request.form.get("password", "")
        if pw == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            session.permanent = False
            return redirect(url_for("admin_dashboard"))
        error = "Incorrect password. Try again."
    return render_template("admin/login.html", error=error)

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("admin_login"))

# ── Admin dashboard ───────────────────────────────────────────────────────────
@app.route("/admin")
@login_required
def admin_dashboard():
    projects = get_projects(limit=50)
    return render_template("admin/dashboard.html", projects=projects)

# ── Admin: upload new project ─────────────────────────────────────────────────
@app.route("/admin/upload", methods=["GET", "POST"])
@login_required
def admin_upload():
    if request.method == "POST":
        title    = bleach.clean(request.form.get("title", "").strip())
        location = bleach.clean(request.form.get("location", "").strip())
        category = bleach.clean(request.form.get("category", "Solar Installation").strip())
        description = bleach.clean(request.form.get("description", "").strip())
        featured = request.form.get("featured") == "on"

        if not title or not location:
            flash("Title and location are required.", "error")
            return redirect(url_for("admin_upload"))

        image_url = None
        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Only JPG, PNG or WEBP images are allowed.", "error")
                return redirect(url_for("admin_upload"))
            file.seek(0, 2)
            size = file.tell()
            file.seek(0)
            if size > MAX_FILE_BYTES:
                flash("Image must be under 8 MB.", "error")
                return redirect(url_for("admin_upload"))
            image_url = upload_image_to_supabase(file, file.filename)
            if not image_url:
                flash("Image upload failed. Check Supabase config.", "error")
                return redirect(url_for("admin_upload"))

        # Save metadata to Supabase table
        if supabase:
            try:
                supabase.table("projects").insert({
                    "title": title,
                    "location": location,
                    "category": category,
                    "description": description,
                    "image_url": image_url,
                    "featured": featured,
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
                flash(f'Project "{title}" uploaded successfully!', "success")
            except Exception as e:
                app.logger.error(f"Insert error: {e}")
                flash("Database insert failed. Check Supabase config.", "error")
        else:
            flash("Supabase not configured — project not saved.", "error")

        return redirect(url_for("admin_dashboard"))

    return render_template("admin/upload.html")

# ── Admin: edit project ───────────────────────────────────────────────────────
@app.route("/admin/edit/<project_id>", methods=["GET", "POST"])
@login_required
def admin_edit(project_id):
    if not supabase:
        flash("Supabase not configured.", "error")
        return redirect(url_for("admin_dashboard"))

    res = supabase.table("projects").select("*").eq("id", project_id).single().execute()
    project = res.data
    if not project:
        abort(404)

    if request.method == "POST":
        title       = bleach.clean(request.form.get("title", "").strip())
        location    = bleach.clean(request.form.get("location", "").strip())
        category    = bleach.clean(request.form.get("category", "").strip())
        description = bleach.clean(request.form.get("description", "").strip())
        featured    = request.form.get("featured") == "on"

        updates = {
            "title": title,
            "location": location,
            "category": category,
            "description": description,
            "featured": featured,
        }

        file = request.files.get("image")
        if file and file.filename:
            if not allowed_file(file.filename):
                flash("Only JPG, PNG or WEBP images are allowed.", "error")
                return redirect(url_for("admin_edit", project_id=project_id))
            new_url = upload_image_to_supabase(file, file.filename)
            if new_url:
                delete_image_from_supabase(project.get("image_url", ""))
                updates["image_url"] = new_url

        supabase.table("projects").update(updates).eq("id", project_id).execute()
        flash("Project updated.", "success")
        return redirect(url_for("admin_dashboard"))

    return render_template("admin/edit.html", project=project)

# ── Admin: delete project ─────────────────────────────────────────────────────
@app.route("/admin/delete/<project_id>", methods=["POST"])
@login_required
def admin_delete(project_id):
    if not supabase:
        flash("Supabase not configured.", "error")
        return redirect(url_for("admin_dashboard"))
    res = supabase.table("projects").select("image_url").eq("id", project_id).single().execute()
    if res.data:
        delete_image_from_supabase(res.data.get("image_url", ""))
    supabase.table("projects").delete().eq("id", project_id).execute()
    flash("Project deleted.", "success")
    return redirect(url_for("admin_dashboard"))

# ── Error pages ───────────────────────────────────────────────────────────────
@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404

@app.errorhandler(500)
def server_error(e):
    return render_template("404.html", error="Server error. Please try again."), 500

@app.route('/google0843481c2fb28a34.html')
def google_verification():
    return send_from_directory('static', 'google0843481c2fb28a34.html')
# ── SEO: robots.txt ───────────────────────────────────────────────────────────
@app.route('/robots.txt')
def robots_txt():
    return send_from_directory('static', 'robots.txt')

# ── SEO: sitemap.xml ──────────────────────────────────────────────────────────
@app.route('/sitemap.xml')
def sitemap():
    today = datetime.utcnow().date().isoformat()
    pages = [
        {'loc': url_for('index',        _external=True), 'lastmod': today, 'priority': '1.0'},
        {'loc': url_for('services',     _external=True), 'lastmod': today, 'priority': '0.9'},
        {'loc': url_for('projects_page',_external=True), 'lastmod': today, 'priority': '0.8'},
        {'loc': url_for('contact',      _external=True), 'lastmod': today, 'priority': '0.7'},
        {'loc': url_for('about',        _external=True), 'lastmod': today, 'priority': '0.6'},
    ]
    xml = render_template('sitemap.xml', pages=pages)
    return Response(xml, mimetype='application/xml')

if __name__ == "__main__":
    app.run(debug=True)
