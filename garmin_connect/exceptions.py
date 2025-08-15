from garth.exc import GarthException, GarthHTTPError

__all__ = [
    "GarminConnectConnectionError",
    "GarminConnectTooManyRequestsError",
    "GarminConnectAuthenticationError",
    "GarminConnectInvalidFileFormatError",
    "GarthHTTPError",
    "GarthException",
]


class GarminConnectConnectionError(Exception):
    """Raised when communication ended in error."""


class GarminConnectTooManyRequestsError(Exception):
    """Raised when rate limit is exceeded."""


class GarminConnectAuthenticationError(Exception):
    """Raised when authentication is failed."""


class GarminConnectInvalidFileFormatError(Exception):
    """Raised when an invalid file format is passed to upload."""
