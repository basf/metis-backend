"""
This server is dev-only,
by no means to use in production!
"""

from flask import Flask, Blueprint, Response, request, abort, send_file
from netius.servers import WSGIServer


app_tmp_phaseid = Blueprint('app_tmp_phaseid', __name__)

@app_tmp_phaseid.route("/", methods=["GET"])
def index():

    pattern_id = request.values.get('id')
    if not pattern_id: abort(400)

    # FIXME sanitize!

    import os.path

    if os.path.exists(f'/tmp/{pattern_id}'):
        return send_file(f'/tmp/{pattern_id}', mimetype='image/webp')

    else:
        abort(404)


app = Flask(__name__)
app.register_blueprint(app_tmp_phaseid)
app.debug = True

server = WSGIServer(app=app)
server.serve(host='0.0.0.0', port=64638)
