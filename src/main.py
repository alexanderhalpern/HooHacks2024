import time

from instructor import Instructor
from player import Player
from analyzer import Analyzer
import mido
import requests
import json


def main():

    # # wait until the server is ready
    # while True:
    #     response = requests.get('http://localhost:5000/getState')

    #     hi = response.json()
    #     if response.json()['state'] == "teach":
    #         break
    #     time.sleep(1)

    # create the player
    player = Player()

    # create the analyzer
    analyzer = Analyzer()

    # create the instructor
    instructor = Instructor(player, analyzer)

    # get the song from the server
    # response = requests.get('http://localhost:5000/getSong')
    # song = response.json()['song']
    # reformat the response from '/twinkle-3-mid' to '../assets/midi/downloads/twinkle-3.mid'
    # input_song_midi = mido.MidiFile(f"../assets/midi/downloads/{song}.mid")
    input_song_midi = mido.MidiFile(f"assets/midi/untitled.mid")

    # print(input_song_midi)
    # quit()

    # start the lesson
    instructor.lesson(input_song_midi)

    # end the lesson
    return


if __name__ == "__main__":
    main()
