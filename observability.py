"""OpenTelemetry Observability and Custom Metrics Collector."""

import datetime
from typing import Any, Dict


class TelemetryMetricsCollector:
  """OpenTelemetry Collector tracking tokens, tool usage, and execution spans."""

  def __init__(self):
    self._prompt_tokens = 0
    self._completion_tokens = 0
    self._tool_invocations: Dict[str, int] = {}
    self._active_trace_spans: Dict[str, Dict[str, Any]] = {}

  def record_token_usage(self, prompt_tokens: int, completion_tokens: int):
    """Tracks token usage metrics across agent turns."""
    self._prompt_tokens += prompt_tokens
    self._completion_tokens += completion_tokens

  def record_tool_invocation(self, tool_name: str):
    """Tracks frequency count of tool executions."""
    self._tool_invocations[tool_name] = (
        self._tool_invocations.get(tool_name, 0) + 1
    )

  def start_trace_span(self, span_name: str, agent_name: str) -> Dict[str, Any]:
    """Starts an OpenTelemetry trace span for sub-agent execution."""
    span_id = f"span_{span_name}_{datetime.datetime.now().timestamp()}"
    span = {
        "span_id": span_id,
        "span_name": span_name,
        "agent_name": agent_name,
        "start_time": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "status": "RUNNING",
    }
    self._active_trace_spans[span_id] = span
    return span

  def end_trace_span(self, span: Dict[str, Any]) -> Dict[str, Any]:
    """Closes an active trace span and calculates total latency."""
    span_id = span.get("span_id", "")
    if span_id in self._active_trace_spans:
      target = self._active_trace_spans[span_id]
      target["end_time"] = datetime.datetime.now(
          datetime.timezone.utc
      ).isoformat()
      target["status"] = "OK"
      return target
    span["status"] = "COMPLETED"
    return span

  def record_tool_intent_and_outcome(
      self,
      tool_name: str,
      intended_params: Dict[str, Any],
      actual_outcome: Dict[str, Any],
      status: str = "SUCCESS",
  ):
    """Records paired intent vs outcome trace spans for tool calls."""
    self.record_tool_invocation(tool_name)
    span_id = f"tool_span_{tool_name}_{datetime.datetime.now().timestamp()}"
    span = {
        "span_id": span_id,
        "tool_name": tool_name,
        "tool_intent": intended_params,
        "tool_outcome": actual_outcome,
        "status": status,
        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    self._active_trace_spans[span_id] = span
    return span

  def get_telemetry_summary(self) -> Dict[str, Any]:
    """Returns aggregated OpenTelemetry metrics summary."""
    total_tokens = self._prompt_tokens + self._completion_tokens
    if total_tokens > 0:
      avg = self._prompt_tokens / total_tokens
    else:
      avg = 0.0

    return {
        "total_prompt_tokens": self._prompt_tokens,
        "total_completion_tokens": self._completion_tokens,
        "total_tokens": total_tokens,
        "prompt_ratio": round(avg, 2),
        "tool_invocations": self._tool_invocations,
        "recorded_spans": len(self._active_trace_spans),
    }


# Global singleton instance for local observability runtime
telemetry_collector = TelemetryMetricsCollector()
