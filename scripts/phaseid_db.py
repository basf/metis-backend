#!/usr/bin/env python3

import sys
import logging
#from io import BytesIO

import matplotlib.pyplot as plt
import numpy as np
#from PIL import Image

import set_path
from metis_backend.helpers import get_data_storage
from metis_backend.datasources.fmt import detect_format
from metis_backend.datasources.xrpd import extract_pattern
from metis_backend.structures import html_to_latex
from metis_backend.calculations.xrpd import get_pattern
from metis_backend.phaseid import (
    WAVELENGTH, MIN_Q, MAX_Q, N_BINS, N_BEST_MATCHES,
    background,
    get_best_match,
    create_reference_array,
    get_q_twotheta_wv,
    integrate_patt_q,
    get_q_dspace,
    cleanup_convert_dis,
    get_elements_or_groups,
)


STRICT_ARITY = False
N_TEST_MATCHES = 0 or N_BEST_MATCHES

target = sys.argv[1]
with open(target, "rb") as f:
    contents = f.read()

fmt = detect_format(contents)

if fmt == "xy":
    pattern = get_pattern(target)
elif fmt == "raw":
    pattern = extract_pattern(contents)
else:
    raise RuntimeError("Unknown input pattern format given")

pattern = np.array(pattern["content"])

els = get_elements_or_groups("-".join(sys.argv[2:]))
assert els, "Unknown elements or groups given"
if len(els) == 1 and not STRICT_ARITY:
    STRICT_ARITY = True
    logging.warning("For only one element, the search space is reduced to unary compounds")

db = get_data_storage()
patterns_db, patterns_ids, names = db.get_refdis(els, STRICT_ARITY)
db.close()

assert len(patterns_db), "Cannot match this pattern against the elements given"

# BOF phase ID algo
_, ref_patterns_db = create_reference_array(patterns_db, MIN_Q, MAX_Q, N_BINS)

intensities = pattern[:, 1]
twoteta = pattern[:, 0]
max_intens = np.max(intensities)

intensities_bg = background(
    intensities,
    twoteta,
    iterations=20,
    sec_iterations=20,
    curvature=0.0001,
    perc_anchor_pnts=20,
)
intens_minus_bg = intensities - intensities_bg
qhisto_diffpatt = integrate_patt_q(
    get_q_twotheta_wv(twoteta, WAVELENGTH), # convert two theta to Q-space
    intens_minus_bg,
    MIN_Q,
    MAX_Q,
    N_BINS,
    normalize=True,
)

best_match_idx, _, __ = get_best_match(
    ref_patterns_db, qhisto_diffpatt, N_TEST_MATCHES
)
# EOF phase ID algo

for item in best_match_idx:
    logging.warning(('Match:', patterns_ids[item], names[item]))

_, axs = plt.subplots(N_TEST_MATCHES + 1, 1)

axs[0].plot(twoteta, intensities, color="red")
axs[0].set_title('$Sample$', fontdict={'fontsize': 6}, loc='left', y=0.6)
axs[0].set_xticks([])
axs[0].set_yticks([])

for n in range(min(N_TEST_MATCHES, len(best_match_idx))):

    nplot = n + 1

    best_patt = patterns_db[best_match_idx[n], :, :]
    best_patt_conv = cleanup_convert_dis(best_patt)

    axs[nplot].set_xlim(0, MAX_Q)
    axs[nplot].bar(
        qhisto_diffpatt[0],
        qhisto_diffpatt[1] * max_intens,
        width=(MAX_Q - MIN_Q) / N_BINS,
        color="green",
    )
    #axs[nplot].plot(
    #    get_q_twotheta_wv(twoteta, WAVELENGTH),
    #    intensities_bg,
    #    color="black",
    #)
    axs[nplot].plot(
        get_q_twotheta_wv(twoteta, WAVELENGTH),
        intens_minus_bg,
        color="black",
    )
    axs[nplot].stem(
        get_q_dspace(best_patt_conv[0]),
        (best_patt_conv[1] * max_intens),
        linefmt="blue",
        basefmt="blue",
    )
    axs[nplot].set_xticks([])
    axs[nplot].set_yticks([])
    axs[nplot].set_title(html_to_latex(names[best_match_idx[n]]).replace(" ", "\;"), fontdict={'fontsize': 6}, loc='left', y=0.6)
    #axs[nplot].legend()

plt.margins(0.1)
plt.subplots_adjust(bottom=0.15)
plt.savefig('result.png', dpi=250)

#raise SystemExit
#mem = BytesIO()
#plt.savefig(mem, format='png', dpi=250)
#mem.seek(0)
#im = Image.open(mem)
#im2 = im.convert('RGB').convert('P', palette=Image.ADAPTIVE)
#im2.save('result.png')
