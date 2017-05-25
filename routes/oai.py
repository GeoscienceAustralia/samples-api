import datetime
from flask import Blueprint, render_template, request, Response
import oai_functions
from model.datestamp import datetime_to_datestamp
import config
oai_ = Blueprint('oai', __name__)


def render_error(response_date, request_uri, values):
    return Response(
        render_template(
            'oai_error.xml',
            response_date=response_date,
            request_uri=request_uri,
            values=values
        ),
        status=400,
        mimetype='text/xml'
    )


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

    # common template variables
    response_date = datetime_to_datestamp(datetime.datetime.now())
    request_uri = request.base_url

    # error
    if verb is None:
        values = {
            'error_code': 'badVerb',
            'error_text': 'Illegal OAI verb'
        }

        return render_error(response_date, request_uri, values)

    # validate all request variables
    try:
        oai_functions.validate_oai_parameters(request_args)
    except ValueError:
        values = {
            'error_code': 'badArgument',
            'error_text': 'The request includes illegal arguments, is missing required arguments,\
                           includes a repeated argument, or values for arguments have an illegal syntax.'
            }

        return render_error(response_date, request_uri, values)

    # now call underlying implementation, based on the verb
    if verb == 'GetRecord':
        try:
            from model.sample import Sample
            s = Sample(request_args.get('identifier'))

            if s.date_modified is not None:
                date_modified = datetime_to_datestamp(s.date_modified)
            else:
                date_modified = '1900-01-01T00:00:00Z'

            if request_args['metadataPrefix'] == 'oai_dc':
                record_xml = s.export_dc_xml()
            elif request_args['metadataPrefix'] == 'igsn':
                record_xml = s.export_igsn_xml()
            elif request_args['metadataPrefix'] == 'igsn-dev':
                record_xml = s.export_igsn_dev_xml()
            elif request_args['metadataPrefix'] == 'csirov3':
                record_xml = s.export_csirov3_xml()

            return Response(
                render_template(
                    'oai_get_record.xml',
                    response_date=response_date,
                    request_uri=request_uri,
                    metadataPrefix=request_args['metadataPrefix'],
                    identifier=request_args.get('identifier'),
                    date_modified=date_modified,
                    record_xml=record_xml
                ),
                mimetype='text/xml'
            )

        except ValueError:
            values = {
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
            }

            return render_error(response_date, request_uri, values)

    elif verb == 'Identify':
        values = {
            'admin_email': config.ADMIN_EMAIL,
            'earliest_date': oai_functions.get_earliest_datestamp()
        }

        return Response(
            render_template(
                'oai_identify.xml',
                response_date=response_date,
                request_uri=request_uri,
                values=values
            ),
            mimetype='text/xml'
        )

    elif verb == 'ListIdentifiers':
        # render_template
        try:
            samples, resumption_token = oai_functions.list_records(
                request_args.get('metadataPrefix'),
                request_args.get('resumptionToken'),
                request_args.get('from'),
                request_args.get('until')
            )

            return Response(
                render_template(
                    'oai_list_identifiers.xml',
                    response_date=response_date,
                    request_uri=request_uri,
                    metadataPrefix=request_args.get('metadataPrefix'),
                    samples=samples,
                    resumptiontoken=resumption_token
                ),
                mimetype='text/xml'
            )
        except ValueError:
            values = {
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
            }

            return render_error(response_date, request_uri, values)

    elif verb == 'ListMetadataFormats':
        return Response(
            render_template(
                'oai_list_metadata_formats.xml',
                response_date=response_date,
                request_uri=request_uri,
                identifier=request_args.get('identifier')
            ),
            mimetype='text/xml'
        )

    elif verb == 'ListRecords':
        try:
            samples, token = oai_functions.list_records_xml(
                request_args.get('metadataPrefix'),
                request_args.get('resumptionToken'),
                request_args.get('from'),
                request_args.get('until')
            )

            return Response(
                render_template(
                    'oai_list_records.xml',
                    response_date=response_date,
                    request_uri=request_uri,
                    metadataPrefix=request_args.get('metadataPrefix'),
                    samples=samples,
                    resumptiontoken=token
                ),
                mimetype='text/xml'
            )

        except ValueError:
            values = {
                'error_code': 'idDoesNotExist',
                'error_text': 'No matching identifier in GA Samples Database'
            }

            return render_error(response_date, request_uri, values)

    elif verb == 'ListSets':
        # TODO: create a set for all GA records in readiness for sets for each other Geological Survey samples GA houses
        return Response(
            render_template(
                'oai_list_sets.xml',
                response_date=response_date,
                request_uri=request_uri
            ),
            mimetype='text/xml'
        )
