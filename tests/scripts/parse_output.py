#!/usr/bin/env python3

import os, sys
from pprint import pprint

#from pycrystal import CRYSTOUT

import set_path
from i_calculations import Calc_setup


fmt = 'pcrystal'
#fmt = 'topas'

try:
    sys.argv[1] and os.path.exists(sys.argv[1])
except (IndexError, OSError):
    sys.exit("USAGE: <script> <target>")

#assert CRYSTOUT.acceptable(sys.argv[1])
#result = CRYSTOUT(sys.argv[1])

#pprint(result.info)
#raise SystemExit

setup = Calc_setup()
output, error = setup.postprocess(fmt, os.path.dirname(sys.argv[1]))
if error:
    raise RuntimeError(error)

print(output)
