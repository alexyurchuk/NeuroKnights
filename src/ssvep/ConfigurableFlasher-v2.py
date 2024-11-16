# src / ssvep / ConfigurableFlasher-v2.py

"""
Summary:

Steady-State Visual Evoked Potential (SSVEP) Flicker Stimulus Generator. 
It uses Pygame to create full-screen flickering stimuli as data analysis for inputs in chess. 
The flicker frequencies and durations are configurable, enabling mutiple different visual 
stimuli affect the user's brain activity to map different user inputs (WASD).

Author(s): Jessu Doroy, Ivan Costa Neto
Commenter(s): Ivan Costa Neto
Last Updated: Nov. 16, 2024
"""

import pygame
import time

# initialize Pygame
pygame.init()

# full-screen setup
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)  # fullscreen mode
screen_width, screen_height = screen.get_size()  # get screen dimensions
pygame.display.set_caption("SSVEP Chess WASD Movement Flashing Boxes")

# colors
white = (255, 255, 255)
black = (0, 0, 0)

# fonts
font = pygame.font.SysFont("arial", 48, bold=True)

# box dimensions and spacing
box_width = 200
box_height = 200
spacing_multiplier = 1.8  # multiplies the gap between boxes (prevent peripheral vision in EEG data)
gap = box_width * spacing_multiplier

# positioning boxes for W, A, S, D (chess directions)
positions = {
    "W": ((screen_width - box_width) // 2, (screen_height - box_height) // 1.3 - gap),  # up
    "A": ((screen_width - box_width) // 2 - gap, (screen_height - box_height) // 1.3),  # left
    "S": ((screen_width - box_width) // 2, (screen_height - box_height) // 1.3),  # down
    "D": ((screen_width - box_width) // 2 + gap, (screen_height - box_height) // 1.3)  # right
}

# frequencies for each box (in Hz)
frequencies = {
    "W": 4,  # up: 4 Hz
    "A": 8,  # left: 8 Hz
    "S": 12,  # down: 12 Hz
    "D": 16  # right: 16 Hz
}

# directional labels
labels = {
    "W": "Up",
    "A": "Left",
    "S": "Down",
    "D": "Right"
}

# state of each box (on/off) and their last toggle times
states = {key: False for key in positions}
last_toggle_times = {key: time.time() for key in positions}

# main loop
running = True
clock = pygame.time.Clock()

while running:
    current_time = time.time()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:  # exit on Esc key
            running = False

    # update flashing states based on frequencies
    for key in positions:
        interval = 1 / (2 * frequencies[key])  # time for one on/off cycle
        if current_time - last_toggle_times[key] >= interval:
            states[key] = not states[key]  # toggle state
            last_toggle_times[key] = current_time  # reset toggle time

    # fill the screen with black
    screen.fill(black)

    # draw the boxes based on their states
    for key, pos in positions.items():
        # draw flashing box
        if states[key]:  # box is "on"
            pygame.draw.rect(screen, white, (*pos, box_width, box_height), 0)
        else:  # box is "off"
            pygame.draw.rect(screen, black, (*pos, box_width, box_height), 0)

        # draw border for all boxes
        pygame.draw.rect(screen, white, (*pos, box_width, box_height), 5)

        # add text label with black font
        label_surface = font.render(labels[key], True, black)
        label_rect = label_surface.get_rect(center=(pos[0] + box_width // 2, pos[1] + box_height // 2))
        screen.blit(label_surface, label_rect)

    # update the display
    pygame.display.flip()

    # limit frame rate
    clock.tick(60)

# quit Pygame
pygame.quit()
