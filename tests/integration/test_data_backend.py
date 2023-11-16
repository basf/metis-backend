#!/usr/bin/env python
"""
NB this is equivalent to the curl calls, e.g.
curl -XPOST -HKey:... http://localhost:7050/data/create -d 'content={"attributes":{"immutable_id":42,"species":[{"chemical_symbols":["Au"]}],"cartesian_site_positions":[[0,0,0]],"lattice_vectors":[[0,2,2],[2,0,2],[2,2,0]]}}'
curl -XPOST -HKey:... http://localhost:7050/calculations/create -d 'engine=dummy&uuid=$UUID'
curl -XPOST -HKey:... http://localhost:7050/calculations/phaseid -d 'uuid=$UUID&els=Al-K-O'
curl -XPOST -HKey:... http://localhost:7050/data/import -d 'id=S1254081'
"""

import sys
import os.path
import base64

from common import make_request

import set_path
from metis_backend.helpers import API_KEY
from metis_backend.datasources.fmt import detect_format


host = 'http://localhost:7050'
#API_KEY = 'XXX'  # redefine for production

try:
    fname = sys.argv[1]
except IndexError:
    fname = None
    content = """{"attributes":{"immutable_id":42, "species":[{"chemical_symbols":
["Au"]}],"cartesian_site_positions":[[0,0,0]],"lattice_vectors":[[0,2,2],[2,0,2],[2,2,0]]}}"""

try:
    content = open(fname).read()
except UnicodeDecodeError:
    content = open(fname, "rb").read()
except TypeError:
    pass

if fname:
    fname = os.path.basename(fname)

fmt = detect_format(content)
if fmt == 'raw':
    content = b'base64,' + base64.b64encode(content)

try: engine = sys.argv[2]
except IndexError: engine = None

print(f"Requested calculation: {engine or 'NO'}")

#_, answer = make_request(host + '/data/create', {'content': content, 'name': fname}, 'POST', headers={'Key': API_KEY})
_, answer = make_request(host + '/data/create', {'content': content, 'fmt': fmt, 'name': fname}, 'POST', headers={'Key': API_KEY})
print(answer)
print('=' * 100 + 'Data uploaded correctly')

if engine:
    _, answer = make_request(host + '/calculations/create', {'uuid': answer['uuid'], 'engine': engine}, 'POST', headers={'Key': API_KEY})
    print(answer)
    print('=' * 100 + f'Calc via {engine} engine submitted correctly')

print('=' * 100 + 'Test passed')
