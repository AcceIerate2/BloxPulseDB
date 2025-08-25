from flask import Flask, request, jsonify
import dbHandler

app = Flask(__name__)

@app.route('/schedule', methods=['POST'])
def schedule_task():
    dataReceived = request.get_json()
    if not type(dataReceived) == dict: return

    universeId = dataReceived.get('universeId')
    response = dbHandler.insert(universeId, dataReceived)

    return response

@app.route('/bulk_remove', methods=['POST'])
def remove_bulk():
    dataReceived: list = request.get_json()

    for data in dataReceived:
        universeId = data["universeId"]
        if not universeId:
            continue

        dbHandler.remove(universeId, data)

@app.route('/get_database', methods=["GET"])
def get_database():
    dataToReturn = []
    try:
        dataToReturn = dbHandler.getAll()
    except:
        pass
    
    return jsonify(dataToReturn)

@app.route('/', methods=['GET'])
def index():
    return "Hello, World!"
    

if __name__ == "__main__":
    app.run(debug=False)
    

