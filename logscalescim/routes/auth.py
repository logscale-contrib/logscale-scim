from functools import wraps
from flask import request, jsonify, current_app


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({"error": "Token is missing or invalid!"}), 401

        if token != current_app.config.get('SCIM_TOKEN'):
            return jsonify({"error": "Token is invalid!"}), 401

        return f(*args, **kwargs)
    return decorated
