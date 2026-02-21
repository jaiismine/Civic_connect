"""
setup_satellite.py — CivicConnect Satellite System Installer
=============================================================
Run this ONCE:
    python setup_satellite.py

What it does:
  1. Installs all required packages
  2. Creates satellite database tables
  3. Patches app.py to register satellite routes
  4. Adds satellite link to admin sidebar
  5. Runs a demo scan so you can see it working immediately
"""

import os, sys, subprocess, sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))

def step(msg): print(f"\n{'='*56}\n  {msg}\n{'='*56}")
def ok(msg):   print(f"  ✅  {msg}")
def warn(msg): print(f"  ⚠️   {msg}")
def err(msg):  print(f"  ❌  {msg}")


# ── STEP 1: Install packages ──────────────────────────────────
step("STEP 1 — Installing required packages")
packages = ["opencv-python", "numpy", "requests", "Pillow",
            "imagehash", "geopy", "APScheduler"]
for pkg in packages:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pkg],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok(f"Installed: {pkg}")
    else:
        warn(f"{pkg} — may already be installed")


# ── STEP 2: Create database tables ───────────────────────────
step("STEP 2 — Setting up satellite database tables")
db_path = os.path.join(BASE, "civic_connect.db")

if not os.path.exists(db_path):
    warn("civic_connect.db not found — tables will be created on first app run")
else:
    conn = sqlite3.connect(db_path)

    conn.executescript("""
        CREATE TABLE IF NOT EXISTS satellite_scans (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_date     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            area_name     TEXT NOT NULL,
            latitude      REAL NOT NULL,
            longitude     REAL NOT NULL,
            radius_km     REAL DEFAULT 5.0,
            image_path    TEXT,
            issues_found  INTEGER DEFAULT 0,
            new_reports   INTEGER DEFAULT 0,
            confirmed     INTEGER DEFAULT 0,
            status        TEXT DEFAULT 'processing'
        );

        CREATE TABLE IF NOT EXISTS satellite_issues (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            scan_id            INTEGER NOT NULL,
            issue_type         TEXT NOT NULL,
            confidence         REAL DEFAULT 0.0,
            latitude           REAL,
            longitude          REAL,
            bbox_coords        TEXT,
            image_crop_path    TEXT,
            matched_report_id  INTEGER,
            action_taken       TEXT DEFAULT 'pending',
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS report_satellite_links (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id    INTEGER NOT NULL,
            scan_id      INTEGER NOT NULL,
            issue_id     INTEGER NOT NULL,
            link_type    TEXT DEFAULT 'confirmed',
            linked_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)

    for col, coltype in [
        ("source",              "TEXT DEFAULT 'citizen'"),
        ("satellite_confirmed", "INTEGER DEFAULT 0"),
        ("satellite_scan_id",   "INTEGER"),
    ]:
        try:
            conn.execute(f"ALTER TABLE reports ADD COLUMN {col} {coltype}")
            ok(f"Added column: {col}")
        except Exception:
            ok(f"Column already exists: {col}")

    conn.commit()
    conn.close()
    ok("All satellite tables created successfully")


# ── STEP 3: Create satellite folder ──────────────────────────
step("STEP 3 — Creating satellite image folder")
sat_folder = os.path.join(BASE, "static", "satellite")
os.makedirs(sat_folder, exist_ok=True)
ok(f"Created: static/satellite/")


# ── STEP 4: Patch app.py ─────────────────────────────────────
step("STEP 4 — Patching app.py to add satellite routes")
app_path = os.path.join(BASE, "app.py")

with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

if "satellite_routes" in content:
    ok("app.py already has satellite routes — skipping")
else:
    # Add import
    old_import = "from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify"
    new_import  = old_import + "\nfrom satellite_routes import sat_bp"

    if old_import in content:
        content = content.replace(old_import, new_import)
        ok("Added: from satellite_routes import sat_bp")
    else:
        content = "from satellite_routes import sat_bp\n" + content
        warn("Added import at top (fallback)")

    # Register blueprint
    old_flask = "app = Flask(__name__)"
    new_flask  = old_flask + "\napp.register_blueprint(sat_bp)"

    if old_flask in content and "register_blueprint(sat_bp)" not in content:
        content = content.replace(old_flask, new_flask)
        ok("Registered satellite blueprint")

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    ok("app.py patched successfully")


# ── STEP 5: Add satellite link to admin sidebar ───────────────
step("STEP 5 — Adding satellite link to admin sidebar")
admin_base = os.path.join(BASE, "templates", "admin", "base_admin.html")

if os.path.exists(admin_base):
    with open(admin_base, "r", encoding="utf-8") as f:
        html = f.read()

    if "satellite" in html:
        ok("Satellite link already in admin sidebar")
    else:
        old_nav = '<a href="{{ url_for(\'map_view\') }}" class="nav-item {% if request.endpoint==\'map_view\' %}active{% endif %}"><span class="nav-icon">🗺️</span> Reports Map</a>'
        new_nav  = old_nav + '\n      <a href="{{ url_for(\'satellite.satellite_dashboard\') }}" class="nav-item {% if request.endpoint==\'satellite.satellite_dashboard\' %}active{% endif %}"><span class="nav-icon">🛰️</span> Satellite</a>'

        if old_nav in html:
            html = html.replace(old_nav, new_nav)
            with open(admin_base, "w", encoding="utf-8") as f:
                f.write(html)
            ok("Added 🛰️ Satellite link to admin sidebar")
        else:
            warn("Could not auto-add sidebar link — add it manually to base_admin.html")
else:
    warn("base_admin.html not found — run setup.py first")


# ── STEP 6: Run demo scan ─────────────────────────────────────
step("STEP 6 — Running demo satellite scan")
print("  Running a demo scan of New York City...")
print("  (Uses mock satellite imagery for demonstration)")

try:
    sys.path.insert(0, BASE)
    from satellite_engine import run_satellite_scan, ensure_satellite_tables
    ensure_satellite_tables()

    results = run_satellite_scan(
        area_name = "New York City — Demo",
        latitude  = 40.7128,
        longitude = -74.0060,
        radius_km = 5.0
    )

    ok(f"Demo scan complete!")
    ok(f"Issues detected  : {results['total_detected']}")
    ok(f"New auto-reports : {results['new_reports']}")
    ok(f"Reports confirmed: {results['confirmed']}")

except Exception as e:
    warn(f"Demo scan failed: {e}")
    warn("Satellite features will still work when app is running")


# ── DONE ─────────────────────────────────────────────────────
step("SETUP COMPLETE ✅")
print("""
  Satellite Intelligence is now part of CivicConnect!

  ─────────────────────────────────────────────────
  HOW TO USE:
  ─────────────────────────────────────────────────
  1. Run:     python app.py
  2. Open:    http://127.0.0.1:5000
  3. Log in as admin (admin / admin123)
  4. Click 🛰️ Satellite in the left sidebar

  WHAT YOU CAN DO:
  ✅ View satellite-detected issues on map
  ✅ Run a manual scan for any city coordinates
  ✅ See which citizen reports were satellite confirmed
  ✅ View auto-generated satellite reports
  ✅ Track scan history and statistics

  FOR REAL SATELLITE IMAGERY:
  Sign up free at dataspace.copernicus.eu
  Add credentials to satellite_engine.py:
    SENTINEL_CLIENT_ID     = "your_id"
    SENTINEL_CLIENT_SECRET = "your_secret"
  ─────────────────────────────────────────────────
""")
