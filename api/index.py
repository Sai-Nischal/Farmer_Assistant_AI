import os
import sys

# Add project root directory to sys.path so app, agents, services, and models are importable
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

class VercelWSGIMiddleware:
    """
    WSGI middleware to fix Vercel serverless rewrite PATH_INFO behavior.
    When Vercel rewrites requests to /api/index, PATH_INFO can be set to /api/index
    or omit the client-requested route. This middleware inspects original URI headers
    and restores the correct route for Flask.
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # 1. Check for original request path in Vercel headers / environ
        req_uri = (
            environ.get('HTTP_X_FORWARDED_URI') or 
            environ.get('RAW_URI') or 
            environ.get('REQUEST_URI')
        )
        if req_uri:
            path_only = req_uri.split('?')[0]
            if path_only and path_only != '/api/index':
                environ['PATH_INFO'] = path_only

        # 2. If PATH_INFO is still /api/index, point to root /
        path = environ.get('PATH_INFO', '')
        if path in ('/api/index', '/api/index/'):
            environ['PATH_INFO'] = '/'
        elif path.startswith('/api/index/'):
            environ['PATH_INFO'] = path[len('/api/index'):]

        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
