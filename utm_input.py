from utm import *
from parser import load_from_xml
import sys

if __name__ == "__main__":
    """
    Construct a UTM input tape from a Turing Machine XML file and an initial tape.
    Usage: python utm_input.py <machine xml filepath> <initial tape>
    """
    if len(sys.argv) != 3:
        print("Usage: python utm_input.py <machine xml filepath> <initial tape>")
        sys.exit(1)

    machine_file = sys.argv[1]
    initial_tape = sys.argv[2].strip()
    initial_tape = [c for c in initial_tape]

    if not set(initial_tape).issubset(set(["0", "1"])):
        print("Initial tape must only contain 0s and 1s")
        sys.exit(1)

    tm = load_from_xml(machine_file)
    tm.set_tape(initial_tape)
    print(''.join(construct_utm_input(tm)))