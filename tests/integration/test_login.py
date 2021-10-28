#!/usr/bin/env python3

from utils import make_request


host = 'http://localhost:3000'
#host = 'https://gate.basf.science/v0'

headers, answer = make_request(host + '/auth', {'email': 'test@test.com', 'password': '123123'}, 'POST')

assert headers.get('set-cookie')

user_session = headers.get('set-cookie')

_, answer = make_request(host + '/auth', {}, 'GET', headers={'Cookie': user_session})

print(answer)