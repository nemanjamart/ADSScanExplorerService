import os
import sys
from flask import Blueprint, request
from adsmutils import ADSFlask
from flask_limiter import Limiter
import flask_limiter.util

from .views import bp_manifest, bp_search, bp_canvas
from .extensions import manifest_factory


def get_remote_address():
    return request.headers.get('X-Original-Forwarded-For', flask_limiter.util.get_remote_address())

def create_app(**config):
    opath = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    if opath not in sys.path:
        sys.path.insert(0, opath)

    if config:
        app = ADSFlask(__name__, static_folder=None, local_config=config)
    else:
        app = ADSFlask(__name__, static_folder=None)
    
    app.url_map.strict_slashes = False

    if app.config['ENV'] == "development":
        app.debug = True

    Limiter(app, key_func=get_remote_address)

    # Configure manifest factory
    manifest_factory.set_base_prezi_uri(app.config.get('BASE_URL'))
    manifest_factory.set_base_image_uri(app.config.get('IMAGE_API_BASE_URL'))
    manifest_factory.set_iiif_image_info(2.0, 2) # Version, ComplianceLevel
    
    if app.debug:
        manifest_factory.set_debug("error_on_warning")
    else:
        manifest_factory.set_debug("error")

    # Wrapping views with shared base url
    bp_wrapper = Blueprint('wrapper', __name__)
    bp_wrapper.register_blueprint(bp_manifest)
    bp_wrapper.register_blueprint(bp_canvas)
    bp_wrapper.register_blueprint(bp_search)
    app.register_blueprint(bp_wrapper, url_prefix=app.config.get('BASE_PATH'))

    return app


app = create_app()