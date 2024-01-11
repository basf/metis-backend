
import numpy as np

from metis_backend.phaseid.el_groups import groups_abbreviations, chemical_symbols_and_groups, get_elements_or_groups
from metis_backend.phaseid.background import background
from metis_backend.phaseid.histogram import get_best_match


WAVELENGTH = 0.1610184395  # experimental, switch between wavelengths based on 2theta

MIN_Q = 0.5  # inv. angstroms
MAX_Q = 5

N_BINS = 75  # the lower, the faster, the worse

N_BEST_MATCHES = 5

MAX_PATT_LEN = 1200


def get_non_zero_indices(data):
    return np.nonzero(data)[0]


def cleanup_convert_dis(dis):
    valid_idx = get_non_zero_indices(dis[:, 1])
    intensities = dis[(valid_idx), 1]
    dspacing = dis[(valid_idx), 0]

    return dspacing, intensities


def get_q_twotheta_wv(angular_vals, wavelength):
    q_values = np.zeros(len(angular_vals))

    for n, item in enumerate(angular_vals):
        q_values[n] = (4 * np.pi * np.sin(np.deg2rad(item / 2))) / wavelength

    return q_values


def get_twotheta_qwv(q_values, wavelength):
    twotheta = np.zeros(len(q_values))

    for n, q_value in enumerate(q_values):
        twotheta[n] = np.rad2deg(2 * math.asin(wavelength * q_value / (4 * math.pi)))

    return twotheta


def get_q_dspace(dspacings):
    q_values = np.zeros(len(dspacings))

    for n, dspacing in enumerate(dspacings):
        if dspacing > 0:
            q_values[n] = (2 * np.pi) / dspacing

    return q_values


def integrate_patt_q(q_values, intensity, min_q, max_q=10, nbins=10, normalize=False):
    # min_q = np.min(q_values)
    q_bins, intensities = rebin_1d_array(
        q_values, intensity, min_q, max_q, nbins, force_positive=True
    )
    if normalize:
        intensities = intensities / np.max(intensities)

    return q_bins, intensities


def rebin_1d_array(x_vals, y_vals, start_x, end_x, nbins, force_positive=True):
    # create the container arrays
    rebinned_x = np.linspace(start_x, end_x, nbins)
    rebinned_y = np.zeros((nbins,), dtype=float)
    rebinned_x_stride = rebinned_x[1] - rebinned_x[0]

    # trim the X and Y-values to match the integrated range
    trimmed_idx = np.where(x_vals > rebinned_x[0])
    trimmed_x = x_vals[trimmed_idx]
    trimmed_y = y_vals[trimmed_idx]

    trimmed_idx = np.where(trimmed_x < rebinned_x[nbins - 1])
    trimmed_x = trimmed_x[trimmed_idx]
    trimmed_y = trimmed_y[trimmed_idx]

    # copy the intensity array and make the lowest value zero
    integration_array = trimmed_y.copy()
    if force_positive:
        integration_array[np.where(trimmed_y < 0)] = 0

    for n in range(nbins):
        integration_idx = np.where(
            trimmed_x < (rebinned_x[n] + rebinned_x_stride / 2)
        )
        rebinned_y[n] = np.sum(integration_array[integration_idx])
        integration_array[integration_idx] = 0

    return rebinned_x, rebinned_y


def create_reference_array(ref_patterns, min_q, max_q=10, nbins=10):
    n_ref_patterns = np.shape(ref_patterns)[0]
    references = np.zeros((n_ref_patterns, nbins))
    qbins = None

    for n in range(n_ref_patterns):
        dspacings = ref_patterns[n, :, 0]
        intensity = ref_patterns[n, :, 1]
        q_values = get_q_dspace(dspacings)

        qbins, rebinned = integrate_patt_q(
            q_values, intensity, min_q, max_q=max_q, nbins=nbins
        )
        references[n, :] = rebinned / np.max(rebinned)

        # plt.bar(qbins, (references[n,:]),  width = qbins[1]-qbins[0], color = 'mediumseagreen')
        # plt.stem(q_values, intensity)
        # plt.show(block=True)

    assert qbins is not None
    return qbins, references
