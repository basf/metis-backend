#!/usr/bin/env python3

from os import environ

from flask import Flask
from netius.servers import WSGIServer
from aiida import load_profile as load_aiida_profile

from i_data.bp_data import bp_data
from i_calculations.bp_calculations import bp_calculations


app = Flask(__name__)
app.debug = True
app.register_blueprint(bp_data)
app.register_blueprint(bp_calculations)

if __name__ == '__main__':

    load_aiida_profile()

    host = environ.get('HOST', '127.0.0.1')
    port = int(environ.get('PORT', '7050'))

    # production server
    server = WSGIServer(app=app)
    server.serve(host=host, port=port)

    # development server
    #app.run(host=host, port=port)
