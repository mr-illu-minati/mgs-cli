"""Typed CLI errors with stable exit codes and JSON serialization."""

from __future__ import annotations


class MgsError(Exception):
    kind = "other"
    exit_code = 1

    def __init__(self, message: str, *, status: int | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.status = status

    def to_json(self) -> dict:
        err: dict = {"kind": self.kind, "message": self.message}
        if self.status is not None:
            err["status"] = self.status
        return {"error": err}


class UsageError(MgsError):
    kind = "usage"
    exit_code = 2


class AuthError(MgsError):
    kind = "auth"
    exit_code = 3


class HttpError(MgsError):
    kind = "http"
    exit_code = 4


class MetadataError(MgsError):
    kind = "metadata"
    exit_code = 5


class ValidationError(MgsError):
    kind = "validation"
    exit_code = 6
