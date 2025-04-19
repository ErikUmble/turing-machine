import json

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
    def __init__(self):
        # format {state_name : {symbol: Transition}}
        self.transitions = {'0':{}, '1':{}}
        self.state = '1'
        # convention: head is at last item in r_tape
        # and r_tape is in reverse order (moving right means popping from the back)
        # both tapes are treated as stacks with the head at the top
        self.l_tape = TapeStack()
        self.r_tape = TapeStack()

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
        if transition:
            self.write(transition.symbol_to_write or symbol)  # write the same symbol if None write value specified in the transition
            if transition.direction == RIGHT:
                self.move_right()
            elif transition.direction == LEFT:
                self.move_left()
            self.state = transition.state_to
        else:
            raise HaltException(f"Transition not found for state {self.state} and symbol {symbol}")
        
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
        