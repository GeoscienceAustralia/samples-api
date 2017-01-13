APP_DIR = 'c:/work/igsn-ld-api/'
STATIC_DIR = 'static/'
LOGFILE = APP_DIR + 'igsn-ld-api.log'
HOST = '0.0.0.0'
PORT = 8080
THREADED = False
DEBUG = True

BASE_URI = 'http://localhost:' + str(PORT)
# TODO: depricate WEB_SUBFOLDER in favour of url_for in templates, like PROMS Server
WEB_SUBFOLDER = ''  # no trailing slash

# Internal Oracle URL
# XML_API_URL = 'http://biotite.ga.gov.au:7777/wwwstaff_distd/a.igsn_api.get_igsnSample?pIGSN=' + igsn
XML_API_URL = 'http://dbforms.ga.gov.au/www_distp/a.igsn_api.get_igsnSampleSet?pOrder=IGSN&pPageNo={0}&pNoOfLinesPerPage=25'

OAI_BASE_URL = "http://localhost:8080/oai"
