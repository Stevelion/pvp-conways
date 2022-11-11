import numpy as np
import pygame
import time
from math import ceil
from gridfont import font
from grid import Grid

# owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
COLOURS = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}
# some temporary colour definitions for easier GUI dev
BUILD_COLOUR = (30, 240, 80)
DEFAULT_BUTTON_COLOUR = (180,180,180)
BACKGROUND_COLOUR = (240,240,240)
BLACK, RED, GREEN, BLUE = (0,0,0), (255, 0, 0), (0,255,0), (0,0,255)



# GUI Abstract Classes
class LifeTextBox():
    """Abstract class for buttons that collapse into Conway's Game of Life sims when hovered"""
    def __init__(self, text, rect, cell_size = 5, background = BLACK, cell_colour = BLUE, centered = False, collapse = False):
        self.rect = pygame.Rect(rect)
        grid_width = rect[2] // cell_size - 4 # calculate width for font.arrange()
        array = font.arrange(text, grid_width, centered = centered) # turn text into array
        array = font.expand_grid(array, (array.shape[1] + 14, array.shape[0] + 14)) # expand array with 0s
        self.grid = Grid(array) # create grid object from array
        self.cell_size = cell_size
        self.collapse = collapse
        self.colours = {0 : background, 1 : cell_colour}
        self.hovered = False
        if self.collapse: # collapse rect dimensions to match grid
            self.rect.update(self.rect[0], self.rect[1],
                            (self.grid.array.shape[1] - 10) * self.cell_size,
                            (self.grid.array.shape[0] - 10) * self.cell_size)

    def update(self):
        self.grid.update()
    
    def hover(self, event): # event handler for MOUSEMOTION events
        if not self.hovered and self.rect.collidepoint(event.pos): # if it wasn't hovered and now is
            self.hovered = True
            self.placeholder_grid = self.grid.array
        elif self.hovered and not self.rect.collidepoint(event.pos): # if it was hovered and now isn't
            self.hovered = False
            self.grid.array = self.placeholder_grid

    def draw(self, surface):
        """draw object on surface"""
        mask_list = [np.equal(self.grid.array, n) for n in range(2)] # create boolean masks for each type of cell (0 through 4)
        # the next line is very densely packed to avoid wasteful memory intensive copies of potentially million item arrays. There is an explanation for how it works in commit Alpha v1.6
        pixel_array = sum([np.asarray(self.colours[n]) * np.transpose(np.broadcast_to(mask_list[n][:,:,None], (mask_list[n].shape[0], mask_list[n].shape[1], 3)), (1,0,2)) for n in range(2)])
        pixel_surf = pygame.surfarray.make_surface(pixel_array[5:-5,5:-5,:]) # make surface, excluding outer 5 rows/columns
        pixel_surf = pygame.transform.scale(pixel_surf, (pixel_surf.get_size()[0]*self.cell_size, pixel_surf.get_size()[1]*self.cell_size)) # scale by cell size
        surface.blit(pixel_surf, self.rect[0:2]) # draw on window



class LifeButton(LifeTextBox):
    def __init__(self, text, rect, cell_size = 5, background = BLACK, cell_colour = GREEN, centered = True):
        LifeTextBox.__init__(self, text, rect, cell_size, background, cell_colour, centered)
    
    def function(self):
        self.hovered = False
        self.grid.array = self.placeholder_grid



class LifeMenu:
    """Abstract menu class for containing and updating LifeButtons"""
    def __init__(self, surface, background, buttons, tickrate = 0.1):
        self.surface = surface
        self.buttons = buttons
        self.background = background
        self.tickrate = tickrate

    def main(self): # main event loop
        self.restart_timer()
        self.draw()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.MOUSEMOTION: # find if mouse motion involved hovering or unhovering a button
                    for button in self.buttons:
                        button.hover(event) # pass to each button, they turn flip a var that says whether to update at update step
                if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
                    # find button and execute it's function
                    for button in self.buttons:
                        if isinstance(button, LifeButton):
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
                    if button.hovered: # update all buttons that are ticked as hovered, should only ever be 1
                        button.update()
                self.draw()
            time.sleep(0.01)
    
    def restart_timer(self): # causes issues if a button doesn't open a menu, adjust start time (modulo maybe)
        """restart update timer"""
        self.start_time = time.perf_counter()
        self.cycles = 1

    def draw(self):
        """draw menu with buttons"""
        self.surface.fill(self.background)
        for button in self.buttons:
            button.draw(self.surface)
        pygame.display.update()



class PrefabButton(LifeButton):
    def __init__(self, name, rect, array, parent, cell_size):
        self.name = name
        self.rect = pygame.Rect(rect)
        self.pattern = array
        self.parent = parent
        self.cell_size = cell_size
        self.grid = Grid(self.expand_array(self.pattern, (self.rect[2], self.rect[3]), self.cell_size)) # create grid object from array
        self.colours = {0 : BLACK, 1 : BLUE}
        self.hovered = False
        self.rect_surface = pygame.Surface((self.rect[2], self.rect[3])) # intermediate surface to hide edge of draw()
    
    def expand_array(self, array, size, cell_size):
        """fill in empty space around array to fill button size"""
        width = ceil(size[0] / cell_size + 10)
        height = ceil(size[1] / cell_size + 10)
        x_expand = (width - array.shape[1]) // 2
        y_expand = (height - array.shape[0]) // 2 # calculate how many 0s are needed on each side
        new_array = array
        new_array = np.append(np.zeros((new_array.shape[0], x_expand)), new_array, 1) # expand x axis in both directions with 0s
        new_array = np.append(new_array, np.zeros((new_array.shape[0], x_expand)), 1)
        if x_expand * 2 != width - array.shape[1]: # catch lost odd from integer div
            new_array = np.append(new_array, np.zeros((new_array.shape[0], 1)), 1)
        new_array = np.append(np.zeros((y_expand, new_array.shape[1])), new_array, 0) # expand y axis in both directions with 0s
        new_array = np.append(new_array, np.zeros((y_expand, new_array.shape[1])), 0)
        if y_expand * 2 != height - array.shape[0]: # catch lost odd from integer div
            new_array = np.append(new_array, np.zeros((1, new_array.shape[1])), 0)
        return new_array

    def draw(self, surface):
        """nearly inherited draw method, only difference is intermediate blit to rect surface"""
        mask_list = [np.equal(self.grid.array, n) for n in range(2)] # create boolean masks for each type of cell (0 through 4)
        # the next line is very densely packed to avoid wasteful memory intensive copies of potentially million item arrays. There is an explanation for how it works in commit Alpha v1.6
        pixel_array = sum([np.asarray(self.colours[n]) * np.transpose(np.broadcast_to(mask_list[n][:,:,None], (mask_list[n].shape[0], mask_list[n].shape[1], 3)), (1,0,2)) for n in range(2)])
        pixel_surf = pygame.surfarray.make_surface(pixel_array[5:-5,5:-5,:]) # make surface, excluding outer 5 rows/columns
        pixel_surf = pygame.transform.scale(pixel_surf, (pixel_surf.get_size()[0]*self.cell_size, pixel_surf.get_size()[1]*self.cell_size)) # scale by cell size
        surface.blit(self.rect_surface, self.rect) # draw intermediate surface to hide hanging pixels at edge
        self.rect_surface.blit(pixel_surf, (0,0)) # draw

    def function(self):
        """copy pattern to selected"""
        self.parent.selected_pattern = self.pattern.copy()