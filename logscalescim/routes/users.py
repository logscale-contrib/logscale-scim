import datetime
import logging
from flask import Blueprint, g, make_response, request, jsonify, current_app
from gql.transport.exceptions import TransportQueryError
from .auth import token_required
from ..graphql_client import (
    LOGSCALE_GQL_MUTATION_USER_ADD,
    LOGSCALE_GQL_QUERY_USER_BY_KEY,
    LOGSCALE_GQL_MUTATION_USER_UPDATE_BY_ID,
    LOGSCALE_GQL_QUERY_USERS,
)
from ..utils import handle_graphql_error
from ..response_utils import ResponseUtils


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the blueprint for users
bp = Blueprint(
    "Users", __name__, url_prefix=f"{current_app.config['REQUEST_PATH_PREFIX']}/Users"
)


@bp.route("", methods=["GET"])
@token_required
def get_users():
    """
    Handle GET request to retrieve a specific user by ID.
    """
    try:

        result = current_app.graphql_client.execute(LOGSCALE_GQL_QUERY_USERS)
        users = []
        for user in result["users"]:
            users.append(
                {
                    "id": user["id"],
                    "userName": user["username"],
                    "email": user["email"],
                    "displayName": user["fullName"],
                    "firstName": user["firstName"],
                    "lastName": user["lastName"],
                    "full_name": user["fullName"],
                    "meta": {
                        "location": f"{request.root_url.rstrip('/')}{current_app.config['REQUEST_PATH_PREFIX']}/Users/{user['id']}",
                        "resourceType": "User",
                        "created": "2024-10-06T00:00Z",
                        "lastModified": "2024-10-06T00:00Z",
                    },
                }
            )
        # for result in result:

        return ResponseUtils.generate_users_response(200, users)
    except TransportQueryError as e:
        return handle_graphql_error(e, entity_id=id, entity_type="user")


@bp.route('/<id>', methods=['GET'])
@token_required
def get_user(id):
    """
    Handle GET request to retrieve a specific user by ID.
    """
    try:
        variables = {"id": id}
        result = g.graphql_client.execute(GET_USER_QUERY, variables)
        logger.info("Retrieved user.", extra={"user_id": id})
        return jsonify(result['user'])
    except TransportQueryError as e:
        return handle_graphql_error(e, entity_id=id, entity_type="user")


@bp.route("", methods=["POST"])
@token_required
def create_user():
    """
    Handle POST request to create a new user.
    """

    data = request.json
    # Expected value of data is
    # {'userName': 'akadmin', 'id': '5gmZOlekCgZFDDdKcCuvMZ6b', 'name': {'formatted': 'authentik Default Admin', 'familyName': 'Default Admin', 'givenName': 'authentik'}, 'displayName': 'authentik Default Admin', 'active': True, 'emails': [{'value': 'user@example.com', 'type': 'other', 'primary': True}], 'schemas': ['urn:ietf:params:scim:schemas:core:2.0:User'], 'externalId': 'e89f4b0dcc531b703369420fbe0d6504b8f5c8a5fc419527358d07308a47b3c7'}
    try:

        primary_email = next(
            (email["value"] for email in data["emails"] if email.get("primary")), None
        )
        if not primary_email:
            return jsonify({"error": "Primary email is required"}), 400

        # Check if the user already exists
        #
        variables = {"search": primary_email}
        existingId = None
        result = current_app.graphql_client.execute(
            LOGSCALE_GQL_QUERY_USER_BY_KEY, variables
        )

        for user in result["users"]:
            if user["email"] == primary_email:
                existingId = user["id"]

        if not existingId:
            variables = {"search": data["userName"]}

            result = current_app.graphql_client.execute(
                LOGSCALE_GQL_QUERY_USER_BY_KEY, variables
            )

            for user in result["users"]:
                if user["username"] == data["userName"]:
                    existingId = user["id"]
        id = None
        if existingId:
            logger.warning(
                "User already exists.",
                extra={
                    "username": data["userName"],
                    "email": primary_email,
                    "externalId": data["externalId"],
                    "logscaleId": existingId,
                },
            )
            variables = {
                "input": {
                    "userId": existingId,
                    "fullName": data["name"]["formatted"],
                    "email": primary_email,
                }
            }
            if "familyName" in data["name"]:
                variables["input"]["lastName"] = data["name"]["familyName"]
            if "givenName" in data["name"]:
                variables["input"]["firstName"] = data["name"]["givenName"]

            result = current_app.graphql_client.execute(
                LOGSCALE_GQL_MUTATION_USER_UPDATE_BY_ID, variables
            )
            logger.info(
                "Updated User.",
                extra={"username": data["userName"], "existingId": existingId},
            )
            id = existingId
        else:
            variables = {
                "input": {
                    "fullName": data["name"]["formatted"],
                    "username": data["userName"],
                    "email": primary_email,
                }
            }
            if "familyName" in data["name"]:
                variables["input"]["lastName"] = data["name"]["familyName"]
            if "givenName" in data["name"]:
                variables["input"]["firstName"] = data["name"]["givenName"]

            result = current_app.graphql_client.execute(
                LOGSCALE_GQL_MUTATION_USER_ADD, variables
            )
            logger.info("Created user.", extra={"username": data["userName"]})
            id = result["addUserV2"]["id"]
        ts = datetime.datetime.now(datetime.timezone.utc)
        return ResponseUtils.generate_user_response(
            201, id, data["userName"], primary_email, data["name"]["formatted"]
        )

    except TransportQueryError as e:
        return handle_graphql_error(e, entity_id=None, entity_type="user")


@bp.route("/<id>", methods=["PUT"])
@token_required
def replace_user(id):
    """
    Handle PUT request to replace a specific user by ID.
    """
    data = request.json
    try:
        primary_email = next(
            (email["value"] for email in data["emails"] if email.get("primary")), None
        )
        if not primary_email:
            return jsonify({"error": "Primary email is required"}), 400

        variables = {
            "input": {
                "userId": id,
                "fullName": data["name"]["formatted"],
                "email": primary_email,
            }
        }
        if "familyName" in data["name"]:
            variables["input"]["lastName"] = data["name"]["familyName"]
        if "givenName" in data["name"]:
            variables["input"]["firstName"] = data["name"]["givenName"]

        result = current_app.graphql_client.execute(
            LOGSCALE_GQL_MUTATION_USER_UPDATE_BY_ID, variables
        )
        logger.info(
            "Updated User.", extra={"username": data["userName"], "existingId": id}
        )
    except TransportQueryError as e:
        return handle_graphql_error(e, entity_id=id, entity_type="user")

    ts = datetime.datetime.now(datetime.timezone.utc)
    return make_response(
        jsonify(
            {
                "schemas": ["urn:ietf:params:scim:schemas:core:2.0:User"],
                "id": id,
                "externalId": data["externalId"],
                "meta": {
                    "location": f"{request.base_url}/Users/{id}",
                    "resourceType": "User",
                    "created": f"{ts.isoformat()}",
                    "lastModified": f"{ts.isoformat()}",
                },
            }
        ),
        201,
    )


# @bp.route('/<id>', methods=['PATCH'])
# @token_required
# def update_user(id):
#     """
#     Handle PATCH request to update a specific user by ID.
#     """
#     data = request.json
#     try:
#         variables = {
#             "id": id,
#             "input": {
#                 "username": data.get('username'),
#                 "email": data.get('email'),
#                 "password": data.get('password')
#             }
#         }
#         result = g.graphql_client.execute(UPDATE_USER_MUTATION, variables)
#         logger.info("Updated user.", extra={"user_id": id})
#         return jsonify(result['updateUser']['user'])
#     except TransportQueryError as e:
#         return handle_graphql_error(e, entity_id=id, entity_type="user")

# @bp.route('/<id>', methods=['DELETE'])
# @token_required
# def delete_user(id):
#     """
#     Handle DELETE request to delete a specific user by ID.
#     """
#     try:
#         variables = {"id": id}
#         result = g.graphql_client.execute(DELETE_USER_MUTATION, variables)
#         logger.info("Deleted user.", extra={"user_id": id})
#         return '', 204
#     except TransportQueryError as e:
#         return handle_graphql_error(e, entity_id=id, entity_type="user")
