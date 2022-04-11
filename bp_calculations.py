
import random
import json
from configparser import ConfigParser

from flask import Blueprint, current_app, request, Response
import requests
from yascheduler import CONFIG_FILE
from yascheduler.scheduler import Yascheduler

from utils import get_data_storage, fmt_msg, key_auth, webhook_auth, html_formula, is_valid_uuid, ase_unserialize, WEBHOOK_KEY, WEBHOOK_CALC_UPDATE
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
        engine: string, one from the engines supported
        input: {inputname: inputdata, ...}
    Returns
        JSON->error: string
        or JSON {uuid}
    """
    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg('Empty or invalid request', 400)

    engine = request.values.get('engine')
    if not engine:
        engine = 'dummy'

    if engine not in yac.engines:
        return fmt_msg('Wrong engine requested', 400)

    db = get_data_storage()
    item = db.get_item(uuid)
    if not item:
        return fmt_msg('No such content', 204)

    if item['type'] != Data_type.structure:
        return fmt_msg('Wrong item requested', 400)

    ase_obj = ase_unserialize(item['content'])
    input_data = setup.preprocess(ase_obj, engine, item['name'])

    user_input_files = request.values.get('input')
    if user_input_files:
        try: user_input_files = json.loads(user_input_files)
        except Exception:
            return fmt_msg('Invalid input definition', 400)
        if type(user_input_files) != dict:
            return fmt_msg('Invalid input definition', 400)

        for key, value in user_input_files.items():
            if key not in input_data:
                return fmt_msg('Invalid input %s' % key, 400)

            input_data[key] = value

    for chk in yac.engines[engine]['input_files']:
        if chk not in input_data:
            return fmt_msg('Invalid input files', 400)

    input_data['webhook_url'] = 'http://' + request.host + '/calculations/update?Key=' + WEBHOOK_KEY # TODO setup host in config

    task_id = yac.queue_submit_task(item['name'], input_data, engine)
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
            db.drop_item(uuid)
            progress = 100
            # TODO results parsing here

        results.append(dict(
            uuid=uuid,
            type=Data_type.calculation,
            name=html_formula(name),
            progress=progress
        ))

    db.close()
    return Response(json.dumps(results, indent=4), content_type='application/json', status=200)


@bp_calculations.route("/update", methods=['POST'])
@webhook_auth
def update():
    """
    A scheduler webhooks handler, being a proxy to the user interface
    Expects
        task_id: int
        status: int
    Returns
        no content
    """
    task_id = request.values.get('task_id')
    status = request.values.get('status')

    db = get_data_storage()
    item = db.search_item(task_id)
    if item:

        if status == yac.STATUS_DONE:

            db.drop_item(item['uuid'])
            progress = 100
            # TODO results parsing here

        else:
            progress = 50

        # here no response is required
        # TODO status vs. progress
        try: requests.post(WEBHOOK_CALC_UPDATE, data={'uuid': item['uuid'], 'status': progress}, timeout=0.5)
        except requests.exceptions.ReadTimeout: pass

    return Response('', status=204)


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


@bp_calculations.route("/template", methods=['GET'])
def template():
    """
    Expects
        engine: string, one from the engines supported
    Returns
        JSON->error: string
        or JSON {template}
    """
    engine = request.values.get('engine')
    if not engine:
        engine = 'dummy'

    output = {
        'template': setup.get_input(engine),
        'schema': setup.get_schema(engine),
    }
    return Response(json.dumps(output, indent=4), content_type='application/json', status=200)
