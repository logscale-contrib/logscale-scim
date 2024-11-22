import logging
import time
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import TransportQueryError, TransportServerError, TransportProtocolError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define GraphQL queries and mutations as constants
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
mutation CreateUser($input: CreateUserInput!) {
    createUser(input: $input) {
        user {
            id
            username
            email
        }
    }
}
""")

REPLACE_USER_MUTATION = gql("""
mutation ReplaceUser($id: ID!, $input: ReplaceUserInput!) {
    replaceUser(id: $id, input: $input) {
        user {
            id
            username
            email
        }
    }
}
""")

UPDATE_USER_MUTATION = gql("""
mutation UpdateUser($id: ID!, $input: UpdateUserInput!) {
    updateUser(id: $id, input: $input) {
        user {
            id
            username
            email
        }
    }
}
""")

DELETE_USER_MUTATION = gql("""
mutation DeleteUser($id: ID!) {
    deleteUser(id: $id) {
        id
    }
}
""")

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
query GetGroup($id: ID!) {
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
mutation CreateGroup($input: CreateGroupInput!) {
    createGroup(input: $input) {
        group {
            id
            displayName
        }
    }
}
""")

REPLACE_GROUP_MUTATION = gql("""
mutation ReplaceGroup($id: ID!, $input: ReplaceGroupInput!) {
    replaceGroup(id: $id, input: $input) {
        group {
            id
            displayName
        }
    }
}
""")

UPDATE_GROUP_MUTATION = gql("""
mutation UpdateGroup($id: ID!, $input: UpdateGroupInput!) {
    updateGroup(id: $id, input: $input) {
        group {
            id
            displayName
        }
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

# Define the test query
TEST_QUERY = gql("""
query {
    __schema {
        queryType {
            name
        }
    }
}
""")

class GraphQLClient:
    def __init__(self, endpoint, headers=None, retry_interval=1, max_retry_duration=15):
        transport = RequestsHTTPTransport(
            url=endpoint,
            headers=headers,
            use_json=True,
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        self.retry_interval = retry_interval
        self.max_retry_duration = max_retry_duration

    def execute(self, query, variables=None):
        start_time = time.time()
        while True:
            try:
                return self.client.execute(query, variable_values=variables)
            except TransportQueryError as e:
                logger.error("GraphQL query error.", extra={"error": str(e), "query": query, "variables": variables})
                raise
            except (TransportServerError, TransportProtocolError) as e:
                elapsed_time = time.time() - start_time
                if elapsed_time + self.retry_interval > self.max_retry_duration:
                    logger.error("GraphQL execution error after retries.", extra={"error": str(e), "query": query, "variables": variables})
                    raise
                logger.warning("Retryable GraphQL execution error. Retrying...", extra={"error": str(e), "query": query, "variables": variables, "retry_interval": self.retry_interval})
                time.sleep(self.retry_interval)
            except Exception as e:
                logger.error("Unexpected error during GraphQL execution.", extra={"error": str(e), "query": query, "variables": variables})
                raise
