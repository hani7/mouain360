import os
import sys
import traceback

sys.path.insert(0, os.path.dirname(__file__))

def application(environ, start_response):
    try:
        from django.core.wsgi import get_wsgi_application
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
        _app = get_wsgi_application()
        return _app(environ, start_response)
    except Exception as e:
        start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
        error_msg = traceback.format_exc()
        return [b"CRASH REPORT:\n\n", error_msg.encode('utf-8')]
