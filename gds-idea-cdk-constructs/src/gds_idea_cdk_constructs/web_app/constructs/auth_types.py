from enum import StrEnum


class AuthType(StrEnum):
    """Defines the supported authentication types for the WebApp construct."""

    NONE = "none"
    COGNITO = "cognito"
