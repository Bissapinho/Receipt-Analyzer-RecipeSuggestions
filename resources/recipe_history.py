from dataclasses import dataclass
from datetime import datetime


@dataclass
class RecipeRecord:
    """
    A single recipe history record.
    """
    name: str
    status: str          # "viewed", "accepted", "rejected"
    timestamp: datetime


class RecipeHistory:
    """
    Stores user's recipe interaction history.
    """

    def __init__(self):
        self.records = []

    def add(self, name: str, status: str = "viewed"):
        """
        Add a record to history.
        """
        record = RecipeRecord(
            name=name,
            status=status,
            timestamp=datetime.now()
        )
        self.records.append(record)

    def list(self):
        """
        Return all history records.
        """
        return self.records

    def list_by_status(self, status: str):
        """
        Filter records by status.
        """
        return [r for r in self.records if r.status == status]

    def last(self):
        """
        Get the most recent history record.
        """
        return self.records[-1] if self.records else None