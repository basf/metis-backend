import random
import string

from metis_backend.datasources import Data_type


def get_pattern(resource):
    """
    Check if a file / given string contains computed XRPD pattern
    (two columns of floats)
    TODO
    process large patterns in-place leaving only their integral feature
    """
    output = []

    try:
        f = open(resource, "r")
    except OSError:
        for line in resource.splitlines():
            line = line.strip()
            if not line or line.startswith("END"): # FullProf fmt
                break
            try:
                output.append([float(item) for item in line.split()[:3]])
            except ValueError:
                continue
    else:
        while True:
            try: line = f.readline().strip()
            except UnicodeDecodeError: return None

            if not line or line.startswith("END"): # FullProf fmt
                break
            try:
                output.append([float(item) for item in line.split()[:3]])
            except ValueError:
                continue
        f.close()

    if output:
        return dict(content=output, type=Data_type.pattern)

    return None


def export_pattern(node_content):

    output = ""

    for deck in node_content:
        for value in deck:
            output += "%10.5f " % value
        output = output[:-1] + "\n"

    return output


def get_topas_output(path):
    """
    Caveat: separator symbol ":" is user-defined in Topas
    TODO?
    """
    output = {}

    with open(path, "r") as f:
        try: data = f.read(2048)
        except UnicodeDecodeError: return None

    for line in data.splitlines():

        if len(line) > 256: return None # this is definitely not what we expect

        line = line.strip()
        if not line or ":" not in line:
            continue

        key, value = line.split(":", maxsplit=1)
        value = value.strip()
        try: value = float(value)
        except ValueError: pass
        output[key.strip()] = value

    if output:
        return dict(content=output, type=Data_type.property)

    return None


def get_topas_error(path):

    with open(path, "rb") as f:
        topas_log = f.read(1024)

    # Fix problematic Windows encoding
    charmap = set([10, 13] + list(range(32, 128)))
    topas_log = ''.join(chr(byte) for byte in topas_log if byte in charmap)

    if "Abnormal program termination" in topas_log:
        return dict(content=dict(error=topas_log.splitlines()))

    return None


if __name__ == "__main__":
    import os, sys

    for item in os.listdir(sys.argv[1]):
        result = get_pattern(os.path.join(sys.argv[1], item))
        if result:
            print(item, len(result.get("content")))
        else:
            print(item, "Nothing found")
