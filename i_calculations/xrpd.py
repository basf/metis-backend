import random
import string

from i_data import Data_type


def get_pattern(resource):
    """
    Check if a file / given string contains computed XRPD pattern
    (basicaly, two columns of floats)
    TODO
    process large patterns in-place leaving only their integral feature
    """
    output = []

    try:
        f = open(resource)
    except OSError:
        for line in resource.splitlines():
            if line.startswith("END"): # FullProf fmt
                break
            try:
                output.append([float(item) for item in line.split(maxsplit=1)])
            except ValueError:
                continue

    else:
        while True:
            line = f.readline()
            if not line or line.startswith("END"): # FullProf fmt
                break
            try:
                output.append([float(item) for item in line.split(maxsplit=1)])
            except ValueError:
                continue
        f.close()

    if output:

        try: ymax = max([y for _, y in output]) # normalize
        except ValueError: return None

        output = [[x, int(round(y / ymax * 200))] for x, y in output]
        return dict(content=output, type=Data_type.pattern)

    return None


def get_pattern_name():
    """
    TODO generate meaningful name based on the pattern features?
    """
    symbols = string.ascii_uppercase
    return "XRPD-" + "".join(random.choice(symbols) for _ in range(6))


if __name__ == "__main__":
    import os, sys

    for item in os.listdir(sys.argv[1]):
        result = get_pattern(os.path.join(sys.argv[1], item))
        if result:
            print(item, len(result.get("content")))
        else:
            print(item, "Nothing found")
