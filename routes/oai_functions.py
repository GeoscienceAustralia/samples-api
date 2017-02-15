from model import Sample
import settings
from lxml import etree
from StringIO import StringIO
import requests
from flask import Response, render_template
import datetime as datetime

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
        'from_': 'optional',
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
    verb = qsa_args['verb']
    other_args = qsa_args.copy()
    del other_args['verb']

    argspec = OAI_ARGS.get(verb)
    if argspec is None:
        raise ParameterError('The OAI verb is not correct. Must be one of {0}'.format(', '.join(OAI_ARGS.iterkeys())))

    exclusive = None
    for arg_name, arg_type in list(argspec.items()):
        if arg_type == 'exclusive':
            exclusive = arg_name

    # check if we have unknown arguments
    for key, value in list(other_args.items()):
        if key not in argspec:
            msg = "Unknown argument: %s" % key
            raise ParameterError(msg)
    # first investigate if we have exclusive argument
    if exclusive in other_args:
        if len(other_args) > 1: 
            msg = ("Exclusive argument %s is used but other "
                   "arguments found." % exclusive)
            raise ParameterError(msg)
        return
    # if not exclusive, check for required
    for arg_name, arg_type in list(argspec.items()):
        if arg_type == 'required':
            msg = "Argument required but not found: %s" % arg_name
            if arg_name not in other_args:
                raise ParameterError(msg)

    return True


def get_record(request):
    try:
        sample = Sample(settings.XML_API_URL_SAMPLE, request.args.get('identifier'))

        return sample.export_dc_xml()
    except ValueError:
        raise ValueError

def list_records(request):
    samples_dict =[]
    #  TODO need to implement from, until, metadataprefix and resumption token
    oracle_api_samples_url = settings.XML_API_URL_SAMPLESET.format(1)

    r = requests.get(oracle_api_samples_url)
    if "No data" in r.content:
        raise ParameterError('No Data')
    if not r.content.startswith('<?xml version="1.0" ?>'):
        xml = '<?xml version="1.0" ?>\n' + r.content
    else:
        xml = r.content
    context = etree.iterparse(StringIO(xml), tag='ROW')
    for event, elem in context:
        samples_dict.append(props(Sample(None, None, StringIO(etree.tostring(elem)))))

    return samples_dict

def list_identifiers(request):
    samples_dict =[]
    #  TODO need to implement from, until, metadataprefix and resumption token
    oracle_api_samples_url = settings.XML_API_URL_SAMPLESET.format(1)

    r = requests.get(oracle_api_samples_url)
    if "No data" in r.content:
        raise ParameterError('No Data')
    if not r.content.startswith('<?xml version="1.0" ?>'):
        xml = '<?xml version="1.0" ?>\n' + r.content
    else:
        xml = r.content
    context = etree.iterparse(StringIO(xml), tag='ROW')
    for event, elem in context:
        samples_dict.append(props(Sample(None, None, StringIO(etree.tostring(elem)))))

    return samples_dict

def props(x):
    return dict((key, getattr(x, key)) for key in dir(x) if key not in dir(x.__class__))

def calc_expiration_date(request_date):
    '''
    responseDate = 2017-02-08T06:01:12Z
    expirationDate=2017-02-08T07:01:13Z
    '''



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

    print 'valid_oai_args(args[\'verb\'])', valid_oai_args(args['verb'])
    print 'validate_oai_parameters(args)', validate_oai_parameters(args)
