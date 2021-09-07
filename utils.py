
import uuid

from flask import Response, current_app


SECRET = 'b088a178-47db-458f-b00d-465490f9517a'


def fmt_msg(msg, http_code=400):
    current_app.logger.warning(msg)
    return Response('{"error":"%s"}' % msg, content_type='application/json', status=http_code)


def is_plain_text(test):
    try: test.encode('ascii')
    except: return False
    else: return True


def html_formula(string):
    sub, formula = False, ''
    for symb in string:
        if symb.isdigit() or symb == '.' or symb == '-':
            if not sub:
                formula += '<sub>'
                sub = True
        else:
            if sub and symb != 'd':
                formula += '</sub>'
                sub = False
        formula += symb
    if sub:
        formula += '</sub>'
    return formula


def is_valid_uuid(given):
    try:
        uuid.UUID(str(given))
        return True
    except ValueError:
        return False