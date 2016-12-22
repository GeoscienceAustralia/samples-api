import datetime
from flask import Blueprint, Response, render_template, request, make_response
import oai_functions
oai_ = Blueprint('oai', __name__)
from renderers.datestamp import datetime_to_datestamp

@oai_.route('/oai')
def oai():
    # TODO: validate args using functions_oai
    dt = datetime.datetime.now()
    date_stamp = datetime_to_datestamp(dt)
    if request.args.get('verb'):
        verb = request.args.get('verb')
    else:
        values = {
            'response_date': date_stamp,
            'request_uri': 'http://54.66.133.7/igsn-ld-api/oai',
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

    # TODO: implement using lxml etree or XML template?
    if verb == 'GetRecord':
        # render_template
        try:
            xml = oai_functions.get_record(request.args)
            return xml
        except ValueError:
            values = {
                'response_date': date_stamp,
                'request_uri': 'http://54.66.133.7/igsn-ld-api/oai',
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
            }
            template = render_template('oai_error.xml', values=values), 400
            response = make_response(template)
            response.headers['Content-Type'] = 'application/xml'

            return response

        pass

    elif verb == 'Identify':
        values = {
                'response_date': date_stamp
            }
        template = render_template('oai_identify.xml', values=values), 400
        response = make_response(template)
        response.headers['Content-Type'] = 'application/xml'

        return response


