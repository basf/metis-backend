#!/usr/bin/env python3
"""
NB curl -XPOST -HKey:... http://localhost:7070/data/create -d 'content={"attributes":{"immutable_id":"x","species":[{"chemical_symbols":["Au"]}],"cartesian_site_positions":[[0,0,0]],"lattice_vectors":[[0,2,2],[2,0,2],[2,2,0]]}}'
"""
import sys

from common import make_request
import set_path
from utils import API_KEY


host = 'http://localhost:7070'
#host = 'https://peer.basf.science/v0'

content = open(sys.argv[1]).read()

_, answer = make_request(host + '/data/create', {'content': content}, 'POST', headers={'Key': API_KEY})
print(answer)
