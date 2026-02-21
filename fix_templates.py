"""
fix_templates.py
Run this: python fix_templates.py
Rewrites report_issue.html and support_ai.html with full AI features.
"""
import os

BASE      = os.path.dirname(os.path.abspath(__file__))
CIT_DIR   = os.path.join(BASE, "templates", "citizen")
os.makedirs(CIT_DIR, exist_ok=True)

# ─────────────────────────────────────────────────────────────
# 1. report_issue.html  — with AI Auto-Fill button
# ─────────────────────────────────────────────────────────────
REPORT_ISSUE = r"""{% extends "citizen/base_citizen.html" %}
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

      <!-- ── AI Result Banner ───────────────────────────────── -->
      <div id="aiBanner" style="display:none;background:linear-gradient(135deg,#1a56db,#0ea5e9);border-radius:12px;padding:18px 20px;margin-bottom:18px;color:#fff">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px">
          <span style="font-size:1.5rem">🤖</span>
          <span style="font-weight:700;font-size:1rem">AI Analysis Complete</span>
          <span id="aiConfidence" style="margin-left:auto;background:rgba(255,255,255,.2);padding:3px 12px;border-radius:99px;font-size:.78rem;font-weight:600"></span>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:12px">
          <div style="background:rgba(255,255,255,.15);border-radius:8px;padding:12px">
            <div style="font-size:.7rem;opacity:.75;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Detected Category</div>
            <div id="aiCategory" style="font-weight:700;font-size:1rem"></div>
          </div>
          <div style="background:rgba(255,255,255,.15);border-radius:8px;padding:12px">
            <div style="font-size:.7rem;opacity:.75;margin-bottom:4px;text-transform:uppercase;letter-spacing:.5px">Suggested Severity</div>
            <div id="aiSeverity" style="font-weight:700;font-size:1rem"></div>
          </div>
        </div>
        <div style="background:rgba(255,255,255,.12);border-radius:8px;padding:12px;font-size:.88rem;margin-bottom:12px">
          <span style="opacity:.75">💡 AI Reasoning: </span>
          <span id="aiReason" style="font-weight:500"></span>
        </div>
        <div style="display:flex;gap:8px">
          <button type="button" onclick="applyAISuggestions()"
            style="background:#fff;color:#1a56db;border:none;border-radius:8px;padding:9px 20px;font-weight:700;cursor:pointer;font-size:.88rem">
            ✅ Apply AI Suggestions
          </button>
          <button type="button" onclick="document.getElementById('aiBanner').style.display='none'"
            style="background:rgba(255,255,255,.15);color:#fff;border:none;border-radius:8px;padding:9px 18px;font-weight:600;cursor:pointer;font-size:.88rem">
            Dismiss
          </button>
        </div>
      </div>

      <!-- ── Issue Details Card ────────────────────────────── -->
      <div class="card mb-4">
        <div class="card-header">
          <div class="card-title">📋 Issue Details</div>
          <button type="button" id="aiClassifyBtn" onclick="runAIClassifier()"
            style="display:inline-flex;align-items:center;gap:6px;padding:8px 16px;background:linear-gradient(135deg,#1a56db,#0ea5e9);color:#fff;border:none;border-radius:8px;font-weight:700;cursor:pointer;font-size:.88rem">
            🤖 AI Auto-Fill
          </button>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>Issue Title *</label>
            <input type="text" name="title" id="titleInput" placeholder="Brief title of the issue" required>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
            <div class="form-group">
              <label>Category *</label>
              <select name="category" id="categoryInput" required>
                <option value="">Select Category</option>
                <option>Roads</option>
                <option>Infrastructure</option>
                <option>Sanitation</option>
                <option>Utilities</option>
                <option>Parks &amp; Recreation</option>
                <option>Public Safety</option>
                <option>Drainage</option>
                <option>Street Lighting</option>
                <option>Other</option>
              </select>
            </div>
            <div class="form-group">
              <label>Severity Level *</label>
              <select name="severity" id="severityInput" required>
                <option value="Low">🟢 Low</option>
                <option value="Medium" selected>🟡 Medium</option>
                <option value="High">🟠 High</option>
                <option value="Critical">🔴 Critical</option>
              </select>
            </div>
          </div>
          <div class="form-group">
            <label>Description *</label>
            <textarea name="description" id="descInput" required
              placeholder="Describe the issue in detail — the more you write, the better AI can classify it..."></textarea>
          </div>
          <!-- AI Loading indicator -->
          <div id="aiLoading" style="display:none;text-align:center;padding:16px;background:#eff6ff;border-radius:8px;border:1px solid #bfdbfe;margin-top:10px">
            <div style="font-size:1.6rem;margin-bottom:6px">🤖</div>
            <div style="font-size:.9rem;color:#1e40af;font-weight:600">AI is analyzing your report...</div>
            <div style="font-size:.78rem;color:#64748b;margin-top:4px">Detecting category, severity and priority</div>
          </div>
        </div>
      </div>

      <!-- ── Photo Upload ──────────────────────────────────── -->
      <div class="card mb-4">
        <div class="card-header"><div class="card-title">📸 Photo Evidence</div></div>
        <div class="card-body">
          <div class="image-drop-zone">
            <input type="file" name="image" id="imageFile" accept="image/*">
            <div class="drop-icon">📷</div>
            <div class="drop-text">Click or drag to upload photo</div>
            <div class="drop-sub">Supports JPG, PNG, WebP • Max 10MB</div>
          </div>
          <img id="imagePreview" src="" alt="Preview"
            style="max-width:100%;border-radius:8px;margin-top:12px;display:none">
        </div>
      </div>

      <button type="submit" class="btn btn-primary btn-full" style="padding:14px;font-size:1rem">
        🚀 Submit Report
      </button>
    </div>

    <!-- ── Right Column: Location ──────────────────────────── -->
    <div>
      <div class="card" style="position:sticky;top:80px">
        <div class="card-header">
          <div class="card-title">📍 Location</div>
          <button type="button" id="getLocationBtn" class="btn btn-accent btn-sm">📡 Auto-Detect</button>
        </div>
        <div class="card-body">
          <p class="text-sm text-muted mb-4">Click Auto-Detect or click on the map to drop a pin.</p>
          <div class="map-preview"><div id="previewMap"></div></div>
          <div class="form-group mt-4">
            <label>Address</label>
            <input type="text" name="address" id="addrInput" placeholder="Auto-filled or enter manually">
          </div>
          <input type="hidden" name="latitude"  id="latInput">
          <input type="hidden" name="longitude" id="lngInput">
          <div style="background:#fef3c7;border:1px solid #fde68a;border-radius:8px;padding:12px;margin-top:10px">
            <p style="font-size:.82rem;color:#92400e">💡 Enable location services in your browser for GPS accuracy.</p>
          </div>
        </div>
      </div>

      <!-- AI Tips -->
      <div class="card mt-4">
        <div class="card-header"><div class="card-title">💡 AI Tips</div></div>
        <div class="card-body">
          <ul style="list-style:none;display:flex;flex-direction:column;gap:10px">
            <li class="text-sm">🤖 Click <strong>AI Auto-Fill</strong> after entering title + description</li>
            <li class="text-sm">📝 More detail = more accurate classification</li>
            <li class="text-sm">✅ Review AI suggestion then click Apply</li>
            <li class="text-sm">📍 Always add location for faster response</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</form>
{% endblock %}

{% block scripts %}
<script>
let aiData = null;

async function runAIClassifier() {
  const title = document.getElementById('titleInput').value.trim();
  const desc  = document.getElementById('descInput').value.trim();
  if (!title || !desc) {
    alert('Please fill in the Title and Description first so AI can analyze your report.');
    return;
  }
  document.getElementById('aiLoading').style.display  = 'block';
  document.getElementById('aiBanner').style.display   = 'none';
  const btn = document.getElementById('aiClassifyBtn');
  btn.disabled   = true;
  btn.textContent = '🤖 Analyzing...';
  try {
    const res  = await fetch('/ai/classify', {
      method : 'POST',
      headers: {'Content-Type': 'application/json'},
      body   : JSON.stringify({ title, description: desc })
    });
    aiData = await res.json();
    if (aiData.success || aiData.category) {
      document.getElementById('aiCategory').textContent   = aiData.category   || '—';
      document.getElementById('aiSeverity').textContent   = aiData.severity   || '—';
      document.getElementById('aiReason').textContent     = aiData.reason     || aiData.summary || '—';
      document.getElementById('aiConfidence').textContent = aiData.urgent ? '🔴 Urgent' : '✅ Normal';
      document.getElementById('aiBanner').style.display   = 'block';
    } else {
      alert('AI error: ' + (aiData.error || 'Unknown error. Check your API key in config.py'));
    }
  } catch(e) {
    alert('Could not reach AI. Make sure app.py is running and config.py has your API key.');
  } finally {
    document.getElementById('aiLoading').style.display = 'none';
    btn.disabled    = false;
    btn.textContent = '🤖 AI Auto-Fill';
  }
}

function applyAISuggestions() {
  if (!aiData) return;
  // Apply category
  const cat = document.getElementById('categoryInput');
  for (let opt of cat.options) {
    if (opt.value === aiData.category) { cat.value = aiData.category; break; }
  }
  // Apply severity
  if (aiData.severity) document.getElementById('severityInput').value = aiData.severity;
  document.getElementById('aiBanner').style.display = 'none';
  // Show confirmation flash
  const flash = document.createElement('div');
  flash.className = 'alert alert-success';
  flash.style.marginBottom = '12px';
  flash.innerHTML = '✅ AI suggestions applied! Category and Severity have been auto-filled.';
  const cardBody = document.querySelector('.card-body');
  cardBody.insertBefore(flash, cardBody.firstChild);
  setTimeout(() => flash.remove(), 3500);
}
</script>
{% endblock %}
"""

# ─────────────────────────────────────────────────────────────
# 2. support_ai.html  — with AI Chatbot
# ─────────────────────────────────────────────────────────────
SUPPORT_AI = r"""{% extends "citizen/base_citizen.html" %}
{% block title %}Get Support — CivicConnect{% endblock %}
{% block page_title %}Get Support{% endblock %}
{% block page_sub %}Reach city officials or chat with our AI assistant{% endblock %}

{% block content %}
<!-- Support Options -->
<div class="section-title">🎯 Choose Support Type</div>
<div class="support-cards mb-6">
  <div class="support-option" onclick="selectSupport(this,'Start Consultation')">
    <div class="support-icon">🎯</div>
    <div class="support-title">Start Consultation</div>
    <div class="support-desc">Schedule a formal consultation with the relevant department.</div>
    <button class="btn btn-primary btn-sm" style="margin-top:16px" onclick="event.stopPropagation();selectSupport(this.closest('.support-option'),'Start Consultation')">Request Consultation</button>
  </div>
  <div class="support-option" onclick="selectSupport(this,'Active Chat')">
    <div class="support-icon">💬</div>
    <div class="support-title">Active Chat</div>
    <div class="support-desc">Start a real-time chat session with a city representative.</div>
    <button class="btn btn-accent btn-sm" style="margin-top:16px" onclick="event.stopPropagation();selectSupport(this.closest('.support-option'),'Active Chat')">Start Chat</button>
  </div>
  <div class="support-option" onclick="selectSupport(this,'Quick Connect')">
    <div class="support-icon">⚡</div>
    <div class="support-title">Quick Connect</div>
    <div class="support-desc">Fast response from priority departments for urgent matters.</div>
    <button class="btn btn-danger btn-sm" style="margin-top:16px" onclick="event.stopPropagation();selectSupport(this.closest('.support-option'),'Quick Connect')">Quick Connect</button>
  </div>
</div>

<!-- Human Support Form -->
<div id="supportForm" style="display:none">
  <div class="card mb-6">
    <div class="card-header">
      <div class="card-title">📝 Submit Request</div>
      <span id="selectedTypeLabel" class="badge badge-info"></span>
    </div>
    <div class="card-body">
      <form method="POST" action="{{ url_for('get_support') }}">
        <input type="hidden" name="type" id="supportType">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:18px">
          <div class="form-group"><label>Department *</label>
            <select name="department" required>
              <option value="">Select Department</option>
              <option>Roads &amp; Infrastructure</option>
              <option>Sanitation &amp; Environment</option>
              <option>Water &amp; Utilities</option>
              <option>Public Safety</option>
              <option>Parks &amp; Recreation</option>
              <option>Emergency Services</option>
              <option>City Planning</option>
              <option>General Enquiry</option>
            </select>
          </div>
          <div class="form-group"><label>Priority</label>
            <select name="priority"><option>Normal</option><option>High</option><option>Urgent</option></select>
          </div>
        </div>
        <div class="form-group">
          <label>Your Message *</label>
          <textarea name="message" placeholder="Describe your issue in detail..." required style="min-height:120px"></textarea>
        </div>
        <div style="display:flex;gap:12px">
          <button type="submit" class="btn btn-primary">📤 Submit Request</button>
          <button type="button" class="btn btn-outline" onclick="document.getElementById('supportForm').style.display='none'">Cancel</button>
        </div>
      </form>
    </div>
  </div>
</div>

<!-- ── AI CHATBOT SECTION ──────────────────────────────────── -->
<div class="section-title">🤖 CivicAssist AI — Instant Support</div>
<div class="card mb-6">
  <div class="card-header">
    <div style="display:flex;align-items:center;gap:12px">
      <div style="width:42px;height:42px;background:linear-gradient(135deg,#1a56db,#0ea5e9);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:1.2rem;flex-shrink:0">🤖</div>
      <div>
        <div style="font-weight:700;font-size:1rem">CivicAssist AI</div>
        <div style="font-size:.78rem;color:#16a34a;display:flex;align-items:center;gap:5px">
          <span style="width:7px;height:7px;background:#16a34a;border-radius:50%;display:inline-block"></span>
          Online — powered by Claude AI
        </div>
      </div>
    </div>
  </div>

  <!-- Chat Window -->
  <div id="chatMessages" style="height:400px;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;background:#f8fafc">
    <!-- Welcome bubble -->
    <div style="display:flex;gap:10px;align-items:flex-start">
      <div style="width:34px;height:34px;background:linear-gradient(135deg,#1a56db,#0ea5e9);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.95rem;flex-shrink:0">🤖</div>
      <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;border-bottom-left-radius:4px;padding:14px 18px;max-width:78%;font-size:.9rem;box-shadow:0 1px 4px rgba(0,0,0,.06);line-height:1.6">
        👋 Hi <strong>{{ session.full_name }}</strong>! I'm CivicAssist, your AI support agent.<br><br>
        I can help you with:
        <ul style="margin:8px 0 0 16px;font-size:.85rem;color:#64748b">
          <li>Status of your submitted reports</li>
          <li>How to escalate unresolved issues</li>
          <li>Finding the right department</li>
          <li>General civic guidance</li>
        </ul>
        <div style="margin-top:10px;font-size:.85rem;color:#94a3b8">What can I help you with today?</div>
      </div>
    </div>
  </div>

  <!-- Quick Reply Chips -->
  <div id="quickReplies" style="padding:12px 20px;display:flex;gap:8px;flex-wrap:wrap;border-top:1px solid #f1f5f9;background:#fff">
    <button class="react-btn" onclick="sendQuickReply(this,'What is the status of my reports?')">📋 My report status</button>
    <button class="react-btn" onclick="sendQuickReply(this,'How do I escalate an unresolved report?')">📢 How to escalate</button>
    <button class="react-btn" onclick="sendQuickReply(this,'Which department handles road issues?')">🛣️ Road issues</button>
    <button class="react-btn" onclick="sendQuickReply(this,'My report has been pending too long with no response')">⏳ No response yet</button>
  </div>

  <!-- Input Row -->
  <div style="padding:14px 20px;border-top:1px solid #e2e8f0;display:flex;gap:10px;background:#fff">
    <input type="text" id="chatInput" placeholder="Type your message and press Enter..."
      onkeydown="if(event.key==='Enter' && !event.shiftKey){event.preventDefault();sendChat();}"
      style="flex:1;padding:11px 18px;border:1.5px solid #e2e8f0;border-radius:99px;font-size:.9rem;outline:none;transition:border-color .2s"
      onfocus="this.style.borderColor='#1a56db'" onblur="this.style.borderColor='#e2e8f0'">
    <button onclick="sendChat()" id="sendBtn" class="btn btn-primary" style="border-radius:99px;padding:11px 22px">
      Send ➤
    </button>
  </div>
</div>

<!-- Previous Requests -->
<div class="section-title">📁 My Support Requests</div>
{% if consultations %}
<div class="card">
  <div class="card-body" style="padding:0">
    <div class="table-wrap">
      <table>
        <thead><tr><th>Type</th><th>Department</th><th>Message</th><th>Status</th><th>Reply</th><th>Date</th></tr></thead>
        <tbody>
          {% for c in consultations %}
          <tr>
            <td>{% if c['type']=='Start Consultation' %}🎯{% elif c['type']=='Active Chat' %}💬{% else %}⚡{% endif %} <strong>{{ c['type'] }}</strong></td>
            <td>{{ c['department'] or '—' }}</td>
            <td><span style="font-size:.85rem;color:#64748b;display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:200px">{{ c['message'] }}</span></td>
            <td><span class="badge badge-{{ 'progress' if c['status']=='Open' else 'resolved' }}">{{ '🔓 Open' if c['status']=='Open' else '✅ Closed' }}</span></td>
            <td class="text-sm">{{ c['admin_reply'] or 'Awaiting...' }}</td>
            <td class="text-muted text-sm">{{ c['created_at'][:10] }}</td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
    </div>
  </div>
</div>
{% else %}
<div class="card">
  <div class="card-body" style="text-align:center;padding:48px">
    <div style="font-size:3rem;margin-bottom:12px">📭</div>
    <h3>No support requests yet</h3>
    <p class="text-muted">Choose a support type above to get started.</p>
  </div>
</div>
{% endif %}

<!-- Emergency Contacts -->
<div class="card mt-6">
  <div class="card-header"><div class="card-title">📞 Emergency Contacts</div></div>
  <div class="card-body">
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px">
      <div style="padding:14px;background:#fff5f5;border:1px solid #fecaca;border-radius:10px;text-align:center"><div style="font-size:1.8rem">🚨</div><div style="font-weight:700;color:#dc2626">Emergency</div><div style="font-weight:800;color:#991b1b;font-size:1.2rem">911</div></div>
      <div style="padding:14px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;text-align:center"><div style="font-size:1.8rem">🏛️</div><div style="font-weight:700;color:#1e40af">City Hall</div><div style="color:#1e40af">(555) 100-2000</div></div>
      <div style="padding:14px;background:#f0fdf4;border:1px solid #bbf7d0;border-radius:10px;text-align:center"><div style="font-size:1.8rem">💧</div><div style="font-weight:700;color:#166534">Water Dept.</div><div style="color:#166534">(555) 100-3000</div></div>
      <div style="padding:14px;background:#fefce8;border:1px solid #fde68a;border-radius:10px;text-align:center"><div style="font-size:1.8rem">🔧</div><div style="font-weight:700;color:#92400e">Public Works</div><div style="color:#92400e">(555) 100-4000</div></div>
    </div>
  </div>
</div>
{% endblock %}

{% block scripts %}
<script>
let chatHistory = [];

function selectSupport(card, type) {
  document.querySelectorAll('.support-option').forEach(c => c.classList.remove('selected'));
  card.classList.add('selected');
  document.getElementById('supportType').value        = type;
  document.getElementById('selectedTypeLabel').textContent = type;
  const f = document.getElementById('supportForm');
  f.style.display = 'block';
  f.scrollIntoView({ behavior: 'smooth' });
}

function addBubble(role, text) {
  const wrap = document.getElementById('chatMessages');
  const isUser = role === 'user';
  const div = document.createElement('div');
  div.style.cssText = `display:flex;gap:10px;align-items:flex-start;${isUser ? 'flex-direction:row-reverse' : ''}`;

  const av = document.createElement('div');
  av.style.cssText = `width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.9rem;flex-shrink:0;font-weight:700;${isUser ? 'background:linear-gradient(135deg,#667eea,#764ba2);color:#fff' : 'background:linear-gradient(135deg,#1a56db,#0ea5e9)'}`;
  av.textContent = isUser ? '{{ (session.full_name or "U")[0].upper() }}' : '🤖';

  const bub = document.createElement('div');
  bub.style.cssText = `padding:12px 16px;border-radius:14px;max-width:76%;font-size:.9rem;line-height:1.6;${isUser ? 'background:#1a56db;color:#fff;border-bottom-right-radius:4px' : 'background:#fff;border:1px solid #e2e8f0;border-bottom-left-radius:4px;box-shadow:0 1px 4px rgba(0,0,0,.06)'}`;
  bub.textContent = text;

  div.appendChild(av);
  div.appendChild(bub);
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

function showTyping() {
  const wrap = document.getElementById('chatMessages');
  const div  = document.createElement('div');
  div.id = 'typing';
  div.style.cssText = 'display:flex;gap:10px;align-items:flex-start';
  div.innerHTML = `
    <div style="width:34px;height:34px;background:linear-gradient(135deg,#1a56db,#0ea5e9);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:.9rem;flex-shrink:0">🤖</div>
    <div style="background:#fff;border:1px solid #e2e8f0;border-radius:14px;border-bottom-left-radius:4px;padding:14px 18px;box-shadow:0 1px 4px rgba(0,0,0,.06)">
      <div style="display:flex;gap:5px;align-items:center">
        <div class="dot"></div><div class="dot" style="animation-delay:.2s"></div><div class="dot" style="animation-delay:.4s"></div>
      </div>
    </div>`;
  wrap.appendChild(div);
  wrap.scrollTop = wrap.scrollHeight;
}

async function sendChat() {
  const input = document.getElementById('chatInput');
  const msg   = input.value.trim();
  if (!msg) return;

  input.value = '';
  document.getElementById('sendBtn').disabled = true;
  document.getElementById('quickReplies').style.display = 'none';

  addBubble('user', msg);
  chatHistory.push({ role: 'user', content: msg });
  showTyping();

  try {
    const res  = await fetch('/ai/chat', {
      method : 'POST',
      headers: { 'Content-Type': 'application/json' },
      body   : JSON.stringify({ message: msg, history: chatHistory })
    });
    const data = await res.json();
    document.getElementById('typing')?.remove();

    const reply = data.reply || 'Sorry, I could not process that request.';
    addBubble('assistant', reply);
    chatHistory.push({ role: 'assistant', content: reply });

    // Show dynamic quick replies if provided
    if (data.quick_replies && data.quick_replies.length) {
      const qr = document.getElementById('quickReplies');
      qr.style.display = 'flex';
      qr.innerHTML = data.quick_replies.map(q =>
        `<button class="react-btn" onclick="sendQuickReply(this,'${q.replace(/'/g,"\\'")}'">${q}</button>`
      ).join('');
    }
  } catch(e) {
    document.getElementById('typing')?.remove();
    addBubble('assistant', 'I am having trouble connecting right now. Please check your API key in config.py and try again.');
  }

  document.getElementById('sendBtn').disabled = false;
  input.focus();
}

function sendQuickReply(btn, text) {
  document.getElementById('chatInput').value = text;
  sendChat();
}
</script>
<style>
.dot {
  width:8px;height:8px;background:#94a3b8;border-radius:50%;
  animation:bounce 1.2s infinite ease-in-out;
}
@keyframes bounce {
  0%,80%,100%{transform:translateY(0);opacity:.5}
  40%{transform:translateY(-7px);opacity:1}
}
</style>
{% endblock %}
"""

# ── Write files ───────────────────────────────────────────────
files = {
    os.path.join(CIT_DIR, "report_issue.html"): REPORT_ISSUE,
    os.path.join(CIT_DIR, "support_ai.html")  : SUPPORT_AI,
}

for path, content in files.items():
    with open(path, "w", encoding="utf-8") as f:
        f.write(content.strip())
    print(f"✅ Written: {os.path.basename(path)}")

print("""
══════════════════════════════════════════
  ✅  Templates fixed successfully!
══════════════════════════════════════════

Now run:
    python app.py

Then open:
    http://127.0.0.1:5000

  🤖 AI Auto-Fill → Report an Issue page
  💬 AI Chatbot   → Get Support page
""")
