from os.path import dirname, realpath, join, abspath

APP_DIR = dirname(dirname(realpath(__file__)))
TEMPLATES_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'templates')
STATIC_DIR = join(dirname(dirname(abspath(__file__))), 'view', 'static')
LOGFILE = APP_DIR + '/flask.log'
DEBUG = True

XML_API_URL_SAMPLESET = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSampleSet' \
                        '?pOrder=IGSN&pPageNo={0}&pNoOfLinesPerPage={1}'
XML_API_URL_SAMPLE = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSample?pIGSN={0}'

XML_API_URL_SAMPLESET_DATE_RANGE = \
    'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSampleSet' \
    '?pOrder=IGSN&pPageNo={0}&pNoOfLinesPerPage={1}&pModifiedFromDate={2}' \
    '&pModifiedToDate={3}'

XML_API_URL_MIN_DATE = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_Earliest_Date_Modified'
XML_API_URL_TOTAL_COUNT = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_Number_Modified'
XML_API_URL_TOTAL_COUNT_DATE_RANGE = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_Number_Modified'\
                                     '?pModifiedFromDate={0}&pModifiedToDate={1}'

ADMIN_EMAIL = 'dataman@ga.gov.au'

REGISTER_BASE_URI = 'http://pid.geoscience.gov.au/sample/'
URI_SAMPLE_CLASS = 'http://pid.geoscience.gov.au/def/ont/ga/igsn#Sample'
URI_SAMPLE_INSTANCE_BASE = 'http://pid.geoscience.gov.au/sample/'
BASE_URI_OAI = 'http://pid.geoscience.gov.au/oai'

OAI_BATCH_SIZE = 1000

GOOGLE_MAPS_API_KEY_EMBED = 'AIzaSyDhuFCoJynhhQT7rcgKYzk3i7K77IEwjO4'
GOOGLE_MAPS_API_KEY = 'AIzaSyCUDcjVRsIHVHpv53r7ZnaX5xzqJbyGk58'
