"""Abstract base class for email sources."""

from abc import ABC, abstractmethod


class EmailSource(ABC):
    """Base class for email source implementations."""

    @abstractmethod
    def get_email_text(self, **kwargs) -> str:
        """Fetch email text from the source."""
        pass