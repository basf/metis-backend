#!/usr/bin/env python3

from common import make_request, TEST_CREDENTIALS


host = 'http://localhost:3000/v0'
#host = 'https://gate.basf.science/v0'

headers, answer = make_request(host + '/auth', TEST_CREDENTIALS, 'POST')
assert headers.get('set-cookie')

user_session = headers.get('set-cookie')

_, answer = make_request(host + '/auth', {}, 'GET', headers={'Cookie': user_session})
print(answer)

_, answer = make_request(host + '/data', {}, 'GET', headers={'Cookie': user_session})
print(answer)