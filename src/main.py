from instructor import Instructor
from player import Player
from analyzer import Analyzer
import mido


def main():
    # Load midi file
    input_song_midi = mido.MidiFile("twinkle.mid")

    # create an instructor to teach you the song
    # instructor = Instructor(Player(), Analyzer())
    instructor = Instructor(None, None)

    # start the lesson
    instructor.lesson(input_song_midi)

    # end the lesson
    return


if __name__ == "__main__":
    main()
