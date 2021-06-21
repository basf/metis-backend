#!/usr/bin/env python3

import json
from flask import Flask, Blueprint, Response, current_app, request


app_server = Blueprint('app_server', __name__)

LOGIN = 'basf'
PASSWORD = 'fsab'
SESSION_ID = 'XXXXXXXXXXBNGHTKLGHBNHGFHFQAWRRT'


@app_server.after_request
def add_cors_header(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


@app_server.route("/users/login", methods=['POST'])
def login():
    """
    Auth endpoint
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


@app_server.route("/users/logout", methods=['POST'])
def logout():
    """
    Auth endpoint
    Returns empty {}
    """
    sid = request.values.get('sid')
    if sid != SESSION_ID:
        current_app.logger.warning("Illegal logout from an unauthorized user")
        #return Response(json.dumps({'error': 'Unauthorized'}, indent=4), content_type='application/json', status=401)

    return Response(json.dumps({}, indent=4), content_type='application/json', status=200)


if __name__ == '__main__':

    app = Flask(__name__)
    app.debug = False
    app.register_blueprint(app_server)
    app.run(port=7070)

    # NB dev-only, no production usage