import logging
import uuid
from flask import Blueprint, g, request, jsonify
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError
from .auth import token_required

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the blueprint for groups
bp = Blueprint('groups', __name__, url_prefix='/Groups')

# Define GraphQL queries and mutations
GET_GROUPS_QUERY = gql("""
query {
    groups {
        id
        displayName
        members {
            id
            username
        }
    }
}
""")

GET_GROUP_QUERY = """
query GetGroup($id: ID!) {
    group(id: $id) {
        id
        name
    }
}
"""

CREATE_GROUP_MUTATION = """
mutation CreateGroup($input: CreateGroupInput!) {
    createGroup(input: $input) {
        group {
            id
            name
        }
    }
}
"""

REPLACE_GROUP_MUTATION = """
mutation ReplaceGroup($id: ID!, $input: ReplaceGroupInput!) {
    replaceGroup(id: $id, input: $input) {
        group {
            id
            name
        }
    }
}
"""

UPDATE_GROUP_MUTATION = """
mutation UpdateGroup($id: ID!, $input: UpdateGroupInput!) {
    updateGroup(id: $id, input: $input) {
        group {
            id
            name
        }
    }
}
"""

DELETE_GROUP_MUTATION = gql("""
mutation deleteGroup($id: ID!) {
    deleteGroup(id: $id) {
        id
    }
}
""")

def get_client():
    # Create a GraphQL client using the configured endpoint
    transport = RequestsHTTPTransport(
        url=current_app.config['GRAPHQL_ENDPOINT'],
        use_json=True,
    )
    return Client(transport=transport, fetch_schema_from_transport=True)

@bp.route('/', methods=['GET'])
def get_groups():
    # Handle GET request to retrieve all groups
    client = get_client()
    try:
        result = client.execute(GET_GROUPS_QUERY)
        return jsonify(result['groups'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods=['GET'])
@token_required
def get_group(id):
    """
    Handle GET request to retrieve a specific group by ID.
    """
    try:
        variables = {"id": id}
        result = g.graphql_client.execute(GET_GROUP_QUERY, variables)
        logger.info(f"Retrieved group with ID {id}")
        return jsonify(result['group'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Error ID {error_id}: Error retrieving group with ID {id}: {e}")
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/', methods=['POST'])
@token_required
def create_group():
    """
    Handle POST request to create a new group.
    """
    data = request.json
    try:
        variables = {
            "input": {
                "name": data['name']
            }
        }
        result = g.graphql_client.execute(CREATE_GROUP_MUTATION, variables)
        logger.info(f"Created group with name {data['name']}")
        return jsonify(result['createGroup']['group']), 201
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Error ID {error_id}: Error creating group with name {data['name']}: {e}")
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['PUT'])
@token_required
def replace_group(id):
    """
    Handle PUT request to replace a specific group by ID.
    """
    data = request.json
    try:
        variables = {
            "id": id,
            "input": {
                "name": data['displayName']
            }
        }
        result = g.graphql_client.execute(REPLACE_GROUP_MUTATION, variables)
        logger.info(f"Replaced group with ID {id}")
        return jsonify(result['replaceGroup']['group'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Error ID {error_id}: Error replacing group with ID {id}: {e}")
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['PATCH'])
@token_required
def update_group(id):
    """
    Handle PATCH request to update a specific group by ID.
    """
    data = request.json
    try:
        variables = {
            "id": id,
            "input": {
                "name": data.get('displayName')
            }
        }
        result = g.graphql_client.execute(UPDATE_GROUP_MUTATION, variables)
        logger.info(f"Updated group with ID {id}")
        return jsonify(result['updateGroup']['group'])
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Error ID {error_id}: Error updating group with ID {id}: {e}")
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400

@bp.route('/<id>', methods=['DELETE'])
@token_required
def delete_group(id):
    """
    Handle DELETE request to delete a specific group by ID.
    """
    client = get_client()
    try:
        variables = {"id": id}
        result = client.execute(DELETE_GROUP_MUTATION, variable_values=variables)
        logger.info(f"Deleted group with ID {id}")
        return '', 204
    except TransportQueryError as e:
        error_id = str(uuid.uuid4())
        logger.error(f"Error ID {error_id}: Error deleting group with ID {id}: {e}")
        return jsonify({"error": f"An error occurred. Please contact support with error ID {error_id}"}), 400