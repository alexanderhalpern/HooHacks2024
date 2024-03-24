from flask import Flask, request, jsonify
from flask_cors import CORS

from song_finder import SongFinder, get_search_results
from instructor import Instructor
from player import Player
from analyzer import Analyzer
import mido
import os
import json

# when the server start read from json called state.json
# do it with os


app = Flask(__name__)
CORS(app)

# set the default values for the state
if not os.path.exists('state.json'):
    with open('state.json', 'w') as f:
        json.dump({"state": "search", "feedback": "", "song": ""}, f)
#else:
#    with open('state.json', "r") as f:
#        file = json.load(f)
#    file['state'] = "search"
#    file['feedback'] = ""
#    file['song'] = ""

#    with open('state.json', "w") as f:
#        json.dump(file, f)


@app.route('/teach', methods=['GET'])
async def teach():

    # if state is "song_set", then start the lesson
    with open('state.json', 'r') as f:
        file = json.load(f)
    if file['state'] == "song_set":
        # set the state to "lesson_started"
        file['state'] = "lesson_started"
        with open('state.json', 'w') as f:
            json.dump(file, f)
        return jsonify({"message": "Lesson started."})

    # end the lesson
    return jsonify({"message": "No song configured."})

@app.route('/setState', methods=['GET'])
def setState():
    print("HSDFSDFSDF")
    state = request.args.get('state')
    print(state)
    # write to json called state.json
    with open('state.json', 'r') as f:
        file = json.load(f)
    file['state'] = state

    with open('state.json', 'w') as f:
        json.dump(file, f)

    return jsonify({"message": "State set."})

@app.route('/setFeedback', methods=['GET'])
def setFeedback():
    feedback = request.args.get('feedback')
    # write to json called state.json
    with open('state.json', 'r') as f:
        file = json.load(f)
        file['feedback'] = feedback

    with open('state.json', 'w') as f:
        json.dump(file, f)

    return jsonify({"message": "Feedback set."})

@app.route('/getFeedback', methods=['GET'])
def getFeedback():
    if os.path.exists('state.json'):
        with open('state.json') as f:
            feedback = json.load(f)
    return jsonify({"feedback": feedback})

@app.route('/getState', methods=['GET'])
def getState():
    if os.path.exists('state.json'):
        with open('state.json') as f:
            state = json.load(f)['state']
    return jsonify({"state": state})

@app.route('/search', methods=['GET'])
def search():
    search_query = request.args.get('query')
    results_array = get_search_results(search_query)
    return jsonify({"results": results_array})

@app.route('/setSong', methods=['GET'])
def setSong():
    song_url = request.args.get('song_url')
    print(song_url)
    song = SongFinder()
    song._download_midi(song_url)
    with open('state.json', 'r') as f:
        file = json.load(f)
    file['song'] = song_url[1:]
    file['state'] = "song_set"

    with open('state.json', 'w') as f:
        json.dump(file, f)
    return jsonify({"message": "Song set."})

@app.route('/getSong', methods=['GET'])
def getSong():
    if os.path.exists('state.json'):
        with open('state.json') as f:
            song = json.load(f)['song']
    return jsonify({"song": song})

if __name__ == '__main__':
    app.run(debug=True)

    print('lihoih')

