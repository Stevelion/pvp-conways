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



def update_grid(grid):
    new_grid = grid.copy()
    relevants = set()
    for living in np.nonzero(grid):
        for cell in grid[living[0]-1:living[0]+1, living[1]-1:living[1]+1]:
            relevants.add(cell)
    for cell in relevants:
        new_grid[cell] = update_cell(grid[cell[0]-1:cell[0]+1, cell[1]-1:cell[1]+1])


# handle_click and find_cell are wip attempts at translating clicks to interactions with a cell
def handle_click(click, grid, cell_size = 20, border_width = 20):
    mouse_x, mouse_y = click.pos
    # determine what was clicked
    # logic to find grid clicks
    pass

def find_cell(click, grid_dimensions, cell_size = 20, border_width = 20):
    mouse_x, mouse_y = click.pos
    grid_y, grid_x = grid_dimensions[0] - 4, grid_dimensions[1] - 4
    if border_width > mouse_x < border_width + grid_x * cell_size and border_width > mouse_y < border_width + grid_y * cell_size:
        cell_x = ((mouse_x - border_width) / cell_size) - 1
        cell_y = ((mouse_y - border_width) / cell_size) - 1
        return (cell_x, cell_y)
    return


def draw_grid():
    pass




def main():
    grid = np.zeros(34,34)
    owners = {0:'', 1:'', 2:'', 3:'', 4:''}
    gamestate = 'ingame'
    run = True
    while run:
        # get events
        ev = pygame.event.get()
        for event in ev:
            if event.type == pygame.MOUSEBUTTONUP:
                target = find_cell(event, grid.shape)
                if grid[target] == 0: grid[target] = 1
                else: grid[target] = 0
        draw_grid()