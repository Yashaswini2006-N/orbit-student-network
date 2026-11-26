import json
import os
import tempfile
from pathlib import Path

import storage


def with_temp_data_folder(fn):
    """Run a test function with storage.DATA_FOLDER pointed to a temporary directory."""
    original_folder = storage.DATA_FOLDER
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage.DATA_FOLDER = Path(tmp_dir) / "data"
        try:
            fn(storage.DATA_FOLDER)
        finally:
            storage.DATA_FOLDER = original_folder


def test_path_is_anchored_to_storage_file():
    expected = Path(storage.__file__).resolve().parent / "data"
    assert storage.DATA_FOLDER == expected, (
        f"Expected DATA_FOLDER {expected}, got {storage.DATA_FOLDER}"
    )

    # Confirm DATA_FOLDER remains independent of current working directory
    original_cwd = Path.cwd()
    with tempfile.TemporaryDirectory() as other_dir:
        try:
            os.chdir(other_dir)
            students, connections, posts, notifications = storage.load_all_data()
            assert isinstance(students, dict)
            assert "accepted" in connections and "pending" in connections
            assert isinstance(posts, list)
            assert isinstance(notifications, dict)
        finally:
            os.chdir(original_cwd)


def test_load_existing_json_data():
    def run(data_dir):
        data_dir.mkdir(parents=True, exist_ok=True)
        sample_students = {"yashaswini": {"name": "Yashaswini N", "branch": "CSE"}}
        (data_dir / "students.json").write_text(
            json.dumps(sample_students), encoding="utf-8"
        )

        loaded = storage.load_data("students.json")
        assert loaded == sample_students, f"Expected {sample_students}, got {loaded}"

    with_temp_data_folder(run)


def test_save_and_load_roundtrip_utf8():
    def run(_data_dir):
        sample_posts = [
            {
                "post_id": 1,
                "username": "Rachana C Madure",
                "text": "DSA Graph project 🚀 — café notes",
                "image_path": None,
                "likes": ["Yashaswini N"],
                "comments": [],
                "created_at": "2026-11-24T12:00:00",
            }
        ]
        storage.save_data("posts.json", sample_posts)
        loaded = storage.load_data("posts.json")
        assert loaded == sample_posts, "Loaded JSON data did not match saved data"

    with_temp_data_folder(run)


def test_missing_files_return_defaults():
    def run(_data_dir):
        students = storage.load_data("students.json")
        connections = storage.load_data("connections.json")
        posts = storage.load_data("posts.json")
        notifications = storage.load_data("notifications.json")

        assert students == {}, f"Expected {{}}, got {students}"
        assert connections == {"accepted": {}, "pending": []}, (
            f"Expected empty network structure, got {connections}"
        )
        assert posts == [], f"Expected [], got {posts}"
        assert notifications == {}, f"Expected {{}}, got {notifications}"

        # Ensure returned defaults are fresh copies (not shared references)
        connections["accepted"]["Alice"] = ["Bob"]
        connections["pending"].append({"sender": "A", "receiver": "B"})
        fresh_connections = storage.load_data("connections.json")
        assert fresh_connections == {"accepted": {}, "pending": []}, (
            "Mutating a returned default must not affect future loads"
        )

    with_temp_data_folder(run)


def test_empty_files_return_defaults():
    def run(data_dir):
        data_dir.mkdir(parents=True, exist_ok=True)
        (data_dir / "students.json").write_text("", encoding="utf-8")
        (data_dir / "connections.json").write_text("   \n\t ", encoding="utf-8")
        (data_dir / "posts.json").write_text("", encoding="utf-8")
        (data_dir / "notifications.json").write_text("\n", encoding="utf-8")

        assert storage.load_data("students.json") == {}
        assert storage.load_data("connections.json") == {"accepted": {}, "pending": []}
        assert storage.load_data("posts.json") == []
        assert storage.load_data("notifications.json") == {}

    with_temp_data_folder(run)


def test_malformed_json_raises_clear_error_without_overwriting():
    def run(data_dir):
        data_dir.mkdir(parents=True, exist_ok=True)
        corrupted_path = data_dir / "posts.json"
        corrupted_content = "{ this is not valid json: [1, 2,"
        corrupted_path.write_text(corrupted_content, encoding="utf-8")

        raised = False
        try:
            storage.load_data("posts.json")
        except ValueError as err:
            raised = True
            message = str(err)
            assert "Malformed JSON" in message, f"Expected clear error message, got: {message}"
            assert "posts.json" in message, f"Error message should mention filename: {message}"

        assert raised, "Malformed JSON should raise ValueError instead of failing silently"
        assert corrupted_path.read_text(encoding="utf-8") == corrupted_content, (
            "Corrupted JSON file must NOT be overwritten or cleared"
        )

    with_temp_data_folder(run)


def test_save_creates_missing_data_directory():
    def run(data_dir):
        assert not data_dir.exists(), "Test expects data_dir not to exist yet"
        storage.save_data("students.json", {"Anshuman Roy": {"year": 2}})
        assert data_dir.exists(), "save_data should create missing data directory"
        assert (data_dir / "students.json").exists(), "Saved file should exist"
        assert storage.load_data("students.json") == {"Anshuman Roy": {"year": 2}}

    with_temp_data_folder(run)


def test_save_all_and_load_all_data():
    def run(_data_dir):
        students = {"Yashaswini N": {"branch": "CSE"}, "Rachana C Madure": {"branch": "CSE"}}
        connections = {
            "accepted": {"Yashaswini N": ["Rachana C Madure"], "Rachana C Madure": ["Yashaswini N"]},
            "pending": [{"sender": "Anshuman Roy", "receiver": "Yashaswini N"}],
        }
        posts = [{"post_id": 1, "username": "Yashaswini N", "text": "Hello", "image_path": None, "likes": [], "comments": [], "created_at": "2026-11-24T12:00:00"}]
        notifications = {"Yashaswini N": [{"message": "Welcome!", "created_at": "2026-11-24T12:00:00", "read": False}]}

        storage.save_all_data(students, connections, posts, notifications)
        loaded = storage.load_all_data()

        assert isinstance(loaded, tuple) and len(loaded) == 4, (
            "load_all_data must return a 4-tuple"
        )
        loaded_students, loaded_connections, loaded_posts, loaded_notifications = loaded
        assert loaded_students == students
        assert loaded_connections == connections
        assert loaded_posts == posts
        assert loaded_notifications == notifications

    with_temp_data_folder(run)


def run_all_tests():
    tests = [
        test_path_is_anchored_to_storage_file,
        test_load_existing_json_data,
        test_save_and_load_roundtrip_utf8,
        test_missing_files_return_defaults,
        test_empty_files_return_defaults,
        test_malformed_json_raises_clear_error_without_overwriting,
        test_save_creates_missing_data_directory,
        test_save_all_and_load_all_data,
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
