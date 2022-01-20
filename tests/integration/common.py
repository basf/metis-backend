
import math
import json
from urllib.parse import urlencode

import httplib2

import set_path
from utils import API_KEY


# see BFF server
TEST_CREDENTIALS = {
    'email': 'test@test.com',
    'password': '123123'
}

req = httplib2.Http()

def make_request(url, data, httpverb='GET', headers={}):

    url = url + '?' + urlencode(data)

    if httpverb == 'GET':
        response, content = req.request(url, httpverb, headers=headers)

    else:
        headers.update({'Content-type': 'application/x-www-form-urlencoded'})
        response, content = req.request(url, httpverb, headers=headers, body=urlencode(data))

    if math.floor(response.status / 100) != 2: raise RuntimeError( "HTTP error %s: %s" % (response.status, content) )

    if not content:
        content = '{}'

    return response, json.loads(content)
