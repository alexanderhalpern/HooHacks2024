from instructor import Instructor
from player import Player
from analyzer import Analyzer
import mido


def main():
    # Load midi file
    input_song_midi = mido.MidiFile(
        "assets/midi/twinkle-twinkle-bad.mid")

    # create an instructor to teach you the song
    instructor = Instructor(Player(), Analyzer())

    # start the lesson
    instructor.lesson(input_song_midi)

    # end the lesson
    return


if __name__ == "__main__":
    main()
