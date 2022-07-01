from werkzeug.serving import run_simple, WSGIRequestHandler
from scan_explorer_service import app as application

class ScriptNameHandler(WSGIRequestHandler):
    def make_environ(self):
        environ = super().make_environ()
        environ['SCRIPT_NAME'] = application.config.get('APP_VIRTUAL_ROOT')
        return environ

if __name__ == "__main__":

    run_simple(
        '0.0.0.0', 8181, application, use_reloader=False, use_debugger=True, threaded=True, request_handler=ScriptNameHandler
    )
