from tm import TM, Transition, RIGHT, LEFT

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
        '0': '00',
        '1': '01',
        '#': '10',
        '@': '11'
    }
    new_transitions = {}
    for state_from, transitions in tm.transitions.items():

        # fork on first bit
        new_transitions[state_from] = {
            '0' : Transition(state_from + '_0', '0', 'R'),
            '1' : Transition(state_from + '_1', '1', 'R')
        }
        # fork on second bit (move left since we will have read the full symbol)
        new_transitions[state_from + '_0'] = {
            '0' : Transition(state_from + '_00', '0', 'L'),
            '1' : Transition(state_from + '_01', '1', 'L')
        }
        new_transitions[state_from + '_1'] = {
            '0' : Transition(state_from + '_10', '0', 'L'),
            '1' : Transition(state_from + '_11', '1', 'L')
        }

        # now state_from_00 represents the branch for reading symbol '0', state_from_01 for '1', state_from_10 for '#' and state_from_11 for '@'
        
        # next step is to write the new symbol
        for symbol, transition in transitions[state_from].items():
            symbol_en = symbol_map[symbol]
            # get the new symbol
            write_en = symbol_map[transition.symbol_to_write or symbol]

            new_transitions[state_from + '_' + symbol_en] = {
                symbol_en[0]: Transition(state_from + '_' + symbol_en + 'w0', write_en[0], 'R'),
            }
            # if the transition specifies a RIGHT move, then after we write the second bit, we move right and are done (can go to the transition's next state)
            if transition.direction == 'R':
                new_transitions[state_from + '_' + symbol_en + 'w0'] = {
                    symbol_en[1]: Transition(transition.state_to, write_en[1], 'R'),
                }
            else:
                # otherwise, we move left and need to move left twice more before we can go to the next state
                new_transitions[state_from + '_' + symbol_en + 'w0'] = {
                    symbol_en[1]: Transition(state_from + '_' + symbol_en + 'w1', write_en[1], 'L'),
                }
                # we just wrote this next bit, so only have to have one transition
                new_transitions[state_from + '_' + symbol_en + 'w1'] = {
                    write_en[0]: Transition(state_from + '_' + symbol_en + 'w1_L', write_en[0], 'L'),
                }
                # we don't know what the next bit is so add transition for either possibility
                new_transitions[state_from + '_' + symbol_en + 'w1_L'] = {
                    '0': Transition(transition.state_to, '0', 'L'),
                    '1': Transition(transition.state_to, '1', 'L'),
                }

        return TM(transitions=new_transitions, start_state=tm.start_state)
                