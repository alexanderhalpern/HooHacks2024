from src.instructor import Instructor
from src.player import Player
from src.analyzer import Analyzer

# main loop
from player import Player


def main():

    # pick a song
    song = None

    # create an instructor to teach you the song
    instructor = Instructor(Player(), Analyzer())

<<<<<<< HEAD
    # instructor.lesson(song)
    bob = Player()
    bob.record_attempt()
    pass
=======
    # start the lesson
    instructor.lesson(song)

    # end the lesson
    return
>>>>>>> c96d5e2cabb5406e94d1e9cf949821fd25565e8d


if __name__ == "__main__":
    main()
