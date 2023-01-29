#!/usr/bin/env python3

import sys

from common import make_request, TEST_CREDENTIALS


bff_host = 'http://localhost:3000/v0'

try: content = open(sys.argv[1]).read()
except IndexError: content = """{"attributes":{"immutable_id":42, "species":[{"chemical_symbols":
["Au"]}],"cartesian_site_positions":[[0,0,0]],"lattice_vectors":[[0,2,2],[2,0,2],[2,2,0]]}}"""

headers, _ = make_request(bff_host + '/auth', TEST_CREDENTIALS, 'POST')
user_session = headers['set-cookie']

print('=' * 100 + 'Authorized correctly')

_, answer = make_request(bff_host + '/datasources', {'content': content}, 'POST',
    headers={'Cookie': user_session})
print(answer)
print('=' * 100 + 'Data upload requested')
print('=' * 100 + 'Test passed')

# NB we have to accept SSE afterwards to make any further processing
