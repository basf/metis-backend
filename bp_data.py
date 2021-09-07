
import random
import json

from flask import Blueprint, current_app, request, Response

from mpds_ml_labs.struct_utils import detect_format, poscar_to_ase, refine, get_formula
from mpds_ml_labs.cif_utils import cif_to_ase

from utils import SECRET, fmt_msg, is_plain_text, html_formula, is_valid_uuid
from i_data import Data_Storage


bp_data = Blueprint('data', __name__, url_prefix='/data')


@bp_data.route("/create", methods=['POST'])
def create():
    """
    Data item recognition and saving logics
    Expects
        secret: string
        content: string
    Returns
        JSON->error: string
        or confirmation object
        {object->uuid, object->type, object->name}
    """
    secret = request.values.get('secret')
    if secret != SECRET:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return fmt_msg('Unauthorized', 401)

    content = request.values.get('content')
    if not content:
        current_app.logger.warning("Illegal request from a known user")
        return fmt_msg('Empty or invalid content')

    if not 0 < len(content) < 200000:
        return fmt_msg('Request size is invalid')

    if not is_plain_text(content):
        return fmt_msg('Request contains unsupported (non-latin) characters')

    fmt = detect_format(content)

    if fmt == 'cif':
        ase_obj, error = cif_to_ase(content)
        if error:
            return fmt_msg(error)

    elif fmt == 'poscar':
        ase_obj, error = poscar_to_ase(content)
        if error:
            return fmt_msg(error)

    else: return fmt_msg('Provided data format is not supported')

    ase_obj, error = refine(ase_obj)
    if error:
        return fmt_msg(error)

    formula = get_formula(ase_obj)
    #content = ase_to_json(ase_obj)

    db = Data_Storage()
    uuid = db.put_item(formula, content)
    db.close()

    return Response(json.dumps(dict(
        uuid=uuid,
        type=random.randint(0, 3),
        name=html_formula(formula),
    ), indent=4), content_type='application/json', status=200)


@bp_data.route("/list", methods=['POST'])
def list():
    """
    Expects
        secret: string
        uuid: uuid or uuid[]
    Returns
        JSON->error: string
        or listing
        [ {object->uuid, object->type, object->name}, ... ]
    """
    secret = request.values.get('secret')
    if secret != SECRET:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return fmt_msg('Unauthorized', 401)

    uuid = request.values.get('uuid')
    current_app.logger.warning(uuid)
    if not uuid or not is_valid_uuid(uuid):
        current_app.logger.warning("Illegal request from a known user")
        return fmt_msg('Empty or invalid content')

    db = Data_Storage()

    if ':' in uuid:
        items = db.get_items(uuid.split(':'))
    else:
        item = db.get_item(uuid)
        items = [item] if item else []

    db.close()

    items = [dict(uuid=item.uuid, name=item.label, type=item.type) for item in items]
    return Response(json.dumps(items, indent=4), content_type='application/json', status=200)


@bp_data.route("/delete", methods=['POST'])
def delete():
    """
    Expects
        secret: string
        uuid: uuid
    Returns
        JSON->error: string
        or JSON empty dict
    """
    secret = request.values.get('secret')
    if secret != SECRET:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return fmt_msg('Unauthorized', 401)

    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        current_app.logger.warning("Illegal request from a known user")
        return fmt_msg('Empty or invalid content')

    db = Data_Storage()
    result = db.drop_item(uuid)
    db.close()

    if result:
        return Response('{}', content_type='application/json', status=200)
    return fmt_msg('No such content', 204)