"""
ai_routes.py — Flask routes for all 3 AI features
===================================================
This file is imported by app.py automatically after running patch_ai.py
"""

from flask import Blueprint, request, jsonify, session, render_template
from ai_features import classify_report, analyze_sentiment_batch, chat_with_support
import sqlite3

ai_bp = Blueprint('ai', __name__)

def get_db():
    import sqlite3
    db = sqlite3.connect('civic_connect.db')
    db.row_factory = sqlite3.Row
    return db


# ─────────────────────────────────────────────────────────────────────
# ROUTE 1 — AI CLASSIFY REPORT
# Called by report_issue.html via JavaScript fetch
# POST /ai/classify  {title, description}
# ─────────────────────────────────────────────────────────────────────
@ai_bp.route('/ai/classify', methods=['POST'])
def ai_classify():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data        = request.get_json()
    title       = data.get('title', '').strip()
    description = data.get('description', '').strip()

    if not title or not description:
        return jsonify({'error': 'Title and description required'}), 400

    result = classify_report(title, description)
    return jsonify(result)


# ─────────────────────────────────────────────────────────────────────
# ROUTE 2 — AI SENTIMENT DASHBOARD
# Called by admin dashboard page
# GET /ai/sentiment
# ─────────────────────────────────────────────────────────────────────
@ai_bp.route('/ai/sentiment')
def ai_sentiment():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    db      = get_db()
    reports = db.execute(
        "SELECT id, title, description, status, severity FROM reports WHERE status != 'Resolved' ORDER BY created_at DESC LIMIT 20"
    ).fetchall()
    db.close()

    reports_list = [dict(r) for r in reports]
    sentiment    = analyze_sentiment_batch(reports_list)
    return jsonify(sentiment)


# ─────────────────────────────────────────────────────────────────────
# ROUTE 3 — AI CHATBOT
# Called by support.html via JavaScript fetch
# POST /ai/chat  {message, history}
# ─────────────────────────────────────────────────────────────────────
@ai_bp.route('/ai/chat', methods=['POST'])
def ai_chat():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data        = request.get_json()
    user_message = data.get('message', '').strip()
    history      = data.get('history', [])

    if not user_message:
        return jsonify({'error': 'Message required'}), 400

    # Fetch citizen's reports for context
    db      = get_db()
    reports = db.execute(
        'SELECT report_id, title, category, severity, status, created_at FROM reports WHERE user_id=? ORDER BY created_at DESC',
        (session['user_id'],)
    ).fetchall()
    db.close()

    reports_list  = [dict(r) for r in reports]
    citizen_name  = session.get('full_name', 'Citizen')
    reply         = chat_with_support(user_message, history, reports_list, citizen_name)

    return jsonify({'reply': reply})
