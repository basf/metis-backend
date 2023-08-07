
#import numpy as np
import xylib

from i_phaseid import MAX_PATT_LEN
from i_data import Data_type


def extract_pattern(binary):

    df = xylib.load_string(binary, 'bruker_raw')
    block = df.get_block(0)

    nrow = block.get_point_count()
    ncol = block.get_column_count()

    output = []
    counter = 0

    for j in range(nrow):

        if counter > MAX_PATT_LEN:
            break

        values = [block.get_column(k).get_value(j) for k in range(1, ncol + 1)]

        try:
            output.append([float(item) for item in values])
            counter += 1
        except ValueError:
            continue

    if output:
        return dict(content=output, type=Data_type.pattern)

    return None
