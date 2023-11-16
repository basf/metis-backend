#!/usr/bin/env python

import sys
import random
import logging

from helpers import POSSIBLE_CONTENT

import set_path
from metis_backend.helpers import get_data_storage


db = get_data_storage()

accumulated = []

for _ in range(100):
    logging.warning("=" * 100)

    found = db.search_item(random.choice(POSSIBLE_CONTENT))
    assert found

    item = db.get_item(found["uuid"], with_links=True)

    accumulated += [found["uuid"]]
    accumulated += item["children"]
    accumulated += item["parents"]
    logging.warning("Collected %s items" % len(accumulated))

    items = db.get_items(accumulated, with_links=True)

    children, parents = [], []
    for one in items:
        children += one["children"]
        parents += one["parents"]

    logging.warning("Got %s children and %s parents" % (len(children), len(parents)))

db.close()
