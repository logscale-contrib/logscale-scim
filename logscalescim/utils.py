import logging
import uuid
from flask import jsonify

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def handle_graphql_error(e, entity_id=None, entity_type="entity"):
    error_id = str(uuid.uuid4())
    logger.exception(
        f"Error handling {entity_type}.",
        extra={"error_id": error_id, f"{entity_type}_id": entity_id, "error": str(e)},
    )
    return (
        jsonify(
            {
                "error": f"An error occurred. Please contact support with error ID {error_id}"
            }
        ),
        400,
    )
