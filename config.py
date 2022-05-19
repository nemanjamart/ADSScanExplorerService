LOG_STDOUT = True
LOGGING_LEVEL = "DEBUG"
ENV = "development"

IMAGE_API_SERVER = 'http://localhost:8182'
IMAGE_API_BASE_PATH = '/iiif/2'
IMAGE_API_BASE_URL = f'{IMAGE_API_SERVER}{IMAGE_API_BASE_PATH}'

SQLALCHEMY_DATABASE_URI = 'postgres://scan_explorer:scan_explorer@postgres:5432/scan_explorer_pipeline'
SQLALCHEMY_TRACK_MODIFICATIONS = False

ELASTIC_SEARCH_URL = 'http://es:9200'
ELASTIC_SEARCH_INDEX = 'scan-explorer'

ADS_API_URL = 'https://api.adsabs.harvard.edu/v1/search/query'