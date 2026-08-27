"""Errors raised by the FPL API package."""


class FPLAPIError(Exception):
    """Base exception for FPL API failures."""


class FPLTransportError(FPLAPIError):
    """Raised when a response cannot be downloaded or decoded."""


class FPLValidationError(FPLAPIError):
    """Raised when an FPL response does not match the expected schema."""

