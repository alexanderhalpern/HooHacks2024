import mido
from mido import MidiFile, MidiTrack
from music21 import converter, stream, note

from player import Player
from analyzer import Analyzer
from typing import List
import requests
import time


class Instructor:

    time_per_segment = 1

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
        reference_snippets = get_song_snippets(input_song_midi)
        # reference_snippets = [input_song_midi]

        # loop until done
        current_snippet_idx = 0
        while len(reference_snippets) > 0 and current_snippet_idx < len(reference_snippets):

            requests.get('http://localhost:5000/setState?state=demoing')

            # *play* the next snippet
            self.player.demo(reference_snippets[current_snippet_idx])

            requests.get('http://localhost:5000/setState?state=recording')

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

        requests.get('http://localhost:5000/setState?state=done')

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
            mistake_time = list(mistake_timeline.keys())[0]
            advice = f"Time {mistake_time}: " + \
                self._describe_mistake(mistake_timeline[mistake_time])

            # TODO connect to user interface
            print(
                "You're almost there! There's just one last thing to fix before we move on:")
            requests.get(
                'http://localhost:5000/setFeedback?feedback=' + advice)
            time.sleep(5)

        # if the user made multiple mistakes, correct the most severe one
        else:
            worst_mistake, mistake_time = self._find_worst_mistake(
                mistake_timeline)
            advice = f"Time {mistake_time}: " + \
                self._describe_mistake(worst_mistake)

            # TODO connect to user interface
            print("Here's one thing you can fix to make your performance even better:")
            requests.get(
                'http://localhost:5000/setFeedback?feedback=' + advice)
            time.sleep(5)

    def _find_worst_mistake(self, mistake_timeline: dict) -> dict:
        """
        Find the worst mistake in the user's attempt.

        Args:
            mistake_timeline (dict): A dictionary of mistakes and their timings, returned by the analyzer

        Returns:
            dict: The worst mistake
        """
        print(mistake_timeline)
        # if one mistake involves more notes than the others, return it
        counts = sorted([len(mistake_timeline[mistake]["errors"])
                        for mistake in mistake_timeline], reverse=True)
        if counts[0] > counts[1]:
            return mistake_timeline[counts.index(counts[0])], list(mistake_timeline.keys())[counts.index(counts[0])]

        # mistake type priority: "wrong_notes" > "missing_notes" > "extra_notes" > "early_timing" == "late_timing"
        # if multiple mistakes have the same number of notes, return the one with the highest priority
        # TODO more detailed priority system (take into account severity of deviation)
        for priority in ["wrong_notes", "missing_notes", "extra_notes", "early_timing", "late_timing"]:
            for mistake in mistake_timeline:
                if mistake_timeline[mistake]["type"] == priority:
                    return mistake_timeline[mistake], list(mistake_timeline.keys())[0]

        return mistake_timeline[0], list(mistake_timeline.keys())[0]

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
                delta = mistake["errors"][0][1]["reference_pitch"] - \
                    mistake["errors"][0][1]["user_pitch"]
                return "Some of your notes are slightly off here. Try again and pay extra attention here."

                # if all([note[1]["reference_pitch"] - note[1]["user_pitch"] == delta for note in mistake["errors"]]):
                #     return (f"Your notes are all off by {delta} semitones. Try transposing this {'note' if len(mistake['errors']) == 1 else 'chord'}"
                #             f" {'up' if delta > 0 else 'down'}"
                #             f" by {abs(delta)} semitones.")
                # otherwise, give a general message
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

    # def _get_song_snippets(self, input_midi: MidiFile) -> List[MidiFile]:
    #     """
    #     Split a song into snippets of notes each of duration `time_per_segment`.
    #     """
    #     tempo = 500000  # Default MIDI tempo (500,000 microseconds per beat)
    #     for track in input_midi.tracks:
    #         for msg in track:
    #             if msg.type == "set_tempo":
    #                 tempo = msg.tempo
    #                 break  # find first tempo and break

    #     ticks_per_second = input_midi.ticks_per_beat * (1_000_000 / tempo)
    #     ticks_per_segment = ticks_per_second * self.time_per_segment

    #     snippets = []
    #     current_ticks = 0
    #     current_snippet = MidiFile(ticks_per_beat=input_midi.ticks_per_beat)
    #     current_track = MidiTrack()
    #     current_snippet.tracks.append(current_track)

    #     # merge all tracks into one
    #     merged_track = MidiTrack()
    #     for track in input_midi.tracks:
    #         for msg in track:
    #             merged_track.append(msg)

    #     min_index = 0
    #     i = 0
    #     notes_per_segment = 3
    #     for msg in merged_track:

    #         if i >= min_index or len(current_track) >= notes_per_segment:
    #             snippets.append(current_snippet)
    #             current_snippet = MidiFile(
    #                 ticks_per_beat=input_midi.ticks_per_beat)
    #             current_track = MidiTrack()
    #             current_snippet.tracks.append(current_track)
    #             current_ticks = 0

    #         # if the message is a not_on, find the corresponding note_off and make sure it's in the same snippet
    #         if msg.type == "note_on":
    #             current_track.append(msg)
    #             current_ticks += msg.time

    #             # find the corresponding note_off
    #             for note_off_msg in merged_track:
    #                 if note_off_msg.type == "note_off" and note_off_msg.note == msg.note:
    #                     min_index = merged_track.index(note_off_msg)

    #         if msg.type == "note_off":
    #             current_track.append(msg)
    #             current_ticks += msg.time

    #         i += 1

    #     return snippets


def get_song_snippets(input_midi: MidiFile) -> List[MidiFile]:
    """
    Split a song into snippets of notes each of duration `time_per_segment`.
    """

    """# use music21 to split the song into snippets
    myScore = converter.parse('../assets/midi/downloads/twinkle-twinkle-little-star.mid')
    i = 1
    snippets = []
    while (measureStack := myScore.measure(i))[stream.Measure]:
        notes = measureStack[note.Note]
        snippets.append(notes)
        i += 1

    # create a list of snippets
    snippets = []

    return snippets"""
    # print("INPUT_MIDI", input_midi)

    tempo = 500000  # Default MIDI tempo (500,000 microseconds per beat)
    for track in input_midi.tracks:
        for msg in track:
            if msg.type == "set_tempo":
                tempo = msg.tempo
                break  # find first tempo and break

    ticks_per_second = input_midi.ticks_per_beat * (1_000_000 / tempo)

    snippets = []
    current_ticks = 0
    current_snippet = MidiFile(ticks_per_beat=input_midi.ticks_per_beat)
    current_track = MidiTrack()
    current_snippet.tracks.append(current_track)

    # merge all tracks into one
    merged_track = MidiTrack()
    for track in input_midi.tracks:
        for msg in track:
            if msg.type == "note_on" or msg.type == "note_off":
                merged_track.append(msg)

    # stack = {}
    # for msg in merged_track:
    #     if msg.note in stack:
    #         merged_track.remove(msg)
    #         continue
    #     if msg.type == "note_on":
    #         stack[msg.note] = msg
    #     elif msg.type == "note_off":
    #         if msg.note in stack:
    #             del stack[msg.note]

    # print("MERGED_TRACK", merged_track)
    # print number of note_on and note_off messages
    note_on_count = 0
    note_off_count = 0

    for msg in merged_track:
        if msg.type == "note_on":
            note_on_count += 1
        elif msg.type == "note_off":
            note_off_count += 1
    print("note_on_count", note_on_count)
    print("note_off_count", note_off_count)

    notes_per_segment = 4

    # pair up notes ahead of time (note_on, note_off)
    note_pairs = []
    assigned_noteoffs = [False for _ in range(len(merged_track))]
    for i in range(len(merged_track)):
        if merged_track[i].type == "note_on":
            for j in range(i, len(merged_track)):
                if assigned_noteoffs[j]:
                    continue
                if merged_track[j].type == "note_off" and merged_track[j].note == merged_track[i].note:
                    note_pairs.append((i, j))
                    assigned_noteoffs[j] = True
                    break

    # min_cutoff = 1
    # i = 0
    # while i < note_pairs[-1][1]:
    #     if len(current_track) < notes_per_segment:

    #         # add the smallest number of sequential notes possible while keeping both pair members in the snippet
    #         for pair in note_pairs:
    #             if pair[0] >= i:
    #                 for j in range(pair[0], pair[1] + 1):
    #                     if merged_track[j].type == "note_on" or merged_track[j].type == "note_off":
    #                         current_track.append(merged_track[j])
    #                     if merged_track[j].type == "note_on":
    #                         for pair in note_pairs:
    #                             if pair[0] == j:
    #                                 min_cutoff = max(min_cutoff, pair[1])
    #                                 break
    #             if len(current_track) >= notes_per_segment:
    #                 break

    #         if pair[1] >= min_cutoff:
    #             snippets.append(current_snippet)
    #             current_snippet = MidiFile(
    #                 ticks_per_beat=input_midi.ticks_per_beat)
    #             current_track = MidiTrack()
    #             current_snippet.tracks.append(current_track)
    #             i = pair[1]

    # # each snippet should contain all snippets before itself as well (0 1 2, 0 1 2 3, 0 1 2 3 4, etc.)
    # additive_snippets = []
    # for i in range(len(snippets)):
    #     additive_snippets.append(
    #         MidiFile(ticks_per_beat=input_midi.ticks_per_beat))
    #     additive_snippets[i].tracks.append(MidiTrack())
    #     for j in range(i + 1):
    #         for msg in snippets[j].tracks[0]:
    #             additive_snippets[i].tracks[0].append(msg)

    # # for snippet in additive_snippets:
    # #     # make sure that each note_on has a corresponding note_off use a stack
    # #     stack = {}
    # #     for msg in snippet.tracks[0]:
    # #         if msg.type == "note_on":
    # #             stack[msg.note] = msg
    # #         elif msg.type == "note_off":
    # #             if msg.note in stack:
    # #                 del stack[msg.note]
    # #             else:
    # #                 stack[msg.note] = msg

    # #     print(snippet.tracks[0], stack)

    # #     # remove any unmatched note_offs
    # #     # dont want the dictionary to change size during iteration
    # #     stack_copy = stack.copy()
    # #     for note in stack_copy:
    # #         if stack[note].type == "note_off":
    # #             snippet.tracks[0].remove(stack[note])
    # #             del stack[note]

    # #     # add a note_off for any unmatched note_ons
    # #     stack_copy = stack.copy()
    # #     for note in stack_copy:
    # #         if stack[note].type == "note_on":
    # #             snippet.tracks[0].append(
    # #                 mido.Message("note_off", note=note, time=0))

    # print("snippets", additive_snippets[0:3])
    notes_per_segment = 4
    snippets = []
    i = 0
    while i < len(merged_track):
        current_snippet = MidiFile(ticks_per_beat=input_midi.ticks_per_beat)
        current_track = MidiTrack()
        current_snippet.tracks.append(current_track)

        notes_added = 0
        while i < len(merged_track) and notes_added < notes_per_segment:
            msg = merged_track[i]
            current_track.append(msg)
            if msg.type == "note_off":
                notes_added += 1
            i += 1

        if notes_added > 0:
            snippets.append(current_snippet)

    additive_snippets = []
    for i in range(len(snippets)):
        additive_snippets.append(
            MidiFile(ticks_per_beat=input_midi.ticks_per_beat))
        additive_snippets[i].tracks.append(MidiTrack())
        for j in range(i + 1):
            for msg in snippets[j].tracks[0]:
                additive_snippets[i].tracks[0].append(msg)
    return additive_snippets


if __name__ == '__main__':
    file = mido.MidiFile('../assets/midi/downloads/untitled.mid')
    snippets = get_song_snippets(file)
    print(len(snippets))
