# play a given midi object (and light up keys)

# record user input (light up key green if correct red if wrong)
# player.record_attempt():

# start a blank mide file

# loop

# wait for user to press a key

# if it's right, light up green, else red

# save the note to the midi file

# return the midi data

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
    left_oct = 4
    right_oct = 5
    piano_notes = pl.piano_notes
    white_notes = pl.white_notes
    black_notes = pl.black_notes
    black_labels = pl.black_labels
    duration_light_frames = 30
    white_width = 54
    black_width = 34

    def __init__(self) -> None:
        self.timer, self.screen = self._init_pygame()
        self.midi_input = self._ask_midi_device()
        self.font, self.medium_font, self.small_font, self.real_small_font = self._init_fonts()
        self.white_sounds, self.black_sounds = self._load_note_sounds()
        self.active_whites = {}
        self.active_blacks = {}

    def _ask_midi_device(self) -> pygame.midi.Input:
        num_devices = pygame.midi.get_count()
        print("Available MIDI devices:")
        for i in range(num_devices):
            info = pygame.midi.get_device_info(i)
            device_type = "Input" if info[2] == 1 else "Output"
            print(f"Device ID {i}: {info[1].decode()} ({device_type})")
        device_id = int(input("Enter the Device ID to use: "))
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

        # iterates over messages (individual notes)
        for message in midi_file.play():
            self.timer.tick(self.fps)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    return

            self.draw_piano()

            if message.type != "note_on" and message.type != "note_off":
                continue

            # Map Midi Indices to Our Keyboard
            note_name = self.piano_notes[message.note - 21]

            # TODO: Come back to this and understand it please...
            if note_name in self.white_notes:
                white_index = self.white_notes.index(note_name)
                if message.type == "note_on" and message.velocity > 0:
                    self.white_sounds[white_index].play()
                    self.active_whites[white_index] = self.duration_light_frames
                else:
                    if white_index in self.active_whites.keys():
                        self.active_whites.pop(white_index)
            elif note_name in self.black_notes:
                black_index = self.black_notes.index(note_name)
                if message.type == "note_on" and message.velocity > 0:
                    self.black_sounds[black_index].play()
                    self.active_blacks[black_index] = self.duration_light_frames
                else:
                    if black_index in self.active_blacks.keys():
                        self.active_blacks.pop(black_index)

            pygame.display.flip()
            time.sleep(message.time)

        self.active_whites = {}
        self.active_blacks = {}
        pygame.quit()

    def draw_piano(self):
        # === Whites ===
        for i in range(36):
            pygame.draw.rect(self.screen, 'black', [
                i * self.white_width, self.HEIGHT - 100, self.white_width, self.HEIGHT], 0, 2)

        # Paint over green if active
        for (key_pos, frames_left) in self.active_whites.items():
            if frames_left > 0:
                pygame.draw.rect(self.screen, 'green', [
                    key_pos * self.white_width, self.HEIGHT - 100, self.white_width, self.HEIGHT], 0, 2)
                self.active_whites[key_pos] -= 1

        # === Blacks ===
        black_key_positions = []
        for i in range(25):
            if i % 7 not in [2, 6]:  # Skip where there are no black keys
                black_key_positions.append(i)

        for position in black_key_positions:
            draw_position = (position + .75) * self.white_width
            pygame.draw.rect(self.screen, 'black', [
                draw_position, 0, self.black_width, self.HEIGHT // 1.5], 0, 2)

        # Paint over green if active
        for (key_pos, duration_left) in self.active_blacks.items():
            draw_position = (key_pos + .75) * self.white_width
            if key_pos == key_pos:
                if duration_left > 0:
                    pygame.draw.rect(self.screen, 'green', [
                        draw_position, 0, self.black_width, self.HEIGHT // 1.5], 0, 2)
                    self.active_blacks[key_pos] -= 1

    def record_attempt(self, reference: mido.MidiFile):
        self.timer, self.screen = self._init_pygame()

        midi_file = mido.MidiFile()
        track = mido.MidiTrack()
        midi_file.tracks.append(track)

        start_time = time.time()
        note_start_times = {}
        last_event_time = 0

        black_keys = []
        white_keys = []

        run = True
        while run:
            print(note_start_times)
            self.timer.tick(self.fps)
            self.draw_piano()

            # Check for MIDI events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    black_key = False
                    for i in range(len(black_keys)):
                        if black_keys[i].collidepoint(event.pos):
                            self.black_sounds[i].play(0, 1000)
                            black_key = True
                            self.active_blacks[i] = 30
                    for i in range(len(white_keys)):
                        if white_keys[i].collidepoint(event.pos) and not black_key:
                            self.white_sounds[i].play(0, 3000)
                            self.active_whites[i] = 30
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RIGHT:
                        if right_oct < 8:
                            right_oct += 1
                    if event.key == pygame.K_LEFT:
                        if right_oct > 0:
                            right_oct -= 1
                    if event.key == pygame.K_UP:
                        if left_oct < 8:
                            left_oct += 1
                    if event.key == pygame.K_DOWN:
                        if left_oct > 0:
                            left_oct -= 1
            if self.midi_input.poll():
                midi_events = self.midi_input.read(10)
                current_time = time.time() - start_time
                # Process MIDI events
                for event in midi_events:
                    midi_data = event[0]
                    status, note, velocity, _ = midi_data
                    print(status, note, velocity)
                    event_time = int((current_time - last_event_time) * 1000)
                    last_event_time = current_time

                    # Map MIDI notes to piano keys here
                    # This is an example mapping; you'll need to adjust it based on your setup
                    if velocity > 0:
                        note_start_times[note] = current_time
                        track.append(
                            mido.Message(
                                "note_on", note=note, velocity=velocity, time=event_time
                            )
                        )
                        note_index = note - 21
                        note_name = self.piano_notes[note_index]
                        # piano_notes[note_index].play()

                        if note_name in self.black_notes:
                            black_index = self.black_notes.index(note_name)
                            self.black_sounds[black_index].play()
                            self.active_blacks[black_index] = 30
                        if note_name in self.white_notes:
                            white_index = self.white_notes.index(note_name)
                            self.white_sounds[white_index].play()
                            self.active_whites[white_index] = 30

                        self.active_whites[note_index] = 30
                        print(note_name)

                    elif status == 128 or velocity == 0:  # Note off
                        # Handle note off if necessary
                        print("end", note_start_times)
                        if note in note_start_times:
                            note_duration = current_time - \
                                note_start_times[note]
                            track.append(
                                mido.Message(
                                    "note_off",
                                    note=note,
                                    velocity=velocity,
                                    time=event_time,
                                )
                            )
                            del note_start_times[note]

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            midi_file.save("output.mid")
            pygame.display.flip()
        self.midi_input.close()
        pygame.midi.quit()
        pygame.quit()


# class Player:
#     def __init__(self) -> None:
#         pygame.init()
#         pygame.midi.init()
#         pygame.mixer.init()
#         # Print available MIDI devices
#         self.num_devices = pygame.midi.get_count()

#     def demo(self, midi_file: mido.MidiFile):
#         # Preparing for playback
#         pygame.init()
#         self.screen = pygame.display.set_mode([self.WIDTH, self.HEIGHT])
#         pygame.mixer.init()

#         # Processing MIDI messages
#         for message in midi_file.play():  # play() returns a generator
#             print(message)

#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     pygame.quit()
#                     return

#             if message.type == "note_on" or message.type == "note_off":
#                 note = (
#                     message.note - 21
#                 )  # Adjusting MIDI note number to our piano setup
#                 velocity = message.velocity
#                 note_name = self.piano_notes[note]

#                 if note_name in self.white_notes:
#                     white_index = self.white_notes.index(note_name)
#                     if message.type == "note_on" and velocity > 0:
#                         self.white_sounds[white_index].play()
#                         # Light up key for a short duration
#                         self.active_whites.append([white_index, 30])
#                     else:
#                         if [white_index, 30] in self.active_whites:
#                             self.active_whites.remove([white_index, 30])
#                 elif note_name in self.black_notes:
#                     black_index = self.black_notes.index(note_name)
#                     if message.type == "note_on" and velocity > 0:
#                         self.black_sounds[black_index].play()
#                         self.active_blacks.append([black_index, 30])
#                     else:
#                         if [black_index, 30] in self.active_blacks:
#                             self.active_blacks.remove([black_index, 30])

#                 self.screen.fill("gray")
#                 (
#                     self.white_keys,
#                     self.black_keys,
#                     self.active_whites,
#                     self.active_blacks,
#                 ) = self.draw_piano(self.active_whites, self.active_blacks)
#                 pygame.display.flip()
#                 # Wait for the duration of the MIDI message
#                 time.sleep(message.time)

#         pygame.quit()

#     def draw_piano(self):
#         white_key_width = 60  # New width for white keys
#         self.black_width = 34  # New width for black keys

#         white_rects = []
#         for i in range(36):
#             rect = pygame.draw.rect(
#                 self.screen, 'black', [i * white_key_width, self.HEIGHT - 300, white_key_width, 300], 0, 2)
#             white_rects.append(rect)
#             pygame.draw.rect(self.screen, 'black', [
#                 i * white_key_width, self.HEIGHT - 300, white_key_width, 300], 2, 2)
#             key_label = self.small_font.render(
#                 self.white_notes[i], True, 'black')
#             self.screen.blit(
#                 key_label, (i * white_key_width + 3, self.HEIGHT - 20))

#         skip_count = 0
#         last_skip = 2
#         skip_track = 2
#         black_rects = []
#         for i in range(25):
#             x_position = 23 + (i * white_key_width) + \
#                 (skip_count * white_key_width)
#             rect = pygame.draw.rect(self.screen, 'black', [
#                                     x_position, self.HEIGHT - 300, self.black_width, 200], 0, 2)
#             for q in range(len(self.active_blacks)):
#                 if self.active_blacks[q][0] == i:
#                     if self.active_blacks[q][1] > 0:
#                         pygame.draw.rect(self.screen, 'green', [
#                                          x_position, self.HEIGHT - 300, self.black_width, 200], 0, 2)
#                         self.active_blacks[q][1] -= 1

#             key_label = self.real_small_font.render(
#                 self.black_labels[i], True, 'white')
#             self.screen.blit(key_label, (x_position + 1, self.HEIGHT - 120))
#             black_rects.append(rect)

#             if last_skip == 2 and skip_track == 3:
#                 last_skip = 3
#                 skip_track = 0
#                 skip_count += 1
#             elif last_skip == 3 and skip_track == 2:
#                 last_skip = 2
#                 skip_track = 0
#                 skip_count += 1

#         for i in range(len(self.active_whites)):
#             if self.active_whites[i][1] > 0:
#                 j = self.active_whites[i][0]
#                 pygame.draw.rect(self.screen, 'green', [
#                     j * white_key_width, self.HEIGHT - 100, white_key_width, 100], 0, 2)
#                 self.active_whites[i][1] -= 1

#         return white_rects, black_rects

#     def record_attempt(self, reference: mido.MidiFile):
#         pygame.init()
#         pygame.mixer.init()
#         midi_file = mido.MidiFile()
#         track = mido.MidiTrack()
#         midi_file.tracks.append(track)

#         start_time = time.time()
#         note_start_times = {}
#         last_event_time = 0

#         run = True
#         while run:
#             print(note_start_times)
#             self.timer.tick(self.fps)
#             self.screen.fill("gray")
#             self.white_keys, self.black_keys, self.active_whites, self.active_blacks = (
#                 self.draw_piano(self.active_whites, self.active_blacks)
#             )
#             # Check for MIDI events
#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     run = False
#                 if event.type == pygame.MOUSEBUTTONDOWN:
#                     black_key = False
#                     for i in range(len(self.black_keys)):
#                         if self.black_keys[i].collidepoint(event.pos):
#                             self.black_sounds[i].play(0, 1000)
#                             black_key = True
#                             self.active_blacks.append([i, 30])
#                     for i in range(len(self.white_keys)):
#                         if self.white_keys[i].collidepoint(event.pos) and not black_key:
#                             self.white_sounds[i].play(0, 3000)
#                             self.active_whites.append([i, 30])
#                 if event.type == pygame.KEYDOWN:
#                     if event.key == pygame.K_RIGHT:
#                         if right_oct < 8:
#                             right_oct += 1
#                     if event.key == pygame.K_LEFT:
#                         if right_oct > 0:
#                             right_oct -= 1
#                     if event.key == pygame.K_UP:
#                         if left_oct < 8:
#                             left_oct += 1
#                     if event.key == pygame.K_DOWN:
#                         if left_oct > 0:
#                             left_oct -= 1
#             if self.midi_input.poll():
#                 midi_events = self.midi_input.read(10)
#                 current_time = time.time() - start_time
#                 # Process MIDI events
#                 for event in midi_events:
#                     midi_data = event[0]
#                     status, note, velocity, _ = midi_data
#                     print(status, note, velocity)
#                     event_time = int((current_time - last_event_time) * 1000)
#                     last_event_time = current_time

#                     # Map MIDI notes to piano keys here
#                     # This is an example mapping; you'll need to adjust it based on your setup
#                     if velocity > 0:
#                         note_start_times[note] = current_time
#                         track.append(
#                             mido.Message(
#                                 "note_on", note=note, velocity=velocity, time=event_time
#                             )
#                         )
#                         note_index = note - 21
#                         note_name = self.piano_notes[note_index]
#                         # piano_notes[note_index].play()

#                         if note_name in self.black_notes:
#                             black_index = self.black_notes.index(note_name)
#                             self.black_sounds[black_index].play()
#                             self.active_blacks.append([black_index, 30])
#                         if note_name in self.white_notes:
#                             white_index = self.white_notes.index(note_name)
#                             self.white_sounds[white_index].play()
#                             self.active_whites.append([white_index, 30])

#                         self.active_whites.append([note_index, 30])
#                         print(note_name)

#                     elif status == 128 or velocity == 0:  # Note off
#                         # Handle note off if necessary
#                         print("end", note_start_times)
#                         if note in note_start_times:
#                             note_duration = current_time - \
#                                 note_start_times[note]
#                             track.append(
#                                 mido.Message(
#                                     "note_off",
#                                     note=note,
#                                     velocity=velocity,
#                                     time=event_time,
#                                 )
#                             )
#                             del note_start_times[note]

#             for event in pygame.event.get():
#                 if event.type == pygame.QUIT:
#                     run = False
#             midi_file.save("output.mid")
#             pygame.display.flip()
#         self.midi_input.close()
#         pygame.midi.quit()
#         pygame.quit()
