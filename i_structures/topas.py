import re

from ase.geometry import cell_to_cellpar
from ase.atoms import Atom, Atoms
from ase.spacegroup import crystal

from .struct_utils import sgn_to_crsystem


def ase_to_topas(ase_obj):
    """
    Convert ASE object into the TOPAS input str section
    TODO under @ parameters control
    """
    str_output = "str\n"
    sgn = getattr(ase_obj.info.get("spacegroup", object), "no", 1)
    str_output += "space_group %s\n" % sgn
    str_output += "phase_name %s\n" % ase_obj.get_chemical_formula()

    a, b, c, al, be, ga = cell_to_cellpar(ase_obj.cell)
    crystal_system = sgn_to_crsystem(sgn)

    if crystal_system == "cubic":
        cell_fmt = "Cubic(@ {a})\n"
    elif crystal_system == "tetragonal":
        cell_fmt = "Tetragonal(@ {a}, @ {c})\n"
    elif crystal_system == "hexagonal":
        cell_fmt = "Hexagonal(@ {a}, @ {c})\n"
    else:
        cell_fmt = """
a  @  {a:8.5f}
b  @  {b:8.5f}
c  @  {c:8.5f}
al {refal:1}  {al}
be {refbe:1}  {be}
ga {refga:1}  {ga}
"""
    refal = " " if al == 90 else "@"
    refbe = " " if be == 90 else "@"
    refga = " " if ga == 90 else "@"
    str_output += cell_fmt.format(
        a=a, b=b, c=c, refal=refal, al=al, refbe=refbe, be=be, refga=refga, ga=ga
    )

    # str_output += "CS_L(, 150)"

    for atom in ase_obj:
        str_output += "site {element:2s}  x  {x:.5f}  y  {y:.5f}  z  {z:.5f}  occ {element:2s}  1  beq  1\n".format(
            element=atom.symbol, x=atom.x, y=atom.y, z=atom.z
        )

    return str_output


def topas_to_ase(content):
    """
    Extracts one ASE object from an arbitrary TOPAS input
    TODO support occupancies via .info['occupancy'] dict
    TODO support multiple str, not only the 1st one
    TODO support lattice classes
    TODO support omitting the cellpar components
    TODO use settings class below?
    class Topas_params(dict):
            def __getitem__(self, key):
                try:
                    return super(Topas_params, self).__getitem__(key)
                except KeyError as e:
                    raise RuntimeError(e.message)
    """
    found, ending = False, False
    atom_data = []
    cellpar = [None, None, None, None, None, None]
    spg = None
    topas_params = {}

    sg_topas2ase = {
        "C 1 2/m 1": "C 2/m",
        "P 1 21/n 1": "P 21/n",
    }

    for line in content.splitlines():
        cmp = line.strip().lower().split("'")[0]
        if not cmp:
            continue

        if found:
            for n, check in enumerate(("a ", "b ", "c ", "al", "be", "ga")):
                if cmp.startswith(check):
                    params = cmp[2:].split()
                    if len(params) == 1:
                        cellpar[n] = float(
                            topas_params[
                                params[0]
                                .replace("=", "")
                                .replace("=", "")
                                .replace(";", "")
                            ]
                            if params[0].startswith("=")
                            else params[0]
                        )

                    elif len(params) == 2:
                        topas_params[params[0]] = params[1].replace("`", "")
                        cellpar[n] = float(params[1].replace("`", ""))

                    else:
                        raise RuntimeError("Unknown TOPAS params definition: %s" % line)
                    break

            if cmp.startswith("space_group"):
                spg = (
                    cmp[12:].strip().replace("_", " ").capitalize()
                )  # TOPAS to ASE fmt

            elif cmp.startswith("site"):
                ending = True
                str_symb = re.split(
                    "\d", cmp[5:].split(" x ")[0].split()[0].split("_")[0].capitalize()
                )[0]

                str_x = convert_to_float(
                    cmp.split(" x ")[-1]
                    .split(" y ")[0]
                    .split()[-1]
                    .replace("=", "")
                    .replace(";", "")
                    .replace("`", "")
                )

                str_y = convert_to_float(
                    cmp.split(" y ")[-1]
                    .split(" z ")[0]
                    .split()[-1]
                    .replace("=", "")
                    .replace(";", "")
                    .replace("`", "")
                )

                str_z = convert_to_float(
                    cmp.split(" z ")[-1]
                    .split(" occ ")[0]
                    .split()[-1]
                    .replace("=", "")
                    .replace(";", "")
                    .replace("`", "")
                )

                # str_occ = convert_to_float(
                # cmp.split(' occ ')[-1].split(' beq ')[0].split()[-1].replace('=', '').replace(';', '').replace('`', ''))

                atom_data.append(Atom(str_symb, (str_x, str_y, str_z)))

            elif ending:
                break

        if cmp == "str":
            found = True

        elif cmp.startswith("str("):
            found = True
            spg = line.split("(")[-1].split(")")[0]

    if spg in sg_topas2ase:
        spg = sg_topas2ase[spg]

    # print(atom_data)
    # print(spg)
    # print(cellpar)
    assert len(list(filter(None, cellpar))) == 6, "Cell info corrupt"

    # FIXME primitive or conventional cell?
    return crystal(atom_data, spacegroup=spg, cellpar=cellpar)


def convert_to_float(frac_str):
    try:
        return float(frac_str)
    except ValueError:
        num, denom = frac_str.split("/")
        try:
            leading, num = num.split()
            whole = float(leading)
        except ValueError:
            whole = 0
        frac = float(num) / float(denom)
        return whole - frac if whole < 0 else whole + frac
