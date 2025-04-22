from utm import get_utm
from parser import save_to_xml
import sys

if __name__ == "__main__":
    """
    Construct UTM, saving it to an XML file
    """
    filepath = 'utm.xml'
    if len(sys.argv) == 2:
        filepath = sys.argv[1]

    utm = get_utm()
    save_to_xml(utm, filepath)