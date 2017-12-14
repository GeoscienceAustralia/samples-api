"""
This file contains all the HTTP routes for classes from the IGSN model, such as Samples and the Sample Register
"""
from flask import Blueprint, render_template, request, Response
from .functions import render_alternates_view, client_error_Response
import _config as conf
from _ldapi.__init__ import LDAPI, LdapiParameterError
from controller import classes_functions
import requests
try:
    import urllib.parse as uparse
except:
    from urlparse import urlparse


classes = Blueprint('classes', __name__)

@classes.context_processor
def organisation_branding():
    return dict(organisation_branding='gsv')


@classes.route('/sample/test')
def test_branding():
    return render_template('testing_branding.html')

@classes.route('/sample/<string:igsn>')
def sample(igsn):
    """
    A single Sample

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    c = conf.URI_SAMPLE_CLASS
    views_formats = LDAPI.get_classes_views_formats().get(c)

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
            return render_alternates_view(
                class_uri,
                uparse.quote_plus(class_uri),
                instance_uri,
                uparse.quote_plus(instance_uri),
                views_formats,
                request.args.get('_format')
            )
        else:
            from model.sample import Sample
            try:
                s = Sample(igsn)
                return s.render(view, mimetype)
            except ValueError:
                return render_template('class_sample_no_record.html', organisation=ORGANISATION)

    except LdapiParameterError as e:
        return client_error_Response(e)


@classes.route('/sample/<string:igsn>/pingback', methods=['GET', 'POST'])
def sample_pingback(igsn):
    if request.method == 'GET':
        return Response(
            'This endpoint is the individual PROV "pingback" endpoint for Sample {}. It is expected to be used in '
            'accordance with the PROV-AQ Working Group Note (https://www.w3.org/TR/prov-aq/).'.format(igsn),
            mimetype='text/plain'
            )

    # TODO: validate the pingback
    valid = True
    if valid:
        return Response(
            'This is a test response, no action has been taken with the pingback information',
            status=204,
            mimetype='text/plain'
        )
    else:
        return Response(
            'The pingback message submitted is not valid',
            status=400,
            mimetype='text/plain'
        )


@classes.route('/sample/')
def samples():
    """
    The Register of Samples

    :return: HTTP Response
    """
    # lists the views and formats available for a Sample
    views_formats = classes_functions.get_classes_views_formats() \
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
            return render_alternates_view(
                class_uri,
                uparse.quote_plus(class_uri),
                None,
                None,
                views_formats,
                request.args.get('_format')
            )
        else:
            from model import register

            # pagination
            page = int(request.args.get('page')) if request.args.get('page') is not None else 1
            per_page = int(request.args.get('per_page')) if request.args.get('per_page') is not None else 100

            if per_page > conf.OAI_BATCH_SIZE:
                return Response(
                    'You must enter either no value for per_page or an integer <= {}.'.format(conf.OAI_BATCH_SIZE),
                    status=400,
                    mimetype='text/plain'
                )

            links = list()
            links.append('<http://www.w3.org/ns/ldp#Resource>; rel="type"')
            # signalling that this is, in fact, a resource described in pages
            links.append('<http://www.w3.org/ns/ldp#Page>; rel="type"')
            links.append('<{}?per_page={}>; rel="first"'.format(conf.URI_SAMPLE_INSTANCE_BASE, per_page))

            # if this isn't the first page, add a link to "prev"
            if page != 1:
                links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                    conf.URI_SAMPLE_INSTANCE_BASE,
                    per_page,
                    (page - 1)
                ))

            # if this isn't the first page, add a link to "prev"
            if page != 1:
                prev_page = page - 1
                links.append('<{}?per_page={}&page={}>; rel="prev"'.format(
                    conf.URI_SAMPLE_INSTANCE_BASE,
                    per_page,
                    prev_page
                ))
            else:
                prev_page = None

            # add a link to "next" and "last"
            try:
                r = requests.get(conf.XML_API_URL_TOTAL_COUNT)
                no_of_samples = int(r.content.decode('utf-8').split('<RECORD_COUNT>')[1].split('</RECORD_COUNT>')[0])
                last_page = int(round(no_of_samples / per_page, 0)) + 1  # same as math.ceil()

                # if we've gotten the last page value successfully, we can choke if someone enters a larger value
                if page > last_page:
                    return Response(
                        'You must enter either no value for page or an integer <= {} which is the last page number.'
                        .format(last_page),
                        status=400,
                        mimetype='text/plain'
                    )

                # add a link to "next"
                if page != last_page:
                    next_page = page + 1
                    links.append('<{}?per_page={}&page={}>; rel="next"'
                                 .format(conf.URI_SAMPLE_INSTANCE_BASE, per_page, (page + 1)))
                else:
                    next_page = None

                # add a link to "last"
                links.append('<{}?per_page={}&page={}>; rel="last"'
                             .format(conf.URI_SAMPLE_INSTANCE_BASE, per_page, last_page))
            except:
                # if there's some error in getting the no of samples, add the "next" link but not the "last" link
                next_page = page + 1
                links.append('<{}?per_page={}&page={}>; rel="next"'
                             .format(conf.URI_SAMPLE_INSTANCE_BASE, per_page, (page + 1)))

            headers = {
                'Link': ', '.join(links)
            }

            class_uri_of_register_items = 'http://pid.geoscience.gov.au/def/ont/igsn#Sample'
            return register.RegisterRenderer(
                request,
                conf.REGISTER_BASE_URI,
                class_uri_of_register_items,
                None,
                page,
                per_page,
                prev_page,
                next_page,
                last_page).render(view, mime_format, extra_headers=headers)

    except LdapiParameterError as e:
        return client_error_Response(e)
