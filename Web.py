from flask import Flask
import os

# Create a Flask app instance
app = Flask(__name__)

@app.route('/')
def status():
    """This route will just show a simple status message."""
    return "Hello! The server is running."

def start():
    """This function starts the simple web server."""
    # Get the port from the environment, defaulting to 5000 for local testing
    port = int(os.environ.get("PORT", 5000))
    # Run the Flask app
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    start()
