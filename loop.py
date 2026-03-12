def create_loop_state():
    return {
        "loop": 1
    }


def advance_loop(player, loop_state):
    loop_state["loop"] += 1
    player["sanidade"] = max(3, 7 - loop_state["loop"])


def register_death(player, loop_state):
    player["mortes"] += 1
    advance_loop(player, loop_state)