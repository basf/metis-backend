
import sys, os.path

INCL_PATH = os.path.realpath(os.path.normpath(
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "../"
    )
))

if not INCL_PATH in sys.path:
    sys.path.insert(0, INCL_PATH)
