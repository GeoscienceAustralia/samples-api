import datetime
from flask import Blueprint, render_template, request, make_response, Response
import oai_functions
from model.datestamp import datetime_to_datestamp
import settings
oai_ = Blueprint('oai', __name__)


@oai_.route('/oai', methods=['GET', 'POST'])
def oai():
    # cater for either a GET or a POST
    request_args = {}
    verb = request.values.get('verb')
    if request.method == 'GET':
        for k, v in request.values.iteritems():
            request_args[k] = v
    elif request.method == 'POST':
        for k, v in request.form.iteritems():
            request_args[k] = v

    # TODO: validate args using functions_oai
    dt = datetime.datetime.now()
    date_stamp = datetime_to_datestamp(dt)
    base_url = request.base_url

    if verb is None:
        values = {
            'response_date': date_stamp,
            'request_uri': base_url,
            'error_code': 'badVerb',
            'error_text': 'Illegal OAI verb'
        }
        template = render_template('oai_error.xml', values=values), 400
        response = make_response(template)
        response.headers['Content-Type'] = 'application/xml'

        return response

    try:
        oai_functions.validate_oai_parameters(request_args)
    except ValueError:
        values = {
            'response_date': date_stamp,
            'request_uri': base_url,
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
    if verb == 'GetRecord':
        # render_template
        try:
            request_args['base_uri_oai'] = settings.BASE_URI_OAI
            request_args['date_stamp'] = date_stamp
            sample = oai_functions.get_record(request_args['identifier'])
            template = render_template('oai_get_record.xml',
                                       sample=sample,
                                       request_args=request_args)
            response = make_response(template)
            response.mimetype = 'text/xml'
            return response

        except ValueError:
            values = {
                'response_date': date_stamp,
                'request_uri': base_url,
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
                }
            template = render_template('oai_error.xml', values=values), 400
            response = make_response(template)
            response.mimetype = 'text/xml'
            return response

    elif verb == 'Identify':
        values = {
            'response_date': date_stamp,
            'admin_email': settings.ADMIN_EMAIL,
            'base_url': settings.BASE_URI_OAI,
            'earliest_date': oai_functions.get_earliest_datestamp()
            }
        template = render_template('oai_identify.xml', values=values)
        response = make_response(template)
        response.mimetype = 'text/xml'
        return response

    elif verb == 'ListIdentifiers':
        # render_template
        try:
            samples, resumption_token = oai_functions.list_records(
                request_args.get('metadataPrefix'),
                request_args.get('resumptionToken'),
                request_args.get('from'),
                request_args.get('until')
            )
            request_args['base_uri_oai'] = settings.BASE_URI_OAI
            request_args['date_stamp'] = date_stamp
            template = render_template('oai_list_identifiers.xml',
                                       samples=samples,
                                       request_args=request_args,
                                       resumptiontoken=resumption_token)
            response = make_response(template)
            response.mimetype = 'text/xml'
            return response
        except ValueError:
            values = {
                'response_date': date_stamp,
                'request_uri': base_url,
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
                }
            template = render_template('oai_error.xml', values=values), 400
            response = make_response(template)
            response.mimetype = 'text/xml''application/xml'
            return response

    elif verb == 'ListMetadataFormats':
        # render_template
        template = render_template(
            'oai_list_metadata_formats.xml',
            identifier=request_args.get('identifier'),
            response_date=date_stamp,
            base_url=settings.BASE_URI_OAI
        ), 200
        response = make_response(template)
        response.mimetype = 'text/xml'
        return response

    elif verb == 'ListRecords':
        # render_template
        try:
            samples, token = oai_functions.list_records(
                request_args.get('metadataPrefix'),
                request_args.get('resumptionToken'),
                request_args.get('from'),
                request_args.get('until')
            )

            request_args['date_stamp'] = date_stamp
            request_args['base_uri_oai'] = settings.BASE_URI_OAI
            template = render_template('oai_list_records.xml',
                                       samples=samples,
                                       resumptiontoken=token,
                                       request_args=request_args,
                                       base_url=base_url)
            response = make_response(template)
            response.mimetype = 'text/xml'
            return response
        except ValueError:
            values = {
                'response_date': date_stamp,
                'request_uri': base_url,
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
                }
            template = render_template('oai_error.xml', values=values), 400
            response = make_response(template)
            response.mimetype = 'text/xml'
            return response

    elif verb == 'ListSets':
        # render_template
        values = {
            'response_date': date_stamp,
            'base_url': settings.BASE_URI_OAI
        }
        template = render_template('oai_list_sets.xml', values=values), 200
        response = make_response(template)
        response.mimetype = 'text/xml'
        return response
