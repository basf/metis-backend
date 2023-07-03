
import sys
import json
import urllib3
import threading
from queue import Queue

import sseclient
from common import make_request, TEST_CREDENTIALS


bff_host = 'http://localhost:3000'


def submit_structure(comms, user_session, content):
    make_request(bff_host + '/v0/datasources', {'content': content}, 'POST',
        headers={'Cookie': user_session})
    print('=' * 100 + 'Structure submitted')


def submit_calc(comms, user_session):
    answer = comms.get()
    print('=' * 100 + 'Submitting calculation')
    print(answer)
    data_id = sorted(answer['data'], key=lambda x: x['id'])[-1]['id'] # take the most recent id

    make_request(bff_host + '/v0/calculations', {'dataId': data_id, 'engine': 'topas'}, 'POST',
        headers={'Cookie': user_session})
    print('=' * 100 + 'Calculation submitted')


def list_calcs(comms, user_session):
    make_request(bff_host + '/v0/calculations', {}, 'GET',
        headers={'Cookie': user_session})


headers, _ = make_request(bff_host + '/v0/auth', TEST_CREDENTIALS, 'POST')
user_session = headers['set-cookie']

try: content = open(sys.argv[1]).read()
except IndexError: content = """{"attributes":{"immutable_id":42, "species":[{"chemical_symbols":
["Au"]}],"cartesian_site_positions":[[0,0,0]],"lattice_vectors":[[0,2,2],[2,0,2],[2,2,0]]}}"""

queue = Queue()

thread = threading.Timer(1, submit_structure, args=(queue, user_session, content))
thread.start()

thread = threading.Timer(2, submit_calc, args=(queue, user_session))
thread.start()

thread = threading.Timer(3, list_calcs, args=(queue, user_session))
thread.start()

http = urllib3.PoolManager()
response = http.request('GET', bff_host + '/stream', preload_content=False,
    headers={'Accept': 'text/event-stream', 'Cookie': user_session})
client = sseclient.SSEClient(response)
for event in client.events():
    try:
        answer = json.loads(event.data)
    except json.decoder.JSONDecodeError:
        print('=' * 100 + 'JSON error')
        print(event)
        raise

    print("=" * 100)
    print(answer)
    assert len(answer['data'])

    error = answer['data'][0].get('error')
    if error:
        raise RuntimeError(error)

    queue.put(answer)

    if 'progress' in event.data: # TODO get calculation stream
        print('=' * 100 + 'Test passed')
