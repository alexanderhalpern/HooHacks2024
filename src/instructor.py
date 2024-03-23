import mido
from mido import MidiFile, MidiTrack
from player import Player
from analyzer import Analyzer
from typing import List


class Instructor:

    time_per_segment = 3

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

        # loop until done
        current_snippet_idx = 0
        while len(reference_snippets) > 0:

            # *play* the next snippet
            self.player.demo(reference_snippets[current_snippet_idx])

            # *get* user attempt
            student_attempt = self.player.record_attempt(
                reference_snippets[current_snippet_idx]
            )

            # *analyze* their mistakes
            is_sufficient, mistakes = self.analyzer.judge_attempt(
                reference_midi=reference_snippets[current_snippet_idx],
                user_midi=student_attempt,
            )

            if not is_sufficient:
                self._correct_mistakes(mistakes)
                continue
            current_snippet_idx += 1

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
            advice = self._describe_mistake(mistake_timeline[0])

            # TODO connect to user interface
            print("You're almost there! There's just one last thing to fix before we move on:")
            print(advice)

        # if the user made multiple mistakes, correct the most severe one
        else:
            worst_mistake = self._find_worst_mistake(mistake_timeline)
            advice = self._describe_mistake(worst_mistake)

            # TODO connect to user interface
            print("Here's one thing you can fix to make your performance even better:")
            print(advice)


    def _find_worst_mistake(self, mistake_timeline: dict) -> dict:
        """
        Find the worst mistake in the user's attempt.

        Args:
            mistake_timeline (dict): A dictionary of mistakes and their timings, returned by the analyzer

        Returns:
            dict: The worst mistake
        """

        # if one mistake involves more notes than the others, return it
        counts = sorted([len(mistake["errors"]) for mistake in mistake_timeline], reverse=True)
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
                delta = mistake["errors"][0]["correct_note"] - mistake["errors"][0]["user_note"]
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
        Split a song into snippets of notes each of duration `time_per_segment`.
        """
        tempo = 500000  # Default MIDI tempo (500,000 microseconds per beat)
        for track in input_midi.tracks:
            for msg in track:
                if msg.type == "set_tempo":
                    tempo = msg.tempo
                    break  # find first tempo and break

        ticks_per_second = input_midi.ticks_per_beat * (1_000_000 / tempo)
        ticks_per_segment = ticks_per_second * self.time_per_segment

        snippets = []
        current_ticks = 0
        current_snippet = MidiFile(ticks_per_beat=input_midi.ticks_per_beat)
        current_track = MidiTrack()
        current_snippet.tracks.append(current_track)

        for track in input_midi.tracks:
            for msg in track:
                if current_ticks + msg.time > ticks_per_segment:
                    if len(current_track) > 0:
                        snippets.append(current_snippet)
                    current_snippet = MidiFile(ticks_per_beat=input_midi.ticks_per_beat)
                    current_track = MidiTrack()
                    current_snippet.tracks.append(current_track)
                    current_ticks = 0

                current_ticks += msg.time
                current_track.append(msg)

        if len(current_track) > 0:
            snippets.append(current_snippet)

        return snippets
