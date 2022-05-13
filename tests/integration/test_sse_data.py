
import sys
import json
import urllib3
import threading
from pprint import pprint

import sseclient
from common import make_request, TEST_CREDENTIALS


bff_host = 'http://localhost:3000'
#bff_host = 'https://gate.basf.science'

def submit_structure(content, user_session):
    _, answer = make_request(bff_host + '/v0/datasources', {'content': content}, 'POST', headers={'Cookie': user_session})
    print('Structure submitted')
    print(answer)

def submit_calc(user_session):
    _, answer = make_request(bff_host + '/v0/calculations', {'dataId': 5}, 'POST', headers={'Cookie': user_session})
    print('Calc submitted')
    print(answer)

headers, _ = make_request(bff_host + '/v0/auth', TEST_CREDENTIALS, 'POST')
user_session = headers['set-cookie']

content = open(sys.argv[1]).read()

#thread = threading.Timer(1, submit_structure, args=[content, user_session])
#thread.start()

thread = threading.Timer(2, submit_calc, args=[user_session])
thread.start()

http = urllib3.PoolManager()
response = http.request('GET', bff_host + '/stream', preload_content=False, headers={'Accept': 'text/event-stream', 'Cookie': user_session})
client = sseclient.SSEClient(response)
for event in client.events():
    pprint(json.loads(event.data))
