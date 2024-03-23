from src.instructor import Instructor
from src.player import Player
from src.analyzer import Analyzer

# main loop

def main():

    # pick a song
    song = None

    # create an instructor to teach you the song
    instructor = Instructor(Player(), Analyzer())

    # start the lesson
    instructor.lesson(song)

    # end the lesson
    return


