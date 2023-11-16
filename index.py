#!/usr/bin/env python3

from os import environ
import logging

from flask import Flask
from netius.servers import WSGIServer

from metis_backend.datasources.bp_data import bp_data
from metis_backend.calculations.bp_calculations import bp_calculations


app = Flask(__name__)
app.debug = True
app.register_blueprint(bp_data)
app.register_blueprint(bp_calculations)

if __name__ == '__main__':

    host = environ.get('HOST', 'localhost')
    port = int(environ.get('PORT', '7050'))
    logging.warning(f'Backend listens to {host}:{port}')

    # production server
    server = WSGIServer(app=app)
    server.serve(host=host, port=port) # NB ipv6 is not going to work here

    # development server
    #app.run(host=host, port=port)
