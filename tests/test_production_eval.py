"""Consolidated Production Readiness, Telemetry Observability, and ADK Evaluation Tests."""

import pathlib
import unittest

from google3.experimental.users.slichtor.exercise_planner_agent import observability
from google3.experimental.users.slichtor.exercise_planner_agent import run_eval


class TestProductionEval(unittest.TestCase):
  """Unit tests for telemetry, ADK benchmark scoring, and IaC structure."""

  def test_telemetry_observability_collector(self):
    """Test token metrics, tool invocation counts, and OpenTelemetry trace span generation."""
    observability.telemetry_collector.record_tool_invocation(
        "search_exercise_catalog"
    )
    observability.telemetry_collector.record_token_usage(
        prompt_tokens=150, completion_tokens=300
    )

    span = observability.telemetry_collector.start_trace_span(
        "WorkoutPlanner_Execution", "WorkoutPlanner"
    )
    self.assertEqual(span["span_name"], "WorkoutPlanner_Execution")
    self.assertEqual(span["agent_name"], "WorkoutPlanner")

    ended_span = observability.telemetry_collector.end_trace_span(span)
    self.assertEqual(ended_span["status"], "OK")

    summary = observability.telemetry_collector.get_telemetry_summary()
    self.assertEqual(summary["total_tokens"], 450)
    self.assertIn("search_exercise_catalog", summary["tool_invocations"])

  def test_adk_evaluation_benchmark_scoring(self):
    """Test ADK Evaluation scoring against target thresholds."""
    evaluator = run_eval.ADKEvaluator()
    report = evaluator.run_evaluation()

    self.assertEqual(report["eval_name"], "exercise_planner_agent_eval")
    self.assertGreater(report["total_test_cases"], 0)
    self.assertIn("plan_safety_score", report["scores"])
    self.assertIn("tool_accuracy_score", report["scores"])
    self.assertEqual(report["overall_status"], "PASSED")

  def test_terraform_iac_file_structure(self):
    """Test Terraform IaC infrastructure declarations."""
    tf_file = pathlib.Path(__file__).parent.parent / "terraform" / "main.tf"
    self.assertTrue(tf_file.exists())

    tf_content = tf_file.read_text(encoding="utf-8")
    self.assertIn("google_firestore_database", tf_content)
    self.assertIn("google_cloud_run_v2_service", tf_content)


if __name__ == "__main__":
  unittest.main()
