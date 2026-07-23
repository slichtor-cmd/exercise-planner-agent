"""Main Root CLI Entrypoint for Exercise Planner & Tracker Agent.

Supports interactive chat REPL, single-prompt execution, batch directory
processing, and automated benchmark evaluation.
"""

import argparse
import glob
import json
import logging
import os
import sys
from typing import Any, Dict

from google3.experimental.users.slichtor.exercise_planner_agent import agent
from google3.experimental.users.slichtor.exercise_planner_agent import guardrails
from google3.experimental.users.slichtor.exercise_planner_agent import hitl_service
from google3.experimental.users.slichtor.exercise_planner_agent import observability
from google3.experimental.users.slichtor.exercise_planner_agent import run_eval

try:
  from google.adk import runners  # pylint: disable=g-import-not-at-top
except (ImportError, ModuleNotFoundError):
  runners = None


def run_single_prompt(prompt: str, user_id: str = "user_default") -> str:
  """Runs a single prompt turn non-interactively and returns the response."""
  coordinator = agent.create_coordinator_agent()
  context = {"user_id": user_id, "session_id": "single_turn_session"}

  # Redact PII
  try:
    clean_text = guardrails.redact_pii_dlp(prompt)
  except Exception:  # pylint: disable=broad-exception-caught
    clean_text = prompt

  response = agent.run_agent_turn(coordinator, clean_text, context=context)
  return response


def run_interactive_mode(user_id: str = "user_default"):
  """Runs the interactive CLI chat session or single execution if non-interactive."""
  # If executed in non-interactive environment (e.g. automated eval runner),
  # run a single turn non-interactively.
  if not sys.stdin.isatty():
    piped_input = sys.stdin.read().strip()
    default_prompt = (
        "Create a 3-day beginner workout routine focusing on strength."
    )
    prompt = piped_input if piped_input else default_prompt
    print(f"🤖 Processing non-interactive prompt: '{prompt}'...")
    res = run_single_prompt(prompt, user_id=user_id)
    print(f"\n{res}")
    return

  coordinator = agent.create_coordinator_agent()
  session_context: Dict[str, Any] = {
      "user_id": user_id,
      "session_id": "cli_session_default",
  }
  runner = (
      runners.InMemoryRunner(agent=coordinator) if runners is not None else None
  )
  if runner is not None:
    runner.auto_create_session = True

  print("=" * 70)
  print("🏋️  Exercise Planner & Tracker Agent CLI")
  print(
      "Commands: '/user <id>' to switch user, '/approve <id>' for HITL, "
      "'/telemetry' for ops metrics, 'exit' to quit."
  )
  print("=" * 70)

  while True:
    try:
      raw_input = input(f"\n[{user_id}] > ").strip()
      if not raw_input:
        continue

      if raw_input.lower() in ["exit", "quit"]:
        print("\n👋 Thank you for using Exercise Planner Agent. Goodbye!")
        break

      if raw_input.startswith("/user "):
        new_id = raw_input.split("/user ", 1)[1].strip()
        if new_id:
          user_id = new_id
          session_context["user_id"] = user_id
          print(f"🔄 Switched user to: '{user_id}'")
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
        print(f"\n📬 HITL Approval Result:\n{json.dumps(res, indent=2)}")
        continue

      if raw_input.lower() == "/telemetry":
        summary = observability.telemetry_collector.get_telemetry_summary()
        print(f"\n📊 Telemetry Summary:\n{json.dumps(summary, indent=2)}")
        continue

      # Scrub PII
      try:
        clean_text = guardrails.redact_pii_dlp(raw_input)
      except Exception:  # pylint: disable=broad-exception-caught
        clean_text = raw_input

      # Execute agent turn
      response = agent.run_agent_turn(
          coordinator,
          clean_text,
          context=session_context,
          runner=runner,
      )
      print(f"\n🤖 Agent:\n{response}")

    except (KeyboardInterrupt, EOFError):
      print("\n👋 Session ended.")
      break


def run_batch_mode(input_dir: str, output_dir: str, auto_approve: bool = False):
  """Processes batch prompt/profile files from input_dir and saves outputs to output_dir."""
  os.makedirs(output_dir, exist_ok=True)
  coordinator = agent.create_coordinator_agent()

  input_files = glob.glob(os.path.join(input_dir, "*.txt")) + glob.glob(
      os.path.join(input_dir, "*.json")
  )
  if not input_files:
    print(f"⚠️  No input files found in '{input_dir}'")
    return

  print(f"🔄 Processing {len(input_files)} input files in batch mode...")

  for filepath in input_files:
    filename = os.path.basename(filepath)
    user_id = os.path.splitext(filename)[0]
    with open(filepath, "r", encoding="utf-8") as f:
      prompt_content = f.read().strip()

    print(f"  -> Processing: '{filename}' for user '{user_id}'...")
    context = {"user_id": user_id, "batch_mode": True}

    response = agent.run_agent_turn(
        coordinator, prompt_content, context=context
    )

    if auto_approve:
      latest_draft = hitl_service.hitl_service.get_latest_pending_draft_id()
      if latest_draft:
        hitl_service.approve_email_draft(latest_draft)
        print(f"     ✅ Auto-approved email draft '{latest_draft}'")

    out_filepath = os.path.join(output_dir, f"{user_id}_output.json")
    out_payload = {
        "user_id": user_id,
        "input_file": filename,
        "agent_response": response,
        "hitl_drafts": hitl_service.hitl_service.list_pending_drafts(),
    }
    with open(out_filepath, "w", encoding="utf-8") as f:
      json.dump(out_payload, f, indent=2)

    print(f"     Saved output to '{out_filepath}'")

  print("✅ Batch processing complete!")


def run_evaluation_mode():
  """Runs evaluation benchmark dataset and prints JSON results."""
  print("📊 Running ADK Agent Benchmark Evaluation Suite...")
  evaluator = run_eval.ADKEvaluator()
  results = evaluator.run_evaluation()
  print(json.dumps(results, indent=2))
  return results


def main():
  logging.basicConfig(
      level=logging.INFO,
      format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
  )
  parser = argparse.ArgumentParser(
      description="Exercise Planner & Tracker Multi-Agent CLI"
  )
  parser.add_argument(
      "prompt",
      nargs="?",
      default="",
      help="Optional prompt string to run non-interactively",
  )
  parser.add_argument(
      "--mode",
      choices=["interactive", "batch", "eval"],
      default="interactive",
      help=(
          "Run mode: 'interactive' (REPL), 'batch' (file processing), or"
          " 'eval' (benchmark evaluation)"
      ),
  )
  parser.add_argument(
      "--eval",
      action="store_true",
      help="Run benchmark evaluation suite and exit",
  )
  parser.add_argument(
      "--user_id", default="user_default", help="Default User ID for session"
  )
  parser.add_argument(
      "--input_dir",
      default="./inputs",
      help="Directory containing batch prompt files",
  )
  parser.add_argument(
      "--output_dir",
      default="./plans",
      help="Directory to save generated workout plans",
  )
  parser.add_argument(
      "--auto_approve",
      action="store_true",
      help="Automatically approve pending HITL email drafts in batch mode",
  )
  args = parser.parse_args()

  if args.eval or args.mode == "eval":
    run_evaluation_mode()
  elif args.prompt:
    res = run_single_prompt(args.prompt, user_id=args.user_id)
    print(res)
  elif args.mode == "batch":
    run_batch_mode(
        input_dir=args.input_dir,
        output_dir=args.output_dir,
        auto_approve=args.auto_approve,
    )
  else:
    run_interactive_mode(user_id=args.user_id)


if __name__ == "__main__":
  main()
