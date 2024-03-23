import mido

class Player:

    def __init__(self):
        # TODO include any properties the player needs
        pass

    # calibrate the projector so the virtual keys match up with the real keys
    def calibrate_visualization(self):
        pass

    # play a given midi object (and light up keys)
    def play(self, song):
        pass

    # record user input (light up key green if correct red if wrong)
    def record_attempt(self, song):

        # start a blank mide file
        attempt = mido.MidiFile()

        # copy the song properties (tempo, time signature, etc.)
        # don't copy the notes
        attempt.ticks_per_beat = song.ticks_per_beat
        attempt.type = song.type

        # loop
        while True:

            # wait for user to press a key

            # if it's right, light up green, else red

            # save the note to the midi file

            # if the user is done, break

            pass


        # return the midi data
        return attempt



