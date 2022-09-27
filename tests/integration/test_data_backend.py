#!/usr/bin/env python
"""
NB
curl -XPOST -HKey:... http://localhost:7050/data/create -d 'content={"attributes":{"immutable_id":"x","species":[{"chemical_symbols":["Au"]}],"cartesian_site_positions":[[0,0,0]],"lattice_vectors":[[0,2,2],[2,0,2],[2,2,0]]}}'

curl -XPOST -HKey:... http://localhost:7050/calculations/create -d 'engine=dummy&uuid=0ee24493-5f4a-41f6-a5d7-171e408f4048'
"""
import sys

from common import make_request
import set_path
from utils import API_KEY


host = 'http://localhost:7050'
#host = 'https://peer.metis.science/v0'
#API_KEY = 'XXX' # in case of production server

content = open(sys.argv[1]).read()

try: engine = sys.argv[2]
except IndexError: engine = 'topas'

_, answer = make_request(host + '/data/create', {'content': content}, 'POST', headers={'Key': API_KEY})
print(answer)
print('=' * 100 + 'Data uploaded correctly')

_, answer = make_request(host + '/calculations/create', {'uuid': answer['uuid'], 'engine': engine}, 'POST', headers={'Key': API_KEY})
print(answer)
print('=' * 100 + f'Calc via {engine} engine submitted correctly')
