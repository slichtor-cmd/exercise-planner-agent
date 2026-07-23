load("//third_party/bazel_rules/rules_python/python:defs.bzl", "py_binary", "py_library", "py_test")

package(default_visibility = ["//visibility:public"])

py_library(
    name = "exercise_planner_agent",
    srcs = [
        "__init__.py",
        "agent.py",
        "custom_functions.py",
        "firestore_service.py",
        "guardrails.py",
        "hitl_service.py",
        "interactive_chat.py",
        "main.py",
        "observability.py",
        "run_eval.py",
        "tests/__init__.py",
        "tests/test_agent_core.py",
        "tests/test_ai_tester.py",
        "tests/test_production_eval.py",
        "tests/test_security_guardrails.py",
        "tests/test_tools_and_hitl.py",
    ],
    data = [
        "eval_config.yaml",
        "eval_dataset.jsonl",
        "instructions.md",
        "skills/plan_refinement/SKILL.md",
        "skills/workout_planning/SKILL.md",
        "terraform/main.tf",
    ],
    deps = [
        "//third_party/py/google/adk",
        "//third_party/py/google/adk:runners",
        "//third_party/py/google/cloud:core",
        "//third_party/py/google/cloud/secretmanager",
        "//third_party/py/google/genai",
        "//third_party/py/pydantic:pydantic_v2",
        "//third_party/py/yaml",
    ],
)

py_binary(
    name = "main",
    srcs = ["main.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)

py_binary(
    name = "interactive_chat",
    srcs = ["interactive_chat.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)

py_binary(
    name = "deploy_vertex",
    srcs = ["deploy_vertex.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
        "//third_party/py/google/cloud/aiplatform",
    ],
)

py_binary(
    name = "run_eval",
    srcs = ["run_eval.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)

py_test(
    name = "test_agent_core",
    srcs = ["tests/test_agent_core.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)

py_test(
    name = "test_tools_and_hitl",
    srcs = ["tests/test_tools_and_hitl.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)

py_test(
    name = "test_security_guardrails",
    srcs = ["tests/test_security_guardrails.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)

py_test(
    name = "test_production_eval",
    srcs = ["tests/test_production_eval.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)

py_test(
    name = "test_ai_tester",
    srcs = ["tests/test_ai_tester.py"],
    deps = [
        ":exercise_planner_agent",
        "//third_party/py/google/adk",
    ],
)
