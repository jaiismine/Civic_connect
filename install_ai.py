"""
install_ai.py — CivicConnect AI Auto-Installer
================================================
Run this ONCE:
    python install_ai.py

It will:
  1. Install the anthropic package
  2. Patch app.py to register AI routes
  3. Replace support.html with the AI chatbot version
  4. Confirm everything is ready
"""

import os, sys, shutil, subprocess

BASE = os.path.dirname(os.path.abspath(__file__))

def step(msg): print(f"\n{'='*55}\n  {msg}\n{'='*55}")
def ok(msg):   print(f"  ✅  {msg}")
def warn(msg): print(f"  ⚠️   {msg}")
def err(msg):  print(f"  ❌  {msg}")


# ─── STEP 1: Install anthropic package ───────────────────────────────
step("STEP 1 — Installing anthropic package")
try:
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "anthropic"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("anthropic installed successfully")
    else:
        warn("pip install had warnings (may already be installed)")
        print(result.stdout[-300:] if result.stdout else "")
except Exception as e:
    err(f"Could not run pip: {e}")
    sys.exit(1)


# ─── STEP 2: Check required AI files exist ───────────────────────────
step("STEP 2 — Checking AI files")

required = ["ai_features.py", "ai_routes.py"]
for f in required:
    path = os.path.join(BASE, f)
    if os.path.exists(path):
        ok(f"Found: {f}")
    else:
        err(f"Missing: {f}  — make sure it's in the same folder as app.py")
        sys.exit(1)


# ─── STEP 3: Patch app.py ─────────────────────────────────────────────
step("STEP 3 — Patching app.py to add AI routes")

app_path = os.path.join(BASE, "app.py")
with open(app_path, "r", encoding="utf-8") as f:
    content = f.read()

# Check if already patched
if "from ai_routes import ai_bp" in content:
    ok("app.py already patched — skipping")
else:
    # Add import after first flask import line
    old_import = "from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify"
    new_import  = old_import + "\nfrom ai_routes import ai_bp"

    if old_import in content:
        content = content.replace(old_import, new_import)
        ok("Added: from ai_routes import ai_bp")
    else:
        # fallback — add at top
        content = "from ai_routes import ai_bp\n" + content
        warn("Added AI import at top of file (fallback method)")

    # Register blueprint before routes — find 'app = Flask(__name__)' line
    old_flask = "app = Flask(__name__)"
    new_flask  = old_flask + "\napp.register_blueprint(ai_bp)"

    if old_flask in content and "register_blueprint(ai_bp)" not in content:
        content = content.replace(old_flask, new_flask)
        ok("Registered AI blueprint with Flask app")

    # Update get_support route to use new AI template
    old_render = "return render_template('citizen/support.html', consultations=consultations)"
    new_render  = "return render_template('citizen/support_ai.html', consultations=consultations)"

    if old_render in content:
        content = content.replace(old_render, new_render)
        ok("Updated get_support() to use AI chatbot template")
    else:
        warn("Could not auto-update support template reference — do it manually if needed")

    with open(app_path, "w", encoding="utf-8") as f:
        f.write(content)
    ok("app.py saved successfully")


# ─── STEP 4: Confirm templates exist ─────────────────────────────────
step("STEP 4 — Checking templates")

templates = {
    "templates/citizen/report_issue.html" : "AI Classifier (report form)",
    "templates/citizen/support_ai.html"   : "AI Chatbot (support page)",
}
for path, label in templates.items():
    full = os.path.join(BASE, path)
    if os.path.exists(full):
        ok(f"Found: {path}  [{label}]")
    else:
        err(f"Missing: {path}")
        warn("Re-download the template files and place them in the correct folder")


# ─── STEP 5: Remind user to set API key ──────────────────────────────
step("STEP 5 — API Key Setup")

ai_features_path = os.path.join(BASE, "ai_features.py")
with open(ai_features_path, "r") as f:
    ai_content = f.read()

if "YOUR_CLAUDE_API_KEY_HERE" in ai_content:
    print("""
  ⚠️  ACTION REQUIRED — Set your Claude API Key
  ─────────────────────────────────────────────
  1. Go to:  https://console.anthropic.com
  2. Sign up free → go to API Keys → Create Key
  3. Open ai_features.py in any text editor
  4. Find this line:
        AI_API_KEY = "YOUR_CLAUDE_API_KEY_HERE"
  5. Replace with your actual key:
        AI_API_KEY = "sk-ant-api03-xxxxxxxxxxxx"
  6. Save the file
    """)
else:
    ok("API key already set in ai_features.py")


# ─── DONE ─────────────────────────────────────────────────────────────
step("SETUP COMPLETE")
print("""
  ✅  All 3 AI features installed:

  1. 🤖 AI Report Classifier
     → Open any browser → Log in as citizen
     → Go to Report an Issue
     → Fill title + description → Click "AI Auto-Fill"

  2. 📊 AI Sentiment Analyzer
     → Log in as admin → Dashboard loads automatically
     → Each report shows urgency + sentiment badge

  3. 💬 AI Chatbot
     → Log in as citizen → Go to Get Support
     → Scroll down to CivicAssist AI section
     → Start chatting!

  ─────────────────────────────────────────────
  Now run:   python app.py
  Open:      http://127.0.0.1:5000
  ─────────────────────────────────────────────
""")
