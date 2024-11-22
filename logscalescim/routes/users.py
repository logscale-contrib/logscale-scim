import logging
import uuid
from flask import Blueprint, g, request, jsonify
from gql.transport.exceptions import TransportQueryError
from .auth import token_required

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the blueprint for users
bp = Blueprint('users', __name__, url_prefix='/Users')

# Define GraphQL queries and mutations
GET_USERS_QUERY = """
query {
    users {
        id
        username
        email
    }
}
"""

GET_USER_QUERY = """
query getUser($id: ID!) {
    user(id: $id) {
        id
        username
        email
    }
}
"""

CREATE_USER_MUTATION = """
mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
        user {
            id
            username
            email
        }
    }
}
"""

REPLACE_USER_MUTATION = """
mutation ReplaceUser($id: ID!, $input: ReplaceUserInput!) {
    replaceUser(id: $id, input: $input) {
        user {
            id
            username
            email
        }
    }
}
"""

UPDATE_USER_MUTATION = """
mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
    updateUser(id: $id, input: $input) {
        user {
            id
            username
            email
        }
    }
}
"""

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