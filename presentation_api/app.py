import os
import sys
from flask import Blueprint, request
from adsmutils import ADSFlask
from flask_limiter import Limiter
import flask_limiter.util


from .views import *
from .extensions import manifest_factory, compress

def get_remote_address():
    return request.headers.get('X-Original-Forwarded-For', flask_limiter.util.get_remote_address())

def register_extensions(app):
    """ Register extensions.

    Args:
        app (ADSFlask): Application object
    """

    compress.init_app(app)
    Limiter(app, key_func=get_remote_address)

    # base_prezi_uri should be updated when handling the request.
    manifest_factory.set_base_prezi_uri(app.config.get('BASE_URL')) 
    manifest_factory.set_base_image_uri(app.config.get('IMAGE_API_BASE_URL'))
    manifest_factory.set_iiif_image_info(2.0, 2) # Version, ComplianceLevel

def register_blueprints(app):
    """ Register all views with the flask application. 

        The views are registered with a wrapper
        to allow for global manipulation of base path
        and response headers. 

    Args:
        app (ADSFlask): Application object
    """

    bp_wrapper = Blueprint('wrapper', __name__)
    bp_wrapper.register_blueprint(bp_manifest)
    bp_wrapper.register_blueprint(bp_canvas)
    bp_wrapper.register_blueprint(bp_search)

    @bp_wrapper.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
        
    app.register_blueprint(bp_wrapper, url_prefix=app.config.get('BASE_PATH'))

def create_app(**config):
    """ Create application and initialize dependencies.

    Returns:
        ADSFlask: Application object
    """
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
    
    if app.debug:
        manifest_factory.set_debug("error_on_warning")
    else:
        manifest_factory.set_debug("error")

    register_blueprints(app)
    register_extensions(app)

    return app

app = create_app()
