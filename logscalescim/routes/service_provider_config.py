from flask import Blueprint, g, request, jsonify, current_app


bp = Blueprint('service_provider_config', __name__, url_prefix=f"{current_app.config['REQUEST_PATH_PREFIX']}/service_provider_config")

@bp.route('/ServiceProviderConfig', methods=['GET'])
def get_service_provider_config():
    # Implement the logic to retrieve the service provider configuration
    return jsonify({
        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ServiceProviderConfig"],
        "patch": {
            "supported": True
        },
        "bulk": {
            "supported": False,
            "maxOperations": 0,
            "maxPayloadSize": 0
        },
        "filter": {
            "supported": True,
            "maxResults": 200
        },
        "changePassword": {
            "supported": False
        },
        "sort": {
            "supported": False
        },
        "etag": {
            "supported": False
        },
        "authenticationSchemes": [
            {
                "name": "OAuth Bearer Token",
                "description": "Authentication scheme using the OAuth Bearer Token Standard",
                "specUri": "http://www.rfc-editor.org/info/rfc6750",
                "type": "oauthbearertoken",
                "primary": True
            }
        ]
    })