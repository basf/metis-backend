
import sys

from common import make_request, TEST_CREDENTIALS


bff_host = 'http://localhost:3000'
#bff_host = 'https://gate.basf.science'

content = open(sys.argv[1]).read()

headers, _ = make_request(bff_host + '/v0/auth', TEST_CREDENTIALS, 'POST')
user_session = headers['set-cookie']

_, answer = make_request(bff_host + '/v0/data', {'content': content}, 'POST', headers={'Cookie': user_session})
print(answer)
