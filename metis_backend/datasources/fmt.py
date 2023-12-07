
def detect_format(string):
    """
    Detect data format, checking the most common features
    """
    try: string = string.encode("utf-8")
    except: pass # keep strings as bytes

    ascii_data = string.decode("ascii", errors="ignore")

    # CIF crystalline data
    if "_cell_angle_gamma" in ascii_data and "loop_" in ascii_data:
        return "cif"

    # Topas CLI simulations
    elif "ymin_on_ymax " in ascii_data:
        return "topas"

    # Optimade JSON crystalline data
    elif (
        '"immutable_id"' in ascii_data
        and '"cartesian_site_positions"' in ascii_data
        and '"lattice_vectors"' in ascii_data
    ):
        return "optimade"

    # POSCAR crystalline data
    lines = ascii_data.splitlines()
    for nline in [6, 7, 8]:
        if len(lines) <= nline:
            break
        if lines[nline].strip().lower().startswith("direct") or lines[
            nline
        ].strip().lower().startswith("cart"):
            return "poscar"

    # XY patterns (TSV-alike)
    counter = 0
    for line in lines[:-1]:
        if line.startswith(("'", "*", "#")): # Rigaku features
            continue
        try:
            [float(item) for item in line.split(maxsplit=2)]
            counter += 1
        except ValueError:
            break
    else:
        if counter:
            return "xy"

    # Bruker's RAW measurements
    flag = string[:4]
    if flag == b"RAW1" or flag == b"RAW2" or flag == b"RAW3" or flag == b"RAW4":
        return "raw"

    # Synchrotron HDF5 measurements
    elif flag == b"\x89HDF" and b"pyFAI" in string:
        return "nexus"

    return None


def is_ase_obj(test):
    try:
        getattr(test, "pbc")
    except AttributeError:
        return False
    return True
