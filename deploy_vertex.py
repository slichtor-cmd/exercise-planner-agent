"""Deployment script registering ADK Exercise Planner Agent to Vertex AI Agent Engine."""

import argparse
import sys
from typing import Any, Dict

from google3.experimental.users.slichtor.exercise_planner_agent import agent

try:
  from google.cloud.aiplatform import aiplatform  # pylint: disable=g-import-not-at-top
  from google.cloud.aiplatform import vertexai  # pylint: disable=g-import-not-at-top
  from google.cloud.aiplatform.vertexai.preview import reasoning_engines  # pylint: disable=g-import-not-at-top
except (ImportError, ModuleNotFoundError) as err:
  sys.stderr.write(
      f"WARNING: google.cloud.aiplatform SDK not available: {err}\n"
  )
  aiplatform = None
  vertexai = None
  reasoning_engines = None


def deploy_agent_to_vertex(
    project_id: str = "slichtor-test-sandbox-667157",
    location: str = "us-central1",
    display_name: str = "exercise-planner-agent-prod",
    staging_bucket: str = "gs://slichtor-test-sandbox-667157-agent-staging",
) -> Any:
  """Registers and deploys the root ADK FitnessCoordinator agent to Vertex AI Agent Engine."""
  if aiplatform is None or reasoning_engines is None:
    raise RuntimeError(
        "google-cloud-aiplatform package is required for deployment."
    )

  print(
      f"Initializing Vertex AI SDK for project '{project_id}' in '{location}'"
      f" with staging bucket '{staging_bucket}'..."
  )
  aiplatform.init(
      project=project_id, location=location, staging_bucket=staging_bucket
  )
  vertexai.init(
      project=project_id, location=location, staging_bucket=staging_bucket
  )

  print("Instantiating ADK Root Coordinator Agent...")
  root_agent = agent.create_agent()
  adk_app = reasoning_engines.AdkApp(agent=root_agent)

  print("Deploying Reasoning Engine artifact to Vertex AI Agent Engine...")
  reasoning_engine = reasoning_engines.ReasoningEngine.create(
      reasoning_engine=adk_app,
      requirements=[
          "google-adk",
          "google-genai",
          "google-cloud-firestore",
          "google-cloud-secret-manager",
      ],
      display_name=display_name,
      description="Multi-Agent Exercise Routine Planner & Tracker (ADK)",
  )

  print(
      "✅ Agent successfully deployed!\nResource Name:"
      f" {reasoning_engine.resource_name}"
  )
  return reasoning_engine


def query_deployed_agent(
    resource_name: str,
    prompt: str = "Suggest a 3-day workout routine for strength.",
    user_id: str = "user_demo",
) -> Dict[str, Any]:
  """Queries a deployed Vertex AI Reasoning Engine instance."""
  if aiplatform is None:
    raise RuntimeError("google-cloud-aiplatform package is required.")

  print(f"Connecting to remote Reasoning Engine '{resource_name}'...")
  remote_agent = reasoning_engines.ReasoningEngine(resource_name)

  print(f"Sending prompt: '{prompt}'...")
  response = remote_agent.query(
      input=prompt,
      context={"user_id": user_id},
  )
  print(f"Response: {response}")
  return response


def main():
  parser = argparse.ArgumentParser(
      description="Deploy ADK Agent to Vertex AI Agent Engine."
  )
  parser.add_argument(
      "--project_id",
      default="slichtor-test-sandbox-667157",
      help="GCP Project ID",
  )
  parser.add_argument(
      "--location",
      default="us-central1",
      help="GCP Region Location",
  )
  parser.add_argument(
      "--staging_bucket",
      default="gs://slichtor-test-sandbox-667157-agent-staging",
      help="GCS Staging Bucket URI (e.g. gs://my-bucket)",
  )
  parser.add_argument(
      "--display_name",
      default="exercise-planner-agent-prod",
      help="Reasoning Engine Display Name",
  )
  parser.add_argument(
      "--query_resource",
      default="",
      help="Resource Name of existing Reasoning Engine to query",
  )
  parser.add_argument(
      "--prompt",
      default="Suggest a 3-day workout routine for strength.",
      help="Prompt string for testing deployed agent",
  )
  args = parser.parse_args()

  if args.query_resource:
    query_deployed_agent(
        resource_name=args.query_resource,
        prompt=args.prompt,
    )
  else:
    deploy_agent_to_vertex(
        project_id=args.project_id,
        location=args.location,
        staging_bucket=args.staging_bucket,
        display_name=args.display_name,
    )


if __name__ == "__main__":
  main()
