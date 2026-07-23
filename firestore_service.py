"""Cloud Firestore Persistence Service for Exercise Planner & Tracker Agent."""

import datetime
import json
import logging
import os
import sqlite3
from typing import Any, Dict, List, Optional

DB_DIR = os.getenv("TEST_TMPDIR", os.getenv("TMPDIR", "./state"))
try:
  os.makedirs(DB_DIR, exist_ok=True)
except PermissionError:
  DB_DIR = "/tmp/state"
  os.makedirs(DB_DIR, exist_ok=True)

DB_FILE = os.path.join(DB_DIR, "workout_state.sqlite")


class FirestoreService:
  """Persistence Service backing user profiles, workout plans, and logs with SQLite."""

  def __init__(self):
    self._user_profiles: Dict[str, Dict[str, Any]] = {}
    self._workout_plans: Dict[str, List[Dict[str, Any]]] = {}
    self._workout_logs: Dict[str, List[Dict[str, Any]]] = {}

    # Initialize SQLite Persistent Storage
    os.makedirs(DB_DIR, exist_ok=True)
    self._conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    self._init_sqlite_tables()

  def _init_sqlite_tables(self):
    """Creates persistent SQLite database tables if missing."""
    with self._conn:
      self._conn.execute(
          "CREATE TABLE IF NOT EXISTS user_profiles (user_id TEXT PRIMARY"
          " KEY, profile_json TEXT)"
      )
      self._conn.execute(
          "CREATE TABLE IF NOT EXISTS workout_plans (plan_id TEXT PRIMARY KEY,"
          " user_id TEXT, plan_json TEXT, created_at TEXT)"
      )
      self._conn.execute(
          "CREATE TABLE IF NOT EXISTS workout_logs (log_id TEXT PRIMARY KEY,"
          " user_id TEXT, exercise_name TEXT, sets INTEGER, reps INTEGER,"
          " weight REAL, timestamp TEXT)"
      )
    self._catalog: List[Dict[str, Any]] = [
        # --- CHEST & PUSH ---
        {
            "name": "Barbell Bench Press",
            "muscle_group": "chest",
            "equipment": "barbell",
            "difficulty": "intermediate",
            "primary_goal": "strength",
            "instructions": (
                "Flat bench barbell press targeting pectoralis major."
            ),
        },
        {
            "name": "Incline Dumbbell Press",
            "muscle_group": "chest",
            "equipment": "dumbbell",
            "difficulty": "intermediate",
            "primary_goal": "muscle_gain",
            "instructions": (
                "Incline bench dumbbell press targeting upper chest."
            ),
        },
        {
            "name": "Pushups",
            "muscle_group": "chest",
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "primary_goal": "endurance",
            "instructions": (
                "Bodyweight push targeting chest, front delts, and core."
            ),
        },
        {
            "name": "Chest Dips",
            "muscle_group": "chest",
            "equipment": "bodyweight",
            "difficulty": "intermediate",
            "primary_goal": "muscle_gain",
            "instructions": "Bodyweight movement for lower chest and triceps.",
        },
        # --- BACK & PULL ---
        {
            "name": "Barbell Bent Over Rows",
            "muscle_group": "back",
            "equipment": "barbell",
            "difficulty": "intermediate",
            "primary_goal": "strength",
            "instructions": (
                "Heavy rowing movement targeting mid-back thickness and lats."
            ),
        },
        {
            "name": "Dumbbell Single-Arm Rows",
            "muscle_group": "back",
            "equipment": "dumbbell",
            "difficulty": "beginner",
            "primary_goal": "muscle_gain",
            "instructions": (
                "Unilateral row for lat isolation and shoulder stability."
            ),
        },
        {
            "name": "Pull-ups / Chin-ups",
            "muscle_group": "back",
            "equipment": "bodyweight",
            "difficulty": "intermediate",
            "primary_goal": "muscle_gain",
            "instructions": (
                "Vertical pulling bodyweight exercise for lat width."
            ),
        },
        {
            "name": "Bodyweight Inverted Rows",
            "muscle_group": "back",
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "primary_goal": "endurance",
            "instructions": "Horizontal pulling exercise using body weight.",
        },
        # --- LEGS & LOWER BODY ---
        {
            "name": "Barbell Back Squats",
            "muscle_group": "legs",
            "equipment": "barbell",
            "difficulty": "intermediate",
            "primary_goal": "strength",
            "instructions": (
                "King of lower body compound lifts targeting quads and glutes."
            ),
        },
        {
            "name": "Dumbbell Goblet Squats",
            "muscle_group": "legs",
            "equipment": "dumbbell",
            "difficulty": "beginner",
            "primary_goal": "muscle_gain",
            "instructions": (
                "Front-loaded squat with dumbbell targeting quad depth."
            ),
        },
        {
            "name": "Bodyweight Squats",
            "muscle_group": "legs",
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "primary_goal": "weight_loss",
            "instructions": "High volume bodyweight squats for conditioning.",
        },
        {
            "name": "Barbell / Dumbbell Romanian Deadlifts",
            "muscle_group": "legs",
            "equipment": "dumbbell",
            "difficulty": "intermediate",
            "primary_goal": "muscle_gain",
            "instructions": (
                "Hip hinge targeting hamstrings and gluteus maximus."
            ),
        },
        {
            "name": "Walking Dumbbell Lunges",
            "muscle_group": "legs",
            "equipment": "dumbbell",
            "difficulty": "beginner",
            "primary_goal": "weight_loss",
            "instructions": (
                "Dynamic single-leg movement for quad and glute strength."
            ),
        },
        {
            "name": "Jumping Bodyweight Lunges",
            "muscle_group": "legs",
            "equipment": "bodyweight",
            "difficulty": "intermediate",
            "primary_goal": "weight_loss",
            "instructions": (
                "Plyometric leg exercise for high heart rate and fat loss."
            ),
        },
        # --- SHOULDERS & ARMS ---
        {
            "name": "Overhead Barbell Press",
            "muscle_group": "shoulders",
            "equipment": "barbell",
            "difficulty": "intermediate",
            "primary_goal": "strength",
            "instructions": (
                "Standing vertical press targeting all three deltoid heads."
            ),
        },
        {
            "name": "Dumbbell Shoulder Press",
            "muscle_group": "shoulders",
            "equipment": "dumbbell",
            "difficulty": "beginner",
            "primary_goal": "muscle_gain",
            "instructions": "Seated overhead press for shoulder hypertrophy.",
        },
        {
            "name": "Dumbbell Lateral Raises",
            "muscle_group": "shoulders",
            "equipment": "dumbbell",
            "difficulty": "beginner",
            "primary_goal": "muscle_gain",
            "instructions": "Lateral deltoid isolation for shoulder width.",
        },
        {
            "name": "Pike Pushups",
            "muscle_group": "shoulders",
            "equipment": "bodyweight",
            "difficulty": "intermediate",
            "primary_goal": "endurance",
            "instructions": (
                "Bodyweight shoulder press targeting front/side delts."
            ),
        },
        {
            "name": "Dumbbell Bicep Curls",
            "muscle_group": "arms",
            "equipment": "dumbbell",
            "difficulty": "beginner",
            "primary_goal": "muscle_gain",
            "instructions": "Bicep isolation curl.",
        },
        {
            "name": "Tricep Overhead Extensions",
            "muscle_group": "arms",
            "equipment": "dumbbell",
            "difficulty": "beginner",
            "primary_goal": "muscle_gain",
            "instructions": "Tricep isolation targeting long head.",
        },
        # --- CARDIO & CORE ---
        {
            "name": "Zone 2 Treadmill Running / Outdoor Jogging",
            "muscle_group": "cardio",
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "primary_goal": "endurance",
            "instructions": "Steady-state aerobic cardio for aerobic capacity.",
        },
        {
            "name": "Stationary Cycling / Exercise Bike Intervals",
            "muscle_group": "cardio",
            "equipment": "full_gym",
            "difficulty": "beginner",
            "primary_goal": "endurance",
            "instructions": (
                "Low impact cardiovascular training for aerobic stamina."
            ),
        },
        {
            "name": "Jump Rope HIIT Circuit",
            "muscle_group": "cardio",
            "equipment": "bodyweight",
            "difficulty": "intermediate",
            "primary_goal": "weight_loss",
            "instructions": (
                "High intensity interval jump rope for heart rate elevation."
            ),
        },
        {
            "name": "Rowing Ergometer Intervals",
            "muscle_group": "cardio",
            "equipment": "full_gym",
            "difficulty": "intermediate",
            "primary_goal": "endurance",
            "instructions": "Full body aerobic endurance rowing.",
        },
        {
            "name": "Burpees",
            "muscle_group": "full_body",
            "equipment": "bodyweight",
            "difficulty": "intermediate",
            "primary_goal": "weight_loss",
            "instructions": (
                "Explosive full body exercise for caloric expenditure."
            ),
        },
        {
            "name": "Mountain Climbers",
            "muscle_group": "core",
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "primary_goal": "weight_loss",
            "instructions": "Fast tempo core and cardio exercise.",
        },
        {
            "name": "Plank Hold",
            "muscle_group": "core",
            "equipment": "bodyweight",
            "difficulty": "beginner",
            "primary_goal": "endurance",
            "instructions": "Isometric core stabilization exercise.",
        },
    ]

  # --- User Profile Operations ---
  def save_user_profile(
      self,
      user_id: str,
      goals: List[str],
      fitness_level: str = "beginner",
      schedule_days: int = 3,
      equipment: str = "full_gym",
      unavailable_days: Optional[List[str]] = None,
  ) -> Dict[str, Any]:
    """Saves customized user profile preferences to SQLite."""
    profile = {
        "user_id": user_id,
        "goals": goals,
        "fitness_level": fitness_level,
        "schedule_days": schedule_days,
        "equipment": equipment,
        "unavailable_days": unavailable_days or [],
        "updated_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    self._user_profiles[user_id] = profile

    with self._conn:
      self._conn.execute(
          "INSERT OR REPLACE INTO user_profiles (user_id, profile_json) VALUES"
          " (?, ?)",
          (user_id, json.dumps(profile)),
      )
    logger.info("Persisted profile for user '%s' to SQLite database.", user_id)
    return {"status": "success", "profile": profile}

  def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves saved user profile preferences from SQLite or memory cache."""
    if user_id in self._user_profiles:
      return self._user_profiles[user_id]

    cursor = self._conn.cursor()
    cursor.execute(
        "SELECT profile_json FROM user_profiles WHERE user_id = ?", (user_id,)
    )
    row = cursor.fetchone()
    if row:
      profile = json.loads(row[0])
      self._user_profiles[user_id] = profile
      return profile
    return None

  # --- Exercise Catalog Operations ---
  def search_exercise_catalog(
      self,
      query: str = "",
      difficulty: Optional[str] = None,
      muscle_group: Optional[str] = None,
      primary_goal: Optional[str] = None,
      equipment: Optional[str] = None,
  ) -> List[Dict[str, Any]]:
    """Searches exercise catalog filtered by muscle, goal, and required equipment."""
    results = []
    for item in self._catalog:
      if (
          query
          and query.lower() not in item["name"].lower()
          and query.lower() not in item["instructions"].lower()
      ):
        continue
      if difficulty and item["difficulty"].lower() != difficulty.lower():
        continue
      if muscle_group and item["muscle_group"].lower() != muscle_group.lower():
        continue
      if primary_goal and item["primary_goal"].lower() != primary_goal.lower():
        continue
      if (
          equipment
          and equipment.lower() != "full_gym"
          and item["equipment"].lower() != equipment.lower()
          and item["equipment"].lower() != "bodyweight"
      ):
        continue
      results.append(item)
    return results

  # --- Workout Plan Operations ---
  def save_workout_plan(
      self, user_id: str, plan: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Saves a workout plan for a user to SQLite."""
    p_id = f"plan_{user_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    created_at = datetime.datetime.now(datetime.timezone.utc).isoformat()
    record = {
        "plan_id": p_id,
        "user_id": user_id,
        "plan": plan,
        "created_at": created_at,
    }
    if user_id not in self._workout_plans:
      self._workout_plans[user_id] = []
    self._workout_plans[user_id].append(record)

    with self._conn:
      self._conn.execute(
          "INSERT INTO workout_plans (plan_id, user_id, plan_json, created_at)"
          " VALUES (?, ?, ?, ?)",
          (p_id, user_id, json.dumps(plan), created_at),
      )
    logger.info("Persisted plan '%s' for user '%s' to SQLite.", p_id, user_id)
    return {"status": "success", "plan_id": p_id}

  def get_latest_workout_plan(self, user_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves the most recently saved workout plan for a user from SQLite."""
    if user_id in self._workout_plans and self._workout_plans[user_id]:
      return self._workout_plans[user_id][-1]

    cursor = self._conn.cursor()
    cursor.execute(
        "SELECT plan_id, plan_json, created_at FROM workout_plans WHERE user_id"
        " = ? ORDER BY created_at DESC LIMIT 1",
        (user_id,),
    )
    row = cursor.fetchone()
    if row:
      record = {
          "plan_id": row[0],
          "user_id": user_id,
          "plan": json.loads(row[1]),
          "created_at": row[2],
      }
      return record
    return None

  # --- Workout Log & Progress Operations ---
  def log_completed_exercise(
      self,
      user_id: str,
      exercise_name: str,
      sets: int,
      reps: int,
      weight: float = 0.0,
      duration_minutes: int = 0,
      notes: str = "",
  ) -> Dict[str, Any]:
    """Logs a completed exercise session to SQLite."""
    log_id = f"log_{user_id}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    entry = {
        "log_id": log_id,
        "user_id": user_id,
        "exercise_name": exercise_name,
        "sets": sets,
        "reps": reps,
        "weight": weight,
        "duration_minutes": duration_minutes,
        "notes": notes,
        "timestamp": timestamp,
    }
    if user_id not in self._workout_logs:
      self._workout_logs[user_id] = []
    self._workout_logs[user_id].append(entry)

    with self._conn:
      self._conn.execute(
          "INSERT INTO workout_logs (log_id, user_id, exercise_name, sets,"
          " reps, weight, timestamp) VALUES (?, ?, ?, ?, ?, ?, ?)",
          (log_id, user_id, exercise_name, sets, reps, weight, timestamp),
      )
    logger.info(
        "Logged exercise '%s' (%dx%d) for user '%s' in SQLite.",
        exercise_name,
        sets,
        reps,
        user_id,
    )
    return {"status": "success", "entry": entry}

  def get_user_workout_history(
      self, user_id: str, limit: int = 20, time_window: Optional[str] = None
  ) -> List[Dict[str, Any]]:
    """Retrieves historical workout logs for progress tracking from SQLite."""
    del time_window
    if user_id in self._workout_logs and self._workout_logs[user_id]:
      return self._workout_logs[user_id][-limit:]

    cursor = self._conn.cursor()
    cursor.execute(
        "SELECT log_id, exercise_name, sets, reps, weight, timestamp FROM"
        " workout_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
        (user_id, limit),
    )
    rows = cursor.fetchall()
    logs = []
    for row in rows:
      logs.append({
          "log_id": row[0],
          "user_id": user_id,
          "exercise_name": row[1],
          "sets": row[2],
          "reps": row[3],
          "weight": row[4],
          "timestamp": row[5],
      })
    return logs

  # --- Async Memory Operations (Non-blocking DB Layer) ---
  async def async_get_user_profile(
      self, user_id: str
  ) -> Optional[Dict[str, Any]]:
    """Async wrapper for non-blocking profile retrieval."""
    return self.get_user_profile(user_id)

  async def async_save_workout_plan(
      self, user_id: str, plan: Dict[str, Any]
  ) -> Dict[str, Any]:
    """Async wrapper for non-blocking workout plan persistence."""
    return self.save_workout_plan(user_id, plan)

  async def async_log_completed_exercise(
      self,
      user_id: str,
      exercise_name: str,
      sets: int,
      reps: int,
      weight: float = 0.0,
  ) -> Dict[str, Any]:
    """Async wrapper for non-blocking workout logging."""
    return self.log_completed_exercise(
        user_id=user_id,
        exercise_name=exercise_name,
        sets=sets,
        reps=reps,
        weight=weight,
    )


# Global singleton instance for local runtime
db_service = FirestoreService()
