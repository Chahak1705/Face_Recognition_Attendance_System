import cv2
import pickle
import time
import numpy as np
from deepface import DeepFace
from database import init_db, mark_attendance, get_attendance_today

# ── Configuration ─────────────────────────────────────────────────────────────
ENCODINGS_FILE     = "encodings.pkl"
MODEL_NAME         = "Facenet"
DISTANCE_THRESHOLD = 0.65   # Higher = more lenient
FRAME_SKIP         = 15     # Run recognition every N frames
CONFIRM_FRAMES     = 2      # Consecutive matches needed to confirm identity
SUCCESS_HOLD_SEC   = 2      # Seconds to show success screen before closing
# ──────────────────────────────────────────────────────────────────────────────


def load_encodings(path: str) -> dict:
    """
    Load face encodings from disk.
    Expected format: {student_name: embedding_list}
    """
    try:
        with open(path, "rb") as f:
            data = pickle.load(f)

        if not isinstance(data, dict):
            print("[ERROR] encodings.pkl is corrupted. Run register_faces.py again.")
            return {}

        if "names" in data and "encodings" in data:
            print("[ERROR] Old encoding format detected. Delete encodings.pkl and re-run register_faces.py.")
            return {}

        return data

    except FileNotFoundError:
        print(f"[ERROR] '{path}' not found. Run register_faces.py first.")
        return {}


def recognize_face(frame: np.ndarray, encodings: dict) -> tuple[str, float]:
    """
    Compare live frame against all known encodings using cosine distance.
    Returns (name, confidence_percent) or ("Unknown", 0.0).
    """
    best_name     = "Unknown"
    best_distance = float("inf")

    try:
        result = DeepFace.represent(
            img_path          = frame,
            model_name        = MODEL_NAME,
            enforce_detection = False,
        )
        if not result:
            return "Unknown", 0.0

        live_embedding = np.array(result[0]["embedding"])

        for name, stored_embedding in encodings.items():
            stored_vec = np.array(stored_embedding)
            dot      = np.dot(live_embedding, stored_vec)
            norm     = np.linalg.norm(live_embedding) * np.linalg.norm(stored_vec) + 1e-6
            distance = 1 - dot / norm

            if distance < best_distance:
                best_distance = distance
                best_name     = name

    except Exception:
        return "Unknown", 0.0

    if best_distance > DISTANCE_THRESHOLD:
        return "Unknown", 0.0

    confidence = round((1 - best_distance) * 100, 1)
    return best_name, confidence


def draw_overlay(frame: np.ndarray, name: str, confidence: float, marked: bool) -> np.ndarray:
    """Draw status overlay on the webcam frame."""
    h, w = frame.shape[:2]

    if marked:
        cv2.rectangle(frame, (0, h - 60), (w, h), (34, 139, 34), -1)
        cv2.putText(frame, f"  Attendance Marked: {name}  — closing...",
                    (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    elif name != "Unknown":
        cv2.rectangle(frame, (0, h - 60), (w, h), (180, 100, 0), -1)
        cv2.putText(frame, f"  Recognized: {name}  ({confidence}%)",
                    (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 2)
    else:
        cv2.rectangle(frame, (0, h - 60), (w, h), (40, 40, 40), -1)
        cv2.putText(frame, "  No match — look directly at the camera",
                    (10, h - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (180, 180, 180), 2)

    cv2.putText(frame, "Attendance System  |  Press Q to quit",
                (10, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (220, 220, 220), 1)

    return frame


def print_todays_log() -> None:
    records = get_attendance_today()
    print("\n" + "─" * 45)
    print("  Today's Attendance Log")
    print("─" * 45)
    if records:
        for i, record in enumerate(records, 1):
            print(f"  {i}. {record['name']:<20} {record['time']}")
    else:
        print("  No attendance recorded today.")
    print("─" * 45 + "\n")


def main():
    init_db()

    encodings = load_encodings(ENCODINGS_FILE)
    if not encodings:
        return

    print(f"[Attendance] Loaded {len(encodings)} student(s): {', '.join(encodings.keys())}")
    print("[Attendance] System started. Press Q to quit.\n")

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Could not open webcam.")
        return

    frame_count       = 0
    last_name         = "Unknown"
    last_confidence   = 0.0
    consecutive_hits  = 0
    attendance_marked = False
    success_time      = None

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[ERROR] Failed to read from webcam.")
            break

        frame_count += 1

        if frame_count % FRAME_SKIP == 0 and not attendance_marked:
            name, confidence = recognize_face(frame, encodings)

            if name != "Unknown":
                if name == last_name:
                    consecutive_hits += 1
                else:
                    consecutive_hits = 1
                last_name       = name
                last_confidence = confidence
            else:
                consecutive_hits = 0
                last_name        = "Unknown"
                last_confidence  = 0.0

            if consecutive_hits >= CONFIRM_FRAMES and not attendance_marked:
                mark_attendance(last_name)
                print(f"[Attendance] Marked: {last_name} ({last_confidence}%)")
                attendance_marked = True
                success_time      = time.time()

        display = draw_overlay(frame.copy(), last_name, last_confidence, attendance_marked)
        cv2.imshow("Attendance System", display)

        if attendance_marked and (time.time() - success_time) >= SUCCESS_HOLD_SEC:
            print("[Attendance] Done — closing.")
            break

        if cv2.waitKey(1) & 0xFF == ord("q"):
            print("[Attendance] Quit by user.")
            break

    cap.release()
    cv2.destroyAllWindows()
    print_todays_log()


if __name__ == "__main__":
    main()