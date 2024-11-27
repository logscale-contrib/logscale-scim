from flask import Blueprint, g, request, jsonify, current_app


bp = Blueprint(
    "resource_types",
    __name__,
    url_prefix=f"{current_app.config['REQUEST_PATH_PREFIX']}/ResourceTypes",
)


@bp.route("", methods=["GET"])
def get_resource_types():
    # Implement the logic to retrieve the service provider configuration
    response = jsonify(
        {
            "schemas": ["urn:ietf:params:scim:api:messages:2.0:ListResponse"],
            "totalResults": 2,
            "itemsPerPage": 2,
            "startIndex": 1,
            "Resources": [
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                    "id": "User",
                    "name": "User",
                    "endpoint": "/Users",
                    "description": "https://tools.ietf.org/html/rfc7643#section-8.7.1",
                    "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
                    "schemaExtensions": [
                        {
                            "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                            "required": False,
                        }
                    ],
                    "meta": {
                        "location": f"{request.root_url.rstrip("/")}{current_app.config['REQUEST_PATH_PREFIX']}/ResourceTypes/User",
                        "resourceType": "ResourceType",
                    },
                },
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
                    "id": "Group",
                    "name": "Group",
                    "endpoint": "/Groups",
                    "description": "https://tools.ietf.org/html/rfc7643#section-8.7.1",
                    "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
                    "meta": {
                        "location": f"{request.root_url.rstrip("/")}{current_app.config['REQUEST_PATH_PREFIX']}/ResourceTypes/Group",
                        "resourceType": "ResourceType",
                    },
                },
            ],
        }
    )

    response.headers["Content-Type"] = "application/scim+json"
    response.status_code
    return response


@bp.route("/User", methods=["GET"])
def resource_types_user():
    # Implement the logic to retrieve the service provider configuration
    response = jsonify(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "User",
            "name": "User",
            "endpoint": "/Users",
            "description": "https://tools.ietf.org/html/rfc7643#section-8.7.1",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:User",
            "schemaExtensions": [
                {
                    "schema": "urn:ietf:params:scim:schemas:extension:enterprise:2.0:User",
                    "required": False,
                }
            ],
            "meta": {
                "location": f"{request.root_url.rstrip("/")}{current_app.config['REQUEST_PATH_PREFIX']}/ResourceTypes/User",
                "resourceType": "ResourceType",
            },
        }
    )

    response.headers["Content-Type"] = "application/scim+json"
    response.status_code
    return response


@bp.route("/Group", methods=["GET"])
def resource_types_group():
    # Implement the logic to retrieve the service provider configuration
    response = jsonify(
        {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ResourceType"],
            "id": "Group",
            "name": "Group",
            "endpoint": "/Groups",
            "description": "https://tools.ietf.org/html/rfc7643#section-8.7.1",
            "schema": "urn:ietf:params:scim:schemas:core:2.0:Group",
            "meta": {
                "location": f"{request.root_url.rstrip("/")}{current_app.config['REQUEST_PATH_PREFIX']}/ResourceTypes/Group",
                "resourceType": "ResourceType",
            },
        }
    )

    response.headers["Content-Type"] = "application/scim+json"
    response.status_code
    return response
