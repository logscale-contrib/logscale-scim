from flask import Flask, g
from .config import Config
from .graphql_client import GraphQLClient
from opentelemetry.instrumentation.flask import FlaskInstrumentor

def create_app():
    # Create a new Flask application instance
    app = Flask(__name__)
    
    # Load configuration from the Config class in logscalescim.config module
    app.config.from_object(Config)

    # Instrument Flask with OpenTelemetry
    FlaskInstrumentor().instrument_app(app)

    # Use the application context to register blueprints
    with app.app_context():
        # Import and register the blueprints for different routes
        from .routes import users, groups, service_provider_config, schemas
        app.register_blueprint(users.bp)
        app.register_blueprint(groups.bp)
        app.register_blueprint(service_provider_config.bp)
        app.register_blueprint(schemas.bp)

        # Initialize the GraphQL client and store it in the application context
        g.graphql_client = GraphQLClient(endpoint=app.config['GRAPHQL_ENDPOINT'], headers={'Authorization': f"Bearer {app.config['GRAPHQL_TOKEN']}"})

    # Return the configured Flask application instance
    return app