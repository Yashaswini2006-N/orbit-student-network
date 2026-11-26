import hashlib
import hmac
import secrets
from datetime import datetime

PBKDF2_ITERATIONS = 600_000
MIN_USERNAME_LENGTH = 3
MIN_PASSWORD_LENGTH = 8


def hash_password(password):
    """Hash a password using PBKDF2-HMAC-SHA256 (600,000 iterations) and a random salt."""
    if not isinstance(password, str):
        raise TypeError("Password must be a string.")

    salt = secrets.token_hex(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    )
    return f"{salt}${derived_key.hex()}"


def verify_password(password, stored_hash):
    """Verify a plain-text password against a stored 'salt$hash' string."""
    if not isinstance(password, str) or not isinstance(stored_hash, str):
        return False

    if "$" not in stored_hash:
        return False

    salt, expected_hex = stored_hash.split("$", 1)
    if not salt or not expected_hex:
        return False

    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()

    return hmac.compare_digest(computed, expected_hex)


def _is_valid_email(email):
    """Basic format check for an optional student email address."""
    if " " in email or email.count("@") != 1:
        return False
    local, domain = email.split("@", 1)
    if not local or not domain or "." not in domain:
        return False
    if domain.startswith(".") or domain.endswith("."):
        return False
    return True


def _normalize_skills(skills):
    """Normalize skills into a JSON-compatible list of non-empty strings."""
    if skills is None:
        return []
    if isinstance(skills, str):
        return [item.strip() for item in skills.split(",") if item.strip()]
    if isinstance(skills, (list, tuple)):
        return [str(item).strip() for item in skills if str(item).strip()]
    return None


def _find_canonical_username(students, username):
    """Return the stored username matching case-insensitively, or None."""
    target = username.lower()
    for existing in students:
        if existing.lower() == target:
            return existing
    return None


def register_student(
    students,
    connections,
    username,
    password,
    full_name,
    email="",
    department="",
    year="",
    skills=None,
    bio="",
):
    """Register a new student account and add them as an isolated graph vertex."""
    if not isinstance(username, str):
        return False, "Username must be a string."

    clean_username = username.strip()
    if len(clean_username) < MIN_USERNAME_LENGTH:
        return False, f"Username must be at least {MIN_USERNAME_LENGTH} characters long."

    if not all(ch.isalnum() or ch in " ._-" for ch in clean_username):
        return False, "Username contains unsupported characters."

    if _find_canonical_username(students, clean_username) is not None:
        return False, "Username already exists."

    if not isinstance(password, str) or not password.strip():
        return False, "Password cannot be empty."

    if len(password) < MIN_PASSWORD_LENGTH:
        return False, f"Password must be at least {MIN_PASSWORD_LENGTH} characters long."

    if not isinstance(full_name, str) or not full_name.strip():
        return False, "Full name cannot be empty."

    if not isinstance(email, str):
        return False, "Email must be a string."
    clean_email = email.strip()
    if clean_email and not _is_valid_email(clean_email):
        return False, "Please enter a valid email address."

    normalized_skills = _normalize_skills(skills)
    if normalized_skills is None:
        return False, "Skills must be a list or comma-separated string."

    if isinstance(year, bool) or (not isinstance(year, (int, str))):
        return False, "Year must be a number or text."
    clean_year = year if isinstance(year, int) else year.strip()

    students[clean_username] = {
        "username": clean_username,
        "full_name": full_name.strip(),
        "password_hash": hash_password(password),
        "email": clean_email,
        "department": str(department).strip() if department is not None else "",
        "year": clean_year,
        "skills": normalized_skills,
        "bio": str(bio).strip() if bio is not None else "",
        "created_at": datetime.now().isoformat(),
    }

    # Add newly registered student to connections["accepted"] as an isolated vertex
    connections.setdefault("accepted", {})
    connections.setdefault("pending", [])
    connections["accepted"].setdefault(clean_username, [])

    return True, "Account registered successfully."


def login_student(students, username, password, session=None):
    """Authenticate a student and store the logged-in user in session on success."""
    if not isinstance(username, str) or not isinstance(password, str):
        return False, "Invalid username or password."

    clean_username = username.strip()
    if not clean_username or not password:
        return False, "Username and password are required."

    canonical_username = _find_canonical_username(students, clean_username)
    if canonical_username is None:
        return False, "Invalid username or password."

    student = students[canonical_username]
    if not verify_password(password, student.get("password_hash", "")):
        return False, "Invalid username or password."

    if session is not None:
        session["logged_in_user"] = canonical_username

    return True, "Login successful."


def logout_student(session):
    """Clear the current logged-in user from the session dictionary."""
    if session is None:
        return False, "No active session."

    current_user = session.get("logged_in_user")
    session["logged_in_user"] = None

    if not current_user:
        return False, "No user is currently logged in."

    return True, "Logged out successfully."


def get_current_user(session):
    """Return the currently logged-in username from session, or None."""
    if session is None:
        return None
    return session.get("logged_in_user")


def view_profile(students, username):
    """Return a safe copy of a student's profile without password_hash."""
    if not isinstance(username, str) or username not in students:
        return None

    record = students[username]
    profile = {
        key: value
        for key, value in record.items()
        if key != "password_hash"
    }
    if "skills" in profile and isinstance(profile["skills"], list):
        profile["skills"] = list(profile["skills"])

    return profile


def update_profile(
    students,
    username,
    full_name=None,
    email=None,
    department=None,
    year=None,
    skills=None,
    bio=None,
):
    """Update editable profile fields without modifying username, password_hash, or created_at."""
    if not isinstance(username, str) or username not in students:
        return False, "Student not found."

    updates = {}

    if full_name is not None:
        if not isinstance(full_name, str) or not full_name.strip():
            return False, "Full name cannot be empty."
        updates["full_name"] = full_name.strip()

    if email is not None:
        if not isinstance(email, str):
            return False, "Email must be a string."
        clean_email = email.strip()
        if clean_email and not _is_valid_email(clean_email):
            return False, "Please enter a valid email address."
        updates["email"] = clean_email

    if department is not None:
        if not isinstance(department, str):
            return False, "Department must be a string."
        updates["department"] = department.strip()

    if year is not None:
        if isinstance(year, bool) or not isinstance(year, (int, str)):
            return False, "Year must be a number or text."
        updates["year"] = year if isinstance(year, int) else year.strip()

    if skills is not None:
        normalized_skills = _normalize_skills(skills)
        if normalized_skills is None:
            return False, "Skills must be a list or comma-separated string."
        updates["skills"] = normalized_skills

    if bio is not None:
        if not isinstance(bio, str):
            return False, "Bio must be a string."
        updates["bio"] = bio.strip()

    students[username].update(updates)
    return True, "Profile updated successfully."
