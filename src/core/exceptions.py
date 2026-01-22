class UserExistsError(Exception):
    """Raised when attempting to create a user with an existing email."""

    pass


class UserNotFoundError(Exception):
    """Raised when a user is not found."""

    pass


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""

    pass


class AccountLockedError(Exception):
    """Raised when account is locked due to too many failed attempts."""

    pass


class TokenExpiredError(Exception):
    """Raised when a token has expired."""

    pass


class TokenInvalidError(Exception):
    """Raised when a token is invalid."""

    pass


class TokenRevokedError(Exception):
    """Raised when a token has been revoked."""

    pass


class ResetTokenInvalidError(Exception):
    """Raised when a password reset token is invalid, expired, or used."""

    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass
