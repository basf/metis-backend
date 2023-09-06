import re
import itertools

from ase.data import chemical_symbols


groups_abbreviations = {
    "actinide": "Ad",
    "alkali": "Ak",
    "alkaline": "An",
    "chalcogen": "Ch",
    "group 10": "G0",
    "group 11": "G1",
    "group 12": "G2",
    "group 3": "G3",
    "group 4": "G4",
    "group 5": "G5",
    "group 6": "G6",
    "group 7": "G7",
    "group 8": "G8",
    "group 9": "G9",
    "halogen": "Hn",
    "lanthanide": "Lt",
    "noble gas": "Nl",
    "period 1": "P1",
    "period 2": "P2",
    "period 3": "P3",
    "period 4": "P4",
    "period 5": "P5",
    "period 6": "P6",
    "period 7": "P7",
    "pnictogen": "Pn",
    "tetrels": "Tt",
    "triels": "Tr",
}

chemical_symbols_and_groups = chemical_symbols[1:] + list(groups_abbreviations.values())


el_groups = {
    "Ac": ["Ad"],
    "Ag": ["P5", "G1"],
    "Al": ["P3", "Tr"],
    "Am": ["Ad"],
    "Ar": ["P3", "Nl"],
    "As": ["P4", "Pn"],
    "At": ["P6", "Hn"],
    "Au": ["P6", "G1"],
    "B": ["P2", "Tr"],
    "Ba": ["P6", "An"],
    "Be": ["P2", "An"],
    "Bi": ["P6", "Pn"],
    "Bk": ["Ad"],
    "Br": ["P4", "Hn"],
    "C": ["P2", "Tt"],
    "Ca": ["P4", "An"],
    "Cd": ["P5", "G2"],
    "Ce": ["Lt"],
    "Cf": ["Ad"],
    "Cl": ["P3", "Hn"],
    "Cm": ["Ad"],
    "Co": ["P4", "G9"],
    "Cr": ["P4", "G6"],
    "Cs": ["P6", "Ak"],
    "Cu": ["P4", "G1"],
    "Dy": ["Lt"],
    "Er": ["Lt"],
    "Es": ["Ad"],
    "Eu": ["Lt"],
    "F": ["P2", "Hn"],
    "Fe": ["P4", "G8"],
    "Fm": ["Ad"],
    "Fr": ["P7", "Ak"],
    "Ga": ["P4", "Tr"],
    "Gd": ["Lt"],
    "Ge": ["P4", "Tt"],
    "H": ["P1", "Ak"],
    "He": ["P1", "Nl"],
    "Hf": ["P6", "G4"],
    "Hg": ["P6", "G2"],
    "Ho": ["Lt"],
    "I": ["P5", "Hn"],
    "In": ["P5", "Tr"],
    "Ir": ["P6", "G9"],
    "K": ["P4", "Ak"],
    "Kr": ["P4", "Nl"],
    "La": ["Lt"],
    "Li": ["P2", "Ak"],
    "Lr": ["P7", "G3"],
    "Lu": ["P6", "G3"],
    "Md": ["Ad"],
    "Mg": ["P3", "An"],
    "Mn": ["P4", "G7"],
    "Mo": ["P5", "G6"],
    "N": ["P2", "Pn"],
    "Na": ["P3", "Ak"],
    "Nb": ["P5", "G5"],
    "Nd": ["Lt"],
    "Ne": ["P2", "Nl"],
    "Ni": ["P4", "G0"],
    "No": ["Ad"],
    "Np": ["Ad"],
    "O": ["P2", "Ch"],
    "Os": ["P6", "G8"],
    "P": ["P3", "Pn"],
    "Pa": ["Ad"],
    "Pb": ["P6", "Tt"],
    "Pd": ["P5", "G0"],
    "Pm": ["Lt"],
    "Po": ["P6", "Ch"],
    "Pr": ["Lt"],
    "Pt": ["P6", "G0"],
    "Pu": ["Ad"],
    "Ra": ["P7", "An"],
    "Rb": ["P5", "Ak"],
    "Re": ["P6", "G7"],
    "Rh": ["P5", "G9"],
    "Rn": ["P6", "Nl"],
    "Ru": ["P5", "G8"],
    "S": ["P3", "Ch"],
    "Sb": ["P5", "Pn"],
    "Sc": ["P4", "G3"],
    "Se": ["P4", "Ch"],
    "Si": ["P3", "Tt"],
    "Sm": ["Lt"],
    "Sn": ["P5", "Tt"],
    "Sr": ["P5", "An"],
    "Ta": ["P6", "G5"],
    "Tb": ["Lt"],
    "Tc": ["P5", "G7"],
    "Te": ["P5", "Ch"],
    "Th": ["Ad"],
    "Ti": ["P4", "G4"],
    "Tl": ["P6", "Tr"],
    "Tm": ["Lt"],
    "U": ["Ad"],
    "V": ["P4", "G5"],
    "W": ["P6", "G6"],
    "Xe": ["P5", "Nl"],
    "Y": ["P5", "G3"],
    "Yb": ["Lt"],
    "Zn": ["P4", "G2"],
    "Zr": ["P5", "G4"],
}


def els_to_groups(els):
    els = list(set(els))
    els.sort()

    result = []

    for n, ela in enumerate(els):
        for grpa in el_groups[ela]:
            result.append(els[:n] + [grpa] + els[n + 1 :])

            combs = []

            for m, elb in enumerate(result[-1]):
                for grpb in el_groups.get(elb, []):
                    combs.append(
                        list(set(result[-1][:m] + [grpb] + result[-1][m + 1 :]))
                    )

            result.extend(combs)

    if len(els) > 2:
        all_replaced = []
        back_map = {}

        for el in els:
            all_replaced.append([])
            for grp in el_groups[el]:
                all_replaced[-1].append(grp)
                back_map.setdefault(grp, []).append(el)

        for item in itertools.product(*all_replaced):
            candidate = list(set(item))

            if len(candidate) <= 2:  # only same-type and pair groups
                result.append(candidate)

            elif len(candidate) == 3:  # pairs + individual element
                for n, grp in enumerate(candidate):
                    for el in back_map[grp]:
                        result.append(candidate[:n] + [el] + candidate[n + 1 :])

    result.append(els)

    for n in range(len(result)):
        result[n] = sorted(result[n])

    result.sort()
    return list(
        x for x, _ in itertools.groupby(result)
    )  # remove dups from list of lists


def get_elements_or_groups(string):

    els = []

    for el in re.split(r"\s|\-|\,", string):

        if el not in chemical_symbols_and_groups:
            return None

        els.append(el)

    return sorted(els)


if __name__ == "__main__":

    import sys
    import random

    from ase.data import chemical_symbols

    chemical_symbols = chemical_symbols[1:103]
    els = sys.argv[1:]

    if not els:
        for n in range(random.choice(range(1, 11))):
            els.append(random.choice(chemical_symbols))

    print("Given", els)
    for item in els_to_groups(els):
        print(item)
