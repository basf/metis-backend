
import json
import pprint
import urllib3
import threading

import sseclient
from common import make_request, TEST_CREDENTIALS


bff_host = 'http://localhost:3000'

headers, _ = make_request(bff_host + '/v0/auth', TEST_CREDENTIALS, 'POST')
user_session = headers['set-cookie']

thread = threading.Timer(1, lambda: make_request(bff_host + '/v0', '', 'HEAD',
    headers={'Cookie': user_session}))
thread.start()

http = urllib3.PoolManager()
response = http.request('GET', bff_host + '/stream', preload_content=False,
    headers={'Accept': 'text/event-stream', 'Cookie': user_session})
client = sseclient.SSEClient(response)

for event in client.events():

    print("=" * 100)
    try: pprint.pprint(json.loads(event.data))
    except json.decoder.JSONDecodeError: print(event.data)

    print('=' * 100 + 'Test passed')
