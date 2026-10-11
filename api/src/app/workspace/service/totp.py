import base64
import hashlib
import hmac
import struct


def totp_code(secret: str, step: int, digits: int = 6) -> str:
    key = base64.b32decode(secret.upper(), casefold=True)
    digest = hmac.new(key, struct.pack(">Q", step), hashlib.sha1).digest()
    offset = digest[-1] & 15
    number = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    return str(number % (10**digits)).zfill(digits)


def verify_totp(secret: str, code: str, timestamp: int, last_step: int | None) -> int | None:
    current = timestamp // 30
    for step in (current, current - 1, current + 1):
        if step >= 0 and (last_step is None or step > last_step):
            if hmac.compare_digest(totp_code(secret, step), code):
                return step
    return None
