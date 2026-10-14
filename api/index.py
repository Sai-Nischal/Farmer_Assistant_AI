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
    """
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        # DEBUG: Log ALL environ keys that look like headers/URLs
        print(f"[VERCEL DEBUG] === REQUEST START ===", file=sys.stderr)
        for key, val in environ.items():
            if any(k in key.upper() for k in ['PATH', 'URI', 'URL', 'FORWARD', 'ORIGINAL', 'VERCEL', 'REWRITE', 'HOST', 'SERVER']):
                print(f"[VERCEL DEBUG] {key}: {val}", file=sys.stderr)

        # Vercel provides the original path in several places.
        # Try all known headers in order of reliability
        path = (environ.get('HTTP_X_VERCEL_ORIGINAL_URL') or
                environ.get('HTTP_X_VERCEL_PATH') or
                environ.get('REQUEST_URI') or
                environ.get('HTTP_X_FORWARDED_URI') or
                environ.get('ORIGINAL_URI') or
                environ.get('HTTP_X_ORIGINAL_URL') or
                environ.get('HTTP_X_REWRITE_URL') or
                environ.get('PATH_INFO'))

        if path:
            # 1. Strip query strings
            path = path.split('?')[0]

            # 2. If it's a full URL, extract the path
            if '://' in path:
                from urllib.parse import urlparse
                path = urlparse(path).path

            # 3. Vercel often prefixes the path with /api/index when rewriting.
            # We must remove this so Flask sees the route defined in app.py (e.g., /diagnose)
            if path.startswith('/api/index'):
                path = path[len('/api/index'):]

            # 4. Ensure it starts with / and isn't empty
            if not path or path == '':
                path = '/'
            elif not path.startswith('/'):
                path = '/' + path

            environ['PATH_INFO'] = path
            print(f"[VERCEL DEBUG] FINAL PATH_INFO: {path}", file=sys.stderr)

        # Final check: if Flask still sees /api/index, force it to root
        if environ.get('PATH_INFO') == '/api/index':
            environ['PATH_INFO'] = '/'

        print(f"[VERCEL DEBUG] === REQUEST END ===", file=sys.stderr)
        return self.wsgi_app(environ, start_response)

app.wsgi_app = VercelWSGIMiddleware(app.wsgi_app)
