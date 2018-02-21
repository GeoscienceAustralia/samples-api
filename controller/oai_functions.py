from datetime import datetime, timedelta
from io import BytesIO
import requests
from lxml import etree
import _config as conf
from model import Sample
from controller.oai_datestamp import *
from controller.oai_errors import *
import math


# https://www.openarchives.org/OAI/openarchivesprotocol.html, 3.6 Error and Exception Conditions
OAI_ARGS = {
    'GetRecord': {
        'identifier': 'required',
        'metadataPrefix': 'required'
    },

    'GetMetadata': {
        'identifier': 'required',
        'metadataPrefix': 'required'
    },

    'Identify': {
    },

    'ListIdentifiers': {
        'from': 'optional',
        'until': 'optional',
        'metadataPrefix': 'required',
        'set': 'optional',
        'resumptionToken': 'exclusive'
    },

    'ListMetadataFormats': {
        'identifier': 'optional'
    },

    'ListRecords': {
        'from': 'optional',
        'until': 'optional',
        'set': 'optional',
        'metadataPrefix': 'required',
        'resumptionToken': 'exclusive'
    },

    'ListSets': {
        'resumptionToken': 'exclusive'
    },
}


def validate_oai_parameters(qsa_args):
    """
    Validates GET or POST arguments against the OAI_ARGS dict

    :param qsa_args: query string or form parameters from a GET or POST request
    :return: True if valie, else raises a BadVerb or BadArgument error
    """
    expected_oai_args = OAI_ARGS.get(qsa_args['verb'])

    # check the verb
    if expected_oai_args is None:
        raise BadVerbError('The OAI verb is not correct. Must be one of {}'.format(', '.join(OAI_ARGS.keys())))

    # check if we have any unknown args given
    for key, value in list(qsa_args.items()):
        if key != 'verb' and key not in expected_oai_args:
            raise BadArgumentError("Unknown argument: {}".format(key))

    # check if we have any exclusive args given and any other args, apart from the verb
    exclusive_possible = None
    for arg_name, arg_type in list(expected_oai_args.items()):
        if arg_type == 'exclusive':
            exclusive_possible = arg_name
    exclusive_present = False
    for key, value in list(qsa_args.items()):
        if key == exclusive_possible:
            exclusive_present = True
    if exclusive_present and len(qsa_args) > 2:  # verb + exclusive
        raise BadArgumentError("Exclusive argument {} is used but other arguments found.".format(exclusive_possible))

    # if no exclusive present, check for required args
    if not exclusive_present:
        for arg_name, arg_type in list(expected_oai_args.items()):
            if arg_name != 'verb':
                if arg_type == 'required' and arg_name not in qsa_args:
                    raise BadArgumentError("Argument required but not found: {}".format(arg_name))
    return True


def list_records(metadataPrefix, resumptionToken=None, from_=None, until=None):
    # if we don't have a resumption token, start at the beginning
    if resumptionToken is None:
        oracle_api_samples_url = conf.XML_API_URL_SAMPLESET.format(1, conf.OAI_BATCH_SIZE)
    else:
        oracle_api_samples_url = create_url_query_token(resumptionToken)
        [from_, until, batch_num, metadataPrefix] = resumptionToken.split(',')

    r = requests.get(oracle_api_samples_url)

    if "No data" in r.content.decode('utf-8'):
        raise NoRecordsMatchError('No Data')

    samples = []

    for event, elem in etree.iterparse(BytesIO(r.content), tag='ROW'):
        samples.append(get_obj_vars_as_dict(Sample(None, '<root>{}</root>'.format(etree.tostring(elem)))))

    resumption_token = get_resumption_token(metadataPrefix, resumptionToken, from_, until)

    return samples, resumption_token


def list_records_xml(metadataPrefix, resumptionToken=None, from_=None, until=None):
    no_per_page = conf.OAI_BATCH_SIZE
    page_no = 1

    if resumptionToken is None:
        oracle_api_samples_url = conf.XML_API_URL_SAMPLESET.format(page_no, no_per_page)
    else:
        oracle_api_samples_url = create_url_query_token(resumptionToken)
        [from_, until, batch_num, metadataPrefix] = resumptionToken.split(',')

    print(oracle_api_samples_url)
    r = requests.get(oracle_api_samples_url)

    if "No data" in r.content.decode('utf-8'):
        raise NoRecordsMatchError(
            'The combination of the values of the from, until, '
            'set and metadataPrefix arguments results in an empty list.')

    samples = []

    for event, elem in etree.iterparse(BytesIO(r.content), tag='ROW'):
        # create a Sample for each XML ROW
        sample = Sample(None, '<root>{}</root>'.format(etree.tostring(elem)))
        if sample.date_modified is not None:
            datestamp = datetime_to_datestamp(sample.date_modified)
        else:
            datestamp = '1900-01-01T00:00:00Z'

        # make the record XML using the Sample export
        # for some reason, there's this odd whitespace character in the metadataPrefix
        metadataPrefix = metadataPrefix.replace(u'\u200b', '')
        if metadataPrefix == 'igsn':
            record_xml = sample.export_igsn_xml()
        elif metadataPrefix == 'igsn-r1':
            record_xml = sample.export_igsn_r1_xml()
        elif metadataPrefix == 'csirov3':
            record_xml = sample.export_csirov3_xml()
        else:  # oai_dc
            record_xml = sample.export_dct_xml()

        # make the full OAI record
        oai_record_vars = {
            'identifier': sample.igsn,
            'datestamp': datestamp,
            'record_xml': record_xml
        }
        if metadataPrefix == 'oai_dc':
            oai_record = '''
            <record>
                <header>
                    <identifier>{identifier}</identifier>
                    <datestamp>{datestamp}</datestamp>
                </header>
                {record_xml}
            </record>
                    '''.format(**oai_record_vars)
        else:
            oai_record = '''
            <record>
                <header>
                    <identifier>{identifier}</identifier>
                    <datestamp>{datestamp}</datestamp>
                </header>
                <metadata>
                    {record_xml}
                </metadata>
            </record>
                    '''.format(**oai_record_vars)

        # add the OAI record to the list of samples
        samples.append(oai_record)
    resumption_token = get_resumption_token(metadataPrefix, resumptionToken, from_, until)

    return samples, resumption_token


def get_resumption_token(metadataPrefix, resumptionToken=None, from_=None, until=None):
    """
    <resumptionToken expirationDate="2017-03-24T05:02:52Z"
    completeListSize="6267770" cursor="100">
    1490328172912,2011-06-01T00:00:00Z,9999-12-31T23:59:59Z,150,null,oai_dc
    </resumptionToken>
    :param resumptionToken:
    :param metadataPrefix:
    :param from_:
    :param until:
    :return:
    """

    expiration_date = calc_expiration_datestamp()

    if resumptionToken:
        [from_, until, cursor, metadataPrefix] = resumptionToken.split(',')
    else:
        if from_ is None:
            from_ = '2011-06-01T00:00:00Z'

        if until is None:
            until = '9999-12-31T23:59:59Z'

        cursor = 0

    complete_list_size = get_complete_list_size(from_, until)
    cursor_next = int(cursor) + conf.OAI_BATCH_SIZE
    if cursor_next >= complete_list_size:
        next_resumption_token = None
    else:
        next_resumption_token = {
            'expiration_date': expiration_date,
            'complete_list_size': complete_list_size,
            'cursor': cursor,
            'from_': from_,
            'until': until,
            'cursor_next': cursor_next,
            'metadataPrefix': metadataPrefix
        }

    return next_resumption_token


def get_earliest_date():
    """
    queries GA's ORACLE DB and gets the earliest modified
    date from the samples table.
    :return: a date object
    """
    r = requests.get(conf.XML_API_URL_MIN_DATE)

    if "No data" in r.content.decode('utf-8'):
        raise NoRecordsMatchError('No Data')

    xml = r.content
    context = etree.iterparse(BytesIO(xml), tag='EARLIEST_MODIFIED_DATE')
    for event, elem in context:
        str_min_date = elem.text

    return str2datetime(str_min_date)


def get_earliest_datestamp():
    """
    returns an OAI-PMH format datestamp of the earliest modified_date in GA's
    Samples database eg 2017-03-27T19:20:53Z
    :param :
    :return: an OAI-PMH format datestamp
    """
    return datetime_to_datestamp(get_earliest_date())


def get_complete_list_size(str_from_date=None, str_until_date=None):
    """
    queries GA's ORACLE DB and gets the number of records the query
    matches from the samples table.
    :return: an integer
    """

    if str_from_date is None:
        str_from_date = convert_datestamp_to_oracle('2011-06-01T00:00:00Z')
    else:
        str_from_date = convert_datestamp_to_oracle(str_from_date)
    if str_until_date is None:
        str_until_date = convert_datestamp_to_oracle('2099-12-31T23:59:59Z')
    else:
        str_until_date = convert_datestamp_to_oracle(str_until_date)

    r = requests.get(conf.XML_API_URL_TOTAL_COUNT_DATE_RANGE.format(str_from_date, str_until_date))

    if "No data" in r.content.decode('utf-8'):
        raise NoRecordsMatchError('No Data')

    context = etree.iterparse(BytesIO(r.content), tag='RECORD_COUNT')
    for event, elem in context:
        str_record_count = elem.text

    return int(str_record_count)


def create_url_query_token(token):
    """
    returns the url to query GA's Samples database based
    on a resumption token.
    :param token: a resumption token
    :return: A url for querying the samples DB
    """
    no_per_page = conf.OAI_BATCH_SIZE

    [from_, until, cursor, metadataPrefix] = token.split(',')
    from_date = convert_datestamp_to_oracle(from_)
    until_date = convert_datestamp_to_oracle(until)

    page_no = str(math.floor(int(cursor) / int(no_per_page)))

    oracle_api_samples_url = conf.XML_API_URL_SAMPLESET_DATE_RANGE.format(
        page_no, no_per_page, from_date, until_date
    )
    return oracle_api_samples_url


def get_obj_vars_as_dict(x):
    return dict((key, getattr(x, key)) for key in dir(x) if key not in dir(x.__class__))


def calc_expiration_datestamp():
    """
    responseDate = 2017-02-08T06:01:12Z
    expirationDate=2017-02-08T07:01:13Z
    """
    dt = datetime.datetime.now()
    request_datestamp = datetime_to_datestamp(dt)
    request_date = datestamp_to_datetime(request_datestamp)
    expiration_date = request_date + timedelta(hours=1)
    expiration_timestamp = datetime_to_datestamp(expiration_date)

    return expiration_timestamp


class ParameterError(ValueError):
    pass


if __name__ == '__main__':
    pass
