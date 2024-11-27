import os
from dotenv import load_dotenv
import logging

# Load environment variables from a .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)


class Config:
    # Configuration class for the Flask application

    # Helper method to get environment variables and raise an error if not found
    @staticmethod
    def get_env_variable(var_name):
        value = os.getenv(var_name)
        if value is None:
            logger.error(
                "Environment variable is not set.", extra={"variable": var_name}
            )
            raise EnvironmentError(f"Environment variable {var_name} is not set.")
        return value

    @staticmethod
    def add_slashes(var_name):
        string = os.getenv(var_name)
        if string == "//" or string == "/":
            return ""
        if not string.startswith("/"):
            string = "/" + string
        if string.endswith("/"):
            string = string[:-1]
        return string

    # Required configuration variables
    SCIM_TOKEN = get_env_variable.__func__("SCIM_TOKEN")
    LOGSCALE_API_TOKEN = get_env_variable.__func__("LOGSCALE_API_TOKEN")
    LOGSCALE_URL = get_env_variable.__func__("LOGSCALE_URL")

    # Optional configuration variable for request path prefix
    REQUEST_PATH_PREFIX = add_slashes.__func__("REQUEST_PATH_PREFIX")
