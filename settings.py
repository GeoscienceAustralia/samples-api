APP_DIR = 'E:/samples-api/'
LOGFILE = APP_DIR + 'samples-api.log'
PORT = 8080
DEBUG = True

# Internal Oracle URL
# XML_API_URL = 'http://biotite.ga.gov.au:7777/wwwstaff_distd/a.igsn_api.get_igsnSample?pIGSN=' + igsn
XML_API_URL_SAMPLESET = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSampleSet' \
                        '?pOrder=IGSN&pPageNo={0}&pNoOfLinesPerPage={1}'
XML_API_URL_SAMPLE = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSample?pIGSN={0}'

XML_API_URL_SAMPLESET_DATE_RANGE = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSampleSet' \
                        '?pOrder=IGSN&pPageNo={0}&pNoOfLinesPerPage={1}&pModifiedFromDate={2}' \
                                   '&pModifiedToDate={3}'

XML_API_URL_MIN_DATE = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_Earliest_Date_Modified'
XML_API_URL_TOTAL_COUNT = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_Number_Modified'
XML_API_URL_TOTAL_COUNT_DATE_RANGE = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_Number_Modified'\
                                        '?pModifiedFromDate={0}&pModifiedToDate={1}'

ADMIN_EMAIL = 'data@ga.gov.au'

BASE_URI_SAMPLE = 'http://pid.geoscience.gov.au/sample/'
BASE_URI_OAI = 'http://pid.geoscience.gov.au/oai'

OAI_BATCH_SIZE =10
