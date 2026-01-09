# app/shared/protocols.py

"""
Shared protocol definitions between client & server """

SOCKET_EVENTS = {
    #connection events
    "CONNECT":    "connect",
    "DISCONNECT": "disconnect",

    #client -> server
    "CREATE_GAME": "create_game",
    "JOIN_GAME":   "join_game",
    "LEAVE_GAME":  "leave_game",
    "MAKE_MOVE":   "make_move",
    "SEND_MESSAGE": "send_message",  # send message

    #server -> client
    "GAME_CREATED":  "game_created",
    "PLAYER_JOINED": "player_joined",
    "GAME_UPDATE":   "game_update",
    "GAME_TIMER":    "game_timer",
    "GAME_OVER":     "game_over",
    "NEW_MESSAGE":   "new_message",  # receive new message
    "FRIEND_REQUEST": "friend_request"  #receive friend request
}

#REST endpoints
LOGIN_ENDPOINT           = "/login"
REGISTER_ENDPOINT        = "/register"
PUZZLES_ENDPOINT         = "/puzzles"
PUZZLE_ENDPOINT          = "/puzzle/{puzzle_id}"
PUZZLE_ENDPOINT_FMT      = PUZZLE_ENDPOINT    # for .format(puzzle_id=…)
ADD_PUZZLE               = "/puzzle"
ADD_PUZZLE_ENDPOINT      = ADD_PUZZLE  #backward compatibility
SUBMIT_RESULT_ENDPOINT   = "/submit_result"
STATS_ENDPOINT           = "/stats/{username}"
STATS_ENDPOINT_FMT       = STATS_ENDPOINT     # for .formatusername
GAMES_ENDPOINT           = "/games"
SUBMIT_RESULT            = SUBMIT_RESULT_ENDPOINT 

# Social feature API endpoints
SEARCH_USERS_ENDPOINT    = "/users/search"
FRIEND_REQUEST_ENDPOINT  = "/friends/request"
ACCEPT_FRIEND_ENDPOINT   = "/friends/accept"
REJECT_FRIEND_ENDPOINT   = "/friends/reject"  #reject friend request endpoint
FRIENDS_LIST_ENDPOINT    = "/friends"
MESSAGES_ENDPOINT        = "/messages/{username}"
MESSAGES_ENDPOINT_FMT    = MESSAGES_ENDPOINT  # for .format(username=…)
SEND_MESSAGE_ENDPOINT    = "/messages/send"
UNREAD_COUNT_ENDPOINT    = "/messages/unread"
ACTIVITY_ENDPOINT        = "/activity"


def create_game_message(puzzle_id, username):
    return {"puzzle_id": puzzle_id, "username": username}

def join_game_message(game_id, username):
    return {"game_id": game_id, "username": username}

# Social feature message formats
def friend_request_message(from_user, to_user):
    return {"from_user": from_user, "to_user": to_user}

def chat_message(sender, receiver, content):
    return {"sender": sender, "receiver": receiver, "content": content}
