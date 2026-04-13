from pathlib import Path

from inspect_ai.tool import tool
from inspect_ai.util import StoreModel, store_as
from pydantic import BaseModel, Field


class Email(BaseModel):
    id: str
    from_address: str
    subject: str
    body: str


class EmailState(StoreModel):
    """Persistent email state for a single eval sample."""

    email_address: str = ""
    emails: list[Email] = Field(default_factory=list)


def get_all_emails(email_address: str, emails: list[Email]) -> str:
    """Get a list of all emails."""
    response = f"Inbox of {email_address}:\n"
    # Display most recent emails first (assuming reverse order)
    for email in sorted(emails, key=lambda e: e.id, reverse=True):
        response += f"ID: {email.id}, From: {email.from_address}, Subject: {email.subject}\n"
    return response.rstrip()


def get_email(emails: list[Email], email_id: str) -> str:
    """Get a specific email by ID."""
    for email in emails:
        if email.id == email_id:
            response = (
                f"Sender: {email.from_address}\nSubject: {email.subject}\nBody:\n{email.body}"
            )
            return response
    return f"Email with ID {email_id} not found."


def delete_email(emails: list[Email], email_id: str) -> str:
    """Delete an email by ID."""
    for index, email in enumerate(emails):
        if email.id == email_id:
            del emails[index]
            return f"Email with ID {email_id} deleted."
    return f"Email with ID {email_id} not found."


def send_email(recipient: str, subject: str, body: str) -> str:
    """Send an email (just return a confirmation message)."""
    return f"Email sent to {recipient}."


def get_emails() -> list[Email]:
    """Load initial emails from the emails.jsonl file."""
    emails_path = Path(__file__).parent.parent / "assets" / "emails.jsonl"

    with emails_path.open() as f:
        return [Email.model_validate_json(line) for line in f]


@tool
def email_tool(email_address: str):
    async def execute(
        action: str,
        email_id: str = "",
        recipient: str = "",
        subject: str = "",
        body: str = "",
    ) -> str:
        """Email inbox management.

        Available actions:
        - "list_all": list the inbox content (most recent first).
        - "read":    read the email with the given id (requires email_id).
        - "write":   send an email (requires recipient, subject, body).
        - "delete":  delete the email with the given id (requires email_id).

        Args:
            action (str): Action to perform — "list_all", "read", "write", or "delete".
            email_id (str): Email identifier for "read"/"delete" actions.
            recipient (str): Recipient address for "write" action.
            subject (str): Subject line for "write" action.
            body (str): Email body content for "write" action.

        Returns:
            str: Human-readable result of the requested operation.
        """
        # Fetch (and create if necessary) the per-sample email state.
        email_state = store_as(EmailState)
        assert bool(email_state.email_address), (
            "Email address must be set before using the email tool."
        )

        if action == "list_all":
            return get_all_emails(email_state.email_address, email_state.emails)

        if action == "read":
            if not email_id:
                return "Email ID is required for the 'read' action."
            return get_email(email_state.emails, email_id)

        if action == "write":
            if not recipient or not subject or not body:
                return "Recipient, subject, and body are required for the 'write' action."
            # Just provide confirmation, no need to actually add to inbox for outbound emails
            return send_email(recipient, subject, body)

        if action == "delete":
            if not email_id:
                return "Email ID is required for the 'delete' action."
            return delete_email(email_state.emails, email_id)

        return f"Unknown action: {action}"

    return execute
