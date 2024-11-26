import logging
from flask import Blueprint, g, make_response, request, jsonify, current_app
from gql.transport.exceptions import TransportQueryError
from .auth import token_required
from ..graphql_client import LOGSCALE_GQL_MUTATION_GROUP_ADD, LOGSCALE_GQL_MUTATION_GROUP_UPDATE, LOGSCALE_GQL_QUERY_GROUP_BY_DISPLAY_NAME, LOGSCALE_GQL_MUTATION_GROUP_ADD_USERS, LOGSCALE_GQL_MUTATION_GROUP_REMOVE_USERS, LOGSCALE_GQL_QUERY_GROUP_BY_ID
from ..utils import handle_graphql_error

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the blueprint for groups
bp = Blueprint('Groups', __name__,
               url_prefix=f'{current_app.config['REQUEST_PATH_PREFIX']}/Groups')

# @bp.route('', methods=['GET'])
# @token_required
# def get_groups():
#     # Handle GET request to retrieve all groups
#     try:
#         variables = {
#             "input": {
#                 "groupId": id,
#             }
#         }
#         result = current_app.graphql_client.execute(
#                 LOGSCALE_GQL_QUERY_GROUP_BY_ID, variables)
#         logging.debug(result)

#         result = g.graphql_client.execute(GET_GROUPS_QUERY)
#         logger.info("Retrieved all groups.")
#         return jsonify(result['groups'])
#     except TransportQueryError as e:
#         return handle_graphql_error(e, entity_type="group")


@bp.route('/<id>', methods=['GET'])
@token_required
def get_group(id):
    # Handle GET request to retrieve a specific group by ID
    try:
        variables = {"groupId": id}
        result = current_app.graphql_client.execute(
            LOGSCALE_GQL_QUERY_GROUP_BY_ID, variables)
        logger.debug("Retrieved group.", extra={
                     "group_id": id, "result": result})
        return make_response(
            jsonify(
                {
                    "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                    "id": result["updateGroup"]["group"]["id"],
                    "externalId": result["externalId"],
                    "meta": {
                        "location": f"{id}",
                        "resourceType": "Group",
                        "created": "2024-10-06T00:00Z",
                        "lastModified": "2024-10-06T00:00Z",
                    },
                }
            ),
            200,
        )
    except TransportQueryError as e:
        return handle_graphql_error(e, entity_id=id, entity_type="group")


@bp.route('', methods=['POST'])
@token_required
def create_group():
    # Handle POST request to create a new group
    data = request.json
    try:
        variables = {
            "displayName": data["displayName"],
        }

        result = current_app.graphql_client.execute(
            LOGSCALE_GQL_QUERY_GROUP_BY_DISPLAY_NAME, variables)

        id = None
        existingId = None
        if ('groupByDisplayName' in result.keys() and 'id' in result['groupByDisplayName'].keys()):
            existingId = result["groupByDisplayName"]["id"]

            variables = {
                "input": {
                    "groupId": existingId,
                    "displayName": data["displayName"],
                    "lookupName": data["externalId"],
                }
            }

            result = current_app.graphql_client.execute(
                LOGSCALE_GQL_MUTATION_GROUP_UPDATE, variables)
            logger.info("Updated group.", extra={
                        "group_name": data['displayName']})
            id = existingId
            return make_response(
                jsonify(
                    {
                        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                        "id": id,
                        "externalId": data["externalId"],
                        "meta": {
                            "location": f"{request.base_url}/Groups/{id}",
                            "resourceType": "Group",
                            "created": "2024-10-06T00:00Z",
                            "lastModified": "2024-10-06T00:00Z",
                        },
                    }
                ),
                201,
            )
        else:
            variables = {
                "displayName": data["displayName"],
                "lookupName": data["externalId"],
            }
            result = current_app.graphql_client.execute(
                LOGSCALE_GQL_MUTATION_GROUP_ADD, variables)
            logger.info("Created group.", extra={
                        "group_name": data['displayName']})
            id = result["addGroup"]["group"]["id"]
            return make_response(
                jsonify(
                    {
                        "schemas": ["urn:ietf:params:scim:schemas:core:2.0:Group"],
                        "id": id,
                        "externalId": data["externalId"],
                        "meta": {
                            "location": f"{request.base_url}/Groups/{id}",
                            "resourceType": "Group",
                            "created": "2024-10-06T00:00Z",
                            "lastModified": "2024-10-06T00:00Z",
                        },
                    }
                ),
                201,
            )
    except TransportQueryError as e:
        return handle_graphql_error(e, entity_type="group")

# @bp.route('/<id>', methods=['PUT'])
# @token_required
# def replace_group(id):
#     # Handle PUT request to replace a specific group by ID
#     data = request.json
#     try:
#         variables = {
#             "id": id,
#             "input": {
#                 "displayName": data['displayName']
#             }
#         }
#         result = g.graphql_client.execute(REPLACE_GROUP_MUTATION, variables)
#         logger.info("Replaced group.", extra={"group_id": id})
#         return jsonify(result['replaceGroup']['group'])
#     except TransportQueryError as e:
#         return handle_graphql_error(e, entity_id=id, entity_type="group")


@bp.route('/<id>', methods=['PATCH'])
@token_required
def update_group(id):
    # Handle PATCH request to update a specific group by ID
    data = request.json
    """
    {'Operations': [{...}], 'schemas': ['urn:ietf:params:scim:api:messages:2.0:PatchOp']}
    [{'op': 'replace', 'path': 'displayName', 'value': 'weka2-logscale-usersx'}]
    {'op': 'add', 'path': 'members', 'value': [{'value': 'b0PWHGSfJGY97Cjd37eQ81nv'}]}
    """

    """
    {"Operations": [
        {"op": "add", "path": "members", "value": [{"value": "b0PWHGSfJGY97Cjd37eQ81nv"}]}, {"op": "add", "path": "members", "value": [{"value": "BTckjpsawMXSMJZf0PbQUQMJ"}]}], "schemas": ["urn:ietf:params:scim:api:messages:2.0:PatchOp"]}
    """

    # for operation in userdata['Operations']
    query = None
    for operation in data["Operations"]:
        variables = {
            "input": {
                "groupId": id,
            }
        }
        if operation["op"] == "replace":
            resultkey = "updateGroup"
            query = LOGSCALE_GQL_MUTATION_GROUP_UPDATE
            if "displayName" in operation["value"]:
                variables["input"]["displayName"] = operation["value"]["displayName"]

            if "externalId" in operation["value"]:
                variables["input"]["lookupName"] = operation["value"]["externalId"]
        elif operation["op"] == "add" and operation["path"] == "members":
            resultkey = "addUsersToGroup"
            query = LOGSCALE_GQL_MUTATION_GROUP_ADD_USERS
            variables["input"]["groupId"] = id
            variables["input"]["users"] = []
            for value in operation["value"]:
                variables["input"]["users"].append(value["value"])
        elif operation["op"] == "remove" and operation["path"] == "members":
            resultkey = "addUsersToGroup"
            query = LOGSCALE_GQL_MUTATION_GROUP_REMOVE_USERS
            variables["input"]["groupId"] = id
            variables["input"]["users"] = []
            for value in operation["value"]:
                variables["input"]["users"].append(value["value"])
        else:
            continue

        try:
            result = current_app.graphql_client.execute(
                query, variables)
            logging.debug(result)

        except TransportQueryError:
            logging.exception("TransportQueryError")
            return "", 500

    return "", 204

# @bp.route('/<id>', methods=['DELETE'])
# @token_required
# def delete_group(id):
#     # Handle DELETE request to delete a specific group by ID
#     try:
#         variables = {"id": id}
#         result = g.graphql_client.execute(DELETE_GROUP_MUTATION, variables)
#         logger.info("Deleted group.", extra={"group_id": id})
#         return '', 204
#     except TransportQueryError as e:
#         return handle_graphql_error(e, entity_id=id, entity_type="group")
