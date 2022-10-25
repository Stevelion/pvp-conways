import numpy as np
import pygame

# grid dimension 2 length 2, [0] is living or dead value and [1] is owner value
# owner is: 0 = dead, 1 = p1, 2 = p2, 3 = shrapnel, 4 = key/what you defend




def update_cell(kernel):
    if kernel[1,1] == 0: # if dead
        if len(np.nonzero(kernel)) == 3:
            # become alive
            if len(set([kernel[xy] for xy in np.nonzero(kernel)])) == 1: # if all the same, return it
                return np.max(kernel)
            else: # if mixed
                return 3
        else: # stay dead
            return 0
    else: # if living
        if len(np.nonzero(kernel)) in (3,4): # stay alive
            return kernel[1,1]
        else: # die
            return 0


def update_grid():
    new_grid = grid.copy()
    relevants = set()
    for living in np.nonzero(grid):
        for cell in grid[living[0]-1:living[0]+1, living[1]-1:living[1]+1]:
            relevants.add(cell)
    for cell in relevants:
        new_grid[cell] = update_cell(grid[cell[0]-1:cell[0]+1, cell[1]-1:cell[1]+1])




def click_grid(coords):
    """If grid is clicked, find which cell and operate on that cell"""
    coords = coords[::-1] # reversed because numpy uses reversed coords
    if grid[coords] == 0: grid[coords] = 1
    else: grid[coords] = 0


def handle_click(click):
    """Find click target and execute"""
    mouse_x, mouse_y = click.pos
    global right_drag
    # determine what was clicked
    if not time: # what to do if time is stopped
        if click.button == 2 and click.type == pygame.MOUSEBUTTONUP:
            right_drag = False
        # if click is on grid
        if border_width > mouse_x < border_width + grid.shape[1] - 4 * cell_size and border_width > mouse_y < border_width + grid.shape[0] - 4 * cell_size:
            if click.button == 1 and click.type == pygame.MOUSEBUTTONUP: # when left click
                click_grid([(axis - border_width)/cell_size for axis in click.pos])
            if click.button == 2 and click.type == pygame.MOUSEBUTTONDOWN: # when right click down
                right_drag = True


def handle_game_events(events):
    for event in events:
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_SPACE:
                    time = not time # flip time on space press
                    global right_drag
                    right_drag = False # safety to catch hitting space without mouseup
                if event.key == pygame.K_ESCAPE:
                    pass # open escape menu
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
                handle_click(event)
            if event.type == pygame.MOUSEMOTION:
                pass





def draw_grid():
    pass




def main():
    # start a game

    # initialize some vars
    global time
    time = False
    global right_drag
    right_drag = False
    global cell_size
    cell_size = 20
    global border_width
    border_width = 20

    gamestate = 'ingame'

    global grid
    grid = np.zeros(34,34)
    while gamestate == 'ingame':
        # get events
        handle_game_events(pygame.event.get())
        draw_grid()