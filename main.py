import numpy as np
import pygame
import json
from gridfont import font
from lifegui import LifeTextBox, LifeButton, LifeMenu
from game import Game, LevelEditor
# import subprocess # potentially for file management later

# owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
COLOURS = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}
# some temporary colour definitions for easier GUI dev
BLACK, RED, GREEN, BLUE = (0,0,0), (255, 0, 0), (0,255,0), (0,0,255)



# Define buttons
class LevelSelectButton(LifeButton):
    def __init__(self):
        text = 'Singleplayer'
        rect = (165,170,330,75)
        LifeButton.__init__(self, text, rect)

    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        level_select.main()


class LevelEditorButton(LifeButton):
    def __init__(self):
        text = 'Level Editor'
        rect = (165,275,330,75)
        LifeButton.__init__(self, text, rect)

    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        array = np.zeros((13,40))
        build_area = (((0,0), (0,0)),)
        level_editor = LevelEditor(window, array, build_area=build_area, cell_size=50)
        level_editor.main()
    

class SandboxButton(LifeButton):
    def __init__(self):
        text = 'Sandbox'
        rect = (165,380,330,75)
        LifeButton.__init__(self, text, rect)

    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        game = Game(window, np.zeros((124, 124)), cell_size=20)
        game.main()


class LevelButton(LifeButton): # child class for buttons in level select submenu
    def __init__(self, text, rect, filename):
        LifeButton.__init__(self, text, rect)
        self.filename = filename
        
    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        if self.filename == None: return
        # run game with array loaded from csv file
        with open('levels/' + self.filename + '.json', 'r') as f:
            self.setup = json.load(f)
        game = Game(window , np.genfromtxt('levels/' + self.setup['array'], delimiter=','), build_area = self.setup['build_area'])
        game.main()


# Define menus
class MainMenu(LifeMenu):
    def __init__(self, surface):
        LifeMenu.__init__(self, surface, BLACK, self.init_buttons())

    def init_buttons(self): # creates all buttons in the menu and returns them
        return (
            LevelSelectButton(),
            LevelEditorButton(),
            SandboxButton(),
            LifeTextBox("Welcome to the Game of Life",
                        (196,40,268,28), cell_size=2, background = BLACK,
                        cell_colour = GREEN, centered=True),
            TestButton()
        )


class LevelSelect(LifeMenu):
    def __init__(self, surface):
        LifeMenu.__init__(self, surface, BLACK, self.init_buttons())

    def init_buttons(self): # creates all buttons in the menu and returns them
        return (
            LevelButton('Demo', (60,180,250,75), 'demo'),
            LevelButton('Level 1', (60,295,250,75), 'level_1'),
            LevelButton('Level 2', (60,400,250,75), 'level_2'),
            LevelButton('Level 3', (350,180,250,75), 'level_3'),
            LevelButton('Test', (350,295,250,75), 'test_level'),
            LevelButton('Unused', (350,400,250,75), None)
        )

# this is a test menu for rendering and interacting with large text boxes, mainly for font and optimization testing
# to use, replace the arguments for the LifeTextBox in TestMenu.init_buttons()
class TestMenu(LifeMenu): # Test menu for GridFont
    def __init__(self, surface):
        LifeMenu.__init__(self, surface, BLACK, self.init_buttons())

    def init_buttons(self): # creates all buttons in the menu and returns them
        return (
            LifeTextBox(text = font.inventory, rect = (30,30,600,600), cell_size=4, background = BLACK, cell_colour = BLUE, collapse=True),
        )

class TestButton(LifeButton):
    def __init__(self):
        text = 'Test Menu'
        rect = (165,485,330,75)
        LifeButton.__init__(self, text, rect)

    def function(self): # function to execute when button is clicked
        LifeButton.function(self)
        test_menu.main()


WINDOW_WIDTH = 960
WINDOW_HEIGHT = 660
window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
window.fill(BLACK)

level_select = LevelSelect(window)
main_menu = MainMenu(window)

test_menu = TestMenu(window)

main_menu.main()
