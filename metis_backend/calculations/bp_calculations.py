import logging
import json
import os.path

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import numpy as np

from flask import Blueprint, current_app, request, abort, Response
import requests
from yascheduler import Yascheduler

from metis_backend.helpers import (
    WEBHOOK_KEY, WEBHOOK_CALC_UPDATE, WEBHOOK_CALC_CREATE, TMP_PHASEID_DIR, TMP_PHASEID_URL,
    get_data_storage,
    fmt_msg,
    key_auth,
    webhook_auth,
    is_valid_uuid,
    get_rnd_string,
)
from metis_backend.calculations import Calc_setup, _scheduler_status_mapping
from metis_backend.calculations.xrpd import topas_serialize, topas_unserialize
from metis_backend.datasources import Data_type
from metis_backend.structures import html_formula
from metis_backend.structures.struct_utils import ase_unserialize
from metis_backend.phaseid import (
    WAVELENGTH, MIN_Q, MAX_Q, N_BINS, N_BEST_MATCHES,
    background,
    get_best_match,
    create_reference_array,
    get_q_twotheta_wv,
    integrate_patt_q,
    get_q_dspace,
    cleanup_convert_dis,
    groups_abbreviations,
    chemical_symbols_and_groups,
)


bp_calculations = Blueprint("calculations", __name__, url_prefix="/calculations")

yac = Yascheduler()

setup = Calc_setup()


@bp_calculations.route("/create", methods=["POST"])
@key_auth
def create():
    """
    @api {post} /calculations/create create
    @apiGroup Calculations
    @apiDescription Calculation start

    @apiParam {String} uuid Datasource
    @apiParam {String} engine Use engine from those supported by scheduler
    @apiParam {Object} [input] Params as per scheduler engines supported: {inputname: inputdata, ...}
    @apiParam {Boolean/String} [workflow] AiiDA integration
    """
    uuid = request.values.get("uuid")
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg("Empty or invalid request", 400)

    engine = request.values.get("engine")
    if not engine or engine not in yac.config.engines:
        return fmt_msg("Wrong engine requested", 400)

    workflow = request.values.get("workflow") == "workflow"
    current_app.logger.warning(
        f'Requested {"workflow" if workflow else "calculation"} of {uuid} with {engine}'
    )
    if workflow: abort(501)

    db = get_data_storage()
    node = db.get_item(uuid)
    if not node:
        return fmt_msg("No such content", 400)

    if node["type"] == Data_type.structure:

        ase_obj = ase_unserialize(node["content"])
        input_data, error = setup.preprocess(ase_obj, engine, node["metadata"]["name"])
        if error:
            return fmt_msg(error, 503)

    elif node["type"] == Data_type.user_input:

        input_str = topas_unserialize(node["content"])
        input_data, error = setup.preprocess(input_str, engine, node["metadata"]["name"], db=db)
        if error:
            return fmt_msg(error, 503)

    else: return fmt_msg("The item of this type cannot be used for calculation", 400)

    # inject user-defined input to override calculation
    user_input_files = request.values.get("input")
    if user_input_files:
        # TODO only the first (main) input is currently overridden
        input_data[yac.config.engines[engine].input_files[0]] = user_input_files
        current_app.logger.warning("Custom input requested:")
        current_app.logger.warning(input_data)

        # try: user_input_files = json.loads(user_input_files)
        # except IndexError:
        #    return fmt_msg('Invalid input definition', 400)
        #
        # if type(user_input_files) != dict:
        #    return fmt_msg('Invalid input definition', 400)
        #
        # for key, value in user_input_files.items():
        #    if key not in input_data:
        #        return fmt_msg('Invalid input %s' % key, 400)
        #
        #    input_data[key] = value

    for chk in yac.config.engines[engine].input_files:
        if chk not in input_data:
            return fmt_msg("Invalid input files", 400)

    # TODO define in config
    input_data["webhook_url"] = (
        "http://" + request.host + "/calculations/update?Key=" + WEBHOOK_KEY
    )
    # input_data['webhook_custom_params'] = {'blabla': 'blabla'}
    # input_data['webhook_onsubmit'] = True

    task_id = yac.queue_submit_task(node["metadata"]["name"], input_data, engine)
    new_uuid = db.put_item(
        dict(
            name=node["metadata"]["name"], engine=engine, parent=uuid
        ),  # FIXME migrate parent
        task_id,
        Data_type.calculation,
    )
    current_app.logger.warning(f"Submitted {engine} calculation {task_id}")

    db.close()
    return Response(
        json.dumps(dict(uuid=new_uuid), indent=4),
        content_type="application/json",
        status=200,
    )


@bp_calculations.route("/status", methods=["POST"])
@key_auth
def status():
    """
    @api {post} /calculations/status status
    @apiGroup Calculations
    @apiDescription Calculation status

    @apiParam {String/String[]} uuid Datasource(s)
    """
    uuid = request.values.get("uuid")
    if not uuid:
        return fmt_msg("Empty request", 400)

    db = get_data_storage()

    if ":" in uuid:
        uuids = uuid.split(":")
        unique_uuids = set(uuids)
        for item in unique_uuids:
            if not is_valid_uuid(item):
                return fmt_msg("Invalid content", 400)

        calcs = db.get_items(list(unique_uuids))

        # found_uuids = set( [item['uuid'] for item in calcs] )
        # if found_uuids != unique_uuids:
        #    return fmt_msg('Internal error, consistency broken', 500)

    else:
        uuids = [uuid]
        if not is_valid_uuid(uuid):
            return fmt_msg("Invalid content", 400)

        item = db.get_item(uuid)
        calcs = [item] if item else []

    if not calcs: return fmt_msg("No such content", 204)

    results_mapping = {}
    yac_items = []

    # separating individual yascheduler calcs vs. AiiDA workflows
    for calc in calcs:
        if calc["type"] == Data_type.calculation:
            calc["content"] = int(calc["content"])
            yac_items.append(calc)

        elif calc["type"] == Data_type.workflow:
            # TODO load many nodes at once
            wf_progress = Workflow_setup.check_process(
                calc["content"], current_app.logger
            )
            if not wf_progress:
                return fmt_msg("Wrong workflow requested", 400)

            results_mapping[calc["uuid"]] = dict(
                uuid=calc["uuid"],
                type=Data_type.workflow,
                name=html_formula(calc["metadata"]["name"]),
                progress=wf_progress,
            )
            # TODO remove ready workflow

        else: return fmt_msg("Wrong item requested", 400)

    yac_tasks = []
    if yac_items:
        yac_tasks = yac.queue_get_tasks(jobs=[item["content"] for item in yac_items])

        if not yac_tasks or len(yac_tasks) != len(yac_items):
            return fmt_msg(
                "Scheduler and backend are out of sync, task(s) not scheduled", 500
            )

    for task in yac_tasks:
        found = [item for item in yac_items if item["content"] == task["task_id"]]
        if not found or len(found) > 1:
            return fmt_msg("Internal error, task(s) lost", 500)

        calc_uuid =   found[0]["uuid"]
        calc_name =   found[0]["metadata"]["name"]
        calc_parent = found[0]["metadata"]["parent"]

        if task["status"] == Yascheduler.STATUS_TO_DO:
            progress = _scheduler_status_mapping[task["status"]]

        elif task["status"] == Yascheduler.STATUS_RUNNING:
            progress = _scheduler_status_mapping[task["status"]]

        else:
            if not db.get_sources(calc_parent):
                # Should we handle results here? TODO?
                current_app.logger.critical("Listing precedes hook")

            progress = _scheduler_status_mapping[Yascheduler.STATUS_DONE]

        results_mapping[calc_uuid] = dict(
            uuid=calc_uuid,
            type=Data_type.calculation,
            name=html_formula(calc_name),
            parent=calc_parent,
            progress=progress,
        )

    db.close()

    results = []
    if results_mapping:
        # sort according to unique sequence requested
        results = list(
            filter(None, [results_mapping.get(uuid) for uuid in dict.fromkeys(uuids)])
        )

    return Response(
        json.dumps(results, indent=4),
        content_type="application/json",
        status=200
    )


def process_calc(db, calc_row, scheduler_id):
    ready_task = yac.queue_get_task(scheduler_id) or {}
    local_folder = ready_task.get("metadata", {}).get("local_folder")

    if local_folder and os.path.exists(local_folder):
        output, error = setup.postprocess(calc_row["metadata"]["engine"], local_folder)
    else:
        output, error = None, "No calculation results exist"

    if error: return None, error

    output["metadata"]["engine"] = calc_row["metadata"]["engine"]
    output["metadata"]["name"] = calc_row["metadata"]["name"] # + " result"

    new_uuid = db.put_item(output["metadata"], output["content"], output["type"])
    result = {"uuid": new_uuid, "parent": calc_row["metadata"]["parent"]}

    try:
        db.put_link(calc_row["metadata"]["parent"], new_uuid)
    except Exception:
        return (
            None,
            "Graph edge consistency error (no source %s ?)"
            % calc_row["metadata"]["parent"],
        )

    db.drop_item(calc_row["uuid"])

    return result, None


@bp_calculations.route("/update", methods=["POST"])
@webhook_auth
def update():
    """
    @api {post} /calculations/update update
    @apiGroup Calculations
    @apiDescription A scheduler webhooks handler, being a proxy to BFF
    Currently this is the only way to transition calcs in BFF (TODO?)

    @apiParam {Number} task_id Scheduler ID
    @apiParam {Number} status Scheduler state
    @apiParam {Object} [custom_params] Currently, calculation provenance details
    """
    try:
        task_id = int(request.values.get("task_id"))
        status = int(request.values.get("status"))
    except Exception:
        abort(400)

    current_app.logger.warning(f"Got webhook of task {task_id} with status {status}")

    if status == Yascheduler.STATUS_TO_DO:
        # only AiiDA workflows, since regular calculations do NOT fire this
        try:
            custom_params = json.loads(request.values.get("custom_params", "{}"))
        except Exception:
            current_app.logger.error("Got bad JSON")
            abort(500)
        if custom_params.get("parent") and is_valid_uuid(custom_params["parent"]):
            search_by_content = custom_params["parent"]
        else:
            current_app.logger.error("Got unexpected workflow sequence data")
            abort(403)

    else: search_by_content = task_id

    current_app.logger.warning(f"Processing calc by ref {search_by_content}")

    db = get_data_storage()
    item = db.search_item(search_by_content)
    if item:
        if status == Yascheduler.STATUS_TO_DO:
            assert item["type"] == Data_type.workflow
            assert item["metadata"]["parent"]

            new_uuid = db.put_item(item["metadata"], task_id, Data_type.calculation)

            try:
                requests.post(
                    WEBHOOK_CALC_CREATE,
                    json={"uuid": new_uuid, "parent": item["metadata"]["parent"]},
                    timeout=0.5,
                )
            except Exception:
                pass

        elif status == Yascheduler.STATUS_RUNNING:
            assert item["type"] == Data_type.calculation, (
                "Unexpected data type %s" % item["type"]
            )
            progress = _scheduler_status_mapping[status]

            try:
                requests.post(
                    WEBHOOK_CALC_UPDATE,
                    json={"uuid": item["uuid"], "progress": progress},
                    timeout=0.5,
                )
            except Exception:
                pass

        elif status == Yascheduler.STATUS_DONE:
            assert item["type"] == Data_type.calculation, (
                "Unexpected data type %s" % item["type"]
            )
            result = None

            error = None
            if not db.get_sources(item["metadata"]["parent"]):
                result, error = process_calc(db, item, task_id)

            if error:
                current_app.logger.error(error)
            else:
                current_app.logger.warning(
                    "Successfully processed calc %s and linked %s to %s"
                    % (task_id, result["parent"], result["uuid"])
                )

            progress = _scheduler_status_mapping[status]

            if result:
                result = [result]
            try:
                requests.post(
                    WEBHOOK_CALC_UPDATE,
                    json={"uuid": item["uuid"], "progress": progress, "result": result, "error": error},
                    timeout=0.5,
                )
            except Exception:
                if result:
                    current_app.logger.critical(
                        "Internal error, calc %s not delivered to GUI" % task_id
                    )

        else: abort(403)

    else: current_app.logger.error("No calc for task %s" % task_id)

    db.close()
    return Response("", status=204)


@bp_calculations.route("/delete", methods=["POST"])
@key_auth
def delete():
    """
    @api {post} /calculations/delete delete
    @apiGroup Calculations
    @apiDescription Calculation removal

    @apiParam {String} uuid Datasource
    """
    # raise NotImplementedError
    return Response(
        "{}",
        content_type="application/json",
        status=200
    )


@bp_calculations.route("/template", methods=["POST"])
@key_auth
def template():
    """
    @api {post} /calculations/template template
    @apiGroup Calculations
    @apiDescription Get calculation defaults to be overridden in a submission

    @apiParam {String} uuid Datasource
    @apiParam {String} engine Use engine from those supported by scheduler
    """
    uuid = request.values.get("uuid")
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg("Empty or invalid request", 400)

    engine = request.values.get("engine")
    if not engine:
        engine = "dummy"

    db = get_data_storage()
    node = db.get_item(uuid)
    db.close()
    if not node:
        return fmt_msg("No such content", 400)

    if node["type"] == Data_type.structure:

        ase_obj = ase_unserialize(node["content"])
        input_data, error = setup.preprocess(ase_obj, engine, node["metadata"]["name"], merged=True)
        if error:
            return fmt_msg(error, 503)

    elif node["type"] == Data_type.user_input:

        input_str = topas_unserialize(node["content"])
        input_data, error = setup.preprocess(input_str, "topas", node["metadata"]["name"], merged=True)
        if error:
            return fmt_msg(error, 503)

    else: return fmt_msg("The item of this type cannot be used for calculation", 400)

    output = {
        "template": input_data.get("merged", setup.get_input(engine)),
        "schema": setup.get_schema(engine),
    }
    return Response(
        json.dumps(output, indent=4),
        content_type="application/json",
        status=200
    )


@bp_calculations.route("/supported", methods=["GET"])
def supported():
    """
    @api {get} /calculations/supported supported
    @apiGroup Calculations
    @apiDescription Get list of the supported scheduler engines, e.g.
        ["dummy", "dummy+workflow", "pcrystal", "pcrystal+workflow", "gulp", "topas"]
    """
    return Response(
        json.dumps(list(yac.config.engines.keys())),
        content_type="application/json",
        status=200,
    )


@bp_calculations.route("/phaseid", methods=["POST"])
@key_auth
def phaseid():
    """
    @api {post} /calculations/phaseid phaseid
    @apiGroup Calculations
    @apiDescription Run phase ID
    """
    if not os.path.exists(TMP_PHASEID_DIR):
        logging.critical(f"Phase ID requires a folder {TMP_PHASEID_DIR} to exist")
        return fmt_msg(f"Phase ID requires a folder {TMP_PHASEID_DIR} to exist", 503)

    uuid = request.values.get("uuid")
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg("Empty or invalid request")

    els = request.values.get("els")
    if not els:
        return fmt_msg("Empty element or group provided")

    els = list(set(els.split('-')))

    for n in range(len(els)):
        els[n] = groups_abbreviations.get(els[n], els[n])
        if els[n] not in chemical_symbols_and_groups:
            return fmt_msg("Unknown element or group provided")

    try: strict = bool(int(request.values.get('strict', 0)))
    except: return fmt_msg("Unknown strict flag provided")

    db = get_data_storage()
    node = db.get_item(uuid)
    if not node or node["type"] != Data_type.pattern:
        db.close()
        return fmt_msg("Unsuitable content requested")

    try: pattern = np.array(json.loads(node["content"]))
    except Exception: return fmt_msg("Sorry erroneous data cannot be shown")

    patterns_db, patterns_ids, names = db.get_refdis(els, strict)
    db.close()
    logging.warning(f"Using {len(patterns_db)} reference patterns")

    if not len(patterns_db):
        return fmt_msg("Cannot match this pattern against the elements given", 200)

    # BOF phase ID algo
    _, ref_patterns_db = create_reference_array(patterns_db, MIN_Q, MAX_Q, N_BINS)

    intensities = pattern[:, 1]
    twoteta = pattern[:, 0]

    intensities_bg = background(
        intensities,
        twoteta,
        iterations=20,
        sec_iterations=20,
        curvature=0.0001,
        perc_anchor_pnts=20,
    )
    intens_minus_bg = intensities - intensities_bg
    qhisto_diffpatt = integrate_patt_q(
        get_q_twotheta_wv(twoteta, WAVELENGTH), # convert two theta to Q-space
        intens_minus_bg,
        MIN_Q,
        MAX_Q,
        N_BINS,
        normalize=True,
    )

    best_match_idx, _, __ = get_best_match(
        ref_patterns_db, qhisto_diffpatt, N_BEST_MATCHES
    )
    logging.warning('Results: %s' % [(patterns_ids[item], names[item]) for item in best_match_idx])
    # EOF phase ID algo

    results = []
    tmp_fnames = []
    max_intens = np.max(intensities)

    for n in range(min(N_BEST_MATCHES, len(best_match_idx))):
        plt.figure(n + 1)

        best_patt = patterns_db[best_match_idx[n], :, :]
        best_patt_conv = cleanup_convert_dis(best_patt)

        plt.xlim([0, MAX_Q])
        plt.bar(
            qhisto_diffpatt[0],
            qhisto_diffpatt[1] * max_intens,
            width=(MAX_Q - MIN_Q) / N_BINS,
            color="red",
        )
        plt.plot(
            get_q_twotheta_wv(twoteta, WAVELENGTH),
            intensities_bg,
            color="black",
        )
        plt.plot(
            get_q_twotheta_wv(twoteta, WAVELENGTH),
            intens_minus_bg,
            color="black",
        )
        plt.stem(
            get_q_dspace(best_patt_conv[0]),
            (best_patt_conv[1] * max_intens),
            linefmt="blue",
            basefmt="blue",
        )
        #plt.title(names[best_match_idx[n]])

        img_name = get_rnd_string()

        plt.savefig(
            os.path.join(TMP_PHASEID_DIR, f'{img_name}.webp'),
            format="webp",
            transparent=True,
            pil_kwargs={"quality": 35}
        )

        results.append(dict(
            src=TMP_PHASEID_URL + f'{img_name}.webp',
            entry=patterns_ids[best_match_idx[n]],
            name=names[best_match_idx[n]],
        ))

    return Response(
        json.dumps(results, indent=4),
        content_type="application/json",
        status=200
    )
