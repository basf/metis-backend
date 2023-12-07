
import logging
import tempfile

import xylib
import numpy as np
from nexusformat.nexus import nxload

from metis_backend.phaseid import MAX_PATT_LEN
from metis_backend.datasources import Data_type


def extract_pattern(binary):

    df = xylib.load_string(binary, 'bruker_raw')
    block = df.get_block(0)

    nrow = block.get_point_count()
    ncol = block.get_column_count()

    #logging.warning(nrow)
    #logging.warning(ncol)

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


def nexus_to_xye(bin_string):
    """
    ESRF Grenoble ID31 beamline data conversion
    both old pre-2023 & new post-2023 formats supported
    """
    tmp = tempfile.NamedTemporaryFile()
    tmp.write(bin_string)
    tmp.flush()
    pattern = nxload(tmp.name)

    try:
        if 'p3_integrate_2th' in pattern.results:
            return dict(
                content=np.transpose(
                np.array((
                    pattern.results.p3_integrate_2th.integrated['2th'],
                    pattern.results.p3_integrate_2th.integrated['intensity'],
                    pattern.results.p3_integrate_2th.integrated['intensity_errors']
                ))
                ).tolist(),
                type=Data_type.pattern
            )
        elif 'integrate' in pattern.results:
            return dict(
                content=np.transpose(
                np.array((
                    pattern.results.integrate.diffractogram['2th'],
                    pattern.results.integrate.diffractogram.data,
                    pattern.results.integrate.diffractogram.data_errors
                ))
                ).tolist(),
                type=Data_type.pattern
            )
        else:
            logging.critical("Synchrotron format unknown")
            return None

    except Exception:
        logging.critical("Synchrotron format broken")
        return None

    finally:
        tmp.close()
