import datetime
from flask import Blueprint, render_template, request, make_response
import oai_functions
from model.datestamp import datetime_to_datestamp
import settings
oai_ = Blueprint('oai', __name__)


@oai_.route('/oai')
def oai():
    # TODO: validate args using functions_oai
    dt = datetime.datetime.now()
    date_stamp = datetime_to_datestamp(dt)
    base_url = request.base_url
    if request.args.get('verb'):
        verb = request.args.get('verb')
    else:
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
        oai_functions.validate_oai_parameters(request.args)
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

    # TODO: implement using lxml etree or XML template?
    if verb == 'GetRecord':
        # render_template
        try:
            xml = oai_functions.get_record(request)
            return xml
        except ValueError:
            values = {
                'response_date': date_stamp,
                'request_uri': base_url,
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
                }
            template = render_template('oai_error.xml', values=values), 400
            response = make_response(template)
            response.headers['Content-Type'] = 'application/xml'

            return response

        pass

    elif verb == 'ListIdentifiers':
        # render_template
        try:

            samples, resumption_token = oai_functions.list_identifiers(request)
            request_args = request.args

            template = render_template('oai_list_identifiers.xml',
                                       samples=samples,
                                       request_args=request_args,
                                       base_url=base_url,
                                       resumption_token=resumption_token)
            response = make_response(template)
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
            response.headers['Content-Type'] = 'application/xml'

            return response


    elif verb == 'ListRecords':
        # render_template
        try:
            samples = oai_functions.list_records(request)
            request_args = request.args

            template = render_template('oai_list_records.xml',
                                       samples=samples,
                                       request_args=request_args,
                                       base_url=base_url)
            response = make_response(template)
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
            response.headers['Content-Type'] = 'application/xml'

            return response


    elif verb == 'Identify':
        values = {
            'response_date': date_stamp,
            'admin_email': settings.ADMIN_EMAIL
            }
        template = render_template('oai_identify.xml', values=values), 400
        response = make_response(template)
        response.headers['Content-Type'] = 'application/xml'

        return response
