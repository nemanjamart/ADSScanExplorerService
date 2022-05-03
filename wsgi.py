from werkzeug.serving import run_simple
from presentation_api import app as application


if __name__ == "__main__":

    run_simple(
        '0.0.0.0', 8181, application, use_reloader=False, use_debugger=True
    )
