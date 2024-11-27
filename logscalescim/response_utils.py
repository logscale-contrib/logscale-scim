from flask import current_app, jsonify, request, Response

MIME_TYPE = "application/scim+json"


class ResponseUtils:
    @staticmethod
    def generate_group_response(status: int, id: str, externalId: str, displayName: str) -> Response:
        response_data = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
            "id": id,
            "externalId": externalId,
            "displayName": displayName,
            "meta": {
                "location": f"{request.root_url.rstrip("/")}{current_app.config['REQUEST_PATH_PREFIX']}/Groups/{id}",
                "resourceType": "Group",
                "created": "2024-10-06T00:00Z",
                "lastModified": "2024-10-06T00:00Z",
            },
        }

        response = jsonify(response_data)
        response.headers["Content-Type"] = MIME_TYPE
        response.status_code = status
        return response

    @staticmethod
    def generate_user_response(status, id, username, email, displayName):
        response = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
            "id": id,
            "userName": username,
            "email": email,
            "displayName": displayName,
            "meta": {
                "location": f"{request.root_url.rstrip('/')}{current_app.config['REQUEST_PATH_PREFIX']}/Users/{id}",
                "resourceType": "User",
                "created": "2024-10-06T00:00Z",
                "lastModified": "2024-10-06T00:00Z",
            },
        }

        response = jsonify(response)
        response.headers["Content-Type"] = MIME_TYPE
        response.status_code = status
        return response

    @staticmethod
    def generate_users_response(status, users):
        response = {
            "schemas": ["urn:ietf:params:scim:schemas:core:2.0:ListResponse"],
            "totalResults": len(users),
            "Resources": users,
        }
        response = jsonify(response)
        response.headers["Content-Type"] = MIME_TYPE
        response.status_code = status
        return response
