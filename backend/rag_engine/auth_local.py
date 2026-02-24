# ==============================================================================
# LOCAL AUTHENTICATION MODULE
# ==============================================================================
# Purpose: Provide user authentication WITHOUT external database dependency
# Security: PBKDF2 password hashing + HMAC token signing
# Storage: local_users.json file with {username: {salt, password_hash}}
# ==============================================================================

import base64  # Encode/decode binary data to/from base64 strings
import hashlib  # Cryptographic hashing (SHA256, PBKDF2)
import hmac  # HMAC signature for token verification
import json  # Read/write JSON files
import os  # Environment variables
import secrets  # Cryptographically secure random generation
import time  # Unix timestamps for token expiration
from pathlib import Path  # File path operations


# ==============================================================================
# CONFIGURATION: Paths and secrets
# ==============================================================================

# Resolve project root directory (parent of rag_engine/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Path to JSON file storing user credentials
# Format: {"username": {"salt": "hex", "password_hash": "base64"}}
USERS_FILE_PATH = PROJECT_ROOT / "local_users.json"

# Secret key for HMAC token signing
# CRITICAL: Change in production via environment variable
# Used to sign tokens so they can't be tampered with
TOKEN_SECRET = os.getenv("LOCAL_AUTH_SECRET", "change-this-local-auth-secret")

# Token time-to-live in seconds (default: 1 hour)
# After this time, tokens expire and user must login again
TOKEN_TTL_SECONDS = int(os.getenv("LOCAL_AUTH_TTL_SECONDS", "3600"))


# ==============================================================================
# INTERNAL FUNCTION: Load users from JSON file
# ==============================================================================
def _load_users() -> dict[str, dict[str, str]]:
    """
    Load user credentials from local_users.json file.
    
    Returns:
        Dictionary mapping username -> {salt, password_hash}
        Empty dict if file doesn't exist or is corrupted
        
    Format:
        {
          "admin": {
            "salt": "hex_encoded_16_bytes",
            "password_hash": "base64_encoded_pbkdf2_hash"
          }
        }
    """
    # If file doesn't exist yet (first run), return empty dict
    if not USERS_FILE_PATH.exists():
        return {}

    # Read and parse JSON file
    with open(USERS_FILE_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    # Validate data is a dictionary (not array, null, etc.)
    if not isinstance(data, dict):
        return {}  # Corrupted file, return empty

    return data


# ==============================================================================
# INTERNAL FUNCTION: Save users to JSON file
# ==============================================================================
def _save_users(users: dict[str, dict[str, str]]) -> None:
    """
    Save user credentials to local_users.json file.
    
    Args:
        users: Dictionary mapping username -> {salt, password_hash}
        
    Security:
        - Passwords are NEVER stored plaintext
        - Only salt (random) and hash (one-way) are stored
        - File should have restrictive permissions in production
    """
    # Write to file with UTF-8 encoding and pretty-print (indent=2)
    # ensure_ascii=False allows Unicode characters in usernames
    with open(USERS_FILE_PATH, "w", encoding="utf-8") as file:
        json.dump(users, file, ensure_ascii=False, indent=2)


# ==============================================================================
# INTERNAL FUNCTION: Hash password using PBKDF2
# ==============================================================================
def _hash_password(password: str, salt: str) -> str:
    """
    Hash password using PBKDF2-HMAC-SHA256 with 120,000 iterations.
    
    Args:
        password: User's password (plaintext)
        salt: Random salt (hex string) for this user
        
    Returns:
        Base64-encoded hash string
        
    Security:
        - PBKDF2: Password-Based Key Derivation Function 2
        - HMAC-SHA256: Hash-based Message Authentication Code
        - 120,000 iterations: Slow enough to resist brute force
        - Unique salt per user: Prevents rainbow table attacks
        
    Why 120,000 iterations?
        - OWASP recommendation (as of 2023)
        - Takes ~100ms to compute (acceptable for login)
        - Makes brute force attacks very expensive
    """
    # Derive key using PBKDF2
    derived = hashlib.pbkdf2_hmac(
        "sha256",  # Hash algorithm: SHA-256
        password.encode("utf-8"),  # Password as bytes
        salt.encode("utf-8"),  # Salt as bytes
        120_000,  # Iteration count (underscore for readability)
    )
    # Encode binary hash to base64 string for JSON storage
    return base64.urlsafe_b64encode(derived).decode("utf-8")


# ==============================================================================
# PUBLIC FUNCTION: Ensure default user exists
# ==============================================================================
def ensure_default_local_user() -> None:
    """
    Create default admin user if no users exist (first run).
    
    Default Credentials:
        Username: admin (or LOCAL_AUTH_DEFAULT_USERNAME env var)
        Password: admin123 (or LOCAL_AUTH_DEFAULT_PASSWORD env var)
        
    Purpose:
        Allows system to be usable immediately after setup
        without requiring manual user creation
        
    Security Note:
        In production, change default password immediately!
        Set environment variables to override defaults
    """
    # Load existing users
    users = _load_users()
    
    # If any users exist, nothing to do
    if users:
        return

    # No users exist: create default admin
    # Read credentials from env vars or use defaults
    default_username = os.getenv("LOCAL_AUTH_DEFAULT_USERNAME", "admin")
    default_password = os.getenv("LOCAL_AUTH_DEFAULT_PASSWORD", "admin123")
    
    # Generate random 16-byte salt (32 hex characters)
    # secrets.token_hex() is cryptographically secure
    salt = secrets.token_hex(16)
    
    # Create user entry with salt and hashed password
    users[default_username] = {
        "salt": salt,
        "password_hash": _hash_password(default_password, salt),
    }
    
    # Save to file
    _save_users(users)


# ==============================================================================
# PUBLIC FUNCTION: Register new user
# ==============================================================================
def register_local_user(username: str, password: str) -> tuple[bool, str]:
    """
    Register a new user with username and password.
    
    Args:
        username: Desired username
        password: Desired password
        
    Returns:
        (success: bool, message: str)
        - (True, "User registered successfully.") on success
        - (False, "error message") on failure
        
    Validation:
        - Username must not be empty (after stripping)
        - Password must be at least 6 characters
        - Username must not already exist
        
    Security:
        - Password is immediately hashed (never stored plaintext)
        - Unique salt generated per user
        - 120,000 PBKDF2 iterations
    """
    # Normalize username: strip leading/trailing whitespace
    normalized_username = (username or "").strip()
    
    # Validate username not empty
    if not normalized_username:
        return False, "Username is required."

    # Validate password length (minimum 6 characters)
    if len(password or "") < 6:
        return False, "Password must be at least 6 characters."

    # Load existing users
    users = _load_users()
    
    # Check if username already taken
    if normalized_username in users:
        return False, "Username already exists."

    # Generate cryptographically secure random salt (16 bytes = 32 hex chars)
    salt = secrets.token_hex(16)
    
    # Create user entry with salt and hashed password
    users[normalized_username] = {
        "salt": salt,  # Store salt for this user
        "password_hash": _hash_password(password, salt),  # Store hashed password
    }
    
    # Persist to file
    _save_users(users)
    
    # Return success
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
