class LDAPI:


    """
    Associates an RDF mimetype to an rdflib RDF format
    """
    MIMETYPES_PARSERS = {
        'text/turtle': 'turtle',
        'application/rdf+xml': 'xml',
        'application/rdf+json': 'json-ld',
        'text/ntriples': 'nt',
        'text/nt': 'nt',
        'text/n3': 'nt',
    }

    """
    Matches the file extension to MIME types
    """
    MIMETYPES_FILE_EXTENSTIONS = {
        'text/turtle': '.ttl',
        'application/rdf+xml': '.rdf',
        'application/rdf+json': '.json',
        'text/ntriples': '.nt',
        'text/nt': 'nt',
        'text/n3': 'nt',
        'application/xml': '.xml',
        'text/xml': '.xml',
    }
