import pygame
import piano_lists as pl
from pygame import mixer
import pygame.midi
import time
import mido
from typing import Tuple, List


class Player:

    fps = 60
    WIDTH = 52 * 25  # Set Width of Window
    HEIGHT = 300  # Set Height of Window
    piano_notes = pl.piano_notes
    white_notes = pl.white_notes
    black_notes = pl.black_notes
    black_labels = pl.black_labels
    white_width = 54
    black_width = 34
    keyboard_offset = 21
    end_sleep_time = 1

    def __init__(self) -> None:
        self.timer, self.screen = self._init_pygame()
        self.midi_input = self._ask_midi_device()
        self.white_sounds, self.black_sounds = self._load_note_sounds()
        self.active_whites = []
        self.active_blacks = []

    def _ask_midi_device(self) -> pygame.midi.Input:
        # num_devices = pygame.midi.get_count()
        # print("Available MIDI devices:")
        # for i in range(num_devices):
        #     info = pygame.midi.get_device_info(i)
        #     device_type = "Input" if info[2] == 1 else "Output"
        #     print(f"Device ID {i}: {info[1].decode()} ({device_type})")
        # device_id = int(input("Enter the Device ID to use: "))
        device_id = 1
        return pygame.midi.Input(device_id)

    def _init_fonts(self) -> Tuple[pygame.font.Font]:
        font = pygame.font.Font("../assets/OldStandardTT-Bold.ttf", 48)
        medium_font = pygame.font.Font(
            "../assets/OldStandardTT-Bold.ttf", 28)
        small_font = pygame.font.Font("../assets/OldStandardTT-Bold.ttf", 16)
        real_small_font = pygame.font.Font(
            "../assets/OldStandardTT-Bold.ttf", 10)
        return font, medium_font, small_font, real_small_font

    def _load_note_sounds(self) -> Tuple[List[mixer.Sound]]:
        white_sounds = []
        black_sounds = []
        for i in range(len(self.white_notes)):
            white_sounds.append(
                mixer.Sound(f"../assets\\notes\\{self.white_notes[i]}.wav")
            )

        for i in range(len(self.black_notes)):
            black_sounds.append(
                mixer.Sound(f"../assets\\notes\\{self.black_notes[i]}.wav")
            )
        return white_sounds, black_sounds

    def _init_pygame(self) -> Tuple:
        pygame.init()
        pygame.midi.init()
        pygame.mixer.init()
        pygame.mixer.set_num_channels(50)
        timer = pygame.time.Clock()
        screen = pygame.display.set_mode([self.WIDTH, self.HEIGHT])
        return timer, screen

    def demo(self, midi_file: mido.MidiFile):
        self.timer, self.screen = self._init_pygame()

        start_time = time.time()
        track_iter = iter(midi_file)
        next_event_time = 0
        has_messages = True

        try:
            next_msg = next(track_iter)
            next_event_time = next_msg.time
        except StopIteration:
            next_msg = None
            has_messages = False

        while has_messages:
            elapsed_time = time.time() - start_time

            # Check and play the MIDI messages when their time comes
            while elapsed_time >= next_event_time and next_msg:
                self._process_midi_message(next_msg)

                try:
                    next_msg = next(track_iter)
                    next_event_time += next_msg.time
                except StopIteration:
                    next_msg = None
                    has_messages = False

            self.timer.tick(self.fps)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self._draw_piano()
            pygame.display.flip()

        time.sleep(self.end_sleep_time)

        self.active_whites = []
        self.active_blacks = []
        pygame.display.quit()

    def record_attempt(self, reference: mido.MidiFile) -> mido.MidiFile:
        self.timer, self.screen = self._init_pygame()

        start_time = time.time()
        self.midi_input.read(10)

        # Extract tempo (microseconds per beat) from reference MIDI file
        tempo = 500000  # default MIDI tempo (120 BPM)
        for track in reference.tracks:
            for msg in track:
                if msg.is_meta and msg.type == 'set_tempo':
                    tempo = msg.tempo
                    break

        midi_file = mido.MidiFile(ticks_per_beat=reference.ticks_per_beat)
        track = mido.MidiTrack()
        midi_file.tracks.append(track)

        start_time = time.time()
        last_event_time = start_time
        total_notes = self._count_notes_in_midi_file(reference)
        current_notes = 0

        run = True
        while run and (current_notes < total_notes):
            self.timer.tick(self.fps)
            self._draw_piano()
            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False

            if not self.midi_input.poll():
                continue

            midi_events = self.midi_input.read(10)
            current_time = time.time()
            event_delta_time_seconds = current_time - last_event_time
            last_event_time = current_time

            # Convert the event delta time to MIDI ticks
            event_delta_time_ticks = int(
                (event_delta_time_seconds * 1000000) / (tempo / midi_file.ticks_per_beat))

            off_notes_added = self._process_midi_events(
                midi_events, event_delta_time_ticks, track)
            current_notes += off_notes_added
            print(f"Current notes: {current_notes}/{total_notes}")

        time.sleep(self.end_sleep_time)
        self.active_whites = []
        self.active_blacks = []
        # self.midi_input.close()
        # pygame.midi.quit()
        pygame.display.quit()

        midi_file.save('newoutput.mid')

        return midi_file

    def _process_midi_message(self, message):
        if message.type not in ["note_on", "note_off"]:
            return

        note_name = self.piano_notes[message.note - self.keyboard_offset]
        # print(note_name)

        if note_name in self.white_notes:
            white_index = self.white_notes.index(note_name)
            if message.type == "note_on" and message.velocity > 0:
                print(f"note white: {message.note}")
                self.white_sounds[white_index].play()
                self.active_whites.append(white_index)
            elif message.type == "note_off":
                self.active_whites.remove(white_index)
        elif note_name in self.black_notes:
            black_index = self.black_notes.index(note_name)
            if message.type == "note_on" and message.velocity > 0:
                print(f"note black: {message.note}")
                self.black_sounds[black_index].play()
                self.active_blacks.append(black_index)
            elif message.type == "note_off":
                self.active_blacks.remove(black_index)

    def _draw_piano(self):
        # === Whites ===
        for i in range(36):
            pygame.draw.rect(self.screen, 'black', [
                i * self.white_width, 0, self.white_width, self.HEIGHT], 0, 2)

        # Paint over green if active
        for key_pos in self.active_whites:
            pygame.draw.rect(self.screen, 'green', [
                key_pos * self.white_width, 0, self.white_width, self.HEIGHT], 0, 2)

        # === Blacks ===
        # Pattern of black keys relative to white keys in each octave
        black_key_offsets = [0, 1, 3, 4, 5]
        octave_size = 7  # Number of white keys in an octave

        for i, black_note in enumerate(self.black_notes):
            # Extract the octave number
            octave = int(black_note[-1])

            # Determine the black key's position within the octave
            black_key_index_within_octave = black_key_offsets[i % len(
                black_key_offsets)]

            # Calculate white key index relative to C of the octave and then the black key position
            draw_position = ((octave - 2) * octave_size + black_key_index_within_octave) * \
                self.white_width + self.white_width - self.black_width / 2

            # Draw the black key
            color = 'green' if i in self.active_blacks else 'black'
            pygame.draw.rect(self.screen, color, [
                             draw_position, 0, self.black_width, self.HEIGHT // 1.5], 0, 2)

    def _process_midi_events(self, midi_events, event_delta_time_ticks, track) -> int:
        """Processes midi_events and returns number of new notes"""
        off_notes_added = 0

        for event in midi_events:
            status, note, velocity, _ = event[0]
            print(status, note, velocity)
            note_name = self.piano_notes[note - self.keyboard_offset]

            if velocity > 0:

                track.append(
                    mido.Message(
                        "note_on", note=note, velocity=velocity, time=event_delta_time_ticks
                    )
                )
                if note_name in self.black_notes:
                    black_index = self.black_notes.index(note_name)
                    self.black_sounds[black_index].play()
                    self.active_blacks.append(black_index)
                if note_name in self.white_notes:
                    white_index = self.white_notes.index(note_name)
                    self.white_sounds[white_index].play()
                    self.active_whites.append(white_index)

            elif status == 128 or velocity == 0:
                off_notes_added += 1
                print("note off")
                track.append(
                    mido.Message(
                        "note_off",
                        note=note,
                        velocity=velocity,
                        time=event_delta_time_ticks,
                    )
                )
                if note_name in self.black_notes:
                    black_index = self.black_notes.index(note_name)
                    self.active_blacks.remove(black_index)
                if note_name in self.white_notes:
                    white_index = self.white_notes.index(note_name)
                    self.active_whites.remove(white_index)

        return off_notes_added

    def _count_notes_in_midi_file(self, midi_file: mido.MidiFile) -> int:
        note_count = 0
        for track in midi_file.tracks:
            for msg in track:
                if msg.type == 'note_off':
                    note_count += 1
        return note_count
