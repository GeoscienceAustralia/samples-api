import os.path
from flask import Blueprint, Response, render_template, request
import settings
import functions
routes = Blueprint('routes', __name__)


@routes.route('/')
def index():
    return render_template(
        'index.html'
    )


@routes.route('/sample')
def sample():
    """
    A single Sample

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    VIEWS_FORMATS = {
        'default': 'igsn',
        'alternates': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'igsn': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'dc': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json']
    }

    # TODO: generalise this and move it to functions.py
    # validate view
    if request.args.get('_view') is not None:
        if request.args.get('_view') not in VIEWS_FORMATS.iterkeys():
            return Response(
                'You have selected a view that does not exist for Samples. Please choose one of ' +
                ', '.join(VIEWS_FORMATS.iterkeys()) + '.',
                status=400,
                mimetype='text/plain')
        else:
            view = request.args.get('_view')
    else:
        view = 'default'

    # replace 'default' with nominated default view

    if view == 'default':
        view = VIEWS_FORMATS['default']

    # validate format
    if request.args.get('_format') is not None:
        if request.args.get('_format') not in VIEWS_FORMATS[view]:
            return Response(
                'You have selected a format that does not exist for the view of Samples you selected. ' +
                'Please choose one of ' + ', '.join(VIEWS_FORMATS[view]) + '.',
                status=400,
                mimetype='text/plain')
        else:
            format = request.args.get('_format')
    else:
        format = 'text/html'

    # select view and format
    if view == 'alternates':
        return render_template(
            'sample.html',
            view=view,
            alternates_html=render_template('view_alternates.html', views_formats=VIEWS_FORMATS)
        )
    elif view == 'igsn':
        pass
    elif view == 'dc':
        pass



@routes.route('/sample/')
def samples():
    return render_template(
        'samples.html'
    )


@routes.route('/test')
def test():
    return Response('test page', status=200, mimetype='text/plain')

