from tm import TM, Transition, RIGHT, LEFT
from subroutine import SuperTransition
from utils import get_state_id_map

def n_to_2_symbols(tm):
    """
    Convert a Turing Machine that uses n symbols to one that uses only '0' and '1'.
    Note that this works by by expressing each symbol as a unique fixed-length binary string,
    so input tape symbols may need to be converted to the multiple-bit representation as well.
    Args:
        tm (TM): The original Turing Machine instance
    
    Returns:
        TM: A new Turing Machine instance with all transitions using only '0' and '1'
    """
    # get the symbols used
    symbols = set()
    for state, transitions in tm.transitions.items():
        for symbol in transitions.keys():
            symbols.add(symbol)

    # TODO: consider using a variable-length encoding scheme to handle skewed symbol distributions more efficiently
    symbol_map = {}
    # create a mapping of symbols to binary strings
    fixed_length = len(bin(len(symbols)-1)[2:])  # length of binary string needed
    for i, symbol in enumerate(symbols):
        binary_str = bin(i)[2:].zfill(fixed_length)
        symbol_map[symbol] = binary_str

    new_transitions = {}

    # convert each transition into a sequence of transitions
    for state_from, transitions in tm.transitions.items():
        new_transitions[state_from] = {}
        # read the full symbol that we are looking at by reading fixed_length bits starting with the current one
        for i in range(fixed_length):
            # create a new state for each bit in the binary string
            state_to = f"{state_from}_{i}"

        for symbol, transition in transitions.items():
            symbol_encoded = symbol_map[symbol]
            # create a sequence of transitions to write the binary string
            for i, bit in enumerate(binary_str):
                if i == 0:
                    new_transitions[state_from][bit] = Transition(transition.state_to, bit, transition.direction)
                else:
                    new_transitions[state_from][bit] = Transition(transition.state_to, bit, 'R')
    
    # TODO: finish
    
    return TM


def four_to_two_symbols(tm):
    """
    Hardcoded version of n_to_2_symbols for a Turing Machine that uses 4 symbols ('0', '1', '#', '@').
    This allows for certain optimizations.
    Convert a Turing Machine that uses 4 symbols ('0', '1', '#', '@') to one that uses only '0' and '1'.
    Args:
        tm (TM): The original Turing Machine instance
    
    Returns:
        TM: A new Turing Machine instance with all transitions using only '0' and '1'
    """
    symbol_map = {
        '0': '01',
        '1': '11',
        '#': '00',
        '@': '10'
    }
    new_transitions = {}
    for state_from, transitions in tm.transitions.items():

        # fork on first bit
        new_transitions[state_from] = {
            '0' : Transition(state_from + '_r0', '0', 'R'),
            '1' : Transition(state_from + '_r1', '1', 'R')
        }
        # fork on second bit (move left since we will have read the full symbol)
        new_transitions[state_from + '_r0'] = {
            '0' : Transition(state_from + '_r00', '0', 'L'),
            '1' : Transition(state_from + '_r01', '1', 'L')
        }
        new_transitions[state_from + '_r1'] = {
            '0' : Transition(state_from + '_r10', '0', 'L'),
            '1' : Transition(state_from + '_r11', '1', 'L')
        }

        # now state_from_00 represents the branch for reading symbol '0', state_from_01 for '1', state_from_10 for '#' and state_from_11 for '@'
        
        # next step is to write the new symbol
        for symbol, transition in transitions.items():
            symbol_en = symbol_map[symbol]
            # get the new symbol
            write_en = symbol_map[transition.symbol_to_write or symbol]

            new_transitions[state_from + '_r' + symbol_en] = {
                symbol_en[0]: Transition(state_from + '_r' + symbol_en + 'w0', write_en[0], 'R'),
            }
            # if the transition specifies a RIGHT move, then after we write the second bit, we move right and are done (can go to the transition's next state)
            if transition.direction == RIGHT:
                new_transitions[state_from + '_r' + symbol_en + 'w0'] = {
                    symbol_en[1]: Transition(transition.state_to, write_en[1], 'R'),
                }
            elif transition.direction == LEFT:
                # if left movement, we move left and need to move left twice more before we can go to the next state
                new_transitions[state_from + '_r' + symbol_en + 'w0'] = {
                    symbol_en[1]: Transition(state_from + '_r' + symbol_en + 'w1', write_en[1], 'L'),
                }
                # we just wrote this next bit, so only have to have one transition
                new_transitions[state_from + '_r' + symbol_en + 'w1'] = {
                    write_en[0]: Transition(state_from + '_r' + symbol_en + 'w1_L', None, 'L'),
                }
                # we don't know what the next bit is so add transition for either possibility
                new_transitions[state_from + '_r' + symbol_en + 'w1_L'] = {
                    '0': Transition(transition.state_to, None, 'L'),
                    '1': Transition(transition.state_to, None, 'L'),
                }
            else:
                # if no movement, we just have to backup
                new_transitions[state_from + '_r' + symbol_en + 'w0'] = {
                    symbol_en[1]: Transition(transition.state_to, write_en[1], 'L'),
                }
    return TM(transitions=new_transitions, start_state=tm.state, tape=tm.tape, head_idx=tm.head_idx, empty_symbol=tm.empty_symbol)

def quintuple_to_quadruple(tm):
    """
    Convert a Turing Machine that uses quintuple transitions to one that uses quadruple transitions.
    Each transition in the resulting machine will either move or will write a symbol but not both.
    Args:
        tm (TM): The original Turing Machine instance
    
    Returns:
        TM: A new Turing Machine instance with all transitions using quadruple transitions
    """
    new_transitions = {}
    for state_from, transitions in tm.transitions.items():
        new_transitions[state_from] = {}
        for symbol, transition in transitions.items():
            if transition.direction is None or transition.symbol_to_write is None:
                # if either the direction or symbol to write is None, we can just copy the transition
                new_transitions[state_from][symbol] = transition
                continue
            elif transition.symbol_to_write == symbol:
                # if the symbol to write is the same as the symbol we are reading, we can just use a move transition
                new_transitions[state_from][symbol] = Transition(transition.state_to, None, transition.direction)
                continue

            # otherwise, we need to create two transitions
            if state_from + '_w' not in new_transitions:
                new_transitions[state_from + '_w'] = {}
            new_transitions[state_from][symbol] = Transition(state_from + '_w', transition.symbol_to_write, None)
            new_transitions[state_from + '_w'][transition.symbol_to_write] = Transition(transition.state_to, None, transition.direction)

    return TM(transitions=new_transitions, start_state=tm.state, tape=tm.tape, head_idx=tm.head_idx, empty_symbol=tm.empty_symbol)
              

def standardize_simulation_target(tm):
    """
    Assumptions for UTM simulation target:
    - Quadruple transitions
    - '0' is halt state
    - '1' is the start state
    - if there are n non-halting states, then they are named '0', '1', '2', ..., 'n'
    - every transition is defined for symbols '0' and '1' except for the halt state, which has no transitons
    - Only uses right half of the tape

    It is up to the user to ensure the TM only uses the right half of the tape, but this compilation step handles the rest.
    """
    print(f"Warning: standardize_simulation_target has not been properly tested on nonstandard TMs yet")
    tm = compile_super_transitions(tm)
    tm = remove_null_transitions(tm)
    tm = quintuple_to_quadruple(tm)
    new_transitions = {
        '0': {},  # halt state
    }
    state_id_map = get_state_id_map(tm)
    for state_from, transitions in tm.transitions.items():
        state_id = state_id_map[state_from]
        
        new_transitions[state_id] = {}
        for symbol in ('0', '1'):
            transition = transitions.get(symbol)
            if transition is None:
                transition = Transition('0', symbol, None)
            else:
                transition.state_to = state_id_map[transition.state_to]

            new_transitions[state_id][symbol] = transition

    tm = TM(transitions=new_transitions, start_state='1', tape=tm.tape, head_idx=tm.head_idx, empty_symbol=tm.empty_symbol)
    #tm = remove_null_transitions(tm)
    #print(tm)
    return tm

def compose_transitions(t1, t2):
    """
    Merges two transition dictionaries into one, updating the first with the second, but not removing any nested keys of the first.
    """
    for state_from, transitions in t2.items():
        if state_from not in t1:
            t1[state_from] = {}
        for symbol, transition in transitions.items():
            t1[state_from][symbol] = transition
    return t1

def compile_super_transitions(tm):
    """
    Convert a Turing Machine that uses super transitions to one that uses normal transitions.
    """
    new_transitions = {}
    for state_from, transitions in tm.transitions.items():
        new_transitions[state_from] = {}
        for symbol, transition in transitions.items():
            if isinstance(transition, SuperTransition):
                # if the transition is a super transition, we need to assemble it
                sub_transitions, first_state = transition.assemble()
                new_transitions = compose_transitions(new_transitions, sub_transitions)
                new_transitions[state_from][symbol] = Transition(first_state, None, None)
            else:
                new_transitions[state_from][symbol] = transition

    return TM(transitions=new_transitions, start_state=tm.state, tape=tm.tape, head_idx=tm.head_idx, empty_symbol=tm.empty_symbol)

def remove_null_transitions(tm):
    """
    Removes transitions that do not write and do not move (by skipping the unnecessary intermediate state)
    """
    new_transitions = {}
    for state_from, transitions in tm.transitions.items():
        new_transitions[state_from] = {}
        for symbol, transition in transitions.items():
            if transition.symbol_to_write is None and transition.direction is None:  # TODO: can improve by using (transition.symbol_to_write is None or transition.symbol_to_write == symbol)
                # if the transition does not write or move, we can skip it
                #print(f"Removing null transition: {state_from} -> {symbol} -> {transition.state_to}")
                next_transition = tm.transitions[transition.state_to].get(symbol)
                while next_transition is not None and next_transition.symbol_to_write is None and next_transition.direction is None:
                    next_transition = tm.transitions[next_transition.state_to].get(symbol)
                if next_transition is None:
                    # remove this transition entirely if it leads to halt without doing anything
                    continue
                new_transitions[state_from][symbol] = next_transition
            else:
                new_transitions[state_from][symbol] = transition

    return TM(transitions=new_transitions, start_state=tm.state, tape=tm.tape, head_idx=tm.head_idx, empty_symbol=tm.empty_symbol)