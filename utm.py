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
    print("probably a bug in standardize_simulation_target")
    #tm = standardize_simulation_target(tm)
    #print(tm)
    num_states = len(tm.transitions)

    utm_input = ['1' for i in range(num_states)] + ['0']
    for i in range(1, num_states):
        state_transitions = tm.transitions[str(i)]
        for symbol in ('0', '1'):
            utm_input += action_of_transition(state_transitions[symbol]) + ['0']
            utm_input += ['1'] * (int(state_transitions[symbol].state_to) + 1) + ['0']

    utm_input += tm.tape
    return utm_input

def get_utm():
    preprocess = {
        # encode the tape to 4-symbol
        '1': TwoToFourSymbolExpansion('TODO')
    }
    transitions = {
        '0': {},
    # insert '#' in between memory segments and initialize '@' to left part of each region
        # move left two times, add '#@'
        '2': {
            '1': MoveFixed('3', 2, LEFT, prefix="mf1_"),
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
            '0': Transition('6', '@', LEFT),
            '#': MoveUntil('try_increment_state_idx', '@', LEFT, overshoot=-1),
        },
        # use the num states as a counter to move the state pointer to the end of the state definitions
        'try_increment_state_idx': {
            # enter this state just to the right of the '@' in state index segment
            '#': Transition('after_last_state', None, None),
            '1': Transition('try_increment_state_idx', '@', LEFT),
            '@': Transition('try_increment_state_idx_2', '1', RIGHT)
        },
        'try_increment_state_idx_2' : {
            '@': Transition('still_more_states', None, RIGHT)
        },
        'still_more_states': {
            '1': MoveUntil('advance_state_desc_ptr', '@', RIGHT),
            '#': MoveUntil('advance_state_desc_ptr', '@', RIGHT),
        },
        'advance_state_desc_ptr': {
            '@': Transition('advance_state_desc_ptr', '0', RIGHT),
            '1': MoveUntilRepeat('advance_state_desc_ptr', '0', 4, RIGHT),
            '0': Transition('advance_state_desc_ptr_2', '@', LEFT),
        },
        'advance_state_desc_ptr_2': {
            '1': MoveUntil('try_increment_state_idx', '@', LEFT, overshoot=-1),
        },
        'after_last_state': {
            # advance past the last state definition to insert '#' boundary
            '#': MoveUntil('after_last_state', '@', RIGHT),
            '@': Transition('shift_input_right', '#', RIGHT),
        },
    # shift input right by one to make space for '@' pointer
        'shift_input_right': {
            # enter this state while on the first '1' of the input ('#' to the left)
            '0': Transition('done_shifting', '@', None),
            '1': Transition('shift_input_right_saw1', '@', RIGHT),
        },
        'shift_input_right_saw1': {
            # enter this state while on the first '1' of the input ('#' to the left)
            '0': Transition('shift_input_right_saw0', '1', RIGHT),
            '1': Transition('shift_input_right_saw1', '1', RIGHT),
        },
        'shift_input_right_saw0': {
            # enter this state while on the first '1' of the input ('#' to the left)
            '0': Transition('done_shifting', '0', None),
            '1': Transition('shift_input_right_saw1', '0', RIGHT),
        },
    # finish initial preprocessing by re-inserting '@' pointer into state segment and reseting the state index counter
        'done_shifting': {
            '0': MoveUntil('done_shifting_2', '#', LEFT, overshoot=1),
            '1': MoveUntil('done_shifting_2', '#', LEFT, overshoot=1),
            '@': MoveUntil('done_shifting_2', '#', LEFT, overshoot=1),
            '#': Transition('done_shifting_2', None, LEFT),            
        },
        'done_shifting_2': {
            '1': MoveUntil('done_shifting_2', '#', LEFT, overshoot=-1),
            '0': Transition('done_shifting_2', '@', LEFT),
            '#': MoveUntil('done_shifting_3', '@', LEFT),
        },
        'done_shifting_3': {
            '@': Transition('done_shifting_3', '1', LEFT),
            '1': MoveUntil('done_shifting_4', '#', LEFT, overshoot=-1),
        },
        'done_shifting_4': {
            '1': Transition('sim_loop_1', '@', LEFT),
        },
    # main simulation loop
        'sim_loop_1': {
            # enter this state while at the '#' just left of the state index memory segment
            # ensure that the state index counter is reset and that the state description pointer is at the start of the current state description
            # this will "sanity check" that state index counter is reset
            '#': Transition('sim_loop_1', None, RIGHT),
            '@': Transition('read_tape_head_1', None, RIGHT),
            # we don't define transiton on '1', because '@' had better be just right of the '#'
        },
        'read_tape_head_1': {
            # go to the user tape pointer and then one step further
            '1': MoveUntil('read_tape_head_1', '#', RIGHT),
            '#': MoveUntilRepeat('read_tape_head_1', '@', 2, RIGHT),
            '@': Transition('read_tape_head_2', None, RIGHT),
        },
        'read_tape_head_2': {
            # if we see a '0' then state desc pointer is already at the right action
            '0': MoveUntilRepeat('parse_action', '@', 2, LEFT),
            '1': MoveUntilRepeat('read_a_one', '@', 2, LEFT),
        },
        'read_a_one': {
            '@': Transition('read_a_one', '0', RIGHT),
            '1': MoveUntilRepeat('read_a_one', '0',2, RIGHT),
            '0': Transition('parse_action', '@', RIGHT),
        },
        'parse_action': {
            # enter this state while at the first '1' (or the '@') of the correct action description based on current state and current read
            '@': Transition('parse_action', None, RIGHT),
            '1': Transition('parse_action_at_least_1', None, RIGHT)
        },
        'parse_action_at_least_1': {
            '0': MoveUntil('handle_write_0_action', '@', RIGHT, overshoot=1),
            '1': Transition('parse_action_at_least_2', None, RIGHT)
        },
        'parse_action_at_least_2': {
            '0': MoveUntil('handle_write_1_action', '@', RIGHT, overshoot=1),
            '1': Transition('parse_action_at_least_3', None, RIGHT)
        },
        'parse_action_at_least_3': {
            '0': MoveUntil('handle_move_left_action', '@', RIGHT, overshoot=0),
            '1': MoveUntil('handle_move_right_action', '@', RIGHT, overshoot=0),
        },
        'handle_write_0_action' : {},
        'handle_write_1_action' : {},
        'handle_move_left_action' : {},
        'handle_move_right_action' : {},
     
        

    }
    return TM(transitions=transitions, start_state='2', empty_symbol='0')
    