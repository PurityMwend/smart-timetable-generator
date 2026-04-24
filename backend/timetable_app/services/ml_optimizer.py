"""
ML Optimizer — learns from past TimetableEntry records to rank
(course, time_slot, room) scheduling candidates.

Uses a RandomForestClassifier trained on historical assignment quality.
Falls back gracefully to uniform scores when no training data exists.
"""

import hashlib
import logging

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Feature helpers
# ---------------------------------------------------------------------------

DAY_ORDER = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4, "SAT": 5}
ROOM_TYPE_ORDER = {"lecture": 0, "lab": 1, "seminar": 2, "studio": 3, "workshop": 4}


def _entry_features(day: str, start_hour: int, room_capacity: int,
                    room_type: str, course_credits: int, course_semester: int) -> list:
    """Convert scheduling attributes to a numeric feature vector."""
    return [
        DAY_ORDER.get(day, 0),
        start_hour,
        room_capacity,
        ROOM_TYPE_ORDER.get(room_type, 0),
        course_credits,
        course_semester,
    ]


# ---------------------------------------------------------------------------
# MLOptimizer
# ---------------------------------------------------------------------------

class MLOptimizer:
    """
    Learns from past TimetableEntry records and scores scheduling candidates.

    Usage:
        optimizer = MLOptimizer()
        optimizer.train()                            # load history from DB
        score = optimizer.score(day, start_time, room, course)   # float 0-1
    """

    def __init__(self):
        self._model = None
        self._trained = False

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self):
        """Train (or re-train) on all existing TimetableEntry rows in the DB."""
        try:
            from ..models import TimetableEntry  # local import to avoid circular deps
            entries = list(TimetableEntry.objects.select_related(
                "room", "course", "course__program"
            ).all()[:5000])   # cap at 5k to stay fast

            if len(entries) < 5:
                logger.info("MLOptimizer: insufficient history (%d entries), skipping train", len(entries))
                self._trained = False
                return

            X, y = [], []
            for entry in entries:
                try:
                    feats = _entry_features(
                        day=entry.day,
                        start_hour=entry.start_time.hour,
                        room_capacity=entry.room.capacity,
                        room_type=entry.room.room_type,
                        course_credits=entry.course.credits,
                        course_semester=entry.course.semester,
                    )
                    X.append(feats)
                    # Label: 1 (good assignment) for all existing entries.
                    # We also synthesise label-0 examples by adding jitter.
                    y.append(1)

                    # Negative synthetic sample: swap day to weekend slot
                    bad_feats = feats.copy()
                    bad_feats[0] = 5   # SAT — typically undesirable
                    bad_feats[1] = 18  # 6 PM
                    X.append(bad_feats)
                    y.append(0)
                except Exception:
                    continue

            if len(X) < 2:
                self._trained = False
                return

            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline

            pipe = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(n_estimators=50, random_state=42, n_jobs=-1)),
            ])
            pipe.fit(np.array(X), np.array(y))
            self._model = pipe
            self._trained = True
            logger.info("MLOptimizer: trained on %d samples", len(X))

        except Exception as exc:
            logger.warning("MLOptimizer training failed: %s", exc)
            self._trained = False

    # ------------------------------------------------------------------
    # Scoring
    # ------------------------------------------------------------------

    def score(self, day: str, start_time, room, course) -> float:
        """
        Return a quality score in [0, 1] for the given assignment.
        Higher = more preferred by the model.
        Falls back to 0.5 when not trained.
        """
        if not self._trained or self._model is None:
            return 0.5

        try:
            feats = _entry_features(
                day=day,
                start_hour=start_time.hour if hasattr(start_time, "hour") else int(str(start_time).split(":")[0]),
                room_capacity=room.capacity,
                room_type=room.room_type,
                course_credits=course.credits,
                course_semester=course.semester,
            )
            proba = self._model.predict_proba([feats])[0]
            # Index 1 = probability of class "1" (good assignment)
            return float(proba[1]) if len(proba) > 1 else 0.5
        except Exception as exc:
            logger.debug("MLOptimizer score error: %s", exc)
            return 0.5

    def score_batch(self, candidates: list) -> list:
        """
        Score a batch of (day, start_time, room, course) tuples.
        Returns list of float scores parallel to `candidates`.
        """
        return [self.score(day, st, room, course) for day, st, room, course in candidates]
