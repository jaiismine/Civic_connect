from flask import Blueprint, request, jsonify, session
from ai_features import classify_report, analyze_sentiment, chat_with_ai
import sqlite3

ai_bp = Blueprint('ai', __name__)

def get_db():
    db = sqlite3.connect('civic_connect.db')
    db.row_factory = sqlite3.Row
    return db

# ── Route 1: AI Classifier ─────────────────────────────────────
@ai_bp.route('/ai/classify', methods=['POST'])
def ai_classify():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data = request.get_json()
    title       = data.get('title', '').strip()
    description = data.get('description', '').strip()
    if not title or not description:
        return jsonify({'error': 'Title and description required'}), 400
    result = classify_report(title, description)
    result['success'] = 'error' not in result
    return jsonify(result)

# ── Route 2: AI Sentiment ──────────────────────────────────────
@ai_bp.route('/ai/sentiment')
def ai_sentiment():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401
    db = get_db()
    reports = db.execute(
        "SELECT id, title, description, status, severity FROM reports WHERE status != 'Resolved' ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    db.close()
    reports_list = [dict(r) for r in reports]
    result = analyze_sentiment(reports_list)
    return jsonify(result)

# ── Route 3: AI Chatbot ────────────────────────────────────────
@ai_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    data         = request.get_json()
    user_message = data.get('message', '').strip()
    history      = data.get('history', [])
    if not user_message:
        return jsonify({'error': 'Message required'}), 400
    db = get_db()
    reports = db.execute(
        'SELECT report_id, title, severity, status FROM reports WHERE user_id=? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    db.close()
    user_context = {
        'name'   : session.get('full_name', 'Citizen'),
        'reports': [dict(r) for r in reports]
    }
    result = chat_with_ai(user_message, history, user_context)
    return jsonify({'reply': result.get('reply', ''), 'quick_replies': result.get('quick_replies', [])})
