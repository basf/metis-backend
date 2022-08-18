
import sys
import json
import urllib3
import threading
from queue import Queue

import sseclient
from common import make_request, TEST_CREDENTIALS


bff_host = 'http://localhost:3000'
#bff_host = 'https://gate.basf.science'


def submit_structure(comms, user_session, content):
    make_request(bff_host + '/v0/datasources', {'content': content}, 'POST', headers={'Cookie': user_session})
    print('Structure submitted')


def submit_calc(comms, user_session):
    answer = comms.get()
    print("submit_calc" + "=" * 100)
    print(answer)
    data_id = sorted(answer['data'], key=lambda x: x['id'])[-1]['id'] # take the most recent id

    make_request(bff_host + '/v0/calculations', {'dataId': data_id}, 'POST', headers={'Cookie': user_session})
    print('Calc submitted')


headers, _ = make_request(bff_host + '/v0/auth', TEST_CREDENTIALS, 'POST')
user_session = headers['set-cookie']

content = open(sys.argv[1]).read()

queue = Queue()

thread = threading.Timer(1, submit_structure, args=(queue, user_session, content))
thread.start()

thread = threading.Timer(2, submit_calc, args=(queue, user_session))
thread.start()

http = urllib3.PoolManager()
response = http.request('GET', bff_host + '/stream', preload_content=False, headers={'Accept': 'text/event-stream', 'Cookie': user_session})
client = sseclient.SSEClient(response)
for event in client.events():
    answer = json.loads(event.data)

    print("=" * 100)
    print(answer)
    assert len(answer['data'])

    error = answer['data'][0].get('error')
    if error:
        raise RuntimeError
    queue.put(answer)
