#!/usr/bin/env python3

import sys

import set_path
from metis_backend.datasources.fmt import detect_format
from metis_backend.structures.struct_utils import poscar_to_ase, optimade_to_ase, refine, get_formula
from metis_backend.structures.cif_utils import cif_to_ase
from metis_backend.structures.topas import ase_to_topas
from metis_backend.calculations import Calc_setup


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

ase_obj, error = refine(ase_obj)
if error:
    raise RuntimeError(error)

struct_input = ase_to_topas(ase_obj)

setup = Calc_setup()
control_input = setup.get_input('topas')

merged_input = control_input.replace('#include "structure.inc"', struct_input)
print(merged_input)
