import logging
import sys
from pythonjsonlogger import jsonlogger
from logscalescim import create_app

# Set up logging
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Create a stream handler to output logs to stdout
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)

# Define the JSON log format
formatter = jsonlogger.JsonFormatter(
    '%(asctime)s %(name)s %(levelname)s %(message)s')
handler.setFormatter(formatter)

# Add the handler to the root logger
root.addHandler(handler)

if __name__ == "__main__":
    # Create the Flask application instance
    app = create_app()
    # Run the application on host 0.0.0.0 and port 5000
    app.run(host="0.0.0.0", port=5000)
