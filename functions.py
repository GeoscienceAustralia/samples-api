def get_file_extension(mimetype):
    """
    Matches the file extension to MIME types

    :param mimetype: an HTTP mime type
    :return: a string
    """
    file_extension = {
        'text/turtle': '.ttl',
        'application/rdf+xml': '.rdf',
        'application/rdf+json': '.json',
        'application/xml': '.xml',
        'text/xml': '.xml',
    }

    return file_extension[mimetype]
