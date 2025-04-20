import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import random


from utils import get_state_id_map
from tm import TM, Transition, TapeStack, LEFT, RIGHT


def load_from_xml(filepath):
    """
    Load a Turing Machine from an XML file from Turing Machine Simulator Application.
    
    Args:
        filepath (str): Path to the XML file
        empty_symbol (str): Symbol to use for empty cells
        
    Returns:
        TM: A Turing Machine instance initialized with the transitions from the XML
    """
    # Parse the XML file
    tree = ET.parse(filepath)
    root = tree.getroot()
    
    # Initialize transitions dictionary
    transitions = {}
    
    # Find the start state
    start_state = None
    for state_elem in root.findall(".//States/*"):
        tag = state_elem.tag
        state_id = tag.split('_')[1]  # Get state ID from tag (State_X)
        
        # Check if this is the start state
        start_state_elem = state_elem.find("startstate")
        if start_state_elem is not None and start_state_elem.text.lower() == "true":
            start_state = state_id
            
        # Initialize the state in the transitions dictionary
        if state_id not in transitions:
            transitions[state_id] = {}
    
    # Parse transitions
    for trans_elem in root.findall(".//Transitions/*"):
        from_state = trans_elem.find("fromstate").text
        to_state = trans_elem.find("tostate").text
        old_char = trans_elem.find("oldchar").text
        new_char = trans_elem.find("newchar").text
        
        # Direction in XML: 1 = LEFT, 2 = RIGHT
        direction_code = trans_elem.find("direction").text
        direction = LEFT if direction_code == "1" else RIGHT
        
        # Create a Transition object
        transition = Transition(to_state, new_char, direction)
        
        # Add the transition to the dictionary
        if from_state not in transitions:
            transitions[from_state] = {}
        transitions[from_state][old_char] = transition
    
    # Create and return a TM instance
    if not start_state:
        # Default to the first state if no start state is specified
        start_state = list(transitions.keys())[0] if transitions else "1"
        
    return TM(transitions=transitions, start_state=start_state, empty_symbol='0')


def save_to_xml(tm, filepath):
    """
    Save a Turing Machine to an XML file in the specified format.
    
    Args:
        tm (TM): The Turing Machine instance to save
        filepath (str): Path to save the XML file
        
    Returns:
        bool: True if successful, False otherwise
    """
    # Check that the TM only uses '0' and '1' symbols
    valid_symbols = {'0', '1'}
    all_symbols = set()
    
    # Collect all symbols used in transitions
    for state, transitions in tm.transitions.items():
        for symbol in transitions.keys():
            all_symbols.add(symbol)
            
        # Check symbols written in transitions
        for symbol, transition in transitions.items():
            if transition.symbol_to_write:
                all_symbols.add(transition.symbol_to_write)
    
    # Validate symbols
    if not all_symbols.issubset(valid_symbols):
        invalid_symbols = all_symbols - valid_symbols
        raise ValueError(f"TM uses invalid symbols: {invalid_symbols}. Only '0' and '1' are allowed.")
    
    # Create XML structure
    root = ET.Element("TuringMachine")
    states = ET.SubElement(root, "States")
    transitions = ET.SubElement(root, "Transitions")

    if tm.state != '0':
        print(f"Warning: Known bug in Turing Machine Simulator Application assigns state '0' to first state too. You will need to manually set the start state to the correct one (which also will have an arrow to it) in the Application.")

    # rename all states to simple integers
    state_id_map = get_state_id_map(tm)
    
    # Add states
    state_names = list(tm.transitions.keys())
    for i, state_name in enumerate(state_names):
        state_id = state_id_map[state_name]
        state_elem = ET.SubElement(states, f"State_{state_id}")
        
        # Random coordinates
        x = ET.SubElement(state_elem, "x")
        x.text = str(random.uniform(0, 600))
        
        y = ET.SubElement(state_elem, "y")
        y.text = str(random.uniform(0, 600))
        
        # Final state (default to false for now)
        finalstate = ET.SubElement(state_elem, "finalstate")
        finalstate.text = "false"
        
        # Start state
        startstate = ET.SubElement(state_elem, "startstate")
        startstate.text = "true" if state_name == tm.state else "false"
    
    # Add transitions
    trans_idx = 0
    for from_state, state_transitions in tm.transitions.items():
        for symbol, transition in state_transitions.items():
            trans_elem = ET.SubElement(transitions, f"Transition_{trans_idx}")
            trans_idx += 1
            
            # From state
            from_state_elem = ET.SubElement(trans_elem, "fromstate")
            from_state_elem.text = state_id_map[from_state]
            
            # To state
            to_state_elem = ET.SubElement(trans_elem, "tostate")
            to_state_elem.text = state_id_map[transition.state_to]
            
            # Old character (read symbol)
            old_char = ET.SubElement(trans_elem, "oldchar")
            old_char.text = symbol
            
            # New character (write symbol)
            new_char = ET.SubElement(trans_elem, "newchar")
            # If transition doesn't specify a symbol to write, use the same symbol
            new_char.text = transition.symbol_to_write if transition.symbol_to_write else symbol
            
            # Direction (1 = LEFT, 2 = RIGHT)
            direction = ET.SubElement(trans_elem, "direction")
            direction.text = "1" if transition.direction == LEFT else "2"
    
    # Create a pretty-formatted XML string
    rough_string = ET.tostring(root, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    pretty_xml = reparsed.toprettyxml(indent="    ")
    
    # Write to file
    with open(filepath, 'w') as f:
        f.write(pretty_xml)
    
    return True