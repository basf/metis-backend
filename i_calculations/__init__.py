
from mpds_aiida.common import get_template, get_basis_sets, get_input
from aiida_crystal_dft.io.f34 import Fort34


class Calc_Setup(object):

    def __init__(self):
        self.template = get_template()
        self.bs_repo = get_basis_sets(self.template['basis_family'])


    def preprocess(self, ase_obj, name):

        els = set(ase_obj.get_chemical_symbols())

        f34_input = Fort34([self.bs_repo[el] for el in els])
        struct_input = f34_input.from_ase(ase_obj)
        struct_input = str(struct_input)

        setup_input = get_input(self.template['default']['crystal'], els, self.bs_repo, name)
        setup_input = str(setup_input)

        return dict(structure=struct_input, input=setup_input)