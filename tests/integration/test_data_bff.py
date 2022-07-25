#!/usr/bin/env python3

import sys

from common import make_request, TEST_CREDENTIALS


bff_host = 'http://localhost:3000/v0'
#bff_host = 'https://gate.basf.science'

content = open(sys.argv[1]).read()

headers, _ = make_request(bff_host + '/auth', TEST_CREDENTIALS, 'POST')
user_session = headers['set-cookie']

print('='*100 + 'Authorized correctly')

_, answer = make_request(bff_host + '/datasources', {'content': content}, 'POST', headers={'Cookie': user_session})
print(answer)
print('='*100 + 'Data upload requested')

# NB we have to accept SSE to make further processing
