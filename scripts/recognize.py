#!/usr/bin/env python3
"""
An example of the arbitrary data recognition
and consequent conditional processing
"""
import os.path
import sys

import set_path
from metis_backend.datasources.fmt import detect_format
from metis_backend.datasources.xrpd import extract_pattern, nexus_to_xye
from metis_backend.calculations.xrpd import get_pattern
from metis_backend.structures.cif_utils import cif_to_ase
from metis_backend.structures.struct_utils import poscar_to_ase, optimade_to_ase


input = sys.argv[1]
assert os.path.exists(input) and os.path.isfile(input)

with open(input, "rb") as f:
    contents = f.read()

fmt = detect_format(contents)

print("=" * 100)
print(f"This is the {fmt or 'unknown'} format data.")

if fmt == "cif":
    result, error = cif_to_ase(contents.decode("ascii"))
    if error: raise RuntimeError(error)

elif fmt == "poscar":
    result, error = poscar_to_ase(contents.decode("ascii"))
    if error: raise RuntimeError(error)

elif fmt == "optimade":
    result, error = optimade_to_ase(contents.decode("ascii"))
    if error: raise RuntimeError(error)

elif fmt == "xy":
    result = get_pattern(contents.decode("ascii"))
    if not result: raise RuntimeError("Not a valid pattern provided")

elif fmt == "raw":
    result = extract_pattern(contents)
    if not result: raise RuntimeError("Not a valid pattern provided")

elif fmt == "nexus":
    result = nexus_to_xye(contents)
    if not result: raise RuntimeError("Not a valid synchrotron format provided")

elif fmt == "topas":
    result = contents

else: raise RuntimeError("Provided data format unsuitable or not recognized")

print(repr(result)[:256] + "...")
