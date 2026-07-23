"""Consolidated Custom Functions, Data Persistence, and HITL Tests."""

import unittest

from google3.experimental.users.slichtor.exercise_planner_agent import custom_functions
from google3.experimental.users.slichtor.exercise_planner_agent import hitl_service


class TestToolsAndHITL(unittest.TestCase):
  """Unit tests for custom functions, Firestore persistence, and HITL staging."""

  def test_profile_and_catalog_search(self):
    """Test user profile creation and exercise catalog search."""
    context = {"user_id": "test_user_tools"}

    save_res = custom_functions.save_user_profile(
        goals=["strength"],
        fitness_level="intermediate",
        schedule_days=4,
        equipment="dumbbells_only",
        context=context,
    )
    self.assertEqual(save_res["status"], "success")

    profile = custom_functions.get_user_profile(context=context)
    self.assertEqual(profile["fitness_level"], "intermediate")

    catalog = custom_functions.search_exercise_catalog(
        muscle_group="chest", equipment="dumbbell", context=context
    )
    self.assertEqual(catalog["status"], "SUCCESS")
    self.assertGreater(len(catalog["results"]), 0)

  def test_workout_plan_saving_and_retrieval(self):
    """Test saving and retrieving 7-day workout plans."""
    context = {"user_id": "plan_user_1"}
    sample_plan = {
        "title": "4-Day Hypertrophy Routine",
        "schedule_days": 4,
        "non_consecutive_rest": True,
    }

    result = custom_functions.save_workout_plan(
        plan=sample_plan, context=context
    )
    self.assertEqual(result["status"], "success")
    self.assertTrue(result["plan_id"].startswith("plan_"))

    latest = custom_functions.get_latest_workout_plan(context=context)
    self.assertEqual(latest["plan"]["title"], "4-Day Hypertrophy Routine")

  def test_workout_history_logging(self):
    """Test logging completed exercises and retrieving history."""
    context = {"user_id": "logger_user"}

    log_res = custom_functions.log_completed_exercise(
        "Barbell Bench Press", sets=3, reps=10, weight=135.0, context=context
    )
    self.assertEqual(log_res["status"], "success")

    history = custom_functions.get_user_workout_history(context=context)
    self.assertGreater(len(history), 0)
    self.assertEqual(history[-1]["user_id"], "logger_user")

  def test_hitl_email_draft_pausing_and_approval(self):
    """Test that email drafting pauses for user approval before sending."""
    draft_res = hitl_service.draft_weekly_email(
        recipient="athlete@example.com",
        subject="Weekly Summary",
        body="Routine details...",
    )
    self.assertEqual(draft_res["status"], "PAUSED")
    draft_id = draft_res["draft_id"]

    # Verify pending state in HITL store
    record = hitl_service.hitl_service.get_draft(draft_id)
    self.assertEqual(record["status"], "PENDING_APPROVAL")
    self.assertEqual(record["execution_state"], "PAUSED_FOR_HUMAN_APPROVAL")

    # Explicit approval
    approve_res = hitl_service.hitl_service.approve_email_draft(draft_id)
    self.assertEqual(approve_res["status"], "SENT")
    updated_record = hitl_service.hitl_service.get_draft(draft_id)
    self.assertEqual(updated_record["execution_state"], "COMPLETED")


if __name__ == "__main__":
  unittest.main()
