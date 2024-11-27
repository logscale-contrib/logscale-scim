import uuid
from flask import Flask, g, jsonify
import gql
from .config import Config
from .graphql_client import GraphQLClient, TEST_QUERY
from opentelemetry.instrumentation.flask import FlaskInstrumentor
import logging
from gql.transport.exceptions import TransportServerError, TransportProtocolError
from werkzeug.middleware.proxy_fix import ProxyFix

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Capture werkzeug logs
werkzeug_logger = logging.getLogger("werkzeug")
werkzeug_logger.setLevel(logging.INFO)


def create_app():
    # Create a new Flask application instance
    app = Flask(__name__)

    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_for=1, x_host=1)

    # Load configuration from the Config class in logscalescim.config module
    app.config.from_object(Config)

    # Instrument Flask with OpenTelemetry
    FlaskInstrumentor().instrument_app(app)

    try:
        app.graphql_client = GraphQLClient(
            endpoint=app.config["LOGSCALE_URL"],
            headers={"Authorization": f"Bearer {app.config['LOGSCALE_API_TOKEN']}"},
        )
        # Verify the connection to the GraphQL endpoint
        app.graphql_client.execute(TEST_QUERY)
        logger.info(
            "Successfully connected to the GraphQL endpoint.",
            extra={"endpoint": app.config["LOGSCALE_URL"]},
        )
    except gql.transport.exceptions.TransportError as e:
        logger.exception(
            "Error initializing GraphQL client or verifying connection.",
            extra={"error": str(e)},
        )
        raise

    # Use the application context to register blueprints
    with app.app_context():
        # Initialize the GraphQL client and store it in the application context

        # Import and register the blueprints for different routes
        from .routes import (
            users,
            groups,
            resource_types,
            service_provider_config,
            schemas,
        )

        app.register_blueprint(users.bp)
        app.register_blueprint(groups.bp)
        app.register_blueprint(service_provider_config.bp)
        app.register_blueprint(resource_types.bp)
        app.register_blueprint(schemas.bp)

    # Global error handlers

    @app.errorhandler(TransportServerError)
    @app.errorhandler(TransportProtocolError)
    def handle_retryable_errors(e):
        error_id = str(uuid.uuid4())
        logger.exception(
            "Service unavailable.", extra={"error_id": error_id, "error": str(e)}
        )
        return (
            jsonify(
                {
                    "error": f"Service unavailable. Please contact support with error ID {error_id}"
                }
            ),
            503,
        )

    @app.errorhandler(404)
    def not_found(e):
        response = jsonify(
            {"status": 404, "error": "not found", "message": "invalid resource URI"}
        )
        response.status_code = 404
        return response

    @app.errorhandler(Exception)
    def handle_unexpected_errors(e):
        error_id = str(uuid.uuid4())
        logger.exception(
            "Unexpected error.", extra={"error_id": error_id, "error": str(e)}
        )
        return (
            jsonify(
                {
                    "error": f"An unexpected error occurred. Please contact support with error ID {error_id}"
                }
            ),
            500,
        )

    # Return the configured Flask application instance
    return app
