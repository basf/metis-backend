import random

import set_path
from metis_backend.datasources import Data_type
from metis_backend.structures.chemical_formulae import common_chem_elements
from metis_backend.helpers import get_rnd_string


common_chem_elements = common_chem_elements.split()
POSSIBLE_CONTENT = list(range(42))


def gen_data_item(data_type):
    meta = {}
    content = random.choice(POSSIBLE_CONTENT)

    if data_type == Data_type.calculation:
        meta["name"] = gen_chem_formula()

    elif data_type == Data_type.structure:
        meta["name"] = gen_chem_formula()

    elif data_type == Data_type.property:
        meta["name"] = gen_chem_formula()  # FIXME

    elif data_type == Data_type.pattern:
        meta["name"] = get_rnd_string()

    else:
        raise RuntimeError

    return (meta, content, data_type)


def gen_chem_formula():
    els = set()
    pseudo_formula = ""

    for _ in range(random.randint(1, 7)):
        els.add(random.choice(common_chem_elements))

    els = list(els)

    for n in range(len(els)):
        coeff = random.randint(1, 10)
        coeff = "" if coeff == 1 else str(coeff)
        pseudo_formula += els[n] + coeff

    return pseudo_formula


if __name__ == "__main__":
    print(gen_chem_formula())
