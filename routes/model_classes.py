"""
This file contains all the HTTP routes for classes from the IGSN model, such as Samples and the Sample Register
"""
from flask import Blueprint, render_template, request
import routes_functions
import settings
from ldapi import LDAPI, LdapiParameterError
from routes import model_classes_functions
import urllib
# from oaipmh.datestamp import datestamp_to_datetime, datetime_to_datestamp

model_classes = Blueprint('model_classes', __name__)


@model_classes.route('/sample/<string:igsn>')
def sample(igsn):
    """
    A single Sample

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = model_classes_functions.get_classes_views_formats() \
        .get('http://pid.geoscience.gov.au/def/ont/igsn#Sample')

    try:
        view, mimetype = LDAPI.get_valid_view_and_format(
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
                return s.render(view, mimetype)
            except ValueError:
                return render_template('no_record_sample.html')

    except LdapiParameterError, e:
        return routes_functions.client_error_Response(e)


@model_classes.route('/sample/')
def samples():
    """
    The Register of Samples

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = model_classes_functions.get_classes_views_formats() \
        .get('http://purl.org/linked-data/registry#Register')

    try:
        view, mime_format = LDAPI.get_valid_view_and_format(
            request.args.get('_view'),
            request.args.get('_format'),
            views_formats
        )

        # if alternates model, return this info from file
        class_uri = 'http://pid.geoscience.gov.au/def/ont/igsn#Sample'

        if view == 'alternates':
            del views_formats['renderer']
            return routes_functions.render_alternates_view(
                class_uri,
                urllib.quote_plus(class_uri),
                None,
                None,
                views_formats,
                request.args.get('_format')
            )
        else:
            from model import register
            page_no = int(request.args.get('page_no')) if request.args.get('page_no') is not None else 1
            no_per_page = int(request.args.get('no_per_page')) if request.args.get('no_per_page') is not None else 100
            return register.RegisterRenderer(request, class_uri, None, page_no, no_per_page).render(view, mime_format)

    except LdapiParameterError, e:
        return routes_functions.client_error_Response(e)
