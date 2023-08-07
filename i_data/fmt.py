
#from utils import is_plain_text


def is_ascii(test):
    try: test.decode("utf-8")
    except: return False
    else: return True


def detect_format(string):
    """
    Detect data format checking the most common features
    """
    try: string = string.encode("utf-8")
    except: pass # keep strings as bytes FIXME

    if is_ascii(string):

        string = string.decode("ascii", errors="ignore")

        # CIF crystalline data
        if "_cell_angle_gamma" in string and "loop_" in string:
            return "cif"

        # Topas CLI simulations
        elif "ymin_on_ymax " in string:
            return "topas"

        # Optimade JSON crystalline data
        elif (
            '"immutable_id"' in string
            and '"cartesian_site_positions"' in string
            and '"lattice_vectors"' in string
        ):
            return "optimade"

        # POSCAR crystalline data
        lines = string.splitlines()
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
            if line.startswith("'"):
                continue
            try:
                [float(item) for item in line.split(maxsplit=1)]
                counter += 1
            except ValueError:
                break
        else:
            if counter:
                return "xy"

    else:

        # Bruker's RAW measurements
        flag = string[:4]
        if flag == b"RAW1" or flag == b"RAW2" or flag == b"RAW4":
            return "raw"

        # Synchrotron HDF5 measurements
        # TODO

    return None

