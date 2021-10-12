#!/usr/bin/env python3

from utils import make_request


host = 'http://localhost:3000'
#host = 'https://gate.basf.science/v0'

headers, answer = make_request(host + '/users/login', {'login': 'basf', 'password': 'fsab'}, 'POST')

assert headers.get('set-cookie')

user_session = headers.get('set-cookie')

_, answer = make_request(host + '/users/me', {'empty': 'empty'}, 'GET', headers={'Cookie': user_session})

print(answer)