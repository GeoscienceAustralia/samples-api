"""
This file contains all the HTTP routes for classes from the IGSN model, such as Samples and the Sample Register
"""
import datetime
from flask import Blueprint, Response, render_template, request, make_response
import routes_functions
import settings
from ldapi import LDAPI, LdapiParameterError
from model.datestamp import datetime_to_datestamp
from routes import model_classes_functions
import urllib

# from oaipmh.datestamp import datestamp_to_datetime, datetime_to_datestamp

model_classes = Blueprint('model_classes', __name__)


# TODO: compare this with the instance endpoint in PROMS
@model_classes.route('/sample/<string:igsn>')
def sample(igsn):
    """
    A single Sample

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = model_classes_functions.get_classes_views_formats()\
        .get('http://pid.geoscience.gov.au/def/ont/igsn#Sample')

    try:
        view, format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )

        # if alternates model, return this info from file
        if view == 'alternates':
            class_uri = 'http://pid.geoscience.gov.au/def/ont/igsn#Sample'
            instance_uri = 'http://pid.geoscience.gov.au/sample/' + igsn
            del views_formats['renderer']
            return routes_functions.render_alternates_view(
                class_uri,
                urllib.quote_plus(class_uri),
                instance_uri,
                urllib.quote_plus(instance_uri),
                views_formats,
                request.args.get('_format')
            )
        else:
            from model.sample import Sample
            try:
                s = Sample(settings.XML_API_URL_SAMPLE, igsn)
                return s.render(request.args.get('_view'), request.args.get('_format'))
            except ValueError:
                return render_template('no_record_sample.html')

    except LdapiParameterError, e:
        return routes_functions.client_error_Response(e)


# TODO: compare this with the register endpoint in PROMS
@model_classes.route('/sample/')
def samples():
    """
    Samples register

    :return: HTTP Response
    """
    views_formats = model_classes_functions.get_classes_views_formats()\
        .get('http://pid.geoscience.gov.au/def/ont/igsn#SampleRegister')

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
        from model.SamplesRegister import SampleRegister


        dt = datetime.datetime.now()
        date_stamp = datetime_to_datestamp(dt)

        try:
            sr = SampleRegister(settings.XML_API_URL, page_no)
        except ValueError:
            values = {
                'response_date': date_stamp,
                'request_uri': request.base_url,
                'error_code': 'badArgument',
                'error_text': 'The request includes illegal arguments, is missing required arguments,\
                               includes a repeated argument, or values for arguments have an illegal syntax.'
            }
            template = render_template('oai_error.xml', values=values), 400
            response = make_response(template)
            response.headers['Content-Type'] = 'application/xml'

            return response
        if format == 'text/html':
            return render_template(
                'page_samples.html',
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


