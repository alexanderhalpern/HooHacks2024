import mido

# class instructor
class Instructor:

    def __init__(self, player, analyzer):
        self.type = "friendly"
        self.player = player
        self.analyzer = analyzer

    # def lesson(song)
    def lesson(self, song):

        # copy the song properties (tempo, time signature, etc.)
        # don't copy the notes
        student_song = mido.MidiFile()
        student_song.ticks_per_beat = song.ticks_per_beat
        student_song.type = song.type

        # get all notes from the song
        ref_notes = []
        for track in song.tracks:
            for msg in track:
                if msg.type == 'note_on':
                    ref_notes.append(msg.note)
                if msg.type == 'note_off':
                    ref_notes.append(msg.note)

        # get all notes from the song
        student_notes = [ref_notes[:10]]

        # loop until done
        while True:

            # *play* the next snippet
            self.player.play(student_notes)

            # *get* user attempt
            student_attempt = self.player.record_attempt(student_notes)

            # *analyze* their mistakes
            (sufficient, mistakes) = self.analyzer.judge_attempt(student_attempt, student_notes)

            # if they got it right
            if sufficient:

                # add the next section to the snippet
                student_notes.append(ref_notes[len(student_notes):len(student_notes)+10])

            # else
            else:

                # inform them (somehow) of mistakes
                # TODO - implement this
                pass


        # return


