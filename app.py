from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from satellite_routes import sat_bp
from image_hash_util import process_uploaded_image, save_image_hash
from ai_routes import ai_bp
import sqlite3, os, json, uuid, base64
from datetime import datetime, timedelta
from functools import wraps
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)
app.register_blueprint(sat_bp)
app.register_blueprint(ai_bp)
app.secret_key = 'civic_connect_secret_2024'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# ─────────────────────────────────────────
# DATABASE SETUP
# ─────────────────────────────────────────
def get_db():
    db = sqlite3.connect('civic_connect.db')
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = get_db()
    db.executescript('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'citizen',
            full_name TEXT,
            email TEXT,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            location_address TEXT,
            latitude REAL,
            longitude REAL,
            image_path TEXT,
            status TEXT DEFAULT 'Pending',
            severity TEXT DEFAULT 'Medium',
            admin_notes TEXT,
            label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS community_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            message TEXT,
            likes INTEGER DEFAULT 0,
            dislikes INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES reports(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS post_reactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            reaction TEXT NOT NULL,
            UNIQUE(post_id, user_id)
        );

        CREATE TABLE IF NOT EXISTS surveys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            q1 TEXT, q2 TEXT, q3 TEXT, q4 TEXT, q5 TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );

        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            department TEXT,
            message TEXT,
            status TEXT DEFAULT 'Open',
            admin_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    ''')

    # Seed default users
    try:
        db.execute("INSERT OR IGNORE INTO users (username,password,role,full_name,email) VALUES (?,?,?,?,?)",
                   ('admin', 'admin123', 'admin', 'City Administrator', 'admin@civicconnect.gov'))
        db.execute("INSERT OR IGNORE INTO users (username,password,role,full_name,email,phone) VALUES (?,?,?,?,?,?)",
                   ('citizen1', 'pass123', 'citizen', 'John Smith', 'john@example.com', '555-0101'))
        db.execute("INSERT OR IGNORE INTO users (username,password,role,full_name,email,phone) VALUES (?,?,?,?,?,?)",
                   ('jane', 'pass123', 'citizen', 'Jane Doe', 'jane@example.com', '555-0202'))

        # Seed sample reports
        sample_reports = [
            ('RPT-001', 2, 'Broken Street Light', 'Infrastructure', 'Street light on Main St has been off for a week.', '123 Main St', 40.7128, -74.0060, 'Pending', 'High'),
            ('RPT-002', 2, 'Pothole on 5th Avenue', 'Roads', 'Large pothole causing traffic issues.', '5th Ave & 23rd', 40.7450, -73.9920, 'In Progress', 'Critical'),
            ('RPT-003', 3, 'Garbage Not Collected', 'Sanitation', 'Waste not picked up for 2 weeks.', '456 Oak Ave', 40.7300, -74.0100, 'Resolved', 'Low'),
            ('RPT-004', 2, 'Water Leakage', 'Utilities', 'Pipe burst near the community park.', 'Central Park Rd', 40.7850, -73.9680, 'Pending', 'Critical'),
            ('RPT-005', 3, 'Damaged Sidewalk', 'Infrastructure', 'Cracked pavement causing pedestrian hazard.', '789 Elm Street', 40.7200, -74.0050, 'Pending', 'Medium'),
        ]
        for r in sample_reports:
            db.execute('''INSERT OR IGNORE INTO reports 
                (report_id,user_id,title,category,description,location_address,latitude,longitude,status,severity)
                VALUES (?,?,?,?,?,?,?,?,?,?)''', r)

        # Seed community posts
        db.execute("INSERT OR IGNORE INTO community_posts (report_id,user_id,message,likes,dislikes) VALUES (?,?,?,?,?)",
                   (2, 3, 'This pothole damaged my car tire! Needs immediate attention.', 12, 1))
        db.execute("INSERT OR IGNORE INTO community_posts (report_id,user_id,message,likes,dislikes) VALUES (?,?,?,?,?)",
                   (4, 2, 'Water leakage is getting worse. Entire street is flooded!', 18, 0))

        db.commit()
    except Exception as e:
        print(f"Seed error (likely already seeded): {e}")
    db.close()

# ─────────────────────────────────────────
# AUTH DECORATORS
# ─────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def citizen_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'citizen':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# ─────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        role     = request.form.get('role', 'citizen')

        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username=? AND password=? AND role=?',
                          (username, password, role)).fetchone()
        db.close()

        if user:
            session['user_id']   = user['id']
            session['username']  = user['username']
            session['role']      = user['role']
            session['full_name'] = user['full_name']
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('citizen_dashboard'))
        flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ─────────────────────────────────────────
# CITIZEN ROUTES
# ─────────────────────────────────────────
@app.route('/citizen/dashboard')
@citizen_required
def citizen_dashboard():
    db = get_db()
    reports = db.execute('SELECT * FROM reports WHERE user_id=? ORDER BY created_at DESC LIMIT 5',
                         (session['user_id'],)).fetchall()
    total   = db.execute('SELECT COUNT(*) FROM reports WHERE user_id=?', (session['user_id'],)).fetchone()[0]
    pending = db.execute("SELECT COUNT(*) FROM reports WHERE user_id=? AND status='Pending'", (session['user_id'],)).fetchone()[0]
    resolved= db.execute("SELECT COUNT(*) FROM reports WHERE user_id=? AND status='Resolved'", (session['user_id'],)).fetchone()[0]
    db.close()
    return render_template('citizen/dashboard.html', reports=reports, total=total, pending=pending, resolved=resolved)

@app.route('/citizen/report', methods=['GET', 'POST'])
@citizen_required
def report_issue():
    if request.method == 'POST':
        title       = request.form.get('title')
        category    = request.form.get('category')
        description = request.form.get('description')
        address     = request.form.get('address')
        latitude    = request.form.get('latitude')
        longitude   = request.form.get('longitude')
        severity    = request.form.get('severity', 'Medium')
        image_path  = None

        if 'image' in request.files:
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
                    return redirect(url_for('report_issue'))

        report_id = f"RPT-{uuid.uuid4().hex[:6].upper()}"
        db = get_db()
        db.execute('''INSERT INTO reports (report_id,user_id,title,category,description,
                      location_address,latitude,longitude,image_path,severity)
                      VALUES (?,?,?,?,?,?,?,?,?,?)''',
                   (report_id, session['user_id'], title, category, description,
                    address, latitude, longitude, image_path, severity))
        db.commit()
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
        return redirect(url_for('track_reports'))
    return render_template('citizen/report_issue.html')

@app.route('/citizen/track')
@citizen_required
def track_reports():
    db = get_db()
    reports = db.execute('SELECT * FROM reports WHERE user_id=? ORDER BY created_at DESC',
                         (session['user_id'],)).fetchall()
    db.close()
    return render_template('citizen/track_reports.html', reports=reports)

@app.route('/citizen/survey', methods=['GET', 'POST'])
@citizen_required
def survey():
    already = False
    db = get_db()
    existing = db.execute('SELECT id FROM surveys WHERE user_id=?', (session['user_id'],)).fetchone()
    if existing:
        already = True
    if request.method == 'POST' and not already:
        q1 = request.form.get('q1'); q2 = request.form.get('q2')
        q3 = request.form.get('q3'); q4 = request.form.get('q4')
        q5 = request.form.get('q5')
        db.execute('INSERT INTO surveys (user_id,q1,q2,q3,q4,q5) VALUES (?,?,?,?,?,?)',
                   (session['user_id'], q1, q2, q3, q4, q5))
        db.commit()
        db.close()
        flash('Thank you for completing the survey!', 'success')
        return redirect(url_for('citizen_dashboard'))
    db.close()
    return render_template('citizen/survey.html', already=already)

@app.route('/citizen/community')
@citizen_required
def community():
    db = get_db()
    posts = db.execute('''
        SELECT cp.*, r.title as report_title, r.category, r.status, r.severity,
               u.full_name as author
        FROM community_posts cp
        JOIN reports r ON cp.report_id = r.id
        JOIN users u ON cp.user_id = u.id
        ORDER BY cp.created_at DESC
    ''').fetchall()
    # Reports eligible to be forwarded (Pending > 3 days or In Progress with no update)
    eligible = db.execute('''SELECT * FROM reports WHERE user_id=? AND status != 'Resolved' ''',
                          (session['user_id'],)).fetchall()
    db.close()
    return render_template('citizen/community.html', posts=posts, eligible_reports=eligible)

@app.route('/citizen/community/forward', methods=['POST'])
@citizen_required
def forward_report():
    report_id = request.form.get('report_id')
    message   = request.form.get('message', 'Forwarding this report to the community — no response received yet.')
    db = get_db()
    report = db.execute('SELECT * FROM reports WHERE id=? AND user_id=?',
                        (report_id, session['user_id'])).fetchone()
    if report:
        db.execute('INSERT INTO community_posts (report_id,user_id,message) VALUES (?,?,?)',
                   (report_id, session['user_id'], message))
        db.commit()
        flash('Report forwarded to community!', 'success')
    db.close()
    return redirect(url_for('community'))

@app.route('/citizen/community/react', methods=['POST'])
@citizen_required
def react_post():
    post_id  = request.form.get('post_id')
    reaction = request.form.get('reaction')  # 'like' or 'dislike'
    db = get_db()
    existing = db.execute('SELECT * FROM post_reactions WHERE post_id=? AND user_id=?',
                          (post_id, session['user_id'])).fetchone()
    if existing:
        if existing['reaction'] == reaction:
            db.execute('DELETE FROM post_reactions WHERE post_id=? AND user_id=?', (post_id, session['user_id']))
            col = 'likes' if reaction == 'like' else 'dislikes'
            db.execute(f'UPDATE community_posts SET {col}={col}-1 WHERE id=?', (post_id,))
        else:
            db.execute('UPDATE post_reactions SET reaction=? WHERE post_id=? AND user_id=?',
                       (reaction, post_id, session['user_id']))
            old_col = 'dislikes' if reaction == 'like' else 'likes'
            new_col = 'likes' if reaction == 'like' else 'dislikes'
            db.execute(f'UPDATE community_posts SET {old_col}={old_col}-1, {new_col}={new_col}+1 WHERE id=?', (post_id,))
    else:
        db.execute('INSERT INTO post_reactions (post_id,user_id,reaction) VALUES (?,?,?)',
                   (post_id, session['user_id'], reaction))
        col = 'likes' if reaction == 'like' else 'dislikes'
        db.execute(f'UPDATE community_posts SET {col}={col}+1 WHERE id=?', (post_id,))
    db.commit()
    db.close()
    return redirect(url_for('community'))

@app.route('/citizen/support', methods=['GET', 'POST'])
@citizen_required
def get_support():
    if request.method == 'POST':
        ctype      = request.form.get('type')
        department = request.form.get('department')
        message    = request.form.get('message')
        db = get_db()
        db.execute('INSERT INTO consultations (user_id,type,department,message) VALUES (?,?,?,?)',
                   (session['user_id'], ctype, department, message))
        db.commit()
        db.close()
        flash(f'Your {ctype} request has been submitted!', 'success')
        return redirect(url_for('get_support'))
    db = get_db()
    consultations = db.execute('SELECT * FROM consultations WHERE user_id=? ORDER BY created_at DESC',
                               (session['user_id'],)).fetchall()
    db.close()
    return render_template('citizen/support_ai.html', consultations=consultations)

# ─────────────────────────────────────────
# ADMIN ROUTES
# ─────────────────────────────────────────
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    db = get_db()
    reports  = db.execute('SELECT r.*, u.full_name FROM reports r JOIN users u ON r.user_id=u.id ORDER BY r.created_at DESC').fetchall()
    total    = db.execute('SELECT COUNT(*) FROM reports').fetchone()[0]
    pending  = db.execute("SELECT COUNT(*) FROM reports WHERE status='Pending'").fetchone()[0]
    progress = db.execute("SELECT COUNT(*) FROM reports WHERE status='In Progress'").fetchone()[0]
    resolved = db.execute("SELECT COUNT(*) FROM reports WHERE status='Resolved'").fetchone()[0]
    critical = db.execute("SELECT COUNT(*) FROM reports WHERE severity='Critical'").fetchone()[0]
    citizens = db.execute("SELECT COUNT(*) FROM users WHERE role='citizen'").fetchone()[0]
    db.close()
    stats = dict(total=total, pending=pending, progress=progress, resolved=resolved,
                 critical=critical, citizens=citizens)
    return render_template('admin/dashboard.html', reports=reports, stats=stats)

@app.route('/admin/report/update', methods=['POST'])
@admin_required
def update_report():
    report_id   = request.form.get('report_id')
    status      = request.form.get('status')
    severity    = request.form.get('severity')
    label       = request.form.get('label')
    admin_notes = request.form.get('admin_notes')
    db = get_db()
    db.execute('''UPDATE reports SET status=?, severity=?, label=?, admin_notes=?,
                  updated_at=CURRENT_TIMESTAMP WHERE id=?''',
               (status, severity, label, admin_notes, report_id))
    db.commit()
    db.close()
    flash('Report updated successfully!', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/weather')
@admin_required
def weather_alert():
    # Mock 5-day weather data (replace with real API key for live data)
    today = datetime.now()
    weather_data = []
    conditions = ['Sunny', 'Partly Cloudy', 'Heavy Rain', 'Thunderstorm', 'Cloudy']
    icons       = ['☀️', '⛅', '🌧️', '⛈️', '☁️']
    temps       = [(28, 18), (25, 16), (19, 13), (17, 11), (22, 15)]
    for i in range(5):
        day = today + timedelta(days=i)
        idx = i % len(conditions)
        weather_data.append({
            'date':      day.strftime('%A, %b %d'),
            'condition': conditions[idx],
            'icon':      icons[idx],
            'high':      temps[i][0],
            'low':       temps[i][1],
            'rain_chance': random.randint(10, 90),
            'wind':      random.randint(5, 40),
            'alert':     conditions[idx] in ['Heavy Rain', 'Thunderstorm']
        })
    db = get_db()
    critical_reports = db.execute(
        "SELECT r.*, u.full_name FROM reports r JOIN users u ON r.user_id=u.id WHERE r.severity IN ('Critical','High') AND r.status!='Resolved' ORDER BY r.created_at DESC"
    ).fetchall()
    db.close()
    return render_template('admin/weather_alert.html', weather=weather_data, critical_reports=critical_reports)

@app.route('/admin/map')
@admin_required
def map_view():
    db = get_db()
    reports = db.execute('''SELECT r.*, u.full_name FROM reports r JOIN users u ON r.user_id=u.id
                            WHERE r.latitude IS NOT NULL AND r.longitude IS NOT NULL''').fetchall()
    reports_list = [dict(r) for r in reports]
    db.close()
    return render_template('admin/map_view.html', reports=reports_list, reports_json=json.dumps(reports_list))

# ─────────────────────────────────────────
# API ENDPOINTS
# ─────────────────────────────────────────
@app.route('/api/reports/stats')
@admin_required
def report_stats_api():
    db = get_db()
    by_category = db.execute("SELECT category, COUNT(*) as count FROM reports GROUP BY category").fetchall()
    by_severity = db.execute("SELECT severity, COUNT(*) as count FROM reports GROUP BY severity").fetchall()
    db.close()
    return jsonify({
        'by_category': [dict(r) for r in by_category],
        'by_severity': [dict(r) for r in by_severity]
    })

if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
