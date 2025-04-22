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
    num_states = len(tm.transitions)

    utm_input = ['1' for i in range(num_states)] + ['0']
    for i in range(1, num_states):
        state_transitions = tm.transitions[str(i)]
        for symbol in ('0', '1'):
            utm_input += action_of_transition(state_transitions[symbol]) + ['0']
            utm_input += ['1'] * (int(state_transitions[symbol].state_to) + 1) + ['0']

    utm_input += tm.tape
    return utm_input

def get_utm(four_symbol_mode=False):
    """
    Returns a TM instance that acts as a Universal Turing Machine.
    four_symbol_mode: if True, this uses '0', '1', '@', and '#' as the symbols on the tape; if false, this uses only '0' and '1' (after compiling)
    """
    preprocess = {
        # encode the tape to 4-symbol
        '1': {
            # this requires there to be at least one '1' on the input, and it makes sense to just halt if that is not the case
            '1': TwoToFourSymbolExpansion('2'),
        }
    }
    core = {
    # insert '#' in between memory segments and initialize '@' to left part of each region
        # move left two times, add '#@'
        '2': {
            '1': MoveFixed('3', 2, LEFT, prefix="mf1_"),
        },
        '3': {
            '0': Transition('4', '#', RIGHT),
            '#': Transition('4', '#', RIGHT),  # handle empty tape interpreted as '#'
        },
        '4': {
            '0': Transition('append_zero', '@', None),
            '#': Transition('append_zero', '@', None),  # handle empty tape interpreted as '#'
        },
        # in case the initial user tape is empty, we need to add a '0' to start it for the state desc segment to function properly
        'append_zero': {
            '@': MoveUntil('append_zero', '#', RIGHT),
            '#': Transition('append_zero', '0', None),
            '0': MoveUntil('5', '@', LEFT, overshoot=-1)
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
            '#': Transition('done_shifting', '@', None)
        },
        'shift_input_right_saw1': {
            # enter this state while on the first '1' of the input ('#' to the left)
            '0': Transition('shift_input_right_saw0', '1', RIGHT),
            '#': Transition('shift_input_right_saw0', '1', RIGHT), # handle empty tape interpreted as '#'
            '1': Transition('shift_input_right_saw1', '1', RIGHT),
        },
        'shift_input_right_saw0': {
            # enter this state while on the first '1' of the input ('#' to the left)
            '0': Transition('done_shifting', '0', None),
            '#': Transition('done_shifting', '0', None), # handle empty tape interpreted as '#'
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
            '1': Transition('sim_loop', '@', LEFT),
        },
    # main simulation loop
        'sim_loop': {
            # enter this state while at the '#' just left of the state index memory segment
            # ensure that the state index counter is reset and that the state description pointer is at the start of the current state description
            # this will "sanity check" that state index counter is reset
            '#': Transition('sim_loop', None, RIGHT),
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
            '#': MoveUntilRepeat('parse_action', '@', 2, LEFT),  # at the right end of known user tape, the '00' is interpreted as '#' but we want it to be treated as a '0' instead
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
            '0': MoveUntil('handle_move_left_action', '@', RIGHT, overshoot=-1),
            '1': MoveUntil('handle_move_right_action', '@', RIGHT, overshoot=1),
        },
        'handle_write_0_action' : {
            # enter this state either at or just right of the user tape pointer
            '@': Transition('handle_write_0_action', None, RIGHT),
            '1': Transition('action_done', '0', None),
            '0': Transition('action_done', '0', None),
            '#': Transition('action_done', '0', None),  # handle empty tape interpreted as '#'
        },
        'handle_write_1_action' : {
            # enter this state either at or just right of the user tape pointer
            '@': Transition('handle_write_1_action', None, RIGHT),
            '1': Transition('action_done', '1', None),
            '0': Transition('action_done', '1', None),
            '#': Transition('action_done', '1', None),  # handle empty tape interpreted as '#'
        },
        'handle_move_left_action' : {
            # enter this state just left of the user tape pointer
            '#': Transition('move_out_of_bounds', None, None), # cannot move left past the user tape boundary (treat this as a program crash / termination)
            '1': Transition('handle_move_left_action_saw1', '@', RIGHT),
            '0': Transition('handle_move_left_action_saw0', '@', RIGHT),
        },
        'move_out_of_bounds' : {
            # for now, handle this as a program crash; remove the state desc pointer and go to the halt/cleanup state
            # we could change this to shift the tape contents right by one and then move back to the leftmost position of the tape
            '#': MoveUntil('move_out_of_bounds', '@', LEFT),
            '@': Transition('move_out_of_bounds', '0', None),
            '0': Transition('program_halt', None, None),
        },
        'handle_move_left_action_saw1' : {
            '@': Transition('action_done', '1', None)
        },
        'handle_move_left_action_saw0' : {
            '@': Transition('action_done', '0', None)
        },
        'handle_move_right_action' : {
            # enter this state just right of the user tape pointer
            '#': Transition('handle_move_right_action_saw0', '@', LEFT), # moving right past 'known' tape territory '00' interpreted as '#' but we want it to be '0' instead
            '1': Transition('handle_move_right_action_saw1', '@', LEFT),
            '0': Transition('handle_move_right_action_saw0', '@', LEFT),
        },
        'handle_move_right_action_saw1' : {
            '@': Transition('action_done', '1', None)
        },
        'handle_move_right_action_saw0' : {
            '@': Transition('action_done', '0', None)
        },
        # next step: determine which simulated state to transition to next
        'action_done': {
            # go to the state desc pointer
            '#': MoveUntil('action_done', '#', LEFT),
            '1': MoveUntil('action_done', '#', LEFT),
            '0': MoveUntil('action_done', '#', LEFT),
            '#': MoveUntil('get_next_state_desc', '@', LEFT),
        },
        'get_next_state_desc': {
            # enter this state at the '@' in the state description pointing to the action that was just taken
            '@': Transition('get_next_state_desc', '0', RIGHT),
            '1': MoveUntil('get_next_state_desc', '0', RIGHT),
            '0': MoveFixed('check_for_transition_to_halt', 2, RIGHT),  # since the q values are 1-indexed, skip the first one, which represents the 0 state, as the index counter is already at 0
        },
        'check_for_transition_to_halt' :{
            '0': Transition('program_halt', None, None),  # this simulated transition goes to the 0th state, which is the halt state
            '#': Transition('program_halt', None, LEFT),  # handle boundary of state desc segment (move left into the state desc segment)
            '1': Transition('try_increment_state_desc', None, RIGHT)  # normal situation: we can try incrementing to count up to the next state to get to (NOTE: we do the first increment as an extra here since the entire state desc segment skips the 0th state)
        },
        'try_increment_state_desc': {
            # enter this state at the state description pointer, which should be pointing at the current count of the next state to transition to
            '0': Transition('counter_at_next_state_idx', None, LEFT),  # we intentionally don't write the pointer here, because of the '#' boundary situation, and because we will just need to reset it to the left side of state desc in a moment
            '#': Transition('counter_at_next_state_idx', None, LEFT),  # we see this when we are at the end of the state desc segment
            '1': Transition('increment_state_idx', '@', LEFT),
            '@': Transition('try_increment_state_desc', '1', RIGHT),
        },
        'increment_state_idx': {
            '1': MoveUntil('increment_state_idx_2', '@', LEFT, overshoot=-1),
            '0': MoveUntil('increment_state_idx_2', '@', LEFT, overshoot=-1),
        },
        'increment_state_idx_2': {
            '1': Transition('increment_state_idx_2', '@', LEFT),
            '@': Transition('increment_state_idx_3', '1', RIGHT),
        },
        'increment_state_idx_3': {
            '@': MoveUntilRepeat('try_increment_state_desc', '@', 2, RIGHT),  # we are already at a '@' which means this technically just moves over to the next '@' which is the state desc pointer
        },
    # we need to position the state desc pointer to the start of the correct next state
    # we have already counted the number of states descs to skip through, in the state index counter
        'counter_at_next_state_idx': {
            # enter this state within the state desc segment, which should not have any '@' at the moment
            # we need to reset the '@'
            '1': MoveUntil('counter_at_next_state_idx', '#', LEFT, overshoot=-1),
            '0': Transition('counter_at_next_state_idx', '@', None),
            '@': MoveUntilRepeat('try_decrement_state_idx', '@', 2, LEFT),  # we are already at a '@' which means this technically just moves over to the next '@' which is the state idx pointer
        },
        'try_decrement_state_idx': {
            # enter this state at the state idx pointer
            '@': Transition('try_decrement_state_idx', '1', LEFT),
            '#': Transition('try_decrement_state_idx_oops_too_far', None, RIGHT),
            '1': Transition('try_decrement_state_idx_2', '@', None),
        },
        'try_decrement_state_idx_2': {
            '@': MoveUntilRepeat('skip_to_next_state_desc', '@', 2, RIGHT),  # we are already at a '@' which means this technically just moves over to the next '@' which is the state desc pointer
        },
        'try_decrement_state_idx_oops_too_far': {
            '#': Transition('try_decrement_state_idx_oops_too_far', None, RIGHT),
            '1': Transition('try_decrement_state_idx_oops_too_far', '@', None),
            '@': MoveUntil('sim_loop', '#', LEFT),  # move back to the '#' (really this is just a single left step, but more concise to write it like this) and then start the sim loop over
        },
        'skip_to_next_state_desc' : {
            # enter this state while at the '@' state desc pointer
            '@': Transition('skip_to_next_state_desc', '0', RIGHT),
            '1': MoveUntilRepeat('skip_to_next_state_desc', '0', 4, RIGHT),
            '0': Transition('skip_to_next_state_desc_2', '@', None)
        },
        'skip_to_next_state_desc_2': {
            '@': MoveUntilRepeat('try_decrement_state_idx', '@', 2, LEFT),  # we are already at a '@' which means this technically just moves over to the next '@' which is the state idx pointer
        },
    # when the simulated program halts, we need to clean up the simulation state before we can decode the result
        'program_halt' : {
            # enter this state while somewhere in the state desc segment
            # we start by going back to the left edge of the state index segment
            '1': MoveUntilRepeat('program_halt', '#', 2, LEFT),
            '0': MoveUntilRepeat('program_halt', '#', 2, LEFT),
            '@': MoveUntilRepeat('program_halt', '#', 2, LEFT), 
            '#': Transition('clean_state_idx', None, RIGHT),
        },
        # since '#' represented by "00", we clean up by overwriting with '#' to reset tape contents to '0's
        'clean_state_idx' : {
            '@': Transition('clean_state_idx', '#', RIGHT),
            '1': Transition('clean_state_idx', '#', RIGHT),
            '0': Transition('clean_state_idx', '#', RIGHT),
            '#': Transition('clean_state_desc', None, RIGHT),
        },
        'clean_state_desc' : {
            '@': Transition('clean_state_desc', '#', RIGHT),
            '1': Transition('clean_state_desc', '#', RIGHT),
            '0': Transition('clean_state_desc', '#', RIGHT),
            '#': Transition('clean_tape', None, RIGHT),
        },
        # to clean tape, we just need to shift everything before the '@' to the right by one and then move back to the start of the tape
        'clean_tape' : {
            '@': Transition('decode_tape', '#', RIGHT),  # simulated head was already at the leftmost position of the tape
            '1': Transition('clean_tape_saw1', '#', RIGHT),
            '0': Transition('clean_tape_clear_leading_0s', '#', RIGHT),  # we have to clear leading 0s for the postprocessing decode step to work
        },
        'clean_tape_clear_leading_0s': {
            '0': Transition('clean_tape_clear_leading_0s', '#', RIGHT),
            '1': Transition('clean_tape_saw1', '#', RIGHT),
            '@': Transition('decode_tape', '#', RIGHT),
        },
        'clean_tape_saw1' : {
            '@': Transition('done_clearning_tape', '1', None),
            '1': Transition('clean_tape_saw1', '1', RIGHT),
            '0': Transition('clean_tape_saw0', '1', RIGHT),
        },
        'clean_tape_saw0' : {
            '@': Transition('done_clearning_tape', '0', None),
            '1': Transition('clean_tape_saw1', '0', RIGHT),
            '0': Transition('clean_tape_saw0', '0', RIGHT),
        },
        'done_clearning_tape' : {
            '1': MoveUntil('decode_tape', '#', LEFT, overshoot=-1),
            '0': MoveUntil('decode_tape', '#', LEFT, overshoot=-1),
        },
        'decode_tape': {}
    }
    postprocess = {
        'decode_tape': {
            '1': FourToTwoSymbolDecode('0', '4to2_')
        },
        '0': {}
    }

    if four_symbol_mode:
        core = compile_super_transitions(TM(transitions=core))
        transitions = core.transitions
        utm = TM(transitions=transitions, start_state='2', empty_symbol='#')  # use '#' as the empty symbol to better simulate the behavior of two_symbol_mode that uses '0' as empty symbol
        return utm

    # compile
    preprocess = compile_super_transitions(TM(transitions=preprocess))
    core = compile_super_transitions(TM(transitions=core))
    core = four_to_two_symbols(core)
    postprocess = compile_super_transitions(TM(transitions=postprocess))
    transitions = compose_transitions(compose_transitions(preprocess.transitions, core.transitions), postprocess.transitions)
    utm = TM(transitions=transitions, start_state='1')
    utm = remove_null_transitions(utm)
    return utm
    

if __name__ == "__main__":
    """
    Run the UTM on an input
    usage: python utm.py <input>
    """
    import sys

    initial_tape = sys.argv[1].strip()
    initial_tape = [c for c in initial_tape]

    tm = get_utm(debug=False)
    tm.set_tape(initial_tape)
    tm.draw(max_tape_length=50)
    tm.run()
    tm.draw(max_tape_length=50)
    print(''.join(tm.tape[tm.head_idx:]))