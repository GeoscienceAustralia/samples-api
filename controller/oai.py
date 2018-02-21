from flask import Blueprint, render_template, request, Response
from controller.oai_functions import *
from controller.oai_errors import *
import _config as conf

oai_ = Blueprint('oai', __name__)


def render_error(response_date, request_uri, oai_code, message, http_status=400):
    return Response(
        render_template(
            'oai_error.xml',
            response_date=response_date,
            request_uri=request_uri,
            oai_code=oai_code,
            message=message
        ),
        status=http_status,
        mimetype='text/xml'
    )


@oai_.route('/oai', methods=['GET', 'POST'])
def oai():
    # date in OAI format
    response_date = datetime_to_datestamp(datetime.datetime.now())

    # validate request parameters
    if len(request.values) < 1:
        return render_error(
            response_date,
            request.base_url,
            "badVerb",
            'You did not specify an OAI verb'
        )

    try:
        validate_oai_parameters(request.values)
    except OaiError as e:
        return render_error(response_date, request.base_url, e.oainame(), e)

    # call underlying implementation, based on the verb, since all parameters are valid
    if request.values.get('verb') == 'GetRecord':
        try:
            from model.sample import Sample
            s = Sample(request.values.get('identifier'))

            if s.date_modified is not None:
                date_modified = datetime_to_datestamp(s.date_modified)
            else:
                date_modified = '1900-01-01T00:00:00Z'

            if request.values.get('metadataPrefix') == 'igsn':
                record_xml = s.export_igsn_xml()
            elif request.values.get('metadataPrefix') == 'igsn-r1':
                record_xml = s.export_igsn_r1_xml()
            elif request.values.get('metadataPrefix') == 'csirov3':
                record_xml = s.export_csirov3_xml()
            else:  # 'oai_dc':
                record_xml = s.export_dct_xml()

            return Response(
                render_template(
                    'oai_get_record.xml',
                    response_date=response_date,
                    request_uri=request.base_url,
                    metadataPrefix=request.values.get('metadataPrefix'),
                    identifier=request.values.get('identifier'),
                    date_modified=date_modified,
                    record_xml=record_xml
                ),
                mimetype='text/xml'
            )

        except IdDoesNotExistError as e:
            message = 'The value of the identifier argument is unknown or illegal in this repository.'
            return render_error(response_date, request.base_url, e.oainame(), message)

    elif request.values.get('verb') == 'Identify':
        values = {
            'base_url': request.base_url,
            'admin_email': conf.ADMIN_EMAIL,
            'earliest_date': get_earliest_datestamp()
        }

        return Response(
            render_template(
                'oai_identify.xml',
                response_date=response_date,
                request_uri=request.base_url,
                values=values
            ),
            mimetype='text/xml'
        )

    elif request.values.get('verb') == 'ListIdentifiers':
        # render_template
        try:
            samples, resumption_token = list_records(
                request.values.get('metadataPrefix'),
                request.values.get('resumptionToken'),
                request.values.get('from'),
                request.values.get('until')
            )

            return Response(
                render_template(
                    'oai_list_identifiers.xml',
                    response_date=response_date,
                    request_uri=request.base_url,
                    metadataPrefix=request.values.get('metadataPrefix'),
                    samples=samples,
                    resumptiontoken=resumption_token
                ),
                mimetype='text/xml'
            )
        except ValueError:
            oai_code = 'idDoesNotExist'
            message = 'No matching identifier in GA Samples Database'
            return render_error(response_date, request.base_url, oai_code, message)

    elif request.values.get('verb') == 'ListMetadataFormats':
        return Response(
            render_template(
                'oai_list_metadata_formats.xml',
                response_date=response_date,
                request_uri=request.base_url,
                identifier=request.values.get('identifier')
            ),
            mimetype='text/xml'
        )

    elif request.values.get('verb') == 'ListRecords':
        try:
            samples, token = list_records_xml(
                request.values.get('metadataPrefix'),
                request.values.get('resumptionToken'),
                request.values.get('from'),
                request.values.get('until')
            )

            return Response(
                render_template(
                    'oai_list_records.xml',
                    response_date=response_date,
                    request_uri=request.base_url,
                    metadataPrefix=request.values.get('metadataPrefix'),
                    samples=samples,
                    resumptiontoken=token
                ),
                mimetype='text/xml'
            )

        except OaiError as e:
            return render_error(response_date, request.base_url, e.oainame(), e)

    elif request.values.get('verb') == 'ListSets':
        # TODO: create a set for all GA records in readiness for sets for each other Geological Survey samples GA houses
        return Response(
            render_template(
                'oai_list_sets.xml',
                response_date=response_date,
                request_uri=request.base_url
            ),
            mimetype='text/xml'
        )
