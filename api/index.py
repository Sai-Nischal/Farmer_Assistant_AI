import os
import sys

# Add project root directory to sys.path so app, agents, services, and models are importable
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from app import app

# The path fix is now handled in app.py via @app.before_request
# This is more reliable than WSGI middleware for Vercel

# Simple test endpoint to verify routing works
from flask import jsonify, request

@app.route('/api/test-path')
def test_path():
    return jsonify({
        "path_info": request.environ.get('PATH_INFO'),
        "request_uri": request.environ.get('REQUEST_URI'),
        "vercel_original": request.environ.get('HTTP_X_VERCEL_ORIGINAL_URL'),
        "vercel_path": request.environ.get('HTTP_X_VERCEL_PATH'),
    })
