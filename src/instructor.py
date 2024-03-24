import mido
from mido import MidiFile, MidiTrack
from player import Player
from analyzer import Analyzer
from typing import List
import requests


class Instructor:

    notes_per_segment = 5

    def __init__(self, player: Player, analyzer: Analyzer) -> None:
        """
        Create a new Instructor object

        Args:
            player (Player): The player object to use
            analyzer (Analyzer): The analyzer object to use

        Returns:
            None
        """
        self.type = "friendly"
        self.player = player
        self.analyzer = analyzer
        self.lesson_state = "not_started"

    # def lesson(song)
    def lesson(self, input_song_midi: mido.MidiFile) -> None:
        """
        Teach the user the song.

        Args:
            input_song_midi (mido.MidiFile): The song to teach

        Returns:
            None
        """
        reference_snippets = self._get_song_snippets(input_song_midi)
        # reference_snippets = [input_song_midi]

        # loop until done
        current_snippet_idx = 0
        while len(reference_snippets) > 0 and current_snippet_idx < len(reference_snippets):

            # requests.get('http://localhost:5000/setState?state=demoing')

            # *play* the next snippet
            self.player.demo(reference_snippets[current_snippet_idx])

            # requests.get('http://localhost:5000/setState?state=recording')

            # *get* user attempt
            student_attempt = self.player.record_attempt(
                reference_snippets[current_snippet_idx]
            )

            # requests.get('http://localhost:5000/setState?state=feedback')

            # *analyze* their mistakes
            is_sufficient, mistakes = self.analyzer.judge_attempt(
                reference_midi=reference_snippets[current_snippet_idx],
                user_midi=student_attempt,
            )

            if not is_sufficient:
                self._correct_mistakes(mistakes)
                continue
            current_snippet_idx += 1

        # requests.get('http://localhost:5000/setState?state=done')

    def _correct_mistakes(self, mistake_timeline: dict) -> None:
        """
        Correct the mistakes in the user's attempt.

        Args:
            mistake_timeline (dict): A dictionary of mistakes and their timings, returned by the analyzer

        Returns:
            None
        """
        # if the user made a single mistake, tell them how to correct it
        if len(mistake_timeline) == 1:
            # get the time of the mistake (first key in the dictionary)
            time = list(mistake_timeline.keys())[0]
            advice = f"Time {time}: " + \
                self._describe_mistake(mistake_timeline[0])

            # TODO connect to user interface
            print(
                "You're almost there! There's just one last thing to fix before we move on:")
            # requests.get('http://localhost:5000/setFeedback?feedback=' + advice)
            print(advice)

        # if the user made multiple mistakes, correct the most severe one
        else:
            worst_mistake, time = self._find_worst_mistake(mistake_timeline)
            advice = f"Time {time}: " + self._describe_mistake(worst_mistake)

            # TODO connect to user interface
            print("Here's one thing you can fix to make your performance even better:")
            # requests.get('http://localhost:5000/setFeedback?feedback=' + advice)

    def _find_worst_mistake(self, mistake_timeline: dict) -> dict:
        """
        Find the worst mistake in the user's attempt.

        Args:
            mistake_timeline (dict): A dictionary of mistakes and their timings, returned by the analyzer

        Returns:
            dict: The worst mistake
        """

        # if one mistake involves more notes than the others, return it
        counts = sorted([len(mistake["errors"])
                        for mistake in mistake_timeline], reverse=True)
        if counts[0] > counts[1]:
            return mistake_timeline[counts.index(counts[0])]

        # mistake type priority: "wrong_notes" > "missing_notes" > "extra_notes" > "early_timing" == "late_timing"
        # if multiple mistakes have the same number of notes, return the one with the highest priority
        # TODO more detailed priority system (take into account severity of deviation)
        for priority in ["wrong_notes", "missing_notes", "extra_notes", "early_timing", "late_timing"]:
            for mistake in mistake_timeline:
                if mistake["type"] == priority:
                    return mistake

        return mistake_timeline[0]

    def _describe_mistake(self, mistake: dict) -> str:
        """
        Describe a mistake to the user.

        Args:
            mistake (dict): A dictionary representing a mistake, returned by the analyzer

        Returns:
            str: A description of the mistake
        """
        match mistake["type"]:
            case "wrong_notes":
                # if all notes are wrong in the same way, tell the user to transpose
                delta = mistake["errors"][0]["correct_note"] - \
                    mistake["errors"][0]["user_note"]
                if all([note["correct_note"] - note["user_note"] == delta for note in mistake["errors"]]):
                    return (f"Your notes are all off by {delta} semitones. Try transposing this {'note' if len(mistake['errors']) == 1 else 'chord'}"
                            f" {'up' if delta > 0 else 'down'}"
                            f" by {abs(delta)} semitones.")
                # otherwise, give a general message
                return "Some of your notes are slightly off here. Try again and pay extra attention here."
            case "missing_notes":
                if len(mistake["errors"]) == 1:
                    return "You missed a note here. Try playing it again."
                return "You missed some notes in this chord. Try playing them again."
            case "extra_notes":
                if len(mistake["errors"]) == 1:
                    return "You played an extra note here. Try playing it again."
                return "You played some extra notes in this chord. Try playing it again."
            case "early_timing":
                if len(mistake["errors"]) == 1:
                    return "You played this note too early. Try playing it again."
                return "You played these notes too early. Try playing them again."
            case "late_timing":
                if len(mistake["errors"]) == 1:
                    return "You played this note too late. Try playing it again."
                return "You played these notes too late. Try playing them again."
            case _:
                return "There was a mistake here. Try playing this part again."

    def _get_song_snippets(self, input_midi: MidiFile) -> List[MidiFile]:
        """
        Split a song into cumulative snippets based on the number of notes.
        """
        snippets = []
        note_count = 0
        current_snippet = MidiFile(ticks_per_beat=input_midi.ticks_per_beat)
        current_track = MidiTrack()
        current_snippet.tracks.append(current_track)

        notes_on = 0
        notes_off = 0

        for track in input_midi.tracks:
            for msg in track:
                # Copy the message to the current track
                current_track.append(msg.copy())
                # Count note on/off events
                print(msg)
                if msg.type == 'note_on':
                    notes_on += 1
                if msg.type == 'note_off':
                    notes_off += 1
                print(notes_on, notes_off)
                if msg.type == 'note_off' and notes_on == notes_off:
                    note_count += 1
                    # When the note count hits the threshold, save the snippet and reset the count
                    if note_count >= self.notes_per_segment:
                        snippets.append(current_snippet)
                        current_snippet = MidiFile(
                            ticks_per_beat=input_midi.ticks_per_beat)
                        current_track = MidiTrack()
                        current_snippet.tracks.append(current_track)
                        note_count = 0
                        # Copy all messages from the beginning up to this point
                        for previous_msg in track[:track.index(msg) + 1]:
                            current_track.append(previous_msg.copy())

        # Add the last snippet if it contains any messages
        if len(current_track) > 0:
            snippets.append(current_snippet)

        return snippets
