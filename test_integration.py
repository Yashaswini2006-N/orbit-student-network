import tempfile
from pathlib import Path

import accounts
import main
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


def test_connection_state_refreshes_between_two_sessions_in_both_directions():
    """Check that sessions reload request JSON and expose incoming/outgoing requests."""
    original_folder = storage.DATA_FOLDER

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage.DATA_FOLDER = Path(tmp_dir) / "data"
        try:
            graph = network.initialise_network(["Alice", "Bob"])
            storage.save_data("connections.json", graph)
            alice_session = {"connections": network.initialise_network(["Alice", "Bob"])}
            bob_session = {"connections": network.initialise_network(["Alice", "Bob"])}

            # Alice sends; Bob's stale session refreshes and sees the incoming request.
            assert network.send_request(graph, "Alice", "Bob") == "Connection request sent."
            storage.save_data("connections.json", graph)
            main._refresh_connection_state(bob_session)
            incoming_senders = {
                request["sender"] for request in bob_session["connections"]["pending"]
                if request["receiver"] == "Bob"
            }
            outgoing_receivers = {
                request["receiver"] for request in bob_session["connections"]["pending"]
                if request["sender"] == "Alice"
            }
            assert "Alice" in incoming_senders
            assert "Bob" in outgoing_receivers
            assert network.send_request(bob_session["connections"], "Bob", "Alice") == (
                "This user has already sent you a request."
            )

            # Bob accepts; Alice's session reloads mutual accepted state from JSON.
            assert network.accept_request(bob_session["connections"], "Alice", "Bob") == "Connection accepted."
            storage.save_data("connections.json", bob_session["connections"])
            main._refresh_connection_state(alice_session)
            assert "Bob" in alice_session["connections"]["accepted"]["Alice"]
            assert "Alice" in alice_session["connections"]["accepted"]["Bob"]
            assert alice_session["connections"]["pending"] == []

            # Repeat with Bob sending and Alice accepting.
            reverse_graph = network.initialise_network(["Alice", "Bob"])
            storage.save_data("connections.json", reverse_graph)
            alice_session["connections"] = network.initialise_network(["Alice", "Bob"])
            bob_session["connections"] = network.initialise_network(["Alice", "Bob"])
            assert network.send_request(reverse_graph, "Bob", "Alice") == "Connection request sent."
            storage.save_data("connections.json", reverse_graph)
            main._refresh_connection_state(alice_session)
            main._refresh_connection_state(bob_session)
            incoming_senders = {
                request["sender"] for request in alice_session["connections"]["pending"]
                if request["receiver"] == "Alice"
            }
            outgoing_receivers = {
                request["receiver"] for request in bob_session["connections"]["pending"]
                if request["sender"] == "Bob"
            }
            assert "Bob" in incoming_senders
            assert "Alice" in outgoing_receivers
            assert network.send_request(bob_session["connections"], "Bob", "Alice") == "Request already sent."

            assert network.accept_request(alice_session["connections"], "Bob", "Alice") == "Connection accepted."
            storage.save_data("connections.json", alice_session["connections"])
            main._refresh_connection_state(bob_session)
            assert "Alice" in bob_session["connections"]["accepted"]["Bob"]
            assert "Bob" in bob_session["connections"]["accepted"]["Alice"]
            assert bob_session["connections"]["pending"] == []
        finally:
            storage.DATA_FOLDER = original_folder


def test_notifications_refresh_between_sessions_and_mark_read():
    """Verify request/accept notifications and unread counts refresh from JSON."""
    original_folder = storage.DATA_FOLDER

    with tempfile.TemporaryDirectory() as tmp_dir:
        storage.DATA_FOLDER = Path(tmp_dir) / "data"
        try:
            storage.save_data("notifications.json", {})
            sender_session = {"notifications": {}}
            recipient_session = {"notifications": {}}

            request_notifications = storage.load_data("notifications.json")
            notif_mod.notify_connection_request(request_notifications, "Alice", "Bob")
            storage.save_data("notifications.json", request_notifications)

            main._refresh_notification_state(recipient_session)
            assert notif_mod.unread_count(recipient_session["notifications"], "Bob") == 1
            assert notif_mod.view_notifications(recipient_session["notifications"], "Bob")[0]["message"] == (
                "Alice sent you a connection request."
            )

            notif_mod.mark_notifications_read(recipient_session["notifications"], "Bob")
            storage.save_data("notifications.json", recipient_session["notifications"])
            main._refresh_notification_state(sender_session)
            assert notif_mod.unread_count(sender_session["notifications"], "Bob") == 0

            accepted_notifications = storage.load_data("notifications.json")
            notif_mod.notify_connection_accepted(accepted_notifications, "Alice", "Bob")
            storage.save_data("notifications.json", accepted_notifications)
            main._refresh_notification_state(sender_session)
            assert notif_mod.unread_count(sender_session["notifications"], "Alice") == 1
            assert notif_mod.view_notifications(sender_session["notifications"], "Alice")[0]["message"] == (
                "Bob accepted your connection request."
            )
        finally:
            storage.DATA_FOLDER = original_folder


def test_navigation_page_restores_from_validated_query_parameter():
    """Persist the selected page without treating a URL value as authentication."""
    valid_pages = {"Home", "Trending", "Connections", "Profile", "Notifications"}
    session_state = {}
    main._restore_navigation_page(session_state, {"page": "Profile"}, valid_pages)
    assert session_state["sidebar_navigation"] == "Profile"

    session_state = {}
    main._restore_navigation_page(session_state, {"page": "admin"}, valid_pages)
    assert session_state["sidebar_navigation"] == "Home"


def run_all_tests():
    tests = [
        test_end_to_end_backend_workflow,
        test_connection_state_refreshes_between_two_sessions_in_both_directions,
        test_notifications_refresh_between_sessions_and_mark_read,
        test_navigation_page_restores_from_validated_query_parameter,
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
