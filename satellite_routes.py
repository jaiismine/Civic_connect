"""
satellite_routes.py — Flask routes for satellite dashboard
==========================================================
Registers as a Blueprint — imported by app.py
"""

from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for, flash
from satellite_engine import (
    run_satellite_scan, get_satellite_stats,
    ensure_satellite_tables, get_db
)
import json

sat_bp = Blueprint('satellite', __name__)

# ── Admin only decorator ──────────────────────────────────────
def admin_required_sat(f):
    from functools import wraps
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session or session.get('role') != 'admin':
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


# ─────────────────────────────────────────────────────────────
# SATELLITE DASHBOARD PAGE
# ─────────────────────────────────────────────────────────────
@sat_bp.route('/admin/satellite')
@admin_required_sat
def satellite_dashboard():
    ensure_satellite_tables()
    db    = get_db()
    stats = get_satellite_stats()

    scans = db.execute("""
        SELECT * FROM satellite_scans
        ORDER BY scan_date DESC LIMIT 20
    """).fetchall()

    sat_reports = db.execute("""
        SELECT r.*, u.full_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE r.source = 'satellite'
        ORDER BY r.created_at DESC
        LIMIT 20
    """).fetchall()

    confirmed = db.execute("""
        SELECT r.*, u.full_name
        FROM reports r
        JOIN users u ON r.user_id = u.id
        WHERE r.satellite_confirmed = 1
        ORDER BY r.updated_at DESC
        LIMIT 20
    """).fetchall()

    issues = db.execute("""
        SELECT si.*, ss.area_name, ss.scan_date
        FROM satellite_issues si
        JOIN satellite_scans ss ON si.scan_id = ss.id
        ORDER BY si.created_at DESC
        LIMIT 50
    """).fetchall()

    # Map data — all reports with coordinates
    map_reports = db.execute("""
        SELECT id, report_id, title, category, severity, status,
               latitude, longitude, source, satellite_confirmed
        FROM reports
        WHERE latitude IS NOT NULL AND longitude IS NOT NULL
    """).fetchall()

    db.close()

    return render_template(
        'admin/satellite.html',
        stats       = stats,
        scans       = scans,
        sat_reports = sat_reports,
        confirmed   = confirmed,
        issues      = [dict(i) for i in issues],
        map_reports = [dict(r) for r in map_reports],
        map_json    = json.dumps([dict(r) for r in map_reports])
    )


# ─────────────────────────────────────────────────────────────
# TRIGGER MANUAL SCAN
# ─────────────────────────────────────────────────────────────
@sat_bp.route('/admin/satellite/scan', methods=['POST'])
@admin_required_sat
def trigger_scan():
    area_name = request.form.get('area_name', 'City Center')
    latitude  = float(request.form.get('latitude',  40.7128))
    longitude = float(request.form.get('longitude', -74.0060))
    radius    = float(request.form.get('radius',    5.0))

    results = run_satellite_scan(area_name, latitude, longitude, radius)

    if 'error' in results:
        flash(f'❌ Scan failed: {results["error"]}', 'error')
    else:
        flash(
            f'✅ Satellite scan complete for {area_name}! '
            f'Detected: {results["total_detected"]} issues | '
            f'New reports: {results["new_reports"]} | '
            f'Citizen reports confirmed: {results["confirmed"]}',
            'success'
        )

    return redirect(url_for('satellite.satellite_dashboard'))


# ─────────────────────────────────────────────────────────────
# API — Get scan results as JSON
# ─────────────────────────────────────────────────────────────
@sat_bp.route('/api/satellite/stats')
@admin_required_sat
def satellite_stats_api():
    stats = get_satellite_stats()
    return jsonify(stats)


@sat_bp.route('/api/satellite/scan/<int:scan_id>')
@admin_required_sat
def scan_detail_api(scan_id):
    db     = get_db()
    scan   = db.execute("SELECT * FROM satellite_scans WHERE id=?", (scan_id,)).fetchone()
    issues = db.execute("""
        SELECT si.*, r.report_id, r.title as report_title
        FROM satellite_issues si
        LEFT JOIN reports r ON si.matched_report_id = r.id
        WHERE si.scan_id = ?
    """, (scan_id,)).fetchall()
    db.close()

    if not scan:
        return jsonify({'error': 'Scan not found'}), 404

    return jsonify({
        'scan'  : dict(scan),
        'issues': [dict(i) for i in issues]
    })
