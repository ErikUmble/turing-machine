

def get_state_id_map(tm):
    """
    Returns a dictionary mapping state names to unique integer IDs.
    """
    state_id_map = {}
    state_id_map[tm.state] = '1'
    counter = 2
    for state_id in tm.transitions.keys():
        if state_id not in state_id_map:
            state_id_map[state_id] = str(counter)
            counter += 1
    return state_id_map