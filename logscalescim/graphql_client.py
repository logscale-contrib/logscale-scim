import logging
import time
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from gql.transport.exceptions import (
    TransportQueryError,
    TransportServerError,
    TransportProtocolError,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define GraphQL queries and mutations as constants
LOGSCALE_GQL_MUTATION_GROUP_ADD = gql(
    """mutation AddGroup($displayName: String!, $lookupName: String) {
  addGroup(displayName: $displayName, lookupName: $lookupName) {
    group {
      id
    }
  }
}"""
)

LOGSCALE_GQL_MUTATION_GROUP_UPDATE = gql(
    """
mutation UpdateGroup($input: UpdateGroupInput!) {
  updateGroup(input: $input) {
    group {
      id
      lookupName
    }
  }
}                                         
"""
)

LOGSCALE_GQL_MUTATION_GROUP_DELETE = gql(
    """mutation RemoveGroup($groupId: String!) {
  removeGroup(groupId: $groupId) {
    group {
      id
      lookupName
    }
  }
}"""
)

LOGSCALE_GQL_MUTATION_GROUP_ADD_USERS = gql(
    """mutation AddUsersToGroup($input: AddUsersToGroupInput!) {
  addUsersToGroup(input: $input) {
    group {
      id
      lookupName
    }
  }
}"""
)

LOGSCALE_GQL_MUTATION_GROUP_REMOVE_USERS = gql(
    """mutation RemoveUsersFromGroup($input: RemoveUsersFromGroupInput!) {
  removeUsersFromGroup(input: $input) {
    group {
      id
    }
  }
}"""
)


LOGSCALE_GQL_MUTATION_USER_UPDATE_BY_ID = gql(
    """mutation UpdateUserById($input: UpdateUserByIdInput!) {
  updateUserById(input: $input) {
    user {
      id
    }
  }
}"""
)

LOGSCALE_GQL_MUTATION_USER_ADD = gql(
    """mutation AddUserV2($input: AddUserInputV2!) {
  addUserV2(input: $input) {
    ... on User {
      id
    }
  }
}"""
)

LOGSCALE_GQL_MUTATION_USER_REMOVE = gql(
    """mutation RemoveUserById($input: RemoveUserByIdInput!) {
  removeUserById(input: $input) {
    user {
      id
    }
  }
}"""
)

LOGSCALE_GQL_QUERY_GROUP_BY_DISPLAY_NAME = gql(
    """
query GroupByDisplayName($displayName: String!) {
  groupByDisplayName(displayName: $displayName) {
    id
  }  
}
"""
)

LOGSCALE_GQL_QUERY_GROUP_BY_ID = gql(
    """
query Group($groupId: String!) {
  group(groupId: $groupId) {
    id
    lookupName
    displayName
    roles {
      role {
        displayName
        id
      }
    }
    organizationRoles {
      role {
        displayName
        id
      }
    }
    systemRoles {
      role {
        displayName
        id
      }
    }
    users {
      displayName
      email
      firstName
      fullName
      id
      lastName
      username
      createdAt
    }
    userCount
  }
}
"""
)

LOGSCALE_GQL_QUERY_USER_BY_KEY = gql(
    """query Users($search: String) {
  users(search: $search) {id,username, email, displayName}
}"""
)

LOGSCALE_GQL_QUERY_USERS = gql(
    """
query Users {
  users {
    username
    displayName
    fullName
    firstName
    lastName
    email
    company
    createdAt
    id
  }
}
"""
)
# Define the test query
TEST_QUERY = gql(
    """
query {
    __schema {
        queryType {
            name
        }
    }
}
"""
)


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
                logger.error(
                    "GraphQL query error.",
                    extra={"error": str(e), "query": query, "variables": variables},
                )
                raise
            except (TransportServerError, TransportProtocolError) as e:
                elapsed_time = time.time() - start_time
                if elapsed_time + self.retry_interval > self.max_retry_duration:
                    logger.error(
                        "GraphQL execution error after retries.",
                        extra={"error": str(e), "query": query, "variables": variables},
                    )
                    raise
                logger.warning(
                    "Retryable GraphQL execution error. Retrying...",
                    extra={
                        "error": str(e),
                        "query": query,
                        "variables": variables,
                        "retry_interval": self.retry_interval,
                    },
                )
                time.sleep(self.retry_interval)
            except Exception as e:
                logger.error(
                    "Unexpected error during GraphQL execution.",
                    extra={"error": str(e), "query": query, "variables": variables},
                )
                raise
