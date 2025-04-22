import json
import xml.etree.ElementTree as ET


RIGHT = 'R'
LEFT = 'L'

class HaltException(Exception):
    def __init__(self, message):
        super().__init__(message)

class TapeStack:
    def __init__(self, initial_contents=None, empty_symbol='0'):
        self.stack = initial_contents or []
        self.empty_symbol = empty_symbol

    def push(self, symbol):
        self.stack.append(symbol)

    def pop(self):
        if len(self.stack) > 0:
            return self.stack.pop()
        return self.empty_symbol

    def peek(self):
        if len(self.stack) > 0:
            return self.stack[-1]
        return self.empty_symbol
    
    def write(self, symbol):
        if len(self.stack) > 0:
            self.stack[-1] = symbol
        else:
            self.push(symbol)

    def __str__(self):
        return str(self.stack)

class Transition:
    def __init__(self, state_to, symbol_to_write, direction):
        self.state_to = state_to
        self.symbol_to_write = symbol_to_write
        self.direction = direction

    def __str__(self):
        return json.dumps({
            "s": self.state_to,
            "w": self.symbol_to_write,
            "m": self.direction
        })
    
    def load(self, data):
        self.state_to = data["s"]
        self.symbol_to_write = data["w"]
        self.direction = data["m"]

class TM:
    def __init__(self, transitions=None, start_state='1', tape=None, head_idx=0, empty_symbol='0'):
        """
        transitions: {state_name : {symbol: Transition}}
        start_state: initial state of the TM
        tape: initial tape contents [list of symbols]
        head_idx: index of the head in the tape (0 is the leftmost position in the initial tape)
        empty_symbol: symbol used to represent unspecified cells on the infinite tape
        """
        self.transitions = transitions or {'0':{}, '1':{}}
        self.state = start_state
        self.empty_symbol = empty_symbol

        self.set_tape(tape=tape, head_idx=head_idx)

    @property
    def tape(self):
        # return the tape as a list
        return self.l_tape.stack + self.r_tape.stack[::-1]
    
    @property
    def head_idx(self):
        # return the index of the head in the tape
        return len(self.l_tape.stack)
    
    def set_tape(self, tape=None, head_idx=0):
        # convention: head is at last item in r_tape
        # and r_tape is in reverse order (moving right means popping from the back)
        # both tapes are treated as stacks with the head at the top
        tape = tape or [self.empty_symbol,]
        r_stop = head_idx - 1 if head_idx > 0 else None

        self.l_tape = TapeStack(tape[:head_idx], self.empty_symbol)
        self.r_tape = TapeStack(tape[-1:r_stop:-1], self.empty_symbol)

    def move_right(self):
        # pop from the right tape
        symbol = self.r_tape.pop()
        # push to the left tape
        self.l_tape.push(symbol)

    def move_left(self):
        # pop from the left tape
        symbol = self.l_tape.pop()
        # push to the right tape
        self.r_tape.push(symbol)

    def write(self, symbol):
        # write to the right tape
        self.r_tape.write(symbol)

    def read(self):
        # read from the right tape
        return self.r_tape.peek()
    
    def step(self):
        symbol = self.read()
        transition = self.transitions[self.state].get(symbol)

        # TODO: could implement a "simulation" method on super transitions to support pre-compile
        from subroutine import SuperTransition
        if isinstance(transition, SuperTransition):
            raise Exception("Compile the TM to transform SuperTransitions before running")
        
        if transition:
            self.write(transition.symbol_to_write or symbol)  # write the same symbol if None write value specified in the transition
            if transition.direction == RIGHT:
                self.move_right()
            elif transition.direction == LEFT:
                self.move_left()
            self.state = transition.state_to
        else:
            raise HaltException(f"Transition not found for state {self.state} and symbol {symbol}")
        
    def run(self):
        while True:
            try:
                self.step()
            except HaltException:
                break
            except Exception as e:
                print(f"Error: {e}")
                self.draw(max_tape_length=70)
                break
        
    def __str__(self):
        return json.dumps({
            "state": self.state,
            "l_tape": str(self.l_tape),
            "r_tape": str(self.r_tape),
            "transitions": {state: {symbol: str(transition) for symbol, transition in transitions.items()} for state, transitions in self.transitions.items()}
        }, indent=4)
    
    def save(self, filepath):
        with open(filepath, 'w') as f:
            json.dump({
                "state": self.state,
                "l_tape": str(self.l_tape),
                "r_tape": str(self.r_tape),
                "transitions": {state: {symbol: str(transition) for symbol, transition in transitions.items()} for state, transitions in self.transitions.items()}
            }, f, indent=4)
    
    def load(self, filepath):
        with open(filepath, 'r') as f:
            data = json.load(f)
            self.state = data["state"]
            self.l_tape = TapeStack(data["l_tape"])
            self.r_tape = TapeStack(data["r_tape"])
            for state, transitions in data["transitions"].items():
                for symbol, transition in transitions.items():
                    t = Transition('', '', '')
                    t.load(json.loads(transition))
                    self.transitions[state][symbol] = t

    def draw(self, max_tape_length=20):
        # Draw the tape with the head position
        tape_contents = self.tape
        head_pos = self.head_idx
        if head_pos < max_tape_length // 2:
            tape_contents = tape_contents[:max_tape_length]
        elif len(self.tape) > max_tape_length:
            tape_contents = tape_contents[:head_pos + (max_tape_length // 2)]
            head_pos = max_tape_length - (len(tape_contents) - head_pos)
            tape_contents = tape_contents[-max_tape_length:]
        
        tape_str = '|'.join(tape_contents)
        head_str = ' ' * (head_pos * 2) + '^'
        border = '-' * (len(tape_str) + 1)
        print(f"State: {self.state}")
        print(border)
        print(tape_str)
        print(border)
        print(head_str)
        


if __name__ == "__main__":
    import sys
    from parser import load_from_xml
    tm_filepath = sys.argv[1]
    initial_tape = sys.argv[2].strip()
    initial_tape = [c for c in initial_tape]

    tm = load_from_xml(tm_filepath)
    tm.set_tape(initial_tape)
    tm.draw(max_tape_length=50)
    tm.run()
    tm.draw(max_tape_length=50)
    print(''.join(tm.tape[tm.head_idx:]))