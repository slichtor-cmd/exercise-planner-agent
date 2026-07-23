"""Human-in-the-Loop (HITL) email drafting and review staging service."""

import datetime
from typing import Any, Dict, Optional


class HITLEmailService:
  """Staging service for managing human-in-the-loop approval workflows."""

  def __init__(self):
    self._draft_store: Dict[str, Dict[str, Any]] = {}

  def draft_weekly_email(
      self,
      recipient: str,
      subject: str,
      body: str,
      user_id: str = "user_default",
  ) -> Dict[str, Any]:
    """Drafts outbound email and pauses execution until approved by human.

    Args:
      recipient: Recipient email address.
      subject: Subject line of the email.
      body: Email body text.
      user_id: Target user identity context.

    Returns:
      Dict containing draft ID and PAUSED execution state.
    """
    draft_id = f"email_draft_{len(self._draft_store) + 1}"
    record = {
        "draft_id": draft_id,
        "user_id": user_id,
        "recipient": recipient,
        "subject": subject,
        "body": body,
        "status": "PENDING_APPROVAL",
        "execution_state": "PAUSED_FOR_HUMAN_APPROVAL",
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    self._draft_store[draft_id] = record
    return {
        "status": "PAUSED",
        "draft_id": draft_id,
        "message": (
            "Email draft generated and paused for user review. Please approve"
            " before sending."
        ),
        "draft_preview": {
            "to": recipient,
            "subject": subject,
            "body": body,
        },
    }

  def approve_email_draft(self, draft_id: str) -> Dict[str, Any]:
    """Simulates user reviewing and approving a staged email draft."""
    if draft_id not in self._draft_store:
      return {"status": "ERROR", "message": f"Draft '{draft_id}' not found."}

    draft = self._draft_store[draft_id]
    if draft["status"] == "APPROVED":
      return {"status": "ALREADY_SENT", "draft_id": draft_id}

    draft["status"] = "APPROVED"
    draft["execution_state"] = "COMPLETED"
    draft["sent_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

    return {
        "status": "SENT",
        "draft_id": draft_id,
        "recipient": draft["recipient"],
        "subject": draft["subject"],
        "sent_at": draft["sent_at"],
    }

  def get_draft(self, draft_id: str) -> Optional[Dict[str, Any]]:
    """Retrieves a staged email draft."""
    return self._draft_store.get(draft_id)

  def get_latest_pending_draft_id(self) -> Optional[str]:
    """Returns the ID of the most recently created pending email draft."""
    pending = [
        d_id
        for d_id, rec in self._draft_store.items()
        if rec.get("status") == "PENDING_APPROVAL"
    ]
    return pending[-1] if pending else None


# Global singleton instance for local HITL runtime
hitl_service = HITLEmailService()


def draft_weekly_email(
    recipient: str,
    subject: str,
    body: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
  """Tool invoked by CommunicationDispatcher agent to prepare email drafts.

  Args:
    recipient: Destination email address.
    subject: Email subject title.
    body: Email body string.
    context: Context dictionary containing user_id.

  Returns:
    Staging response dictionary with PAUSED execution status.
  """
  clean_body = body.strip() if body else ""
  clean_subject = subject.strip() if subject else ""
  clean_recipient = recipient.strip() if recipient else ""
  user_id = (
      context.get("user_id", "user_default") if context else "user_default"
  )
  return hitl_service.draft_weekly_email(
      recipient=clean_recipient,
      subject=clean_subject,
      body=clean_body,
      user_id=user_id,
  )


def approve_email_draft(draft_id: str) -> Dict[str, Any]:
  """Module-level function to approve a staged email draft."""
  return hitl_service.approve_email_draft(draft_id)
