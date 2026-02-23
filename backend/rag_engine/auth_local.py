import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent
USERS_FILE_PATH = PROJECT_ROOT / "local_users.json"
TOKEN_SECRET = os.getenv("LOCAL_AUTH_SECRET", "change-this-local-auth-secret")
TOKEN_TTL_SECONDS = int(os.getenv("LOCAL_AUTH_TTL_SECONDS", "3600"))


def _load_users() -> dict[str, dict[str, str]]:
    if not USERS_FILE_PATH.exists():
        return {}

    with open(USERS_FILE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        return {}

    return data


def _save_users(users: dict[str, dict[str, str]]) -> None:
    with open(USERS_FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=2)


def _hash_password(password: str, salt: str) -> str:
    derived = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        120_000,
    )
    return base64.urlsafe_b64encode(derived).decode("utf-8")


def ensure_default_local_user() -> None:
    users = _load_users()
    if users:
        return

    default_username = os.getenv("LOCAL_AUTH_DEFAULT_USERNAME", "admin")
    default_password = os.getenv("LOCAL_AUTH_DEFAULT_PASSWORD", "admin123")
    salt = secrets.token_hex(16)
    users[default_username] = {
        "salt": salt,
        "password_hash": _hash_password(default_password, salt),
    }
    _save_users(users)


def register_local_user(username: str, password: str) -> tuple[bool, str]:
    normalized_username = (username or "").strip()
    if not normalized_username:
        return False, "Username is required."

    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."

    users = _load_users()
    if normalized_username in users:
        return False, "Username already exists."

    salt = secrets.token_hex(16)
    users[normalized_username] = {
        "salt": salt,
        "password_hash": _hash_password(password, salt),
    }
    _save_users(users)
    return True, "User registered successfully."


def verify_local_login(username: str, password: str) -> bool:
    users = _load_users()
    user = users.get(username)
    if not user:
        return False

    stored_salt = user.get("salt", "")
    stored_hash = user.get("password_hash", "")
    computed_hash = _hash_password(password, stored_salt)
    return hmac.compare_digest(stored_hash, computed_hash)


def _sign_payload(payload_bytes: bytes) -> str:
    signature = hmac.new(TOKEN_SECRET.encode("utf-8"), payload_bytes, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(signature).decode("utf-8")


def create_login_token(username: str) -> str:
    payload = {
        "sub": username,
        "iat": int(time.time()),
        "exp": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    payload_json = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    payload_encoded = base64.urlsafe_b64encode(payload_json).decode("utf-8")
    signature_encoded = _sign_payload(payload_json)
    return f"{payload_encoded}.{signature_encoded}"


def verify_login_token(token: str) -> dict[str, str | int] | None:
    try:
        payload_encoded, signature_encoded = token.split(".", 1)
    except ValueError:
        return None

    try:
        payload_bytes = base64.urlsafe_b64decode(payload_encoded.encode("utf-8"))
    except Exception:
        return None

    expected_signature = _sign_payload(payload_bytes)
    if not hmac.compare_digest(expected_signature, signature_encoded):
        return None

    try:
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        return None

    exp = payload.get("exp")
    if not isinstance(exp, int) or exp < int(time.time()):
        return None

    return payload
