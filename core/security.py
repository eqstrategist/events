import hashlib
import hmac
import secrets

# Hashed passwords are exactly: 32-byte hex salt + "$" + 64-byte hex SHA256 = 97 chars
_HASHED_PASSWORD_LENGTH = 97

def hash_password(password, salt=None):
    """Hash a password with SHA256 and a salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    salted = f"{salt}{password}"
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password, stored_hash):
    """Verify a password against a stored hash."""
    if not stored_hash or not is_password_hashed(str(stored_hash)):
        # Legacy plaintext password - direct comparison
        return hmac.compare_digest(str(password), str(stored_hash)) if stored_hash else False

    try:
        salt, expected_hash = str(stored_hash).split("$", 1)
        salted = f"{salt}{password}"
        actual_hash = hashlib.sha256(salted.encode()).hexdigest()
        return hmac.compare_digest(actual_hash, expected_hash)
    except ValueError:
        return False

def is_password_hashed(password_value):
    """Check if a password is already hashed (format: 32-char hex salt + '$' + 64-char hex hash)."""
    if not password_value:
        return False
    val = str(password_value)
    if len(val) != _HASHED_PASSWORD_LENGTH:
        return False
    parts = val.split("$", 1)
    if len(parts) != 2:
        return False
    salt, hash_val = parts
    # Salt is 32 hex chars, hash is 64 hex chars
    return len(salt) == 32 and len(hash_val) == 64 and all(c in '0123456789abcdef' for c in salt + hash_val)
