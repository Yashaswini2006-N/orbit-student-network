import tempfile
from pathlib import Path

import accounts
import network
import notifications as notif_mod
import posts
import storage


def test_end_to_end_backend_workflow():
    """Run the full backend lifecycle across accounts, network, posts, notifications, and storage."""
    original_folder = storage.DATA_FOLDER

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage.DATA_FOLDER = Path(tmp_dir) / "data"
        try:
            # 0. Load initial empty structures from isolated temp storage
            students, connections, posts_list, notifications = storage.load_all_data()
            assert students == {}
            assert connections == {"accepted": {}, "pending": []}
            assert posts_list == []
            assert notifications == {}

            # 1. Register two students: Alice and Bob
            ok_alice, msg_alice = accounts.register_student(
                students,
                connections,
                "Alice",
                "AlicePass123",
                "Alice Sharma",
                email="alice@college.edu",
                department="CSE",
                year=2,
                skills=["Python", "DSA"],
            )
            ok_bob, msg_bob = accounts.register_student(
                students,
                connections,
                "Bob",
                "BobPass123",
                "Bob Verma",
                email="bob@college.edu",
                department="ECE",
                year=2,
                skills=["Graphs", "Python"],
            )
            assert ok_alice is True, f"Alice registration failed: {msg_alice}"
            assert ok_bob is True, f"Bob registration failed: {msg_bob}"

            # 2. Verify both students are in students dict and graph as isolated vertices
            assert "Alice" in students and "Bob" in students
            assert students["Alice"]["password_hash"] != "AlicePass123"
            assert students["Bob"]["password_hash"] != "BobPass123"
            assert connections["accepted"]["Alice"] == []
            assert connections["accepted"]["Bob"] == []

            # 3. Log in as Alice
            session = {}
            login_ok, login_msg = accounts.login_student(students, "Alice", "AlicePass123", session)
            assert login_ok is True, f"Alice login failed: {login_msg}"
            assert accounts.get_current_user(session) == "Alice"

            # 4. Alice sends Bob a connection request
            req_msg = network.send_request(connections, "Alice", "Bob")
            assert req_msg == "Connection request sent."
            notif_mod.notify_connection_request(notifications, "Alice", "Bob")

            # 5. Verify Bob receives the connection request notification
            bob_notifs = notif_mod.view_notifications(notifications, "Bob")
            assert len(bob_notifs) == 1
            assert bob_notifs[0]["message"] == "Alice sent you a connection request."
            assert bob_notifs[0]["read"] is False
            assert notif_mod.unread_count(notifications, "Bob") == 1

            # 6. Bob accepts Alice's request
            accept_msg = network.accept_request(connections, "Alice", "Bob")
            assert accept_msg == "Connection accepted."
            notif_mod.notify_connection_accepted(notifications, "Alice", "Bob")

            # 7. Verify accepted connection exists in both adjacency lists (undirected)
            assert "Bob" in connections["accepted"]["Alice"]
            assert "Alice" in connections["accepted"]["Bob"]
            assert connections["pending"] == []

            # 8. Verify Alice receives the acceptance notification
            alice_notifs = notif_mod.view_notifications(notifications, "Alice")
            assert len(alice_notifs) == 1
            assert alice_notifs[0]["message"] == "Bob accepted your connection request."
            assert alice_notifs[0]["read"] is False

            # 9. Alice creates a post
            post_msg = posts.create_post(posts_list, "Alice", "Excited to share my DSA graph project!")
            assert post_msg == "Post created successfully."
            assert len(posts_list) == 1
            post_id = posts_list[0]["post_id"]

            # 10. Verify Bob sees Alice's post in his home feed
            bob_feed = posts.home_feed(posts_list, "Bob", connections)
            assert len(bob_feed) == 1
            assert bob_feed[0]["post_id"] == post_id
            assert bob_feed[0]["username"] == "Alice"

            # 11. Bob likes the post and adds a comment
            assert posts.like_post(posts_list, post_id, "Bob", notifications) == "Post liked."
            assert (
                posts.add_comment(posts_list, post_id, "Bob", "Great work, Alice!", notifications)
                == "Comment added."
            )

            # 12. Verify Alice receives the like and comment notifications
            alice_notifs = notif_mod.view_notifications(notifications, "Alice")
            assert [n["message"] for n in alice_notifs] == [
                "Bob accepted your connection request.",
                "Bob liked your post.",
                "Bob commented on your post.",
            ]

            # 13. Verify notification unread counts
            assert notif_mod.unread_count(notifications, "Alice") == 3
            assert notif_mod.unread_count(notifications, "Bob") == 1

            # 14. Mark Alice's notifications as read and verify unread count becomes 0
            assert notif_mod.mark_notifications_read(notifications, "Alice") == "Notifications marked as read."
            assert notif_mod.unread_count(notifications, "Alice") == 0
            assert notif_mod.unread_count(notifications, "Bob") == 1

            # 15. Save all four data structures using storage.save_all_data()
            storage.save_all_data(students, connections, posts_list, notifications)

            # 16. Reload them using storage.load_all_data()
            (
                reloaded_students,
                reloaded_connections,
                reloaded_posts,
                reloaded_notifications,
            ) = storage.load_all_data()

            # 17. Verify all reloaded structures remain intact
            assert reloaded_students == students
            bob_login_ok, _ = accounts.login_student(reloaded_students, "Bob", "BobPass123", {})
            assert bob_login_ok is True, "Reloaded student credentials should still authenticate"

            assert reloaded_connections == connections
            assert "Bob" in reloaded_connections["accepted"]["Alice"]
            assert "Alice" in reloaded_connections["accepted"]["Bob"]
            assert network.shortest_path(reloaded_connections, "Alice", "Bob") == ["Alice", "Bob"]
            assert network.connection_degree(reloaded_connections, "Alice", "Bob") == 1

            assert reloaded_posts == posts_list
            assert len(reloaded_posts) == 1
            assert reloaded_posts[0]["likes"] == ["Bob"]
            assert len(reloaded_posts[0]["comments"]) == 1
            assert reloaded_posts[0]["comments"][0]["username"] == "Bob"
            assert reloaded_posts[0]["comments"][0]["text"] == "Great work, Alice!"
            assert posts.home_feed(reloaded_posts, "Bob", reloaded_connections) == reloaded_posts

            assert reloaded_notifications == notifications
            assert notif_mod.unread_count(reloaded_notifications, "Alice") == 0
            assert notif_mod.unread_count(reloaded_notifications, "Bob") == 1
            assert all(n["read"] is True for n in reloaded_notifications["Alice"])
            assert reloaded_notifications["Bob"][0]["read"] is False
        finally:
            storage.DATA_FOLDER = original_folder


def run_all_tests():
    tests = [test_end_to_end_backend_workflow]
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
