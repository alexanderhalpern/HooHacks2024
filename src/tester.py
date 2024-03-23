import pygame
import os

# Initialize Pygame
pygame.init()

# Constants
WHITE_KEY_WIDTH = 60
WHITE_KEY_HEIGHT = 200
BLACK_KEY_WIDTH = 40
BLACK_KEY_HEIGHT = 120
NUM_WHITE_KEYS = 52  # Number of white keys from C2 to C7
SCREEN_WIDTH = WHITE_KEY_WIDTH * NUM_WHITE_KEYS
SCREEN_HEIGHT = WHITE_KEY_HEIGHT

# Create a window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pygame Piano")

# Load piano sounds
sounds = {}
for note in ['C', 'D', 'E', 'F', 'G', 'A', 'B']:
    for octave in range(2, 8):
        sound_file = f'{note}{octave}.wav'  # Example: C2.wav, D2.wav, ...
        if os.path.exists(sound_file):
            sounds[f'{note}{octave}'] = pygame.mixer.Sound(sound_file)


def draw_piano(screen):
    # Draw white keys
    for i in range(NUM_WHITE_KEYS):
        rect = (i * WHITE_KEY_WIDTH, 0, WHITE_KEY_WIDTH, WHITE_KEY_HEIGHT)
        pygame.draw.rect(screen, (255, 255, 255), rect, 0)
        pygame.draw.rect(screen, (0, 0, 0), rect, 1)

    # Draw black keys
    black_key_positions = []
    for i in range(NUM_WHITE_KEYS - 1):  # -1 to avoid adding a black key at the end
        if i % 7 not in [2, 6]:  # Skip where there are no black keys
            black_key_positions.append(i)

    for pos in black_key_positions:
        rect = ((pos + 0.75) * WHITE_KEY_WIDTH, 0,
                BLACK_KEY_WIDTH, BLACK_KEY_HEIGHT)
        pygame.draw.rect(screen, (0, 0, 0), rect, 0)


# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill((0, 0, 0))
    draw_piano(screen)
    pygame.display.flip()

pygame.quit()
