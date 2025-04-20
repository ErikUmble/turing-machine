from tm import TM, Transition, HaltException
from parser import load_from_xml, save_to_xml
from subroutine import two_to_four_symbol_tape_expansion, four_to_two_symbol_tape_decode

def test_tm_methods():
    # Test the TM class with a simple transition function
    transitions = {
        '1': {
            '0': Transition('2', '1', 'R'),
            '1': Transition('1', '0', 'L')
        },
        '2': {
            '0': Transition('H', '0', 'R'),
            '1': Transition('H', '1', 'R')
        }
    }
    
    tm = TM(transitions=transitions, start_state='1', tape=['0', '1', '0'], head_idx=0, empty_symbol='0')
        
    # Test the initial state
    assert tm.state == '1'
    assert tm.read() == '0'
    
    # Test the transition function
    tm.step()
    assert tm.state == '2'
    assert tm.read() == '1'
    
    # Test writing to the tape
    tm.write('X')
    assert tm.read() == 'X'
    
    # Test moving the head
    current_head = tm.head_idx
    tm.move_right()
    assert tm.head_idx == current_head + 1


def test_draw():
    tape=['0', '1', '2', '3', '4', '5', '6' ,'7', '8', '9']
    TM(transitions=None, start_state='1', tape=tape, head_idx=0).draw()

    TM(transitions=None, start_state='1', tape=tape, head_idx=0).draw(max_tape_length=5)

    TM(transitions=None, start_state='1', tape=tape, head_idx=7).draw(max_tape_length=5)


def test_load_xml():
    filepath = "examples/shift_right_tm.xml"
    tm = load_from_xml(filepath)
    tm.set_tape(['1', '1', '0', '1'])
    tm.draw()
    tm.run()
    tm.draw()

    # should shift right by 2 cells and set head at leftmost 1
    assert tm.tape == ['0', '0', '1', '1', '0', '1']
    assert tm.head_idx == 2

def test_save_to_xml():
    tm = load_from_xml("examples/shift_right_tm.xml")
    assert save_to_xml(tm, "examples/shift_right_tm_copy.xml")

    # check that symbols other than '0' and '1' are not allowed
    tm.transitions['1']['0'].symbol_to_write = '2'
    try:
        save_to_xml(tm, "examples/shift_right_tm_copy.xml")
    except ValueError as e:
        assert "TM uses invalid symbols" in str(e)


def test_two_to_four_symbol_expansion():
    transitions, entry_state = two_to_four_symbol_tape_expansion('0', '2to4_')
    transitions['0'] = {}
    tm = TM(transitions, entry_state, tape=['1', '0', '1'], head_idx=0)
    tm.draw()
    tm.run()
    tm.draw()
    assert '110111' in ''.join(tm.tape)

def test_four_to_two_symbol_expansion():
    transitions, entry_state = four_to_two_symbol_tape_decode('0', '4to2_')
    transitions['0'] = {}
    tm = TM(transitions, entry_state, tape=['1', '1', '0', '1', '1', '1'], head_idx=0)
    tm.draw()
    tm.run()
    tm.draw()
    assert '101' in ''.join(tm.tape)

if __name__ == "__main__":
    test_tm_methods()
    test_draw()
    test_load_xml()
    test_save_to_xml()
    test_two_to_four_symbol_expansion()
    test_four_to_two_symbol_expansion()
    print("All tests passed!")