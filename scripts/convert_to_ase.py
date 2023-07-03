#!/usr/bin/env python3

import sys

import set_path
from i_structures.struct_utils import detect_format, poscar_to_ase, optimade_to_ase, refine, get_formula
from i_structures.cif_utils import cif_to_ase


structure = open(sys.argv[1]).read()
fmt = detect_format(structure)

if fmt == 'cif':
    ase_obj, error = cif_to_ase(structure)
    if error:
        raise RuntimeError(error)

elif fmt == 'poscar':
    ase_obj, error = poscar_to_ase(structure)
    if error:
        raise RuntimeError(error)

elif fmt == 'optimade':
    ase_obj, error = optimade_to_ase(structure, skip_disorder=True)
    if error:
        raise RuntimeError(error)

else:
    raise RuntimeError('Provided data format unsuitable or not recognized')

ase_obj, error = refine(ase_obj, conventional_cell=True)
if error:
    raise RuntimeError(error)

print(ase_obj)
print(ase_obj.get_scaled_positions())
print(get_formula(ase_obj))
