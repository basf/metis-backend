
import random
import json
from configparser import ConfigParser

from flask import Blueprint, current_app, request, Response

from yascheduler import CONFIG_FILE
from yascheduler.scheduler import Yascheduler

from utils import get_data_storage, fmt_msg, key_auth, html_formula, is_valid_uuid, ase_unserialize
from i_calculations import Calc_setup
from i_data import Data_type


bp_calculations = Blueprint('calculations', __name__, url_prefix='/calculations')

config = ConfigParser()
config.read(CONFIG_FILE)
yac = Yascheduler(config)

setup = Calc_setup()


@bp_calculations.route("/create", methods=['POST'])
@key_auth
def create():
    """
    Expects
        uuid: uuid
    Returns
        JSON->error: string
        or JSON {uuid}
    """
    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg('Empty or invalid request', 400)

    db = get_data_storage()
    item = db.get_item(uuid)
    if not item:
        return fmt_msg('No such content', 204)

    if item['type'] != Data_type.structure:
        return fmt_msg('Wrong item requested', 400)

    ase_obj = ase_unserialize(item['content'])
    submittable = setup.preprocess(ase_obj, item['name'])

    task_id = yac.queue_submit_task(item['name'], submittable, 'dummy')
    new_uuid = db.put_item(item['name'], task_id, Data_type.calculation)
    db.close()

    return Response(json.dumps(dict(uuid=new_uuid), indent=4), content_type='application/json', status=200)


@bp_calculations.route("/status", methods=['POST'])
@key_auth
def status():
    """
    Expects
        uuid: uuid or uuid[]
    Returns
        JSON->error::string
        or JSON {progress}
    """
    uuid = request.values.get('uuid')
    if not uuid:
        return fmt_msg('Empty request')

    db = get_data_storage()

    if ':' in uuid:
        uuids = set( uuid.split(':') )
        for uuid in uuids:
            if not is_valid_uuid(uuid): return fmt_msg('Invalid content')

        calcs = db.get_items(list(uuids))

        #found_uuids = set( [item['uuid'] for item in calcs] )
        #if found_uuids != uuids:
        #    return fmt_msg('Internal error, consistency broken', 500)

    else:
        if not is_valid_uuid(uuid): return fmt_msg('Invalid content')

        item = db.get_item(uuid)
        calcs = [item] if item else []

    if not calcs: return fmt_msg('No such content', 204)

    for n in range(len(calcs)):
        if calcs[n]['type'] != Data_type.calculation:
            return fmt_msg('Wrong item requested')

        calcs[n]['content'] = int(calcs[n]['content'])

    yac_tasks = yac.queue_get_tasks(jobs=[ item['content'] for item in calcs ])
    if not yac_tasks or len(yac_tasks) != len(calcs):
        return fmt_msg('Internal error, task(s) not scheduled', 500)

    results = []
    for task in yac_tasks:

        found = [item for item in calcs if item['content'] == task['task_id']]
        if not found or len(found) > 1:
            return fmt_msg('Internal error, task(s) lost', 500)

        uuid = found[0]['uuid']
        name = found[0]['name']

        if task['status'] == yac.STATUS_TO_DO:
            progress = 25

        elif task['status'] == yac.STATUS_RUNNING:
            progress = 50

        else:
            progress = 100
            db.drop_item(uuid)

        results.append(dict(
            uuid=uuid,
            type=Data_type.calculation,
            name=html_formula(name),
            progress=progress
        ))

    db.close()
    return Response(json.dumps(results, indent=4), content_type='application/json', status=200)


@bp_calculations.route("/delete", methods=['POST'])
@key_auth
def delete():
    """
    Expects
        uuid: uuid
    Returns
        JSON->error: string
        or JSON {uuid}
    """
    return Response('{}', content_type='application/json', status=200)