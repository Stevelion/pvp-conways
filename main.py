import numpy as np
import pygame
import time
# import subprocess # potentially for file management later



def init_vars():
    """initialize some vars, mostly here for alpha development"""
    global cell_size, border_width, tickrate, colours, GREY
    cell_size = 20 # pixels
    border_width = 30 # pixels
    tickrate = 0.1 # seconds
    # owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
    colours = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}
    GREY = (180,180,180)



def update_grid():
    """handle updating the grid with CGoL logic every game tick while time is on"""
    global new_grid
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
    """basic CGoL logic for a cell
    kernel refers to the 3x3 of cells around the currently focused cell"""
    global game_over
    if kernel[1,1] == 0: # if dead
        if len(np.nonzero(kernel)[0]) == 3: # become alive
            # if all the same, return it
            nonzero = np.nonzero(kernel)
            if len(set([kernel[nonzero[0][n], nonzero[1][n]] for n in range(len(nonzero[0]))])) == 1:
                return np.max(kernel)
            else: # if mixed
                if kernel[1,1] == 4:
                    game_over = True
                return 3
        else: # stay dead
            return 0
    else: # if living
        if len(np.nonzero(kernel)[0]) in (3,4): # stay alive
            return kernel[1,1]
        else: # die
            if kernel[1,1] == 4:
                game_over = True
            return 0




def handle_game_events(events):
    """top level function to delegate events"""
    for event in events:
        if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3): # left/right click
            handle_game_click(event)
        elif event.type == pygame.KEYDOWN: # various keys
            if event.key == pygame.K_SPACE:
                if not game_over:
                    global time_on
                    time_on = not time_on # flip time_on on space press
            elif event.key == pygame.K_ESCAPE: # currently returns to menu, eventually run open_escape()
                global ingame
                ingame = False
        elif event.type == pygame.QUIT: # if x is clicked on top right of window
            pygame.quit()
            quit()


def handle_game_click(click):
    """Find click target and execute"""
    mouse_x, mouse_y = click.pos
    # determine what was clicked
    # only do if time is stopped
    if not time_on:
        # if click is within grid bounds
        if border_width < mouse_x < border_width + (grid.shape[1] - 4) * cell_size and border_width < mouse_y < border_width + (grid.shape[0] - 4) * cell_size:
            coords = [int((axis - border_width)/cell_size + 2) for axis in click.pos[::-1]]
            if click.type == pygame.MOUSEBUTTONDOWN and click.button == 1 and grid[coords[0], coords[1]] == 0: # when left click
                grid[coords[0], coords[1]] = 1 # if the clicked cell is dead, make it a player owned cell
            if click.type == pygame.MOUSEBUTTONDOWN and click.button == 3:
                if grid[coords[0], coords[1]] == 1: # if the clicked cell is player owned, make it dead
                    grid[coords[0], coords[1]] = 0


def open_escape():
    """open menu on esc key press"""
    # nonfunctional -  eventually for potential escape menu ingame
    pass



def draw_grid():
    """draw visible grid on pygame window"""
    for x in range(grid.shape[1] - 4):     # draw rectangles for each xy pair
        for y in range(grid.shape[0] - 4): # will need to be reworked if screen is made dragable
            draw_x = x * cell_size + border_width
            draw_y = y * cell_size + border_width
            rect = pygame.Rect(draw_x, draw_y, cell_size - 1, cell_size - 1)
            pygame.draw.rect(window, colours[grid[y + 2, x + 2]], rect)



def game(board = np.zeros((34, 34))):
    """start a game"""
    # initialize basic game functions
    global ingame, game_over, time_on
    ingame = True
    game_over = False
    time_on = False
    global grid
    grid = board

    start_time = time.perf_counter() # record when the game started to handle grid updates
    cycles = 1                       # when time is on
    while ingame:
        # get events
        handle_game_events(pygame.event.get())

        if time.perf_counter() - start_time - cycles * tickrate > 0: # true every 'tickrate' seconds
            cycles += 1
            if time_on: # only run update logic if time is turned on
                grid = update_grid()
                if game_over: time_on = False # stop time permanently on game end

        draw_grid()
        pygame.display.update()
        time.sleep(0.01) # events will rarely happen multiple times in 1/100 of a second



def level_edit():
    """quickly bashed together level editor that prints grid to console
    press s to save current grid as csv, does not have any update logic so space does nothing (intended)
    mostly copy and paste from other funcs, purpose is to have a basic level editor to build test boards"""
    global ingame, saved_grid
    ingame = True
    global grid
    grid = np.zeros((34, 34))
    while ingame:
        # get events
        events = pygame.event.get()
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3):
                mouse_x, mouse_y = event.pos
                # if click is within grid bounds
                if border_width < mouse_x < border_width + (grid.shape[1] - 4) * cell_size and border_width < mouse_y < border_width + (grid.shape[0] - 4) * cell_size:
                    coords = [int((axis - border_width)/cell_size + 2) for axis in event.pos[::-1]]
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and grid[coords[0], coords[1]] < 4: # increment when left click
                        grid[coords[0], coords[1]] += 1
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and grid[coords[0], coords[1]] > 0: # decrement when right click
                        grid[coords[0], coords[1]] -= 1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    ingame = False
                elif event.key == pygame.K_s: # save as csv
                    np.savetxt('savedgrid.csv', grid, '%1.0f', delimiter=",")
            elif event.type == pygame.QUIT:
                pygame.quit()
                quit()
        draw_grid()
        pygame.display.update()
        time.sleep(0.01)


class Button(): # parent class for menu buttons
    def __init__(self, rect, function, colour = GREY):
        self.rect = rect
        self.function = function
        self.colour = colour
    def draw(self, surface = window):
        pygame.draw.rect(window, self.colour, self.rect)

class LevelButton(Button): # child class for buttons in level select submenu
    def __init__(self, rect, filename, colour = GREY):
        Button.__init__(self, rect, None, colour)
        self.filename = filename
    def load(self):
        game(np.genfromtxt('levels/' + self.filename, delimiter=','))


def init_buttons():
    # initialize some button objects to easily draw them when a menu is active
    global singleplayer_button, level_editor, demo
    global level_1, level_2, level_3, level_4, level_5
    # main menu buttons with bounds and submenu function
    singleplayer_button = Button((280,200,100,50), level_select)
    level_editor = Button(((280,260,100,50)), level_edit)
    # level select buttons with bounds and filename to load
    demo = LevelButton((200,200,100,50), 'demo.csv')
    level_1 = LevelButton((200,260,100,50), 'basic_level.csv')
    level_2 = LevelButton((200,320,100,50), None)
    level_3 = LevelButton((360,200,100,50), None)
    level_4 = LevelButton((360,260,100,50), None)
    level_5 = LevelButton((360,320,100,50), None)


def draw_main_menu():
    """draw main menu with singleplayer, custom level/level editor, settings"""
    window.fill((240, 240, 240))
    pygame.draw.rect(window, GREY, (280,200,100,50))
    pygame.display.update()


def draw_level_select():
    """level select screen with buttons for each level"""
    window.fill((240, 240, 240))
    pygame.display.update()


def menu():
    """top level for menu"""
    # initialize button objects
    draw_main_menu()
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3):
                # logic to find click target
                game()
                draw_main_menu()
                
            elif event.type == pygame.QUIT:
                pygame.quit()
                quit()
        time.sleep(0.01)


def level_select():
    """submenu for level select"""
    draw_level_select()
    while True:
        events = pygame.event.get()
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3):
                # logic to find click target
                pass
                
            elif event.type == pygame.QUIT:
                pygame.quit()
                quit()
        time.sleep(0.01)



def main():
    init_vars()
    WINDOW_WIDTH = 660
    WINDOW_HEIGHT = 660
    global window
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    window.fill((240, 240, 240)) # white background

    # menu()
    
    # level_edit()
    board = np.genfromtxt('levels/demo.csv', delimiter=',')
    # board = np.genfromtxt('levels/basic_level.csv', delimiter=',')
    game(board)


main() # at the top of the script are some init vars including tickrate (in seconds)