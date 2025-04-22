from tm import TM, Transition, HaltException
from parser import load_from_xml, save_to_xml
from subroutine import *
from compiler import *
from utm import *

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
    assert save_to_xml(tm, "examples/shift_right_tm(1).xml")

    # check that symbols other than '0' and '1' are not allowed
    tm.transitions['1']['0'].symbol_to_write = '2'
    try:
        save_to_xml(tm, "examples/shift_right_tm_copy.xml")
    except ValueError as e:
        assert "TM uses invalid symbols" in str(e)


def test_two_to_four_symbol_expansion():
    transitions, entry_state = TwoToFourSymbolExpansion('0', '2to4_').assemble()
    transitions['0'] = {}
    tm = TM(transitions, entry_state, tape=['1', '0', '1'], head_idx=0)
    tm.draw()
    tm.run()
    tm.draw(max_tape_length=70)
    assert '110111' in ''.join(tm.tape)

def test_two_to_four_symbol_expansion2():
    preprocess = {
        # encode the tape to 4-symbol
        '1': {
            '1': TwoToFourSymbolExpansion('0'),
        }
    }
    tm = compile_super_transitions(TM(preprocess, tape=[c for c in '110110101111011011101111'], head_idx=0))
    tm.draw(max_tape_length=70)
    tm.run()
    tm.draw(max_tape_length=70)

def test_four_to_two_symbol_expansion():
    transitions, entry_state = FourToTwoSymbolDecode('0', '4to2_').assemble()
    transitions['0'] = {}
    tm = TM(transitions, entry_state, tape=['1', '1', '0', '1', '1', '1'], head_idx=0)
    tm.draw()
    tm.run()
    tm.draw()
    assert '101' in ''.join(tm.tape)


def test_quintuple_to_quadruple():
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
    new_tm = quintuple_to_quadruple(tm)
    
    print(new_tm)


def test_move_until():
    tape = ['#', '0', '0', '0', '#', '1', '0', '1', '#', '0', '0']
    transitions = {
        '1' : {
            '#': Transition('1', None, RIGHT),
            '0': MoveUntil('2', '#', RIGHT, overshoot=1, prefix='nextHash_'),
            '1': MoveUntil('2', '#', RIGHT, overshoot=1, prefix='nextHash_'),
        },
        '2' : {
            '1': MoveUntil('3', '#', RIGHT, overshoot=0, prefix='nextHash2_'),
            '#': Transition('3', None, LEFT),
        },
        '3' : {}
    }
    tm = TM(transitions=transitions, start_state='1', tape=tape, head_idx=0, empty_symbol='0')
    tm = compile_super_transitions(tm)
    tm.draw()
    tm.run()
    tm.draw()

def test_construct_utm_input():
    transitions = {
        '0': {},
        '1': {
            '0': Transition('2', '1', None),
            '1': Transition('1', None, RIGHT)
        },
        '2': {
            '0': Transition('0', None, LEFT),
            '1': Transition('0', '1', None)
        }
    }
    tape = ['1', '0', '1']
    tm = TM(transitions=transitions, start_state='1', tape=tape, head_idx=0, empty_symbol='0')
    utm_input = construct_utm_input(tm)
    assert ''.join(utm_input) == "111011011101111011011101011010101"

def test_simple_utm_input():
    target = load_from_xml("examples/simple2_tm.xml")
    target.set_tape(['1', '1', '1', '0', '1', '1'])
    print(''.join(construct_utm_input(target)))

def test_utm():
    # verify that the in-memory UTM works as a UTM
    target = load_from_xml("examples/add_tm.xml")
    target.set_tape(['1', '1', '1', '0', '1', '1'])  # 2 + 1
    utm_input = construct_utm_input(target)
    utm = get_utm()
    utm.set_tape(utm_input)   
    utm.run()

    assert "1111" == (''.join(utm.tape)).strip('0')

def test_utm_file():
    # verify that the saved UTM file produces a TM that works as a UTM
    target = load_from_xml("examples/shift_copy_tm.xml")
    target.set_tape(['1', '1', '1'])
    utm_input = construct_utm_input(target)
    utm = load_from_xml("utm.xml")
    utm.set_tape(utm_input)   
    utm.run()
    assert "1110111" == (''.join(utm.tape)).strip('0')


def test_compile_four_to_two_symbols():
    transitions = {
        '0': {},
        '1': {
            '1': MoveUntilRepeat('2', '0', 4, RIGHT),
        },
        '2': {
            '0': Transition('0', '#', RIGHT)
        }
    }
    
    tm = TM(transitions=transitions, start_state='1', tape=['1', '1', '0', '1', '1', '1', '0', '1', '1', '1', '0', '1', '1', '1', '0', '1', '1', '1', '0', '1'], head_idx=0, empty_symbol='0')
    tm = compile_super_transitions(tm)
    tm = four_to_two_symbols(tm)
    tm.draw()
    tm.run()
    tm.draw()
    assert '11011101110111001101' == ''.join(tm.tape)
    assert tm.head_idx == 16

def test_remove_null_transitions():
    transitions = {
        '1': {
            '0': Transition('2', '1', None),
            '1': Transition('1', None, RIGHT)
        },
        '2': {
            '0': Transition('0', None, LEFT),
            '1': Transition('0', '1', None)
        }
    }
    tm = TM(transitions=transitions, start_state='1', tape=['1', '0', '1'], head_idx=0, empty_symbol='0')
    tm = remove_null_transitions(tm)
    print(tm)


if __name__ == "__main__":
    test_tm_methods()
    test_draw()
    test_load_xml()
    test_save_to_xml()
    test_two_to_four_symbol_expansion2()
    test_four_to_two_symbol_expansion()
    test_quintuple_to_quadruple()
    test_move_until()
    test_construct_utm_input()
    test_utm()
    test_utm_file()
    test_compile_four_to_two_symbols()
    test_remove_null_transitions()
    test_simple_utm_input()
    print("All tests passed!")