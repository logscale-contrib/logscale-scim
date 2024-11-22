from flask import Blueprint, jsonify

bp = Blueprint('schemas', __name__)

@bp.route('/Schemas', methods=['GET'])
def get_schemas():
    # Implement the logic to retrieve all schemas
    return jsonify([
        {
            "id": "urn:ietf:params:scim:schemas:core:2.0:User",
            "name": "User",
            "description": "User Account",
            "attributes": [
                # Define user schema attributes here
            ]
        },
        {
            "id": "urn:ietf:params:scim:schemas:core:2.0:Group",
            "name": "Group",
            "description": "Group",
            "attributes": [
                # Define group schema attributes here
            ]
        }
    ])