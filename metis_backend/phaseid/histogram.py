import numpy as np

# import matplotlib.pyplot as plt


def get_best_match(ref_array, exp_array, n_best_matches):
    """
    Compute residual via histogram comparison
    """

    n_ref_patterns = np.shape(ref_array)[0]
    nbins = np.shape(ref_array)[1]
    sqrt_exp_intensities = np.sqrt(exp_array[1])
    sqrt_ref_array = np.sqrt(ref_array)

    residual = np.absolute(
        np.subtract(
            sqrt_ref_array,
            np.broadcast_to(
                sqrt_exp_intensities, (n_ref_patterns, nbins)
            ),
        )
    )

    rel_residual_sum = np.sum(residual, axis=1) / np.sum(exp_array)
    idx_best_matches = rel_residual_sum.argsort()[:n_best_matches]
    # idx_worst_matches = (rel_residual_sum).argsort()[n_best_matches:]

    # plot data for debugging
    # i = 0
    # x_axis = np.linspace(0, 1, nbins)

    # for i in range(n_best_matches):
    #     plt.bar(x_axis, sqrt_exp_intensities,  width = (1/nbins), color = 'mediumseagreen')
    #     plt.bar(x_axis, -(ref_array[idx_best_matches[i],:]),  width = (1/nbins), color = 'black')
    #     plt.bar(x_axis, residual[idx_best_matches[i],:],  width = (1/nbins), color = 'red', alpha = 0.7)
    #     plt.show(block=True)

    # i = 0
    # x_axis = np.linspace(0, 1, nbins)

    # for i in range(n_best_matches):
    #     plt.bar(x_axis, sqrt_exp_intensities,  width = (1/nbins), color = 'mediumseagreen')
    #     plt.bar(x_axis, -(ref_array[idx_worst_matches[i],:]),  width = (1/nbins), color = 'black')
    #     plt.bar(x_axis, residual[idx_worst_matches[i],:],  width = (1/nbins), color = 'red', alpha = 0.7)
    #     plt.show(block=True)

    return idx_best_matches, ref_array[idx_best_matches, :], residual[idx_best_matches, :]
