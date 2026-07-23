"""Custom ADK Function Tools for Exercise Planner Agent."""

from typing import Any, Dict, List, Optional
from google3.experimental.users.slichtor.exercise_planner_agent import firestore_service


def save_user_profile(
    goals: List[str],
    fitness_level: str = "beginner",
    schedule_days: int = 3,
    equipment: str = "full_gym",
    unavailable_days: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Saves customized user profile preferences to Cloud Firestore."""
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  return firestore_service.db_service.save_user_profile(
      user_id=user_id,
      goals=goals,
      fitness_level=fitness_level,
      schedule_days=schedule_days,
      equipment=equipment,
      unavailable_days=unavailable_days,
  )


def get_user_profile(
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
  """Retrieves saved user profile preferences from Cloud Firestore."""
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  return firestore_service.db_service.get_user_profile(user_id=user_id)


def search_exercise_catalog(
    query: str = "",
    difficulty: Optional[str] = None,
    muscle_group: Optional[str] = None,
    primary_goal: Optional[str] = None,
    equipment: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Searches exercise catalog by difficulty, muscle group, goal, or equipment."""
  del context  # Unused parameter required by ADK interface contract
  results = firestore_service.db_service.search_exercise_catalog(
      query=query,
      difficulty=difficulty,
      muscle_group=muscle_group,
      primary_goal=primary_goal,
      equipment=equipment,
  )
  if not results:
    return {
        "status": "NO_MATCHING_EXERCISES",
        "message": (
            "No exercises found matching your filter criteria. Try relaxing the"
            " difficulty or muscle_group parameters, or perform a broader"
            " catalog search."
        ),
        "suggested_actions": [
            "Omit specific equipment filters",
            "Try query='' with difficulty='beginner'",
        ],
        "results": [],
    }
  return {"status": "SUCCESS", "count": len(results), "results": results}


def save_workout_plan(
    plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  """Saves a generated workout plan for the user in Cloud Firestore."""
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  return firestore_service.db_service.save_workout_plan(
      user_id=user_id, plan=plan
  )


def get_latest_workout_plan(
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
  """Retrieves the user's latest workout plan from Cloud Firestore."""
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  return firestore_service.db_service.get_latest_workout_plan(user_id=user_id)


def log_completed_exercise(
    exercise_name: str,
    sets: int,
    reps: int,
    weight: float = 0.0,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Logs a completed exercise for the user in Cloud Firestore."""
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  return firestore_service.db_service.log_completed_exercise(
      user_id=user_id,
      exercise_name=exercise_name,
      sets=sets,
      reps=reps,
      weight=weight,
  )


def get_user_workout_history(
    time_window: str = "7_days", context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
  """Fetches logged workout history for the user from Cloud Firestore."""
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  return firestore_service.db_service.get_user_workout_history(
      user_id=user_id, time_window=time_window
  )
