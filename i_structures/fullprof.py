from ase.geometry import cell_to_cellpar


def ase_to_fullprof(ase_obj):
    """
    Convert ASE object into FullProf input phase definition
    FIXME
    calculate occupancies with multiplicity and Wyckoff positions treatment
    """
    input_phase = """!-------------------------------------------------------------------------------
!  Data for PHASE number:   1  ==> Current R_Bragg for Pattern#  1:   0.0000
!-------------------------------------------------------------------------------
{comment}
!
!Nat Dis Ang Pr1 Pr2 Pr3 Jbt Irf Isy Str Furth       ATZ    Nvk Npr More
{natoms:4d}   0   0 0.0 0.0 1.0   0   0   0   0     0         0      0   5    0
!
!
{spg}                  <--Space group symbol
!Atom   Typ       X        Y        Z     Biso       Occ     In Fin N_t Spc /Codes""".format(
        comment=ase_obj.get_chemical_formula(),
        natoms=len(ase_obj),
        spg=getattr(ase_obj.info.get("spacegroup", object), "no", 1)
    )

    input_phase += "\n"

    pos_fmt = "{:8s} {:4s} {: 6.5f} {: 6.5f} {: 6.5f} 0.00000 {:6.5f}   0   0   0    0\n"
    pos_fmt += "                  0.00     0.00     0.00     0.00      0.00\n"

    for n, atom in enumerate(ase_obj):
        input_phase += pos_fmt.format(
            atom.symbol + str(n + 1),
            atom.symbol.upper(),
            atom.x,
            atom.y,
            atom.z,
            1 # FIXME
        )

    input_phase = input_phase[:-1]

    input_cell = """!     a          b         c        alpha      beta       gamma      #Cell Info
{: 6.6f}   {: 6.6f}   {: 6.6f}   {: 6.6f}   {: 6.6f}   {: 6.6f}
0.00000    0.00000    0.00000    0.00000    0.00000    0.00000""".format(
        *cell_to_cellpar(ase_obj.cell)
    )

    return (input_phase, input_cell)
