
from collections import deque


def initialise_network(usernames):
    """Create an empty adjacency list for all registered users."""
    return {
        "accepted": {username: [] for username in usernames},
        "pending": []
    }


def send_request(network, sender, receiver):
    accepted = network["accepted"]
    pending = network["pending"]

    if sender not in accepted or receiver not in accepted:
        return "User does not exist."

    if sender == receiver:
        return "You cannot connect with yourself."

    if receiver in accepted[sender]:
        return "You are already connected."

    # Check whether a request already exists
    for request in pending:
        if request["sender"] == sender and request["receiver"] == receiver:
            return "Request already sent."

        # If the other person has already requested you
        if request["sender"] == receiver and request["receiver"] == sender:
            return "This user has already sent you a request."

    pending.append({
        "sender": sender,
        "receiver": receiver
    })

    return "Connection request sent."


def accept_request(network, sender, receiver):
    pending = network["pending"]
    accepted = network["accepted"]

    for request in pending:
        if request["sender"] == sender and request["receiver"] == receiver:

            # Add the connection in both directions
            accepted[sender].append(receiver)
            accepted[receiver].append(sender)

            pending.remove(request)
            return "Connection accepted."

    return "No such pending request."


def reject_request(network, sender, receiver):
    for request in network["pending"]:
        if request["sender"] == sender and request["receiver"] == receiver:
            network["pending"].remove(request)
            return "Connection request rejected."

    return "No such pending request."


def cancel_request(network, sender, receiver):
    for request in network["pending"]:
        if request["sender"] == sender and request["receiver"] == receiver:
            network["pending"].remove(request)
            return "Connection request cancelled."

    return "No such pending request."


def remove_connection(network, user1, user2):
    accepted = network["accepted"]

    if user1 not in accepted or user2 not in accepted:
        return "User does not exist."

    if user2 not in accepted[user1]:
        return "You are not connected."

    accepted[user1].remove(user2)
    accepted[user2].remove(user1)

    return "Connection removed."


def view_connections(network, username):
    return network["accepted"].get(username, [])


def mutual_connections(network, user1, user2):
    accepted = network["accepted"]

    if user1 not in accepted or user2 not in accepted:
        return []

    return list(set(accepted[user1]) & set(accepted[user2]))

#Jaccard's coefficient

def jaccard_score(network, user1, user2):
    accepted = network["accepted"]

    friends1 = set(accepted[user1])
    friends2 = set(accepted[user2])

    union = friends1 | friends2

    if len(union) == 0:
        return 0

    intersection = friends1 & friends2

    return len(intersection) / len(union)


def suggest_connections(network, username):
    accepted = network["accepted"]

    if username not in accepted:
        return []

    existing = set(accepted[username])

    # Exclude users with pending requests in either direction
    pending_users = set()

    for request in network["pending"]:
        if request["sender"] == username:
            pending_users.add(request["receiver"])
        elif request["receiver"] == username:
            pending_users.add(request["sender"])

    suggestions = []

    for candidate in accepted:
        if candidate == username:
            continue

        if candidate in existing or candidate in pending_users:
            continue

        score = jaccard_score(network, username, candidate)

        if score > 0:
            suggestions.append((candidate, score))

    suggestions.sort(key=lambda item: item[1], reverse=True)

    return suggestions
#BFS

def shortest_path(network, start, destination):
    accepted = network["accepted"]

    if start not in accepted or destination not in accepted:
        return None

    queue = deque([[start]])
    visited = {start}

    while queue:
        path = queue.popleft()
        current = path[-1]

        if current == destination:
            return path

        for neighbour in accepted[current]:
            if neighbour not in visited:
                visited.add(neighbour)
                queue.append(path + [neighbour])

    return None


def connection_degree(network, user1, user2):
    path = shortest_path(network, user1, user2)

    if path is None:
        return None

    return len(path) - 1


