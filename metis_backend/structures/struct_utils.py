import math
import re
import json
import random
import pickle
import base64
import itertools
from functools import reduce
from io import StringIO

from ase.atoms import Atom, Atoms
from ase.io import read as ase_read, write as ase_write
from ase.spacegroup import crystal

import spglib


def poscar_to_ase(poscar_string):
    """
    Parse POSCAR using ase

    Returns:
        Refined ASE structure (object) *or* None
        None *or* error (str)
    """
    ase_obj, error = None, None
    buff = StringIO(poscar_string)
    try:
        ase_obj = ase_read(buff, format='vasp')
    except AttributeError:
        error = "Types of atoms can be neither found nor inferred"
    except Exception:
        error = "Cannot process POSCAR: invalid or missing data"
    buff.close()
    return ase_obj, error


def json_to_ase(datarow):
    """
    Handling the disordered structures
    in an oversimplified, very narrow-purpose way

    TODO?
    Avoid els_noneq rewriting
    """
    if not datarow or not datarow[-1]:
        return None, "No structure found"

    occs_noneq, cell_abc, sg_n, basis_noneq, els_noneq = (
        datarow[-5],
        datarow[-4],
        int(datarow[-3]),
        datarow[-2],
        datarow[-1],
    )

    occ_data = None
    if any([occ != 1 for occ in occs_noneq]):
        partial_pos, occ_data = {}, {}
        for n in range(len(occs_noneq) - 1, -1, -1):
            if occs_noneq[n] != 1:
                disordered_pos = basis_noneq.pop(n)
                disordered_el = els_noneq.pop(n)
                partial_pos.setdefault(tuple(disordered_pos), {})[
                    disordered_el
                ] = occs_noneq[n]

        for xyz, occs in partial_pos.items():
            index = len(els_noneq)
            els_noneq.append(sorted(occs.keys())[0])
            basis_noneq.append(xyz)
            occ_data[index] = occs

    atom_data = []

    for n, xyz in enumerate(basis_noneq):
        atom_data.append(Atom(els_noneq[n], tuple(xyz), tag=n))

    if not atom_data:
        return None, "No atoms found"

    try:
        return (
            crystal(
                atom_data,
                spacegroup=sg_n,
                cellpar=cell_abc,
                primitive_cell=True,
                onduplicates="error",
                info=dict(disordered=occ_data) if occ_data else {},
            ),
            None,
        )
    except Exception as ex:
        return None, "ASE cannot handle structure: %s" % ex


def optimade_to_ase(structure, skip_disorder=False):
    """
    A very permissive Optimade format support
    so far only with a very limited disorder handling

    Returns:
        ASE Atoms (object) *or* None
        None *or* error (str)
    """
    if type(structure) == str:
        try:
            structure = json.loads(structure)
        except Exception:
            return None, "Misformatted data occured"

    # if 'cartesian_site_positions' not in structure['attributes'] or 'lattice_vectors' not in structure['attributes']:
    #    return None, "Invalid structure"

    if (
        "data" in structure
        and type(structure["data"]) == list
        and len(structure["data"])
    ):
        structure = structure["data"][0]

    elems_src, atom_data, atom_meta = [], [], {}

    # The field *species* might contain all the atoms,
    # but it also might contain only the distinct atoms;
    # in the latter case we have to link *species_at_sites* <-> *species* (TODO)
    if "species" in structure["attributes"]:
        for n, specie in enumerate(structure["attributes"]["species"]):
            # account isotopes
            if specie["chemical_symbols"][0] == "D":
                specie["chemical_symbols"][0] = "H"
                atom_meta[n] = "D"

            elems_src.append(specie["chemical_symbols"][0])

            if not skip_disorder and len(specie["chemical_symbols"]) > 1:
                if "concentration" not in specie:
                    return None, "Atomic disorder data incomplete"

                return None, "Structural disorder is not yet supported"

    if len(structure["attributes"].get("species", [])) != len(
        structure["attributes"]["cartesian_site_positions"]
    ):
        elems_src = structure["attributes"].get(
            "species_at_sites", structure["attributes"].get("elements", [])
        )

    for n, pos in enumerate(structure["attributes"]["cartesian_site_positions"]):
        try:
            atom_data.append(Atom(extract_chemical_element(elems_src[n]), pos))
        except KeyError as exc:  # TODO link *species_at_sites* <-> *species*
            return None, "Unrecognized atom symbol: %s" % exc

    if not atom_data:
        return None, "Atoms missing"

    return (
        Atoms(
            atom_data,
            cell=structure["attributes"]["lattice_vectors"],
            pbc=structure["attributes"].get("dimension_types") or True,
            info=dict(isotopes=atom_meta) if atom_meta else {},
        ),
        None,
    )


def provider_to_ase(json_obj):

    # FIXME switch to optimade_to_ase

    assert json_obj["occs_noneq"]
    assert json_obj["basis_noneq"]
    assert json_obj["els_noneq"]
    assert json_obj["sg_n"]
    assert json_obj["cell_abc"]

    if any([occ != 1 for occ in json_obj["occs_noneq"]]):
        return None, "Structural disorder is not yet supported"

    atom_data = []

    for n, xyz in enumerate(json_obj["basis_noneq"]):
        atom_data.append(Atom(json_obj["els_noneq"][n], tuple(xyz), tag=n))

    if not atom_data:
        return None, "No atoms found"

    try:
        return crystal(
            atom_data,
            spacegroup=json_obj["sg_n"],
            cellpar=json_obj["cell_abc"],
            primitive_cell=True,
            onduplicates='error',
            info={}
        ), None

    except Exception as ex:
        return None, "ASE cannot handle structure: %s" % ex


def refine(ase_obj, accuracy=1e-03, **kwargs): # FIXME switch to primitive cell
    """
    Refine ASE structure using spglib

    Args:
        ase_obj: (object) ASE structure
        accuracy: (float) spglib tolerance, normally within [1E-02, 1E-04]

    Returns:
        Refined ASE structure (object) *or* None
        None *or* error (str)
    """
    spg_result = spglib.standardize_cell(
        ase_obj, symprec=accuracy, to_primitive=True
    )
    if not spg_result or len(spg_result) != 3:
        return None, f"Error in structure refinement, spglib returned {spg_result}"
    lattice, positions, numbers = spg_result

    symmetry = spglib.get_spacegroup(ase_obj, symprec=accuracy)
    try:
        spacegroup = int(symmetry.split()[1].replace("(", "").replace(")", ""))
    except (ValueError, IndexError, AttributeError):
        return None, "Symmetry error (coinciding atoms?) in structure"

    try:
        return (
            crystal(
                Atoms(
                    numbers=numbers, cell=lattice, scaled_positions=positions, pbc=True
                ),
                spacegroup=spacegroup,
                primitive_cell=True,
                onduplicates="replace",
            ),
            None,
        )
    except:
        return None, "Unrecognized sites or invalid site symmetry in structure"


FORMULA_SEQUENCE = [
    "Fr",
    "Cs",
    "Rb",
    "K",
    "Na",
    "Li",
    "Be",
    "Mg",
    "Ca",
    "Sr",
    "Ba",
    "Ra",
    "Sc",
    "Y",
    "La",
    "Ce",
    "Pr",
    "Nd",
    "Pm",
    "Sm",
    "Eu",
    "Gd",
    "Tb",
    "Dy",
    "Ho",
    "Er",
    "Tm",
    "Yb",
    "Ac",
    "Th",
    "Pa",
    "U",
    "Np",
    "Pu",
    "Ti",
    "Zr",
    "Hf",
    "V",
    "Nb",
    "Ta",
    "Cr",
    "Mo",
    "W",
    "Fe",
    "Ru",
    "Os",
    "Co",
    "Rh",
    "Ir",
    "Mn",
    "Tc",
    "Re",
    "Ni",
    "Pd",
    "Pt",
    "Cu",
    "Ag",
    "Au",
    "Zn",
    "Cd",
    "Hg",
    "B",
    "Al",
    "Ga",
    "In",
    "Tl",
    "Pb",
    "Sn",
    "Ge",
    "Si",
    "C",
    "N",
    "P",
    "As",
    "Sb",
    "Bi",
    "H",
    "Po",
    "Te",
    "Se",
    "S",
    "O",
    "At",
    "I",
    "Br",
    "Cl",
    "F",
    "He",
    "Ne",
    "Ar",
    "Kr",
    "Xe",
    "Rn",
]


def get_formula(ase_obj, find_gcd=True, as_dict=False):
    parsed_formula = {}

    for label in ase_obj.get_chemical_symbols():
        if label not in parsed_formula:
            parsed_formula[label] = 1
        else:
            parsed_formula[label] += 1

    expanded = reduce(math.gcd, parsed_formula.values()) if find_gcd else 1
    if expanded > 1:
        parsed_formula = {
            el: int(content / float(expanded)) for el, content in parsed_formula.items()
        }

    if as_dict:
        return parsed_formula

    atoms = parsed_formula.keys()
    atoms = [x for x in FORMULA_SEQUENCE if x in atoms] + [
        x for x in atoms if x not in FORMULA_SEQUENCE
    ]
    formula = ""
    for atom in atoms:
        index = parsed_formula[atom]
        index = "" if index == 1 else str(index)
        formula += atom + index

    return formula


def sgn_to_crsystem(number):
    if 195 <= number <= 230:    return "cubic"
    elif 168 <= number <= 194:  return "hexagonal"
    elif 143 <= number <= 167:  return "trigonal"
    elif 75 <= number <= 142:   return "tetragonal"
    elif 16 <= number <= 74:    return "orthorhombic"
    elif 3 <= number <= 15:     return "monoclinic"
    else:                       return "triclinic"


def sgn_to_label(number):
    if 195 <= number <= 230:    return "cub"
    elif 168 <= number <= 194:  return "hex"
    elif 143 <= number <= 167:  return "trig"
    elif 75 <= number <= 142:   return "tet"
    elif 16 <= number <= 74:    return "orth"
    elif 3 <= number <= 15:     return "monocl"
    else:                       return "tricl"


def crsystem_to_sgn(crsystem):

    mapping = {
        "cubic":        (195, 230), # 1.
        "hexagonal":    (168, 194), # 2.
        "trigonal":     (143, 167), # 3.
        "tetragonal":   (75, 142),  # 4.
        "orthorhombic": (16, 74),   # 5.
        "monoclinic":   (3, 15),    # 6.
        "triclinic":    (1, 2)      # 7.
    }

    if crsystem not in mapping:
        raise KeyError("Unexpected crystalline lattice: %s" % crsystem)

    return mapping[crsystem]


MAX_ATOMS = 1000
SITE_SUM_OCCS_TOL = 0.99


def order_disordered(ase_obj):
    """
    This is a toy algo to get rid of the structural disorder;
    just one random possible ordered structure is returned
    (out of may be billions). No attempt to embrace all permutations is made.
    For that one needs to consider the special-purpose software (e.g.
    https://doi.org/10.1186/s13321-016-0129-3 etc.).

    Args:
        ase_obj: (object) ASE structure; must have *info* dict *disordered* and *Atom* tags
            *disordered* dict format: {'disordered': {at_index: {element: occupancy, ...}, ...}

    Returns:
        ASE structure (object) *or* None
        None *or* error (str)

    TODO?
    Rewrite space group info accordingly
    """
    for index in ase_obj.info["disordered"]:
        if sum(ase_obj.info["disordered"][index].values()) < SITE_SUM_OCCS_TOL:
            ase_obj.info["disordered"][index].update(
                {"X": 1 - sum(ase_obj.info["disordered"][index].values())}
            )

    min_occ = min(
        sum([list(item.values()) for item in ase_obj.info["disordered"].values()], [])
    )
    if min_occ == 0:
        return None, "Zero occupancy is encountered"

    needed_det = math.ceil(1.0 / min_occ)
    if needed_det * len(ase_obj) > MAX_ATOMS:
        return None, "Resulting crystal cell size is too big"

    diag = needed_det ** (1.0 / 3)
    supercell_matrix = [int(x) for x in (round(diag), math.ceil(diag), math.ceil(diag))]
    actual_det = reduce(lambda x, y: x * y, supercell_matrix)

    occ_data = {}
    for index, occs in ase_obj.info["disordered"].items():
        disorder = []
        for el, occ in occs.items():
            disorder += [el] * int(round(occ * actual_det))
        random.shuffle(disorder)
        occ_data[index] = itertools.cycle(disorder)

    order_obj = ase_obj.copy()
    order_obj *= supercell_matrix
    del order_obj.info["disordered"]

    for index, occs in occ_data.items():
        for n in range(len(order_obj) - 1, -1, -1):
            if order_obj[n].tag == index:
                distrib_el = next(occs)
                if distrib_el == "X":
                    del order_obj[n]
                else:
                    try:
                        order_obj[n].symbol = distrib_el
                    except KeyError as exc:
                        return None, "Unrecognized atom symbol: %s" % exc

    return order_obj, None


def extract_chemical_element(str):
    return re.sub("\W", "", str)


def ase_serialize(ase_obj):
    return base64.b64encode(pickle.dumps(ase_obj, protocol=4)).decode("ascii")
    #buff = StringIO()
    #ase_write(buff, ase_obj, format='json')
    #return buff.getvalue()


def ase_unserialize(string):
    return pickle.loads(base64.b64decode(string))
    #buff = StringIO(string)
    #return ase_read(buff, format='json')


if __name__ == "__main__":
    from ase.spacegroup import crystal

    crystal_obj = crystal(
        ("Sr", "Ti", "O", "O"),
        basis=[(0, 0.5, 0.25), (0, 0, 0), (0, 0, 0.25), (0.255, 0.755, 0)],
        spacegroup=140,
        cellpar=[5.511, 5.511, 7.796, 90, 90, 90],
        primitive_cell=True,
    )
    # print(crystal_obj)

    repr = ase_serialize(crystal_obj)
    # print(repr)

    new_obj = ase_unserialize(repr)
    # print(new_obj)

    assert new_obj == crystal_obj
