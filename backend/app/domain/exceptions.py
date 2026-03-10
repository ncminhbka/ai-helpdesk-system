"""Domain-level exceptions — no framework dependencies."""


class DomainError(Exception):
    """Base class for all domain exceptions."""


class TicketNotFoundError(DomainError):
    pass


class InvalidTicketStatusError(DomainError):
    pass


class BookingNotFoundError(DomainError):
    pass


class InvalidBookingStatusError(DomainError):
    pass


class UserNotFoundError(DomainError):
    pass


class EmailAlreadyExistsError(DomainError):
    pass
