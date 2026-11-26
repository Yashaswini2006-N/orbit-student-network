import json
import tempfile
from pathlib import Path

import network
import notifications as notif_mod
import posts
import storage


def test_add_and_view_notifications_preserves_insertion_order():
    notifications = {}

    notif_mod.add_notification(notifications, "Yashaswini N", "First alert")
    notif_mod.add_notification(notifications, "Yashaswini N", "Second alert")
    notif_mod.add_notification(notifications, "Yashaswini N", "Third alert")

    items = notif_mod.view_notifications(notifications, "Yashaswini N")
    assert [n["message"] for n in items] == [
        "First alert",
        "Second alert",
        "Third alert",
    ], "Notifications must preserve insertion order"
    assert all(n["read"] is False for n in items), "New notifications must start unread"
    assert all("created_at" in n and isinstance(n["created_at"], str) for n in items)

    # Viewing a user with no notifications should return [] without mutating dict
    assert notif_mod.view_notifications(notifications, "Unknown") == []
    assert "Unknown" not in notifications


def test_unread_count_and_mark_read_isolation():
    notifications = {}

    assert notif_mod.unread_count(notifications, "Rachana C Madure") == 0

    notif_mod.add_notification(notifications, "Rachana C Madure", "Alert 1")
    notif_mod.add_notification(notifications, "Rachana C Madure", "Alert 2")
    notif_mod.add_notification(notifications, "Anshuman Roy", "Other user alert")

    assert notif_mod.unread_count(notifications, "Rachana C Madure") == 2
    assert notif_mod.unread_count(notifications, "Anshuman Roy") == 1

    res = notif_mod.mark_notifications_read(notifications, "Rachana C Madure")
    assert res == "Notifications marked as read."
    assert notif_mod.unread_count(notifications, "Rachana C Madure") == 0
    assert all(
        n["read"] is True
        for n in notif_mod.view_notifications(notifications, "Rachana C Madure")
    )

    # Unrelated user's notifications must not be modified
    anshuman_items = notif_mod.view_notifications(notifications, "Anshuman Roy")
    assert notif_mod.unread_count(notifications, "Anshuman Roy") == 1
    assert anshuman_items[0]["read"] is False

    # Adding a new notification after marking previous ones read increments unread_count again
    notif_mod.add_notification(notifications, "Rachana C Madure", "Alert 3")
    assert notif_mod.unread_count(notifications, "Rachana C Madure") == 1


def test_connection_request_and_accept_notifications():
    net = network.initialise_network(["Yashaswini N", "Rachana C Madure"])
    notifications = {}

    # Send connection request -> notify receiver
    send_msg = network.send_request(net, "Yashaswini N", "Rachana C Madure")
    assert send_msg == "Connection request sent."
    notif_mod.notify_connection_request(notifications, "Yashaswini N", "Rachana C Madure")

    rachana_items = notif_mod.view_notifications(notifications, "Rachana C Madure")
    assert len(rachana_items) == 1
    assert rachana_items[0]["message"] == "Yashaswini N sent you a connection request."
    assert rachana_items[0]["read"] is False
    assert notif_mod.unread_count(notifications, "Yashaswini N") == 0

    # Accept connection request -> notify original sender
    accept_msg = network.accept_request(net, "Yashaswini N", "Rachana C Madure")
    assert accept_msg == "Connection accepted."
    notif_mod.notify_connection_accepted(notifications, "Yashaswini N", "Rachana C Madure")

    yash_items = notif_mod.view_notifications(notifications, "Yashaswini N")
    assert len(yash_items) == 1
    assert yash_items[0]["message"] == "Rachana C Madure accepted your connection request."
    assert yash_items[0]["read"] is False

    # Self-notifications for connections should be ignored
    notif_mod.notify_connection_request(notifications, "Yashaswini N", "Yashaswini N")
    notif_mod.notify_connection_accepted(notifications, "Yashaswini N", "Yashaswini N")
    assert len(notif_mod.view_notifications(notifications, "Yashaswini N")) == 1


def test_posts_reexports_share_same_functions_and_json_roundtrip():
    assert posts.add_notification is notif_mod.add_notification
    assert posts.view_notifications is notif_mod.view_notifications
    assert posts.mark_notifications_read is notif_mod.mark_notifications_read

    notifications = {}
    posts_list = []
    posts.create_post(posts_list, "Rachana C Madure", "Hello DSA!")
    posts.like_post(posts_list, 1, "Yashaswini N", notifications)
    notif_mod.notify_connection_request(notifications, "Anshuman Roy", "Rachana C Madure")

    assert notif_mod.unread_count(notifications, "Rachana C Madure") == 2

    # Ensure JSON serializability and storage.py round-trip using a temporary directory
    json.dumps(notifications)
    original_folder = storage.DATA_FOLDER
    with tempfile.TemporaryDirectory() as tmp_dir:
        storage.DATA_FOLDER = Path(tmp_dir) / "data"
        try:
            storage.save_data("notifications.json", notifications)
            reloaded = storage.load_data("notifications.json")
            assert reloaded == notifications
            assert notif_mod.unread_count(reloaded, "Rachana C Madure") == 2
        finally:
            storage.DATA_FOLDER = original_folder


def run_all_tests():
    tests = [
        test_add_and_view_notifications_preserves_insertion_order,
        test_unread_count_and_mark_read_isolation,
        test_connection_request_and_accept_notifications,
        test_posts_reexports_share_same_functions_and_json_roundtrip,
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
