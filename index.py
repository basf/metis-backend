#!/usr/bin/env python3

from flask import Flask
from netius.servers import WSGIServer
from aiida import load_profile as load_aiida_profile

from bp_data import bp_data
from bp_calculations import bp_calculations


app = Flask(__name__)
app.debug = True
app.register_blueprint(bp_data)
app.register_blueprint(bp_calculations)

if __name__ == '__main__':

    load_aiida_profile()

    # production server
    server = WSGIServer(app=app)
    server.serve(host='0.0.0.0', port=7070)

    # development server
    #app.run(host='127.0.0.1', port=7070)
