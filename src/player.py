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


class Player:
    def __init__(self) -> None:
        pygame.midi.init()
        # Print available MIDI devices
        self.num_devices = pygame.midi.get_count()
        print("Available MIDI devices:")
        for i in range(self.num_devices):
            info = pygame.midi.get_device_info(i)
            device_type = "Input" if info[2] == 1 else "Output"
            print(f"Device ID {i}: {info[1].decode()} ({device_type})")

        # Open a MIDI input port
        # You'll need to set this device_id based on the printed list of available devices
        device_id = int(input("Enter the Device ID to use: "))
        self.midi_input = pygame.midi.Input(device_id)

        pygame.init()
        pygame.mixer.set_num_channels(50)
        self.font = pygame.font.Font("assets/OldStandardTT-Bold.ttf", 48)
        self.medium_font = pygame.font.Font("assets/OldStandardTT-Bold.ttf", 28)
        self.small_font = pygame.font.Font("assets/OldStandardTT-Bold.ttf", 16)
        self.real_small_font = pygame.font.Font("assets/OldStandardTT-Bold.ttf", 10)
        self.fps = 60
        self.timer = pygame.time.Clock()
        self.WIDTH = 52 * 35
        self.HEIGHT = 400
        self.screen = pygame.display.set_mode([self.WIDTH, self.HEIGHT])
        self.white_sounds = []
        self.black_sounds = []
        self.active_whites = []
        self.active_blacks = []
        self.left_oct = 4
        self.right_oct = 5

        for i in range(len(self.white_notes)):
            self.white_sounds.append(
                mixer.Sound(f"assets\\notes\\{self.white_notes[i]}.wav")
            )

        for i in range(len(self.black_notes)):
            self.black_sounds.append(
                mixer.Sound(f"assets\\notes\\{self.black_notes[i]}.wav")
            )

    def demo():
        pass

    def draw_piano(self, whites, blacks):
        white_rects = []
        for i in range(36):
            rect = pygame.draw.rect(
                self.screen, "white", [i * 35, self.HEIGHT - 300, 35, 300], 0, 2
            )
            white_rects.append(rect)
            pygame.draw.rect(
                self.screen, "black", [i * 35, self.HEIGHT - 300, 35, 300], 2, 2
            )
            key_label = self.small_font.render(self.white_notes[i], True, "black")
            self.screen.blit(key_label, (i * 35 + 3, self.HEIGHT - 20))
        skip_count = 0
        last_skip = 2
        skip_track = 2
        black_rects = []
        for i in range(25):
            rect = pygame.draw.rect(
                self.screen,
                "black",
                [23 + (i * 35) + (skip_count * 35), self.HEIGHT - 300, 24, 200],
                0,
                2,
            )
            for q in range(len(blacks)):
                if blacks[q][0] == i:
                    if blacks[q][1] > 0:
                        pygame.draw.rect(
                            self.screen,
                            "green",
                            [
                                23 + (i * 35) + (skip_count * 35),
                                self.HEIGHT - 300,
                                24,
                                200,
                            ],
                            0,
                            2,
                        )
                        blacks[q][1] -= 1

            key_label = self.real_small_font.render(self.black_labels[i], True, "white")
            self.screen.blit(
                key_label, (25 + (i * 35) + (skip_count * 35), self.HEIGHT - 120)
            )
            black_rects.append(rect)
            skip_track += 1
            if last_skip == 2 and skip_track == 3:
                last_skip = 3
                skip_track = 0
                skip_count += 1
            elif last_skip == 3 and skip_track == 2:
                last_skip = 2
                skip_track = 0
                skip_count += 1

        for i in range(len(whites)):
            if whites[i][1] > 0:
                j = whites[i][0]
                pygame.draw.rect(
                    self.screen, "green", [j * 35, self.HEIGHT - 100, 35, 100], 0, 2
                )
                whites[i][1] -= 1

        return white_rects, black_rects, whites, blacks

    def record_attempt(self):
        run = True
        while run:
            self.timer.tick(self.fps)
            self.screen.fill("gray")
            self.white_keys, self.black_keys, self.active_whites, self.active_blacks = (
                self.draw_piano(self.active_whites, self.active_blacks)
            )
            # Check for MIDI events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
                if event.type == pygame.MOUSEBUTTONDOWN:
                    black_key = False
                    for i in range(len(self.black_keys)):
                        if self.black_keys[i].collidepoint(event.pos):
                            self.black_sounds[i].play(0, 1000)
                            black_key = True
                            self.active_blacks.append([i, 30])
                    for i in range(len(self.white_keys)):
                        if self.white_keys[i].collidepoint(event.pos) and not black_key:
                            self.white_sounds[i].play(0, 3000)
                            self.active_whites.append([i, 30])
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
                # Process MIDI events
                for event in midi_events:
                    midi_data = event[0]
                    status, note, velocity, _ = midi_data
                    print(status, note, velocity)

                    # Map MIDI notes to piano keys here
                    # This is an example mapping; you'll need to adjust it based on your setup
                    if velocity > 0:
                        note_index = note - 21
                        note_name = self.piano_notes[note_index]
                        # piano_notes[note_index].play()

                        if note_name in self.black_notes:
                            black_index = self.black_notes.index(note_name)
                            self.black_sounds[black_index].play()
                            self.active_blacks.append([black_index, 30])
                        if note_name in self.white_notes:
                            white_index = self.white_notes.index(note_name)
                            self.white_sounds[white_index].play()
                            self.active_whites.append([white_index, 30])

                        self.active_whites.append([note_index, 30])
                        print(note_name)

                    elif status == 128:  # Note off
                        # Handle note off if necessary
                        pass
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    run = False
            pygame.display.flip()
        self.midi_input.close()
        pygame.midi.quit()
        pygame.quit()
