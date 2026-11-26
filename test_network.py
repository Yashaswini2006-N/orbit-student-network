import network


def make_connected_sample_network():
    """Build a sample graph using initialise_network, send_request, and accept_request."""
    net = network.initialise_network([
        "Yashaswini N",
        "Rachana C Madure",
        "Anshuman Roy",
        "Jeevan Yogesh Ghandasi",
        "Giridhar N",
        "Isolated Student",
    ])

    edges = [
        ("Yashaswini N", "Rachana C Madure"),
        ("Yashaswini N", "Anshuman Roy"),
        ("Rachana C Madure", "Jeevan Yogesh Ghandasi"),
        ("Anshuman Roy", "Giridhar N"),
    ]

    for sender, receiver in edges:
        assert network.send_request(net, sender, receiver) == "Connection request sent."
        assert network.accept_request(net, sender, receiver) == "Connection accepted."

    return net


def test_request_send_duplicates_and_self():
    net = network.initialise_network(["Alice", "Bob", "Charlie"])

    # Unknown user check
    assert network.send_request(net, "Alice", "Nobody") == "User does not exist."
    assert network.send_request(net, "Nobody", "Alice") == "User does not exist."

    # Prevent self-request
    assert network.send_request(net, "Alice", "Alice") == "You cannot connect with yourself."
    assert net["pending"] == []
    assert "Alice" not in net["accepted"]["Alice"]

    # Valid request
    assert network.send_request(net, "Alice", "Bob") == "Connection request sent."
    assert net["pending"] == [{"sender": "Alice", "receiver": "Bob"}]

    # Prevent duplicate request in same direction
    assert network.send_request(net, "Alice", "Bob") == "Request already sent."
    assert len(net["pending"]) == 1

    # Prevent duplicate request in reverse direction while pending
    assert network.send_request(net, "Bob", "Alice") == "This user has already sent you a request."
    assert len(net["pending"]) == 1

    # Accept is directed: wrong direction must fail
    assert network.accept_request(net, "Bob", "Alice") == "No such pending request."


def test_request_accept_reject_cancel_and_remove():
    net = network.initialise_network(["Alice", "Bob", "Charlie", "Dave"])

    # Accept flow
    assert network.send_request(net, "Alice", "Bob") == "Connection request sent."
    assert network.accept_request(net, "Alice", "Bob") == "Connection accepted."
    assert net["pending"] == []
    assert "Bob" in net["accepted"]["Alice"] and "Alice" in net["accepted"]["Bob"]

    # Duplicate request after already connected must fail
    assert network.send_request(net, "Alice", "Bob") == "You are already connected."
    assert network.send_request(net, "Bob", "Alice") == "You are already connected."

    # Reject flow
    assert network.send_request(net, "Charlie", "Alice") == "Connection request sent."
    assert network.reject_request(net, "Charlie", "Alice") == "Connection request rejected."
    assert net["pending"] == []
    assert "Charlie" not in net["accepted"]["Alice"]
    assert "Alice" not in net["accepted"]["Charlie"]
    assert network.reject_request(net, "Charlie", "Alice") == "No such pending request."

    # Cancel flow
    assert network.send_request(net, "Alice", "Dave") == "Connection request sent."
    assert network.cancel_request(net, "Alice", "Dave") == "Connection request cancelled."
    assert net["pending"] == []
    assert "Dave" not in net["accepted"]["Alice"]
    assert network.cancel_request(net, "Alice", "Dave") == "No such pending request."

    # Remove accepted connection (undirected removal)
    assert network.remove_connection(net, "Alice", "Bob") == "Connection removed."
    assert "Bob" not in net["accepted"]["Alice"]
    assert "Alice" not in net["accepted"]["Bob"]
    assert network.remove_connection(net, "Alice", "Bob") == "You are not connected."
    assert network.remove_connection(net, "Alice", "Unknown") == "User does not exist."


def test_graph_undirected_no_duplicates_and_mutual():
    net = make_connected_sample_network()

    # Every edge is undirected and has no duplicates or self-loops
    for user, neighbors in net["accepted"].items():
        assert user not in neighbors, f"Self-connection found for {user}"
        assert len(neighbors) == len(set(neighbors)), f"Duplicate edges found for {user}: {neighbors}"
        for friend in neighbors:
            assert user in net["accepted"][friend], (
                f"Undirected edge missing: {friend} does not list {user}"
            )

    assert set(network.view_connections(net, "Yashaswini N")) == {
        "Rachana C Madure",
        "Anshuman Roy",
    }
    assert network.view_connections(net, "Missing") == []

    # Mutual connections
    assert network.mutual_connections(net, "Rachana C Madure", "Anshuman Roy") == ["Yashaswini N"]
    assert network.mutual_connections(net, "Yashaswini N", "Isolated Student") == []
    assert network.mutual_connections(net, "Yashaswini N", "Missing") == []

    # Degrees
    assert network.connection_degree(net, "Yashaswini N", "Yashaswini N") == 0
    assert network.connection_degree(net, "Yashaswini N", "Rachana C Madure") == 1
    assert network.connection_degree(net, "Yashaswini N", "Jeevan Yogesh Ghandasi") == 2
    assert network.connection_degree(net, "Jeevan Yogesh Ghandasi", "Giridhar N") == 4
    assert network.connection_degree(net, "Yashaswini N", "Isolated Student") is None


def test_jaccard_similarity_and_suggestions():
    net = network.initialise_network(["U1", "U2", "U3", "U4", "U5", "Lonely1", "Lonely2"])

    # U1 connects to U2, U3
    # U4 connects to U2, U3 -> Jaccard(U1, U4) = |{U2, U3}| / |{U2, U3}| = 2/2 = 1.0
    # U5 connects to U2, Lonely1 -> Jaccard(U1, U5) = |{U2}| / |{U2, U3, Lonely1}| = 1/3
    edges = [
        ("U1", "U2"),
        ("U1", "U3"),
        ("U4", "U2"),
        ("U4", "U3"),
        ("U5", "U2"),
        ("U5", "Lonely1"),
    ]
    for s, r in edges:
        assert network.send_request(net, s, r) == "Connection request sent."
        assert network.accept_request(net, s, r) == "Connection accepted."

    # Common connections score
    assert abs(network.jaccard_score(net, "U1", "U4") - 1.0) < 1e-9
    assert abs(network.jaccard_score(net, "U1", "U5") - (1 / 3)) < 1e-9

    # No common connections (disjoint friend sets: U2 has {U1, U4, U5}, Lonely1 has {U5})
    # Wait: U2 and Lonely1 share U5; U3 ({U1, U4}) and Lonely1 ({U5}) share 0 friends
    assert network.jaccard_score(net, "U3", "Lonely1") == 0

    # Zero-connection users (must avoid ZeroDivisionError)
    assert network.jaccard_score(net, "Lonely2", "U1") == 0
    assert network.suggest_connections(net, "Lonely2") == []
    assert network.suggest_connections(net, "Unknown") == []

    # Suggestions for U1: should rank U4 (1.0) before U5 (1/3),
    # exclude self (U1), already-connected (U2, U3), and 0-score (Lonely1, Lonely2)
    suggestions = network.suggest_connections(net, "U1")
    assert [u for u, _ in suggestions] == ["U4", "U5"], f"Unexpected suggestions: {suggestions}"
    assert abs(suggestions[0][1] - 1.0) < 1e-9
    assert abs(suggestions[1][1] - (1 / 3)) < 1e-9
    suggested_users = {u for u, _ in suggestions}
    assert "U1" not in suggested_users
    assert "U2" not in suggested_users and "U3" not in suggested_users

    # Pending requests must also be excluded from suggestions
    assert network.send_request(net, "U1", "U4") == "Connection request sent."
    suggestions_after_pending = network.suggest_connections(net, "U1")
    assert [u for u, _ in suggestions_after_pending] == ["U5"]


def test_bfs_shortest_path():
    net = network.initialise_network(["A", "B", "C", "D", "E", "Island"])

    # Create two paths from A to C:
    # Longer path: A - D - E - C (3 hops)
    # Shorter path: A - B - C (2 hops)
    # Put longer-path neighbor D first to prove BFS picks the shortest path, not DFS/first-found
    edges = [
        ("A", "D"),
        ("D", "E"),
        ("E", "C"),
        ("A", "B"),
        ("B", "C"),
    ]
    for s, r in edges:
        assert network.send_request(net, s, r) == "Connection request sent."
        assert network.accept_request(net, s, r) == "Connection accepted."

    # Direct connection
    assert network.shortest_path(net, "A", "B") == ["A", "B"]
    assert network.connection_degree(net, "A", "B") == 1

    # Multi-step shortest path (2 hops via B, not 3 hops via D-E)
    assert network.shortest_path(net, "A", "C") == ["A", "B", "C"]
    assert network.connection_degree(net, "A", "C") == 2

    # Same source and destination
    assert network.shortest_path(net, "A", "A") == ["A"]
    assert network.connection_degree(net, "A", "A") == 0

    # Disconnected user -> None
    assert network.shortest_path(net, "A", "Island") is None
    assert network.connection_degree(net, "A", "Island") is None

    # Unknown user -> None
    assert network.shortest_path(net, "A", "Ghost") is None
    assert network.connection_degree(net, "Ghost", "A") is None


def run_all_tests():
    tests = [
        test_request_send_duplicates_and_self,
        test_request_accept_reject_cancel_and_remove,
        test_graph_undirected_no_duplicates_and_mutual,
        test_jaccard_similarity_and_suggestions,
        test_bfs_shortest_path,
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
