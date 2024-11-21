import os

class Config:
    # Configuration class for the Flask application
    SCIM_TOKEN = os.getenv("SCIM_TOKEN", "default_token")
    GRAPHQL_ENDPOINT = os.getenv("GRAPHQL_ENDPOINT", "https://your-graphql-endpoint.com/graphql")
    # Add other configuration variables here