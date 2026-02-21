"""
satellite_engine.py — CivicConnect Satellite Intelligence Engine
================================================================
Core logic for:
  1. Fetching satellite imagery (Sentinel Hub / NASA fallback)
  2. AI-based issue detection using OpenCV
  3. Smart deduplication against citizen reports
  4. Auto report generation for unmatched issues

Install:
    pip install opencv-python numpy requests Pillow imagehash geopy APScheduler
"""

import os
import cv2
import json
import math
import uuid
import sqlite3
import requests
import numpy as np
from PIL import Image
from datetime import datetime, timedelta
from geopy.geocoders import Nominatim

# ─────────────────────────────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────────────────────────────
DB_PATH          = "civic_connect.db"
SATELLITE_FOLDER = "static/satellite"
UPLOAD_FOLDER    = "static/uploads"

# Sentinel Hub credentials (free at dataspace.copernicus.eu)
SENTINEL_CLIENT_ID     = "YOUR_SENTINEL_CLIENT_ID"
SENTINEL_CLIENT_SECRET = "YOUR_SENTINEL_CLIENT_SECRET"

# Deduplication thresholds
MAX_DISTANCE_METERS = 50    # reports within 50m = same location
MAX_AGE_DAYS        = 30    # citizen reports within 30 days count

# Category mapping — satellite detection → civic category
ISSUE_CATEGORY_MAP = {
    "pothole"        : "Roads",
    "flooding"       : "Drainage",
    "illegal_dump"   : "Sanitation",
    "damaged_road"   : "Roads",
    "waterlogging"   : "Drainage",
    "construction"   : "Infrastructure",
    "dark_area"      : "Street Lighting",
    "overgrown"      : "Parks & Recreation",
    "debris"         : "Sanitation",
}

ISSUE_SEVERITY_MAP = {
    "pothole"        : "High",
    "flooding"       : "Critical",
    "illegal_dump"   : "Medium",
    "damaged_road"   : "High",
    "waterlogging"   : "High",
    "construction"   : "Medium",
    "dark_area"      : "Medium",
    "overgrown"      : "Low",
    "debris"         : "Medium",
}

os.makedirs(SATELLITE_FOLDER, exist_ok=True)
os.makedirs(UPLOAD_FOLDER,    exist_ok=True)


# ─────────────────────────────────────────────────────────────────────
# DATABASE HELPERS
# ─────────────────────────────────────────────────────────────────────
def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def ensure_satellite_tables():
    """Create satellite tables if they don't exist."""
    db = get_db()
    db.executescript("""
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
            created_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (scan_id)           REFERENCES satellite_scans(id),
            FOREIGN KEY (matched_report_id) REFERENCES reports(id)
        );

        CREATE TABLE IF NOT EXISTS report_satellite_links (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id    INTEGER NOT NULL,
            scan_id      INTEGER NOT NULL,
            issue_id     INTEGER NOT NULL,
            link_type    TEXT DEFAULT 'confirmed',
            linked_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (report_id) REFERENCES reports(id),
            FOREIGN KEY (scan_id)   REFERENCES satellite_scans(id)
        );
    """)

    # Add satellite columns to existing reports table
    for col, coltype in [("source", "TEXT DEFAULT 'citizen'"),
                         ("satellite_confirmed", "INTEGER DEFAULT 0"),
                         ("satellite_scan_id", "INTEGER")]:
        try:
            db.execute(f"ALTER TABLE reports ADD COLUMN {col} {coltype}")
        except Exception:
            pass

    db.commit()
    db.close()


# ─────────────────────────────────────────────────────────────────────
# HAVERSINE — Calculate distance between two GPS points
# ─────────────────────────────────────────────────────────────────────
def haversine_distance(lat1, lon1, lat2, lon2) -> float:
    """Returns distance in meters between two GPS coordinates."""
    R = 6371000  # Earth radius in meters
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi       = math.radians(lat2 - lat1)
    dlambda    = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))


# ─────────────────────────────────────────────────────────────────────
# SATELLITE IMAGE FETCH
# ─────────────────────────────────────────────────────────────────────
def fetch_satellite_image(lat: float, lon: float, area_name: str) -> str:
    """
    Fetch satellite image for given coordinates.
    Tries Sentinel Hub first, falls back to NASA GIBS, then generates
    a realistic mock image for demo/offline use.
    Returns path to saved image.
    """
    filename  = f"sat_{area_name.replace(' ','_')}_{datetime.now().strftime('%Y%m')}.jpg"
    save_path = os.path.join(SATELLITE_FOLDER, filename)

    if os.path.exists(save_path):
        return save_path

    # Try Sentinel Hub
    try:
        if SENTINEL_CLIENT_ID != "YOUR_SENTINEL_CLIENT_ID":
            token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"
            token_res = requests.post(token_url, data={
                "grant_type"   : "client_credentials",
                "client_id"    : SENTINEL_CLIENT_ID,
                "client_secret": SENTINEL_CLIENT_SECRET,
            }, timeout=10)
            token = token_res.json().get("access_token")

            delta = 0.05
            bbox  = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
            wms_url = (
                f"https://sh.dataspace.copernicus.eu/ogc/wms/{SENTINEL_CLIENT_ID}"
                f"?SERVICE=WMS&REQUEST=GetMap&LAYERS=TRUE_COLOR"
                f"&BBOX={bbox}&WIDTH=800&HEIGHT=800&FORMAT=image/jpeg"
                f"&CRS=EPSG:4326"
            )
            img_res = requests.get(wms_url, headers={"Authorization": f"Bearer {token}"}, timeout=15)
            if img_res.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(img_res.content)
                return save_path
    except Exception as e:
        print(f"Sentinel Hub unavailable: {e}")

    # Try NASA GIBS (no auth needed)
    try:
        delta    = 0.05
        bbox_str = f"{lon-delta},{lat-delta},{lon+delta},{lat+delta}"
        nasa_url = (
            f"https://gibs.earthdata.nasa.gov/wms/epsg4326/best/wms.cgi"
            f"?SERVICE=WMS&REQUEST=GetMap"
            f"&LAYERS=MODIS_Terra_CorrectedReflectance_TrueColor"
            f"&BBOX={bbox_str}&WIDTH=800&HEIGHT=800"
            f"&FORMAT=image/jpeg&CRS=EPSG:4326"
            f"&TIME={datetime.now().strftime('%Y-%m-%d')}"
        )
        img_res = requests.get(nasa_url, timeout=15)
        if img_res.status_code == 200 and len(img_res.content) > 10000:
            with open(save_path, "wb") as f:
                f.write(img_res.content)
            return save_path
    except Exception as e:
        print(f"NASA GIBS unavailable: {e}")

    # Fallback — generate realistic mock satellite image
    return _generate_mock_satellite_image(save_path)


def _generate_mock_satellite_image(save_path: str) -> str:
    """Generate a realistic-looking mock satellite image for demo purposes."""
    import random
    img = np.zeros((800, 800, 3), dtype=np.uint8)

    # Base ground color (earthy green/brown)
    img[:] = (45, 90, 45)

    # Roads (grey lines)
    road_color = (80, 80, 80)
    for i in range(0, 800, 120):
        cv2.line(img, (0, i), (800, i), road_color, 18)
        cv2.line(img, (i, 0), (i, 800), road_color, 18)

    # Buildings (grey rectangles)
    bld_color = (100, 100, 100)
    random.seed(42)
    for _ in range(60):
        x, y = random.randint(10,750), random.randint(10,750)
        w, h = random.randint(20,60),  random.randint(20,60)
        cv2.rectangle(img, (x,y), (x+w, y+h), bld_color, -1)

    # Water patches (blue)
    cv2.ellipse(img, (200,600), (60,30), 0, 0, 360, (120,80,40), -1)

    # Issue patches — darker anomaly areas
    anomaly_positions = [
        (350, 300), (550, 450), (150, 200),
        (620, 150), (400, 600), (250, 500)
    ]
    for (ax, ay) in anomaly_positions:
        cv2.circle(img, (ax, ay), random.randint(15,30), (20,20,20), -1)
        # Add slight water-like tint to some
        if random.random() > 0.5:
            overlay = img.copy()
            cv2.circle(overlay, (ax, ay), random.randint(20,40), (60,40,20), -1)
            cv2.addWeighted(overlay, 0.4, img, 0.6, 0, img)

    # Add gaussian blur for realism
    img = cv2.GaussianBlur(img, (3,3), 0)

    cv2.imwrite(save_path, img)
    return save_path


# ─────────────────────────────────────────────────────────────────────
# ISSUE DETECTION — OpenCV based anomaly detection
# ─────────────────────────────────────────────────────────────────────
def detect_issues_in_image(image_path: str, base_lat: float, base_lon: float) -> list:
    """
    Detect potential civic issues in a satellite image using OpenCV.
    Returns list of detected issues with coordinates and type.
    """
    img = cv2.imread(image_path)
    if img is None:
        return []

    h, w   = img.shape[:2]
    issues = []

    # ── Detection 1: Dark patches (potholes / damage) ──────────
    gray       = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, dark    = cv2.threshold(gray, 40, 255, cv2.THRESH_BINARY_INV)
    kernel     = np.ones((5,5), np.uint8)
    dark_clean = cv2.morphologyEx(dark, cv2.MORPH_OPEN, kernel)
    contours, _ = cv2.findContours(dark_clean, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if 200 < area < 3000:
            x, y, bw, bh = cv2.boundingRect(cnt)
            cx, cy = x + bw//2, y + bh//2
            lat = base_lat + (0.5 - cy/h) * 0.1
            lon = base_lon + (cx/w - 0.5) * 0.1
            issues.append({
                "type"      : "pothole",
                "confidence": min(0.95, area / 1000),
                "latitude"  : round(lat, 6),
                "longitude" : round(lon, 6),
                "bbox"      : [x, y, bw, bh],
                "pixel_x"   : cx,
                "pixel_y"   : cy,
            })

    # ── Detection 2: Blue/dark patches (flooding / waterlogging) ──
    hsv       = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    blue_mask = cv2.inRange(hsv, (100,50,50), (130,255,255))
    blue_c, _ = cv2.findContours(blue_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    for cnt in blue_c:
        area = cv2.contourArea(cnt)
        if area > 500:
            x, y, bw, bh = cv2.boundingRect(cnt)
            cx, cy = x + bw//2, y + bh//2
            lat = base_lat + (0.5 - cy/h) * 0.1
            lon = base_lon + (cx/w - 0.5) * 0.1
            issues.append({
                "type"      : "flooding",
                "confidence": min(0.90, area / 2000),
                "latitude"  : round(lat, 6),
                "longitude" : round(lon, 6),
                "bbox"      : [x, y, bw, bh],
                "pixel_x"   : cx,
                "pixel_y"   : cy,
            })

    # ── Detection 3: Irregular clusters (illegal dumps / debris) ──
    edges     = cv2.Canny(gray, 50, 150)
    edge_c, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    irregular = []
    for cnt in edge_c:
        area = cv2.contourArea(cnt)
        peri = cv2.arcLength(cnt, True)
        if area > 300 and peri > 0:
            circularity = 4 * math.pi * area / (peri * peri)
            if circularity < 0.3:  # Very irregular shape
                irregular.append(cnt)

    if len(irregular) > 5:
        all_pts  = np.concatenate(irregular)
        x, y, bw, bh = cv2.boundingRect(all_pts)
        cx, cy = x + bw//2, y + bh//2
        lat = base_lat + (0.5 - cy/h) * 0.1
        lon = base_lon + (cx/w - 0.5) * 0.1
        issues.append({
            "type"      : "illegal_dump",
            "confidence": 0.72,
            "latitude"  : round(lat, 6),
            "longitude" : round(lon, 6),
            "bbox"      : [x, y, bw, bh],
            "pixel_x"   : cx,
            "pixel_y"   : cy,
        })

    return issues[:10]  # Limit to 10 issues per scan


def crop_issue_image(image_path: str, bbox: list, issue_id: str) -> str:
    """Crop satellite image around detected issue and save."""
    img = cv2.imread(image_path)
    if img is None:
        return ""
    x, y, w, h = bbox
    pad  = 40
    x1   = max(0, x - pad)
    y1   = max(0, y - pad)
    x2   = min(img.shape[1], x + w + pad)
    y2   = min(img.shape[0], y + h + pad)
    crop = img[y1:y2, x1:x2]

    crop_path = os.path.join(SATELLITE_FOLDER, f"issue_{issue_id}.jpg")
    cv2.imwrite(crop_path, crop)
    return crop_path


# ─────────────────────────────────────────────────────────────────────
# SMART DEDUPLICATION
# ─────────────────────────────────────────────────────────────────────
def find_matching_citizen_report(issue_lat: float, issue_lon: float,
                                  issue_type: str, db) -> dict:
    """
    Find if a citizen has already reported this issue.
    Matches on: location (within 50m) + category + time (within 30 days)
    """
    category    = ISSUE_CATEGORY_MAP.get(issue_type, "Other")
    cutoff_date = (datetime.now() - timedelta(days=MAX_AGE_DAYS)).strftime("%Y-%m-%d")

    # Get all recent unresolved reports in same category
    candidates = db.execute("""
        SELECT id, report_id, title, latitude, longitude, category, severity, status
        FROM reports
        WHERE category = ?
        AND status != 'Resolved'
        AND latitude IS NOT NULL
        AND longitude IS NOT NULL
        AND created_at >= ?
    """, (category, cutoff_date)).fetchall()

    best_match  = None
    best_distance = float('inf')

    for report in candidates:
        if report['latitude'] is None or report['longitude'] is None:
            continue
        dist = haversine_distance(
            issue_lat, issue_lon,
            report['latitude'], report['longitude']
        )
        if dist <= MAX_DISTANCE_METERS and dist < best_distance:
            best_distance = dist
            best_match    = dict(report)
            best_match['distance_meters'] = round(dist, 1)

    return best_match


# ─────────────────────────────────────────────────────────────────────
# AUTO REPORT CREATION
# ─────────────────────────────────────────────────────────────────────
def create_satellite_report(issue: dict, scan_id: int, db) -> str:
    """Auto-create a new report from satellite detection."""
    issue_type = issue['type']
    category   = ISSUE_CATEGORY_MAP.get(issue_type, "Other")
    severity   = ISSUE_SEVERITY_MAP.get(issue_type, "Medium")
    report_id  = f"SAT-{uuid.uuid4().hex[:6].upper()}"

    title_map = {
        "pothole"     : "Pothole Detected by Satellite Scan",
        "flooding"    : "Flooding Area Detected by Satellite",
        "illegal_dump": "Illegal Dump Site Detected by Satellite",
        "damaged_road": "Road Damage Detected by Satellite",
        "waterlogging": "Waterlogging Detected by Satellite",
        "dark_area"   : "Unlit Area Detected by Satellite",
        "debris"      : "Debris Accumulation Detected by Satellite",
        "overgrown"   : "Overgrown Vegetation Detected by Satellite",
    }
    desc_map = {
        "pothole"     : "Satellite imagery analysis detected a pothole or road surface damage at this location. Confidence level indicates significant surface anomaly requiring inspection.",
        "flooding"    : "Satellite imagery has detected abnormal water accumulation at this location, suggesting flooding or drainage failure. Immediate assessment recommended.",
        "illegal_dump": "Irregular material accumulation detected in satellite imagery suggesting an illegal dump site or debris accumulation requiring civic attention.",
        "damaged_road": "Satellite analysis indicates road surface irregularities consistent with significant damage. Ground verification and repair assessment needed.",
        "waterlogging": "Persistent water presence detected in satellite imagery indicating waterlogging or drainage blockage at this location.",
        "dark_area"   : "Analysis of nighttime satellite data indicates inadequate street lighting in this area, posing potential safety concerns.",
        "debris"      : "Satellite imagery shows significant debris accumulation requiring sanitation department attention.",
        "overgrown"   : "Overgrown vegetation detected in public space area requiring parks department attention.",
    }

    title       = title_map.get(issue_type, f"{issue_type.replace('_',' ').title()} Detected")
    description = desc_map.get(issue_type, "Issue detected via satellite imagery analysis.")

    # Use satellite crop image as report image if available
    image_path  = ""
    if issue.get('crop_path'):
        rel = os.path.relpath(issue['crop_path'], 'static')
        image_path = rel.replace("\\", "/")

    # Get address from coordinates
    address = ""
    try:
        geo = Nominatim(user_agent="civicconnect_satellite")
        loc = geo.reverse(f"{issue['latitude']}, {issue['longitude']}", timeout=5)
        if loc:
            address = loc.address[:200]
    except Exception:
        address = f"Lat: {issue['latitude']}, Lng: {issue['longitude']}"

    # Admin user id = 1
    db.execute("""
        INSERT INTO reports
        (report_id, user_id, title, category, description,
         location_address, latitude, longitude, image_path,
         status, severity, label, source, satellite_scan_id)
        VALUES (?,1,?,?,?,?,?,?,?,'Pending',?,'Satellite Detected','satellite',?)
    """, (report_id, title, category, description,
          address, issue['latitude'], issue['longitude'],
          image_path, severity, scan_id))
    db.commit()

    new_row = db.execute("SELECT id FROM reports WHERE report_id=?", (report_id,)).fetchone()
    return report_id, new_row['id'] if new_row else None


# ─────────────────────────────────────────────────────────────────────
# CONFIRM EXISTING CITIZEN REPORT WITH SATELLITE DATA
# ─────────────────────────────────────────────────────────────────────
def confirm_citizen_report(report: dict, issue: dict, scan_id: int, issue_db_id: int, db):
    """
    Mark an existing citizen report as satellite-confirmed.
    Upgrades severity if satellite detects worse condition.
    """
    severity_rank = {"Low": 1, "Medium": 2, "High": 3, "Critical": 4}
    sat_severity  = ISSUE_SEVERITY_MAP.get(issue['type'], "Medium")
    cur_severity  = report['severity']

    new_severity  = sat_severity if severity_rank.get(sat_severity, 0) > severity_rank.get(cur_severity, 0) else cur_severity

    db.execute("""
        UPDATE reports
        SET satellite_confirmed = 1,
            satellite_scan_id   = ?,
            severity            = ?,
            label               = 'Satellite Confirmed',
            updated_at          = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (scan_id, new_severity, report['id']))

    # Link satellite issue to citizen report
    db.execute("""
        INSERT INTO report_satellite_links (report_id, scan_id, issue_id, link_type)
        VALUES (?, ?, ?, 'confirmed')
    """, (report['id'], scan_id, issue_db_id))

    db.commit()


# ─────────────────────────────────────────────────────────────────────
# MAIN SCAN FUNCTION — Called monthly by scheduler
# ─────────────────────────────────────────────────────────────────────
def run_satellite_scan(area_name: str, latitude: float, longitude: float,
                       radius_km: float = 5.0) -> dict:
    """
    Full satellite scan pipeline for a given area.
    Returns summary of what was found and what actions were taken.
    """
    ensure_satellite_tables()
    db = get_db()
    if not(8<=latitude<=37 and 68<=longitude <=97.5):
        return{"error": "Coordinates are outside India. Use lat 8-37 and lon 68-97.5"}

    print(f"\n🛰️  Starting satellite scan: {area_name} ({latitude}, {longitude})")

    # Create scan record
    db.execute("""
        INSERT INTO satellite_scans (area_name, latitude, longitude, radius_km, status)
        VALUES (?, ?, ?, ?, 'processing')
    """, (area_name, latitude, longitude, radius_km))
    db.commit()
    scan_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

    results = {
        "scan_id"       : scan_id,
        "area"          : area_name,
        "total_detected": 0,
        "new_reports"   : 0,
        "confirmed"     : 0,
        "skipped"       : 0,
        "issues"        : []
    }

    try:
        # Step 1: Fetch satellite image
        print(f"  📡 Fetching satellite image...")
        image_path = fetch_satellite_image(latitude, longitude, area_name)

        # Step 2: Detect issues
        print(f"  🔍 Analyzing image for civic issues...")
        raw_issues = detect_issues_in_image(image_path, latitude, longitude)
        print(f"  📊 Detected {len(raw_issues)} potential issues")

        results["total_detected"] = len(raw_issues)

        # Step 3: Process each issue
        for i, issue in enumerate(raw_issues):
            if issue['confidence'] < 0.5:
                results["skipped"] += 1
                continue

            # Crop issue from satellite image
            crop_id   = f"{scan_id}_{i}"
            crop_path = crop_issue_image(image_path, issue['bbox'], crop_id)
            issue['crop_path'] = crop_path

            # Save satellite issue to DB
            db.execute("""
                INSERT INTO satellite_issues
                (scan_id, issue_type, confidence, latitude, longitude,
                 bbox_coords, image_crop_path, action_taken)
                VALUES (?,?,?,?,?,?,?,'pending')
            """, (scan_id, issue['type'], issue['confidence'],
                  issue['latitude'], issue['longitude'],
                  json.dumps(issue['bbox']), crop_path))
            db.commit()
            issue_db_id = db.execute("SELECT last_insert_rowid()").fetchone()[0]

            # Step 4: Check for duplicate citizen report
            match = find_matching_citizen_report(
                issue['latitude'], issue['longitude'], issue['type'], db
            )

            if match:
                # DUPLICATE — confirm existing citizen report
                print(f"  ✅ Issue at ({issue['latitude']}, {issue['longitude']}) matches citizen report {match['report_id']}")
                confirm_citizen_report(match, issue, scan_id, issue_db_id, db)

                db.execute("UPDATE satellite_issues SET matched_report_id=?, action_taken='confirmed' WHERE id=?",
                           (match['id'], issue_db_id))
                db.commit()

                results["confirmed"] += 1
                results["issues"].append({
                    "type"      : issue['type'],
                    "action"    : "confirmed",
                    "report_id" : match['report_id'],
                    "distance"  : match['distance_meters'],
                    "lat"       : issue['latitude'],
                    "lon"       : issue['longitude'],
                })
            else:
                # NEW ISSUE — create satellite report
                print(f"  🆕 New issue detected: {issue['type']} at ({issue['latitude']}, {issue['longitude']})")
                new_report_id, new_db_id = create_satellite_report(issue, scan_id, db)

                db.execute("UPDATE satellite_issues SET action_taken='new_report' WHERE id=?", (issue_db_id,))
                db.commit()

                results["new_reports"] += 1
                results["issues"].append({
                    "type"      : issue['type'],
                    "action"    : "new_report",
                    "report_id" : new_report_id,
                    "lat"       : issue['latitude'],
                    "lon"       : issue['longitude'],
                })

        # Update scan record
        db.execute("""
            UPDATE satellite_scans
            SET issues_found = ?, new_reports = ?, confirmed = ?,
                image_path = ?, status = 'completed'
            WHERE id = ?
        """, (len(raw_issues), results["new_reports"],
              results["confirmed"], image_path, scan_id))
        db.commit()

        print(f"\n  🛰️  Scan complete!")
        print(f"  📊 Total detected : {results['total_detected']}")
        print(f"  🆕 New reports    : {results['new_reports']}")
        print(f"  ✅ Confirmed      : {results['confirmed']}")

    except Exception as e:
        db.execute("UPDATE satellite_scans SET status='failed' WHERE id=?", (scan_id,))
        db.commit()
        results["error"] = str(e)
        print(f"  ❌ Scan failed: {e}")

    db.close()
    return results


# ─────────────────────────────────────────────────────────────────────
# MONTHLY SCHEDULER
# ─────────────────────────────────────────────────────────────────────
def start_monthly_scheduler(areas: list):
    """
    Start APScheduler to run satellite scans monthly.
    areas = [{"name":"Downtown","lat":40.71,"lon":-74.00}, ...]
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        scheduler = BackgroundScheduler()

        def run_all_scans():
            print(f"\n🛰️  Monthly satellite scan triggered: {datetime.now()}")
            for area in areas:
                run_satellite_scan(area["name"], area["lat"], area["lon"])

        # Run on 1st of every month at 2:00 AM
        scheduler.add_job(run_all_scans, 'cron', day=1, hour=2, minute=0)
        scheduler.start()
        print(f"✅ Satellite scheduler started — scans run monthly on day 1 at 02:00 AM")
        print(f"   Monitoring {len(areas)} area(s): {[a['name'] for a in areas]}")
        return scheduler
    except ImportError:
        print("APScheduler not installed. Run: pip install APScheduler")
        return None


# ─────────────────────────────────────────────────────────────────────
# STATS HELPER
# ─────────────────────────────────────────────────────────────────────
def get_satellite_stats() -> dict:
    """Get summary stats for admin dashboard."""
    ensure_satellite_tables()
    db = get_db()

    total_scans = db.execute("SELECT COUNT(*) FROM satellite_scans WHERE status='completed'").fetchone()[0]
    total_auto  = db.execute("SELECT COUNT(*) FROM reports WHERE source='satellite'").fetchone()[0]
    total_conf  = db.execute("SELECT COUNT(*) FROM reports WHERE satellite_confirmed=1").fetchone()[0]
    last_scan   = db.execute("SELECT scan_date, area_name FROM satellite_scans ORDER BY scan_date DESC LIMIT 1").fetchone()
    next_scan   = (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).strftime("%b %d, %Y")

    db.close()
    return {
        "total_scans": total_scans,
        "auto_reports": total_auto,
        "confirmed"  : total_conf,
        "last_scan"  : dict(last_scan) if last_scan else None,
        "next_scan"  : next_scan,
    }
