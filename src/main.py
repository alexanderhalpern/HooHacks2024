from player import Player
from analyzer import Analyzer
import mido


def main():

    # instructor.lesson(song)
    bob = Player()
    # bob.record_attempt()
    midi_file = mido.MidiFile("output.mid")
    # bob.demo(midi_file)
    bob.record_attempt()

    pass


if __name__ == "__main__":
    main()
