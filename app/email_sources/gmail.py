"""Gmail API source - disabled by user configuration."""

from app.email_sources.base import EmailSource
from app.config import settings


class GmailSource(EmailSource):
    """
    Gmail API source for fetching real emails.

    This module is disabled because USE_GMAIL_API=false in the configuration.
    To enable, set USE_GMAIL_API=true in .env and provide a credentials.json file.
    """

    def __init__(self):
        if not settings.USE_GMAIL_API:
            raise RuntimeError(
                "Gmail integration is disabled. Set USE_GMAIL_API=true in .env to enable."
            )

    def get_email_text(self, **kwargs) -> str:
        """Fetch email text from Gmail API."""
        raise NotImplementedError("Gmail integration is not enabled.")