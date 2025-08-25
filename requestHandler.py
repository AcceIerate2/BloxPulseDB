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

def remove_bulk():
    dataReceived: dict = request.get_json()
    if not type(dataReceived) == dict: return

    for universeId, data in dataReceived.items():
        dbHandler.remove(universeId, data)

if __name__ == "__main__":
    app.run(debug=False)
    

