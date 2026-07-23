"""Custom ADK Function Tools for Exercise Planner Agent.

Defines Pydantic input models, comprehensive Google-style tool docstrings,
structured logging, and active OpenTelemetry tracing telemetry wiring.
"""

import logging
from typing import Any, Dict, List, Optional

import pydantic

from google3.experimental.users.slichtor.exercise_planner_agent import firestore_service
from google3.experimental.users.slichtor.exercise_planner_agent import observability

logger = logging.getLogger(__name__)


# --- Pydantic Input Validation Models ---


class UserProfileSchema(pydantic.BaseModel):
  """Schema for validating user fitness profile input parameters."""

  goals: List[str] = pydantic.Field(
      description="List of fitness goals (e.g. ['strength', 'weight_loss'])"
  )
  fitness_level: str = pydantic.Field(
      default="beginner",
      description=(
          "User experience level: 'beginner', 'intermediate', 'advanced'"
      ),
  )
  schedule_days: int = pydantic.Field(
      default=3,
      ge=1,
      le=7,
      description="Number of workout days per week (1 to 7)",
  )
  equipment: str = pydantic.Field(
      default="full_gym",
      description="Available equipment: 'full_gym', 'dumbbell', 'bodyweight'",
  )
  unavailable_days: Optional[List[str]] = pydantic.Field(
      default=None,
      description="Days of the week the user cannot train (e.g. ['Sunday'])",
  )


class ExerciseCatalogQuerySchema(pydantic.BaseModel):
  """Schema for validating exercise catalog search query filters."""

  query: str = pydantic.Field(
      default="", description="Free text search term (e.g. 'press', 'row')"
  )
  difficulty: Optional[str] = pydantic.Field(
      default=None,
      description="Difficulty filter: 'beginner', 'intermediate', 'advanced'",
  )
  muscle_group: Optional[str] = pydantic.Field(
      default=None,
      description=(
          "Target muscle group: 'chest', 'back', 'legs', 'shoulders', 'arms',"
          " 'core'"
      ),
  )
  primary_goal: Optional[str] = pydantic.Field(
      default=None,
      description="Primary goal filter: 'strength', 'muscle_gain', 'endurance'",
  )
  equipment: Optional[str] = pydantic.Field(
      default=None,
      description=(
          "Equipment filter: 'barbell', 'dumbbell', 'bodyweight', 'cable',"
          " 'machine'"
      ),
  )


class WorkoutPlanSaveSchema(pydantic.BaseModel):
  """Schema for validating workout plan payloads prior to persistence."""

  title: str = pydantic.Field(
      default="Custom Workout Routine",
      description="Title of the workout routine",
  )
  days: List[Dict[str, Any]] = pydantic.Field(
      description="Structured daily exercise splits"
  )


class CompletedExerciseLogSchema(pydantic.BaseModel):
  """Schema for validating completed exercise log entries."""

  exercise_name: str = pydantic.Field(
      description="Exact name of completed exercise"
  )
  sets: int = pydantic.Field(
      ge=1, le=20, description="Number of completed sets (1 to 20)"
  )
  reps: int = pydantic.Field(
      ge=1, le=100, description="Number of reps completed per set (1 to 100)"
  )
  weight: float = pydantic.Field(
      default=0.0, ge=0.0, description="Weight used in pounds/kg (>= 0.0)"
  )


# --- ADK Agent Function Tools ---


def save_user_profile(
    goals: List[str],
    fitness_level: str = "beginner",
    schedule_days: int = 3,
    equipment: str = "full_gym",
    unavailable_days: Optional[List[str]] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Saves customized user profile preferences to Cloud Firestore / Local DB.

  Args:
    goals: List of primary fitness goals (e.g., ['strength', 'muscle_gain']).
    fitness_level: User experience level ('beginner', 'intermediate',
      'advanced'). Default 'beginner'.
    schedule_days: Number of training days per week (1 to 7). Default 3.
    equipment: Primary equipment available ('full_gym', 'dumbbell',
      'bodyweight'). Default 'full_gym'.
    unavailable_days: Optional list of days the user cannot exercise (e.g.
      ['Sunday']).
    context: Execution context dictionary supplied by ADK runtime (contains
      user_id).

  Returns:
    Dict containing 'status' ('success') and saved profile record dictionary.
  """
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  logger.info(
      "Executing tool 'save_user_profile' for user '%s' (goals=%s)",
      user_id,
      goals,
  )

  # Pydantic Input Validation
  validated = UserProfileSchema(
      goals=goals,
      fitness_level=fitness_level,
      schedule_days=schedule_days,
      equipment=equipment,
      unavailable_days=unavailable_days,
  )

  result = firestore_service.db_service.save_user_profile(
      user_id=user_id,
      goals=validated.goals,
      fitness_level=validated.fitness_level,
      schedule_days=validated.schedule_days,
      equipment=validated.equipment,
      unavailable_days=validated.unavailable_days,
  )

  observability.telemetry_collector.record_tool_intent_and_outcome(
      tool_name="save_user_profile",
      params={"user_id": user_id, "goals": goals, "level": fitness_level},
      outcome=result,
  )
  return result


def get_user_profile(
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
  """Retrieves saved user profile preferences from Cloud Firestore / Local DB.

  Args:
    context: Execution context dictionary supplied by ADK runtime (contains
      user_id).

  Returns:
    Optional Dict containing user goals, fitness level, schedule, and equipment
    preferences, or None if no profile exists.
  """
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  logger.info("Executing tool 'get_user_profile' for user '%s'", user_id)

  result = firestore_service.db_service.get_user_profile(user_id=user_id)

  observability.telemetry_collector.record_tool_intent_and_outcome(
      tool_name="get_user_profile",
      params={"user_id": user_id},
      outcome=result or {},
  )
  return result


def search_exercise_catalog(
    query: str = "",
    difficulty: Optional[str] = None,
    muscle_group: Optional[str] = None,
    primary_goal: Optional[str] = None,
    equipment: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Searches exercise catalog by muscle group, difficulty, goal, or equipment.

  Args:
    query: Free text search query string for matching exercise names or
      descriptions.
    difficulty: Optional difficulty filter ('beginner', 'intermediate',
      'advanced').
    muscle_group: Optional target muscle group ('chest', 'back', 'legs',
      'shoulders', 'arms', 'core').
    primary_goal: Optional goal filter ('strength', 'muscle_gain', 'endurance').
    equipment: Optional equipment filter ('barbell', 'dumbbell', 'bodyweight',
      'cable', 'machine').
    context: Execution context dictionary supplied by ADK runtime.

  Returns:
    Dict containing 'status' ('SUCCESS' or 'NO_MATCHING_EXERCISES'), 'count',
    and list of matching exercise dict records.
  """
  del context
  logger.info(
      "Executing tool 'search_exercise_catalog' (query='%s', muscle='%s',"
      " diff='%s')",
      query,
      muscle_group,
      difficulty,
  )

  # Pydantic Input Validation
  validated = ExerciseCatalogQuerySchema(
      query=query,
      difficulty=difficulty,
      muscle_group=muscle_group,
      primary_goal=primary_goal,
      equipment=equipment,
  )

  results = firestore_service.db_service.search_exercise_catalog(
      query=validated.query,
      difficulty=validated.difficulty,
      muscle_group=validated.muscle_group,
      primary_goal=validated.primary_goal,
      equipment=validated.equipment,
  )

  if not results:
    outcome = {
        "status": "NO_MATCHING_EXERCISES",
        "message": (
            "No exercises found matching criteria. Relax filters or broaden"
            " search."
        ),
        "suggested_actions": [
            "Omit equipment filter",
            "Try query='' with difficulty='beginner'",
        ],
        "results": [],
    }
  else:
    outcome = {"status": "SUCCESS", "count": len(results), "results": results}

  observability.telemetry_collector.record_tool_intent_and_outcome(
      tool_name="search_exercise_catalog",
      params={"query": query, "muscle": muscle_group, "diff": difficulty},
      outcome=outcome,
  )
  return outcome


def save_workout_plan(
    plan: Dict[str, Any], context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
  """Saves a generated multi-day workout plan to Cloud Firestore / Local DB.

  Args:
    plan: Structured workout plan dictionary containing title and daily exercise
      routines.
    context: Execution context dictionary supplied by ADK runtime (contains
      user_id).

  Returns:
    Dict containing 'status' ('success') and saved plan metadata record.
  """
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  logger.info("Executing tool 'save_workout_plan' for user '%s'", user_id)

  result = firestore_service.db_service.save_workout_plan(
      user_id=user_id, plan=plan
  )

  observability.telemetry_collector.record_tool_intent_and_outcome(
      tool_name="save_workout_plan",
      params={"user_id": user_id, "plan_keys": list(plan.keys())},
      outcome=result,
  )
  return result


def get_latest_workout_plan(
    context: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
  """Retrieves the user's latest saved workout plan from database.

  Args:
    context: Execution context dictionary supplied by ADK runtime (contains
      user_id).

  Returns:
    Optional Dict containing the latest workout plan dictionary, or None if no
    plan exists.
  """
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  logger.info("Executing tool 'get_latest_workout_plan' for user '%s'", user_id)

  result = firestore_service.db_service.get_latest_workout_plan(user_id=user_id)

  observability.telemetry_collector.record_tool_intent_and_outcome(
      tool_name="get_latest_workout_plan",
      params={"user_id": user_id},
      outcome=result or {},
  )
  return result


def log_completed_exercise(
    exercise_name: str,
    sets: int,
    reps: int,
    weight: float = 0.0,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Logs a completed exercise session entry with sets, reps, and weight.

  Args:
    exercise_name: Exact name of completed exercise (e.g. 'Barbell Bench
      Press').
    sets: Number of sets completed (1 to 20).
    reps: Number of repetitions per set (1 to 100).
    weight: Weight load used in lbs/kg (>= 0.0). Default 0.0.
    context: Execution context dictionary supplied by ADK runtime (contains
      user_id).

  Returns:
    Dict containing 'status' ('success') and logged entry metadata.
  """
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  logger.info(
      "Executing tool 'log_completed_exercise' for user '%s' (%s: %dx%d @"
      " %.1flbs)",
      user_id,
      exercise_name,
      sets,
      reps,
      weight,
  )

  # Pydantic Input Validation
  validated = CompletedExerciseLogSchema(
      exercise_name=exercise_name, sets=sets, reps=reps, weight=weight
  )

  result = firestore_service.db_service.log_completed_exercise(
      user_id=user_id,
      exercise_name=validated.exercise_name,
      sets=validated.sets,
      reps=validated.reps,
      weight=validated.weight,
  )

  observability.telemetry_collector.record_tool_intent_and_outcome(
      tool_name="log_completed_exercise",
      params={
          "user_id": user_id,
          "exercise": exercise_name,
          "sets": sets,
          "reps": reps,
      },
      outcome=result,
  )
  return result


def get_user_workout_history(
    time_window: str = "7_days", context: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Any]]:
  """Fetches logged exercise progress history for progress tracking.

  Args:
    time_window: Time window filter string (e.g. '7_days', '30_days'). Default
      '7_days'.
    context: Execution context dictionary supplied by ADK runtime (contains
      user_id).

  Returns:
    List of logged exercise entry dictionaries.
  """
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  logger.info(
      "Executing tool 'get_user_workout_history' for user '%s'", user_id
  )

  results = firestore_service.db_service.get_user_workout_history(
      user_id=user_id, time_window=time_window
  )

  observability.telemetry_collector.record_tool_intent_and_outcome(
      tool_name="get_user_workout_history",
      params={"user_id": user_id, "window": time_window},
      outcome={"count": len(results)},
  )
  return results
