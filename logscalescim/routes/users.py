from flask import Blueprint, jsonify, request, current_app
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError

# Define the blueprint for users
bp = Blueprint('users', __name__, url_prefix='/Users')

# Define GraphQL queries and mutations
GET_USERS_QUERY = gql("""
query {
    users {
        id
        username
        email
    }
}
""")

GET_USER_QUERY = gql("""
query getUser($id: ID!) {
    user(id: $id) {
        id
        username
        email
    }
}
""")

CREATE_USER_MUTATION = gql("""
mutation createUser($username: String!, $email: String!, $password: String!) {
    createUser(username: $username, email: $email, password: $password) {
        id
        username
        email
    }
}
""")

REPLACE_USER_MUTATION = gql("""
mutation replaceUser($id: ID!, $username: String!, $email: String!, $password: String!) {
    replaceUser(id: $id, username: $username, email: $email, password: $password) {
        id
        username
        email
    }
}
""")

UPDATE_USER_MUTATION = gql("""
mutation updateUser($id: ID!, $username: String, $email: String, $password: String) {
    updateUser(id: $id, username: $username, email: $email, password: $password) {
        id
        username
        email
    }
}
""")

DELETE_USER_MUTATION = gql("""
mutation deleteUser($id: ID!) {
    deleteUser(id: $id) {
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
def get_users():
    # Handle GET request to retrieve all users
    client = get_client()
    try:
        result = client.execute(GET_USERS_QUERY)
        return jsonify(result['users'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods=['GET'])
def get_user(id):
    # Handle GET request to retrieve a specific user by ID
    client = get_client()
    try:
        variables = {"id": id}
        result = client.execute(GET_USER_QUERY, variable_values=variables)
        return jsonify(result['user'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/', methods=['POST'])
def create_user():
    # Handle POST request to create a new user
    client = get_client()
    data = request.json
    try:
        variables = {
            "username": data['username'],
            "email": data['email'],
            "password": data['password']
        }
        result = client.execute(CREATE_USER_MUTATION, variable_values=variables)
        return jsonify(result['createUser']), 201
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods=['PUT'])
def replace_user(id):
    # Handle PUT request to replace a specific user by ID
    client = get_client()
    data = request.json
    try:
        variables = {
            "id": id,
            "username": data['username'],
            "email": data['email'],
            "password": data['password']
        }
        result = client.execute(REPLACE_USER_MUTATION, variable_values=variables)
        return jsonify(result['replaceUser'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods=['PATCH'])
def update_user(id):
    # Handle PATCH request to update a specific user by ID
    client = get_client()
    data = request.json
    try:
        variables = {
            "id": id,
            "username": data.get('username'),
            "email": data.get('email'),
            "password": data.get('password')
        }
        result = client.execute(UPDATE_USER_MUTATION, variable_values=variables)
        return jsonify(result['updateUser'])
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400

@bp.route('/<id>', methods=['DELETE'])
def delete_user(id):
    # Handle DELETE request to delete a specific user by ID
    client = get_client()
    try:
        variables = {"id": id}
        result = client.execute(DELETE_USER_MUTATION, variable_values=variables)
        return '', 204
    except TransportQueryError as e:
        return jsonify({"error": str(e)}), 400