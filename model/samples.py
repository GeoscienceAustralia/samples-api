from datestamp import *
from datetime import datetime, timedelta

def calc_expiration_date(request_datestamp):
    '''
    responseDate = 2017-02-08T06:01:12Z
    expirationDate=2017-02-08T07:01:13Z
    '''
    request_date = datestamp_to_datetime(request_datestamp)
    expiration_date = request_date + timedelta(hours=1)
    expiration_timestamp = datetime_to_datestamp(expiration_date)

    return expiration_timestamp