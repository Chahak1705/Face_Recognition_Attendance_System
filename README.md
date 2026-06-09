# Face Recognition Attendance System

![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat&logo=python)
![OpenCV](https://img.shields.io/badge/OpenCV-4.x-green?style=flat&logo=opencv)
![DeepFace](https://img.shields.io/badge/DeepFace-Facenet-orange?style=flat)
![SQLite](https://img.shields.io/badge/Database-SQLite-lightgrey?style=flat&logo=sqlite)

> Automatic attendance system using real time face recognition via webcam.

---

## Features

-  **Real-time face detection** via webcam
- **AI powered recognition** using DeepFace (Facenet model)
-  **Auto attendance marking** : no duplicate entries per day
-  **Easy student registration** : just add a photo
-  **SQLite database** : lightweight, no setup needed

---

## Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.12 | Core language |
| OpenCV | Webcam capture & display |
| DeepFace | Face recognition (Facenet) |
| SQLite | Attendance storage |

---

## Project Structure

```
face_attendance/
├── database.py          # SQLite setup & helper functions
├── register_faces.py    # Register new students via photo
├── attendance.py        # Main script : webcam + auto marking
├── view_attendance.py   # View & export attendance reports
└── known_faces/         # Student photos (gitignored)
```

---

##  Getting Started

### 1. Install dependencies
```bash
pip install deepface opencv-python tf-keras
```

### 2. Register a student
Add photo to `known_faces/StudentName.jpg`, then:
```bash
python register_faces.py
```

### 3. Mark attendance
```bash
python attendance.py
```
> The webcam opens, detects your face, marks attendance, and then closes automatically!!

### 4. View reports
```bash
python view_attendance.py           # today's report
python view_attendance.py --all     # all records
python view_attendance.py --export  # export to CSV
```

---

## How It Works

1. **Register** : Student photo is processed into a 128-d face encoding and saved
2. **Detect** : Webcam captures live frames and detects faces in real time
3. **Match** : DeepFace compares detected face against stored encodings
4. **Mark** : If matched, attendance is logged in SQLite with timestamp
5. **Report** : View or export daily attendance records anytime
