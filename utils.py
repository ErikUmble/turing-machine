

def get_state_id_map(tm):
    """
    Returns a dictionary mapping state names to unique integer IDs.
    Convention: start state maps to '1'.
    If '0' is already a state and is a halt state (no transitions) it will stay '0'.
    """
    state_id_map = {}
    state_id_map[tm.state] = '1'
    if '0' in tm.transitions and len(tm.transitions['0']) == 0:
        state_id_map['0'] = '0'
    counter = 2
    for state_id in tm.transitions.keys():
        if state_id not in state_id_map:
            state_id_map[state_id] = str(counter)
            counter += 1
    return state_id_map