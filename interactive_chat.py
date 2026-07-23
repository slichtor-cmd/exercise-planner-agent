"""Interactive CLI REPL Chat Frontend for Exercise Planner Agent."""

import json
from typing import Any, Dict

from google3.experimental.users.slichtor.exercise_planner_agent import agent
from google3.experimental.users.slichtor.exercise_planner_agent import guardrails
from google3.experimental.users.slichtor.exercise_planner_agent import hitl_service
from google3.experimental.users.slichtor.exercise_planner_agent import observability

try:
  from google.adk import runners  # pylint: disable=g-import-not-at-top
except (ImportError, ModuleNotFoundError):
  runners = None


class PureADKInteractiveChat:
  """Pure ADK-driven interactive terminal REPL."""

  def __init__(self):
    self.coordinator = agent.create_coordinator_agent()
    self.active_user_id = "user_default"
    self.session_context: Dict[str, Any] = {
        "user_id": self.active_user_id,
        "session_id": "cli_session_default",
    }
    if runners is not None:
      self.runner = runners.InMemoryRunner(agent=self.coordinator)
      self.runner.auto_create_session = True
    else:
      self.runner = None

  def start(self):
    """Starts the interactive CLI loop for user interaction."""
    print("=" * 70)
    print("🏋️  Welcome to the Exercise Planner & Tracker Agent CLI (Pure ADK)")
    print(
        "Commands: '/user <id>' to switch user, '/approve <id>' for HITL, "
        "'/telemetry' for ops metrics, 'exit' to quit."
    )
    print("=" * 70)

    while True:
      try:
        raw_input = input(f"\n[{self.active_user_id}] > ").strip()
        if not raw_input:
          continue

        if raw_input.lower() in ["exit", "quit"]:
          print("\n👋 Thank you for using Exercise Planner Agent. Goodbye!")
          break

        # Command Dispatcher
        if raw_input.startswith("/user "):
          new_id = raw_input.split("/user ", 1)[1].strip()
          if new_id:
            self.active_user_id = new_id
            self.session_context["user_id"] = self.active_user_id
            print(
                f"🔄 Active user context switched to: '{self.active_user_id}'"
            )
          continue

        if raw_input.startswith("/approve"):
          parts = raw_input.split(" ", 1)
          draft_id = parts[1].strip() if len(parts) > 1 else ""
          if not draft_id:
            draft_id = (
                hitl_service.hitl_service.get_latest_pending_draft_id() or ""
            )
            if not draft_id:
              print("\n❌ No pending email draft found to approve.")
              continue
          res = hitl_service.approve_email_draft(draft_id)
          print(
              f"\n📬 HITL Staging Action Result:\n{json.dumps(res, indent=2)}"
          )
          continue

        if raw_input.lower() == "/telemetry":
          summary = observability.telemetry_collector.get_telemetry_summary()
          print(
              "\n📊 System Observability Telemetry:\n"
              f"{json.dumps(summary, indent=2)}"
          )
          continue

        # DLP PII Scrubbing
        try:
          clean_text = guardrails.redact_pii_dlp(raw_input)
        except (ImportError, PermissionError):
          clean_text = raw_input

        # Execute Turn
        response = agent.run_agent_turn(
            self.coordinator,
            clean_text,
            context=self.session_context,
            runner=self.runner,
        )
        print(f"\n{response}")

      except (KeyboardInterrupt, EOFError):
        print("\nSession interrupted. Exiting.")
        break


if __name__ == "__main__":
  chat = PureADKInteractiveChat()
  chat.start()
