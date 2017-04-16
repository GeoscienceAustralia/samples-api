import datetime

# taken from https://github.com/infrae/pyoai/blob/master/src/oaipmh/datestamp.py


def datetime_to_datestamp(dt, day_granularity=False):
    assert dt.tzinfo is None  # only accept timezone naive datetimes
    # ignore microseconds
    dt = dt.replace(microsecond=0)
    result = dt.isoformat() + 'Z'
    if day_granularity:
        result = result[:-10]
    return result


# handy utility function not used by pyoai itself yet
def date_to_datestamp(d, day_granularity=False):
    return datetime_to_datestamp(
        datetime.datetime.combine(d, datetime.time(0)), day_granularity)


def datestamp_to_datetime(datestamp, inclusive=False):
    try:
        return _datestamp_to_datetime(datestamp, inclusive)
    except ValueError:
        raise DatestampError(datestamp)


def _datestamp_to_datetime(datestamp, inclusive=False):
    splitted = datestamp.split('T')
    if len(splitted) == 2:
        d, t = splitted
        if not t or t[-1] != 'Z':
            raise DatestampError(datestamp)
        # strip off 'Z'
        t = t[:-1]
    else:
        d = splitted[0]
        if inclusive:
            # used when a date was specified as ?until parameter
            t = '23:59:59'
        else:
            t = '00:00:00'
    YYYY, MM, DD = d.split('-')
    hh, mm, ss = t.split(':')  # this assumes there's no timezone info
    return datetime.datetime(
        int(YYYY), int(MM), int(DD), int(hh), int(mm), int(ss))


def tolerant_datestamp_to_datetime(datestamp):
    """A datestamp to datetime that's more tolerant of diverse inputs.

    Not used inside pyoai itself right now, but can be used when defining
    your own metadata schema if that has a broader variety of datetimes
    in there.
    """
    splitted = datestamp.split('T')
    if len(splitted) == 2:
        d, t = splitted
        # if no Z is present, raise error
        if t[-1] != 'Z':
            raise DatestampError(datestamp)
        # split off Z at the end
        t = t[:-1]
    else:
        d = splitted[0]
        t = '00:00:00'
    d_splitted = d.split('-')
    if len(d_splitted) == 3:
        YYYY, MM, DD = d_splitted
    elif len(d_splitted) == 2:
        YYYY, MM = d_splitted
        DD = '01'
    elif len(d_splitted) == 1:
        YYYY = d_splitted[0]
        MM = '01'
        DD = '01'
    else:
        raise DatestampError(datestamp)

    t_splitted = t.split(':')
    if len(t_splitted) == 3:
        hh, mm, ss = t_splitted
    else:
        raise DatestampError(datestamp)
    return datetime.datetime(
        int(YYYY), int(MM), int(DD), int(hh), int(mm), int(ss))


def str2datetime(datetime_string):
    """
    Helper function to convert a date string to a datetime
    """
    datetime_format_list = ['%Y-%m-%d %H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S',
                            '%Y-%m-%dT%H:%M:%S%Z',
                            '%Y-%m-%d',
                            '%d-%b-%y',
                            '%Y-%m-%dT%H:%M:%S.%f',
                            '%Y-%m-%dT%H:%M:%S%z',
                            '%Y-%m-%dT%H:%M:%S%Z',
                            '%Y-%m-%dT%H:%M:%S.%f%z'
                            ]

    date_time = None
    for datetime_format in datetime_format_list:
        try:
            date_time = datetime.datetime.strptime(str(datetime_string).strip(), datetime_format)
            break
        except ValueError:
            continue

    return date_time


def convert_datestamp_to_oracle(datestamp):
    """
    convert an OAI-PMH format datestamp into the date format
    required by GA's oracle web API.
    2016-12-20%2001:00:00
    """
    try:
        date = tolerant_datestamp_to_datetime(datestamp)
        oracle_api_date = date.strftime('%Y-%m-%dT%H:%M:%S')
        return oracle_api_date
    except ValueError:
        raise DatestampError(datestamp)


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

