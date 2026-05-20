"""Manual text input source."""

from app.email_sources.base import EmailSource


class ManualSource(EmailSource):
    """Manual text input - email text provided directly by user."""

    def get_email_text(self, email_text: str = "") -> str:
        """Return the provided email text."""
        return email_text