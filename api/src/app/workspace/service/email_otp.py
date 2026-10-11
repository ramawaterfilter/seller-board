from typing import Protocol

from app.errors import AppError


class EmailSender(Protocol):
    async def send(self, recipient: str, code: str) -> None: ...


class NullEmailSender:
    async def send(self, recipient: str, code: str) -> None:
        raise AppError(503, "OTP_DELIVERY_UNAVAILABLE", "Email code delivery is not configured.")
