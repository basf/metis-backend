#!/usr/bin/env python3

from common import make_request, TEST_CREDENTIALS


host = 'http://localhost:3000/v0'
#host = 'https://gate.metis.science/v0'

headers, answer = make_request(host + '/auth', TEST_CREDENTIALS, 'POST')
assert headers.get('set-cookie')

user_session = headers.get('set-cookie')
print(user_session)

_, answer = make_request(host + '/auth', {}, 'GET', headers={'Cookie': user_session})
print(answer)
print('='*100 + 'Authorized correctly')

#_, answer = make_request(host + '/datasources', {}, 'GET', headers={'Cookie': user_session})
#print(answer)
#print('='*100 + 'Data loaded correctly')
