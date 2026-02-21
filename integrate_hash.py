"""
integrate_hash.py — Auto-integrates image hashing into CivicConnect
====================================================================
Run this ONCE:
    python integrate_hash.py

What it does:
  1. Installs required packages (Pillow, imagehash, geopy)
  2. Adds image_hash column to your database
  3. Patches app.py report_issue() route to use duplicate detection
  4. Confirms everything is ready
"""

import os, sys, subprocess, sqlite3

BASE = os.path.dirname(os.path.abspath(__file__))

def step(msg): print(f"\n{'='*55}\n  {msg}\n{'='*55}")
def ok(msg):   print(f"  ✅  {msg}")
def warn(msg): print(f"  ⚠️   {msg}")
def err(msg):  print(f"  ❌  {msg}")


# ── STEP 1: Install packages ──────────────────────────────────
step("STEP 1 — Installing required packages")
packages = ["Pillow", "imagehash", "geopy"]
for pkg in packages:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", pkg],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok(f"Installed: {pkg}")
    else:
        warn(f"{pkg} may already be installed")


# ── STEP 2: Add image_hash column to database ─────────────────
step("STEP 2 — Updating database schema")
db_path = os.path.join(BASE, "civic_connect.db")
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("ALTER TABLE reports ADD COLUMN image_hash TEXT")
        conn.commit()
        ok("Added image_hash column to reports table")
    except Exception:
        ok("image_hash column already exists — skipping")
    conn.close()
else:
    warn("civic_connect.db not found — column will be created when app first runs")


# ── STEP 3: Check image_hash_util.py exists ───────────────────
step("STEP 3 — Checking image_hash_util.py")
util_path = os.path.join(BASE, "image_hash_util.py")
if os.path.exists(util_path):
    ok("Found: image_hash_util.py")
else:
    err("Missing: image_hash_util.py — place it in the same folder as app.py")
    sys.exit(1)


# ── STEP 4: Patch app.py ──────────────────────────────────────
step("STEP 4 — Patching app.py")

app_path = os.path.join(BASE, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Already patched?
if "image_hash_util" in content:
    ok("app.py already has image hash integration — skipping patch")
else:
    # 1. Add import at top
    old_import = "from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify"
    new_import  = old_import + "\nfrom image_hash_util import process_uploaded_image, save_image_hash"

    if old_import in content:
        content = content.replace(old_import, new_import)
        ok("Added image_hash_util import to app.py")
    else:
        content = "from image_hash_util import process_uploaded_image, save_image_hash\n" + content
        warn("Added import at top (fallback method)")

    # 2. Replace the image handling block inside report_issue route
    OLD_IMAGE_BLOCK = """        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename and allowed_file(f.filename):
                filename   = secure_filename(f"{uuid.uuid4().hex}_{f.filename}")
                save_path  = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                f.save(save_path)
                image_path = f'uploads/{filename}'"""

    NEW_IMAGE_BLOCK = """        if 'image' in request.files:
            f = request.files['image']
            if f and f.filename and allowed_file(f.filename):
                result = process_uploaded_image(f, app.config['UPLOAD_FOLDER'])
                image_path = result['saved_path']
                # ── Duplicate image detection ──
                if result['is_duplicate']:
                    flash(
                        f"⚠️ Duplicate image detected! This photo was already used in report "
                        f"{result['report_id']} — '{result['title']}'. "
                        f"Please check that report or submit a new photo.",
                        'warning'
                    )
                    return redirect(url_for('report_issue'))"""

    if OLD_IMAGE_BLOCK in content:
        content = content.replace(OLD_IMAGE_BLOCK, NEW_IMAGE_BLOCK)
        ok("Replaced image upload block with duplicate detection")
    else:
        warn("Could not find exact image block — will do manual patch below")

    # 3. After db.execute INSERT for new report, add save_image_hash call
    OLD_COMMIT = """        db.commit()
        db.close()
        flash(f'Report {report_id} submitted successfully!', 'success')
        return redirect(url_for('track_reports'))"""

    NEW_COMMIT = """        db.commit()
        # Save image hash for duplicate detection
        if image_path:
            new_report = db.execute("SELECT id FROM reports WHERE report_id=?", (report_id,)).fetchone()
            if new_report:
                from image_hash_util import save_image_hash as _save_hash
                try:
                    from image_hash_util import get_image_hash as _get_hash
                    import os as _os
                    full_path = _os.path.join('static', image_path)
                    _hash = _get_hash(full_path)
                    _save_hash(new_report['id'], _hash)
                except Exception:
                    pass
        db.close()
        flash(f'Report {report_id} submitted successfully!', 'success')
        return redirect(url_for('track_reports'))"""

    if OLD_COMMIT in content:
        content = content.replace(OLD_COMMIT, NEW_COMMIT)
        ok("Added hash save after report insert")

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    ok("app.py saved successfully")


# ── DONE ──────────────────────────────────────────────────────
step("INTEGRATION COMPLETE ✅")
print("""
  How it works:
  ─────────────────────────────────────────────
  1. Citizen uploads a photo in Report an Issue
  2. System generates a perceptual hash (pHash)
  3. Hash is compared against all previous reports
  4. DUPLICATE → citizen sees a warning message
               → redirect back to form
  5. NEW IMAGE → report saved normally
               → hash stored for future checks

  ─────────────────────────────────────────────
  Now run:   python app.py
  Then go to: http://127.0.0.1:5000

  Test by uploading the SAME photo twice in
  two different reports — you'll see the warning!
  ─────────────────────────────────────────────
""")
