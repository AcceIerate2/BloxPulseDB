from flask import Flask, request, jsonify, Response
import dbHandler
import logging
import time
from werkzeug.exceptions import ClientDisconnected
from functools import wraps
import os

# Configure logging
logging.basicConfig(
    filename='bloxpulse.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize database
dbHandler.init_db()
app = Flask(__name__)

def log_request_time(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        start_time = time.time()
        response = f(*args, **kwargs)
        duration = time.time() - start_time
        # Log if request takes more than 1 second
        if duration > 1:
            logger.warning(f"Slow request to {request.path}: {duration:.2f}s")
        return response
    return decorated_function

@app.errorhandler(ClientDisconnected)
def client_disconnected(e):
    logger.info("Client disconnected prematurely")
    return Response(status=499)  # Client Closed Request

@app.route('/schedule', methods=['POST'])
@log_request_time
def schedule_task():
    try:
        # Process request quickly to minimize connection time
        dataReceived = request.get_json(silent=True)
        if not dataReceived or not isinstance(dataReceived, dict):
            return Response("Invalid data format", status=400, content_type='text/plain')

        universeId = dataReceived.get('universeId')
        if not universeId:
            return Response("Invalid data", status=400, content_type='text/plain')
        
        # Do database operation
        if dbHandler.insert(universeId, dataReceived):
            return Response("Success", status=200, content_type='text/plain')
        return Response("Error", status=500, content_type='text/plain')

    except ClientDisconnected:
        logger.info("Client disconnected during schedule operation")
        return Response(status=499)
    except Exception as e:
        logger.error(f"Schedule task error: {str(e)}")
        return Response("Error", status=500, content_type='text/plain')

@app.route('/bulk_remove', methods=['POST'])
@log_request_time
def remove_bulk():
    auth_key = request.args.get("auth")
    if not auth_key or auth_key != os.getenv("AUTH_KEY"):
        return Response(f"Access Denied.", status=401, content_type='text/plain')
    
    try:
        dataReceived = request.get_json(silent=True)
        if not isinstance(dataReceived, list):
            return Response("Invalid data format", status=400, content_type='text/plain')

        # Perform bulk deletion in dbHandler using executemany
        ok = dbHandler.remove_bulk(dataReceived)
        if ok:
            return Response("Success", status=200, content_type='text/plain')
        return Response("Error", status=500, content_type='text/plain')
    except ClientDisconnected:
        logger.info("Client disconnected during bulk remove operation")
        return Response(status=499)
    except Exception as e:
        logger.error(f"Bulk remove error: {str(e)}")
        return Response("Error", status=500, content_type='text/plain')

@app.route('/get_database', methods=["GET"])
@log_request_time
def get_database():
    auth_key = request.args.get("auth")
    if not auth_key or auth_key != os.getenv("AUTH_KEY"):
        return Response("Access Denied.", status=401, content_type='text/plain')

    dataToReturn = []
    try:
        dataToReturn = dbHandler.getAll()
    except Exception as e:
        logger.error(f"Get database error: {str(e)}")
        pass
    
    return jsonify(dataToReturn)

@app.route('/', methods=['GET'])
def index():
    return "Hello, World!"

#if __name__ == "__main__":
    #app.run(debug=False)
