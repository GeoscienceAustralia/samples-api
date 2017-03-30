from model import Sample
import settings
from lxml import etree
from StringIO import StringIO
import requests
from flask import Response, render_template
from model.datestamp import *
from datetime import datetime, timedelta


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

# https://www.openarchives.org/OAI/openarchivesprotocol.html, 3.6 Error and Exception Conditions
OAI_ERRORS = {
    'badArgument': 'Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb '
                   'argument is repeated.',
}


def valid_oai_args(verb):
    argspec = OAI_ARGS.get(verb)
    if argspec is None:
        raise ParameterError('The OAI verb is not correct. Must be one of {0}'.format(', '.join(OAI_ARGS.iterkeys())))

    return True


def validate_oai_parameters(qsa_args):
    argspec = OAI_ARGS.get(qsa_args['verb'])
    if argspec is None:
        raise ParameterError('The OAI verb is not correct. Must be one of {0}'.format(', '.join(OAI_ARGS.iterkeys())))

    exclusive = None
    for arg_name, arg_type in list(argspec.items()):
        if arg_type == 'exclusive':
            exclusive = arg_name

    # check if we have unknown arguments
    for key, value in list(qsa_args.items()):
        if key != 'verb':
            if key not in argspec:
                msg = "Unknown argument: %s" % key
                raise ParameterError(msg)
    # first investigate if we have exclusive argument
    if exclusive in qsa_args:
        if len(qsa_args) > 2:  # verb + exclusive
            msg = ("Exclusive argument %s is used but other "
                   "arguments found." % exclusive)
            raise ParameterError(msg)
        return
    # if not exclusive, check for required
    for arg_name, arg_type in list(argspec.items()):
        if arg_name != 'verb':
            if arg_type == 'required':
                msg = "Argument required but not found: %s" % arg_name
                if arg_name not in qsa_args:
                    raise ParameterError(msg)

    return True


def get_record(identifier):
    sample = Sample(settings.XML_API_URL_SAMPLE, identifier)

    return props(sample)
    # try:
    #
    # except ValueError:
    #     raise ValueError


def list_records(metadataPrefix, resumptionToken=None, from_=None, until=None):
    samples_dict = []
    no_per_page = settings.OAI_BATCH_SIZE
    page_no = 1

    if resumptionToken is None:
        oracle_api_samples_url = settings.XML_API_URL_SAMPLESET.format(page_no, no_per_page)
    else:
        oracle_api_samples_url = create_url_query_token(resumptionToken)

    r = requests.get(oracle_api_samples_url)

    if "No data" in r.content:
        raise ParameterError('No Data')

    xml = r.content
    context = etree.iterparse(StringIO(xml), tag='ROW')
    for event, elem in context:
        samples_dict.append(props(Sample(None, None, StringIO(etree.tostring(elem)))))

    resumption_token = get_resumption_token(metadataPrefix, resumptionToken, from_, until)

    return samples_dict, resumption_token


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
        [from_,
         until,
         cursor,
         metadataPrefix] = resumptionToken.split(',')
    else:
        if from_ is None:
            from_ = '2011-06-01T00:00:00Z'

        if until is None:
            until = '9999-12-31T23:59:59Z'

        cursor = 0
    complete_list_size = get_complete_list_size(from_, until)
    cursor_next = cursor + settings.OAI_BATCH_SIZE
    if cursor_next >= complete_list_size:
        next_resumption_token = None
    else:
        next_resumption_token = {'expiration_date': expiration_date,
                                 'complete_list_size': complete_list_size,
                                 'cursor': cursor,
                                 'from_': from_,
                                 'until': until,
                                 'cursor_next': cursor_next,
                                 'metadataPrefix': metadataPrefix}

    return next_resumption_token


def get_earliest_date():
    """
    queries GA's ORACLE DB and gets the earliest modified
    date from the samples table.
    :return: a date object
    """
    r = requests.get(settings.XML_API_URL_MIN_DATE)

    if "No data" in r.content:
        raise ParameterError('No Data')

    xml = r.content
    context = etree.iterparse(StringIO(xml), tag='EARLIEST_MODIFIED_DATE')
    for event, elem in context:
        str_min_date = elem.text

    min_date = datetime.strptime(str_min_date, '%Y-%m-%d %H:%M:%S')

    return min_date


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

    r = requests.get(settings.XML_API_URL_TOTAL_COUNT_DATE_RANGE.format(str_from_date, str_until_date))

    if "No data" in r.content:
        raise ParameterError('No Data')

    xml = r.content

    context = etree.iterparse(StringIO(xml), tag='RECORD_COUNT')
    for event, elem in context:
        str_record_count = elem.text


    return str_record_count


def create_url_query_token(token):
    """
    returns the url to query GA's Samples database based
    on a resumption token.
    :param token: a resumption token
    :return:
    """
    no_per_page = settings.OAI_BATCH_SIZE

    [from_,until,batch_num,metadataPrefix] =token.split(',')
    from_date = convert_datestamp_to_oracle(from_)
    until_date = convert_datestamp_to_oracle(until)

    oracle_api_samples_url = settings.XML_API_URL_SAMPLESET_DATE_RANGE.format(batch_num,no_per_page,from_date,until_date)
    return oracle_api_samples_url


def props(x):
    return dict((key, getattr(x, key)) for key in dir(x) if key not in dir(x.__class__))


def calc_expiration_datestamp():
    """
    responseDate = 2017-02-08T06:01:12Z
    expirationDate=2017-02-08T07:01:13Z
    """
    dt = datetime.now()
    request_datestamp = datetime_to_datestamp(dt)
    request_date = datestamp_to_datetime(request_datestamp)
    expiration_date = request_date + timedelta(hours=1)
    expiration_timestamp = datetime_to_datestamp(expiration_date)

    return expiration_timestamp


class ParameterError(ValueError):
    pass


if __name__ == '__main__':
    args = {
        'verb': 'GetRecord',
        'identifier': 'AU100',
        'metadataPrefix': 'oai_dc'
    }
    s = Sample(settings.XML_API_URL_SAMPLE, args['identifier'])
    dc_xml = s.export_dc_xml()

#    print 'valid_oai_args(args[\'verb\'])', valid_oai_args(args['verb'])
#    print 'validate_oai_parameters(args)', validate_oai_parameters(args)
