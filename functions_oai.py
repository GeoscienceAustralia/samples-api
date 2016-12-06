# OAI_ARGS = {
#     'GetRecord': {
#         'required': ['identifier', 'metadataPrefix'],
#         'optional': [],
#         'exclusive': []
#     },
#     'GetMetadata': {
#         'required': ['identifier', 'metadataPrefix'],
#         'optional': [],
#         'exclusive': []
#     },
#
#     'Identify': {
#         'required': [],
#         'optional': [],
#         'exclusive': []
#     },
#     'ListIdentifiers': {
#         'required': ['metadataPrefix'],
#         'optional': ['from', 'until', 'set'],
#         'exclusive': ['resumptionToken']
#     },
#     'ListMetadataFormats': {
#         'required': [],
#         'optional': ['identifier'],
#         'exclusive': []
#     },
#     'ListRecords': {
#         'required': ['metadataPrefix'],
#         'optional': ['from', 'until', 'set'],
#         'exclusive': ['resumptionToken']
#     },
#     'ListSets': {
#         'required': [],
#         'optional': [],
#         'exclusive': ['resumptionToken']
#     },
# }

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
    },

    'ListMetadataFormats': {
        'identifier': 'optional'
    },

    'ListRecords': {
        'from_': 'optional',
        'until': 'optional',
        'set': 'optional',
        'metadataPrefix': 'required',
    },

    'ListSets': {
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

    pass


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

    pass


class ParameterError(ValueError):
    pass


if __name__ == '__main__':
    args = {
        'verb': 'GetRecord',
        'identifier': 'AU100',
        'metadataPrefix': 'oai_dc'
    }

    print 'valid_oai_args(args[\'verb\'])', valid_oai_args(args['verb'])
    print 'validate_oai_parameters(args)', validate_oai_parameters(args)
