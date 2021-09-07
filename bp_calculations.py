
import random
import json
from configparser import ConfigParser

from flask import Blueprint, current_app, request, Response

from yascheduler import CONFIG_FILE
from yascheduler.scheduler import Yascheduler

from utils import SECRET, fmt_msg, is_valid_uuid
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
        current_app.logger.warning("Illegal request from an unauthorized user")
        return fmt_msg('Unauthorized', 401)

    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        current_app.logger.warning("Illegal request from a known user")
        return fmt_msg('Empty or invalid content', 400)

    db = Data_Storage()
    item = db.get_item(uuid)
    if not item:
        return fmt_msg('No such content', 204)

    # TODO
    ase_obj = item.content
    submittable = calcs.preprocess(ase_obj, item.label)

    task_id = yac.queue_submit_task(item.label, submittable)
    new_uuid = db.put_item('$', str(task_id))
    db.close()

    return Response(json.dumps(dict(uuid=new_uuid), indent=4), content_type='application/json', status=200)


@bp_calculations.route("/status", methods=['POST'])
def status():
    """
    Expects
        secret: string
        uuid: uuid
    Returns
        JSON->error::string
        or JSON {progress}
    """
    secret = request.values.get('secret')
    if secret != SECRET:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return fmt_msg('Unauthorized', 401)

    uuid = request.values.get('uuid')
    if not uuid or not is_valid_uuid(uuid):
        current_app.logger.warning("Illegal request from a known user")
        return fmt_msg('Empty or invalid content', 400)

    db = Data_Storage()
    item = db.get_item(uuid)
    if not item:
        return fmt_msg('No such content', 204)

    elif item.label != '$':
        return fmt_msg('Wrong item requested')

    yac_task = yac.queue_get_tasks(int(item.content))
    progress = 0

    if yac_task.status == yac.STATUS_TO_DO:
        progress = 25
    elif yac_task.status == yac.STATUS_RUNNING:
        progress = 50 if random.randint(1, 2) == 1 else 75
    else:
        progress = 100
        db.drop_item(uuid)
    db.close()

    return Response(json.dumps(dict(progress=progress), indent=4), content_type='application/json', status=200)
