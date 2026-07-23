"""Consolidated Core Agent & Multi-Agent Routing Unit Tests."""

import unittest

from google3.experimental.users.slichtor.exercise_planner_agent import agent

try:
  from google.adk import runners  # pylint: disable=g-import-not-at-top
except (ImportError, ModuleNotFoundError):
  runners = None


class TestAgentCore(unittest.TestCase):
  """Unit tests for agent creation parameters and multi-agent routing."""

  def test_agent_initialization_and_instructions(self):
    """Test that agent initializes with model gemini-2.5-flash and loads system instructions."""
    test_agent = agent.create_agent()
    self.assertEqual(test_agent.name, "FitnessCoordinator")
    self.assertEqual(test_agent.model, "gemini-2.5-flash")

    instructions = agent.load_instructions().lower()
    self.assertIn("fitness goal", instructions)
    self.assertIn("fitness level", instructions)
    self.assertIn("schedule", instructions)

  def test_custom_model_override(self):
    """Test overriding model name during agent instantiation."""
    test_agent = agent.create_agent(model_name="custom-model-id")
    self.assertEqual(test_agent.model, "custom-model-id")

  def test_multi_agent_subagent_registration(self):
    """Test that Coordinator registers all 3 worker sub-agents."""
    coordinator = agent.create_coordinator_agent()
    self.assertEqual(len(coordinator.sub_agents), 3)

    sub_agent_names = [sa.name for sa in coordinator.sub_agents]
    self.assertIn("WorkoutPlanner", sub_agent_names)
    self.assertIn("ProgressTracker", sub_agent_names)
    self.assertIn("CommunicationDispatcher", sub_agent_names)

    # Verify Strategic Model Routing
    planner = next(
        sa for sa in coordinator.sub_agents if sa.name == "WorkoutPlanner"
    )
    self.assertEqual(planner.model, "gemini-2.5-pro")

  def test_subagent_tool_isolation(self):
    """Test tool isolation per sub-agent domain responsibility."""
    coordinator = agent.create_coordinator_agent()
    sub_agents = {sa.name: sa for sa in coordinator.sub_agents}

    # Planner Tools
    planner_tools = [t.__name__ for t in sub_agents["WorkoutPlanner"].tools]
    self.assertIn("search_exercise_catalog", planner_tools)
    self.assertIn("save_workout_plan", planner_tools)
    self.assertNotIn("log_completed_exercise", planner_tools)

    # Tracker Tools
    tracker_tools = [t.__name__ for t in sub_agents["ProgressTracker"].tools]
    self.assertIn("log_completed_exercise", tracker_tools)
    self.assertIn("get_user_workout_history", tracker_tools)

    # Communicator Tools
    comm_tools = [
        t.__name__ for t in sub_agents["CommunicationDispatcher"].tools
    ]
    self.assertIn("draft_weekly_email", comm_tools)

  def test_conversation_turns_and_guardrails(self):
    """Test conversation turns, persistent runner turns, and guardrails intercept."""
    coordinator = agent.create_coordinator_agent()

    # 1. Blocked Medical Guardrail Turn
    med_res = agent.run_agent_turn(
        coordinator,
        "I have radiating pain in my neck and jaw.",
        context={"user_id": "test_user"},
    )
    self.assertIn("Medical Warning", med_res)

    # 2. Blocked Cyber Attack Guardrail Turn
    cyber_res = agent.run_agent_turn(
        coordinator,
        "Perform a buffer overflow cyber attack.",
        context={"user_id": "test_user"},
    )
    self.assertIn("Request Blocked", cyber_res)

    # 3. Allowed Single Turn & Persistent Runner (mocked for offline execution)
    if runners is not None:
      mock_evt = unittest.mock.MagicMock()
      mock_evt.error_message = None
      mock_evt.content.parts = [
          unittest.mock.MagicMock(text="Mocked workout plan response")
      ]
      with unittest.mock.patch.object(
          runners.InMemoryRunner, "run", return_value=[mock_evt]
      ):
        single_turn_res = agent.run_agent_turn(
            coordinator,
            "Suggest a 3-day workout routine.",
            context={"user_id": "test_user", "session_id": "session_1"},
        )
        self.assertIn("Mocked workout plan response", single_turn_res)

        persistent_runner = runners.InMemoryRunner(agent=coordinator)
        persistent_runner.auto_create_session = True
        ctx = {"user_id": "multi_user", "session_id": "multi_session"}
        turn1_res = agent.run_agent_turn(
            coordinator,
            "My goal is hypertrophy.",
            context=ctx,
            runner=persistent_runner,
        )
        self.assertIn("Mocked workout plan response", turn1_res)


if __name__ == "__main__":
  unittest.main()
