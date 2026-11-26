import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "data"


def _default_data(filename):
    """Return a fresh default data structure for known data files."""
    if filename == "students.json":
        return {}
    if filename == "connections.json":
        return {"accepted": {}, "pending": []}
    if filename == "posts.json":
        return []
    if filename == "notifications.json":
        return {}
    return None


def load_data(filename):
    """Load JSON data from the data folder with safe missing/empty handling."""
    path = Path(DATA_FOLDER) / filename

    if not path.exists():
        default = _default_data(filename)
        if default is not None:
            return default
        raise FileNotFoundError(f"Data file not found: '{path}'")

    content = path.read_text(encoding="utf-8")
    if not content.strip():
        default = _default_data(filename)
        if default is not None:
            return default
        raise ValueError(f"Data file '{path}' is empty and has no default schema.")

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"Malformed JSON in '{path}' (line {exc.lineno}, column {exc.colno}): "
            f"{exc.msg}. The file was not modified."
        ) from exc


def save_data(filename, data):
    """Save data as UTF-8 JSON, creating the data directory if needed."""
    path = Path(DATA_FOLDER) / filename
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_all_data():
    """Load all application data in (students, connections, posts, notifications) order."""
    students = load_data("students.json")
    connections = load_data("connections.json")
    posts = load_data("posts.json")
    notifications = load_data("notifications.json")

    return students, connections, posts, notifications


def save_all_data(students, connections, posts, notifications):
    """Save all application data files."""
    save_data("students.json", students)
    save_data("connections.json", connections)
    save_data("posts.json", posts)
    save_data("notifications.json", notifications)
