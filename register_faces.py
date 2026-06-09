"""
register_faces.py
Register known faces for the attendance system.

Usage:
  1. Place student photos inside known_faces/ folder.
     Single photo:    known_faces/Chahak.jpg
     Multiple photos: known_faces/Chahak_1.jpg, Chahak_2.jpg, Chahak_3.jpg ...
     All photos with the same base name are averaged into one strong encoding.

  2. Run: python register_faces.py
     - New students are added automatically.
     - Existing students are RE-encoded if new photos are detected.
     - No need to delete encodings.pkl ever.
"""

import os
import re
import pickle
import numpy as np
from deepface import DeepFace
from database import init_db, add_student

# ── Configuration ─────────────────────────────────────────────────────────────
KNOWN_FACES_DIR = "known_faces"
ENCODINGS_FILE  = "encodings.pkl"
SUPPORTED_EXTS  = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MODEL_NAME      = "Facenet"
# ──────────────────────────────────────────────────────────────────────────────


def load_existing_encodings() -> dict:
    """Load saved encodings. Returns {name: embedding_array}."""
    if os.path.exists(ENCODINGS_FILE):
        with open(ENCODINGS_FILE, "rb") as f:
            data = pickle.load(f)

        # Convert legacy format if needed
        if isinstance(data, dict) and "names" in data and "encodings" in data:
            print("[Register] Converting legacy format...")
            return dict(zip(data["names"], data["encodings"]))

        if isinstance(data, dict):
            print(f"[Register] {len(data)} existing encoding(s) loaded.")
            return data

    return {}


def save_encodings(encodings: dict):
    with open(ENCODINGS_FILE, "wb") as f:
        pickle.dump(encodings, f)
    print(f"[Register] {len(encodings)} encoding(s) saved to '{ENCODINGS_FILE}'.")


def get_base_name(filename: str) -> str:
    """
    Extract student name from filename, stripping trailing _1, _2, _3 etc.
    Examples:
        Chahak.jpg     -> Chahak
        Chahak_1.jpg   -> Chahak
        Chahak_2.png   -> Chahak
        Rahul_front.jpg -> Rahul_front   (only strips _<number>)
    """
    stem = os.path.splitext(filename)[0]
    return re.sub(r'_\d+$', '', stem)


def get_embedding(image_path: str):
    """Extract 128-d face embedding. Returns None if no face detected."""
    try:
        result = DeepFace.represent(
            img_path          = image_path,
            model_name        = MODEL_NAME,
            enforce_detection = True,
        )
        return np.array(result[0]["embedding"])
    except Exception as e:
        print(f"    [FAIL] Could not detect face: {e}")
        return None


def group_photos_by_student(image_files: list) -> dict:
    """Group filenames by student base name."""
    groups = {}
    for filename in sorted(image_files):
        name = get_base_name(filename)
        groups.setdefault(name, []).append(filename)
    return groups


def register_all():
    init_db()

    if not os.path.isdir(KNOWN_FACES_DIR):
        print(f"[Register] ERROR: '{KNOWN_FACES_DIR}' folder not found.")
        return

    # Load current photo list and build a fingerprint per student
    image_files = [
        f for f in os.listdir(KNOWN_FACES_DIR)
        if os.path.splitext(f)[1].lower() in SUPPORTED_EXTS
    ]

    if not image_files:
        print(f"[Register] No photos found in '{KNOWN_FACES_DIR}'.")
        return

    groups   = group_photos_by_student(image_files)
    encodings = load_existing_encodings()

    # Track photo counts already baked into each encoding
    counts_file = ENCODINGS_FILE + ".counts"
    if os.path.exists(counts_file):
        with open(counts_file, "rb") as f:
            saved_counts = pickle.load(f)
    else:
        saved_counts = {}

    print(f"\n[Register] Found {len(groups)} student(s) across {len(image_files)} photo(s).\n")

    updated = 0

    for name, files in groups.items():
        current_count = len(files)
        saved_count   = saved_counts.get(name, 0)

        if name in encodings and current_count == saved_count:
            print(f"  [SKIP]  '{name}' — no new photos detected ({current_count} photo(s)).")
            continue

        print(f"  [....] Processing '{name}' ({current_count} photo(s))...")

        embeddings = []
        for filename in files:
            filepath  = os.path.join(KNOWN_FACES_DIR, filename)
            embedding = get_embedding(filepath)
            if embedding is not None:
                embeddings.append(embedding)
                print(f"    [OK]  {filename}")
            else:
                print(f"    [SKIP] {filename} — no face detected.")

        if not embeddings:
            print(f"  [WARN]  No valid faces found for '{name}'. Skipping.")
            continue

        # Average all embeddings into one strong encoding
        avg_embedding      = np.mean(embeddings, axis=0)
        encodings[name]    = avg_embedding
        saved_counts[name] = current_count

        add_student(name)
        print(f"  [ OK ]  '{name}' registered with {len(embeddings)} photo(s) averaged.")
        updated += 1

    print(f"\n[Register] Done. {updated} student(s) updated.")
    save_encodings(encodings)

    # Save photo counts so we know when to re-encode
    with open(counts_file, "wb") as f:
        pickle.dump(saved_counts, f)

    print("\n── Registered Students ──────────────────────────────")
    for i, name in enumerate(sorted(encodings.keys()), 1):
        count = saved_counts.get(name, 1)
        print(f"   {i:2d}. {name}  ({count} photo(s))")
    print("─────────────────────────────────────────────────────\n")


if __name__ == "__main__":
    register_all()