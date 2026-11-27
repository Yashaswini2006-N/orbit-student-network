import time
import posts
from network import accept_request, initialise_network, send_request


def make_sample_network():
    """Create a sample student graph using network.py functions."""
    network = initialise_network([
        "Yashaswini N",
        "Rachana C Madure",
        "Anshuman Roy",
        "Jeevan Yogesh Ghandasi",
        "Giridhar N",
    ])

    connections = [
        ("Yashaswini N", "Rachana C Madure"),
        ("Yashaswini N", "Anshuman Roy"),
        ("Rachana C Madure", "Jeevan Yogesh Ghandasi"),
        ("Anshuman Roy", "Giridhar N"),
    ]

    for sender, receiver in connections:
        assert send_request(network, sender, receiver) == "Connection request sent.", (
            f"Failed to send request from {sender} to {receiver}"
        )
        assert accept_request(network, sender, receiver) == "Connection accepted.", (
            f"Failed to accept request from {sender} to {receiver}"
        )

    return network


def test_create_post_and_image_only_post():
    posts_list = []

    res1 = posts.create_post(posts_list, "Rachana C Madure", "My first DSA project!")
    assert res1 == "Post created successfully.", f"Unexpected result: {res1}"
    assert len(posts_list) == 1, "Expected 1 post in list"
    assert posts_list[0]["post_id"] == 1, "First post should get post_id 1"
    assert posts_list[0]["image_path"] is None, "Text-only post should have image_path=None"
    assert posts_list[0]["likes"] == [], "New post should start with empty likes"
    assert posts_list[0]["comments"] == [], "New post should start with empty comments"

    res2 = posts.create_post(
        posts_list,
        "Rachana C Madure",
        "",
        image_path="images/project.jpg",
    )
    assert res2 == "Post created successfully.", f"Image-only post failed: {res2}"
    assert len(posts_list) == 2, "Expected 2 posts after image-only post"
    assert posts_list[1]["post_id"] == 2, "Second post should get post_id 2"
    assert posts_list[1]["text"] == "", "Image-only post text should be preserved"
    assert posts_list[1]["image_path"] == "images/project.jpg", "Image path mismatch"


def test_reject_empty_posts():
    posts_list = []

    res_empty = posts.create_post(posts_list, "Anshuman Roy", "")
    assert res_empty == "Post cannot be empty.", f"Empty string should be rejected, got: {res_empty}"

    res_spaces = posts.create_post(posts_list, "Anshuman Roy", "   \t\n  ")
    assert res_spaces == "Post cannot be empty.", f"Whitespace post should be rejected, got: {res_spaces}"

    assert posts_list == [], "Rejected posts must not be added to posts_list"


def test_home_feed_filtering_and_pending_exclusion():
    network = make_sample_network()
    posts_list = []

    # Pending request (not yet accepted) from Giridhar N to Yashaswini N
    assert send_request(network, "Giridhar N", "Yashaswini N") == "Connection request sent."

    posts.create_post(posts_list, "Rachana C Madure", "Accepted friend 1")
    posts.create_post(posts_list, "Anshuman Roy", "Accepted friend 2")
    posts.create_post(posts_list, "Yashaswini N", "My own post")
    posts.create_post(posts_list, "Jeevan Yogesh Ghandasi", "Friend-of-friend stranger")
    posts.create_post(posts_list, "Giridhar N", "Pending request sender")

    feed = posts.home_feed(posts_list, "Yashaswini N", network)
    authors_in_feed = {post["username"] for post in feed}

    assert authors_in_feed == {"Rachana C Madure", "Anshuman Roy"}, (
        f"home_feed should contain only accepted connections, got: {authors_in_feed}"
    )
    assert "Yashaswini N" not in authors_in_feed, "User's own posts should not appear in home_feed"
    assert "Jeevan Yogesh Ghandasi" not in authors_in_feed, "Strangers' posts should not appear in home_feed"
    assert "Giridhar N" not in authors_in_feed, "Pending request user's posts should not appear in home_feed"

    own = posts.view_own_posts(posts_list, "Yashaswini N")
    assert len(own) == 1 and own[0]["text"] == "My own post", "view_own_posts should return user's own posts"

    empty_feed = posts.home_feed(posts_list, "Unknown User", network)
    assert empty_feed == [], "User with no accepted connections should get an empty home_feed"


def test_newest_first_ordering_distinct_timestamps():
    network = make_sample_network()
    posts_list = []

    posts.create_post(posts_list, "Rachana C Madure", "Oldest post")
    time.sleep(0.02)
    posts.create_post(posts_list, "Anshuman Roy", "Middle post")
    time.sleep(0.02)
    posts.create_post(posts_list, "Rachana C Madure", "Newest post")

    # Confirm timestamps are strictly increasing before testing sort order
    assert posts_list[0]["created_at"] < posts_list[1]["created_at"] < posts_list[2]["created_at"], (
        "Test setup expected distinct increasing timestamps"
    )

    all_posts = posts.view_posts(posts_list)
    assert [p["post_id"] for p in all_posts] == [3, 2, 1], (
        f"view_posts should return newest first [3, 2, 1], got {[p['post_id'] for p in all_posts]}"
    )

    feed = posts.home_feed(posts_list, "Yashaswini N", network)
    assert [p["post_id"] for p in feed] == [3, 2, 1], (
        f"home_feed should return newest first [3, 2, 1], got {[p['post_id'] for p in feed]}"
    )


def test_trending_posts_uses_likes_only_and_newest_tiebreak():
    network = make_sample_network()
    posts_list = []
    notifications = {}

    # The first two accepted posts have equal likes; the newer one should lead.
    posts.create_post(posts_list, "Rachana C Madure", "Older two-like post")
    time.sleep(0.02)
    posts.create_post(posts_list, "Anshuman Roy", "Newer two-like post")
    time.sleep(0.02)
    # Many comments must not lift this one-like post above posts with two likes.
    posts.create_post(posts_list, "Rachana C Madure", "Comment-heavy one-like post")
    time.sleep(0.02)
    posts.create_post(posts_list, "Anshuman Roy", "Zero-like post")
    time.sleep(0.02)
    posts.create_post(posts_list, "Jeevan Yogesh Ghandasi", "Popular stranger post")

    assert posts.like_post(posts_list, 1, "Yashaswini N", notifications) == "Post liked."
    assert posts.like_post(posts_list, 1, "Anshuman Roy", notifications) == "Post liked."
    assert posts.like_post(posts_list, 2, "Yashaswini N", notifications) == "Post liked."
    assert posts.like_post(posts_list, 2, "Rachana C Madure", notifications) == "Post liked."
    assert posts.like_post(posts_list, 3, "Yashaswini N", notifications) == "Post liked."
    assert posts.add_comment(posts_list, 3, "Yashaswini N", "First comment", notifications) == "Comment added."
    assert posts.add_comment(
        posts_list, 3, "Rachana C Madure", "Reply one", notifications, parent_comment_id=1
    ) == "Reply added."
    assert posts.add_comment(
        posts_list, 3, "Yashaswini N", "Reply two", notifications, parent_comment_id=2
    ) == "Reply added."
    # An excluded stranger may have more likes and comments than every connection post.
    posts_list[4]["likes"] = [f"user{i}" for i in range(10)]
    posts_list[4]["comments"] = [{"replies": []} for _ in range(10)]

    ranked_ids = [post["post_id"] for post in posts.trending_posts(posts_list, "Yashaswini N", network)]
    assert ranked_ids == [2, 1, 3, 4], (
        f"Expected likes-only order with newest tie-break [2, 1, 3, 4], got {ranked_ids}"
    )

    assert posts.trending_posts([], "Yashaswini N", network) == []
    assert posts.trending_posts(posts_list, "Unknown User", network) == []


def test_trending_updates_after_like_and_home_feed_stays_newest_first():
    network = make_sample_network()
    posts_list = []
    notifications = {}

    posts.create_post(posts_list, "Rachana C Madure", "Older post")
    time.sleep(0.02)
    posts.create_post(posts_list, "Anshuman Roy", "Newer post")

    assert posts.like_post(posts_list, 1, "Yashaswini N", notifications) == "Post liked."
    assert posts.like_post(posts_list, 1, "Anshuman Roy", notifications) == "Post liked."
    assert posts.like_post(posts_list, 2, "Rachana C Madure", notifications) == "Post liked."

    before = [post["post_id"] for post in posts.trending_posts(posts_list, "Yashaswini N", network)]
    feed_before = [post["post_id"] for post in posts.home_feed(posts_list, "Yashaswini N", network)]
    assert before == [1, 2]
    assert feed_before == [2, 1], "The regular feed should remain newest-first"

    assert posts.like_post(posts_list, 2, "Yashaswini N", notifications) == "Post liked."
    after = [post["post_id"] for post in posts.trending_posts(posts_list, "Yashaswini N", network)]
    feed_after = [post["post_id"] for post in posts.home_feed(posts_list, "Yashaswini N", network)]

    assert after == [2, 1], f"Expected the newly liked, newer post to rank first, got {after}"
    assert feed_after == feed_before == [2, 1], "Liking should not change regular feed ordering"


def test_delete_post_ownership_and_invalid_id():
    posts_list = []
    posts.create_post(posts_list, "Rachana C Madure", "Rachana's post")
    posts.create_post(posts_list, "Anshuman Roy", "Anshuman's post")

    # Other user cannot delete Rachana's post
    denied = posts.delete_post(posts_list, 1, "Yashaswini N")
    assert denied == "You can only delete your own posts.", f"Unexpected message: {denied}"
    assert any(p["post_id"] == 1 for p in posts_list), "Post 1 should still exist after failed delete"

    # Invalid post ID
    missing = posts.delete_post(posts_list, 999, "Rachana C Madure")
    assert missing == "Post not found.", f"Expected Post not found, got: {missing}"

    # Owner can delete own post
    ok = posts.delete_post(posts_list, 2, "Anshuman Roy")
    assert ok == "Post deleted successfully.", f"Owner delete failed: {ok}"
    assert [p["post_id"] for p in posts_list] == [1], "Only Post 1 should remain after deleting Post 2"


def test_likes_duplicates_unlike_and_invalid_post():
    posts_list = []
    notifications = {}
    posts.create_post(posts_list, "Rachana C Madure", "Like test post")

    # Invalid post IDs
    assert posts.like_post(posts_list, 999, "Yashaswini N", notifications) == "Post not found."
    assert posts.unlike_post(posts_list, 999, "Yashaswini N") == "Post not found."

    # Unlike before liking
    assert posts.unlike_post(posts_list, 1, "Yashaswini N") == "You have not liked this post."

    # First like succeeds
    assert posts.like_post(posts_list, 1, "Yashaswini N", notifications) == "Post liked."
    assert posts_list[0]["likes"] == ["Yashaswini N"], "Like should be recorded"

    # Duplicate like is prevented
    dup = posts.like_post(posts_list, 1, "Yashaswini N", notifications)
    assert dup == "You have already liked this post.", f"Duplicate like was not blocked: {dup}"
    assert posts_list[0]["likes"] == ["Yashaswini N"], "Likes list must not contain duplicates"
    assert len(posts.view_notifications(notifications, "Rachana C Madure")) == 1, (
        "Duplicate like must not create a second notification"
    )

    # Unlike succeeds and removes username
    assert posts.unlike_post(posts_list, 1, "Yashaswini N") == "Like removed."
    assert posts_list[0]["likes"] == [], "Likes list should be empty after unlike"

    # Unliking again reports not liked
    assert posts.unlike_post(posts_list, 1, "Yashaswini N") == "You have not liked this post."


def test_comments_validation_and_nested_replies():
    posts_list = []
    notifications = {}
    posts.create_post(posts_list, "Rachana C Madure", "Comment test post")

    # Empty and whitespace comments rejected
    assert posts.add_comment(posts_list, 1, "Yashaswini N", "", notifications) == "Comment cannot be empty."
    assert posts.add_comment(posts_list, 1, "Yashaswini N", "   ", notifications) == "Comment cannot be empty."

    # Invalid post ID and invalid parent comment ID
    assert posts.add_comment(posts_list, 999, "Yashaswini N", "Hello", notifications) == "Post not found."
    assert (
        posts.add_comment(posts_list, 1, "Yashaswini N", "Orphan reply", notifications, parent_comment_id=999)
        == "Comment not found."
    )

    # Top-level comment (id=1) -> reply (id=2) -> nested reply (id=3)
    assert posts.add_comment(posts_list, 1, "Yashaswini N", "Great work!", notifications) == "Comment added."
    assert (
        posts.add_comment(posts_list, 1, "Rachana C Madure", "Thank you!", notifications, parent_comment_id=1)
        == "Reply added."
    )
    assert (
        posts.add_comment(posts_list, 1, "Anshuman Roy", "Agree with both!", notifications, parent_comment_id=2)
        == "Reply added."
    )

    comments = posts_list[0]["comments"]
    assert posts.count_comments(comments) == 3, "count_comments should count top-level + nested replies"
    assert comments[0]["comment_id"] == 1
    assert comments[0]["replies"][0]["comment_id"] == 2
    assert comments[0]["replies"][0]["replies"][0]["comment_id"] == 3


def test_notifications_creation_self_actions_and_read_state():
    posts_list = []
    notifications = {}
    posts.create_post(posts_list, "Rachana C Madure", "Notification test post")

    # Self-like and self-comment must not notify the author
    assert posts.like_post(posts_list, 1, "Rachana C Madure", notifications) == "Post liked."
    assert posts.add_comment(posts_list, 1, "Rachana C Madure", "Self comment", notifications) == "Comment added."
    assert posts.view_notifications(notifications, "Rachana C Madure") == [], (
        "Self-likes and self-comments should not create notifications"
    )

    # Another user likes and comments -> unread notifications for Rachana
    assert posts.like_post(posts_list, 1, "Yashaswini N", notifications) == "Post liked."
    assert posts.add_comment(posts_list, 1, "Yashaswini N", "Nice post!", notifications) == "Comment added."

    rachana_notifs = posts.view_notifications(notifications, "Rachana C Madure")
    assert len(rachana_notifs) == 2, f"Expected 2 notifications for Rachana, got {len(rachana_notifs)}"
    assert all(n["read"] is False for n in rachana_notifs), "New notifications must start unread (read=False)"
    assert rachana_notifs[0]["message"] == "Yashaswini N liked your post."
    assert rachana_notifs[1]["message"] == "Yashaswini N commented on your post."

    # Reply to Yashaswini's comment (comment_id=2) -> notification for Yashaswini; self-reply to own comment -> none
    assert (
        posts.add_comment(posts_list, 1, "Rachana C Madure", "Thanks!", notifications, parent_comment_id=2)
        == "Reply added."
    )
    assert (
        posts.add_comment(posts_list, 1, "Rachana C Madure", "Self reply", notifications, parent_comment_id=1)
        == "Reply added."
    )

    yash_notifs = posts.view_notifications(notifications, "Yashaswini N")
    assert len(yash_notifs) == 1, "Yashaswini should receive 1 reply notification"
    assert yash_notifs[0]["message"] == "Rachana C Madure replied to your comment."
    assert yash_notifs[0]["read"] is False, "Reply notification should start unread"

    # Mark Rachana's notifications as read and verify read state changed
    assert posts.mark_notifications_read(notifications, "Rachana C Madure") == "Notifications marked as read."
    rachana_after = posts.view_notifications(notifications, "Rachana C Madure")
    assert all(n["read"] is True for n in rachana_after), "All notifications for Rachana should now be read=True"

    # Yashaswini's notifications must remain unread
    assert posts.view_notifications(notifications, "Yashaswini N")[0]["read"] is False, (
        "Marking one user's notifications read must not affect other users"
    )


def run_all_tests():
    tests = [
        test_create_post_and_image_only_post,
        test_reject_empty_posts,
        test_home_feed_filtering_and_pending_exclusion,
        test_newest_first_ordering_distinct_timestamps,
        test_trending_posts_uses_likes_only_and_newest_tiebreak,
        test_trending_updates_after_like_and_home_feed_stays_newest_first,
        test_delete_post_ownership_and_invalid_id,
        test_likes_duplicates_unlike_and_invalid_post,
        test_comments_validation_and_nested_replies,
        test_notifications_creation_self_actions_and_read_state,
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
