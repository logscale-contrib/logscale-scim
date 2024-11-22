import logging
import uuid
from flask import Blueprint, g, request, jsonify, current_app
from gql.transport.exceptions import TransportQueryError
from .auth import token_required
from ..graphql_client import GET_USERS_QUERY, GET_USER_QUERY, CREATE_USER_MUTATION, REPLACE_USER_MUTATION, UPDATE_USER_MUTATION, DELETE_USER_MUTATION

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the blueprint for users
bp = Blueprint('users', __name__, url_prefix=f"{current_app.config['REQUEST_PATH_PREFIX']}/Users")

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
        error_id = str(uuid.uuid4())
        logger.error("Error retrieving user.", extra={"error_id": error_id, "user_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/', methods=['POST'])
@token_required
def create_user():
    """
    Handle POST request to create a new user.
    """
    data = request.json
    try:
        variables = {
            "input": {
                "username": data['username'],
                "email": data['email'],
                "password": data['password']
            }
        }
        result = g.graphql_client.execute(CREATE_USER_MUTATION, variables)
        logger.info("Created user.", extra={"username": data['username']})
        return jsonify(result['createUser']['user']), 201
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error creating user.", extra={"error_id": error_id, "username": data['username'], "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['PUT'])
@token_required
def replace_user(id):
    """
    Handle PUT request to replace a specific user by ID.
    """
    data = request.json
    try:
        variables = {
            "id": id,
            "input": {
                "username": data['username'],
                "email": data['email'],
                "password": data['password']
            }
        }
        result = g.graphql_client.execute(REPLACE_USER_MUTATION, variables)
        logger.info("Replaced user.", extra={"user_id": id})
        return jsonify(result['replaceUser']['user'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error replacing user.", extra={"error_id": error_id, "user_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['PATCH'])
@token_required
def update_user(id):
    """
    Handle PATCH request to update a specific user by ID.
    """
    data = request.json
    try:
        variables = {
            "id": id,
            "input": {
                "username": data.get('username'),
                "email": data.get('email'),
                "password": data.get('password')
            }
        }
        result = g.graphql_client.execute(UPDATE_USER_MUTATION, variables)
        logger.info("Updated user.", extra={"user_id": id})
        return jsonify(result['updateUser']['user'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error updating user.", extra={"error_id": error_id, "user_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_user(id):
    """
    Handle DELETE request to delete a specific user by ID.
    """
    try:
        variables = {"id": id}
        result = g.graphql_client.execute(DELETE_USER_MUTATION, variables)
        logger.info("Deleted user.", extra={"user_id": id})
        return '', 204
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error("Error deleting user.", extra={"error_id": error_id, "user_id": id, "error": str(e)})
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400