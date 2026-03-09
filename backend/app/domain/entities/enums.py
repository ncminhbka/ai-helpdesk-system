"""
Pure Python business enums for the domain layer.
These enums represent domain vocabulary and have no framework dependencies.
"""
import enum


class TicketStatus(str, enum.Enum):
    PENDING = "Pending"
    RESOLVING = "Resolving"
    CANCELED = "Canceled"
    FINISHED = "Finished"


class BookingStatus(str, enum.Enum):
    SCHEDULED = "Scheduled"
    CANCELED = "Canceled"
    FINISHED = "Finished"
