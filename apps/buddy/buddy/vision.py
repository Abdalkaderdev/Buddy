"""Vision module for face detection and recognition."""

import cv2
import numpy as np
import sqlite3
from pathlib import Path
from .config import DATA_DIR, FACES_DB, FACE_RECOGNITION_THRESHOLD

# Try to import face_recognition (optional, requires dlib)
try:
    import face_recognition
    FACE_RECOGNITION_AVAILABLE = True
except ImportError:
    FACE_RECOGNITION_AVAILABLE = False
    print("Note: face_recognition not available. Using OpenCV face detection only.")


class FaceDatabase:
    """SQLite database for storing known faces."""

    def __init__(self, db_path: Path = FACES_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initialize database tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS faces (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                encoding BLOB NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                interaction_count INTEGER DEFAULT 1
            )
        """)
        conn.commit()
        conn.close()

    def add_face(self, name: str, encoding: np.ndarray):
        """Add a new face to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO faces (name, encoding) VALUES (?, ?)",
            (name, encoding.tobytes())
        )
        conn.commit()
        conn.close()

    def get_all_faces(self) -> list[tuple[int, str, np.ndarray]]:
        """Get all faces from database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, encoding FROM faces")
        rows = cursor.fetchall()
        conn.close()

        faces = []
        for row in rows:
            face_id, name, encoding_bytes = row
            encoding = np.frombuffer(encoding_bytes, dtype=np.float64)
            faces.append((face_id, name, encoding))
        return faces

    def update_last_seen(self, face_id: int):
        """Update last seen timestamp and increment interaction count."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE faces
            SET last_seen = CURRENT_TIMESTAMP,
                interaction_count = interaction_count + 1
            WHERE id = ?
        """, (face_id,))
        conn.commit()
        conn.close()

    def get_person_info(self, name: str) -> dict | None:
        """Get info about a person."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name, interaction_count, last_seen FROM faces WHERE name = ?",
            (name,)
        )
        row = cursor.fetchone()
        conn.close()

        if row:
            return {
                "name": row[0],
                "interactions": row[1],
                "last_seen": row[2]
            }
        return None


class FaceDetector:
    """Detects and recognizes faces."""

    def __init__(self):
        self.db = FaceDatabase()
        self.known_faces = self._load_known_faces()

        # OpenCV face detector (fallback)
        self.cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

    def _load_known_faces(self) -> dict[str, list[np.ndarray]]:
        """Load known faces from database."""
        faces = {}
        for face_id, name, encoding in self.db.get_all_faces():
            if name not in faces:
                faces[name] = []
            faces[name].append((face_id, encoding))
        return faces

    def detect_faces(self, frame: np.ndarray) -> list[dict]:
        """
        Detect faces in a frame.

        Returns:
            List of dicts with keys: bbox, name (or "unknown"), confidence
        """
        results = []

        if FACE_RECOGNITION_AVAILABLE:
            # Use face_recognition library
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            locations = face_recognition.face_locations(rgb_frame)
            encodings = face_recognition.face_encodings(rgb_frame, locations)

            for (top, right, bottom, left), encoding in zip(locations, encodings):
                name, confidence, face_id = self._match_face(encoding)

                if face_id:
                    self.db.update_last_seen(face_id)

                results.append({
                    "bbox": (left, top, right - left, bottom - top),
                    "name": name,
                    "confidence": confidence,
                    "encoding": encoding
                })
        else:
            # Fallback to OpenCV cascade
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.cascade.detectMultiScale(
                gray, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30)
            )

            for (x, y, w, h) in faces:
                results.append({
                    "bbox": (x, y, w, h),
                    "name": "unknown",  # Can't recognize without face_recognition
                    "confidence": 0.0,
                    "encoding": None
                })

        return results

    def _match_face(self, encoding: np.ndarray) -> tuple[str, float, int | None]:
        """
        Match an encoding against known faces.

        Returns:
            Tuple of (name, confidence, face_id) or ("unknown", 0.0, None)
        """
        if not FACE_RECOGNITION_AVAILABLE or not self.known_faces:
            return "unknown", 0.0, None

        best_match = "unknown"
        best_confidence = 0.0
        best_face_id = None

        for name, face_data in self.known_faces.items():
            for face_id, known_encoding in face_data:
                # Calculate distance (lower = more similar)
                distance = face_recognition.face_distance([known_encoding], encoding)[0]
                confidence = 1.0 - distance

                if confidence > best_confidence and confidence > FACE_RECOGNITION_THRESHOLD:
                    best_match = name
                    best_confidence = confidence
                    best_face_id = face_id

        return best_match, best_confidence, best_face_id

    def enroll_face(self, frame: np.ndarray, name: str) -> bool:
        """
        Enroll a new face in the database.

        Returns:
            True if successful, False if no face detected or face_recognition unavailable
        """
        if not FACE_RECOGNITION_AVAILABLE:
            print("Cannot enroll faces without face_recognition library")
            return False

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        locations = face_recognition.face_locations(rgb_frame)

        if not locations:
            return False

        encodings = face_recognition.face_encodings(rgb_frame, locations)
        if not encodings:
            return False

        # Use first face found
        encoding = encodings[0]
        self.db.add_face(name, encoding)

        # Reload known faces
        self.known_faces = self._load_known_faces()
        return True

    def get_face_center(self, bbox: tuple, frame_shape: tuple[int, int]) -> tuple[float, float]:
        """
        Get normalized center of face bbox.

        Args:
            bbox: (x, y, w, h) in pixels
            frame_shape: (height, width) of the source frame

        Returns:
            (x, y) where both are -1 to 1
        """
        x, y, w, h = bbox
        frame_h, frame_w = frame_shape[:2]
        center_x = (x + w / 2) / frame_w * 2 - 1
        center_y = (y + h / 2) / frame_h * 2 - 1
        return center_x, center_y


# Singleton instance
_detector: FaceDetector | None = None


def get_detector() -> FaceDetector:
    """Get the face detector instance."""
    global _detector
    if _detector is None:
        _detector = FaceDetector()
    return _detector
