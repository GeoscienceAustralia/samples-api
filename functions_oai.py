OAI_ARGS = {
    'GetRecord': {
        'required': ['identifier', 'metadataPrefix'],
        'optional': [],
        'exclusive': []
    },
    'Identify': {
        'required': [],
        'optional': [],
        'exclusive': []
    },
    'ListIdentifiers': {
        'required': ['metadataPrefix'],
        'optional': ['from', 'until', 'set'],
        'exclusive': ['resumptionToken']
    },
    'ListMetadataFormats': {
        'required': [],
        'optional': ['identifier'],
        'exclusive': []
    },
    'ListRecords': {
        'required': ['metadataPrefix'],
        'optional': ['from', 'until', 'set'],
        'exclusive': ['resumptionToken']
    },
    'ListSets': {
        'required': [],
        'optional': [],
        'exclusive': ['resumptionToken']
    },
}


def valid_oai_args(verb, other_args):
    args = OAI_ARGS.get(verb)
    if args is None:
        raise ParameterError('The OAI verb is not correct. Must be one of {0}'.format(', '.join(OAI_ARGS.iterkeys())))

    return args

def validate_oai_parameters(args):
    # validate using OAI_ARGS
    pass

class ParameterError(ValueError):
    pass


if __name__ == '__main__':
    print valid_oai_args('ListIdentifiers', [])
