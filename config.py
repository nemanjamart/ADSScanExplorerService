LOG_STDOUT = True
LOGGING_LEVEL = "DEBUG"
ENV = "development"

PROXY_SERVER = "http://localhost:8184"
PROXY_PREFIX = "/v1/scan"

IMAGE_API_SERVER = 'http://localhost:8182'
IMAGE_API_BASE_PATH = '/iiif/2'
IMAGE_API_BASE_URL = f'{IMAGE_API_SERVER}{IMAGE_API_BASE_PATH}'
IMAGE_API_SLASH_SUB = '-~' # Must always correspond to the Cantaloupe setting CANTALOUPE_SLASH_SUBSTITUTE

SQLALCHEMY_DATABASE_URI = 'postgres://scan_explorer:scan_explorer@postgres_service/scan_explorer_service'
SQLALCHEMY_TRACK_MODIFICATIONS = False

OPEN_SEARCH_URL = 'http://opensearch-node1:9200'
OPEN_SEARCH_INDEX = 'scan-explorer'

ADS_SEARCH_SERVICE_URL = 'https://api.adsabs.harvard.edu/v1/search/query'
ADS_SEARCH_SERVICE_TOKEN = '<CHANGE ME>'