# TODO: a better abstraction would be subroutines via TMs
# these could still be generated dynamically, like the super transitions
# but would support composing multiple TMs more naturally
# I used super transitions as the fastest way to get a working UTM for my course project

from tm import TM, Transition, RIGHT, LEFT
from parser import load_from_xml
import random

class SuperTransition:
    def __init__(self, state_to, prefix=None):
        self.state_to = state_to
        self.prefix = prefix or str(random.randint(0, 1000000))

    def assemble(self):
        # return a dictionary of transitons and the name of the first state
        raise NotImplementedError("This method should be implemented in subclasses")
    
class TwoToFourSymbolExpansion(SuperTransition):
    """
    Encodes 1-bit symbols into 2-bit encoded symbols on the tape.
    Assumptions about tape when this is used:
        - Head starts at the leftmost '1' (nonempty) symbol
        - When '00' is reached, the rest of the tape on the right is empty
        - After converting the tape, repositions head to the leftmost '1' and transitions to the return state
        - '1' -> '11'
        - '0' -> '01' (note that because we assume the tape starts with a '1', the leftmost encoded symbol will be '11')
    """
    def __init__(self, state_to, prefix='2to4_'):
        super().__init__(state_to, prefix)
        self.return_state = state_to  # alias for clarity

    def assemble(self):
        # we already have this subroutine developed as an XML file
        # that considers '1' to be the start state and '0' to be the end state
        tm = load_from_xml("subroutines/two_to_four_symbol_expansion.xml")

        # add prefix to all internal states and move transitions to the '0' (end) state to go to the return state
        new_transitions = {}
        for state_from, transitions in tm.transitions.items():
            new_transitions[self.prefix + state_from] = {}
            for symbol, transition in transitions.items():
                if transition.state_to == '0':
                    new_transitions[self.prefix + state_from][symbol] = Transition(self.return_state, transition.symbol_to_write, transition.direction)
                else:
                    new_transitions[self.prefix + state_from][symbol] = Transition(self.prefix + transition.state_to, transition.symbol_to_write, transition.direction)

        return new_transitions, self.prefix + '1'
    
class FourToTwoSymbolDecode(SuperTransition):
    """
    Decodes 2-bit symbols into 1-bit symbols on the tape.
    Assumptions:
        - Head starts at the leftmost '1' (nonempty) symbol
        - When '00' is reached, the rest of the tape on the right is empty
        - After converting the tape, repositions head to the leftmost '1' and transitions to the return state
        - '11' -> '1'
        - '01' -> '0'
        - '10' -> invalid @
        - '00' -> invalid #
    """
    def __init__(self, state_to, prefix='4to2_'):
        super().__init__(state_to, prefix)
        self.return_state = state_to  # alias for clarity

    def assemble(self):
        # we already have this subroutine developed as an XML file
        # that considers '1' to be the start state and '0' to be the end state
        tm = load_from_xml("subroutines/four_to_two_symbol_decode.xml")

        # add prefix to all internal states and move transitions to the '0' (end) state to go to the return state
        new_transitions = {}
        for state_from, transitions in tm.transitions.items():
            new_transitions[self.prefix + state_from] = {}
            for symbol, transition in transitions.items():
                if transition.state_to == '0':
                    new_transitions[self.prefix + state_from][symbol] = Transition(self.return_state, transition.symbol_to_write, transition.direction)
                else:
                    new_transitions[self.prefix + state_from][symbol] = Transition(self.prefix + transition.state_to, transition.symbol_to_write, transition.direction)
        return new_transitions, self.prefix + '1'
    

class MoveUntil(SuperTransition):
    """
    Moves in the specified direction until a specific symbol is found.
    overshoot -1 <= x <= 1 is the number of cells to continue moving in the same direction after the target symbol is found.
    (if overshoot is 0, the head will stop at the target symbol, if -1 it will stop just before the symbol, 1 it will stop just after the symbol)
    """
    def __init__(self, state_to, target_symbol, direction, overshoot=0, prefix=None, all_symbols=('0', '1', '#', '@')):
        if direction != RIGHT and direction != LEFT:
            raise ValueError("direction must be either RIGHT or LEFT")
        if abs(overshoot) > 1:
            raise ValueError("overshoot must be -1, 0, or 1")
        super().__init__(state_to, prefix)
        self.target_symbol = target_symbol
        self.direction = direction
        self.overshoot = overshoot
        self.all_symbols = all_symbols

    def assemble(self):
        transitions = {
            self.state_to: {},
            self.prefix + '1' : {},
        }
        for symbol in self.all_symbols:
            if symbol == self.target_symbol:
                continue
            transitions[self.prefix + '1'][symbol] = Transition(self.prefix + '1', symbol, self.direction)

        reverse_direction = LEFT if self.direction == RIGHT else RIGHT

        if self.overshoot == -1:
            transitions[self.prefix + '1'][self.target_symbol] = Transition(self.state_to, self.target_symbol, reverse_direction)
        elif self.overshoot == 1:
            transitions[self.prefix + '1'][self.target_symbol] = Transition(self.state_to, self.target_symbol, self.direction)
        elif self.overshoot == 0:
            transitions[self.prefix + '1'][self.target_symbol] = Transition(self.state_to, None, None)
        else:
            raise Exception("Invalid overshoot value")
        
        return transitions, self.prefix + '1'
    
class MoveUntilRepeat(SuperTransition):
    """
    Move in specified direction until target symbol is seen n times. When n=1, this is equivalent to MoveUntil with overshoot=0.
    The n occurances of the target symbol need not be consecutive.
    """
    def __init__(self, state_to, target_symbol, n, direction, prefix=None, all_symbols=('0', '1', '#', '@')):
        if direction != RIGHT and direction != LEFT:
            raise ValueError("direction must be either RIGHT or LEFT")
        if n < 1:
            raise ValueError("n must be greater than 0")
        super().__init__(state_to, prefix)
        self.target_symbol = target_symbol
        self.direction = direction
        self.n = n
        self.all_symbols = all_symbols

    def assemble(self):
        transitions = {
            self.state_to: {},
        }
        for i in range(1, self.n+1):
            transitions[self.prefix + str(i)] = {}
            for symbol in self.all_symbols:
                if i == self.n:
                    transitions[self.prefix + str(i)][symbol] = MoveUntil(self.state_to, self.target_symbol, self.direction, overshoot=0, prefix=self.prefix + str(i) + '_', all_symbols=self.all_symbols)
                else:
                    transitions[self.prefix + str(i)][symbol] = MoveUntil(self.prefix + str(i + 1), self.target_symbol, self.direction, overshoot=1, prefix=self.prefix + str(i) + '_', all_symbols=self.all_symbols)
        
        # assembler output cannot contain supertransitions
        from compiler import compile_super_transitions
        tmp = TM(transitions, self.prefix + '1')
        tmp = compile_super_transitions(tmp)

        return tmp.transitions, tmp.state
            
class MoveFixed(SuperTransition):
    """
    Moves a fixed number of cells in the specified direction.
    """
    def __init__(self, state_to, distance, direction, prefix=None, all_symbols=('0', '1', '#', '@')):
        if direction != RIGHT and direction != LEFT:
            raise ValueError("direction must be either RIGHT or LEFT")
        if distance < 1:
            raise ValueError("distance must be greater than 0")
        super().__init__(state_to, prefix)
        self.distance = distance
        self.direction = direction
        self.all_symbols = all_symbols

    def assemble(self):
        transitions = {}
        
        for i in range(1, self.distance+1):
            transitions[self.prefix + str(i)] = {}
            for symbol in self.all_symbols:
                if i == self.distance:
                    transitions[self.prefix + str(i)][symbol] = Transition(self.state_to, symbol, self.direction)
                else:
                    transitions[self.prefix + str(i)][symbol] = Transition(self.prefix + str(i + 1), symbol, self.direction)
        
        return transitions, self.prefix + '1'
    
