import numpy as np
import pygame
import time
from grid import ColouredGrid
from math import ceil


# owner: 0 = dead, 1 = player, 2 = enemy, 3 = shrapnel, 4 = what to defend/attack
COLOURS = {0 : (0, 0, 0), 1 : (0, 0, 255), 2 : (255, 0, 0), 3 : (225, 115, 20), 4 : (140, 0, 200)}
# some temporary colour definitions for easier GUI dev
BUILD_COLOUR = (30, 240, 80)
DEFAULT_BUTTON_COLOUR = (180,180,180)
BACKGROUND_COLOUR = (240,240,240)
BLACK, RED, GREEN, BLUE = (0,0,0), (255, 0, 0), (0,255,0), (0,0,255)


class Game:
    """Main game class to handle events and general gameplay.
    surface: surface to draw onto
    array: array of cells to initialize with
    tickrate: delay between grid.update() calls in seconds
    cell_size: default size of cells in pixels (may be removed later if zooming is added)
    border_width: size of gap between window border and grid in pixels (may be removed later if resizing is added)"""
    def __init__(self, surface, array, tickrate = 0.1, cell_size = 20, rect = (30, 30, 600, 600)):
        self.surface = surface
        self.grid = ColouredGrid(array) # get Grid object
        self.tickrate = tickrate
        self.cell_size = cell_size
        self.rect = pygame.Rect(rect)
        # self.border_width = border_width
        self.time_on = False
        self.ingame = True
        self.cycles = 1
        self.colours = COLOURS
        self.rect_surface = pygame.Surface((self.rect[2], self.rect[3]))
        self.view_coords = [(self.grid.array.shape[1]*cell_size - self.rect[3]) // 2,
                            (self.grid.array.shape[0]*cell_size - self.rect[2]) // 2] # list of top left cell x,y coordinates
        self.MOVES = {pygame.K_UP : (0, -1),
                      pygame.K_DOWN : (0, 1),
                      pygame.K_LEFT : (-1, 0),
                      pygame.K_RIGHT : (1, 0)} # dict for how directions affect coords
        self.DIRECTIONS = {pygame.K_UP : False,
                           pygame.K_DOWN : False,
                           pygame.K_LEFT : False,
                           pygame.K_RIGHT : False} # dict for keypress to var

    def main(self):
        self.start_time = time.perf_counter()
        self.surface.fill(BACKGROUND_COLOUR)
        while self.ingame:
            # get events
            self.handle_events(pygame.event.get())
            if time.perf_counter() - self.start_time - self.cycles * self.tickrate > 0: # true every 'tickrate' seconds
                self.cycles += 1
                if self.time_on: # only run update logic if time is turned on
                    self.grid.update()
            for direction in self.DIRECTIONS:  # check if each direction is held
                if self.DIRECTIONS[direction]: # if it is, scroll that way
                    self.move(direction)
            self.draw()
            # print(self.view_coords, self.cell_size)
            time.sleep(0.01)
    
    def handle_events(self, events):
        """top level function to delegate events"""
        for event in events:
            if event.type in (pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN):
                if event.button in (1, 3): # left/right click
                    self.handle_click(event)
                elif event.button in (4, 5): # scroll
                    self.handle_scroll(event)
            elif event.type == pygame.KEYDOWN: # various keys
                if event.key in (self.DIRECTIONS):
                    self.handle_direction_key(event)
                elif event.key == pygame.K_SPACE:
                    self.handle_space(event)
                elif event.key == pygame.K_ESCAPE:
                    self.handle_escape(event)
                elif event.key == pygame.K_s:
                    self.handle_s_key(event)
            elif event.type == pygame.KEYUP:
                if event.key in (self.DIRECTIONS):
                    self.handle_direction_key(event)
            elif event.type == pygame.QUIT: # if x is clicked on top right of window
                pygame.quit()
                quit()
    
    def handle_direction_key(self, event):
        """toggle whether a key is pressed for move check"""
        if event.type == pygame.KEYDOWN:
            self.DIRECTIONS[event.key] = True
        else:
            self.DIRECTIONS[event.key] = False

    def handle_scroll(self, event):
        """turn scroll wheel events into zooming in and out, ideally centered"""
        if event.type == pygame.MOUSEBUTTONDOWN:
            center_pixel = [(self.view_coords[n]) + self.rect[2+n] // 2 for n in range(2)] # store current center
            total_pixel = [(self.grid.array.shape[int(not n)]) * self.cell_size for n in range(2)] # store current bottom right pixel
            if event.button == 4:
                self.cell_size += 5
            else:
                self.cell_size -= 5
                # catch zooming too far out (far enough that the grid can't cover the full rect)
                self.cell_size = max(5, self.cell_size, max(ceil(self.rect[2] / (self.grid.array.shape[1] - 4)), ceil(self.rect[3] / (self.grid.array.shape[0] - 4))))
            new_total_pixel = [(self.grid.array.shape[int(not n)]) * self.cell_size for n in range(2)] # get new bottom right pixel
            # multiply old center/total ratio by new total to get new center, then subtract half of rect size to find top left
            new_center_pixel = [int(center_pixel[n] / total_pixel[n] * new_total_pixel[n]) - self.rect[2+n] // 2 for n in range(2)]
            # catch overhang when zooming out next to border
            self.view_coords = [max(2 * self.cell_size, min(new_center_pixel[n], new_total_pixel[n] - self.rect[2+n] - 2 * self.cell_size)) for n in range(2)]

    def handle_space(self, event):
        """flip time_on on space press"""
        self.time_on = not self.time_on

    def handle_escape(self, event):
        """currently returns to menu, eventually run open_escape()"""
        self.ingame = False
    
    def handle_s_key(self, event):
        """dummy method to be defined by LevelEditor child"""
        pass
    
    def handle_click(self, event):
        if self.rect.collidepoint(event.pos):
            self.handle_grid_click(event)

    def handle_grid_click(self, event):
        """for clicks inside grid, translate click coords to grid coords, then translate to global array
        then interact appropriately with clicked cell"""
        if not self.time_on: # only do if time is stopped
            # translate to global array coords (also needs to be y,x for numpy)
            coords = [(event.pos[n] - self.rect[n] + self.view_coords[n]) // self.cell_size for n in range(2)][::-1]
            # interact with clicked cell
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.grid.array[coords[0], coords[1]] == 0: # on left click
                self.grid.array[coords[0], coords[1]] = 1 # if the clicked cell is dead, make it a player owned cell
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.grid.array[coords[0], coords[1]] == 1: # on right click
                    self.grid.array[coords[0], coords[1]] = 0 # if the clicked cell is player owned, make it dead

    def move(self, direction, size = 10):
        self.view_coords = [self.view_coords[n] + (self.MOVES[direction][n] * size) for n in range(2)] # shift view in direction
        # catch view going past edge of array
        self.view_coords = [min(max(2 * self.cell_size, self.view_coords[n]), (self.grid.array.shape[int(not n)] - 2) * self.cell_size - self.rect[n+2]) for n in range(2)]

    def draw(self):
        """draw visible grid on pygame window"""
        # slice array to only operate on visible part of grid
        self.viewable_grid = self.grid.array[self.view_coords[1] // self.cell_size : (self.view_coords[1] + self.rect[3]) // self.cell_size + 1,
                                            self.view_coords[0] // self.cell_size : (self.view_coords[0] + self.rect[2]) // self.cell_size + 1]
        mask_list = [np.equal(self.viewable_grid, n) for n in range(5)] # create boolean masks for each type of cell (0 through 4)
        # the next line is very densely packed to avoid wasteful memory intensive copies of potentially million item arrays. There is an explanation for how it works in commit Alpha v1.6
        pixel_array = sum([np.asarray(self.colours[n]) * np.transpose(np.broadcast_to(mask_list[n][:,:,None], (mask_list[n].shape[0], mask_list[n].shape[1], 3)), (1,0,2)) for n in range(5)])
        pixel_surf = pygame.surfarray.make_surface(pixel_array) # make surface
        pixel_surf = pygame.transform.scale(pixel_surf, (pixel_surf.get_size()[0]*self.cell_size, pixel_surf.get_size()[1]*self.cell_size)) # scale by cell size
        pixel_surf.scroll(-(self.view_coords[0] % self.cell_size), -(self.view_coords[1] % self.cell_size)) # scroll surface by the offset (I think it just shifts all pixels in a direction)
        self.surface.blit(self.rect_surface, self.rect) # draw intermediate surface to mask out hanging pixels at edge
        self.rect_surface.blit(pixel_surf, (0,0)) # draw
        pygame.display.update()




class LevelEditor(Game):
    """Child class for the level editor
    works very similarly to Game except for some functionality to help with level building and a save function"""
    def __init__(self, surface, array):
        Game.__init__(self, surface, array)

    def handle_space(self, event):
        if self.time_on == False:
            self.placeholder_grid = self.grid.array.copy()
        else:
            self.grid.array = self.placeholder_grid
        self.time_on = not self.time_on
    
    def handle_s_key(self):
        if self.time_on:
            np.savetxt('savedgrid.csv', self.placeholder_grid, '%1.0f', delimiter=",")
        else:
            np.savetxt('savedgrid.csv', self.grid.array, '%1.0f', delimiter=",")

    def handle_grid_click(self, event):
        """for clicks inside grid, translate click coords to grid coords, then translate to global array
        then interact appropriately with clicked cell"""
        if not self.time_on: # only do if time is stopped
            # translate to global array coords (also needs to be y,x for numpy)
            coords = [(event.pos[n] - self.rect[n] + self.view_coords[n]) // self.cell_size for n in range(2)][::-1]
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and self.grid.array[coords[0], coords[1]] < 4:
                self.grid.array[coords[0], coords[1]] += 1 # increment when left click
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.grid.array[coords[0], coords[1]] > 0:
                self.grid.array[coords[0], coords[1]] -= 1 # decrement when right click
