"""
This file contains all the HTTP routes for classes from the IGSN model, such as Samples and the Sample Register
"""
import datetime

from flask import Blueprint, Response, render_template, request, make_response

import routes_functions
import functions_oai
import settings
from ldapi import LDAPI, LdapiParameterError

# from oaipmh.datestamp import datestamp_to_datetime, datetime_to_datestamp

model_classes = Blueprint('model_classes', __name__)


@model_classes.route('/sample/<string:igsn>')
def sample(igsn):
    """
    A single Sample

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = {
        'default': 'igsn',
        'alternates': ['text/html'],
        'igsn': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'dc': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
        'prov': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json']
    }

    try:
        view, format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )
    except LdapiParameterError, e:
        return routes_functions.client_error_Response(e)

    # select view and format
    if view == 'alternates':
        return routes_functions.render_templates_alternates('page_sample.html', views_formats)
    elif view in ['igsn', 'dc', 'prov']:
        # for all these views we will need to populate a renderers
        from renderers.sample import Sample
        s = Sample()
        #s.populate_from_xml_file('test/sample_eg2.xml')
        s.populate_from_oracle_api(igsn)

        if format in ['text/turtle', 'application/rdf+xml', 'application/rdf+json']:
            return Response(
                s.export_as_rdf(
                    model_view=view,
                    rdf_mime=format),
                status=200,
                mimetype=format,
                headers={'Content-Disposition': 'attachment; filename=' + igsn + LDAPI.get_file_extension(format)}
            )
        elif format == 'application/xml':
            # TODO: implement IGSN XML format
            pass
        else:  # format == 'text/html'
            if s.date_aquired is not None:
                year_acquired = datetime.datetime.strftime(s.date_aquired, '%Y')
            else:
                year_acquired = '2016'
            return render_template(
                'page_sample.html',
                base_uri=settings.BASE_URI,
                web_subfolder=settings.WEB_SUBFOLDER,
                view=view,
                placed_html=s.export_as_html(model_view=view),
                igsn=s.igsn,
                year_acquired=year_acquired,
                date_now=datetime.datetime.now().strftime('%d %B %Y')
            )


@model_classes.route('/sample/')
def samples():
    """
    Samples register

    :return: HTTP Response
    """

    views_formats = {
        'default': 'dpr',
        'alternates': ['text/html'],
        'dpr': ['text/html', 'text/turtle', 'application/rdf+xml', 'application/rdf+json'],
    }

    try:
        view, format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )
    except LdapiParameterError, e:
        return routes_functions.client_error_Response(e)

    # validate page_no parameter
    if routes_functions.an_int(request.args.get('page_no')):
        page_no = int(request.args.get('page_no'))
    else:
        page_no = 1

    # select view and format
    if view == 'alternates':
        return routes_functions.render_templates_alternates('page_samples.html', views_formats)
    elif view in ['dpr']:
        # only create and populate a SamplesRegister for views that need it
        from renderers.samples_register import SampleRegister
        sr = SampleRegister()
        sr.populate_from_oracle_api(page_no)

        if format == 'text/html':
            return render_template(
                'page_samples.html',
                base_uri=settings.BASE_URI,
                web_subfolder=settings.WEB_SUBFOLDER,
                placed_html=sr.export_as_html(model_view='dpr')
            )
        elif format in views_formats['dpr']:
            return Response(
                sr.export_as_rdf(
                    model_view=view,
                    rdf_mime=format),
                status=200,
                mimetype=format,
                headers={
                    'Content-Disposition': 'attachment; filename=samples_register' + LDAPI.get_file_extension(format)
                }
            )
        # no need for an else since views already validated


@model_classes.route('/oai')
def oai():
    # TODO: validate args using functions_oai
    if request.args.get('verb'):
        verb = request.args.get('verb')
    else:
        values = {
            'response_date': datetime.datetime.now().isoformat(),
            'request_uri': 'http://54.66.133.7/igsn-ld-api/oai',
            'error_code': 'badVerb',
            'error_text': 'Illegal OAI verb'
        }
        template = render_template('oai_error.xml', values=values), 400
        response = make_response(template)
        response.headers['Content-Type'] = 'application/xml'

        return response

    try:
        functions_oai.validate_oai_parameters(request.args)
    except ValueError:
        values = {
            'response_date': datetime.datetime.now().isoformat(),
            'request_uri': 'http://54.66.133.7/igsn-ld-api/oai',
            'error_code': 'badArgument',
            'error_text': 'The request includes illegal arguments, is missing required arguments,\
                           includes a repeated argument, or values for arguments have an illegal syntax.'
        }
        template = render_template('oai_error.xml', values=values), 400
        response = make_response(template)
        response.headers['Content-Type'] = 'application/xml'

        return response

    # encode datetimes as datestamps??
    # https://github.com/infrae/pyoai/blob/beced901ea0b494f23053cbb3c6495872acb96a3/src/oaipmh/client.py#L61

    # now call underlying implementation

    # TODO: implement using XML template
    if verb == 'GetRecord':
        # render_template
        pass
    elif verb == 'Identify':
        pass
