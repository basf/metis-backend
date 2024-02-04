#!/usr/bin/env python3

import sys
import logging

import set_path
from metis_backend.datasources.fmt import detect_format
from metis_backend.structures.struct_utils import poscar_to_ase, optimade_to_ase, refine, get_formula
from metis_backend.structures.cif_utils import cif_to_ase
from metis_backend.calculations import Calc_setup
from metis_backend.calculations.pcrystal import Pcrystal_setup


assert len(Pcrystal_setup.els_repo)

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

try:
    template = sys.argv[2]
except IndexError:
    template = None

if template:
    logging.warning(f'Using template {template}')

setup = Calc_setup()
inputs, error = setup.preprocess(ase_obj, 'pcrystal', 'AiiDA test', custom_template=template)
if error:
    raise RuntimeError(error)

print(inputs['INPUT'])
print('=' * 100)
print(inputs['fort.34'])
