
import json
import logging
import pprint
import urllib3

import sseclient


url = 'http://localhost:3000/stream'
#url = 'https://gate.basf.science/stream'

logging.warning('Connecting to a stream %s' % url)

http = urllib3.PoolManager()
response = http.request('GET', url, preload_content=False, headers={'Accept': 'text/event-stream'})
client = sseclient.SSEClient(response)

for event in client.events():

    try: pprint.pprint(json.loads(event.data))
    except json.decoder.JSONDecodeError: print(event.data)
