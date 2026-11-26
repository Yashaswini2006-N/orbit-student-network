from datetime import datetime


def add_notification(notifications, username, message):
    """Append an unread notification for a user in insertion order."""
    if not isinstance(username, str) or not username.strip():
        return
    if not isinstance(message, str) or not message.strip():
        return

    notifications.setdefault(username, [])
    notifications[username].append({
        "message": message,
        "created_at": datetime.now().isoformat(),
        "read": False,
    })


def view_notifications(notifications, username):
    """Return all notifications for a user in insertion order."""
    return notifications.get(username, [])


def mark_notifications_read(notifications, username):
    """Mark all notifications for the given user as read."""
    for notification in notifications.get(username, []):
        notification["read"] = True

    return "Notifications marked as read."


def unread_count(notifications, username):
    """Return the number of unread notifications for the given user."""
    return sum(
        1
        for notification in notifications.get(username, [])
        if not notification.get("read", False)
    )


def notify_connection_request(notifications, sender, receiver):
    """Notify receiver that sender has sent a connection request."""
    if not sender or not receiver or sender == receiver:
        return
    add_notification(
        notifications,
        receiver,
        f"{sender} sent you a connection request.",
    )


def notify_connection_accepted(notifications, sender, receiver):
    """Notify sender that receiver accepted their connection request."""
    if not sender or not receiver or sender == receiver:
        return
    add_notification(
        notifications,
        sender,
        f"{receiver} accepted your connection request.",
    )
