
import random
import json
from configparser import ConfigParser

from flask import Blueprint, current_app, request, Response

from yascheduler import CONFIG_FILE
from yascheduler.scheduler import Yascheduler

from utils import SECRET, fmt_msg, is_valid_uuid, ase_unserialize
from i_data import Data_Storage
from i_calculations import Calc_Setup


bp_calculations = Blueprint('calculations', __name__, url_prefix='/calculations')

config = ConfigParser()
config.read(CONFIG_FILE)
yac = Yascheduler(config)

calcs = Calc_Setup()


@bp_calculations.route("/create", methods=['POST'])
def create():
    """
    Expects
        secret: string
        uuid: uuid
    Returns
        JSON->error: string
        or JSON {uuid}
    """
    secret = request.values.get('secret')
    if secret != SECRET:
        return fmt_msg('Unauthorized', 401)

    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg('Empty or invalid request', 400)

    db = Data_Storage()
    item = db.get_item(uuid)
    if not item:
        return fmt_msg('No such content', 204)

    if item['label'] == '$':
        return fmt_msg('Wrong item requested', 400)

    ase_obj = ase_unserialize(item['content'])
    submittable = calcs.preprocess(ase_obj, item['label'])

    task_id = yac.queue_submit_task(item['label'], submittable)
    new_uuid = db.put_item('$', str(task_id), 1)
    db.close()

    return Response(json.dumps(dict(uuid=new_uuid), indent=4), content_type='application/json', status=200)


@bp_calculations.route("/status", methods=['POST'])
def status():
    """
    Expects
        secret: string
        uuid: uuid or uuid[]
    Returns
        JSON->error::string
        or JSON {progress}
    """
    secret = request.values.get('secret')
    if secret != SECRET:
        return fmt_msg('Unauthorized', 401)

    uuid = request.values.get('uuid')
    if not uuid:
        return fmt_msg('Empty request')

    db = Data_Storage()

    if ':' in uuid:
        uuids = set( uuid.split(':') )
        for uuid in uuids:
            if not is_valid_uuid(uuid): return fmt_msg('Invalid content')

        calcs = db.get_items(list(uuids))

        found_uuids = set( [item['uuid'] for item in calcs] )
        if found_uuids != uuids:
            return fmt_msg('Internal error, consistency broken', 500)

    else:
        if not is_valid_uuid(uuid): return fmt_msg('Invalid content')

        item = db.get_item(uuid)
        calcs = [item] if item else []

    if not calcs: return fmt_msg('No such content', 204)

    for n in range(len(calcs)):
        if calcs[n]['label'] != '$': return fmt_msg('Wrong item requested')
        calcs[n]['content'] = int(calcs[n]['content'])

    yac_tasks = yac.queue_get_tasks(jobs=[ item['content'] for item in calcs ])
    if not yac_tasks or len(yac_tasks) != len(calcs):
        return fmt_msg('Internal error, task(s) not scheduled', 500)

    results = []
    for task in yac_tasks:

        found = [item['uuid'] for item in calcs if item['content'] == task['task_id']]
        if not found or len(found) > 1:
            return fmt_msg('Internal error, task(s) lost', 500)

        uuid = found[0]

        if task['status'] == yac.STATUS_TO_DO:
            results.append(dict(uuid=uuid, progress=25))

        elif task['status'] == yac.STATUS_RUNNING:
            results.append(dict(uuid=uuid, progress=50))

        else:
            results.append(dict(uuid=uuid, progress=100))
            db.drop_item(uuid)

    db.close()
    return Response(json.dumps(results, indent=4), content_type='application/json', status=200)
