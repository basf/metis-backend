
import os.path
import string
import random
import uuid
from functools import wraps
from configparser import ConfigParser

from flask import Response, current_app, request

from metis_backend.datasources import Data_storage


CONFIG_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), '../conf/env.ini'))
assert os.path.exists(CONFIG_PATH)
config = ConfigParser()
config.read(CONFIG_PATH)

API_KEY =             config.get('api', 'key') # NB not to confuse with the BFF API key
WEBHOOK_KEY =         config.get('webhooks', 'key')
WEBHOOK_CALC_UPDATE = config.get('webhooks', 'calc_update')
WEBHOOK_CALC_CREATE = config.get('webhooks', 'calc_create')
TMP_PHASEID_DIR = config.get('local', 'tmp_phaseid_dir')
TMP_PHASEID_URL = config.get('local', 'tmp_phaseid_url')

MAX_UPLOAD_SIZE = 1024 * 1024


def get_data_storage():
    """
    Persistence layer, to be used throughout the codebase
    """
    return Data_storage(
        **dict(config.items('db'))
    )


def key_auth(f):
    """
    Flask auth decorator
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get('Key')
        if key == API_KEY:
            return f(*args, **kwargs)

        return fmt_msg('Unauthorized', 401)

    return decorated


def webhook_auth(f):
    """
    Another auth decorator
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.values.get('Key')
        if key == WEBHOOK_KEY:
            return f(*args, **kwargs)

        return fmt_msg('Unauthorized', 401)

    return decorated


def fmt_msg(msg, http_code=400):
    current_app.logger.error(msg)
    return Response('{"error":"%s"}' % msg, content_type='application/json', status=http_code)


def is_plain_text(test):
    try: test.encode('ascii')
    except: return False
    else: return True


def is_valid_uuid(given):
    try:
        uuid.UUID(str(given))
        return True
    except ValueError:
        return False


def get_rnd_string(length=12):
    symbols = string.digits + string.ascii_letters
    return "".join(random.choice(symbols) for _ in range(length))


def get_name(default, prefix):

    if default:

        maxnamelen = 24
        if len(default) > maxnamelen:
            default = default[:maxnamelen]

        if "." in default[-5:]:
            default = ".".join(default.split(".")[:-1])
        if default.endswith('-') or default.endswith('+') or default.endswith(','):
            default = default[:-1]

        return default

    return prefix + "-" + get_rnd_string(5)
