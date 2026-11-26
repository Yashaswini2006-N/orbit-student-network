import hashlib
import json
import tempfile
from pathlib import Path

import accounts
import network
import storage


def make_empty_state():
    return {}, {"accepted": {}, "pending": []}, {}


def test_password_hashing_salted_and_pbkdf2_600k():
    hash1 = accounts.hash_password("SecurePass123")
    hash2 = accounts.hash_password("SecurePass123")

    assert hash1 != "SecurePass123", "Plain-text password must never be stored"
    assert hash1 != hash2, "Same password must produce different hashes due to unique random salt"
    assert "$" in hash1, "Stored hash should follow 'salt$hash' format"

    salt, expected_hex = hash1.split("$", 1)
    recomputed = hashlib.pbkdf2_hmac(
        "sha256",
        b"SecurePass123",
        salt.encode("utf-8"),
        600_000,
    ).hex()
    assert expected_hex == recomputed, "Hash must use PBKDF2-HMAC-SHA256 with 600,000 iterations"

    assert accounts.verify_password("SecurePass123", hash1) is True
    assert accounts.verify_password("WrongPass123", hash1) is False
    assert accounts.verify_password("SecurePass123", "malformed-hash") is False
    assert accounts.verify_password("SecurePass123", "$missing_salt") is False
    assert accounts.verify_password(None, hash1) is False


def test_register_student_and_isolated_graph_vertex():
    students, connections, _ = make_empty_state()

    ok, msg = accounts.register_student(
        students,
        connections,
        "Yashaswini N",
        "StrongPass1",
        "Yashaswini N",
        email="yashaswini@college.edu",
        department="CSE",
        year=2,
        skills=["Python", "DSA"],
        bio="DSA enthusiast",
    )

    assert ok is True, f"Registration failed: {msg}"
    assert msg == "Account registered successfully."
    assert "Yashaswini N" in students
    record = students["Yashaswini N"]
    assert record["password_hash"] != "StrongPass1"
    assert accounts.verify_password("StrongPass1", record["password_hash"]) is True
    assert "Yashaswini N" in connections["accepted"]
    assert connections["accepted"]["Yashaswini N"] == [], (
        "Newly registered student must start with an empty adjacency list"
    )

    # Ensure everything stored is JSON-serializable
    json.dumps(students)
    json.dumps(connections)


def test_network_integration_with_registered_students():
    students, connections, _ = make_empty_state()

    ok1, _ = accounts.register_student(students, connections, "Yashaswini N", "Password123", "Yashaswini N")
    ok2, _ = accounts.register_student(students, connections, "Rachana C Madure", "Password456", "Rachana C Madure")
    ok3, _ = accounts.register_student(students, connections, "Anshuman Roy", "Password789", "Anshuman Roy")
    assert ok1 and ok2 and ok3

    assert network.send_request(connections, "Yashaswini N", "Rachana C Madure") == "Connection request sent."
    assert network.accept_request(connections, "Yashaswini N", "Rachana C Madure") == "Connection accepted."
    assert network.send_request(connections, "Rachana C Madure", "Anshuman Roy") == "Connection request sent."
    assert network.accept_request(connections, "Rachana C Madure", "Anshuman Roy") == "Connection accepted."

    assert network.view_connections(connections, "Yashaswini N") == ["Rachana C Madure"]
    assert network.shortest_path(connections, "Yashaswini N", "Anshuman Roy") == [
        "Yashaswini N",
        "Rachana C Madure",
        "Anshuman Roy",
    ]


def test_unique_username_case_insensitive():
    students, connections, _ = make_empty_state()

    ok, _ = accounts.register_student(students, connections, "Rachana C Madure", "Password123", "Rachana C Madure")
    assert ok is True

    ok_exact, msg_exact = accounts.register_student(
        students, connections, "Rachana C Madure", "AnotherPass1", "Rachana Duplicate"
    )
    assert ok_exact is False and msg_exact == "Username already exists."

    ok_case, msg_case = accounts.register_student(
        students, connections, "rachana c madure", "AnotherPass1", "Rachana Lowercase"
    )
    assert ok_case is False and msg_case == "Username already exists."
    assert len(students) == 1, "Duplicate registration must not create a second user"
    assert students["Rachana C Madure"]["full_name"] == "Rachana C Madure", (
        "Original student record must not be overwritten"
    )


def test_registration_validation_rules():
    students, connections, _ = make_empty_state()

    cases = [
        ("", "ValidPass1", "Name", "ok@college.edu"),
        ("ab", "ValidPass1", "Name", "ok@college.edu"),
        ("bad$user", "ValidPass1", "Name", "ok@college.edu"),
        ("ValidUser", "", "Name", "ok@college.edu"),
        ("ValidUser", "       ", "Name", "ok@college.edu"),
        ("ValidUser", "1234567", "Name", "ok@college.edu"),  # 7 chars (< 8)
        ("ValidUser", "ValidPass1", "   ", "ok@college.edu"),
        ("ValidUser", "ValidPass1", "Name", "not-an-email"),
        ("ValidUser", "ValidPass1", "Name", "user@nodot"),
    ]

    for uname, pwd, fname, email in cases:
        ok, msg = accounts.register_student(students, connections, uname, pwd, fname, email=email)
        assert ok is False, f"Expected failure for ({uname!r}, len={len(pwd)}, {fname!r}, {email!r}), got ok=True"
        assert isinstance(msg, str) and len(msg) > 0

    assert students == {}, "Invalid registrations must not add users"
    assert connections["accepted"] == {}, "Invalid registrations must not add graph vertices"


def test_login_logout_and_failed_login_preserves_session():
    students, connections, session = make_empty_state()
    accounts.register_student(students, connections, "Anshuman Roy", "MySecret99", "Anshuman Roy")
    accounts.register_student(students, connections, "Giridhar N", "OtherPass99", "Giridhar N")

    assert accounts.get_current_user(session) is None

    # Successful login (including case-insensitive username lookup -> canonical username stored)
    ok, msg = accounts.login_student(students, "anshuman roy", "MySecret99", session)
    assert ok is True and msg == "Login successful."
    assert accounts.get_current_user(session) == "Anshuman Roy"

    # Failed login with wrong password must NOT alter existing session
    ok_bad_pw, msg_bad_pw = accounts.login_student(students, "Giridhar N", "WrongPassword", session)
    assert ok_bad_pw is False and msg_bad_pw == "Invalid username or password."
    assert accounts.get_current_user(session) == "Anshuman Roy", (
        "Failed login must not overwrite the existing logged-in session"
    )

    # Failed login with unknown user must NOT alter existing session
    ok_missing, _ = accounts.login_student(students, "NoSuchUser", "MySecret99", session)
    assert ok_missing is False
    assert accounts.get_current_user(session) == "Anshuman Roy"

    # Logout clears session
    ok_out, msg_out = accounts.logout_student(session)
    assert ok_out is True and msg_out == "Logged out successfully."
    assert accounts.get_current_user(session) is None

    # Logging out again when nobody is logged in
    ok_out2, msg_out2 = accounts.logout_student(session)
    assert ok_out2 is False and msg_out2 == "No user is currently logged in."


def test_view_profile_hides_password_hash():
    students, connections, _ = make_empty_state()
    accounts.register_student(
        students,
        connections,
        "Jeevan Yogesh Ghandasi",
        "PassWord123",
        "Jeevan Yogesh Ghandasi",
        department="ISE",
        skills=["C++", "Python"],
    )

    profile = accounts.view_profile(students, "Jeevan Yogesh Ghandasi")
    assert profile is not None
    assert "password_hash" not in profile, "view_profile must never expose password_hash"
    assert profile["full_name"] == "Jeevan Yogesh Ghandasi"
    assert profile["department"] == "ISE"

    # Mutating returned copy should not mutate stored record
    profile["skills"].append("Hacked")
    assert students["Jeevan Yogesh Ghandasi"]["skills"] == ["C++", "Python"]

    assert accounts.view_profile(students, "NonExistent") is None


def test_update_profile_and_immutable_fields():
    students, connections, _ = make_empty_state()
    accounts.register_student(
        students,
        connections,
        "Yashaswini N",
        "StrongPass1",
        "Yashaswini N",
        email="old@college.edu",
        department="CSE",
        year=2,
        skills=["Python"],
        bio="Old bio",
    )
    original_hash = students["Yashaswini N"]["password_hash"]
    original_created_at = students["Yashaswini N"]["created_at"]

    # Valid update
    ok, msg = accounts.update_profile(
        students,
        "Yashaswini N",
        full_name="Yashaswini Narayanan",
        email="new@college.edu",
        department="AI & ML",
        year=3,
        skills="Python, Graphs, Streamlit",
        bio="Updated bio",
    )
    assert ok is True and msg == "Profile updated successfully."

    updated = students["Yashaswini N"]
    assert updated["full_name"] == "Yashaswini Narayanan"
    assert updated["email"] == "new@college.edu"
    assert updated["department"] == "AI & ML"
    assert updated["year"] == 3
    assert updated["skills"] == ["Python", "Graphs", "Streamlit"]
    assert updated["bio"] == "Updated bio"

    # Immutable fields must remain unchanged
    assert updated["username"] == "Yashaswini N"
    assert updated["password_hash"] == original_hash
    assert updated["created_at"] == original_created_at

    # Invalid update must fail atomically without partial changes
    ok_bad, _ = accounts.update_profile(
        students,
        "Yashaswini N",
        bio="Should not save",
        email="bad-email",
    )
    assert ok_bad is False
    assert students["Yashaswini N"]["bio"] == "Updated bio", (
        "Failed update_profile must not partially mutate fields"
    )

    # Unknown user
    ok_missing, msg_missing = accounts.update_profile(students, "Nobody", bio="Hi")
    assert ok_missing is False and msg_missing == "Student not found."


def test_accounts_storage_roundtrip():
    original_folder = storage.DATA_FOLDER
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage.DATA_FOLDER = Path(tmp_dir) / "data"
        try:
            students, connections, posts, notifications = storage.load_all_data()
            ok, _ = accounts.register_student(
                students,
                connections,
                "Rachana C Madure",
                "StoragePass1",
                "Rachana C Madure",
                skills=["Python", "BFS"],
            )
            assert ok is True

            storage.save_all_data(students, connections, posts, notifications)
            reloaded_students, reloaded_connections, _, _ = storage.load_all_data()

            session = {}
            login_ok, _ = accounts.login_student(
                reloaded_students, "Rachana C Madure", "StoragePass1", session
            )
            assert login_ok is True
            assert accounts.get_current_user(session) == "Rachana C Madure"
            assert reloaded_connections["accepted"]["Rachana C Madure"] == []
        finally:
            storage.DATA_FOLDER = original_folder


def run_all_tests():
    tests = [
        test_password_hashing_salted_and_pbkdf2_600k,
        test_register_student_and_isolated_graph_vertex,
        test_network_integration_with_registered_students,
        test_unique_username_case_insensitive,
        test_registration_validation_rules,
        test_login_logout_and_failed_login_preserves_session,
        test_view_profile_hides_password_hash,
        test_update_profile_and_immutable_fields,
        test_accounts_storage_roundtrip,
    ]

    passed = 0
    failed = 0

    for test_fn in tests:
        try:
            test_fn()
            print(f"PASS: {test_fn.__name__}")
            passed += 1
        except AssertionError as err:
            print(f"FAIL: {test_fn.__name__} -> {err}")
            failed += 1
        except Exception as exc:
            print(f"ERROR: {test_fn.__name__} -> {type(exc).__name__}: {exc}")
            failed += 1

    print(f"\nSummary: {passed} passed, {failed} failed out of {len(tests)} tests.")
    if failed > 0:
        raise SystemExit(1)


if __name__ == "__main__":
    run_all_tests()
