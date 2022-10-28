import numpy as np
import pygame
import time
# import subprocess # potentially for file management later

cell_size = 20 # pixels
border_width = 30 # pixels
tickrate = 0.1 # seconds
# owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
colours = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}
BUILD_COLOUR = (30, 240, 80)
DEFAULT_BUTTON_COLOUR = (180,180,180)



class Grid:
    """Abstract class that evaluates CGoL logic on an array"""
    def __init__(self, array, parent):
        self.array = array
        self.parent = parent
    
    def update_grid(self):
        """handle updating the grid with CGoL logic every game tick while time is on"""
        self.new_array = self.array.copy()
        relevants = set()
        nonzero = np.nonzero(self.array)
        alive = [(nonzero[0][n], nonzero[1][n]) for n in range(len(nonzero[0]))]
        for living in alive:
            for y in range(-1, 2):
                for x in range(-1, 2):
                    relevants.add((living[0] + y, living[1] + x))
        for cell in relevants:
            self.new_array[cell] = self.update_cell(self.array[cell[0]-1:cell[0]+2, cell[1]-1:cell[1]+2])
        # clean up edges
        for n in range(2):
            self.new_array[n, :] = self.array[n, :] * 0
            self.new_array[-n-1, :] = self.array[-n-1, :] * 0
            self.new_array[:, n] = self.array[:, n] * 0
            self.new_array[:, -n-1] = self.array[:, -n-1] * 0
        return self.new_array

    def update_cell(self, kernel):
        """basic CGoL logic for a cell
        kernel refers to the 3x3 of cells around the currently focused cell"""
        if kernel[1,1] == 0: # if dead
            if len(np.nonzero(kernel)[0]) == 3: # become alive
                # if all the same, return it
                nonzero = np.nonzero(kernel)
                if len(set([kernel[nonzero[0][n], nonzero[1][n]] for n in range(len(nonzero[0]))])) == 1:
                    return np.max(kernel)
                else: # if mixed
                    if kernel[1,1] == 4:
                        self.parent.game_over = True # this should hopefully be temporary
                    return 3
            else: # stay dead
                return 0
        else: # if living
            if len(np.nonzero(kernel)[0]) in (3,4): # stay alive
                return kernel[1,1]
            else: # die
                if kernel[1,1] == 4:
                    self.parent.game_over = True # this should hopefully be temporary
                return 0




class Game:
    """Main game class to handle events and general gameplay"""
    def __init__(self, surface, grid, build_area):
        self.surface = surface
        self.grid = Grid(grid, self)
        self.build_area = build_area
        self.time_on = False
        self.game_over = False
        self.ingame = True
        self.start_time = time.perf_counter()
        self.cycles = 1

    def main(self):
        self.surface.fill((240, 240, 240))
        pygame.draw.rect(self.surface, BUILD_COLOUR, self.build_area)
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())

            if time.perf_counter() - self.start_time - self.cycles * tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.array = self.grid.update_grid()
                    if self.game_over: self.time_on = False # stop time permanently on game end

            self.draw_grid()
            time.sleep(0.01) # events will rarely happen multiple times in 1/100 of a second
    
    def handle_events(self, events):
        """top level function to delegate events"""
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3): # left/right click
                self.handle_click(event)
            elif event.type == pygame.KEYDOWN: # various keys
                if event.key == pygame.K_SPACE:
                    if not self.game_over:
                        self.time_on = not self.time_on # flip time_on on space press
                elif event.key == pygame.K_ESCAPE: # currently returns to menu, eventually run open_escape()
                    self.ingame = False
            elif event.type == pygame.QUIT: # if x is clicked on top right of window
                pygame.quit()
                quit()
    
    def handle_click(self, click):
        """Find click target and execute"""
        # determine what was clicked
        # only do if time is stopped
        if not self.time_on:
            # if click is within build area
            if self.build_area.collidepoint(click.pos):
                coords = [int((axis - border_width)/cell_size + 2) for axis in click.pos[::-1]]
                if click.type == pygame.MOUSEBUTTONDOWN and click.button == 1 and self.grid.array[coords[0], coords[1]] == 0: # when left click
                    self.grid.array[coords[0], coords[1]] = 1 # if the clicked cell is dead, make it a player owned cell
                if click.type == pygame.MOUSEBUTTONDOWN and click.button == 3:
                    if self.grid.array[coords[0], coords[1]] == 1: # if the clicked cell is player owned, make it dead
                        self.grid.array[coords[0], coords[1]] = 0

    def draw_grid(self):
        """draw visible grid on pygame window"""
        for x in range(self.grid.array.shape[1] - 4):     # draw rectangles for each xy pair
            for y in range(self.grid.array.shape[0] - 4): # will need to be reworked if screen is made dragable
                draw_x = x * cell_size + border_width
                draw_y = y * cell_size + border_width
                rect = pygame.Rect(draw_x, draw_y, cell_size - 1, cell_size - 1)
                pygame.draw.rect(self.surface, colours[self.grid.array[y + 2, x + 2]], rect)
        pygame.display.update()

            


class LevelEditor(Game):
    """Please dear god for your sanity and mine don't try to figure this mess out
    it spent 30 minutes trying to refactor it, because it's copy and pasted code from like 3 different stages of developement"""
    def __init__(self, surface, grid, build_area):
        Game.__init__(self, surface, grid, build_area)

    def main(self):
        self.surface.fill((240, 240, 240))
        pygame.draw.rect(self.surface, BUILD_COLOUR, self.build_area)
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())

            if time.perf_counter() - self.start_time - self.cycles * tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.array = self.grid.update_grid()
            self.draw_grid()
            time.sleep(0.01)

    def handle_events(self, events):
        """I would strongly recommend not looking too hard at this. It's copy and pasted
        code from like 3 stages of developement and has almost no comments"""
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN) and event.button in (1, 3):
                mouse_x, mouse_y = event.pos
                # if click is within grid bounds
                if border_width < mouse_x < border_width + (self.grid.array.shape[1] - 4) * cell_size and border_width < mouse_y < border_width + (self.grid.array.shape[0] - 4) * cell_size:
                    coords = [int((axis - border_width)/cell_size + 2) for axis in event.pos[::-1]]
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.grid.array[coords[0], coords[1]] < 4: # increment when left click
                        self.grid.array[coords[0], coords[1]] += 1
                    if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.grid.array[coords[0], coords[1]] > 0: # decrement when right click
                        self.grid.array[coords[0], coords[1]] -= 1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if self.time_on == False:
                        self.placeholder_grid = self.grid.array.copy()
                    else:
                        self.grid.array = self.placeholder_grid
                    self.time_on = not self.time_on
                elif event.key == pygame.K_ESCAPE:
                    self.ingame = False
                elif event.key == pygame.K_s: # save as csv
                    if self.time_on:
                        np.savetxt('savedgrid.csv', self.placeholder_grid, '%1.0f', delimiter=",")
                    else:
                        np.savetxt('savedgrid.csv', self.grid.array, '%1.0f', delimiter=",")
            elif event.type == pygame.QUIT:
                pygame.quit()
                quit()




class Button(): # parent class for menu buttons
    def __init__(self, name, rect, colour = DEFAULT_BUTTON_COLOUR):
        self.name = name
        self.rect = pygame.Rect(rect)
        self.colour = colour
        pygame.font.init() # initialize and set font for label, will be removed later and replaced with graphics
        self.font = pygame.font.SysFont('Arial', 25)

    def draw(self, surface):
        pygame.draw.rect(surface, self.colour, self.rect)
        surface.blit(self.font.render(self.name, True, (0,0,0)), self.rect[0:2])


class LevelSelectButton(Button):
    def __init__(self, name, rect, colour=DEFAULT_BUTTON_COLOUR):
        Button.__init__(self, name, rect, colour)

    def function(self): # function to execute when button is clicked
        level_select.main()


class LevelEditorButton(Button):
    def __init__(self, name, rect, colour=DEFAULT_BUTTON_COLOUR):
        Button.__init__(self, name, rect, colour)

    def function(self): # function to execute when button is clicked
        level_editor = LevelEditor(window, np.zeros((34, 34)), pygame.Rect(border_width + cell_size*15, border_width, cell_size*15 - 1, cell_size*15 - 1))
        level_editor.main()
    

class EmptyLevelButton(Button):
    def __init__(self, name, rect, colour=DEFAULT_BUTTON_COLOUR):
        Button.__init__(self, name, rect, colour)

    def function(self): # function to execute when button is clicked
        game = Game(window, np.zeros((34, 34)), pygame.Rect(border_width, border_width, cell_size*30 - 1, cell_size*30 - 1))
        game.main()


class LevelButton(Button): # child class for buttons in level select submenu
    def __init__(self, name, rect, filename, colour = DEFAULT_BUTTON_COLOUR):
        Button.__init__(self, name, rect, colour)
        self.filename = filename
        
    def function(self): # function to execute when button is clicked
        if self.filename == None: return
        game = Game(window , np.genfromtxt('levels/' + self.filename, delimiter=','), pygame.Rect(border_width + cell_size*15, border_width, cell_size*15 - 1, cell_size*15 - 1))
        game.main()




class Menu:
    """Abstract menu class"""
    def __init__(self, surface, buttons):
        self.buttons = buttons
        self.surface = surface

    def main(self): # main event loop
        self.draw()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                    # find button and execute it's function
                    for button in self.buttons:
                        if button.rect.collidepoint(event.pos):
                            button.function()
                    self.draw()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            time.sleep(0.01)

    def draw(self):
        """draw menu with buttons"""
        self.surface.fill((240, 240, 240))
        for button in self.buttons:
            button.draw(self.surface)
        pygame.display.update()


class MainMenu(Menu):
    def __init__(self, surface):
        Menu.__init__(self, surface, self.init_buttons())

    def init_buttons(self): # creates all buttons in the menu and returns them
        return (
            LevelSelectButton('Singleplayer', (280,200,100,50)),
            LevelEditorButton('Level Editor', (280,260,100,50)),
            EmptyLevelButton('Sandbox', (280,320,100,50))
        )


class LevelSelect(Menu):
    def __init__(self, surface):
        Menu.__init__(self, surface, self.init_buttons())

    def init_buttons(self): # creates all buttons in the menu and returns them
        return (
            LevelButton('Demo', (200,200,100,50), 'demo.csv'),
            LevelButton('Level 1', (200,260,100,50), 'level_1.csv'),
            LevelButton('Level 2', (200,320,100,50), 'level_2.csv'),
            LevelButton('Level 3', (360,200,100,50), 'level_3.csv'),
            LevelButton('Unused', (360,260,100,50), None),
            LevelButton('Unused', (360,320,100,50), None)
        )



WINDOW_WIDTH = 660
WINDOW_HEIGHT = 660
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
window.fill((240, 240, 240)) # white background

level_select = LevelSelect(window)
main_menu = MainMenu(window)

main_menu.main()
