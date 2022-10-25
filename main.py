import numpy as np
import pygame
import time


# owner is: 0 = dead, 1 = p1, 2 = p2, 3 = shrapnel, 4 = key/what you defend








def update_grid():
    new_grid = grid.copy()
    relevants = set()
    nonzero = np.nonzero(grid)
    alive = [(nonzero[0][n], nonzero[1][n]) for n in range(len(nonzero[0]))]
    for living in alive:
        for y in range(-1, 2):
            for x in range(-1, 2):
                relevants.add((living[0] + y, living[1] + x))
    for cell in relevants:
        new_grid[cell] = update_cell(grid[cell[0]-1:cell[0]+2, cell[1]-1:cell[1]+2])
    # clean up edges
    for n in range(2):
        new_grid[n, :] = grid[n, :] * 0
        new_grid[-n-1, :] = grid[-n-1, :] * 0
        new_grid[:, n] = grid[:, n] * 0
        new_grid[:, -n-1] = grid[:, -n-1] * 0
    return new_grid




def update_cell(kernel):
    if kernel[1,1] == 0: # if dead
        if len(np.nonzero(kernel)[0]) == 3: # become alive
            # if all the same, return it
            nonzero = np.nonzero(kernel)
            if len(set([kernel[nonzero[0][n], nonzero[1][n]] for n in range(len(nonzero[0]))])) == 1:
                return np.max(kernel)
            else: # if mixed
                return 3
        else: # stay dead
            return 0
    else: # if living
        if len(np.nonzero(kernel)[0]) in (3,4): # stay alive
            return kernel[1,1]
        else: # die
            return 0




def handle_game_events(events):
    for event in events:
        if event.type == pygame.MOUSEMOTION:
            pass # handle motion
        elif event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3):
            handle_game_click(event)
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_SPACE:
                global time_on
                time_on = not time_on # flip time_on on space press
            elif event.key == pygame.K_ESCAPE:
                open_escape()
        elif event.type == pygame.QUIT:
            global running
            running = False


def handle_game_click(click):
    """Find click target and execute"""
    mouse_x, mouse_y = click.pos
    # determine what was clicked
    # what to do if time is stopped
    if not time_on:
        # if click is within grid bounds
        if border_width < mouse_x < border_width + (grid.shape[1] - 4) * cell_size and border_width < mouse_y < border_width + (grid.shape[0] - 4) * cell_size:
            coords = [int((axis - border_width)/cell_size + 2) for axis in click.pos[::-1]]
            if click.type == pygame.MOUSEBUTTONDOWN and click.button == 1 and grid[coords[0], coords[1]] == 0: # when left click
                grid[coords[0], coords[1]] = 1
            if click.type == pygame.MOUSEBUTTONDOWN and click.button == 3:
                if grid[coords[0], coords[1]] == 1 or debug:
                    grid[coords[0], coords[1]] = 0


def open_escape():
    pass



def draw_grid():
    for x in range(grid.shape[1] - 4):
        for y in range(grid.shape[0] - 4):
            draw_x = x * cell_size + border_width
            draw_y = y * cell_size + border_width
            rect = pygame.Rect(draw_x, draw_y, cell_size - 1, cell_size - 1)
            pygame.draw.rect(window, colours[grid[y + 2, x + 2]], rect)


def init_vars():
    """initialize some vars, mostly here for alpha construction"""
    global time_on
    time_on = False
    global cell_size
    cell_size = 20 # pixels
    global border_width
    border_width = 20 # pixels
    global running
    running = True
    global tickrate
    tickrate = 0.3 # seconds
    global debug
    debug = True
    global colours
    colours = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}


def main():
    # start a game

    init_vars()


    WINDOW_WIDTH = 1000
    WINDOW_HEIGHT = 700
    global window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    window.fill((240, 240, 240)) # white background

    grid_size = 30
    grid_size += 4
    global grid
    grid = np.zeros((grid_size, grid_size))

    start_time = time.perf_counter()
    cycles = 1
    while running:
        # get events
        handle_game_events(pygame.event.get())

        if time.perf_counter() - start_time - cycles * tickrate > 0:
            cycles += 1
            if time_on:
                grid = update_grid()

        draw_grid()
        pygame.display.update()

        time.sleep(0.01)


main()