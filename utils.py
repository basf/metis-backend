
import uuid
import pickle
import base64

from flask import Response, current_app


SECRET = 'b088a178-47db-458f-b00d-465490f9517a'


def fmt_msg(msg, http_code=400):
    if http_code == 500:
        current_app.logger.critical(msg)
    else:
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


def ase_serialize(ase_obj):
    return base64.b64encode(pickle.dumps(ase_obj, protocol=4)).decode('ascii')


def ase_unserialize(string):
    return pickle.loads(base64.b64decode(string))




if __name__ == "__main__":

    from ase.spacegroup import crystal

    crystal_obj = crystal(
        ('Sr', 'Ti', 'O', 'O'),
        basis=[(0, 0.5, 0.25), (0, 0, 0), (0, 0, 0.25), (0.255, 0.755, 0)],
        spacegroup=140, cellpar=[5.511, 5.511, 7.796, 90, 90, 90],
        primitive_cell=True
    )
    #print(crystal_obj)

    repr = ase_serialize(crystal_obj)
    #print(repr)

    new_obj = ase_unserialize(repr)
    #print(new_obj)

    assert new_obj == crystal_obj