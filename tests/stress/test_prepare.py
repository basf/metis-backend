#!/usr/bin/env python

import sys
import random
import logging

from helpers import gen_data_item

import set_path
from i_data import Data_type
from utils import get_data_storage


FAKE_NODES = 5000
FAKE_LINKS = 5000

ALLOWED_TRANSITIONS = (
    (Data_type.structure, Data_type.property),
    (Data_type.structure, Data_type.pattern),
    (Data_type.pattern, Data_type.structure),
    (Data_type.pattern, Data_type.property),
    (Data_type.property, Data_type.structure),
    (Data_type.property, Data_type.pattern),
)

db = get_data_storage()
used_uuids = {}

for _ in range(FAKE_NODES):
    selected_dtype = random.choice(
        (
            Data_type.calculation,
            Data_type.structure,
            Data_type.property,
            Data_type.pattern,
        )
    )
    used_uuids.setdefault(selected_dtype, []).append(
        db.put_item(*gen_data_item(selected_dtype))
    )

count_links, num_iters = 0, 0

while True:
    source_dtype, target_dtype = random.choice(ALLOWED_TRANSITIONS)
    source, target = random.choice(used_uuids[source_dtype]), random.choice(
        used_uuids[target_dtype]
    )

    if db.put_link(source, target):
        count_links += 1
    # else:
    #    logging.warning('Duplicate link between %s and %s occured on %s-th step' % (source, target, count_links))

    if count_links == FAKE_LINKS:
        break

    num_iters += 1
    if num_iters > FAKE_LINKS * 3:
        break

db.close()
