
from datetime import datetime

from notifications import (
    add_notification,
    mark_notifications_read,
    view_notifications,
)


# Generate unique post ID
def generate_post_id(posts):
    if not posts:
        return 1
    return max(post["post_id"] for post in posts) + 1


# Generate unique comment ID
def generate_comment_id(post):
    ids = []

    def collect(comments):
        for comment in comments:
            ids.append(comment["comment_id"])
            collect(comment["replies"])

    collect(post["comments"])
    return max(ids, default=0) + 1


# Create text or image post
def create_post(posts, username, text, image_path=None):

    if not text.strip() and not image_path:
        return "Post cannot be empty."

    post = {
        "post_id": generate_post_id(posts),
        "username": username,
        "text": text,
        "image_path": image_path,
        "likes": [],
        "comments": [],
        "created_at": datetime.now().isoformat()
    }

    posts.append(post)
    return "Post created successfully."


# Delete own post
def delete_post(posts, post_id, username):

    for post in posts:
        if post["post_id"] == post_id:

            if post["username"] != username:
                return "You can only delete your own posts."

            posts.remove(post)
            return "Post deleted successfully."

    return "Post not found."


# View own posts
def view_own_posts(posts, username):

    return [
        post for post in posts
        if post["username"] == username
    ]


# Home feed: accepted connections, newest first
def home_feed(posts, username, network):

    connections = network["accepted"].get(username, [])

    feed = [
        post for post in posts
        if post["username"] in connections
    ]

    return sorted(
        feed,
        key=lambda post: post["created_at"],
        reverse=True
    )



# Like a post
def like_post(posts, post_id, username, notifications):

    for post in posts:
        if post["post_id"] == post_id:

            if username in post["likes"]:
                return "You have already liked this post."

            post["likes"].append(username)

            if post["username"] != username:
                add_notification(
                    notifications,
                    post["username"],
                    username + " liked your post."
                )

            return "Post liked."

    return "Post not found."


# Unlike a post
def unlike_post(posts, post_id, username):

    for post in posts:
        if post["post_id"] == post_id:

            if username not in post["likes"]:
                return "You have not liked this post."

            post["likes"].remove(username)
            return "Like removed."

    return "Post not found."


# Add comment or reply
def add_comment(posts, post_id, username, text,
                notifications, parent_comment_id=None):

    if not text.strip():
        return "Comment cannot be empty."

    for post in posts:
        if post["post_id"] == post_id:

            new_comment = {
                "comment_id": generate_comment_id(post),
                "username": username,
                "text": text,
                "created_at": datetime.now().isoformat(),
                "replies": []
            }

            # Normal comment
            if parent_comment_id is None:

                post["comments"].append(new_comment)

                if post["username"] != username:
                    add_notification(
                        notifications,
                        post["username"],
                        username + " commented on your post."
                    )

                return "Comment added."

            # Find parent comment for reply
            def find_comment(comments):

                for comment in comments:

                    if comment["comment_id"] == parent_comment_id:
                        return comment

                    result = find_comment(comment["replies"])

                    if result:
                        return result

                return None

            parent = find_comment(post["comments"])

            if parent is None:
                return "Comment not found."

            parent["replies"].append(new_comment)

            if parent["username"] != username:
                add_notification(
                    notifications,
                    parent["username"],
                    username + " replied to your comment."
                )

            return "Reply added."

    return "Post not found."


# View all posts, newest first
def view_posts(posts):

    return sorted(
        posts,
        key=lambda post: post["created_at"],
        reverse=True
    )


# Count comments and replies
def count_comments(comments):

    total = 0

    for comment in comments:
        total += 1
        total += count_comments(comment["replies"])

    return total


# Trending posts among accepted connections
def trending_posts(posts, username, network):

    connections = network["accepted"].get(username, [])

    trending = [
        post for post in posts
        if post["username"] in connections
    ]

    return sorted(
        trending,
        key=lambda post: (
            len(post["likes"]),
            post["created_at"],
        ),
        reverse=True,
    )


