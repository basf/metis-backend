
from ase.geometry import cell_to_cellpar

from .struct_utils import sgn_to_crsystem


def ase_to_topas(ase_obj):

    str_output = "str\n"
    sgn = getattr(ase_obj.info.get('spacegroup', object), 'no', 1)
    str_output += "space_group %s\n" % sgn
    str_output += "phase_name %s\n" % ase_obj.get_chemical_formula()

    a, b, c, al, be, ga = cell_to_cellpar(ase_obj.cell)
    crystal_system = sgn_to_crsystem(sgn)

    if crystal_system == 'cubic':
        cell_fmt = "Cubic(@ {a})\n"
    elif crystal_system == 'tetragonal':
        cell_fmt = "Tetragonal(@ {a}, @ {c})\n"
    elif crystal_system == 'hexagonal':
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
    str_output += cell_fmt.format(a=a, b=b, c=c, refal=refal, al=al, refbe=refbe, be=be, refga=refga, ga=ga)

    #str_output += "CS_L(, 150)"

    for atom in ase_obj:
        str_output += "site {element:2s}  x  {x:.5f}  y  {y:.5f}  z  {z:.5f}  occ {element:2s}  1  beq  1\n".format(
            element=atom.symbol, x=atom.x, y=atom.y, z=atom.z
        )

    return str_output
