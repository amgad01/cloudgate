from passlib.context import CryptContext
from passlib.exc import MissingBackendError

# context: prefer argon2 then bcrypt. If argon2 backend is missing
# a runtime MissingBackendError will be handled and a bcrypt-only context will be used as a fallback.
_PRIMARY_CTX = CryptContext(
    schemes=["pbkdf2_sha256"],
    deprecated="auto",
)


def _pbkdf2_only_ctx() -> CryptContext:
    return CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def _truncate_for_bcrypt(value: str) -> str:
    b = value.encode()
    if len(b) > 72:
        return b[:72].decode(errors="ignore")
    return value


def hash_password(password: str) -> str:
    pw = _truncate_for_bcrypt(password)
    try:
        return _PRIMARY_CTX.hash(pw)
    except MissingBackendError:
        # Fall back to pure-Python pbkdf2
        return _pbkdf2_only_ctx().hash(pw)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    pw = _truncate_for_bcrypt(plain_password)
    try:
        return _PRIMARY_CTX.verify(pw, hashed_password)
    except MissingBackendError:
        return _pbkdf2_only_ctx().verify(pw, hashed_password)
