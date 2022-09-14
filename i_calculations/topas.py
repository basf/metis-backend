
def check_xrpd(resource):
    """
    Check if a file contains computed xrpd pattern
    (two columns of floats)
    TODO
    process large patterns in-place leaving only their integral feature
    """
    output = []

    f = open(resource)
    while True:
        line = f.readline()
        if not line:
            break
        try:
            output.append([float(item) for item in line.split()])
        except ValueError:
            output = False
            break

    f.close()

    if output:
        # normalize
        ymax = max([y for _, y in output])
        output = [[x, int(round(y / ymax * 200))] for x, y in output]
        return dict(content=output)

    return None


if __name__ == "__main__":

    import os, sys

    for item in os.listdir(sys.argv[1]):
        result = check_xrpd(os.path.join(sys.argv[1], item))
        if result:
            print(item, len(result.get('value')))
        else:
            print(item, 'Nothing found')
