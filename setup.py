"""
CivicConnect Setup Script
Run this once: python setup.py
It will create all folders and template files automatically.
"""
import os

BASE = os.path.dirname(os.path.abspath(__file__))

# ── Create all required directories ──────────────────────────────────────────
dirs = [
    "templates/citizen",
    "templates/admin",
    "static/css",
    "static/js",
    "static/uploads",
]
for d in dirs:
    os.makedirs(os.path.join(BASE, d), exist_ok=True)
    print(f"✅ Created folder: {d}")

# ── Move existing flat files to correct locations ─────────────────────────────
moves = {
    "style.css": "static/css/style.css",
    "main.js":   "static/js/main.js",
    "login.html":"templates/login.html",
}
for src, dst in moves.items():
    src_path = os.path.join(BASE, src)
    dst_path = os.path.join(BASE, dst)
    if os.path.exists(src_path) and not os.path.exists(dst_path):
        import shutil
        shutil.move(src_path, dst_path)
        print(f"📦 Moved: {src} → {dst}")

# ── Write all template files ───────────────────────────────────────────────────

TEMPLATES = {}

# ─── LOGIN ───────────────────────────────────────────────────────────────────
TEMPLATES["templates/login.html"] = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>CivicConnect — Login</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
</head>
<body>
<div class="login-page">
  <div class="login-hero">
    <div class="hero-logo">🏛️</div>
    <h1 class="hero-title">CivicConnect</h1>
    <p class="hero-sub">Bridging citizens and government for a smarter, more responsive community.</p>
    <div class="hero-features">
      <div class="hero-feat"><span>📍</span><span>Report civic issues with location tracking</span></div>
      <div class="hero-feat"><span>📊</span><span>Track your reports in real-time</span></div>
      <div class="hero-feat"><span>🤝</span><span>Engage with your community</span></div>
      <div class="hero-feat"><span>🗺️</span><span>Admin map & weather intelligence</span></div>
      <div class="hero-feat"><span>💬</span><span>Direct consultation with officials</span></div>
    </div>
  </div>
  <div class="login-form-wrap">
    <div class="login-card">
      <h2>Welcome Back</h2>
      <p>Sign in to your account to continue.</p>
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }}" style="margin-top:16px">
            {{ '✅' if category == 'success' else '❌' }} {{ message }}
          </div>
        {% endfor %}
      {% endwith %}
      <div class="role-toggle">
        <button type="button" class="role-btn active" data-role="citizen">👤 Citizen Portal</button>
        <button type="button" class="role-btn" data-role="admin">🛡️ Admin Portal</button>
      </div>
      <form method="POST" action="/login">
        <input type="hidden" name="role" id="roleInput" value="citizen">
        <div class="form-group">
          <label>Username</label>
          <input type="text" name="username" placeholder="Enter your username" required autofocus>
        </div>
        <div class="form-group">
          <label>Password</label>
          <input type="password" name="password" placeholder="Enter your password" required>
        </div>
        <button type="submit" class="btn btn-primary btn-full" style="margin-top:6px">Sign In →</button>
      </form>
      <div style="margin-top:28px;padding:16px;background:#f8fafc;border-radius:10px;border:1px solid #e2e8f0">
        <p style="font-size:.8rem;font-weight:700;color:#64748b;margin-bottom:10px;text-transform:uppercase;letter-spacing:.5px">Demo Credentials</p>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;font-size:.83rem">
          <div style="padding:10px;background:#fff;border-radius:8px;border:1px solid #e2e8f0">
            <div style="font-weight:700;color:#1a56db;margin-bottom:4px">👤 Citizen</div>
            <div>user: <code>citizen1</code></div>
            <div>pass: <code>pass123</code></div>
          </div>
          <div style="padding:10px;background:#fff;border-radius:8px;border:1px solid #e2e8f0">
            <div style="font-weight:700;color:#dc2626;margin-bottom:4px">🛡️ Admin</div>
            <div>user: <code>admin</code></div>
            <div>pass: <code>admin123</code></div>
          </div>
        </div>
      </div>
      <p style="text-align:center;margin-top:20px;font-size:.82rem;color:#94a3b8">© 2024 CivicConnect · City Administration Portal</p>
    </div>
  </div>
</div>
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
</body>
</html>
"""

# ─── CITIZEN BASE ─────────────────────────────────────────────────────────────
TEMPLATES["templates/citizen/base_citizen.html"] = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}CivicConnect{% endblock %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  {% block head %}{% endblock %}
</head>
<body>
<div class="app-layout">
  <aside class="sidebar">
    <a href="{{ url_for('citizen_dashboard') }}" class="sidebar-brand">
      <span class="brand-icon">🏛️</span>
      <div><div class="brand-text">CivicConnect</div><div class="brand-sub">Citizen Portal</div></div>
    </a>
    <div class="sidebar-user">
      <div class="user-avatar">{{ session.full_name[0].upper() if session.full_name else 'C' }}</div>
      <div>
        <div class="user-name">{{ session.full_name or session.username }}</div>
        <div class="user-role">Citizen</div>
      </div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section-title">Main Menu</div>
      <a href="{{ url_for('citizen_dashboard') }}" class="nav-item {% if request.endpoint == 'citizen_dashboard' %}active{% endif %}"><span class="nav-icon">🏠</span> Dashboard</a>
      <a href="{{ url_for('report_issue') }}" class="nav-item {% if request.endpoint == 'report_issue' %}active{% endif %}"><span class="nav-icon">📍</span> Report an Issue</a>
      <a href="{{ url_for('track_reports') }}" class="nav-item {% if request.endpoint == 'track_reports' %}active{% endif %}"><span class="nav-icon">📋</span> Track Reports</a>
      <a href="{{ url_for('survey') }}" class="nav-item {% if request.endpoint == 'survey' %}active{% endif %}"><span class="nav-icon">📝</span> Take Survey</a>
      <div class="nav-section-title">Community</div>
      <a href="{{ url_for('community') }}" class="nav-item {% if request.endpoint == 'community' %}active{% endif %}"><span class="nav-icon">🤝</span> Community Tab</a>
      <a href="{{ url_for('get_support') }}" class="nav-item {% if request.endpoint == 'get_support' %}active{% endif %}"><span class="nav-icon">💬</span> Get Support</a>
    </nav>
    <div class="sidebar-footer">
      <a href="{{ url_for('logout') }}" class="btn btn-outline btn-full" style="color:#94a3b8;border-color:rgba(255,255,255,.1);font-size:.85rem">🚪 Sign Out</a>
    </div>
  </aside>
  <div class="main-content">
    <div class="topbar">
      <div class="topbar-title">
        <h1>{% block page_title %}Dashboard{% endblock %}</h1>
        <p>{% block page_sub %}Welcome back, {{ session.full_name }}{% endblock %}</p>
      </div>
      <div class="topbar-actions">
        <span class="topbar-time" id="live-clock"></span>
        <a href="{{ url_for('report_issue') }}" class="btn btn-primary btn-sm">+ New Report</a>
      </div>
    </div>
    <div class="page-body">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }}">{{ '✅' if category == 'success' else '❌' }} {{ message }}</div>
        {% endfor %}
      {% endwith %}
      {% block content %}{% endblock %}
    </div>
  </div>
</div>
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
{% block scripts %}{% endblock %}
</body>
</html>
"""

# ─── CITIZEN DASHBOARD ────────────────────────────────────────────────────────
TEMPLATES["templates/citizen/dashboard.html"] = r"""{% extends "citizen/base_citizen.html" %}
{% block title %}Dashboard — CivicConnect{% endblock %}
{% block page_title %}My Dashboard{% endblock %}
{% block page_sub %}Here's an overview of your civic activity{% endblock %}
{% block content %}
<div class="stats-grid">
  <div class="stat-card blue"><div class="stat-icon">📋</div><div class="stat-val">{{ total }}</div><div class="stat-label">Total Reports</div></div>
  <div class="stat-card orange"><div class="stat-icon">⏳</div><div class="stat-val">{{ pending }}</div><div class="stat-label">Pending</div></div>
  <div class="stat-card green"><div class="stat-icon">✅</div><div class="stat-val">{{ resolved }}</div><div class="stat-label">Resolved</div></div>
  <div class="stat-card cyan"><div class="stat-icon">🔄</div><div class="stat-val">{{ total - pending - resolved }}</div><div class="stat-label">In Progress</div></div>
</div>
<div class="card mb-6">
  <div class="card-header"><div class="card-title">⚡ Quick Actions</div></div>
  <div class="card-body">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px">
      <a href="{{ url_for('report_issue') }}" class="btn btn-primary" style="flex-direction:column;gap:6px;padding:20px"><span style="font-size:1.8rem">📍</span><span>Report Issue</span></a>
      <a href="{{ url_for('track_reports') }}" class="btn btn-outline" style="flex-direction:column;gap:6px;padding:20px"><span style="font-size:1.8rem">📋</span><span>Track Reports</span></a>
      <a href="{{ url_for('community') }}" class="btn btn-outline" style="flex-direction:column;gap:6px;padding:20px"><span style="font-size:1.8rem">🤝</span><span>Community</span></a>
      <a href="{{ url_for('get_support') }}" class="btn btn-outline" style="flex-direction:column;gap:6px;padding:20px"><span style="font-size:1.8rem">💬</span><span>Get Support</span></a>
      <a href="{{ url_for('survey') }}" class="btn btn-outline" style="flex-direction:column;gap:6px;padding:20px"><span style="font-size:1.8rem">📝</span><span>Take Survey</span></a>
    </div>
  </div>
</div>
<div class="card">
  <div class="card-header"><div class="card-title">🕒 Recent Reports</div><a href="{{ url_for('track_reports') }}" class="btn btn-outline btn-sm">View All</a></div>
  <div class="card-body" style="padding:0">
    {% if reports %}
    <div class="table-wrap">
      <table>
        <thead><tr><th>Report ID</th><th>Title</th><th>Category</th><th>Severity</th><th>Status</th><th>Date</th></tr></thead>
        <tbody>
          {% for r in reports %}
          <tr>
            <td><code style="font-size:.8rem;color:#1a56db">{{ r['report_id'] }}</code></td>
            <td><strong>{{ r['title'] }}</strong></td>
            <td><span style="background:#f1f5f9;padding:3px 10px;border-radius:99px;font-size:.8rem">{{ r['category'] }}</span></td>
            <td>{% set sev=r['severity'] %}<span class="badge badge-{{ sev.lower() }}">{% if sev=='Critical' %}🔴{% elif sev=='High' %}🟠{% elif sev=='Medium' %}🟡{% else %}🟢{% endif %} {{ sev }}</span></td>
            <td>{% set st=r['status'] %}<span class="badge badge-{{ 'progress' if st=='In Progress' else st.lower() }}">{% if st=='Pending' %}⏳{% elif st=='In Progress' %}🔄{% elif st=='Resolved' %}✅{% else %}❌{% endif %} {{ st }}</span></td>
            <td class="text-muted text-sm">{{ r['created_at'][:10] }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
    {% else %}
    <div style="text-align:center;padding:48px;color:#94a3b8">
      <div style="font-size:3rem;margin-bottom:12px">📭</div>
      <div style="font-weight:600;font-size:1.05rem">No reports yet</div>
      <p style="font-size:.88rem;margin:8px 0 20px">Be the first to help improve your community!</p>
      <a href="{{ url_for('report_issue') }}" class="btn btn-primary">+ Submit First Report</a>
    </div>
    {% endif %}
  </div>
</div>
{% endblock %}
"""

# ─── REPORT ISSUE ─────────────────────────────────────────────────────────────
TEMPLATES["templates/citizen/report_issue.html"] = r"""{% extends "citizen/base_citizen.html" %}
{% block title %}Report Issue — CivicConnect{% endblock %}
{% block page_title %}Report an Issue{% endblock %}
{% block page_sub %}Submit a new civic issue with location and photo{% endblock %}
{% block head %}
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
{% endblock %}
{% block content %}
<form method="POST" action="{{ url_for('report_issue') }}" enctype="multipart/form-data">
  <div style="display:grid;grid-template-columns:1.2fr 1fr;gap:24px;align-items:start">
    <div>
      <div class="card mb-4">
        <div class="card-header"><div class="card-title">📋 Issue Details</div></div>
        <div class="card-body">
          <div class="form-group"><label>Issue Title *</label><input type="text" name="title" placeholder="Brief title of the issue" required></div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div class="form-group"><label>Category *</label>
              <select name="category" required>
                <option value="">Select Category</option>
                <option>Roads</option><option>Infrastructure</option><option>Sanitation</option>
                <option>Utilities</option><option>Parks & Recreation</option><option>Public Safety</option>
                <option>Drainage</option><option>Street Lighting</option><option>Other</option>
              </select>
            </div>
            <div class="form-group"><label>Severity Level *</label>
              <select name="severity" required>
                <option value="Low">🟢 Low</option><option value="Medium" selected>🟡 Medium</option>
                <option value="High">🟠 High</option><option value="Critical">🔴 Critical</option>
              </select>
            </div>
          </div>
          <div class="form-group"><label>Description *</label><textarea name="description" placeholder="Describe the issue in detail..." required></textarea></div>
        </div>
      </div>
      <div class="card mb-4">
        <div class="card-header"><div class="card-title">📸 Photo Evidence</div></div>
        <div class="card-body">
          <div class="image-drop-zone">
            <input type="file" name="image" id="imageFile" accept="image/*">
            <div class="drop-icon">📷</div>
            <div class="drop-text">Click or drag to upload photo</div>
            <div class="drop-sub">Supports JPG, PNG, WebP • Max 10MB</div>
          </div>
          <img id="imagePreview" src="" alt="Preview" style="max-width:100%;border-radius:8px;margin-top:12px;display:none">
        </div>
      </div>
      <button type="submit" class="btn btn-primary btn-full" style="padding:14px">🚀 Submit Report</button>
    </div>
    <div>
      <div class="card" style="position:sticky;top:80px">
        <div class="card-header">
          <div class="card-title">📍 Location</div>
          <button type="button" id="getLocationBtn" class="btn btn-accent btn-sm">📡 Auto-Detect My Location</button>
        </div>
        <div class="card-body">
          <p class="text-sm text-muted mb-4">Click the button to auto-detect, or click on the map to drop a pin.</p>
          <div class="map-preview"><div id="previewMap"></div></div>
          <div class="form-group mt-4"><label>Address / Location Description</label><input type="text" name="address" id="addrInput" placeholder="Auto-filled or enter manually"></div>
          <input type="hidden" name="latitude" id="latInput">
          <input type="hidden" name="longitude" id="lngInput">
          <div style="background:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:12px;margin-top:8px">
            <p style="font-size:.82rem;color:#92400e">💡 <strong>Tip:</strong> Enable location services in your browser for best results.</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</form>
{% endblock %}
"""

# ─── TRACK REPORTS ────────────────────────────────────────────────────────────
TEMPLATES["templates/citizen/track_reports.html"] = r"""{% extends "citizen/base_citizen.html" %}
{% block title %}Track Reports — CivicConnect{% endblock %}
{% block page_title %}My Reports{% endblock %}
{% block page_sub %}Track the status of all your submitted reports{% endblock %}
{% block content %}
<div class="card mb-6">
  <div class="card-body" style="padding:16px 22px">
    <div style="display:flex;gap:10px;flex-wrap:wrap;align-items:center">
      <span class="text-sm fw-700" style="color:#64748b">Filter:</span>
      <button class="btn btn-sm btn-primary filter-btn" onclick="filterReports('all',this)">All</button>
      <button class="btn btn-sm btn-outline filter-btn" onclick="filterReports('Pending',this)">⏳ Pending</button>
      <button class="btn btn-sm btn-outline filter-btn" onclick="filterReports('In Progress',this)">🔄 In Progress</button>
      <button class="btn btn-sm btn-outline filter-btn" onclick="filterReports('Resolved',this)">✅ Resolved</button>
    </div>
  </div>
</div>
{% if reports %}
<div id="reportsList">
  {% for r in reports %}
  <div class="report-card" data-status="{{ r['status'] }}" onclick="toggleDetail('d{{ r['id'] }}')">
    <div>
      <div class="rc-id">{{ r['report_id'] }} · {{ r['created_at'][:10] }}</div>
      <div class="rc-title">{{ r['title'] }}</div>
      <div class="rc-meta">
        <span class="rc-cat">{{ r['category'] }}</span>
        {% set sev=r['severity'] %}<span class="badge badge-{{ sev.lower() }}">{% if sev=='Critical' %}🔴{% elif sev=='High' %}🟠{% elif sev=='Medium' %}🟡{% else %}🟢{% endif %} {{ sev }}</span>
        {% if r['label'] %}<span class="badge badge-info">🏷️ {{ r['label'] }}</span>{% endif %}
      </div>
    </div>
    <div class="rc-right">
      {% set st=r['status'] %}<span class="badge badge-{{ 'progress' if st=='In Progress' else st.lower() }}" style="font-size:.85rem;padding:6px 14px">{% if st=='Pending' %}⏳{% elif st=='In Progress' %}🔄{% elif st=='Resolved' %}✅{% else %}❌{% endif %} {{ st }}</span>
    </div>
    <div id="d{{ r['id'] }}" style="grid-column:1/-1;display:none;border-top:1px solid #e2e8f0;padding-top:16px;margin-top:4px" onclick="event.stopPropagation()">
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">
        <div>
          <p class="text-sm fw-700 mb-4" style="color:#64748b">DESCRIPTION</p>
          <p class="text-sm">{{ r['description'] }}</p>
          {% if r['location_address'] %}<p class="text-sm mt-4"><strong>📍 Location:</strong> {{ r['location_address'] }}</p>{% endif %}
          {% if r['admin_notes'] %}
          <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:12px;margin-top:12px">
            <p class="text-sm fw-700" style="color:#1e40af;margin-bottom:4px">💬 Admin Notes</p>
            <p class="text-sm">{{ r['admin_notes'] }}</p>
          </div>
          {% endif %}
        </div>
        <div>
          {% if r['image_path'] %}<p class="text-sm fw-700 mb-4" style="color:#64748b">PHOTO</p><img src="{{ url_for('static', filename=r['image_path']) }}" style="max-width:100%;border-radius:8px;max-height:180px;object-fit:cover">{% endif %}
          <p class="text-sm fw-700 mt-4 mb-4" style="color:#64748b">TIMELINE</p>
          <div class="timeline">
            <div class="tl-item"><strong>Submitted</strong> — {{ r['created_at'][:16] }}</div>
            {% if r['status'] in ['In Progress','Resolved'] %}<div class="tl-item"><strong>Under Review</strong> — Admin assigned</div>{% endif %}
            {% if r['status']=='Resolved' %}<div class="tl-item" style="color:#16a34a"><strong>✅ Resolved</strong> — {{ r['updated_at'][:16] }}</div>{% endif %}
          </div>
        </div>
      </div>
      <div style="margin-top:16px;display:flex;gap:10px">
        <a href="{{ url_for('community') }}" class="btn btn-outline btn-sm">🤝 Forward to Community</a>
        <a href="{{ url_for('get_support') }}" class="btn btn-outline btn-sm">💬 Get Support</a>
      </div>
    </div>
  </div>
  {% endfor %}
</div>
{% else %}
<div class="card"><div class="card-body" style="text-align:center;padding:64px 32px">
  <div style="font-size:4rem;margin-bottom:16px">📭</div>
  <h3>No reports submitted yet</h3>
  <p class="text-muted" style="margin:10px 0 24px">Help make your community better by reporting issues.</p>
  <a href="{{ url_for('report_issue') }}" class="btn btn-primary">+ Submit First Report</a>
</div></div>
{% endif %}
{% endblock %}
{% block scripts %}
<script>
function filterReports(status,btn){document.querySelectorAll('.filter-btn').forEach(b=>{b.className='btn btn-sm btn-outline filter-btn'});btn.className='btn btn-sm btn-primary filter-btn';document.querySelectorAll('.report-card').forEach(card=>{card.style.display=(status==='all'||card.dataset.status===status)?'':'none'});}
function toggleDetail(id){const el=document.getElementById(id);el.style.display=el.style.display==='block'?'none':'block';}
</script>
{% endblock %}
"""

# ─── SURVEY ───────────────────────────────────────────────────────────────────
TEMPLATES["templates/citizen/survey.html"] = r"""{% extends "citizen/base_citizen.html" %}
{% block title %}Survey — CivicConnect{% endblock %}
{% block page_title %}Citizen Satisfaction Survey{% endblock %}
{% block page_sub %}Help us improve city services with your feedback{% endblock %}
{% block content %}
<div class="survey-wrap">
{% if already %}
<div class="card"><div class="card-body" style="text-align:center;padding:64px 32px">
  <div style="font-size:4rem;margin-bottom:16px">🎉</div>
  <h3>Thank you for your feedback!</h3>
  <p class="text-muted" style="margin:10px 0 24px">You have already completed this survey.</p>
  <a href="{{ url_for('citizen_dashboard') }}" class="btn btn-primary">← Back to Dashboard</a>
</div></div>
{% else %}
<div class="card mb-6">
  <div class="card-body" style="padding:16px 22px">
    <div style="display:flex;justify-content:space-between;margin-bottom:8px">
      <span class="text-sm fw-700">Survey Progress</span>
      <span class="text-sm text-muted" id="progressLabel">0 / 5 questions answered</span>
    </div>
    <div class="progress-bar"><div class="progress-fill" id="progressFill" style="width:0%;background:linear-gradient(90deg,#1a56db,#0ea5e9)"></div></div>
  </div>
</div>
<form method="POST" action="{{ url_for('survey') }}">
  {% set questions = [
    ('q1','How satisfied are you with the overall quality of city services?',['Very Satisfied','Satisfied','Neutral','Dissatisfied','Very Dissatisfied']),
    ('q2','How would you rate the responsiveness of city officials?',['Excellent','Good','Average','Poor','Very Poor']),
    ('q3','Which city service needs the most improvement?',['Roads & Infrastructure','Sanitation & Waste','Street Lighting','Water & Utilities','Parks & Public Spaces']),
    ('q4','How often do you experience civic issues requiring reporting?',['Daily','Weekly','Monthly','Rarely','Never']),
    ('q5','How likely are you to recommend CivicConnect to a neighbor?',['Definitely Would','Probably Would','Unsure','Probably Would Not','Definitely Would Not'])
  ] %}
  {% for name,text,opts in questions %}
  <div class="survey-q">
    <div class="survey-q-num">Question {{ loop.index }} of 5</div>
    <div class="survey-q-text">{{ text }}</div>
    <div class="radio-group">
      {% for opt in opts %}
      <label class="radio-option"><input type="radio" name="{{ name }}" value="{{ opt }}" onchange="updateProgress()" required><span>{{ opt }}</span></label>
      {% endfor %}
    </div>
  </div>
  {% endfor %}
  <button type="submit" class="btn btn-primary btn-full" style="padding:14px;font-size:1rem">📤 Submit Survey</button>
</form>
{% endif %}
</div>
{% endblock %}
{% block scripts %}
<script>
function updateProgress(){let a=0;for(let i=1;i<=5;i++){if(document.querySelector(`input[name="q${i}"]:checked`))a++;}document.getElementById('progressLabel').textContent=`${a} / 5 questions answered`;document.getElementById('progressFill').style.width=`${(a/5)*100}%`;}
</script>
{% endblock %}
"""

# ─── COMMUNITY ────────────────────────────────────────────────────────────────
TEMPLATES["templates/citizen/community.html"] = r"""{% extends "citizen/base_citizen.html" %}
{% block title %}Community — CivicConnect{% endblock %}
{% block page_title %}Community Tab{% endblock %}
{% block page_sub %}Forward unresolved reports and engage with your community{% endblock %}
{% block content %}
<div style="display:grid;grid-template-columns:1fr 360px;gap:24px;align-items:start">
  <div>
    <div class="section-title">🗣️ Community Reports Feed</div>
    {% if posts %}
      {% for post in posts %}
      <div class="community-post">
        <div class="post-header">
          <div class="post-author">
            <div class="post-avatar">{{ post['author'][0].upper() }}</div>
            <div><div class="post-name">{{ post['author'] }}</div><div class="post-time">{{ post['created_at'][:16] }}</div></div>
          </div>
          <div style="display:flex;gap:8px;align-items:center">
            {% set sev=post['severity'] %}<span class="badge badge-{{ sev.lower() }}">{% if sev=='Critical' %}🔴{% elif sev=='High' %}🟠{% elif sev=='Medium' %}🟡{% else %}🟢{% endif %} {{ sev }}</span>
            <span class="badge badge-{{ 'progress' if post['status']=='In Progress' else post['status'].lower() }}">{{ post['status'] }}</span>
          </div>
        </div>
        <div class="post-title">📌 {{ post['report_title'] }}</div>
        <div style="font-size:.8rem;color:#94a3b8;margin-bottom:8px">Category: {{ post['category'] }}</div>
        <div class="post-message">{{ post['message'] }}</div>
        <div class="post-actions">
          <form method="POST" action="{{ url_for('react_post') }}" style="display:inline">
            <input type="hidden" name="post_id" value="{{ post['id'] }}"><input type="hidden" name="reaction" value="like">
            <button type="submit" class="react-btn">👍 <span>{{ post['likes'] }}</span></button>
          </form>
          <form method="POST" action="{{ url_for('react_post') }}" style="display:inline">
            <input type="hidden" name="post_id" value="{{ post['id'] }}"><input type="hidden" name="reaction" value="dislike">
            <button type="submit" class="react-btn">👎 <span>{{ post['dislikes'] }}</span></button>
          </form>
          <span class="text-sm text-muted" style="margin-left:auto">{{ post['likes']+post['dislikes'] }} reactions</span>
        </div>
      </div>
      {% endfor %}
    {% else %}
    <div class="card"><div class="card-body" style="text-align:center;padding:64px 32px">
      <div style="font-size:4rem;margin-bottom:16px">🤝</div>
      <h3>No community posts yet</h3>
      <p class="text-muted">Be the first to forward a report!</p>
    </div></div>
    {% endif %}
  </div>
  <div>
    <div class="card" style="position:sticky;top:80px">
      <div class="card-header"><div class="card-title">📢 Forward a Report</div></div>
      <div class="card-body">
        <p class="text-sm text-muted mb-4">Got no response? Forward your report to raise community awareness.</p>
        {% if eligible_reports %}
        <form method="POST" action="{{ url_for('forward_report') }}">
          <div class="form-group"><label>Select Your Report</label>
            <select name="report_id" required><option value="">Choose a report...</option>
              {% for r in eligible_reports %}<option value="{{ r['id'] }}">{{ r['report_id'] }} – {{ r['title'] }}</option>{% endfor %}
            </select>
          </div>
          <div class="form-group"><label>Message to Community</label><textarea name="message">Forwarding this report to the community — still awaiting a response from authorities.</textarea></div>
          <button type="submit" class="btn btn-primary btn-full">📢 Forward to Community</button>
        </form>
        {% else %}
        <div style="text-align:center;padding:24px 0;color:#94a3b8">
          <div style="font-size:2.5rem;margin-bottom:10px">✅</div>
          <p class="text-sm">All your reports are resolved.</p>
          <a href="{{ url_for('report_issue') }}" class="btn btn-primary btn-sm mt-4">+ New Report</a>
        </div>
        {% endif %}
      </div>
    </div>
    <div class="card mt-4">
      <div class="card-header"><div class="card-title">📜 Community Guidelines</div></div>
      <div class="card-body">
        <ul style="list-style:none;display:flex;flex-direction:column;gap:10px">
          <li class="text-sm">✅ Be respectful and constructive</li>
          <li class="text-sm">✅ Only forward genuine unresolved issues</li>
          <li class="text-sm">✅ Include relevant details in your message</li>
          <li class="text-sm">🚫 No personal attacks or hate speech</li>
          <li class="text-sm">🚫 No spam or duplicate posts</li>
        </ul>
      </div>
    </div>
  </div>
</div>
{% endblock %}
"""

# ─── SUPPORT ─────────────────────────────────────────────────────────────────
TEMPLATES["templates/citizen/support.html"] = r"""{% extends "citizen/base_citizen.html" %}
{% block title %}Get Support — CivicConnect{% endblock %}
{% block page_title %}Get Support{% endblock %}
{% block page_sub %}Reach city officials directly for assistance{% endblock %}
{% block content %}
<div class="section-title">🎯 Choose Support Type</div>
<div class="support-cards mb-6">
  <div class="support-option"><div class="support-icon">🎯</div><div class="support-title">Start Consultation</div><div class="support-desc">Schedule a formal consultation with the relevant department.</div><button class="btn btn-primary btn-sm" style="margin-top:16px" onclick="selectSupport(this,'Start Consultation')">Request Consultation</button></div>
  <div class="support-option"><div class="support-icon">💬</div><div class="support-title">Active Chat</div><div class="support-desc">Start a real-time chat session with a city representative.</div><button class="btn btn-accent btn-sm" style="margin-top:16px" onclick="selectSupport(this,'Active Chat')">Start Chat</button></div>
  <div class="support-option"><div class="support-icon">⚡</div><div class="support-title">Quick Connect</div><div class="support-desc">Get a fast response from priority departments for urgent matters.</div><button class="btn btn-danger btn-sm" style="margin-top:16px" onclick="selectSupport(this,'Quick Connect')">Quick Connect</button></div>
</div>
<div id="supportForm" style="display:none">
  <div class="card mb-6">
    <div class="card-header"><div class="card-title">📝 Submit Request</div><span id="selectedTypeLabel" class="badge badge-info"></span></div>
    <div class="card-body">
      <form method="POST" action="{{ url_for('get_support') }}">
        <input type="hidden" name="type" id="supportType">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
          <div class="form-group"><label>Department *</label>
            <select name="department" required><option value="">Select Department</option>
              <option>Roads & Infrastructure</option><option>Sanitation & Environment</option>
              <option>Water & Utilities</option><option>Public Safety</option>
              <option>Parks & Recreation</option><option>Emergency Services</option>
              <option>City Planning</option><option>General Enquiry</option>
            </select>
          </div>
          <div class="form-group"><label>Priority</label><select name="priority"><option>Normal</option><option>High</option><option>Urgent</option></select></div>
        </div>
        <div class="form-group"><label>Your Message *</label><textarea name="message" placeholder="Describe your issue or request in detail..." required style="min-height:140px"></textarea></div>
        <div style="display:flex;gap:12px">
          <button type="submit" class="btn btn-primary">📤 Submit Request</button>
          <button type="button" class="btn btn-outline" onclick="document.getElementById('supportForm').style.display='none'">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</div>
<div class="section-title">📁 My Support Requests</div>
{% if consultations %}
<div class="card"><div class="card-body" style="padding:0"><div class="table-wrap"><table>
  <thead><tr><th>Type</th><th>Department</th><th>Message</th><th>Status</th><th>Admin Reply</th><th>Date</th></tr></thead>
  <tbody>
    {% for c in consultations %}
    <tr>
      <td>{% if c['type']=='Start Consultation' %}🎯{% elif c['type']=='Active Chat' %}💬{% else %}⚡{% endif %} <strong>{{ c['type'] }}</strong></td>
      <td>{{ c['department'] or '—' }}</td>
      <td><span style="font-size:.85rem;color:#64748b;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:220px">{{ c['message'] }}</span></td>
      <td><span class="badge badge-{{ 'progress' if c['status']=='Open' else 'resolved' }}">{{ '🔓 Open' if c['status']=='Open' else '✅ Closed' }}</span></td>
      <td class="text-sm">{{ c['admin_reply'] or 'Awaiting reply...' }}</td>
      <td class="text-muted text-sm">{{ c['created_at'][:10] }}</td>
    </tr>
    {% endfor %}
  </tbody>
</table></div></div></div>
{% else %}
<div class="card"><div class="card-body" style="text-align:center;padding:48px"><div style="font-size:3rem;margin-bottom:12px">📭</div><h3>No support requests yet</h3><p class="text-muted">Choose a support type above to get started.</p></div></div>
{% endif %}
<div class="card mt-6">
  <div class="card-header"><div class="card-title">📞 Emergency Contacts</div></div>
  <div class="card-body">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px">
      <div style="padding:16px;background:#fff5f5;border:1px solid #fecaca;border-radius:10px;text-align:center"><div style="font-size:2rem;margin-bottom:8px">🚨</div><div style="font-weight:700;color:#dc2626">Emergency</div><div style="font-size:1.2rem;font-weight:800;color:#991b1b">911</div></div>
      <div style="padding:16px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;text-align:center"><div style="font-size:2rem;margin-bottom:8px">🏛️</div><div style="font-weight:700;color:#1e40af">City Hall</div><div style="font-size:.95rem;color:#1e40af">(555) 100-2000</div></div>
      <div style="padding:16px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;text-align:center"><div style="font-size:2rem;margin-bottom:8px">💧</div><div style="font-weight:700;color:#166534">Water Dept.</div><div style="font-size:.95rem;color:#166534">(555) 100-3000</div></div>
      <div style="padding:16px;background:#fefce8;border:1px solid #fde68a;border-radius:10px;text-align:center"><div style="font-size:2rem;margin-bottom:8px">🔧</div><div style="font-weight:700;color:#92400e">Public Works</div><div style="font-size:.95rem;color:#92400e">(555) 100-4000</div></div>
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
function selectSupport(btn,type){document.getElementById('supportType').value=type;document.getElementById('selectedTypeLabel').textContent=type;const f=document.getElementById('supportForm');f.style.display='block';f.scrollIntoView({behavior:'smooth'});}
</script>
{% endblock %}
"""

# ─── ADMIN BASE ───────────────────────────────────────────────────────────────
TEMPLATES["templates/admin/base_admin.html"] = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{% block title %}Admin — CivicConnect{% endblock %}</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
  {% block head %}{% endblock %}
</head>
<body>
<div class="app-layout">
  <aside class="sidebar" style="background:#0f0f23">
    <a href="{{ url_for('admin_dashboard') }}" class="sidebar-brand">
      <span class="brand-icon">🛡️</span>
      <div><div class="brand-text">CivicConnect</div><div class="brand-sub">Admin Panel</div></div>
    </a>
    <div class="sidebar-user">
      <div class="user-avatar" style="background:linear-gradient(135deg,#dc2626,#ea580c)">A</div>
      <div><div class="user-name">{{ session.full_name or session.username }}</div><div class="user-role">Administrator</div></div>
    </div>
    <nav class="sidebar-nav">
      <div class="nav-section-title">Administration</div>
      <a href="{{ url_for('admin_dashboard') }}" class="nav-item {% if request.endpoint=='admin_dashboard' %}active{% endif %}"><span class="nav-icon">📊</span> Dashboard</a>
      <a href="{{ url_for('weather_alert') }}" class="nav-item {% if request.endpoint=='weather_alert' %}active{% endif %}"><span class="nav-icon">🌤️</span> Weather Alerts</a>
      <a href="{{ url_for('map_view') }}" class="nav-item {% if request.endpoint=='map_view' %}active{% endif %}"><span class="nav-icon">🗺️</span> Reports Map</a>
    </nav>
    <div class="sidebar-footer">
      <a href="{{ url_for('logout') }}" class="btn btn-outline btn-full" style="color:#94a3b8;border-color:rgba(255,255,255,.1);font-size:.85rem">🚪 Sign Out</a>
    </div>
  </aside>
  <div class="main-content">
    <div class="topbar">
      <div class="topbar-title">
        <h1>{% block page_title %}Dashboard{% endblock %}</h1>
        <p>{% block page_sub %}City Administration Panel{% endblock %}</p>
      </div>
      <div class="topbar-actions">
        <span class="topbar-time" id="live-clock"></span>
        <span class="badge badge-critical">🛡️ Admin</span>
      </div>
    </div>
    <div class="page-body">
      {% with messages = get_flashed_messages(with_categories=true) %}
        {% for category, message in messages %}
          <div class="alert alert-{{ category }}">{{ '✅' if category=='success' else '❌' }} {{ message }}</div>
        {% endfor %}
      {% endwith %}
      {% block content %}{% endblock %}
    </div>
  </div>
</div>
<script src="{{ url_for('static', filename='js/main.js') }}"></script>
{% block scripts %}{% endblock %}
</body>
</html>
"""

# ─── ADMIN DASHBOARD ─────────────────────────────────────────────────────────
TEMPLATES["templates/admin/dashboard.html"] = r"""{% extends "admin/base_admin.html" %}
{% block title %}Admin Dashboard — CivicConnect{% endblock %}
{% block page_title %}Reports Dashboard{% endblock %}
{% block page_sub %}Manage, track, and resolve citizen reports{% endblock %}
{% block content %}
<div class="stats-grid">
  <div class="stat-card blue"><div class="stat-icon">📋</div><div class="stat-val">{{ stats.total }}</div><div class="stat-label">Total Reports</div></div>
  <div class="stat-card orange"><div class="stat-icon">⏳</div><div class="stat-val">{{ stats.pending }}</div><div class="stat-label">Pending</div></div>
  <div class="stat-card cyan"><div class="stat-icon">🔄</div><div class="stat-val">{{ stats.progress }}</div><div class="stat-label">In Progress</div></div>
  <div class="stat-card green"><div class="stat-icon">✅</div><div class="stat-val">{{ stats.resolved }}</div><div class="stat-label">Resolved</div></div>
  <div class="stat-card red"><div class="stat-icon">🔴</div><div class="stat-val">{{ stats.critical }}</div><div class="stat-label">Critical</div></div>
  <div class="stat-card purple"><div class="stat-icon">👥</div><div class="stat-val">{{ stats.citizens }}</div><div class="stat-label">Citizens</div></div>
</div>
<div class="card mb-4">
  <div class="card-body" style="padding:14px 22px">
    <div style="display:flex;gap:12px;flex-wrap:wrap;align-items:center">
      <input type="text" id="searchInput" onkeyup="filterTable()" placeholder="🔍 Search reports..." style="padding:8px 14px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:.9rem;outline:none;min-width:220px">
      <select id="statusFilter" onchange="filterTable()" style="padding:8px 14px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:.9rem;outline:none"><option value="">All Statuses</option><option>Pending</option><option>In Progress</option><option>Resolved</option><option>Rejected</option></select>
      <select id="severityFilter" onchange="filterTable()" style="padding:8px 14px;border:1.5px solid #e2e8f0;border-radius:8px;font-size:.9rem;outline:none"><option value="">All Severities</option><option>Critical</option><option>High</option><option>Medium</option><option>Low</option></select>
      <a href="{{ url_for('map_view') }}" class="btn btn-outline btn-sm" style="margin-left:auto">🗺️ View on Map</a>
    </div>
  </div>
</div>
<div class="card">
  <div class="card-header"><div class="card-title">📋 All Citizen Reports</div><span class="text-sm text-muted">{{ reports|length }} total reports</span></div>
  <div class="card-body" style="padding:0">
    <div class="table-wrap">
      <table id="reportsTable">
        <thead><tr><th>Report ID</th><th>Citizen</th><th>Title</th><th>Category</th><th>Severity</th><th>Status</th><th>Label</th><th>Date</th><th>Actions</th></tr></thead>
        <tbody>
          {% for r in reports %}
          <tr data-status="{{ r['status'] }}" data-severity="{{ r['severity'] }}" data-search="{{ r['title'].lower() }} {{ r['full_name'].lower() }} {{ r['category'].lower() }} {{ r['report_id'].lower() }}">
            <td><code style="font-size:.8rem;color:#1a56db">{{ r['report_id'] }}</code></td>
            <td><div style="display:flex;align-items:center;gap:8px"><div class="user-avatar" style="width:28px;height:28px;font-size:.75rem">{{ r['full_name'][0] }}</div><span class="text-sm">{{ r['full_name'] }}</span></div></td>
            <td><strong style="font-size:.9rem">{{ r['title'] }}</strong>{% if r['admin_notes'] %}<div style="font-size:.78rem;color:#94a3b8;margin-top:2px">💬 Has notes</div>{% endif %}</td>
            <td><span style="background:#f1f5f9;padding:3px 9px;border-radius:99px;font-size:.8rem">{{ r['category'] }}</span></td>
            <td>{% set sev=r['severity'] %}<span class="badge badge-{{ sev.lower() }}">{% if sev=='Critical' %}🔴{% elif sev=='High' %}🟠{% elif sev=='Medium' %}🟡{% else %}🟢{% endif %} {{ sev }}</span></td>
            <td>{% set st=r['status'] %}<span class="badge badge-{{ 'progress' if st=='In Progress' else st.lower() }}">{% if st=='Pending' %}⏳{% elif st=='In Progress' %}🔄{% elif st=='Resolved' %}✅{% else %}❌{% endif %} {{ st }}</span></td>
            <td>{% if r['label'] %}<span class="badge badge-info">🏷️ {{ r['label'] }}</span>{% else %}<span class="text-muted text-sm">—</span>{% endif %}</td>
            <td class="text-sm text-muted">{{ r['created_at'][:10] }}</td>
            <td><button onclick="openEditModal({{ r['id'] }},'{{ r['status'] }}','{{ r['severity'] }}','{{ r['label'] or '' }}',`{{ r['admin_notes'] or '' }}`)" class="btn btn-outline btn-sm">✏️ Edit</button></td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
<div class="modal-overlay" id="editModal">
  <div class="modal">
    <div class="modal-header"><div class="modal-title">✏️ Update Report</div><button class="modal-close" onclick="closeModal('editModal')">×</button></div>
    <div class="modal-body">
      <form method="POST" action="{{ url_for('update_report') }}">
        <input type="hidden" name="report_id" id="editReportId">
        <div class="form-group"><label>Status</label><select name="status" id="editStatus"><option>Pending</option><option>In Progress</option><option>Resolved</option><option>Rejected</option></select></div>
        <div class="form-group"><label>Severity</label><select name="severity" id="editSeverity"><option>Low</option><option>Medium</option><option>High</option><option>Critical</option></select></div>
        <div class="form-group"><label>Label / Tag</label><select name="label" id="editLabel"><option value="">No Label</option><option>Verified</option><option>Duplicate</option><option>Urgent</option><option>Weather-Related</option><option>Needs Site Visit</option><option>Escalated</option></select></div>
        <div class="form-group"><label>Admin Notes</label><textarea name="admin_notes" id="editNotes" placeholder="Add internal notes or feedback to citizen..."></textarea></div>
        <div style="display:flex;gap:12px"><button type="submit" class="btn btn-primary">💾 Save Changes</button><button type="button" class="btn btn-outline" onclick="closeModal('editModal')">Cancel</button></div>
      </form>
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
function openEditModal(id,status,severity,label,notes){document.getElementById('editReportId').value=id;document.getElementById('editStatus').value=status;document.getElementById('editSeverity').value=severity;document.getElementById('editLabel').value=label;document.getElementById('editNotes').value=notes;openModal('editModal');}
function filterTable(){const s=document.getElementById('searchInput').value.toLowerCase();const st=document.getElementById('statusFilter').value;const sv=document.getElementById('severityFilter').value;document.querySelectorAll('#reportsTable tbody tr').forEach(row=>{row.style.display=(!s||row.dataset.search.includes(s))&&(!st||row.dataset.status===st)&&(!sv||row.dataset.severity===sv)?'':'none';});}
</script>
{% endblock %}
"""

# ─── ADMIN WEATHER ────────────────────────────────────────────────────────────
TEMPLATES["templates/admin/weather_alert.html"] = r"""{% extends "admin/base_admin.html" %}
{% block title %}Weather Alerts — CivicConnect{% endblock %}
{% block page_title %}Weather Alerts{% endblock %}
{% block page_sub %}5-day forecast and weather-sensitive critical reports{% endblock %}
{% block content %}
{% set alert_days = weather|selectattr('alert')|list %}
{% if alert_days %}
<div class="alert alert-warning mb-6">⚠️ <strong>Weather Alert Active:</strong> Severe weather expected on {{ alert_days|map(attribute='date')|join(', ') }}. {{ critical_reports|list|length }} critical/high reports may be impacted.</div>
{% endif %}
<div class="section-title">🌤️ 5-Day Weather Forecast</div>
<div class="weather-grid mb-6">
  {% for day in weather %}
  <div class="weather-card {% if day.alert %}alert-day{% endif %}">
    <div class="w-date">{{ day.date }}</div>
    <div class="w-icon">{{ day.icon }}</div>
    <div class="w-condition">{{ day.condition }}</div>
    <div class="w-temp"><span class="w-high">{{ day.high }}°C</span><span style="color:#cbd5e1">/</span><span class="w-low">{{ day.low }}°C</span></div>
    <div class="w-meta"><div>💧 Rain: {{ day.rain_chance }}%</div><div>💨 Wind: {{ day.wind }} km/h</div></div>
    {% if day.alert %}<div class="w-alert-tag">⚠️ ALERT</div>{% endif %}
  </div>
  {% endfor %}
</div>
<div class="grid-2 mb-6">
  <div class="card">
    <div class="card-header"><div class="card-title">📊 Risk Analysis</div></div>
    <div class="card-body">
      <div style="display:flex;flex-direction:column;gap:14px">
        {% for label,val,color in [('Flooding Risk',65,'#3b82f6'),('Road Damage',80,'#ef4444'),('Power Outage',45,'#f59e0b'),('Tree Falls',55,'#10b981'),('Drainage Issues',70,'#8b5cf6')] %}
        <div>
          <div style="display:flex;justify-content:space-between;margin-bottom:4px"><span class="text-sm fw-700">{{ label }}</span><span class="text-sm text-muted">{{ val }}%</span></div>
          <div class="progress-bar"><div class="progress-fill" style="width:{{ val }}%;background:{{ color }}"></div></div>
        </div>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="card">
    <div class="card-header"><div class="card-title">⚠️ Alert Summary</div></div>
    <div class="card-body">
      <div style="display:flex;flex-direction:column;gap:12px">
        <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#fff5f5;border-radius:8px;border:1px solid #fecaca"><div style="font-size:1.8rem">🔴</div><div><div style="font-weight:700;color:#dc2626">Critical Reports</div><div style="font-size:.85rem;color:#64748b">{{ critical_reports|selectattr('severity','equalto','Critical')|list|length }} at critical level</div></div></div>
        <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#fff7ed;border-radius:8px;border:1px solid #fed7aa"><div style="font-size:1.8rem">🟠</div><div><div style="font-weight:700;color:#ea580c">High Priority</div><div style="font-size:.85rem;color:#64748b">{{ critical_reports|selectattr('severity','equalto','High')|list|length }} at high level</div></div></div>
        <div style="display:flex;align-items:center;gap:12px;padding:12px;background:#eff6ff;border-radius:8px;border:1px solid #bfdbfe"><div style="font-size:1.8rem">📍</div><div><div style="font-weight:700;color:#1e40af">Total Affected</div><div style="font-size:.85rem;color:#64748b">{{ critical_reports|list|length }} reports need monitoring</div></div></div>
      </div>
    </div>
  </div>
</div>
<div class="section-title">🚨 Critical & High Severity Reports</div>
<div class="card">
  <div class="card-body" style="padding:0">
    {% if critical_reports %}
    <div class="table-wrap"><table>
      <thead><tr><th>Report ID</th><th>Citizen</th><th>Title</th><th>Category</th><th>Location</th><th>Severity</th><th>Status</th><th>Weather Risk</th></tr></thead>
      <tbody>
        {% for r in critical_reports %}
        <tr>
          <td><code style="font-size:.8rem;color:#1a56db">{{ r['report_id'] }}</code></td>
          <td class="text-sm">{{ r['full_name'] }}</td>
          <td><strong>{{ r['title'] }}</strong></td>
          <td><span style="background:#f1f5f9;padding:3px 8px;border-radius:99px;font-size:.78rem">{{ r['category'] }}</span></td>
          <td class="text-sm text-muted">{{ r['location_address'] or 'N/A' }}</td>
          <td>{% set sev=r['severity'] %}<span class="badge badge-{{ sev.lower() }}">{% if sev=='Critical' %}🔴{% else %}🟠{% endif %} {{ sev }}</span></td>
          <td>{% set st=r['status'] %}<span class="badge badge-{{ 'progress' if st=='In Progress' else st.lower() }}">{{ st }}</span></td>
          <td>{% if r['category'] in ['Roads','Drainage','Infrastructure'] %}<span class="badge" style="background:#fee2e2;color:#991b1b">🌧️ High Risk</span>{% elif r['category'] in ['Utilities','Street Lighting'] %}<span class="badge" style="background:#fef3c7;color:#92400e">⚡ Med Risk</span>{% else %}<span class="badge badge-low">✅ Low Risk</span>{% endif %}</td>
        </tr>
        {% endfor %}
      </tbody>
    </table></div>
    {% else %}<div style="text-align:center;padding:48px;color:#94a3b8"><div style="font-size:3rem;margin-bottom:12px">✅</div><div style="font-weight:600">No critical reports pending</div></div>{% endif %}
  </div>
</div>
{% endblock %}
"""

# ─── ADMIN MAP ────────────────────────────────────────────────────────────────
TEMPLATES["templates/admin/map_view.html"] = r"""{% extends "admin/base_admin.html" %}
{% block title %}Reports Map — CivicConnect{% endblock %}
{% block page_title %}Reports Map{% endblock %}
{% block page_sub %}All submitted reports visualized by severity{% endblock %}
{% block head %}
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
{% endblock %}
{% block content %}
<div style="display:grid;grid-template-columns:1fr 320px;gap:24px;align-items:start">
  <div>
    <div class="card">
      <div class="card-header">
        <div class="card-title">🗺️ Live Reports Map</div>
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button class="btn btn-sm btn-outline" onclick="filterMarkers('all')">All</button>
          <button class="btn btn-sm" style="background:#dc2626;color:#fff" onclick="filterMarkers('Critical')">🔴 Critical</button>
          <button class="btn btn-sm" style="background:#ea580c;color:#fff" onclick="filterMarkers('High')">🟠 High</button>
          <button class="btn btn-sm" style="background:#ca8a04;color:#fff" onclick="filterMarkers('Medium')">🟡 Medium</button>
          <button class="btn btn-sm" style="background:#16a34a;color:#fff" onclick="filterMarkers('Low')">🟢 Low</button>
        </div>
      </div>
      <div class="card-body" style="padding:0"><div id="reportMap"></div></div>
    </div>
    <div class="card mt-4">
      <div class="card-body" style="padding:14px 22px">
        <div class="map-legend">
          <span class="text-sm fw-700" style="color:#64748b">SEVERITY:</span>
          <div class="legend-item"><div class="legend-dot dot-critical"></div> Critical</div>
          <div class="legend-item"><div class="legend-dot dot-high"></div> High</div>
          <div class="legend-item"><div class="legend-dot dot-medium"></div> Medium</div>
          <div class="legend-item"><div class="legend-dot dot-low"></div> Low</div>
        </div>
        <p class="text-sm text-muted" style="margin-top:8px">Click any marker to view details. Use filters to focus on priority levels.</p>
      </div>
    </div>
  </div>
  <div>
    <div class="card" style="position:sticky;top:80px;max-height:calc(100vh - 120px);overflow-y:auto">
      <div class="card-header"><div class="card-title">📋 Reports List</div><span class="text-sm text-muted">{{ reports|length }} shown</span></div>
      {% for r in reports %}
      <div onclick="flyToReport({{ r['latitude'] }},{{ r['longitude'] }})" style="padding:12px 16px;border-bottom:1px solid #f1f5f9;cursor:pointer;transition:background .2s" onmouseover="this.style.background='#f8fafc'" onmouseout="this.style.background=''">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;gap:8px">
          <div style="flex:1">
            <div style="font-size:.75rem;color:#94a3b8;font-family:monospace">{{ r['report_id'] }}</div>
            <div style="font-weight:600;font-size:.88rem;margin:2px 0">{{ r['title'] }}</div>
            <div style="font-size:.78rem;color:#64748b">{{ r['category'] }}</div>
          </div>
          <div>{% set sev=r['severity'] %}<span class="badge badge-{{ sev.lower() }}" style="font-size:.72rem">{% if sev=='Critical' %}🔴{% elif sev=='High' %}🟠{% elif sev=='Medium' %}🟡{% else %}🟢{% endif %} {{ sev }}</span></div>
        </div>
      </div>
      {% else %}
      <div style="text-align:center;padding:32px;color:#94a3b8"><p class="text-sm">No geotagged reports yet</p></div>
      {% endfor %}
    </div>
  </div>
</div>
{% endblock %}
{% block scripts %}
<script>
const reports={{ reports_json|safe }};
const colors={Critical:'#dc2626',High:'#ea580c',Medium:'#ca8a04',Low:'#16a34a'};
let allMarkers=[],map;
window.addEventListener('load',function(){
  map=L.map('reportMap').setView([40.7128,-74.0060],11);
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© OpenStreetMap'}).addTo(map);
  reports.forEach(r=>{
    if(!r.latitude||!r.longitude)return;
    const color=colors[r.severity]||'#64748b';
    const icon=L.divIcon({html:`<div style="background:${color};width:18px;height:18px;border-radius:50%;border:3px solid rgba(255,255,255,.9);box-shadow:0 2px 10px rgba(0,0,0,.4)"></div>`,className:'',iconSize:[18,18],iconAnchor:[9,9]});
    const m=L.marker([r.latitude,r.longitude],{icon}).addTo(map).bindPopup(`<div style="min-width:200px;font-family:Inter,sans-serif"><div style="font-weight:800;font-size:.95rem;margin-bottom:6px">${r.title}</div><div style="font-size:.82rem;color:#64748b;margin-bottom:8px">${r.category}</div><div style="display:flex;gap:6px;flex-wrap:wrap"><span style="background:${color};color:#fff;padding:2px 10px;border-radius:99px;font-size:.75rem;font-weight:700">${r.severity}</span><span style="background:#f1f5f9;color:#475569;padding:2px 10px;border-radius:99px;font-size:.75rem">${r.status}</span></div>${r.location_address?`<div style="font-size:.8rem;color:#94a3b8;margin-top:6px">📍 ${r.location_address}</div>`:''}<div style="font-size:.78rem;color:#94a3b8;margin-top:6px;font-family:monospace">${r.report_id}</div></div>`,{maxWidth:280});
    m.severity=r.severity;allMarkers.push(m);
  });
});
function filterMarkers(sev){allMarkers.forEach(m=>{if(sev==='all'||m.severity===sev){if(!map.hasLayer(m))map.addLayer(m);}else{if(map.hasLayer(m))map.removeLayer(m);}});}
function flyToReport(lat,lng){map.flyTo([lat,lng],15,{animate:true,duration:1});allMarkers.forEach(m=>{if(Math.abs(m.getLatLng().lat-lat)<0.0001)m.openPopup();});}
</script>
{% endblock %}
"""

# ── Write all template files ───────────────────────────────────────────────────
written = 0
for path, content in TEMPLATES.items():
    full_path = os.path.join(BASE, path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(content.strip())
    print(f"📝 Written: {path}")
    written += 1

print(f"\n{'='*50}")
print(f"✅ Setup complete! {written} template files written.")
print(f"{'='*50}")
print("\nNow run:  python app.py")
print("Then open: http://127.0.0.1:5000")
