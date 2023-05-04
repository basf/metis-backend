# from pprint import pprint
import json
from unidecode import unidecode
from io import StringIO

from flask import Blueprint, current_app, request, abort, Response
from ase import io as ase_io

from i_data import Data_type
from i_structures import html_formula
from i_structures.struct_utils import (
    detect_format,
    poscar_to_ase,
    optimade_to_ase,
    refine,
    get_formula,
    ase_serialize,
    ase_unserialize,
)
from i_structures.cif_utils import cif_to_ase
from i_calculations.xrpd import get_pattern, get_pattern_name

from utils import get_data_storage, fmt_msg, key_auth, is_plain_text, is_valid_uuid


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

    if not 0 < len(content) < 300000:
        return fmt_msg("Request size is invalid")

    if not is_plain_text(content):
        # return fmt_msg('Request contains unsupported (non-latin) characters')
        content = unidecode(content)

    fmt = request.values.get("fmt") or detect_format(content)
    ase_obj, raw_obj, error = None, None, None

    if fmt == "cif":
        ase_obj, error = cif_to_ase(content)

    elif fmt == "poscar":
        ase_obj, error = poscar_to_ase(content)

    elif fmt == "optimade":
        ase_obj, error = optimade_to_ase(content)

    elif fmt == "xy":
        raw_obj = get_pattern(content)

        if not raw_obj:
            error = "Not a valid pattern provided"

    else:
        return fmt_msg("Provided data format unsuitable or not recognized")

    if error:
        return fmt_msg(error)

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

    elif raw_obj:
        name = request.values.get("name") or get_pattern_name()
        maxnamelen = 24
        if len(name) > maxnamelen:
            name = name[:maxnamelen]

        db = get_data_storage()
        new_uuid = db.put_item(dict(name=name), raw_obj["content"], raw_obj["type"])
        db.close()

        return Response(
            json.dumps(
                dict(
                    uuid=new_uuid,
                    type=raw_obj["type"],
                    name=name,
                ),
                indent=4,
            ),
            content_type="application/json",
            status=200,
        )

    else:
        abort(400)


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

    if not item:
        return fmt_msg("Sorry these data cannot be shown")

    output = {}

    if item["type"] in (Data_type.property, Data_type.pattern):
        output["engine"] = item["metadata"].get(
            "engine", "default engine"
        )  # FIXME "default engine"

        try:
            output["content"] = json.loads(item["content"])
        except Exception:
            return fmt_msg("Sorry these data are erroneous and cannot be shown")

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

    else:
        return fmt_msg("Sorry this data type cannot be shown")

    return Response(
        json.dumps(output, indent=4), content_type="application/json", status=200
    )
