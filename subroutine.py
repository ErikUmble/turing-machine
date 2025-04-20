from tm import TM, Transition
from parser import load_from_xml


def shift_right(end='00', next_state='0', prefix='shr_'):
    """
    Returns a transitions map that shifts the tape to the right by one cell
    and returns to the leftmost '1'
    """
    pass


def two_to_four_symbol_tape_expansion(return_state, prefix='2to4_'):
    """
    Returns a transitions map, first_state for a TM subroutine that encodes 1-bit symbols into 2-bit encoded symbols on the tape.
    Assumptions:
        - Head starts at the leftmost '1' (nonempty) symbol
        - When '00' is reached, the rest of the tape on the right is empty
        - After converting the tape, repositions head to the leftmost '1' and transitions to the return state
        - '1' -> '11'
        - '0' -> '01' (note that because we assume the tape starts with a '1', the leftmost encoded symbol will be '11')
    """
    # we already have this subroutine developed as an XML file
    # that considers '1' to be the start state and '0' to be the end state
    tm = load_from_xml("examples/two_to_four_symbol_expansion.xml")

    # add prefix to all internal states and move transitions to the '0' (end) state to go to the return state
    new_transitions = {}
    for state_from, transitions in tm.transitions.items():
        new_transitions[prefix + state_from] = {}
        for symbol, transition in transitions.items():
            if transition.state_to == '0':
                new_transitions[prefix + state_from][symbol] = Transition(return_state, transition.symbol_to_write, transition.direction)
            else:
                new_transitions[prefix + state_from][symbol] = Transition(prefix + transition.state_to, transition.symbol_to_write, transition.direction)

    return new_transitions, prefix + '1'


def four_to_two_symbol_tape_decode(return_state, prefix='4to2_'):
    """
    Returns a transitions map, first_state for a TM subroutine that decodes 2-bit symbols into 1-bit symbols on the tape.
    Assumptions:
        - Head starts at the leftmost '1' (nonempty) symbol
        - When '00' is reached, the rest of the tape on the right is empty
        - After converting the tape, repositions head to the leftmost '1' and transitions to the return state
        - '11' -> '1'
        - '01' -> '0'
        - '10' -> invalid
        - '00' -> invalid
    """
    # we already have this subroutine developed as an XML file
    # that considers '1' to be the start state and '0' to be the end state
    tm = load_from_xml("examples/four_to_two_symbol_decode.xml")

    # add prefix to all internal states and move transitions to the '0' (end) state to go to the return state
    new_transitions = {}
    for state_from, transitions in tm.transitions.items():
        new_transitions[prefix + state_from] = {}
        for symbol, transition in transitions.items():
            if transition.state_to == '0':
                new_transitions[prefix + state_from][symbol] = Transition(return_state, transition.symbol_to_write, transition.direction)
            else:
                new_transitions[prefix + state_from][symbol] = Transition(prefix + transition.state_to, transition.symbol_to_write, transition.direction)
    return new_transitions, prefix + '1'