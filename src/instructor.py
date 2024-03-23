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
        # self.type = "friendly"
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
            (is_sufficient, mistakes) = self.analyzer.judge_attempt(
                reference_midi=reference_snippets[current_snippet_idx],
                played_midi=student_attempt,
            )

            if not is_sufficient:
                continue
            current_snippet_idx += 1

        # return

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
