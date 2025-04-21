from tm import TM, Transition, LEFT, RIGHT
from subroutine import *
from compiler import *

def action_of_transition(transition : Transition):
    if transition.direction is not None and transition.symbol_to_write is not None:
        raise ValueError("Action must be quadruple formulation for simulation target")
    if transition.symbol_to_write == '0':
        return ['1']
    elif transition.symbol_to_write == '1':
        return ['1', '1']
    elif transition.direction == LEFT:
        return ['1', '1', '1']
    elif transition.direction == RIGHT:
        return ['1', '1', '1', '1']
    
    raise ValueError("Invalid transition: ", transition)


def construct_utm_input(tm):
    """
    convention: <num states n>0<a_1,0>0<q_1,0>0<a_1,1>0<q_1,1>0...<a_n,0>0<q_n,0>0<a_n,1>0<q_n,1>0[initial tape]
    where each <x> only contains '1's and [x] starts with a '1' if there are any '1's in it at all, and contains at most two successive '0's
    q_i,0 : the state id to go to when in the ith state and read a 0
    a_i,0 : the action to take when in the ith state and read a 0

    actions:
    - '1': write '0'
    - '11': write '1'
    - '111': move left
    - '1111': move right
    """
    tm = standardize_simulation_target(tm)
    print(tm)
    num_states = len(tm.transitions)

    utm_input = ['1' for i in range(num_states + 1)] + ['0']
    for i in range(1, num_states):
        state_transitions = tm.transitions[str(i)]
        for symbol in ('0', '1'):
            utm_input += action_of_transition(state_transitions[symbol]) + ['0']
            utm_input += ['1'] * (int(state_transitions[symbol].state_to) + 1) + ['0']

    utm_input += tm.tape
    return utm_input

def get_utm():
    transitions = {
        '0': {},
    # encode the tape to 4-symbol
        '1': {
            '1': TwoToFourSymbolExpansion('2')
        },
    # insert '#' in between memory segments and initialize '@' to left part of each region
        # move left two times, add '#@'
        '2': {
            '1': MoveFixed('3', 2, LEFT),
        },
        '3': {
            '0': Transition('4', '#', RIGHT),
        },
        '4': {
            '0': Transition('5', '@', RIGHT),
        },
        # change the last '1' of <num states n> to '#' and the following '0' to '@'
        # as we can use n-counting (rather than n+1 counting) for number of states
        '5': {
            '1': MoveUntil('6', '0', RIGHT, overshoot=-1),
        },
        '6': {
            '1': Transition('6', '#', RIGHT),
            '0': Transition('7', '@', None),
        },
        # use the num states as a counter to move the state pointer to the end of the state definitions

    }
    return TM(transitions=transitions, start_state='1', empty_symbol='0')
    