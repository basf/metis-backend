from scipy import stats, interpolate
import numpy as np


def background(
    intensities,
    theta,
    iterations=50,
    sec_iterations=50,
    curvature=0.000001,
    perc_anchor_pnts=50,
):
    """
    Get background from a pattern provided:
    intensities vs. 2 Theta
    """

    # normalize the intenstities of the input signal
    max_intensity = max(intensities)
    intensities = intensities / max_intensity

    # rebin the data to the number of anchor points passed
    n_anchor_pnts = round(perc_anchor_pnts * len(intensities) / 100)
    rebinned_bg = stats.binned_statistic(
        theta, intensities, statistic="median", bins=n_anchor_pnts
    )

    bg_theta = rebinned_bg.bin_edges
    bin_width = bg_theta[1] - bg_theta[0]
    bg_theta = bg_theta[0 : bg_theta.size - 1]
    bg_theta = bg_theta + bin_width / 2
    bg_intensities = rebinned_bg.statistic

    # determine the first background data
    bg = S_V_BG(bg_intensities, iterations, curvature)

    for _ in range(sec_iterations):
        bg = (bg + S_V_BG(bg, iterations, curvature)) / 2
        bg[0] = bg_intensities[0]

    # inter- and extrapolate the background data to fit the original x-axis
    func = interpolate.interp1d(bg_theta, bg, bounds_error=False, fill_value="extrapolate")
    bg_intensities = func(theta)

    return np.array(bg_intensities * max_intensity)


def S_V_BG(intensities, iterations, curvature):
    background = intensities  # FIXME? copy
    i, j = 0, 1

    while i < iterations:

        while j < background.size - 1:

            m = (background[j - 1] + background[j + 1]) / 2

            if background[j] > m + curvature:
                background[j] = m

            j += 1

        i += 1

    return background
