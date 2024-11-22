import logging
import uuid
from flask import Blueprint, g, request, jsonify, current_app
from gql.transport.exceptions import TransportQueryError
from .auth import token_required
from ..graphql_client import GET_GROUPS_QUERY, GET_GROUP_QUERY, CREATE_GROUP_MUTATION, REPLACE_GROUP_MUTATION, UPDATE_GROUP_MUTATION, DELETE_GROUP_MUTATION

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the blueprint for groups
bp = Blueprint('groups', __name__, url_prefix=f"{current_app.config['REQUEST_PATH_PREFIX']}/groups")

@bp.route('/', methods=['GET'])
@token_required
def get_groups():
    # Handle GET request to retrieve all groups
    try:
        result = g.graphql_client.execute(GET_GROUPS_QUERY)
        logger.info("Retrieved all groups.")
        return jsonify(result['groups'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error retrieving groups.", extra={"error_id": error_id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['GET'])
@token_required
def get_group(id):
    # Handle GET request to retrieve a specific group by ID
    try:
        variables = {"id": id}
        result = g.graphql_client.execute(GET_GROUP_QUERY, variables)
        logger.info("Retrieved group.", extra={"group_id": id})
        return jsonify(result['group'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error retrieving group.", extra={"error_id": error_id, "group_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/', methods=['POST'])
@token_required
def create_group():
    # Handle POST request to create a new group
    data = request.json
    try:
        variables = {
            "input": {
                "displayName": data['displayName']
            }
        }
        result = g.graphql_client.execute(CREATE_GROUP_MUTATION, variables)
        logger.info("Created group.", extra={"group_name": data['displayName']})
        return jsonify(result['createGroup']['group']), 201
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error creating group.", extra={"error_id": error_id, "group_name": data['displayName'], "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['PUT'])
@token_required
def replace_group(id):
    # Handle PUT request to replace a specific group by ID
    data = request.json
    try:
        variables = {
            "id": id,
            "input": {
                "displayName": data['displayName']
            }
        }
        result = g.graphql_client.execute(REPLACE_GROUP_MUTATION, variables)
        logger.info("Replaced group.", extra={"group_id": id})
        return jsonify(result['replaceGroup']['group'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error replacing group.", extra={"error_id": error_id, "group_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['PATCH'])
@token_required
def update_group(id):
    # Handle PATCH request to update a specific group by ID
    data = request.json
    try:
        variables = {
            "id": id,
            "input": {
                "displayName": data.get('displayName')
            }
        }
        result = g.graphql_client.execute(UPDATE_GROUP_MUTATION, variables)
        logger.info("Updated group.", extra={"group_id": id})
        return jsonify(result['updateGroup']['group'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error updating group.", extra={"error_id": error_id, "group_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_group(id):
    # Handle DELETE request to delete a specific group by ID
    try:
        variables = {"id": id}
        result = g.graphql_client.execute(DELETE_GROUP_MUTATION, variables)
        logger.info("Deleted group.", extra={"group_id": id})
        return '', 204
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error deleting group.", extra={"error_id": error_id, "group_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400