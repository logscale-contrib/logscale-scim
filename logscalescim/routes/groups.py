from flask import Blueprint, jsonify, request, current_app
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError

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

GET_GROUP_QUERY = gql("""
query getGroup($id: ID!) {
    group(id: $id) {
        id
        displayName
        members {
            id
            username
        }
    }
}
""")

CREATE_GROUP_MUTATION = gql("""
mutation createGroup($displayName: String!) {
    createGroup(displayName: $displayName) {
        id
        displayName
    }
}
""")

REPLACE_GROUP_MUTATION = gql("""
mutation replaceGroup($id: ID!, $displayName: String!) {
    replaceGroup(id: $id, displayName: $displayName) {
        id
        displayName
    }
}
""")

UPDATE_GROUP_MUTATION = gql("""
mutation updateGroup($id: ID!, $displayName: String) {
    updateGroup(id: $id, displayName: $displayName) {
        id
        displayName
    }
}
""")

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
def get_group(id):
    # Handle GET request to retrieve a specific group by ID
    client = get_client()
    try:
        variables = {"id": id}
        result = client.execute(GET_GROUP_QUERY, variable_values=variables)
        return jsonify(result['group'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/', methods=['POST'])
def create_group():
    # Handle POST request to create a new group
    client = get_client()
    data = request.json
    try:
        variables = {
            "displayName": data['displayName']
        }
        result = client.execute(CREATE_GROUP_MUTATION, variable_values=variables)
        return jsonify(result['createGroup']), 201
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods=['PUT'])
def replace_group(id):
    # Handle PUT request to replace a specific group by ID
    client = get_client()
    data = request.json
    try:
        variables = {
            "id": id,
            "displayName": data['displayName']
        }
        result = client.execute(REPLACE_GROUP_MUTATION, variable_values=variables)
        return jsonify(result['replaceGroup'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods=['PATCH'])
def update_group(id):
    # Handle PATCH request to update a specific group by ID
    client = get_client()
    data = request.json
    try:
        variables = {
            "id": id,
            "displayName": data.get('displayName')
        }
        result = client.execute(UPDATE_GROUP_MUTATION, variable_values=variables)
        return jsonify(result['updateGroup'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods['DELETE'])
def delete_group(id):
    # Handle DELETE request to delete a specific group by ID
    client = get_client()
    try:
        variables = {"id": id}
        result = client.execute(DELETE_GROUP_MUTATION, variable_values=variables)
        return '', 204
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400