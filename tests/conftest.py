import pytest
from unittest.mock import patch, MagicMock
from logscalescim import create_app
import os

@pytest.fixture
def app():
    os.environ['SCIM_TOKEN'] = 'test_scim_token'
    os.environ['LOGSCALE_API_TOKEN'] = 'test_logscale_api_token'
    os.environ['LOGSCALE_URL'] = 'https://logscale.weka2.ref.logsr.life/graphql'
    
    app = create_app()
    app.config.update({
        "TESTING": True,
    })
    yield app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def mock_graphql_client():
    with patch('logscalescim.routes.g.GraphQLClient') as MockGraphQLClient:
        mock_client = MockGraphQLClient.return_value
        yield mock_client