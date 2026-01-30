import hashlib
import secrets

def hash_password(password, salt=None):
    """Hash a password with SHA256 and a salt."""
    if salt is None:
        salt = secrets.token_hex(16)
    salted = f"{salt}{password}"
    hashed = hashlib.sha256(salted.encode()).hexdigest()
    return f"{salt}${hashed}"

def verify_password(password, stored_hash):
    """Verify a password against a stored hash."""
    if not stored_hash or "$" not in stored_hash:
        # Legacy plaintext password - direct comparison
        return password == stored_hash

    try:
        salt, expected_hash = stored_hash.split("$", 1)
        salted = f"{salt}{password}"
        actual_hash = hashlib.sha256(salted.encode()).hexdigest()
        return actual_hash == expected_hash
    except ValueError:
        # Fallback for legacy plaintext
        return password == stored_hash

def is_password_hashed(password_value):
    """Check if a password is already hashed (contains salt separator)."""
    return password_value and "$" in password_value and len(password_value) > 50
