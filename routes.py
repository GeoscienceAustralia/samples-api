import os.path
from flask import Blueprint, Response, render_template
import settings
import functions
routes = Blueprint('routes', __name__)


@routes.route('/')
def index():
    return render_template(
        'index.html'
    )


@routes.route('/test')
def test():
    return Response('test page', status=200, mimetype='text/plain')
