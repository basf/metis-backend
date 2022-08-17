
import os
from collections import namedtuple

import yaml
from ase.data import chemical_symbols

from aiida_crystal_dft.io.f34 import Fort34
from aiida_crystal_dft.io.d12 import D12
from aiida_crystal_dft.io.basis import BasisFile # NB only used to determine ecp
from mpds_aiida.properties import get_avg_charges
from pycrystal import CRYSTOUT

from i_data import Data_type
from utils import config, ase_serialize


ELS_REPO_DIR = config.get('local', 'pcrystal_bs_path', fallback='/tmp')

TEMPLATE_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "templates/pcrystal"
)

verbatim_basis = namedtuple("basis", field_names="content, all_electron")


def get_basis_sets(repo_dir=ELS_REPO_DIR):
    """
    Keeps all available BS in a dict for convenience
    NB. we assume BS repo_dir = AiiDA's *basis_family*
    """
    assert os.path.exists(repo_dir), "No folder %s with the basis sets found" % repo_dir

    bs_repo = {}
    for filename in os.listdir(repo_dir):
        if not filename.endswith('.basis'):
            continue

        el = filename.split('.')[0]
        assert el in chemical_symbols, "Unexpected basis set file %s" % filename
        with open(repo_dir + os.sep + filename, 'r') as f:
            bs_str = f.read().strip()

        bs_parsed = BasisFile().parse(bs_str)
        bs_repo[el] = verbatim_basis(content=bs_str, all_electron=('ecp' not in bs_parsed))

    return bs_repo


def get_template(template='demo.yml'):
    """
    Templates present the permanent calc setup
    """
    template_loc = os.path.join(TEMPLATE_DIR, template)
    if not os.path.exists(template_loc):
        template_loc = template

    assert os.path.exists(template_loc)

    with open(template_loc) as f:
        calc = yaml.load(f.read(), Loader=yaml.SafeLoader)
    # assert 'parameters' in calc and 'crystal' in calc['parameters'] and 'basis_family' in calc
    return calc


def get_input(calc_params_crystal, elements, bs_src, label):
    """
    Generates a program input
    """
    calc_params_crystal['label'] = label

    if isinstance(bs_src, dict):
        return D12(parameters=calc_params_crystal, basis=[bs_src[el] for el in elements])

    elif isinstance(bs_src, str):
        return D12(parameters=calc_params_crystal, basis=bs_src)

    raise RuntimeError('Unknown basis set source format!')


class Pcrystal_setup:

    els_repo = get_basis_sets()
    calc_setup = get_template()
    assert calc_setup['default']['crystal']


    def __init__(self, ase_obj):
        self.ase_obj = ase_obj
        self.els = list(set(self.ase_obj.get_chemical_symbols()))


    def validate(self):
        for el in self.els:
            if el not in Pcrystal_setup.els_repo:
                return f"Element {el} is not supported"

        return None


    def get_input_struct(self):
        f34_input = Fort34([Pcrystal_setup.els_repo[el] for el in self.els])
        return str(f34_input.from_ase(self.ase_obj))


    def get_input_setup(self, label):
        return str(get_input(
            Pcrystal_setup.calc_setup['default']['crystal'],
            self.els,
            Pcrystal_setup.els_repo,
            label
        ))


    @staticmethod
    def parse(resource):
        if not CRYSTOUT.acceptable(resource):
            return False

        result = CRYSTOUT(resource)
        output = {'content': {}}

        if result.info['optgeom']:
            #output['content'] = ase_serialize(result.info['structures'][-1])
            output['type'] = Data_type.structure

        # TODO
        # Below is just a quick example
        # this should be more systematic

        conductor, band_gap = 'no data', 'no data'
        try: bands_data = result.info['conduction'][-1]
        except Exception: bands_data = {}
        if bands_data.get('state') == 'CONDUCTING':
            conductor, band_gap = True, None
        elif bands_data.get('state') == 'INSULATING':
            conductor, band_gap = False, f"{bands_data['band_gap']:.1f}"
        try:
            charges = get_avg_charges(result.info['structures'][-1])
            charges = {el: f"{val:.2f}" for el, val in charges.items()}
        except Exception: charges = None

        output['content'] = {
            'total_energy': f"{result.info['energy']:.4f}",
            'total_energy_units': 'eV',
            'conductor': conductor,
            'band_gap': band_gap,
            'band_gap_units': 'eV',
            'charges': charges,
            'n_electrons': result.info['n_electrons'],
            'correctly_finalized': result.info['finished'] == 2,
        }
        return output
