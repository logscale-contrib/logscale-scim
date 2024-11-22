from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport

class GraphQLClient:
    def __init__(self, endpoint, headers=None):
        transport = RequestsHTTPTransport(
            url=endpoint,
            headers=headers,
            use_json=True,
        )
        self.client = Client(transport=transport, fetch_schema_from_transport=True)

    def execute(self, query, variables=None):
        return self.client.execute(gql(query), variable_values=variables)