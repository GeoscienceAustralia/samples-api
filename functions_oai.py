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

# https://www.openarchives.org/OAI/openarchivesprotocol.html, 3.6 Error and Exception Conditions
OAI_ERRORS = {
    'badArgument': 'Value of the verb argument is not a legal OAI-PMH verb, the verb argument is missing, or the verb '
                   'argument is repeated.',

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
