"""
image_hash_util.py — Image Duplicate Detection for CivicConnect
===============================================================
Extracted and adapted from image_hash.py for integration with app.py
Uses perceptual hashing (pHash) to detect duplicate/similar images.

Install required packages:
    pip install Pillow imagehash geopy
"""

from PIL import Image
import imagehash
import sqlite3
import os


# ─────────────────────────────────────────────────────────────
# CORE FUNCTION — Generate hash from image file
# ─────────────────────────────────────────────────────────────
def get_image_hash(image_path: str) -> str:
    """
    Generate a perceptual hash string from an image file.
    pHash is robust — similar images get similar hashes.
    Returns hash string like: 'f8e4c2a1b3d5e7f0'
    """
    img = Image.open(image_path)
    return str(imagehash.phash(img))


# ─────────────────────────────────────────────────────────────
# CHECK DUPLICATE — Compare hash against existing reports
# ─────────────────────────────────────────────────────────────
def check_duplicate(image_hash: str, db_path: str = "civic_connect.db") -> dict:
    """
    Check if an image hash already exists in the reports table.

    Returns:
        {
          "is_duplicate" : True/False,
          "existing_id"  : report DB id (or None),
          "report_id"    : human-readable report id (or None),
          "title"        : title of original report (or None),
          "report_count" : how many times this image was submitted
        }
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Ensure image_hash column exists
    try:
        cursor.execute("ALTER TABLE reports ADD COLUMN image_hash TEXT")
        conn.commit()
    except Exception:
        pass  # Column already exists

    cursor.execute(
        "SELECT id, report_id, title FROM reports WHERE image_hash = ?",
        (image_hash,)
    )
    existing = cursor.fetchone()
    conn.close()

    if existing:
        return {
            "is_duplicate": True,
            "existing_id" : existing["id"],
            "report_id"   : existing["report_id"],
            "title"       : existing["title"],
        }
    return {
        "is_duplicate": False,
        "existing_id" : None,
        "report_id"   : None,
        "title"       : None,
    }


# ─────────────────────────────────────────────────────────────
# SAVE HASH — Store hash after a new report is created
# ─────────────────────────────────────────────────────────────
def save_image_hash(report_db_id: int, image_hash: str, db_path: str = "civic_connect.db"):
    """
    Save the image hash to the reports table after a new report is created.
    Call this right after inserting a new report row.
    """
    conn = sqlite3.connect(db_path)
    conn.execute(
        "UPDATE reports SET image_hash = ? WHERE id = ?",
        (image_hash, report_db_id)
    )
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────────────────────
# FULL PIPELINE — Used directly in app.py report_issue route
# ─────────────────────────────────────────────────────────────
def process_uploaded_image(image_file, upload_folder: str, db_path: str = "civic_connect.db") -> dict:
    """
    Full pipeline:
      1. Save image to upload folder
      2. Generate pHash
      3. Check if duplicate exists
      4. Return result dict

    Returns:
        {
          "saved_path"   : relative path like 'uploads/abc.jpg',
          "image_hash"   : hash string,
          "is_duplicate" : True/False,
          "report_id"    : original report id if duplicate (or None),
          "title"        : original report title if duplicate (or None),
        }
    """
    import uuid
    from werkzeug.utils import secure_filename

    # Save file
    filename  = secure_filename(f"{uuid.uuid4().hex}_{image_file.filename}")
    save_path = os.path.join(upload_folder, filename)
    os.makedirs(upload_folder, exist_ok=True)
    image_file.save(save_path)

    # Generate hash
    img_hash = get_image_hash(save_path)

    # Check duplicate
    dup = check_duplicate(img_hash, db_path)

    return {
        "saved_path"  : f"uploads/{filename}",
        "image_hash"  : img_hash,
        "is_duplicate": dup["is_duplicate"],
        "report_id"   : dup["report_id"],
        "title"       : dup["title"],
    }
