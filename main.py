import numpy as np
import pygame
import time
import gridfont
# import subprocess # potentially for file management later

cell_size = 20 # pixels
border_width = 30 # pixels
tickrate = 0.1 # seconds
# owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
COLOURS = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}
BUILD_COLOUR = (30, 240, 80)
DEFAULT_BUTTON_COLOUR = (180,180,180)
BACKGROUND_COLOUR = (240,240,240)
BLACK = (0,0,0)



class Grid:
    """Abstract class that evaluates CGoL logic on an array"""
    def __init__(self, array, parent):
        self.array = array
        self.parent = parent
    
    def update_grid(self):
        """handle updating the grid with CGoL logic every game tick while time is on"""
        self.new_array = self.array.copy()
        relevants = set()
        nonzero = np.nonzero(self.array) # find living (nonzero) cells
        alive = [(nonzero[0][n], nonzero[1][n]) for n in range(len(nonzero[0]))] # convert np.nonzero output into list of coordinate tuples
        for living in alive: # find all cells adjacent to a living cell
            for y in range(-1, 2):
                for x in range(-1, 2):
                    relevants.add((living[0] + y, living[1] + x))
        for cell in relevants:
            self.new_array[cell] = self.update_cell(self.array[cell[0]-1:cell[0]+2, cell[1]-1:cell[1]+2]) # pass 3x3 around cell to update_cell()
        # clean up edges
        for n in range(2):
            self.new_array[n, :] = self.array[n, :] * 0
            self.new_array[-n-1, :] = self.array[-n-1, :] * 0
            self.new_array[:, n] = self.array[:, n] * 0
            self.new_array[:, -n-1] = self.array[:, -n-1] * 0
        self.array = self.new_array

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
        self.cycles = 1

    def main(self):
        self.start_time = time.perf_counter()
        self.surface.fill(BACKGROUND_COLOUR)
        pygame.draw.rect(self.surface, BUILD_COLOUR, self.build_area)
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())
            if time.perf_counter() - self.start_time - self.cycles * tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.update_grid()
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
                pygame.draw.rect(self.surface, COLOURS[self.grid.array[y + 2, x + 2]], rect)
        pygame.display.update()

            


class LevelEditor(Game):
    """Please dear god for your sanity and mine don't try to figure this mess out
    it spent 30 minutes trying to refactor it, because it's copy and pasted code from like 3 different stages of developement"""
    def __init__(self, surface, grid, build_area):
        Game.__init__(self, surface, grid, build_area)

    def main(self):
        self.surface.fill(BACKGROUND_COLOUR)
        pygame.draw.rect(self.surface, BUILD_COLOUR, self.build_area)
        self.start_time = time.perf_counter()
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())

            if time.perf_counter() - self.start_time - self.cycles * tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.update_grid()
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




class LifeButton():
    """Abstract class for buttons that collapse into Conway's Game of Life sims when hovered"""
    def __init__(self, rect, grid, cell_size = 5, background = DEFAULT_BUTTON_COLOUR):
        self.rect = pygame.Rect(rect)
        self.grid = Grid(grid, self)
        self.background = background
        self.game_over = False
        self.hovered = False
        self.cell_size = cell_size
        self.colours = COLOURS
    
    def function(self):
        self.hovered = False
        self.grid.array = self.placeholder_grid

    def update(self):
        self.grid.update_grid()
    
    def hover(self, event):
        if not self.hovered and self.rect.collidepoint(event.pos): # if it wasn't hovered and now is
            self.hovered = True
            self.placeholder_grid = self.grid.array
        elif self.hovered and not self.rect.collidepoint(event.pos): # if it was hovered and now isn't
            self.hovered = False
            self.grid.array = self.placeholder_grid

    def draw(self, surface):
        for x in range(self.grid.array.shape[1] - 10):     # draw rectangles for each xy pair
            for y in range(self.grid.array.shape[0] - 10): # will need to be reworked if screen is made dragable
                draw_x = x * self.cell_size + self.rect[0]
                draw_y = y * self.cell_size + self.rect[1]
                rect = pygame.Rect(draw_x, draw_y, self.cell_size, self.cell_size)
                pygame.draw.rect(surface, self.colours[self.grid.array[y + 5, x + 5]], rect)



class LifeTextBox(LifeButton):
    def __init__(self, text, rect, cell_size = 2, background = DEFAULT_BUTTON_COLOUR):
        grid_width = rect[2] // cell_size - 4
        grid = font.arrange(text, grid_width)
        grid = font.expand_grid(grid, (grid.shape[1] + 14, grid.shape[0] + 14))
        np.savetxt('savedgrid.csv', grid, '%1.0f', delimiter=",")
        LifeButton.__init__(self, rect, grid, cell_size, background)

    def function():
        return




class LifeMenu:
    """Abstract menu class for containing and updating LifeButtons"""
    def __init__(self, surface, background, buttons):
        self.surface = surface
        self.buttons = buttons
        self.background = background
        self.tickrate = 0.1

    def main(self): # main event loop
        self.restart_timer()
        self.draw()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.MOUSEMOTION: # find if mouse motion involved hovering or unhovering a button
                    for button in self.buttons:
                        button.hover(event)
                if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                    # find button and execute it's function
                    for button in self.buttons:
                        if button.rect.collidepoint(event.pos):
                            button.function()
                    self.restart_timer()
                    self.draw()
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        return
                elif event.type == pygame.QUIT:
                    pygame.quit()
                    quit()
            if time.perf_counter() - self.start_time - self.cycles * self.tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                for button in self.buttons:
                    if button.hovered:
                        button.update()
                self.draw()
            time.sleep(0.01)
    
    def restart_timer(self):
        """restart update timer"""
        self.start_time = time.perf_counter()
        self.cycles = 1

    def draw(self):
        """draw menu with buttons"""
        self.surface.fill(self.background)
        for button in self.buttons:
            button.draw(self.surface)
        pygame.display.update()



class LevelSelectButton(LifeButton):
    def __init__(self):
        text = 'Singleplayer'
        rect = (165,170,330,75)
        grid = font.as_grid(text)
        grid = font.expand_grid(grid, (76,25))
        LifeButton.__init__(self, rect, grid)

    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        level_select.main()


class LevelEditorButton(LifeButton):
    def __init__(self):
        text = 'Level Editor'
        rect = (165,275,330,75)
        grid = font.as_grid(text)
        grid = font.expand_grid(grid, (76,25))
        LifeButton.__init__(self, rect, grid)

    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        level_editor = LevelEditor(window, np.zeros((34, 34)), pygame.Rect(border_width + cell_size*15, border_width, cell_size*15 - 1, cell_size*15 - 1))
        level_editor.main()
    

class SandboxButton(LifeButton):
    def __init__(self):
        text = 'Sandbox'
        rect = (165,380,330,75)
        grid = font.as_grid(text)
        grid = font.expand_grid(grid, (76,25))
        LifeButton.__init__(self, rect, grid)

    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        game = Game(window, np.zeros((34, 34)), pygame.Rect(border_width, border_width, cell_size*30 - 1, cell_size*30 - 1))
        game.main()


class LevelButton(LifeButton): # child class for buttons in level select submenu
    def __init__(self, text, rect, filename):
        grid = font.as_grid(text)
        grid = font.expand_grid(grid, (60,25))
        LifeButton.__init__(self, rect, grid)
        self.filename = filename
        
    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        if self.filename == None: return
        game = Game(window , np.genfromtxt('levels/' + self.filename, delimiter=','), pygame.Rect(border_width + cell_size*15, border_width, cell_size*15 - 1, cell_size*15 - 1))
        game.main()



class MainMenu(LifeMenu):
    def __init__(self, surface):
        LifeMenu.__init__(self, surface, BLACK, self.init_buttons())

    def init_buttons(self): # creates all buttons in the menu and returns them
        return (
            LevelSelectButton(),
            LevelEditorButton(),
            SandboxButton(),
            LifeTextBox("Welcome to the Game of Life",
                        (196,40,268,28), cell_size=2)
        )


class LevelSelect(LifeMenu):
    def __init__(self, surface):
        LifeMenu.__init__(self, surface, BLACK, self.init_buttons())

    def init_buttons(self): # creates all buttons in the menu and returns them
        return (
            LevelButton('Demo', (60,180,250,75), 'demo.csv'),
            LevelButton('Level 1', (60,295,250,75), 'level_1.csv'),
            LevelButton('Level 2', (60,400,250,75), 'level_2.csv'),
            LevelButton('Level 3', (350,180,250,75), 'level_3.csv'),
            LevelButton('Unused', (350,295,250,75), None),
            LevelButton('Unused', (350,400,250,75), None)
        )



WINDOW_WIDTH = 660
WINDOW_HEIGHT = 660
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
window.fill(BACKGROUND_COLOUR)

font = gridfont.Font()

level_select = LevelSelect(window)
main_menu = MainMenu(window)

main_menu.main()
