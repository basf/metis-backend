# from pprint import pprint
import base64
import json
from unidecode import unidecode
from io import StringIO

from flask import Blueprint, current_app, request, abort, Response, send_file
from ase import io as ase_io

from metis_backend.helpers import (
    MAX_UPLOAD_SIZE,
    get_data_storage,
    fmt_msg,
    key_auth,
    is_plain_text,
    is_valid_uuid,
    get_name,
)
from metis_backend.datasources import Data_type
from metis_backend.datasources.fmt import detect_format
from metis_backend.datasources.xrpd import extract_pattern, nexus_to_xye
from metis_backend.structures import html_formula
from metis_backend.structures.cif_utils import cif_to_ase
from metis_backend.structures.struct_utils import (
    poscar_to_ase,
    optimade_to_ase,
    refine,
    get_formula,
    ase_serialize,
    ase_unserialize,
)
from metis_backend.calculations.xrpd import get_pattern, topas_serialize, topas_unserialize


bp_data = Blueprint("data", __name__, url_prefix="/data")


@bp_data.route("/create", methods=["POST"])
@key_auth
def create():
    """
    @api {post} /data/create create
    @apiGroup Datasources
    @apiDescription Datasource recognition and saving logics

    @apiParam {String} content Crystal structure or pattern
    @apiParam {String} [fmt] Format (only used xy for patterns)
    @apiParam {String} [name] Title for content (only used for patterns)
    """
    content = request.values.get("content")
    if not content:
        return fmt_msg("Empty request")

    if 'base64,' in content[:128]:
        # handling raw bytes in Flask request string is non-trivial,
        # so we have to encode them in base64 at the client
        try: content = base64.b64decode(content.split('base64,', maxsplit=1)[1])
        except: pass

    if not 0 < len(content) < MAX_UPLOAD_SIZE:
        return fmt_msg("Request size is invalid")

    #if not is_plain_text(content):
    #    return fmt_msg('Request contains unsupported (non-latin) characters')
    #    content = unidecode(content)

    fmt = request.values.get("fmt") or detect_format(content)
    ase_obj, xrd_obj, input_obj = None, None, None
    error = None

    if fmt == "cif":
        ase_obj, error = cif_to_ase(content)

    elif fmt == "poscar":
        ase_obj, error = poscar_to_ase(content)

    elif fmt == "optimade":
        ase_obj, error = optimade_to_ase(content)

    elif fmt == "xy":
        xrd_obj = get_pattern(content)
        if not xrd_obj:
            error = "Not a valid pattern provided"

    elif fmt == "raw":
        xrd_obj = extract_pattern(content)
        if not xrd_obj:
            error = "Not a valid pattern provided"

    elif fmt == "nexus":
        xrd_obj = nexus_to_xye(content)
        if not xrd_obj:
            error = "Not a valid synchrotron format provided"

    elif fmt == "topas":
        input_obj = topas_serialize(content)

    else: return fmt_msg("Provided data format unsuitable or not recognized")

    if error: return fmt_msg(error)

    if ase_obj:
        if "disordered" in ase_obj.info:
            return fmt_msg("Structural disorder is currently not supported")

        ase_obj, error = refine(ase_obj, conventional_cell=True)
        if error:
            return fmt_msg(error)

        formula = get_formula(ase_obj)
        content = ase_serialize(ase_obj)

        db = get_data_storage()
        new_uuid = db.put_item(
            dict(name=html_formula(formula)), content, Data_type.structure
        )
        db.close()

        return Response(
            json.dumps(
                dict(
                    uuid=new_uuid,
                    type=Data_type.structure,
                    name=html_formula(formula),
                ),
                indent=4,
            ),
            content_type="application/json",
            status=200,
        )

    elif xrd_obj:
        name = get_name(request.values.get("name"), "XRD")
        db = get_data_storage()
        new_uuid = db.put_item(dict(name=name, oname=request.values.get("name")),
            xrd_obj["content"], xrd_obj["type"])
        db.close()

        return Response(
            json.dumps(
                dict(
                    uuid=new_uuid,
                    type=xrd_obj["type"],
                    name=name,
                ),
                indent=4,
            ),
            content_type="application/json",
            status=200,
        )

    elif input_obj:
        name = get_name(request.values.get("name"), "CALC")
        db = get_data_storage()
        new_uuid = db.put_item(dict(name=name, oname=request.values.get("name")),
            input_obj, Data_type.user_input)
        db.close()

        return Response(
            json.dumps(
                dict(
                    uuid=new_uuid,
                    type=Data_type.user_input,
                    name=name,
                ),
                indent=4,
            ),
            content_type="application/json",
            status=200,
        )

    else: abort(400)


@bp_data.route("/import", methods=["POST"])
@key_auth
def importing():
    """
    @api {post} /data/import import
    @apiGroup Datasources
    @apiDescription Import datasource from an external provider DB

    @apiParam {String} ext_id External ID
    """
    ext_id = request.values.get("ext_id")
    if not ext_id:
        abort(400)

    db = get_data_storage()
    new_uuid, name = db.import_item(ext_id)
    db.close()

    if not new_uuid:
        abort(404)

    return Response(
        json.dumps(
            dict(
                uuid=new_uuid,
                type=Data_type.structure,
                name=name, # NB already in HTML
            ),
            indent=4,
        ),
        content_type="application/json",
        status=200,
    )


@bp_data.route("/listing", methods=["POST"])
@key_auth
def listing():
    """
    @api {post} /data/listing listing
    @apiGroup Datasources
    @apiDescription Datasource listing

    @apiParam {String/String[]} uuid What to consider
    """
    uuid = request.values.get("uuid")
    # current_app.logger.warning(uuid)
    if not uuid:
        return fmt_msg("Empty request")

    db = get_data_storage()

    if ":" in uuid:
        uuids = uuid.split(":")
        unique_uuids = set(uuids)
        for uuid in unique_uuids:
            if not is_valid_uuid(uuid):
                return fmt_msg("Invalid request")

        items = db.get_items(list(unique_uuids), with_links=True)

        # found_uuids = set( [item['uuid'] for item in items] )
        # if found_uuids != unique_uuids:
        #    return fmt_msg('No such content', 204)

    else:
        uuids = [uuid]
        if not is_valid_uuid(uuid):
            return fmt_msg("Invalid request")

        item = db.get_item(uuid, with_links=True)
        items = [item] if item else []

    if not items:
        return fmt_msg("No such content", 204)

    db.close()

    items_mapping = {
        item["uuid"]: dict(
            uuid=item["uuid"],
            name=item["metadata"]["name"],
            type=item["type"],
            children=item["children"],
            parents=item["parents"],
        )
        for item in items
    }
    # sort according to unique sequence requested
    items = list(
        filter(None, [items_mapping.get(uuid) for uuid in dict.fromkeys(uuids)])
    )

    return Response(
        json.dumps(items, indent=4), content_type="application/json", status=200
    )


@bp_data.route("/delete", methods=["POST"])
@key_auth
def delete():
    """
    @api {post} /data/delete delete
    @apiGroup Datasources
    @apiDescription Datasource removal

    @apiParam {String} uuid What to consider
    """
    uuid = request.values.get("uuid")
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg("Empty or invalid request")

    db = get_data_storage()
    result = db.drop_item(uuid)
    db.close()

    if result:
        return Response("{}", content_type="application/json", status=200)
    return fmt_msg("No such content", 204)


@bp_data.route("/examine", methods=["POST"])
@key_auth
def examine():
    """
    @api {post} /data/examine examine
    @apiGroup Datasources
    @apiDescription Datasource display

    @apiParam {String} uuid What to consider
    """
    uuid = request.values.get("uuid")
    if not uuid or not is_valid_uuid(uuid):
        return fmt_msg("Empty or invalid request", 400)

    db = get_data_storage()
    item = db.get_item(uuid)
    db.close()

    if not item: return fmt_msg("Sorry these data cannot be shown")

    output = {}

    if item["type"] == Data_type.pattern:
        try: content = json.loads(item["content"])
        except Exception: return fmt_msg("Sorry cannot show erroneous format")

        try: ymax = max([row[1] for row in content]) # normalize intensities
        except ValueError: return fmt_msg("Sorry cannot show erroneous data")

        # for GUI Plot
        output["content"] = [[row[0], int(round(row[1] / ymax * 100))] for row in content]

    elif item["type"] == Data_type.property:
        output["engine"] = item["metadata"].get(
            "engine", "default engine"
        )  # FIXME "default engine"

        try: output["content"] = json.loads(item["content"])
        except Exception: return fmt_msg("Sorry erroneous data cannot be shown")

    elif item["type"] == Data_type.user_input:
        output["content"] = topas_unserialize(item["content"])

    elif item["type"] == Data_type.structure:
        ase_obj = ase_unserialize(item["content"])

        if len(ase_obj) < 10:
            orig_cell = ase_obj.cell[:]
            ase_obj *= (2, 2, 2)
            ase_obj.set_cell(orig_cell)
        ase_obj.center(about=0.0)

        with StringIO() as fd:
            ase_io.write(fd, ase_obj, format="vasp")
            output["content"] = fd.getvalue()

    else: return fmt_msg("Sorry this data type cannot be shown")

    return Response(
        json.dumps(output, indent=4), content_type="application/json", status=200
    )
