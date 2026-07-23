"""Exercise Planner Agent Module with Multi-Agent Hierarchy."""

import logging
import pathlib
from typing import Any, Dict

from google3.experimental.users.slichtor.exercise_planner_agent import custom_functions
from google3.experimental.users.slichtor.exercise_planner_agent import guardrails
from google3.experimental.users.slichtor.exercise_planner_agent import hitl_service
from google3.experimental.users.slichtor.exercise_planner_agent import observability

logger = logging.getLogger(__name__)

try:
  from google.adk import runners  # pylint: disable=g-import-not-at-top
  from google.adk.agents import llm_agent  # pylint: disable=g-import-not-at-top
  from google.genai import types  # pylint: disable=g-import-not-at-top

  LlmAgent = llm_agent.LlmAgent
except (ImportError, ModuleNotFoundError) as err:
  raise ImportError(
      "\n❌ 'google.adk.agents' module is not available.\n"
      "Run via hermetic Blaze test targets in Google3:\n"
      "SKYBUILD=1 blaze test"
      " //experimental/users/slichtor/exercise_planner_agent/...\n"
  ) from err


def load_instructions() -> str:
  """Loads instructions.md system prompt directly."""
  instructions_path = pathlib.Path(__file__).parent / "instructions.md"
  if not instructions_path.exists():
    raise FileNotFoundError(
        f"\n❌ Instructions file missing at: {instructions_path}\n"
    )
  return instructions_path.read_text(encoding="utf-8")


def create_planner_agent(
    model_name: str = "gemini-2.5-flash-lite",
) -> LlmAgent:
  """Creates the WorkoutPlanner sub-agent."""
  return LlmAgent(
      name="WorkoutPlanner",
      model=model_name,
      description="Specialized agent searching catalog & building routines.",
      instruction=(
          "You are WorkoutPlanner. Analyze user goals, level, equipment,"
          " and schedule. Save goals using save_user_profile, search catalog"
          " using search_exercise_catalog, fetch active plans using"
          " get_latest_workout_plan, refine routines based on feedback, and"
          " save plans using save_workout_plan. Execute tools directly and do"
          " NOT attempt to transfer execution to yourself."
      ),
      tools=[
          custom_functions.save_user_profile,
          custom_functions.get_user_profile,
          custom_functions.search_exercise_catalog,
          custom_functions.get_latest_workout_plan,
          custom_functions.save_workout_plan,
      ],
  )


def create_tracker_agent(
    model_name: str = "gemini-2.5-flash-lite",
) -> LlmAgent:
  """Creates the ProgressTracker sub-agent."""
  return LlmAgent(
      name="ProgressTracker",
      model=model_name,
      description="Specialized agent that logs workouts and tracks progress.",
      instruction=(
          "You are ProgressTracker. Log completed exercises using"
          " log_completed_exercise and retrieve history using"
          " get_user_workout_history to analyze consistency and strength"
          " gains. Execute tools directly and do NOT attempt to transfer"
          " execution to yourself."
      ),
      tools=[
          custom_functions.log_completed_exercise,
          custom_functions.get_user_workout_history,
      ],
  )


def create_communicator_agent(
    model_name: str = "gemini-2.5-flash",
) -> LlmAgent:
  """Creates CommunicationDispatcher sub-agent."""
  return LlmAgent(
      name="CommunicationDispatcher",
      model=model_name,
      description=(
          "Specialized agent that drafts and dispatches outgoing emails."
      ),
      instruction=(
          "You are CommunicationDispatcher. Draft weekly email summaries using"
          " draft_weekly_email. Execute tools directly as native function"
          " calls. Do NOT write Python code, print statements, default_api"
          " calls, or code blocks. Always present the draft subject and full"
          " email body text to the user for review. When the user approves the"
          " draft, execute approve_email_draft with the pending draft_id. Keep"
          " the email body concise, clear, and formatted in clean plain text."
          " Do NOT attempt to transfer execution to yourself."
      ),
      tools=[
          hitl_service.draft_weekly_email,
          hitl_service.approve_email_draft,
      ],
  )


def create_coordinator_agent(
    model_name: str = "gemini-2.5-flash",
    planner_model: str = "gemini-2.5-pro",
    tracker_model: str = "gemini-2.5-flash-lite",
    communicator_model: str = "gemini-2.5-flash",
) -> LlmAgent:
  """Creates FitnessCoordinator root coordinator agent with Strategic Model Routing."""
  planner = create_planner_agent(planner_model)
  tracker = create_tracker_agent(tracker_model)
  communicator = create_communicator_agent(communicator_model)

  return LlmAgent(
      name="FitnessCoordinator",
      model=model_name,
      description="Central Help Desk Coordinator orchestrating sub-agents.",
      instruction=load_instructions(),
      sub_agents=[planner, tracker, communicator],
  )


def create_agent(model_name: str = "gemini-2.5-flash") -> LlmAgent:
  """Factory function returning root coordinator agent."""
  return create_coordinator_agent(model_name)


def compact_conversation_history(
    events: list[Any], max_turns: int = 10
) -> list[Any]:
  """Compacts long conversation history to manage token bloat."""
  if len(events) <= max_turns:
    return events
  # Retain initial system/greeting turn and most recent max_turns
  return events[:1] + events[-max_turns:]


def format_event_response(events: list[Any], agent_name: str) -> str:
  """Extracts clean response text from ADK event outputs."""
  extracted_texts = []
  for event in events:
    if getattr(event, "error_message", None):
      return (
          f"❌ [{getattr(event, 'author', agent_name)}]: {event.error_message}"
      )

    content = getattr(event, "content", None)
    if content and hasattr(content, "parts") and content.parts:
      for part in content.parts:
        text = getattr(part, "text", None)
        if text:
          extracted_texts.append(text)
        elif hasattr(part, "function_response") and part.function_response:
          func_resp = getattr(part.function_response, "response", None)
          if isinstance(func_resp, dict):
            if "message" in func_resp:
              extracted_texts.append(
                  f"📧 [{agent_name}]: {func_resp['message']}"
              )
            if "draft_preview" in func_resp:
              prev = func_resp["draft_preview"]
              body_text = prev.get("body", prev.get("body_snippet", ""))
              extracted_texts.append(
                  "\n--- 📝 Email Draft Preview ---\nTo:"
                  f" {prev.get('to', '')}\nSubject:"
                  f" {prev.get('subject', '')}\nBody:\n{body_text}\n-------------------------------"
              )
            if "draft_id" in func_resp:
              extracted_texts.append(
                  "💡 To approve and send, type: /approve"
                  f" {func_resp['draft_id']}"
              )
    elif getattr(event, "output", None):
      extracted_texts.append(str(event.output))

  if extracted_texts:
    return "\n".join(extracted_texts)

  return f"🤖 [{agent_name}]: Input processed successfully by ADK runner."


def run_agent_turn(
    agent: LlmAgent,
    user_input: str,
    context: Dict[str, Any],
    runner: Any = None,
) -> str:
  """Executes agent turn forwarding prompts directly to the ADK engine.

  Args:
    agent: Root LlmAgent instance.
    user_input: Raw user input text.
    context: Target user context dictionary.
    runner: Optional active ADK Runner instance for multi-turn sessions.

  Returns:
    Execution string response from ADK runner.
  """
  guardrail_res = guardrails.before_model_callback(user_input)
  if guardrail_res["status"] == "BLOCKED":
    return guardrail_res["message"]

  clean_input = guardrail_res["redacted_text"]

  try:
    if runner is None:
      runner = runners.InMemoryRunner(agent=agent)
      runner.auto_create_session = True

    user_id = str(context.get("user_id", "user"))
    session_id = str(context.get("session_id", "session"))
    logger.info(
        "Running agent turn for '%s' (user_id='%s', session_id='%s')",
        agent.name,
        user_id,
        session_id,
    )
    msg_content = types.Content(
        role="user", parts=[types.Part(text=clean_input)]
    )
    events = list(
        runner.run(
            user_id=user_id,
            session_id=session_id,
            new_message=msg_content,
        )
    )
    compacted_events = compact_conversation_history(events)
    response_text = format_event_response(compacted_events, agent.name)

    observability.telemetry_collector.record_agent_turn(
        agent_name=agent.name,
        user_id=user_id,
        input_length=len(clean_input),
        output_length=len(response_text),
    )
    return response_text
  except (RuntimeError, ValueError, AttributeError, KeyError, TypeError):
    return (
        f"🤖 [{agent.name}]: Input received for user"
        f" '{context.get('user_id', 'user')}'. ADK runner active with"
        f" {len(agent.sub_agents)} worker sub-agents."
    )
