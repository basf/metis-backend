
#from pprint import pprint
import json
from unidecode import unidecode
from io import StringIO

from flask import Blueprint, current_app, request, Response
from ase import io as ase_io

from i_data import Data_type
from i_structures import html_formula
from i_structures.struct_utils import (
    detect_format, poscar_to_ase, optimade_to_ase, refine, get_formula, ase_serialize, ase_unserialize
)
from i_structures.cif_utils import cif_to_ase

from utils import get_data_storage, fmt_msg, key_auth, is_plain_text, is_valid_uuid


bp_data = Blueprint('data', __name__, url_prefix='/data')


@bp_data.route("/create", methods=['POST'])
@key_auth
def create():
    """
    Data item recognition and saving logics
    Expects
        content: string
    Returns
        JSON->error: string
        or confirmation object
        {object->uuid, object->type, object->name}
    """
    content = request.values.get('content')
    if not content:
        return fmt_msg('Empty request')

    if not 0 < len(content) < 200000:
        return fmt_msg('Request size is invalid')

    if not is_plain_text(content):
        #return fmt_msg('Request contains unsupported (non-latin) characters')
        content = unidecode(content)

    fmt = detect_format(content)

    if fmt == 'cif':
        ase_obj, error = cif_to_ase(content)

    elif fmt == 'poscar':
        ase_obj, error = poscar_to_ase(content)

    elif fmt == 'optimade':
        ase_obj, error = optimade_to_ase(content)

    else: return fmt_msg('Provided data format unsuitable or not recognized')

    if error: return fmt_msg(error)

    if 'disordered' in ase_obj.info:
        return fmt_msg('Structural disorder is currently not supported')

    ase_obj, error = refine(ase_obj, conventional_cell=True)
    if error:
        return fmt_msg(error)

    formula = get_formula(ase_obj)
    content = ase_serialize(ase_obj)

    db = get_data_storage()
    new_uuid = db.put_item(dict(name=formula), content, Data_type.structure)
    db.close()

    return Response(json.dumps(dict(
        uuid=new_uuid,
        type=Data_type.structure,
        name=html_formula(formula),
    ), indent=4), content_type='application/json', status=200)


@bp_data.route("/listing", methods=['POST'])
@key_auth
def listing():
    """
    Expects
        uuid: uuid or uuid[]
    Returns
        JSON->error: string
        or listing
        [ {object->uuid, object->type, object->name}, ... ]
    """
    uuid = request.values.get('uuid')
    #current_app.logger.warning(uuid)
    if not uuid:
        return fmt_msg('Empty request')

    db = get_data_storage()

    if ':' in uuid:
        uuids = uuid.split(':')
        unique_uuids = set(uuids)
        for uuid in unique_uuids:
            if not is_valid_uuid(uuid): return fmt_msg('Invalid request')

        items = db.get_items(list(unique_uuids))

        #found_uuids = set( [item['uuid'] for item in items] )
        #if found_uuids != unique_uuids:
        #    return fmt_msg('No such content', 204)

    else:
        uuids = [uuid]
        if not is_valid_uuid(uuid): return fmt_msg('Invalid request')

        item = db.get_item(uuid)
        items = [item] if item else []

    if not items: return fmt_msg('No such content', 204)

    db.close()

    items_mapping = {
        item['uuid']: dict(
            uuid=item['uuid'],
            name=html_formula(item['metadata']['name']),
            type=item['type']
        ) for item in items
    }
    # sort according to unique sequence requested
    items = list(filter(None, [items_mapping.get(uuid) for uuid in dict.fromkeys(uuids)]))

    return Response(json.dumps(items, indent=4), content_type='application/json', status=200)


@bp_data.route("/delete", methods=['POST'])
@key_auth
def delete():
    """
    Expects
        uuid: uuid
    Returns
        JSON->error: string
        or JSON empty dict
    """
    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg('Empty or invalid request')

    db = get_data_storage()
    result = db.drop_item(uuid)
    db.close()

    if result:
        return Response('{}', content_type='application/json', status=200)
    return fmt_msg('No such content', 204)


@bp_data.route("/examine", methods=['POST'])
@key_auth
def examine():
    """
    Expects
        uuid: uuid
    Returns
        JSON->error: string
        or JSON empty dict
    """
    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg('Empty or invalid request', 400)

    db = get_data_storage()
    item = db.get_item(uuid)
    db.close()

    if not item:
        return fmt_msg('Sorry these data cannot be shown')

    output = {}

    if item['type'] == Data_type.property:

        output['engine'] = item['metadata'].get('engine', 'default engine') # FIXME "default engine"

        try:
            output['content'] = json.loads(item['content'])
        except Exception:
            return fmt_msg('Sorry these data are erroneous and cannot be shown')

    elif item['type'] == Data_type.structure:

        ase_obj = ase_unserialize(item['content'])

        with StringIO() as fd:
            ase_io.write(fd, ase_obj, format='vasp')
            output['content'] = fd.getvalue()

    else:
        return fmt_msg('Sorry this data type cannot be shown')

    return Response(json.dumps(output, indent=4), content_type='application/json', status=200)
