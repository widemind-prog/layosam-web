# LAYOSAM — Full Web Service
**Flask · Supabase · Render · Python**

Solar & electrical business website with admin panel for project uploads.

---

## Project Structure

```
layosam/
├── app.py                   ← Flask application (all routes)
├── requirements.txt         ← Python dependencies
├── render.yaml              ← Render deployment config
├── supabase_schema.sql      ← Run once in Supabase SQL Editor
├── .env.example             ← Copy to .env and fill values
├── .gitignore
│
├── static/
│   ├── css/
│   │   ├── main.css         ← Shared brand styles (all public pages)
│   │   └── admin.css        ← Admin panel styles
│   ├── js/
│   │   ├── main.js          ← Nav, reveal, counter, filter chips
│   │   └── admin.js         ← File drop zone, confirm delete, flash
│   ├── images/              ← Brand images (logo etc.)
│   └── project/             ← Static fallback project photos (optional)
│
└── templates/
    ├── base.html            ← Public nav + footer + sticky bar
    ├── _wa_icon.html        ← WhatsApp SVG partial
    ├── _project_card.html   ← Reusable project card partial
    ├── index.html           ← Landing page (full original design)
    ├── about.html           ← About page
    ├── services.html        ← Services detail page
    ├── projects.html        ← All projects + filter + pagination
    ├── contact.html         ← Contact page
    ├── 404.html             ← Error page
    └── admin/
        ├── base_admin.html  ← Admin layout
        ├── login.html       ← Password login
        ├── dashboard.html   ← Project list with edit/delete
        ├── upload.html      ← Upload new project
        └── edit.html        ← Edit existing project
```

---

## Step 1 — Supabase Setup

1. Go to **https://supabase.com** and create a free project.
2. In **SQL Editor**, paste the entire contents of `supabase_schema.sql` and click **Run**.
3. Go to **Project Settings → API** and copy:
   - **Project URL** → `SUPABASE_URL`
   - **service_role** key (not anon) → `SUPABASE_KEY`
4. The storage bucket `layosam-projects` is created by the SQL script.
   If you prefer, create it manually in **Storage → New Bucket** (set to Public).

---

## Step 2 — Local Development

```bash
# Clone your repo or unzip the project folder
cd layosam

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create your .env file
cp .env.example .env
# Edit .env — fill in SECRET_KEY, ADMIN_PASSWORD, SUPABASE_URL, SUPABASE_KEY

# Run locally
python app.py
# Visit http://localhost:5000
```

---

## Step 3 — GitHub

```bash
git init
git add .
git commit -m "Initial Layosam web service"
git remote add origin https://github.com/YOUR_USERNAME/layosam.git
git push -u origin main
```

**Important:** `.gitignore` already excludes `.env`. Never push your real credentials.

---

## Step 4 — Deploy on Render

1. Go to **https://render.com** and sign in with GitHub.
2. Click **New → Web Service**.
3. Select your `layosam` GitHub repository.
4. Render auto-detects `render.yaml`. Confirm these settings:
   - **Runtime:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn app:app --workers 2 --bind 0.0.0.0:$PORT --timeout 120`
5. Under **Environment Variables**, add:
   ```
   ADMIN_PASSWORD     your-strong-password
   SUPABASE_URL       https://your-project.supabase.co
   SUPABASE_KEY       your-service-role-key
   SUPABASE_BUCKET    layosam-projects
   SECRET_KEY         (click Generate — Render creates this automatically)
   ```
6. Click **Create Web Service**. Deploy takes ~2 minutes.

---

## Admin Panel

| URL | What it does |
|-----|--------------|
| `/admin/login` | Password login |
| `/admin` | Dashboard — all projects, edit, delete |
| `/admin/upload` | Upload new project with photo |
| `/admin/edit/<id>` | Edit title, location, category, photo |
| `/admin/logout` | Log out |

**How to upload a project:**
1. Go to `/admin/login` and enter your `ADMIN_PASSWORD`.
2. Click **Upload New**.
3. Fill in title, location, category, optional description.
4. Tap the photo drop zone and select a JPG/PNG/WEBP (max 8 MB).
5. Click **Upload Project**.

The photo uploads to Supabase Storage. The project metadata saves to the `projects` table.
The landing page and projects page pull from Supabase automatically — no redeploy needed.

---

## Public Pages

| URL | Page |
|-----|------|
| `/` | Landing page (identical brand to original) |
| `/about` | About Layosam |
| `/services` | Service detail page |
| `/projects` | All completed projects (paginated, filterable) |
| `/contact` | Contact page |

---

## Environment Variables Reference

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Flask session secret (long random string) |
| `ADMIN_PASSWORD` | Password to log into `/admin` |
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_KEY` | Supabase **service_role** key (server-side only) |
| `SUPABASE_BUCKET` | Storage bucket name (`layosam-projects`) |

---

## Adding Static Fallback Photos

If Supabase is not yet configured, the landing page falls back to local images.
Place them in `static/project/` named:
```
project1.jpg  project2.jpg  project3.jpg
project4.jpg  project5.jpg  project6.jpg
```

---

## Notes

- The admin panel has no rate limiting on the login form by default.
  For production, consider adding fail2ban or Cloudflare in front of Render.
- The service-role Supabase key bypasses Row Level Security.
  It is only used server-side inside Flask — it is never exposed to the browser.
- Light/dark theme switches automatically based on the device OS preference
  (`prefers-color-scheme`). No toggle needed.
