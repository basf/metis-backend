#!/usr/bin/env python3

import uuid
import random
import json

from flask import Flask, Blueprint, Response, current_app, request


app_server = Blueprint('app_server', __name__)

LOGIN = 'basf'
PASSWORD = 'fsab'
SESSION_ID = 'XXXXXXXXXXBNGHTKLGHBNHGFHFQAWRRT'
ACCESS_ID = 'XXXXXXXXXXQVBLPOFRFGAHQAWYUYSTTS'


@app_server.after_request
def add_service_headers(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

# *******************************************************************************************************************
# Auth endpoints
# *******************************************************************************************************************

@app_server.route("/users/login", methods=['POST'])
def login():
    """
    Auth endpoint
    Expects
        login
        password
    Returns
        JSON->error::str
        or user's object
        JSON->sid::str, email::str, firstname::str, lastname::str
    """
    login = request.values.get('login')
    password = request.values.get('password')

    if login != LOGIN or password != PASSWORD:
        current_app.logger.warning("Wrong login attempt")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    user_obj = dict(
        sid=SESSION_ID,
        email='albert-mileva-elsa-einstein-junior@basf.science',
        firstname='Albert',
        lastname='Einstein'
    )
    return Response(json.dumps(user_obj, indent=4), content_type='application/json', status=200)


@app_server.route("/users/getlink", methods=['POST'])
def getlink():
    """
    Auth endpoint
    Expects
        login
    Returns
        empty {}
    """
    login = request.values.get('login')

    if login != LOGIN:
        current_app.logger.warning("Wrong login attempt")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    # Emailing a secret access link ACCESS_ID here

    return Response(json.dumps({}, indent=4), content_type='application/json', status=200)


@app_server.route("/users/uselink", methods=['POST'])
def uselink():
    """
    Auth endpoint
    Expects
        aid
    Returns
        JSON->error::str
        or user's object
        JSON->sid::str, email::str, firstname::str, lastname::str
    """
    aid = request.values.get('aid')

    if aid != ACCESS_ID:
        current_app.logger.warning("Wrong login attempt")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    user_obj = dict(
        sid=SESSION_ID,
        email='albert-mileva-elsa-einstein-junior@basf.science',
        firstname='Albert',
        lastname='Einstein'
    )
    return Response(json.dumps(user_obj, indent=4), content_type='application/json', status=200)


@app_server.route("/users/logout", methods=['POST'])
def logout():
    """
    Auth endpoint
    Expects
        sid
    Returns
        empty {}
    """
    sid = request.values.get('sid')
    if sid != SESSION_ID:
        current_app.logger.warning("Illegal request from an unauthorized user")
        #return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    return Response(json.dumps({}, indent=4), content_type='application/json', status=200)

# *******************************************************************************************************************
# Data endpoints
# *******************************************************************************************************************

@app_server.route("/data/create", methods=['POST'])
def create():
    """
    Data endpoint
    Expects
        sid
        content
    Returns
        JSON->error::str
        or confirmation object
        {object->uuid, object->type, object->name}
    """
    sid = request.values.get('sid')
    if sid != SESSION_ID:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    content = request.values.get('content')
    if not content:
        current_app.logger.warning("Illegal request from a known user")
        return Response(json.dumps({'error': 'Empty or invalid content'}, indent=4), content_type='application/json', status=401)

    # Data item recognition and saving logics here

    return Response(json.dumps(dict(
        uuid=str(uuid.uuid4()),
        type=random.randint(1, 2),
        name='SrTiO3'
    ), indent=4), content_type='application/json', status=200)


@app_server.route("/data/share", methods=['POST'])
def share():
    """
    Data endpoint
    Expects
        sid
        uuid
    Returns
        empty {}
    """
    sid = request.values.get('sid')
    if sid != SESSION_ID:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    uuid = request.values.get('uuid')
    if not uuid:
        current_app.logger.warning("Illegal request from a known user")
        return Response(json.dumps({'error': 'Empty or invalid content'}, indent=4), content_type='application/json', status=401)

    # Logics here

    return Response(json.dumps({}, indent=4), content_type='application/json', status=200)


@app_server.route("/data/list", methods=['POST'])
def list():
    """
    Data endpoint
    Expects
        sid
    Returns
        JSON->error::str
        or listing
        [ {object->uuid, object->type, object->name}, ... ]
    """
    sid = request.values.get('sid')
    if sid != SESSION_ID:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    # Data item retrieval logics here

    listing = []
    for _ in range(random.randint(0, 2)):
        listing.append(dict(
            uuid=str(uuid.uuid4()),
            type=random.randint(1, 2),
            name='Ba2Li3Sc6O9'
        ))

    return Response(json.dumps(listing, indent=4), content_type='application/json', status=200)

# *******************************************************************************************************************
# Calculations endpoints
# *******************************************************************************************************************

@app_server.route("/calculations/submit", methods=['POST'])
def submit():
    """
    Calculations endpoint
    Expects
        sid
        uuid
    Returns
        empty {}
    """
    sid = request.values.get('sid')
    if sid != SESSION_ID:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    uuid = request.values.get('uuid')
    if not uuid:
        current_app.logger.warning("Illegal request from a known user")
        return Response(json.dumps({'error': 'Empty or invalid content'}, indent=4), content_type='application/json', status=401)

    # Logics here

    return Response(json.dumps({}, indent=4), content_type='application/json', status=200)


@app_server.route("/calculations/overview", methods=['POST'])
def overview():
    """
    Calculations endpoint
    Expects
        sid
    Returns
        JSON->error::str
        or listing
        [ {object->uuid, object->status, object->name}, ... ]
    """
    sid = request.values.get('sid')
    if sid != SESSION_ID:
        current_app.logger.warning("Illegal request from an unauthorized user")
        return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    # Calculations retrieval logics here

    listing = []
    for _ in range(random.randint(0, 2)):
        listing.append(dict(
            uuid=str(uuid.uuid4()),
            status=random.randint(1, 3),
            name='C2H5OH'
        ))

    return Response(json.dumps(listing, indent=4), content_type='application/json', status=200)


if __name__ == '__main__':

    app = Flask(__name__)
    app.debug = False
    app.register_blueprint(app_server)
    app.run(port=7070)

    # NB dev-only, no production usage