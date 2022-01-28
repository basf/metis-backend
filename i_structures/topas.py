
from ase.geometry import cell_to_cellpar

from .struct_utils import sgn_to_crsystem


def ase_to_topas(ase_obj):

    str_output = """str
    Out_CIF_STR(structure.cif)
    scale  @  1.0
    r_bragg   1.0
"""

    s400 = "    prm s400 1.0\n"
    s040 = "    prm s040 1.0\n"
    s004 = "    prm s004 1.0\n"
    s220 = "    prm s220 1.0\n"
    s202 = "    prm s202 1.0\n"
    s022 = "    prm s022 1.0\n"
    s301 = "    prm s301 1.0\n"
    s121 = "    prm s121 1.0\n"
    s103 = "    prm s103 1.0\n"
    eta  = "    prm !eta 0.5 min 0.0 max 1.0\n"

    sgn = getattr(ase_obj.info.get('spacegroup', object), 'no', 1)
    crystal_system = sgn_to_crsystem(sgn)

    if crystal_system == 'monoclinic':
        str_output += "{s400}{s040}{s004}{s220}{s202}{s022}{s301}{s121}{s103}{eta}".format(
            s400=s400, s040=s040, s004=s004, s220=s220, s202=s202, s022=s022, s301=s301, s121=s121, s103=s103, eta=eta
        )
        str_output += "    Stephens_monoclinic(s400, s040, s004, s220, s202, s022, s301, s121, s103, eta)\n"

    elif crystal_system == 'orthorhombic':
        string = "{s400}{s040}{s004}{s220}{s202}{s022}{eta}".format(
            s400=s400, s040=s040, s004=s004, s220=s220, s202=s202, s022=s022, s301=s301, s121=s121, s103=s103, eta=eta
        )
        str_output += "    Stephens_orthorhombic(s400, s040, s004, s220, s202, s022, eta)\n"

    elif crystal_system == 'tetragonal':
        str_output += "{s400}{s004}{s220}{s202}{eta}".format(
            s400=s400, s040=s040, s004=s004, s220=s220, s202=s202, s022=s022, s301=s301, s121=s121, s103=s103, eta=eta
        )
        str_output += "    Stephens_tetragonal(s400, s004, s220, s202, eta)\n"

    elif crystal_system == 'hexagonal':
        str_output += "{s400}{s004}{s202}{eta}".format(
            s400=s400, s040=s040, s004=s004, s220=s220, s202=s202, s022=s022, s301=s301, s121=s121, s103=s103, eta=eta
        )
        str_output += "    Stephens_hexagonal(s400, s202, s004, eta)\n"

    str_output += """
PV_Peak_Type(
    ha,    0.02,
    !hb,   0.0,
    !hc,   0.0,
    lora,  0.5,
    !lorb, 0.0,
    !lorc, 0.0)
    Simple_Axial_Model(axial, 0.0)

"""
    str_output += "space_group %s\n" % sgn
    str_output += "phase_name %s\n" % ase_obj.get_chemical_formula()

    a, b, c, al, be, ga = cell_to_cellpar(ase_obj.cell)

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

    for atom in ase_obj:
        str_output += "site {element:2s}  x  {x:.5f}  y  {y:.5f}  z  {z:.5f}  occ {element:2s}  1  beq  1\n".format(
            element=atom.symbol, x=atom.x, y=atom.y, z=atom.z
        )

    return str_output