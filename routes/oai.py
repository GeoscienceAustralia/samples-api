import datetime
from flask import Blueprint, render_template, request, make_response, Response
import oai_functions
from model.datestamp import datetime_to_datestamp
import config
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
        response.headers['Content-Type'] = 'text/xml'

        return response

    # validate all request variables
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
        response.headers['Content-Type'] = 'text/xml'

        return response

    # now call underlying implementation, based on the verb
    if verb == 'GetRecord':
        try:
            from model.sample import Sample
            s = Sample(request_args['identifier'])

            if request_args['metadataPrefix'] == 'oai_dc':
                record_xml = s.export_dc_xml()
            elif request_args['metadataPrefix'] == 'igsn':
                record_xml = s.export_igsn_xml()
            elif request_args['metadataPrefix'] == 'csirov3':
                record_xml = s.export_csirov3_xml()

            if s.date_acquired is not None:
                datestamp = datetime_to_datestamp(s.date_acquired)
            else:
                datestamp = ''
            return Response(
                render_template(
                    'oai_get_record.xml',
                    response_date=datetime_to_datestamp(datetime.datetime.now()),
                    identifier=request_args['identifier'],
                    metadataPrefix=request_args['metadataPrefix'],
                    datestamp=datestamp,
                    record_xml=record_xml
                ),
                mimetype='text/xml'
            )

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
            'admin_email': config.ADMIN_EMAIL,
            'base_url': config.BASE_URI_OAI,
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
            request_args['base_uri_oai'] = config.BASE_URI_OAI
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
            response.mimetype = 'text/xml''text/xml'
            return response

    elif verb == 'ListMetadataFormats':
        # render_template
        template = render_template(
            'oai_list_metadata_formats.xml',
            identifier=request_args.get('identifier'),
            response_date=date_stamp,
            base_url=config.BASE_URI_OAI
        ), 200
        response = make_response(template)
        response.mimetype = 'text/xml'
        return response

    elif verb == 'ListRecords':
        try:
            samples, token = oai_functions.list_records_xml(
                request_args.get('metadataPrefix'),
                request_args.get('resumptionToken'),
                request_args.get('from'),
                request_args.get('until')
            )

            dt = datetime.datetime.now()
            date_stamp = datetime_to_datestamp(dt)

            request_args['date_stamp'] = date_stamp
            request_args['base_uri_oai'] = config.BASE_URI_OAI
            template = render_template('oai_list_records.xml',
                                       datestamp=date_stamp,
                                       metadataPrefix=request_args.get('metadataPrefix'),
                                       base_uri_oai=request.base_url,
                                       samples=samples,
                                       resumptiontoken=token)
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
        # TODO: create a set for all GA records in readiness for sets for each other Geological Survey samples GA houses
        # render_template
        values = {
            'response_date': date_stamp,
            'base_url': config.BASE_URI_OAI
        }
        template = render_template('oai_list_sets.xml', values=values), 200
        response = make_response(template)
        response.mimetype = 'text/xml'
        return response
