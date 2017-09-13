# taken from https://github.com/infrae/pyoai/blob/master/src/oaipmh/datestamp.py
class OaiError(Exception):
    def oainame(self):
        name = self.__class__.__name__
        # strip off 'Error' part
        name = name[:-5]
        # lowercase error name
        name = name[0].lower() + name[1:]
        return name


class BadArgumentError(OaiError):
    pass


class BadVerbError(OaiError):
    pass


class BadResumptionTokenError(OaiError):
    pass


class CannotDisseminateFormatError(OaiError):
    pass


class IdDoesNotExistError(OaiError):
    pass


class NoRecordsMatchError(OaiError):
    pass


class NoMetadataFormatsError(OaiError):
    pass


class NoSetHierarchyError(OaiError):
    pass


class UnknownError(OaiError):
    pass


# errors not defined by OAI-PMH but which can occur in a client when
# the server is somehow misbehaving
class ClientError(Exception):
    def details(self):
        """Error details in human readable text.
        """
        raise NotImplementedError


class XMLSyntaxError(ClientError):
    """The OAI-PMH XML can not be parsed as it is not well-formed.
    """

    def details(self):
        return ("The data delivered by the server could not be parsed, as it "
                "is not well-formed XML.")


class DatestampError(ClientError):
    """The OAI-PMH datestamps were not proper UTC datestamps as by spec.
    """

    def __init__(self, datestamp):
        self.datestamp = datestamp

    def details(self):
        return "An illegal datestamp was encountered: %s" % self.datestamp
